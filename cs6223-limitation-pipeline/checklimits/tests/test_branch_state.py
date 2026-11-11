"""Effect families beyond `reject`: a branch decision taken (fallback / mechanism_variant) and a branch decision
that depends on state left by earlier calls (state_dependent)."""
import json

import pytest

from checklimits import audit, harness, runner
from checklimits.harness import RunOptions
from checklimits.models import Observation, TargetHit
from checklimits.profile import Profile
from toyhelper import build

QUICK = Profile(n_rep=2)
FAST = RunOptions.fast()
FULL = RunOptions(repeats=2)


def go(tmp_path, options=FAST, **kw):
    b = build(tmp_path, with_ext=False, **kw)
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=options, profile=QUICK)["report"]
    return b, r


def st(r):
    return {d.id: d.status for d in r.confidence.defeaters}


# --- fallback: the branch is taken ----------------------------------------------------------------------------
def test_branch_taken_on_positive_not_on_negative_is_yes(tmp_path):
    b, r = go(tmp_path, kind="branch")
    assert (r.verdict, r.final_verdict, r.exec_result) == ("yes", "yes", "confirmed")
    assert r.positive.effect is True and r.positive.observed_text == f"branch taken at {b['loc']}"
    assert r.negative.effect is False and r.negative.observed_text == f"branch not taken at {b['loc']}"
    assert r.positive.target_kind == "if" and [h.outcome for h in r.positive.target_hits] == ["true"]
    assert [h.outcome for h in r.negative.target_hits] == ["false"]
    assert r.audit.rate == 1.0 and st(r)["D2"] == "eliminated" and st(r)["D4"] == "eliminated"
    assert r.oracle.verified_tier == "O4"          # a path_hook oracle naming Region.location


def test_branch_full_pipeline_reaches_L3(tmp_path):
    b, r = go(tmp_path, FULL, kind="branch")
    assert r.confidence.level == "L3", r.confidence.next_steps
    m = r.checks.mutation
    assert m.generated == 4 and m.killed == 4          # negate, >=, 3->4, 3->2
    assert r.checks.bva.adjacent and {p.label: p.effect for p in r.checks.bva.neighbours} == {"neg+": True, "neg-": False}
    assert r.checks.replay.ok and r.checks.repeat.identical


def test_branch_taken_on_both_inputs_is_inconclusive(tmp_path):
    _, r = go(tmp_path, kind="branch", neg={"n": 7})
    assert (r.verdict, r.exec_result) == ("inconclusive", "test_error") and "both inputs" in r.verdict_reason


def test_branch_not_taken_on_either_input_is_no(tmp_path):
    _, r = go(tmp_path, kind="branch", pos={"n": 3})
    assert r.verdict == "no"
    assert st(r)["D2"] == "refuted"           # the Region says n > 3 holds on the positive input; it does not


def test_branch_with_reversed_pair_is_inconclusive(tmp_path):
    _, r = go(tmp_path, kind="branch", pos={"n": 3}, neg={"n": 4})
    assert r.verdict == "inconclusive" and "reversed" in r.verdict_reason


def test_branch_effect_ignores_what_happens_after_the_decision(tmp_path):
    drv = "from toypkg.core import entry\n\n\ndef run(inputs):\n    entry(inputs['n'], inputs['m'])\n    raise RuntimeError('boom after the call')\n"
    _, r = go(tmp_path, kind="branch", driver_src=drv)
    assert r.verdict == "yes" and r.positive.post_target_exception.type == "RuntimeError"
    assert r.positive.observed_text.startswith("branch taken at") and "later RuntimeError" in r.positive.observed_text


# --- what is not a branch -------------------------------------------------------------------------------------
def test_outcome_support_by_target_kind(tmp_path):
    b = build(tmp_path, with_ext=False, kind="branch")
    from checklimits.adapter import load_task
    t = load_task("F1", b["root"] / "data")
    reg = t.regions[0]
    assert runner.outcome_support(reg, b["repo"]) == (True, "")
    reg2 = reg.model_copy(update={"location": reg.location.model_copy(update={"line_start": reg.location.line_start - 1})})
    ok, why = runner.outcome_support(reg2, b["repo"])
    assert not ok and "not" in why or "statement" in why                  # an assignment is not a branch decision
    reg3 = reg.model_copy(update={"outcome": "suspicious"})
    assert not runner.outcome_support(reg3, b["repo"])[0]


