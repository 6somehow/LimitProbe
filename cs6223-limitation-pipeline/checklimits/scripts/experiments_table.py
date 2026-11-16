"""Tables for EXPERIMENTS.md: earlier agent run vs the runs with the call-chain task text (c2), two repeats (r2, r3)
and the blind runs (bl). Reads scratch/agent_runs/<batch>-<finding>/agent_result.json and the archived earlier run.

  python scripts/experiments_table.py > scratch/experiments_table.md
"""
import glob
import json
from pathlib import Path

C = Path(__file__).resolve().parents[1]
RUNS = C / "scratch" / "agent_runs"
RANK = {"n/a": -2, "invalid": -1, "L0": 0, "L1": 1, "L2": 2, "L3": 3, None: -3}
SETS = {"nnsmith": [("c2n", "c2n"), ("r2n", "r2n"), ("r3n", "r3n"), ("bln", "bln")],
        "flexprefill": [("c2f", "c2f"), ("r2f", "r2f"), ("r3f", "r3f"), ("blf", "blf")]}
ARCHIVE = {"nnsmith": C / "agent_results" / "batch_nnsmith", "flexprefill": C / "agent_results" / "batch"}
COLS = ["earlier", "chain-1", "chain-2", "chain-3", "blind"]


def load(p: Path):
    f = p / "agent_result.json"
    return json.loads(f.read_text()) if f.exists() else None


def cell(r):
    if r is None:
        return "-"
    if r.get("final_verdict") is None:
        return f"no package ({r.get('tokens', 0) / 1e6:.1f}M)"
    d = r.get("defeaters", {})
    return (f"{r['final_verdict']}/{r['level']} D14={d.get('D14', '?')[:3]} D3={d.get('D3', '?')[:3]} "
            f"({r.get('tokens', 0) / 1e6:.1f}M, {r.get('wall_s', 0) / 60:.0f}min)")


def main() -> None:
    rows = []
    for art, sets in SETS.items():
        findings = sorted({p.name.split("-")[-1] for b, _ in sets for p in RUNS.glob(f"{b}-*") if p.is_dir()})
        for f in findings:
            old = next(iter(sorted(ARCHIVE[art].glob(f"{f.upper()}-*"))), None)
            rec = [load(old) if old else None] + [load(RUNS / f"{b}-{f}") for b, _ in sets]
            rows.append((art, f.upper(), rec))
    print("| finding | " + " | ".join(COLS) + " |")
    print("|---|" + "---|" * len(COLS))
    for art, f, rec in rows:
        print(f"| {art}-{f} | " + " | ".join(cell(r) for r in rec) + " |")
    # variance over the three runs with the same skill, white box
    print("\n### Repeat agreement (chain-1, chain-2, chain-3)\n")
    agree_v = agree_l = n = 0
    spread = []
    for art, f, rec in rows:
        runs = [r for r in rec[1:4] if r and r.get("final_verdict")]
        if len(runs) == 3:
            n += 1
            agree_v += len({r["final_verdict"] for r in runs}) == 1
            agree_l += len({r["level"] for r in runs}) == 1
            spread.append(max(RANK[r["level"]] for r in runs) - min(RANK[r["level"]] for r in runs))
    print(f"findings with three valid runs: {n}; same verdict in all three: {agree_v}; same level in all three: {agree_l}; "
          f"level spread (max-min rank): {spread}")
    print("\n### D14 and level by condition\n")
    print("| condition | runs with a package | D14 eliminated | level L1 | L2 | L3 | invalid/n/a |")
    print("|---|---|---|---|---|---|---|")
    for i, name in enumerate(COLS):
        rs = [r for _, _, rec in rows for r in [rec[i]] if r and r.get("final_verdict")]
        lv = [r["level"] for r in rs]
        print(f"| {name} | {len(rs)} | {sum(r['defeaters'].get('D14') == 'eliminated' for r in rs)} | {lv.count('L1')} | "
              f"{lv.count('L2')} | {lv.count('L3')} | {lv.count('invalid') + lv.count('n/a')} |")


if __name__ == "__main__":
    main()
