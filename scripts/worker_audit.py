"""Audit what each worker role actually delivered, per run."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from swarmlab.contract import parse_json  # noqa: E402


def audit(run_dirs):
    rows = []
    for run in run_dirs:
        for handoff_path in sorted(Path(run).glob("cells/*/gap_receipt_swarm/handoff.json")):
            paper = handoff_path.parts[-3]
            for handoff in json.loads(handoff_path.read_text()):
                for worker in handoff["workers"]:
                    raw = worker.get("raw_text") or ""
                    verdict = counts = None
                    question_answered = None
                    try:
                        data = parse_json(raw)
                        verdict = data.get("verdict")
                        counts = data.get("counts")
                        question_answered = data.get("question_answered")
                    except ValueError:
                        verdict = "no-json"
                    rows.append({
                        "run": Path(run).name, "paper": paper,
                        "worker": worker["worker"],
                        "turns": worker.get("turns"),
                        "verdict": verdict,
                        "answered": question_answered,
                        "counts": counts,
                        "raw_candidates": worker.get("raw_candidate_count"),
                        "parsed": worker.get("parsed"),
                        "repairs": worker.get("repairs"),
                    })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = audit(args.runs)
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    if args.out:
        args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    by_verdict = {}
    for row in rows:
        by_verdict[row["verdict"]] = by_verdict.get(row["verdict"], 0) + 1
    print("verdicts:", by_verdict, "| with candidates:", sum(bool(r["raw_candidates"]) for r in rows), "/", len(rows))


if __name__ == "__main__":
    main()