def test_assert_target_with_a_fallback_outcome_is_not_run(tmp_path):
    b = build(tmp_path, with_ext=False)                        # the target is an assert
    reg = json.loads((b["root"] / "data" / "gold_regions.json").read_text())
    reg[0]["outcome"] = "fallback"
    (b["root"] / "data" / "gold_regions.json").write_text(json.dumps(reg))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FULL, profile=QUICK)["report"]
    assert (r.verdict, r.exec_result) == ("inconclusive", "not_run")
    assert "judged from a branch decision" in r.verdict_reason and r.checks.mutation is None


# --- audit grammar --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text,expect", [
    ("branch taken at a/b.py:10", ("branch_taken", None, 10)),
    ("branch not taken at :10", ("branch_not_taken", None, 10)),
    ("Branch taken", ("branch_taken", None, None)),
])
def test_parse_branch_claims(text, expect):
    assert audit.parse_observed(text) == expect


def test_branch_claims_are_checked_against_the_effect():
    taken = Observation(role="positive", inputs={}, status="ok", effect=True, observed_text="branch taken at a:1")
    not_taken = Observation(role="negative", inputs={}, status="ok", effect=False, observed_text="branch not taken at a:1")
    assert audit.observed_matches("branch taken at a:1", taken) and not audit.observed_matches("branch not taken at a:1", taken)
    assert audit.observed_matches("branch not taken at a:1", not_taken) and not audit.observed_matches("branch taken", not_taken)
    assert not audit.observed_matches("AssertionError at a:1", taken)        # a reject-style claim for a branch run
    unknown = Observation(role="positive", inputs={}, status="ok", effect=None, observed_text="whatever")
    assert not audit.observed_matches("branch taken", unknown)


# --- state_dependent: earlier calls change the decision -----------------------------------------------------
STATE = dict(kind="state", design_extra={"negative_prelude": [{"n": 1}], "boundary_variable": "prelude"})


def test_state_dependent_branch_differs_after_a_prelude_call(tmp_path):
    b, r = go(tmp_path, **STATE)
    assert (r.verdict, r.final_verdict) == ("yes", "yes")
    assert r.positive.effect is True and r.negative.effect is False
    assert r.checks.differing_factors == ["prelude"]
    # hits of the prelude call are kept per call, but the observation uses only the checked (last) call
    assert [h.outcome for h in r.negative.target_hits] == ["false"]
    assert r.audit.rate == 1.0 and st(r)["D5"] == "open"


def test_state_prelude_hits_are_tagged_with_their_call(tmp_path):
    b = build(tmp_path, with_ext=False, **STATE)
    ctx = harness._Ctx(b["attempt"], b["root"])
    raw, obs = ctx.run("negative", b["form"]["design"]["negative_input"])
    calls = [(h["call"], h["outcome"]) for h in raw["trace"]["target_hits"]]
    assert calls == [(0, "true"), (1, "false")] and raw["final_call"] == 1
    assert obs.effect is False and len(obs.target_hits) == 1


def test_state_full_pipeline_has_two_known_gaps(tmp_path):
    # (1) adjacency of a *state* cannot be probed: D5 stays residual. (2) `cache is None` offers only the negation
    # mutant, fewer than n_min, so D3 stays residual too. Both cap the level; neither is hidden.
    b, r = go(tmp_path, FULL, **STATE)
    assert r.checks.bva is not None and not r.checks.bva.applicable and "prelude" in r.checks.bva.note
    assert st(r)["D5"] == "residual" and st(r)["D3"] == "residual" and r.checks.mutation.generated == 1
    assert st(r)["D9"] == "eliminated" and st(r)["D8"] == "eliminated"
    assert r.confidence.level == "L1" and any(s.startswith("D3") for s in r.confidence.next_steps)


def test_a_failing_prelude_call_is_a_test_error(tmp_path):
    drv = "from toypkg.core import entry\n\n\ndef run(inputs):\n    if inputs.get('explode'):\n        raise KeyError('prelude')\n    return entry(inputs['n'], inputs['m'])\n"
    _, r = go(tmp_path, driver_src=drv, kind="state",
              design_extra={"negative_prelude": [{"n": 1, "explode": True}], "boundary_variable": "prelude"})
    assert r.negative.effect is None and "prelude call 0 failed" in r.negative.effect_note
    assert (r.verdict, r.exec_result) == ("inconclusive", "test_error")


def test_without_the_prelude_both_runs_see_a_fresh_state(tmp_path):
    _, r = go(tmp_path, kind="state", design_extra={"boundary_variable": "n"})
    assert r.verdict == "inconclusive" and "both inputs" in r.verdict_reason     # same fresh state: the branch is taken twice
