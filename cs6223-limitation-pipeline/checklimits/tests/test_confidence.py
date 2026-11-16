"""Rule table of confidence.py, driven with synthetic measurements (no processes)."""
import dataclasses

import pytest

from checklimits import confidence as C
from checklimits.models import BvaResult, InfoItem, MutationResult, RepeatResult, ReplayResult
from checklimits.profile import Profile
from checklimits.stats import rule_of_three, wilson_lower

P = Profile()


def ideal(**kw) -> C.Measurements:
    base = dict(
        verdict="yes", target_reached=True, cond_true_on_positive=True, cond_false_on_negative=True,
        mutation=MutationResult(generated=5, killed=5, wilson_lower=round(wilson_lower(5, 5), 3)),
        declared_tier="O4", verified_tier="O4", preregistered=True, differing_factors=["x"], controls_differ=True,
        bva=BvaResult(applicable=True, boundary_variable="x", full_scale_positive=True, full_scale_negative=False,
                      adjacent=True), probe_effect_free=True,
        info=[InfoItem(statement="p", run="positive", verdict_bearing=True, evidence_state="direct", basis=""),
              InfoItem(statement="n", run="negative", verdict_bearing=True, evidence_state="direct", basis="")],
        repeat=RepeatResult(runs=5, identical=True, distinct_hashes=1, flake_bound=0.6, trace_hash="x"),
        replay=ReplayResult(ok=True, detail="ok"), scale_declared=False, main_positive_effect=True,
        main_negative_effect=False, scope_status="scope_edge", entry_index=0)
    base.update(kw)
    return C.Measurements(**base)


def run(m):
    conf, final = C.build(m, P)
    return conf, final, {d.id: d.status for d in conf.defeaters}


def test_ideal_is_L3():
    conf, final, st = run(ideal())
    assert conf.level == "L3" and final == "yes" and set(st.values()) == {"eliminated"} and conf.next_steps == []


@pytest.mark.parametrize("change,defeater,status,level", [
    (dict(target_reached=False), "D1", "refuted", "invalid"),
    (dict(cond_true_on_positive=False), "D2", "refuted", "invalid"),
    (dict(cond_true_on_positive=None, cond_false_on_negative=None), "D2", "open", "L0"),
    (dict(condition_translated=True), "D2", "residual", "L1"),
    (dict(mutation=None), "D3", "open", "L1"),
    (dict(mutation=MutationResult(generated=0, killed=0, wilson_lower=0.0)), "D3", "open", "L1"),
    (dict(mutation=MutationResult(generated=3, killed=3, wilson_lower=0.44)), "D3", "residual", "L1"),
    (dict(mutation=MutationResult(generated=4, killed=3, wilson_lower=0.30)), "D3", "refuted", "L1"),
    (dict(verified_tier="O3"), "D4", "residual", "L1"),
    (dict(verified_tier="O2"), "D4", "refuted", "invalid"),
    (dict(preregistered=False), "D4", "refuted", "invalid"),
    (dict(oracle_revisions=1), "D4", "residual", "L1"),
    (dict(differing_factors=["x", "y"]), "D5", "refuted", "L1"),
    (dict(controls_differ=False), "D5", "refuted", "L1"),
    (dict(bva=None), "D5", "open", "L1"),
    (dict(bva=BvaResult(applicable=False, boundary_variable="x", note="float", full_scale_positive=True,
                        full_scale_negative=False)), "D5", "residual", "L2"),
    (dict(bva=BvaResult(applicable=True, boundary_variable="x", adjacent=False, pattern="not adjacent",
                        full_scale_positive=True, full_scale_negative=False)), "D5", "refuted", "L1"),
    (dict(info=[InfoItem(statement="p", run="positive", verdict_bearing=True, evidence_state="simulated:reference", basis="")]),
     "D6", "residual", "L2"),
    (dict(info=[InfoItem(statement="p", run="positive", verdict_bearing=True, evidence_state="simulated:fake", basis="")]),
     "D6", "residual", "L2"),
    (dict(info=[InfoItem(statement="p", run="positive", verdict_bearing=True, evidence_state="simulated:stub", basis="")]),
     "D6", "refuted", "L1"),
    (dict(info=[InfoItem(statement="x", run="negative", verdict_bearing=False, evidence_state="simulated:stub", basis="")]),
     "D6", "open", "L1"),
    (dict(probe_effect_free=None), "D7", "open", "L0"),
    (dict(probe_effect_free=False), "D7", "refuted", "invalid"),
    (dict(repeat=None), "D8", "open", "L1"),
    (dict(repeat=RepeatResult(runs=3, identical=True, distinct_hashes=1, flake_bound=1.0, trace_hash="x")), "D8", "residual", "L1"),
    (dict(repeat=RepeatResult(runs=5, identical=False, distinct_hashes=2, flake_bound=0.6, trace_hash="x")), "D8", "refuted", "L1"),
    (dict(replay=None), "D9", "open", "L1"),
    (dict(replay=ReplayResult(ok=False, detail="differs")), "D9", "refuted", "L1"),
    (dict(scale_declared=True, bva=None), "D10", "open", "L1"),
    (dict(scale_declared=True, main_positive_effect=False), "D10", "refuted", "L1"),
    (dict(target_intact=False), "D11", "refuted", "invalid"),
    (dict(stmts_changed=1, stmts_total=10), "D11", "refuted", "invalid"),
    (dict(snippet_matches=False), "D12", "refuted", "invalid"),
    (dict(scope_status="out_of_scope"), "D13", "refuted", "L3"),
    (dict(scope_status="unknown"), "D13", "residual", "L3"),
    (dict(entry_index=1), "D14", "refuted", "L1"),
    (dict(entry_index=1, entry_reason="unit under test"), "D14", "residual", "L2"),
    (dict(entry_index=None), "D14", "refuted", "L1"),
])
def test_each_defeater_and_the_level_it_allows(change, defeater, status, level):
    conf, final, st = run(ideal(**change))
    assert st[defeater] == status
    assert conf.level == level
    assert (final == "inconclusive") == (level == "invalid")
    if status != "eliminated" and defeater != "D13":
        assert any(s.startswith(defeater) for s in conf.next_steps)


