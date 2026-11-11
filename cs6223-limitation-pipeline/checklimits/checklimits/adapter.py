"""Finding -> Limitation -> Region lookup, and witness_hint -> inputs (PLAN.md section 7).

Only the two witness_hint shapes that exist in the pilot data are implemented:
  flat dict                      {"batch_size": 2, "q_len": 4096}            -> input_value
  call_1, call_2, ... of dicts   {"call_1": {...}, "call_2": {...}}          -> event_sequence
Anything else (mixed keys, call_N that are not dicts) raises ValueError.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import PIPELINE_ROOT

if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from schema.models import Finding, Limitation, Region  # noqa: E402

_CALL_KEY = re.compile(r"^call_(\d+)$")


def witness_to_inputs(hint: dict[str, Any] | None) -> tuple[str, list[dict[str, Any]]]:
    """Return (witness_type, inputs). witness_type is a `schema.models.WitnessType` value."""
    if not hint:
        raise ValueError("finding has no witness_hint")
    call_keys = [k for k in hint if _CALL_KEY.match(k)]
    if not call_keys:
        return "input_value", [dict(hint)]
    if len(call_keys) != len(hint):
        raise ValueError(f"witness_hint mixes call_N keys with other keys: {sorted(hint)}")
    if not all(isinstance(hint[k], dict) for k in call_keys):
        raise ValueError("every call_N value must be a dict")
    ordered = sorted(call_keys, key=lambda k: int(_CALL_KEY.match(k).group(1)))
    return "event_sequence", [dict(hint[k]) for k in ordered]


@dataclass
class Task:
    finding: Finding
    limitations: list[Limitation]
    regions: list[Region]
    witness_type: str
    inputs: list[dict[str, Any]]
    notes: list[str] = field(default_factory=list)

    def region(self, region_id: str) -> Region:
        for r in self.regions:
            if r.region_id == region_id:
                return r
        raise KeyError(f"{region_id} is not linked to {self.finding.finding_id}")


def _load_list(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{path} is not a JSON list")
    return data


def load_task(finding_id: str, data_dir: Path) -> Task:
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
    wtype, inputs = witness_to_inputs(finding.witness_hint)
    return Task(finding, lims, regs, wtype, inputs, notes)
