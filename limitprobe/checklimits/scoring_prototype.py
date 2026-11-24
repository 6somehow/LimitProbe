"""Reference implementation of the check_limits confidence score (PROTOTYPE).

Pure stdlib. Mirrors SCORECARD.md. Weights and thresholds are initial values to be
calibrated with fault injection; they are design choices, not literature values.

Run:  python scoring_prototype.py
"""
from __future__ import annotations

import math
from dataclasses import dataclass

WEIGHTS = {
    "reach": 0.15, "infect": 0.15, "oracle": 0.20, "control": 0.15,
    "mutation": 0.10, "fidelity": 0.15, "reliability": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

FLOOR = 0.05
ORACLE_TIER = {"O4": 1.0, "O3": 0.7, "O2": 0.35, "O1": 0.1}


@dataclass
class Evidence:
    """Harness-verified measurements (never taken from the agent without audit)."""
    # reachability
    target_reached: bool
    decision_outcomes: int            # distinct outcomes of the target predicate seen: 0, 1 or 2
    # infection
    cond_true_on_positive: bool | None    # None = condition not evaluable
    cond_false_on_negative: bool | None
    condition_translated: bool        # True if agent-written predicate was used (Region expr not evaluable)
    # oracle
    oracle_tier: str                  # O1..O4
    preregistered: bool
    oracle_revisions_after_first_run: int
    # control pair
    controls_differ: bool
    differing_factors: int            # number of input factors that differ between positive and negative
    boundary_adjacent: bool | None    # None = unknown / non-ordered factor
    # mutation (None = not run)
    mutants_generated: int | None
    mutants_killed: int | None
    # fidelity
    critical_modification: bool       # target statement or its predicate edited
    modified_stmt_ratio: float        # semantic edits / statements in call_chain functions
    mocks_on_path: int
    mocks_off_path: int
    entry_index: int | None           # index in Region.call_chain of the function the test calls; None = snippet
    call_chain_len: int
    probe_effect_free: bool           # True if no hook, or outcome identical with and without hook
    # reliability
    replay_ok: bool
    runs: int
    consistent_runs: int
    # form audit
    declared_checks: int
    matched_checks: int
    # context
    verdict: str                      # yes | no


def dimension_scores(e: Evidence) -> dict[str, float]:
    s: dict[str, float] = {}
    s["reach"] = 0.5 * e.target_reached + 0.5 * (e.decision_outcomes / 2)
    s["infect"] = (0.5 * bool(e.cond_true_on_positive) + 0.5 * bool(e.cond_false_on_negative)) \
        * (0.6 if e.condition_translated else 1.0)
    s["oracle"] = ORACLE_TIER[e.oracle_tier] * max(0.0, 1 - 0.25 * e.oracle_revisions_after_first_run)
    if not e.controls_differ:
        s["control"] = 0.0
    else:
        base = {1: 1.0, 2: 0.7}.get(e.differing_factors, 0.4)
        s["control"] = base * (1.0 if e.boundary_adjacent else 0.8)
    if e.mutants_generated:
        s["mutation"] = (e.mutants_killed / e.mutants_generated) * min(1.0, e.mutants_generated / 3)
    else:
        s["mutation"] = 0.0
    s_mod = max(0.0, 1 - e.modified_stmt_ratio / 0.05)
    s_mock = max(0.0, 1 - 0.4 * e.mocks_on_path - 0.05 * e.mocks_off_path)
    if e.entry_index is None:
        s_entry = 0.25
    elif e.call_chain_len <= 1:
        s_entry = 1.0
    else:
        s_entry = 1 - e.entry_index / (e.call_chain_len - 1)
    s["fidelity"] = s_mod * s_mock * s_entry * (1.0 if e.probe_effect_free else 0.0)
    s["reliability"] = (1.0 if e.replay_ok else 0.0) * (e.consistent_runs / e.runs) * min(1.0, e.runs / 3)
    return s


def gates(e: Evidence) -> dict[str, bool]:
    g = {
        "G1_target_reached": e.target_reached,
        "G2_replay_ok": e.replay_ok,
        "G3_no_critical_modification": not e.critical_modification,
        "G4_oracle_ge_O3_and_preregistered": e.oracle_tier in ("O3", "O4") and e.preregistered,
    }
    if e.verdict == "no":
        g["G5_no_requires_infection_and_sensitive_oracle"] = (
            bool(e.cond_true_on_positive) and e.mocks_on_path == 0
            and e.mutants_generated is not None and e.mutants_killed / max(1, e.mutants_generated) >= 0.5)
    return g


def score(e: Evidence) -> dict:
    s = dimension_scores(e)
    g = gates(e)
    # weighted geometric mean: a weak link cannot be hidden by strong dimensions
    total = math.exp(sum(w * math.log(max(s[k], FLOOR)) for k, w in WEIGHTS.items()))
    lam = e.matched_checks / e.declared_checks if e.declared_checks else 1.0
    final = total * lam
    if not all(g.values()):
        level, final_verdict = "low", "inconclusive"
        final = min(final, 0.49)
    else:
        final_verdict = e.verdict
        chain_ok = min(s["reach"], s["infect"], s["oracle"], s["control"]) >= 0.7
        if final >= 0.80 and chain_ok and s["mutation"] >= 0.5 and s["fidelity"] >= 0.7:
            level = "high"
        elif final >= 0.55:
            level = "medium"
        else:
            level = "low"
    return {"dims": {k: round(v, 3) for k, v in s.items()}, "gates": g,
            "total": round(total, 3), "form_integrity": round(lam, 3),
            "final": round(final, 3), "level": level, "verdict": final_verdict}


def _ideal(**kw) -> Evidence:
    base = dict(
        target_reached=True, decision_outcomes=2, cond_true_on_positive=True, cond_false_on_negative=True, condition_translated=False,
        oracle_tier="O4", preregistered=True, oracle_revisions_after_first_run=0,
        controls_differ=True, differing_factors=1, boundary_adjacent=True,
        mutants_generated=4, mutants_killed=4, critical_modification=False, modified_stmt_ratio=0.0,
        mocks_on_path=0, mocks_off_path=1, entry_index=0, call_chain_len=1, probe_effect_free=True,
        replay_ok=True, runs=3, consistent_runs=3, declared_checks=6, matched_checks=6, verdict="yes")
    base.update(kw)
    return Evidence(**base)


if __name__ == "__main__":
    cases = {
        "A ideal (F01-like, 1 off-path mock)": _ideal(),
        "B snippet only": _ideal(entry_index=None),
        "C two on-path mocks": _ideal(mocks_on_path=2),
        "D LLM-judged oracle, 2 post-hoc revisions": _ideal(oracle_tier="O1", oracle_revisions_after_first_run=2),
        "E ideal but no mutation, 1 run": _ideal(mutants_generated=None, mutants_killed=None, runs=1, consistent_runs=1),
        "F ideal but agent form wrong on 3/6 checks": _ideal(matched_checks=3),
        "G 'no' verdict, mutation kills 1/4": _ideal(verdict="no", mutants_killed=1),
        "H target not reached": _ideal(target_reached=False, decision_outcomes=0),
        "I condition via agent-written predicate (F03-like)": _ideal(condition_translated=True),
    }
    for name, ev in cases.items():
        r = score(ev)
        failed = [k for k, v in r["gates"].items() if not v]
        print(f"{name:46s} total={r['total']:.3f} final={r['final']:.3f} level={r['level']:6s} "
              f"verdict={r['verdict']:12s} failed_gates={failed}")
