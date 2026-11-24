"""A `raise` target only runs when its guard holds: the contrast run never reaches it. D2 ("the condition is true on the
positive run and false on the negative run") must then be evaluated on the guard, not on the target line. Found by
the 2026-11-16 experiments: NNSmith F001 / F003 and FlexPrefill F019 were `invalid` for this reason although an LLM
reviewer found their tests valid."""
import json

import pytest

from checklimits import harness, tracer
from checklimits.harness import RunOptions
from toyhelper import build

DRV = "from toypkg.core import entry\n\n\ndef run(inputs):\n    return entry(inputs['n'], inputs['m'])\n"


@pytest.mark.parametrize("src,line,span", [
    ("def f(a):\n    if a:\n        raise ValueError(a)\n", 3, (2, 2)),
    ("def f(a):\n    if a == 0:\n        return 0\n    elif a == 1:\n        return 1\n    else:\n        raise ValueError(a)\n", 7, (2, 2)),
    ("def f(a, b):\n    if (a and\n            b):\n        x = 1\n        raise ValueError(a)\n", 5, (2, 3)),
    ("def f(a):\n    raise ValueError(a)\n", 2, (0, 0)),                      # not guarded by an if
    ("def f(a):\n    for i in a:\n        raise ValueError(i)\n", 3, (0, 0)),   # a loop body is not a guard
    ("def f(a):\n    assert a\n", 2, (0, 0)),
    ("def f(a):\n    if a:\n        x = 1\n        if x:\n            raise ValueError(a)\n", 5, (4, 4)),   # nested: the innermost if
])
def test_decision_span(tmp_path, src, line, span):
    (tmp_path / "m.py").write_text(src)
    assert tracer.decision_span(tmp_path, "m.py", line) == span


def _run(tmp_path, pos, neg):
    b = build(tmp_path, with_ext=False, kind="bareraise", driver_src=DRV, pos=pos, neg=neg, design_extra={"boundary_variable": "n"})
    form = json.loads((b["attempt"] / "form.json").read_text())
    loc = b["loc"]
    form["design"]["oracle"]["spec"] = f"ValueError raised at {loc}"
    form["design"]["expected"]["positive"] = f"ValueError at {loc}"
    form["claims"]["positive_observed"] = f"ValueError at {loc}"
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    return harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=RunOptions.fast())["report"]


def st(r):
    return {d.id: d.status for d in r.confidence.defeaters}


def test_contrast_that_does_not_reach_the_raise_still_satisfies_d2(tmp_path):
    r = _run(tmp_path, {"n": 2, "m": 0}, {"n": 1, "m": 0})
    assert r.positive.target_reached and not r.negative.target_reached         # the raise is not executed on the contrast
    assert r.negative.decision_hits and r.negative.decision_hits[-1].condition_value is False
    assert r.positive.decision_hits and r.positive.decision_hits[-1].condition_value is True
    assert (r.verdict, st(r)["D1"], st(r)["D2"]) == ("yes", "eliminated", "eliminated")
    assert r.final_verdict == "yes" and r.confidence.level != "invalid"


def test_a_contrast_that_never_reaches_the_guard_is_still_not_accepted(tmp_path):
    # the driver breaks before the guard when m is negative: no decision hit, no evidence that the condition fails
    drv = DRV.replace("    return entry", "    if inputs['m'] < 0:\n        return None\n    return entry")
    b = build(tmp_path, with_ext=False, kind="bareraise", driver_src=drv, pos={"n": 2, "m": 0}, neg={"n": 1, "m": -1},
              design_extra={"boundary_variable": "n"})
    form = json.loads((b["attempt"] / "form.json").read_text())
    form["design"]["oracle"]["spec"] = f"ValueError raised at {b['loc']}"
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=RunOptions.fast())["report"]
    assert not r.negative.decision_hits and st(r)["D2"] == "refuted" and r.final_verdict == "inconclusive"


def test_a_contrast_where_the_guard_still_holds_is_refuted(tmp_path):
    r = _run(tmp_path, {"n": 2, "m": 0}, {"n": 5, "m": 0})                      # both inputs raise
    assert st(r)["D2"] == "refuted"
