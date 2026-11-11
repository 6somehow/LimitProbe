#!/usr/bin/env python3
"""Step 2 (final route B: route A + filtered sweep and agent, merged) -> step 3b, on all five artifacts.

Input is out/routes_merged/<id>/merged_run<N>.json (built by `cli merge`, see docs/06_two_routes.md).
Output goes to out/pipeline/<id>/: limitations.json, 3b.json, 3b.detail.json. verify3b caches LLM answers in
out/pipeline/<id>/llm_cache, so a stopped run resumes without paying twice.
Paper-side input is Zhaopeng's handoff package (paperside/handoffs/paper-side-v1/<id>/paper_side.json);
--paper-side-dir "" falls back to the old FlexPrefill stub. --seed-cache copies an earlier run's LLM cache, so
only prompts that changed are paid for (bindings appear in prompts, so a new paper side can change a few).
mechanism_variant regions are exported too (as path_change); route A's own mechanism regions are not.
"""
import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = {"flexprefill": "data/pilot_flexprefill/paper_side_stub.json"}


def paper_side(aid: str, a) -> str | None:
    if not a.paper_side_dir:
        return STUB.get(aid)
    p = ROOT / a.paper_side_dir / aid / "paper_side.json"
    return str(p.relative_to(ROOT)) if p.is_file() else None


def one(art_json: Path, a) -> None:
    art = json.loads(art_json.read_text())
    aid = art["artifact_id"]
    repo = f"third_party/{art['repo_url'].rstrip('/').split('/')[-1]}"
    out = ROOT / a.out_dir / aid
    out.mkdir(parents=True, exist_ok=True)
    seed = ROOT / a.seed_cache / aid / "llm_cache" if a.seed_cache else None
    if seed and seed.is_dir() and not (out / "llm_cache").exists():
        shutil.copytree(seed, out / "llm_cache")
    lims, ver = out / "limitations.json", out / "3b.json"
    py = [sys.executable, "-m"]
    subprocess.run([*py, "codeside.cli", "to-limitations", "--regions", f"out/routes_merged/{aid}/merged_run{a.run}.json",
                    "--out", str(lims), "--include-variants"], cwd=ROOT, check=True, capture_output=True)
    if ver.exists():
        print(f"[skip] {ver.relative_to(ROOT)} exists", flush=True)
        return
    cmd = [*py, "codeside.verify3b", "--limitations", str(lims), "--artifact", str(art_json),
           "--pdf", f"third_party/papers/{aid}.pdf", "--repo", repo, "--model", a.model,
           "--repeats", str(a.repeats), "--workers", str(a.workers), "--out", str(ver)]
    if paper_side(aid, a):
        cmd += ["--paper-side", paper_side(aid, a)]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = (p.stdout + p.stderr).strip().splitlines()[-2:]
    print(f"[{'ok' if p.returncode == 0 else 'FAIL'}] {aid}: {' | '.join(t[:300] for t in tail)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="x-test-2")
    ap.add_argument("--run", type=int, default=1, help="which merged run to use")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--out-dir", default="out/pipeline")
    ap.add_argument("--paper-side-dir", default="paperside/handoffs/paper-side-v1")
    ap.add_argument("--seed-cache", default="", help="earlier out dir whose llm_cache to copy, e.g. out/pipeline")
    a = ap.parse_args()
    arts = [p for p in sorted((ROOT / "data").glob("*/artifact.json"))
            if not a.only or json.loads(p.read_text())["artifact_id"] in a.only]
    with ThreadPoolExecutor(a.parallel) as pool:
        list(pool.map(lambda p: one(p, a), arts))
