"""Verdict table of SCORECARD section 3.5 and oracle checks.

Effect (for Region.outcome == "reject"): an exception raised at Region.location. Only
"reject" is implemented in P1; other outcomes return inconclusive / not_run.

  positive effect | negative effect | verdict
  yes             | no              | yes            (confirmed)
  no              | no              | no             (refuted; still needs G5)
  yes             | yes             | inconclusive   (test_error: oracle too weak or wrong boundary)
  no              | yes             | inconclusive   (test_error: boundary direction reversed)
  cannot tell     | any             | inconclusive   (test_error: crashed elsewhere, timeout, import failure)
  not supported   |                 | inconclusive   (not_run)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .models import ExecResultName, Observation, OracleDecl, Tier, Verdict

_TIER_ORDER = {"O1": 1, "O2": 2, "O3": 3, "O4": 4}
_EXC_TYPE = re.compile(r"\b([A-Za-z_]\w*(?:Error|Exception))\b")


@dataclass
class VerdictResult:
    verdict: Verdict
    exec_result: ExecResultName
    reason: str


def decide(pos: Observation, neg: Observation, outcome_supported: bool = True) -> VerdictResult:
    if not outcome_supported:
        return VerdictResult("inconclusive", "not_run", pos.effect_note or "outcome type not supported")
    if pos.effect is None or neg.effect is None:
        bad = pos if pos.effect is None else neg
        return VerdictResult("inconclusive", "test_error", f"{bad.role} run: {bad.effect_note}")
    if pos.effect and not neg.effect:
        return VerdictResult("yes", "confirmed", "effect on positive input, none on negative input")
    if not pos.effect and not neg.effect:
        return VerdictResult("no", "refuted", "no effect on either input")
    if pos.effect and neg.effect:
        return VerdictResult("inconclusive", "test_error", "effect on both inputs: oracle too weak or boundary wrong")
    return VerdictResult("inconclusive", "test_error", "effect only on the negative input: boundary direction reversed")


def expected_exception_type(oracle: OracleDecl) -> Optional[str]:
    """First exception class name mentioned in the oracle spec, if any."""
    m = _EXC_TYPE.search(oracle.spec)
    return m.group(1) if m else None


def verify_tier(oracle: OracleDecl, region_location: str) -> Tier:
    """Highest tier the oracle's content supports; never above what the agent declared."""
    if oracle.type == "exception":
        has_type = expected_exception_type(oracle) is not None
        if has_type and oracle.signal_location == region_location:
            allowed = "O4"
        elif has_type:
            allowed = "O3"
        else:
            allowed = "O2"
    elif oracle.type == "path_hook":
        allowed = "O4" if oracle.signal_location == region_location else "O3"
    else:
        allowed = "O3"  # numeric / metamorphic oracles need a tolerance check not built in P1
    return allowed if _TIER_ORDER[allowed] < _TIER_ORDER[oracle.tier] else oracle.tier  # type: ignore[return-value]