def test_out_of_scope_is_flagged_but_not_scored():
    conf, _, _ = run(ideal(scope_status="out_of_scope"))
    assert "out of scope" in conf.level_note


def test_inconclusive_verdict_gets_no_level():
    conf, final, _ = run(ideal(verdict="inconclusive"))
    assert (conf.level, final) == ("n/a", "inconclusive")


def test_no_verdict_is_only_reported_when_the_oracle_was_shown_to_see_the_effect():
    ok, final, _ = run(ideal(verdict="no", controls_differ=False, bva=None))
    assert final == "no" and ok.level in ("L2", "L3")
    for mut, state in ((MutationResult(generated=4, killed=2, wilson_lower=0.15), "refuted"),     # oracle misses mutants
                       (MutationResult(generated=2, killed=2, wilson_lower=0.34), "residual"),    # too few mutants to say
                       (None, "open")):                                                           # mutation not run
        conf, final, st = run(ideal(verdict="no", controls_differ=False, bva=None, mutation=mut))
        assert st["D3"] == state and final == "inconclusive" and conf.level == "n/a", state
        assert "needs the oracle shown to see the effect" in conf.level_note and state in conf.level_note
    # a `yes` is not held to this rule: the effect itself was observed
    conf, final, st = run(ideal(verdict="yes", mutation=MutationResult(generated=2, killed=2, wilson_lower=0.34)))
    assert final == "yes" and st["D3"] == "residual" and conf.level == "L1"


def test_level_is_deterministic():
    a = C.build(ideal(), P)[0].model_dump()
    b = C.build(ideal(), P)[0].model_dump()
    assert a == b


def test_profile_thresholds_are_used():
    strict = Profile(kill_lb=0.9)
    conf, _ = C.build(ideal(), strict)
    assert {d.id: d.status for d in conf.defeaters}["D3"] == "refuted" and conf.level == "L1"
    many = Profile(n_rep=10)
    conf, _ = C.build(ideal(), many)
    assert {d.id: d.status for d in conf.defeaters}["D8"] == "residual"
    assert conf.profile.n_rep == 10


def test_worst_state():
    assert C.worst_state([]) == "direct"
    assert C.worst_state(["direct", "simulated:fake", "simulated:reference"]) == "simulated:fake"
    assert C.worst_state(["simulated:fake", "simulated:stub"]) == "simulated:stub"


def test_stats():
    assert wilson_lower(4, 4) == pytest.approx(0.5101, abs=1e-3)
    assert wilson_lower(3, 4) == pytest.approx(0.3006, abs=1e-3)
    assert wilson_lower(0, 0) == 0.0 and wilson_lower(0, 5) == 0.0
    assert wilson_lower(50, 100) < 0.5 < wilson_lower(50, 100, z=0.5) + 0.2
    assert rule_of_three(30) == pytest.approx(0.1) and rule_of_three(1) == 1.0 and rule_of_three(0) == 1.0
