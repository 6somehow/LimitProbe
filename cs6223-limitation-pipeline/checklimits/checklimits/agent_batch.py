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


def reaudit(root: Path, out: Path, workers: int = 3, options: Optional[RunOptions] = None) -> dict[str, Any]:
    """Run the harness again on archived agent packages (no agent involved), e.g. after a rule or operator change.

    root/<name>/attempt/ and root/<name>/agent_result.json (the earlier outcome) are read; fresh oracle locks are used."""
    import tempfile
    from .harness import run_attempt

    options = options or RunOptions()
    dirs = sorted(d for d in root.iterdir() if (d / "attempt" / "manifest.json").exists())
    out.mkdir(parents=True, exist_ok=True)

    def one(d: Path) -> dict[str, Any]:
        before = json.loads((d / "agent_result.json").read_text()) if (d / "agent_result.json").exists() else {}
        row: dict[str, Any] = {"name": d.name, "finding": before.get("finding"), "before_verdict": before.get("final_verdict"),
                               "before_level": before.get("level"), "before_defeaters": before.get("defeaters", {})}
        try:
            with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "scratch") as td:
                r = run_attempt(d / "attempt", options=options, locks_dir=Path(td))["report"]
            row.update({"after_verdict": r.final_verdict, "after_level": r.confidence.level,
                        "after_defeaters": {x.id: x.status for x in r.confidence.defeaters},
                        "mutation": (r.checks.mutation.model_dump(include={"generated", "killed", "wilson_lower"})
                                     if r.checks.mutation else None), "error": None})
        except Exception as e:
            row.update({"after_verdict": None, "after_level": None, "after_defeaters": {}, "mutation": None,
                        "error": f"{type(e).__name__}: {e}"[:300]})
        return row

    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(one, dirs))
    (out / "reaudit.json").write_text(json.dumps(rows, indent=1, default=str))
    return {"rows": rows}
