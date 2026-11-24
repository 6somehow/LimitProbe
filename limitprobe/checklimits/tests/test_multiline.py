"""Targets that span several lines: the failing line of a multi-line assert is inside the statement, the Region
snippet is the statement joined onto one line (step 4 style), and LINE events inside the statement must not be
mistaken for 'the assert passed'. Found by the first batch run (flexprefill-F006)."""
import ast
import importlib.util
import sys
import textwrap

import pytest

from checklimits import fidelity, harness
from checklimits.harness import RunOptions
from checklimits.profile import Profile
from checklimits.tracer import ChainFn, MonitoringTracer, SettraceTracer, TargetSpec, classify_target, target_span
from toyhelper import build

FAST = RunOptions.fast()


def run_toy(tmp_path, **kw):
    b = build(tmp_path, with_ext=False, kind="multiline", pos={"n": 2, "m": 0}, neg={"n": 1, "m": 0}, **kw)
    return b, harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]


def test_exception_inside_a_multiline_assert_counts_as_raised_at_the_target(tmp_path):
    b, r = run_toy(tmp_path)
    assert (r.verdict, r.final_verdict) == ("yes", "yes")
    assert r.positive.effect is True and r.positive.exception.type == "AssertionError"
    line = int(r.positive.exception.raised_at.rsplit(":", 1)[1])
    assert b["line"] <= line <= b["line"] + 3                 # somewhere inside assert ( ... ), "msg"
    assert r.negative.effect is False


def test_decision_outcomes_survive_the_extra_line_events(tmp_path):
    _, r = run_toy(tmp_path)
    assert [h.outcome for h in r.positive.target_hits] == ["false"]      # not "error", not "true"
    assert [h.outcome for h in r.negative.target_hits] == ["true"]
    assert r.audit.rate == 1.0


def test_snippet_check_accepts_the_joined_statement_and_ignores_parentheses(tmp_path):
    b, r = run_toy(tmp_path)
    assert r.fidelity.ast_diff.snippet_matches_region
    d12 = next(d for d in r.confidence.defeaters if d.id == "D12")
    assert d12.status == "eliminated"


@pytest.mark.parametrize("snippet,ok", [
    ("assert n == 1 and m >= 0", True),
    ("assert (n == 1 and m >= 0)", True),
    ("assert n == 1  and  m >= 0", True),
    ("assert n == 2 and m >= 0", False),
    ("assert n == 1", False),
])
def test_snippet_matching_rules(tmp_path, snippet, ok):
    b = build(tmp_path, with_ext=False, kind="multiline")
    ad = fidelity.ast_diff(b["repo"], b["commit"], ["toypkg/core.py::entry", "toypkg/core.py::check"],
                           "toypkg/core.py", b["line"], snippet, "check")
    assert ad.snippet_matches_region is ok


def test_one_line_snippets_of_compound_statements_still_match(tmp_path):
    b = build(tmp_path, with_ext=False, kind="branch")
    for snip, ok in (("if n > 3:", True), ("if n > 3", True), ("if n > 4:", False)):
        ad = fidelity.ast_diff(b["repo"], b["commit"], ["toypkg/core.py::entry", "toypkg/core.py::check"],
                               "toypkg/core.py", b["line"], snip, "check")
        assert ad.snippet_matches_region is ok, snip


SRC = textwrap.dedent('''
    def f(a, b):
        if (
            a > 3
            and b > 3
        ):
            return 1
        return 0
''')


@pytest.mark.parametrize("Tracer", [MonitoringTracer, SettraceTracer])
def test_tracer_resolves_a_multiline_if_only_after_its_header(tmp_path, Tracer):
    p = tmp_path / "ml.py"
    p.write_text(SRC)
    spec = importlib.util.spec_from_file_location("ml_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    kind, body = classify_target(tmp_path, "ml.py", 3)
    assert kind == "if" and target_span(tmp_path, "ml.py", 3) == (3, 5)        # header only, not the body
    for args, want in (((5, 5), "true"), ((5, 1), "false"), ((1, 1), "false")):
        t = Tracer(tmp_path, [ChainFn("ml.py", "f")], TargetSpec("ml.py", 3, "f", kind, body, "a > 3 and b > 3", end_line=5))
        t.start()
        try:
            m.f(*args)
        finally:
            t.stop()
        assert [h["outcome"] for h in t.result()["target_hits"]] == [want], args


@pytest.mark.parametrize("Tracer", [MonitoringTracer, SettraceTracer])
def test_tracer_marks_a_failing_multiline_assert_false(tmp_path, Tracer):
    p = tmp_path / "ma.py"
    p.write_text("def g(x):\n    assert (\n        x > 0\n        and x < 10\n    ), 'range'\n    return x\n")
    spec = importlib.util.spec_from_file_location("ma_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for arg, want in ((5, "true"), (50, "false")):
        t = Tracer(tmp_path, [ChainFn("ma.py", "g")], TargetSpec("ma.py", 2, "g", "assert", end_line=5))
        t.start()
        try:
            m.g(arg)
        except AssertionError:
            pass
        finally:
            t.stop()
        assert [h["outcome"] for h in t.result()["target_hits"]] == [want], arg
