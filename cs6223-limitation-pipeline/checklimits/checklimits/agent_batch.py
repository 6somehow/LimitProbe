"""Run the agent over every step 4 Finding the harness can judge, and summarise (PLAN.md P3).

Selection: code-side Finding with a Region whose outcome the harness can judge (runner.outcome_support) and a witness
the step 4 solver actually solved. Everything else is listed with the reason it was skipped. The summary reports
distributions only: there is no ground truth for these Findings, so verdict counts are not accuracy.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from .adapter import load_task
from .agent_loop import Budget, run_agent
from .harness import RunOptions
from .models import PIPELINE_ROOT, PROJECT_ROOT
from .runner import outcome_support

USABLE_WITNESS = ("solved", "solved_contrast_outside_scope")


def select(findings_file: str, data_dir: str = "data/pilot_flexprefill", repo_rel: str = "third_party/FlexPrefill"
           ) -> tuple[list[str], dict[str, str]]:
    ff = PIPELINE_ROOT / findings_file
    ids = [r["finding_id"] for r in json.loads(ff.read_text())["findings"]]
    chosen: list[str] = []
    skipped: dict[str, str] = {}
    for fid in ids:
        t = load_task(fid, PIPELINE_ROOT / data_dir, ff)
        if not t.regions:
            skipped[fid] = "no code location (paper-side or no code evidence)"
            continue
        ok, why = outcome_support(t.regions[0], PIPELINE_ROOT / repo_rel)
        if not ok:
            skipped[fid] = why
        elif t.witness.status not in USABLE_WITNESS or not t.witness.trigger:
            skipped[fid] = f"witness status {t.witness.status!r}"
        else:
            chosen.append(fid)
    return chosen, skipped


def run_batch(findings_file: str, batch_id: str, only: Optional[list[str]] = None, skip: Optional[list[str]] = None,
              workers: int = 3, budget: Budget = Budget(), options: Optional[RunOptions] = None) -> dict[str, Any]:
    chosen, skipped = select(findings_file)
    if only:
        chosen = [c for c in chosen if c in only]
    chosen = [c for c in chosen if c not in (skip or [])]
    out = PROJECT_ROOT / "scratch" / "batches" / batch_id
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    def one(fid: str) -> dict[str, Any]:
        run_id = f"{batch_id}-{fid.split('-')[-1].lower()}"
        try:
            res = run_agent(fid, run_id, budget, options, findings_file=findings_file)
        except BaseException as e:  # a crashed run is a result, not a reason to stop the batch
            res = {"finding": fid, "run_id": run_id, "verdict": None, "level": None, "error": f"{type(e).__name__}: {e}"[:300]}
        (out / f"{run_id}.json").write_text(json.dumps(res, indent=1, default=str))
        return res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, chosen))
    summary = {"batch_id": batch_id, "selected": chosen, "skipped": skipped, "wall_s": round(time.monotonic() - t0, 1),
               "results": results}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    return summary
