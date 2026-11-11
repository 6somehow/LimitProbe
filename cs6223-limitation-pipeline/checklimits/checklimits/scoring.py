"""Scoring (SCORECARD sections 3 to 5). Mirrors scoring_prototype.py; tests/test_scoring.py
checks the nine prototype samples to within 1e-3.

Differences from the prototype, all about "not run":
  * replay_ok may be None (replay not run). Reliability is then 0, gate G2 is
    "not evaluated" (None) rather than failed, and the level cannot be "high".
  * mutants_generated None keeps the prototype behaviour: mutation = 0; for verdict "no"
    gate G5 fails.
  * The final verdict is forced to "inconclusive" only by a gate that is False.
"""
from __future__ import annotations

import math
from typing import Optional

from .models import EvidenceRecord, Scorecard, Verdict

WEIGHTS = {
    "reach": 0.15, "infect": 0.15, "oracle": 0.20, "control": 0.15,
    "mutation": 0.10, "fidelity": 0.15, "reliability": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
FLOOR = 0.05
ORACLE_TIER = {"O4": 1.0, "O3": 0.7, "O2": 0.35, "O1": 0.1}
CAP_WHEN_GATE_FAILS = 0.49


def dimension_scores(e: EvidenceRecord) -> dict[str, float]:
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
    if e.replay_ok and e.runs:
        s["reliability"] = (e.consistent_runs / e.runs) * min(1.0, e.runs / 3)
    else:
        s["reliability"] = 0.0
    return s


def gates(e: EvidenceRecord) -> dict[str, Optional[bool]]:
    g: dict[str, Optional[bool]] = {
        "G1_target_reached": e.target_reached,
        "G2_replay_ok": e.replay_ok,  # None = not run
        "G3_no_critical_modification": not e.critical_modification,
        "G4_oracle_ge_O3_and_preregistered": e.oracle_tier in ("O3", "O4") and e.preregistered,
    }
    if e.verdict == "no":
        g["G5_no_requires_infection_and_sensitive_oracle"] = (
            bool(e.cond_true_on_positive) and e.mocks_on_path == 0
            and e.mutants_generated is not None and e.mutants_killed / max(1, e.mutants_generated) >= 0.5)
    return g


def score(e: EvidenceRecord) -> tuple[Scorecard, Verdict]:
    """Return the scorecard and the final verdict (after gates)."""
    s = dimension_scores(e)
    g = gates(e)
    total = math.exp(sum(w * math.log(max(s[k], FLOOR)) for k, w in WEIGHTS.items()))
    lam = e.matched_checks / e.declared_checks if e.declared_checks else 1.0
    final = total * lam
    not_run = [k for k, v in g.items() if v is None]
    failed = [k for k, v in g.items() if v is False]
    note = ""
    if failed:
        level, final_verdict = "low", "inconclusive"
        final = min(final, CAP_WHEN_GATE_FAILS)
        note = "failed gates: " + ", ".join(failed)
    else:
        final_verdict = e.verdict
        chain_ok = min(s["reach"], s["infect"], s["oracle"], s["control"]) >= 0.7
        if final >= 0.80 and chain_ok and s["mutation"] >= 0.5 and s["fidelity"] >= 0.7:
            level = "high"
        elif final >= 0.55:
            level = "medium"
        else:
            level = "low"
        if level == "high" and not_run:
            level = "medium"
            note = "capped at medium: gates not evaluated: " + ", ".join(not_run)
        elif not_run:
            note = "gates not evaluated: " + ", ".join(not_run)
    card = Scorecard(
        dims={k: round(v, 3) for k, v in s.items()}, gates=g, gates_not_run=not_run,
        total=round(total, 3), form_integrity=round(lam, 3), final=round(final, 3), level=level,
        level_note=note)
    return card, final_verdict  # type: ignore[return-value]
