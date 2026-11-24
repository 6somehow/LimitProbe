#!/usr/bin/env python3
"""Per-entry summary of out/routes: regions, LLM changes, failures, cost, stability."""
import json
from pathlib import Path

from pydantic import TypeAdapter

from codeside.evaluate import stability
from schema.models import Region

ROOT = Path(__file__).resolve().parents[1] / "out/routes"
LOAD = TypeAdapter(list[Region]).validate_json


def regions(p):
    return LOAD(p.read_text())


print("entry | A | B final | added | edges | failed | calls | tokens/run | sec/run | B jaccard | direct")
for d in sorted(p for p in ROOT.glob("*/*") if p.is_dir()):
    h = sorted(d.glob("hybrid_run?.json"))
    m = [json.loads(p.with_suffix(".meta.json").read_text()) for p in h]
    print(" | ".join(map(str, [
        f"{d.parent.name}/{d.name}"[:42], len(regions(d / "static.json")), [len(regions(p)) for p in h],
        [x["added_regions"] for x in m],
        [len(x["edges"]["accepted"]) for x in m], [len(x["failed_calls"]) for x in m], [x["llm_calls"] for x in m],
        sum(x["prompt_tokens"] + x["completion_tokens"] for x in m) // max(len(m), 1),
        round(sum(x["seconds"] for x in m) / max(len(m), 1)),
        round(stability([regions(p) for p in h])["regions_jaccard"], 2) if h else "-",
        [len(regions(p)) for p in sorted(d.glob("direct_run?.json"))]])))
