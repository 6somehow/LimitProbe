"""`reject` is judged by an exception raised at the target. If the target statement cannot raise, the harness must decline
instead of reporting a confident `no`. Found by the NNSmith batch: step 4 labels `if ...: continue` (skip a candidate) and
`while not check_sat():` as `reject`, and three agent runs ended in `no / L1` for the wrong reason."""
import ast

import pytest

from checklimits import harness, runner, tracer
from checklimits.harness import RunOptions
from checklimits.adapter import load_task
from toyhelper import build

FAST = RunOptions.fast()
DRV = "from toypkg.core import entry\n\n\ndef run(inputs):\n    return entry(inputs['n'], inputs['m'])\n"


@pytest.mark.parametrize("src,line,ok", [
    ("def f(a):\n    assert a\n", 2, True),
    ("def f(a):\n    raise ValueError(a)\n", 2, True),
    ("def f(a):\n    if a:\n        raise ValueError(a)\n    return 1\n", 2, True),
    ("def f(a):\n    if a:\n        x = 1\n    else:\n        raise ValueError(a)\n", 2, True),
    ("def f(a):\n    for i in a:\n        if i:\n            continue\n", 3, False),
    ("def f(a):\n    while not a():\n        a = 1\n", 2, False),
    ("def f(a):\n    x = a + 1\n", 2, False),
    ("def f(a):\n    if a:\n        g(a)\n", 2, False),
])
def test_can_raise_here(tmp_path, src, line, ok):
    (tmp_path / "m.py").write_text(src)
    assert tracer.can_raise_here(tmp_path, "m.py", line)[0] is ok


def test_statement_span_includes_the_body(tmp_path):
    (tmp_path / "m.py").write_text("def f(a):\n    if a:\n        x = 1\n        raise ValueError(x)\n    return 2\n")
    assert tracer.statement_span(tmp_path, "m.py", 2) == (2, 4) and tracer.target_span(tmp_path, "m.py", 2) == (2, 2)


def test_reject_on_a_skip_branch_is_not_run_not_no(tmp_path):
    b = build(tmp_path, with_ext=False, kind="ifskip", driver_src=DRV, pos={"n": 1, "m": 0}, neg={"n": 7, "m": 0})
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=RunOptions(repeats=2, mutation=False), profile=harness.DEFAULT.model_copy(update={"n_rep": 2}))["report"]
    assert (r.verdict, r.exec_result) == ("inconclusive", "not_run")
    assert "cannot raise" in r.verdict_reason or "no raise in its body" in r.verdict_reason
    assert r.confidence.level == "n/a" and r.checks.mutation is None


def test_reject_on_an_if_that_raises_is_judged(tmp_path):
    b = build(tmp_path, with_ext=False, kind="ifraise", driver_src=DRV, pos={"n": 2, "m": 0}, neg={"n": 1, "m": 0},
              design_extra={"boundary_variable": "n"})
    form = __import__("json").loads((b["attempt"] / "form.json").read_text())
    loc = b["loc"]
    form["design"]["oracle"]["spec"] = f"ValueError raised at {loc}"
    form["design"]["expected"]["positive"] = f"ValueError at {loc}"
    form["claims"]["positive_observed"] = f"ValueError at {b['loc'].rsplit(':', 1)[0]}:{b['line'] + 1}"
    (b["attempt"] / "form.json").write_text(__import__("json").dumps(form))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    assert (r.verdict, r.final_verdict) == ("yes", "yes")
    assert r.positive.exception.type == "ValueError" and r.positive.effect is True
    line = int(r.positive.exception.raised_at.rsplit(":", 1)[1])
    assert line == b["line"] + 1                      # the raise statement inside the body, not the if line
    assert r.audit.rate == 1.0 or r.audit.matched_checks >= 5


def test_outcome_support_message_names_the_reason(tmp_path):
    b = build(tmp_path, with_ext=False, kind="ifskip")
    reg = load_task("F1", b["root"] / "data").regions[0]
    ok, why = runner.outcome_support(reg, b["repo"])
    assert not ok and "outcome 'reject'" in why and "no raise in its body" in why


def test_asserts_are_unchanged(tmp_path):
    b = build(tmp_path, with_ext=False)
    reg = load_task("F1", b["root"] / "data").regions[0]
    assert runner.outcome_support(reg, b["repo"]) == (True, "")
