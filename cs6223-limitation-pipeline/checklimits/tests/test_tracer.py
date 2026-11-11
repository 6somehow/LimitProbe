"""In-process tests of the sys.monitoring tracer on a tiny module (if / while / assert targets)."""
import importlib.util
import sys
import textwrap

import pytest

from checklimits.tracer import ChainFn, TargetSpec, Tracer, classify_target

SRC = textwrap.dedent('''
    def f(x):
        y = x * 2
        if x > 3:
            y += 1
            y += 2
        else:
            y -= 1
        for i in range(2):
            y += i
        assert y < 100, "too big"
        return y
''')


@pytest.fixture
def mod(tmp_path):
    p = tmp_path / "mod_under_trace.py"
    p.write_text(SRC)
    spec = importlib.util.spec_from_file_location("mod_under_trace", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["mod_under_trace"] = m
    spec.loader.exec_module(m)
    yield tmp_path, m
    sys.modules.pop("mod_under_trace", None)


def line_of(text):
    return next(i for i, l in enumerate(SRC.splitlines(), 1) if text in l)


def trace(tmp, m, line, arg, expr=None):
    kind, body = classify_target(tmp, "mod_under_trace.py", line)
    t = Tracer(tmp, [ChainFn("mod_under_trace.py", "f")], TargetSpec("mod_under_trace.py", line, "f", kind, body, expr))
    t.start()
    try:
        m.f(arg)
    except AssertionError:
        pass
    finally:
        t.stop()
    return kind, t.result()


def test_if_outcomes(mod):
    tmp, m = mod
    ln = line_of("if x > 3")
    kind, r = trace(tmp, m, ln, 5, "x > 3")
    assert kind == "if" and [h["outcome"] for h in r["target_hits"]] == ["true"]
    assert r["target_hits"][0]["condition_value"] is True
    _, r = trace(tmp, m, ln, 1, "x > 3")
    assert [h["outcome"] for h in r["target_hits"]] == ["false"]
    assert r["target_hits"][0]["condition_value"] is False


def test_assert_outcomes(mod):
    tmp, m = mod
    ln = line_of("assert y < 100")
    kind, r = trace(tmp, m, ln, 5)
    assert kind == "assert" and [h["outcome"] for h in r["target_hits"]] == ["true"]
    _, r = trace(tmp, m, ln, 500)
    assert [h["outcome"] for h in r["target_hits"]] == ["false"]


def test_assert_as_last_statement_resolves_on_return(tmp_path):
    p = tmp_path / "m2.py"
    p.write_text("def g(x):\n    assert x\n")
    spec = importlib.util.spec_from_file_location("m2", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    t = Tracer(tmp_path, [ChainFn("m2.py", "g")], TargetSpec("m2.py", 2, "g", "assert"))
    t.start()
    try:
        m.g(1)
    finally:
        t.stop()
    assert [h["outcome"] for h in t.result()["target_hits"]] == ["true"]


def test_loop_line_hit_counts_and_coverage(mod):
    tmp, m = mod
    ln = line_of("y += i")
    kind, r = trace(tmp, m, ln, 1)
    assert kind == "other" and len(r["target_hits"]) == 2
    assert ln in r["lines"]["f"] and line_of("y += 1") not in r["lines"]["f"]  # else-branch only


def test_condition_not_evaluable_is_recorded_not_raised(mod):
    tmp, m = mod
    _, r = trace(tmp, m, line_of("if x > 3"), 5, "undefined_name > 3")
    h = r["target_hits"][0]
    assert h["condition_value"] is None and "NameError" in h["condition_error"]


def test_predicate_callable_is_used(mod):
    tmp, m = mod
    kind, body = classify_target(tmp, "mod_under_trace.py", line_of("if x > 3"))
    t = Tracer(tmp, [ChainFn("mod_under_trace.py", "f")],
               TargetSpec("mod_under_trace.py", line_of("if x > 3"), "f", kind, body, None, lambda loc: loc["y"] == 10))
    t.start()
    try:
        m.f(5)
    finally:
        t.stop()
    assert t.result()["target_hits"][0]["condition_value"] is True


def test_tracer_releases_the_tool_slot(mod):
    tmp, m = mod
    trace(tmp, m, line_of("if x > 3"), 5)
    assert sys.monitoring.get_tool(sys.monitoring.PROFILER_ID) is None
