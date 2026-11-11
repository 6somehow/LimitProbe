"""Finding -> Limitation -> Region lookup, and witness_hint -> inputs (PLAN.md section 7).

Two input sources, chosen by the manifest:

  pilot data (data_dir = data/pilot_flexprefill)
      draft_findings.json + gold_code_limitations.json + gold_regions.json. Finding ids F01..F07.
      witness_hint is flat ({"batch_size": 2}) or call_1, call_2, ... of dicts.

  step 4 output (findings_file = results/step4/<artifact>/limitations_for_tests.json, schema 0.2.0)
      one record per Finding with its Limitations and Verifications embedded; ids like flexprefill-F014.
      witness_hint is `witness-v2`: kind input_value | event_sequence, status, `trigger` (the
      boundary point that takes the restricted branch), `contrast` (the nearest point that does not),
      `atoms` (what each name is: input | local | derived | predicate | category) and `aliases`.
      Step 4 does not emit Regions. A Region is built from the code-side Limitation: location from
      `code_evidence[0]`, condition from `condition`, call chain = [entry point, function] because the
      real call graph between them is not part of the hand-off.

Mixed or unknown witness_hint shapes raise ValueError.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .models import PIPELINE_ROOT

if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from schema.models import Condition, Finding, Limitation, Outcome, Provenance, Region  # noqa: E402

_CALL_KEY = re.compile(r"^call_(\d+)$")
_OUTCOME = {"reject": "reject", "path_change": "fallback", "state": "state_dependent"}


@dataclass
class Witness:
    """Normalised view of a witness_hint."""
    kind: str                                   # input_value | event_sequence
    format: str                                 # flat | calls | witness-v2
    trigger: Optional[dict[str, Any]] = None    # the point that should show the effect
    contrast: Optional[dict[str, Any]] = None   # the neighbouring point that should not (v2 only)
    status: str = "given"
    input_keys: set[str] = field(default_factory=set)   # names a driver can take as direct inputs
    aliases: dict[str, str] = field(default_factory=dict)
    atoms: dict[str, Any] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)


def parse_witness(hint: dict[str, Any] | None) -> Witness:
    if not hint:
        raise ValueError("finding has no witness_hint")
    if hint.get("format") == "witness-v2":
        atoms = hint.get("atoms") or {}
        trig = hint.get("trigger")
        # names a driver can take directly: kind input / local (a local variable has an alias that derives it
        # from an input). Derived values (q.shape[1]), predicates and categories need to be constructed.
        keys = {k for k, a in atoms.items() if a.get("kind") in ("input", "local")} if atoms else set(trig or {})
        return Witness(kind=hint.get("kind", "input_value"), format="witness-v2", trigger=trig,
                       contrast=hint.get("contrast"), status=hint.get("status", "unknown"), input_keys=keys,
                       aliases=hint.get("aliases") or {}, atoms=atoms)
    call_keys = [k for k in hint if _CALL_KEY.match(k)]
    if not call_keys:
        return Witness(kind="input_value", format="flat", trigger=dict(hint), input_keys=set(hint))
    if len(call_keys) != len(hint):
        raise ValueError(f"witness_hint mixes call_N keys with other keys: {sorted(hint)}")
    if not all(isinstance(hint[k], dict) for k in call_keys):
        raise ValueError("every call_N value must be a dict")
    ordered = sorted(call_keys, key=lambda k: int(_CALL_KEY.match(k).group(1)))
    return Witness(kind="event_sequence", format="calls", calls=[dict(hint[k]) for k in ordered])


def witness_to_inputs(hint: dict[str, Any] | None) -> tuple[str, list[dict[str, Any]]]:
    """Return (witness_type, inputs). witness_type is a `schema.models.WitnessType` value."""
    w = parse_witness(hint)
    if w.format == "calls":
        return "event_sequence", w.calls
    ins = [w.trigger] if w.trigger is not None else []
    if w.format == "witness-v2" and w.contrast is not None:
        ins.append(w.contrast)
    if w.kind == "event_sequence":
        return "event_sequence", ins
    return "input_value", ins


@dataclass
class Task:
    finding: Finding
    limitations: list[Limitation]
    regions: list[Region]
    witness_type: str
    inputs: list[dict[str, Any]]
    witness: Witness
    notes: list[str] = field(default_factory=list)
    verifications: list[dict[str, Any]] = field(default_factory=list)
    source: str = "pilot"

    def region(self, region_id: str) -> Region:
        for r in self.regions:
            if r.region_id == region_id:
                return r
        raise KeyError(f"{region_id} is not linked to {self.finding.finding_id}")

    @property
    def trigger(self) -> dict[str, Any]:
        """Positive witness values as a flat dict (empty for call sequences)."""
        return self.witness.trigger or {}


def _load_list(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{path} is not a JSON list")
    return data


def region_from_limitation(lim: Limitation, entry_points: list[str]) -> Optional[Region]:
    """Step 4 hands over Limitations, not Regions. Build one for a code-side Limitation with a location."""
    if not lim.code_evidence or lim.origin != "code":
        return None
    loc = lim.code_evidence[0]
    cond = lim.condition or Condition(expr=lim.condition_text, params=[], path_prefix=[])
    entry = entry_points[0] if entry_points else (loc.function or "")
    chain = [entry] if not loc.function or loc.function == entry else [entry, loc.function]
    return Region(region_id=(lim.region_ids[0] if lim.region_ids else lim.limitation_id), artifact_id=lim.artifact_id,
                  entry_point=entry, condition=cond, outcome=Outcome(_OUTCOME.get(lim.effect_type, "suspicious")),
                  outcome_detail=lim.effect_text, location=loc, call_chain=chain, provenance=Provenance.ast,
                  notes="built from the Limitation by checklimits.adapter (step 4 does not emit Regions)")


def load_task_step4(finding_id: str, findings_file: Path, artifact_file: Path) -> Task:
    data = json.loads(findings_file.read_text())
    recs = {r["finding_id"]: r for r in data["findings"]}
    if finding_id not in recs:
        raise KeyError(f"no finding {finding_id} in {findings_file}")
    rec = dict(recs[finding_id])
    lims_raw, vers = rec.pop("limitations", []), rec.pop("verifications", [])
    finding = Finding.model_validate(rec)
    lims = [Limitation.model_validate(l) for l in lims_raw]
    entry_points = json.loads(artifact_file.read_text()).get("entry_points", []) if artifact_file.exists() else []
    regions, notes = [], []
    for lim in lims:
        r = region_from_limitation(lim, entry_points)
        if r is None:
            notes.append(f"limitation {lim.limitation_id} ({lim.origin}) has no code location: no Region")
        elif r.region_id not in {x.region_id for x in regions}:
            regions.append(r)
    w = parse_witness(finding.witness_hint)
    wtype, inputs = witness_to_inputs(finding.witness_hint)
    if w.status not in ("solved", "solved_contrast_outside_scope", "always", "trigger_only", "given"):
        notes.append(f"witness status is {w.status!r}: the step 4 solver gave no usable trigger/contrast pair")
    return Task(finding, lims, regions, wtype, inputs, w, notes, vers, source="step4")


def load_task(finding_id: str, data_dir: Path, findings_file: Optional[Path] = None) -> Task:
    if findings_file is not None:
        return load_task_step4(finding_id, findings_file, data_dir / "artifact.json")
    findings = [Finding.model_validate(d) for d in _load_list(data_dir / "draft_findings.json")]
    limitations = {l.limitation_id: l for l in
                   (Limitation.model_validate(d) for d in _load_list(data_dir / "gold_code_limitations.json"))}
    regions = {r.region_id: r for r in
               (Region.model_validate(d) for d in _load_list(data_dir / "gold_regions.json"))}
    finding = next((f for f in findings if f.finding_id == finding_id), None)
    if finding is None:
        raise KeyError(f"no finding {finding_id} in {data_dir}")
    lims, regs, notes = [], [], []
    for lid in finding.limitation_ids:
        lim = limitations.get(lid)
        if lim is None:
            notes.append(f"limitation {lid} not found")
            continue
        lims.append(lim)
        for rid in lim.region_ids:
            if rid in regions and regions[rid] not in regs:
                regs.append(regions[rid])
            elif rid not in regions:
                notes.append(f"region {rid} not found")
    w = parse_witness(finding.witness_hint)
    wtype, inputs = witness_to_inputs(finding.witness_hint)
    return Task(finding, lims, regs, wtype, inputs, w, notes)
