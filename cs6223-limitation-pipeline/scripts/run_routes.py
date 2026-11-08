#!/usr/bin/env python3
"""Run route A once and route B (plus the direct-LLM control) N times on every artifact entry.

Results go to out/routes/<artifact>/<entry>/; existing files are kept, so a stopped run can resume.
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOTS = {"infinigen": ["speedup/infinigen", "speedup/flexgen"]}


def jobs(runs, only):
    for f in sorted((ROOT / "data").glob("*/artifact.json")):
        a = json.loads(f.read_text())
        if only and a["artifact_id"] not in only:
            continue
        repo = f"third_party/{a['repo_url'].rstrip('/').split('/')[-1]}"
        roots = [x for r in PACKAGE_ROOTS.get(a["artifact_id"], []) for x in ("--package-root", r)]
        for entry in a["entry_points"]:
            d = Path("out/routes") / a["artifact_id"] / re.sub(r"\W+", "_", entry.split("::")[1])
            base = ["--repo", repo, "--entry", entry, "--artifact", a["artifact_id"], *roots]
            yield ["extract", *base, "--out", str(d / "static.json")]
            for i in range(1, runs + 1):
                yield ["extract-hybrid", *base, "--model", MODEL, "--out", str(d / f"hybrid_run{i}.json")]
                yield ["extract-llm", *base, "--model", MODEL, "--out", str(d / f"direct_run{i}.json")]


def run(cmd):
    out = ROOT / cmd[cmd.index("--out") + 1]
    if out.exists():
        return
    p = subprocess.run([sys.executable, "-m", "codeside.cli", *cmd], cwd=ROOT, capture_output=True, text=True)
    tail = (p.stdout + p.stderr).strip().splitlines()[-1:] or [""]
    print(f"[{'ok' if p.returncode == 0 else 'FAIL'}] {out.relative_to(ROOT)}: {tail[0][:200]}", flush=True)


def agent_jobs(runs, only, cmd="extract-agent", out="out/routes_agent", name="agent"):
    """The agent explores a whole repo, so it runs once per artifact rather than per entry."""
    for f in sorted((ROOT / "data").glob("*/artifact.json")):
        a = json.loads(f.read_text())
        if only and a["artifact_id"] not in only:
            continue
        roots = [x for r in PACKAGE_ROOTS.get(a["artifact_id"], []) for x in ("--package-root", r)]
        entries = [x for e in a["entry_points"] for x in ("--entry", e)]
        for i in range(1, runs + 1):
            yield [cmd, "--repo", f"third_party/{a['repo_url'].rstrip('/').split('/')[-1]}", *entries,
                   "--artifact", a["artifact_id"], "--paper", a["paper_title"], *roots, "--model", MODEL,
                   "--out", f"{out}/{a['artifact_id']}/{name}_run{i}.json"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--mode", choices=["routes", "agent", "sweep"], default="routes")
    a = ap.parse_args()
    MODEL = a.model
    with ThreadPoolExecutor(a.parallel) as pool:
        todo = {"routes": lambda: jobs(a.runs, a.only), "agent": lambda: agent_jobs(a.runs, a.only),
                "sweep": lambda: agent_jobs(a.runs, a.only, "extract-sweep", "out/routes_sweep", "sweep")}[a.mode]()
        list(pool.map(run, todo))
