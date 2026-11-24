"""Confidence profile: every threshold the level rules use, with its provenance.

Same evidence + same profile = same level (CONFIDENCE_SPEC.md section 2, item 5). The profile
used is copied into every report. Values marked 'policy' have no literature basis; they are
to be calibrated against fault-injection ground truth (CONFIDENCE_SPEC.md section 7).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "default-v1"
    n_min: int = Field(4, description="policy: fewest mutants for D3 to count as measured")
    kill_lb: float = Field(0.5, description="policy: Wilson lower bound the mutant kill rate must reach (D3)")
    n_rep: int = Field(5, description="policy: independent runs compared for D8")
    mod_max: float = Field(0.05, description="policy: share of call-chain statements that may be edited (D11)")
    wilson_z: float = Field(1.959964, description="two-sided 95 % normal quantile (Wilson 1927)")
    probe_step: int = Field(1, description="BVA: distance of the ON/OFF neighbours (integer boundary variables)")
    provenance: dict[str, str] = Field(default_factory=lambda: {
        "n_min": "policy", "kill_lb": "policy", "n_rep": "policy", "mod_max": "policy (SCORECARD.md v1 used 0.05)",
        "wilson_z": "Wilson 1927, 95 %", "probe_step": "domain testing ON/OFF points (White & Cohen 1980; Jeng & Weyuker 1994)",
    })


DEFAULT = Profile()
