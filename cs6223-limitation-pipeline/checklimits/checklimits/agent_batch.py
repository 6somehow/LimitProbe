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


def artifact_paths(artifact: str) -> tuple[str, str, str]:
    """(data_dir, findings_file, repo dir) of an artifact, relative to the pipeline root. The data directory is the
    one whose artifact.json has this artifact_id (FlexPrefill keeps its pilot directory `data/pilot_flexprefill`);
    the findings file is results/step4/<artifact>/limitations_for_tests.json."""
    data = None
    for p in sorted((PIPELINE_ROOT / "data").glob("*/artifact.json")):
        if json.loads(p.read_text()).get("artifact_id") == artifact:
            data = p.parent.relative_to(PIPELINE_ROOT).as_posix()
            break
    if data is None:
        raise FileNotFoundError(f"no data/*/artifact.json with artifact_id {artifact!r} (python -m pipeline init)")
    art = json.loads((PIPELINE_ROOT / data / "artifact.json").read_text())
    repo = "third_party/" + art["repo_url"].rstrip("/").split("/")[-1].removesuffix(".git")
    return data, f"results/step4/{artifact}/limitations_for_tests.json", repo


# Reason codes for a Finding the harness does not judge. They are part of the test-report contract
# (CONTRACT_TEST_REPORT.md); keep them stable.
NOT_RUN_CODES = ("no_code_location", "outcome_unsupported", "witness_unusable", "env_unavailable",
                 "input_unreadable", "not_attempted", "agent_failed", "harness_error")


def classify_finding(fid: str, data_dir: str, findings_file: str, repo_rel: str, root: Path = PIPELINE_ROOT
                     ) -> Optional[tuple[str, str]]:
    """None if the harness can judge the Finding; otherwise (reason code, reason text)."""
    ff = root / findings_file
    try:
        t = load_task(fid, root / data_dir, ff)
    except Exception as e:  # a malformed Finding is a result for that Finding, not a reason to stop
        return "input_unreadable", f"{type(e).__name__}: {e}"[:300]
    if not t.regions:
        return "no_code_location", "no code location (paper-side finding or no code evidence)"
    if not (root / repo_rel).is_dir():
        return "env_unavailable", f"repository {repo_rel} is not checked out"
    try:
        ok, why = outcome_support(t.regions[0], root / repo_rel)
    except Exception as e:
        return "input_unreadable", f"target not readable: {type(e).__name__}: {e}"[:300]
    if not ok:
        return "outcome_unsupported", why
    if t.witness.status not in USABLE_WITNESS or not t.witness.trigger:
        hint = t.finding.witness_hint or {}
        why = f" ({hint['infeasible_because']})" if hint.get("infeasible_because") else ""
        more = (": step 4 shows the condition cannot hold together with the path to the target, so the official "
                "entry cannot reach it; testing the inner function directly would not test the product"
                if t.witness.status == "infeasible" else "")
        return "witness_unusable", f"witness status {t.witness.status!r}{why}{more}"
    return None


def select(findings_file: str, data_dir: str = "data/pilot_flexprefill", repo_rel: str = "third_party/FlexPrefill"
           ) -> tuple[list[str], dict[str, str]]:
    ids = [r["finding_id"] for r in json.loads((PIPELINE_ROOT / findings_file).read_text())["findings"]]
    chosen: list[str] = []
    skipped: dict[str, str] = {}
    for fid in ids:
        c = classify_finding(fid, data_dir, findings_file, repo_rel)
        if c is None:
            chosen.append(fid)
        else:
            skipped[fid] = c[1]
    return chosen, skipped


def run_batch(findings_file: str, batch_id: str, only: Optional[list[str]] = None, skip: Optional[list[str]] = None,
              workers: int = 3, budget: Budget = Budget(), options: Optional[RunOptions] = None,
              data_dir: str = "data/pilot_flexprefill", repo_rel: str = "third_party/FlexPrefill") -> dict[str, Any]:
    chosen, skipped = select(findings_file, data_dir, repo_rel)
    if only:
        chosen = [c for c in chosen if c in only]
    chosen = [c for c in chosen if c not in (skip or [])]
    out = PROJECT_ROOT / "scratch" / "batches" / batch_id
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    def one(fid: str) -> dict[str, Any]:
        run_id = f"{batch_id}-{fid.split('-')[-1].lower()}"
        try:
            res = run_agent(fid, run_id, budget, options, findings_file=findings_file, data_dir=data_dir)
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
