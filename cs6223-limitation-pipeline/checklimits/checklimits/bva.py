"""Harness-run boundary value analysis (CONFIDENCE_SPEC defeater D5 and D10).

Domain testing (White & Cohen 1980; Jeng & Weyuker 1994): a boundary is tested with an ON point
(on the boundary) and OFF points (just across it). The agent chose a positive and a negative
input differing in one 'boundary variable'. The harness measures, at full witness scale and
with probe runs that stop at the target decision (tracer.StopProbe):

  * the positive and negative input at full scale (are the effects the same as in the scaled run?),
  * the neighbours of the negative input at distance probe_step on both sides.

The negative input is adjacent to the boundary if at least one neighbour shows the effect.
Both sides showing the effect means the no-effect region is a single point (a '!=' guard).
Probe runs are never used for the verdict.
"""
from __future__ import annotations

from typing import Any, Optional

from .models import AgentForm, BvaProbe, BvaResult


def full_scale_inputs(inputs: dict[str, Any], scale, hint: Optional[dict[str, Any]], positive: bool) -> dict[str, Any]:
    if scale is None:
        return dict(inputs)
    out = dict(inputs)
    for k in scale.scaled:
        if positive and hint and k in hint:
            out[k] = hint[k]
        elif isinstance(inputs.get(k), (int, float)):
            out[k] = int(round(inputs[k] / scale.factor))
    return out


def plan(form: AgentForm, hint: Optional[dict[str, Any]], probe_step: int
         ) -> tuple[list[tuple[str, dict[str, Any]]], Optional[str], str]:
    """Return (cases, boundary variable if adjacency is measurable else None, reason if not)."""
    d = form.design
    pos_full = full_scale_inputs(d.positive_input, d.scale, hint, True)
    neg_full = full_scale_inputs(d.negative_input, d.scale, hint, False)
    cases = [("pos_full", pos_full), ("neg_full", neg_full)]
    diff = sorted(k for k in set(d.positive_input) | set(d.negative_input)
                  if d.positive_input.get(k) != d.negative_input.get(k))
    b = d.boundary_variable
    if diff != [b]:
        return cases, None, f"inputs differ in {diff}, not only in the boundary variable {b!r}"
    v = neg_full.get(b)
    if not isinstance(v, int) or isinstance(v, bool):
        return cases, None, f"boundary variable {b!r} is not an integer (value {v!r})"
    cases += [("neg+", {**neg_full, b: v + probe_step}), ("neg-", {**neg_full, b: v - probe_step})]
    return cases, b, ""


def evaluate(boundary_var: str, effects: dict[str, Optional[bool]], inputs: dict[str, dict[str, Any]],
             measurable: bool, reason: str) -> BvaResult:
    probes = [BvaProbe(label=k, inputs=inputs[k], effect=effects.get(k)) for k in ("neg+", "neg-") if k in inputs]
    res = BvaResult(applicable=measurable, boundary_variable=boundary_var,
                    full_scale_positive=effects.get("pos_full"), full_scale_negative=effects.get("neg_full"),
                    neighbours=probes, note=reason)
    if not measurable:
        return res
    eff = [effects.get("neg+"), effects.get("neg-")]
    if any(e is None for e in eff):
        res.note = "a neighbour probe failed before the target was decided"
        return res
    res.adjacent = any(eff)
    res.pattern = ("effect on both sides: the no-effect region is a single point (a '!=' style guard)" if all(eff) else
                   "effect on one side: the negative input sits on a half-space boundary" if any(eff) else
                   "no effect on either side: the negative input is NOT adjacent to the effect region")
    return res
