"""Recompute every item of AgentForm.claims from the run artifacts (SCORECARD section 1, principle 3).

Item meanings (harness side):
  target_reached              the positive run executed Region.location
  decision_outcomes_seen      set of {"true","false"} outcomes of the target decision over both runs
  condition_true_on_positive  Region.condition (or the agent's predicate) evaluated True at the target, positive run
  condition_false_on_negative same expression evaluated False at the target, negative run
  positive_observed / negative_observed
                              compared as (exception type, line); "no exception at :L" means no
                              exception raised at line L; without a line it means no exception at all
None means "not evaluable" (expression raised on the captured locals, or no hit); the claim must
then also be None.
"""
from __future__ import annotations

import re
from typing import Optional

from .models import AgentForm, AuditItem, AuditResult, Observation

_EXC = re.compile(r"^\s*([A-Za-z_]\w*)\s+(?:raised\s+)?at\s+\S*?:(\d+)", re.I)
_NOEXC = re.compile(r"^\s*no\s+(?:exception|error|assertion)\b(?:.*?at\s+\S*?:(\d+))?", re.I)


def parse_observed(text: str) -> tuple[str, Optional[str], Optional[int]]:
    """('exc', type, line) | ('none', None, line or None) | ('unparsed', None, None)"""
    m = _NOEXC.match(text)
    if m:
        return "none", None, int(m.group(1)) if m.group(1) else None
    m = _EXC.match(text)
    if m:
        return "exc", m.group(1), int(m.group(2))
    return "unparsed", None, None


def _line_of(raised_at: Optional[str]) -> Optional[int]:
    if raised_at and ":" in raised_at:
        try:
            return int(raised_at.rsplit(":", 1)[1])
        except ValueError:
            return None
    return None


def observed_matches(claim: str, obs: Observation) -> bool:
    kind, ctype, cline = parse_observed(claim)
    exc = obs.exception
    if kind == "exc":
        return bool(obs.effect) and exc is not None and exc.type == ctype and _line_of(exc.raised_at) == cline
    if kind == "none":
        if obs.effect:
            return False
        if cline is None:
            return exc is None
        # location-scoped: no exception raised at that line (later failures elsewhere are allowed)
        return exc is None or _line_of(exc.raised_at) != cline
    return False


def cond_value(obs: Observation, want: bool) -> Optional[bool]:
    """Claim value for 'condition is `want`' on this run; None if not evaluable."""
    if not obs.target_hits:
        return False
    last = obs.target_hits[-1]
    if last.condition_value is None:
        return None
    return last.condition_value is want


def outcomes_seen(*runs: Observation) -> list[str]:
    seen = {h.outcome for r in runs for h in r.target_hits if h.outcome in ("true", "false")}
    return sorted(seen)


def audit(form: AgentForm, pos: Observation, neg: Observation) -> AuditResult:
    c = form.claims
    seen = outcomes_seen(pos, neg)
    rp, rn = cond_value(pos, True), cond_value(neg, False)
    items = [
        AuditItem(claim="target_reached", declared=c.target_reached, recomputed=pos.target_reached,
                  match=c.target_reached == pos.target_reached),
        AuditItem(claim="decision_outcomes_seen", declared=sorted(c.decision_outcomes_seen), recomputed=seen,
                  match=sorted(c.decision_outcomes_seen) == seen),
        AuditItem(claim="condition_true_on_positive", declared=c.condition_true_on_positive, recomputed=rp,
                  match=c.condition_true_on_positive == rp),
        AuditItem(claim="condition_false_on_negative", declared=c.condition_false_on_negative, recomputed=rn,
                  match=c.condition_false_on_negative == rn),
        AuditItem(claim="positive_observed", declared=c.positive_observed, recomputed=pos.observed_text,
                  match=observed_matches(c.positive_observed, pos)),
        AuditItem(claim="negative_observed", declared=c.negative_observed, recomputed=neg.observed_text,
                  match=observed_matches(c.negative_observed, neg)),
    ]
    matched = sum(i.match for i in items)
    return AuditResult(declared_checks=len(items), matched_checks=matched, rate=round(matched / len(items), 3),
                       items=items)
