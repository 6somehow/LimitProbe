"""scoring.py must reproduce scoring_prototype.py on its nine sample cases (tolerance 1e-3)."""
import dataclasses

import pytest

import scoring_prototype as proto
from checklimits import scoring
from checklimits.models import EvidenceRecord

CASES = {
    "A": proto._ideal(),
    "B": proto._ideal(entry_index=None),
    "C": proto._ideal(mocks_on_path=2),
    "D": proto._ideal(oracle_tier="O1", oracle_revisions_after_first_run=2),
    "E": proto._ideal(mutants_generated=None, mutants_killed=None, runs=1, consistent_runs=1),
    "F": proto._ideal(matched_checks=3),
    "G": proto._ideal(verdict="no", mutants_killed=1),
    "H": proto._ideal(target_reached=False, decision_outcomes=0),
    "I": proto._ideal(condition_translated=True),
}


def _record(ev):
    return EvidenceRecord(**dataclasses.asdict(ev))


@pytest.mark.parametrize("name", sorted(CASES))
def test_matches_prototype(name):
    ev = CASES[name]
    ref = proto.score(ev)
    card, final_verdict = scoring.score(_record(ev))
    assert card.dims == pytest.approx(ref["dims"], abs=1e-3)
    assert card.total == pytest.approx(ref["total"], abs=1e-3)
    assert card.final == pytest.approx(ref["final"], abs=1e-3)
    assert card.form_integrity == pytest.approx(ref["form_integrity"], abs=1e-3)
    assert card.level == ref["level"]
    assert final_verdict == ref["verdict"]
    assert {k: bool(v) for k, v in card.gates.items()} == {k: bool(v) for k, v in ref["gates"].items()}


def test_documented_values():
    # SCORECARD.md section 7 table
    expect = {"A": (0.992, "high"), "B": (0.806, "medium"), "C": (0.752, "medium"), "D": (0.490, "low"),
              "E": (0.659, "medium"), "F": (0.496, "low"), "G": (0.490, "low"), "H": (0.490, "low"),
              "I": (0.919, "medium")}
    for name, (final, level) in expect.items():
        card, _ = scoring.score(_record(CASES[name]))
        assert card.final == pytest.approx(final, abs=1e-3), name
        assert card.level == level, name


def test_replay_not_run_is_not_a_failed_gate():
    ev = dataclasses.replace(proto._ideal(), replay_ok=None)
    card, fv = scoring.score(_record(ev))
    assert card.gates["G2_replay_ok"] is None
    assert card.gates_not_run == ["G2_replay_ok"]
    assert fv == "yes"
    assert card.dims["reliability"] == 0.0
    assert card.level == "medium"  # would be high if replay had been evaluated
    assert "G2_replay_ok" in card.level_note


def test_failed_gate_forces_inconclusive_and_caps():
    card, fv = scoring.score(_record(proto._ideal(target_reached=False)))
    assert fv == "inconclusive" and card.final <= 0.49 and card.level == "low"


def test_zero_runs_does_not_divide_by_zero():
    card, _ = scoring.score(_record(proto._ideal(runs=0, consistent_runs=0)))
    assert card.dims["reliability"] == 0.0
