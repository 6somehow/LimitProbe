"""Export the all-paper matrix: finals, grades, coverage table and manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

WEIGHT = {"core": 2, "partial": 1, "miss": 0}
PAPERS = {
    "dev": ["nnsmith", "minference", "infinigen", "sparta"],
    "test-source": ["prompt-cache", "spinquant", "kvquant", "dx100"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet_lookup(packet_dir: Path) -> dict:
    mapping = json.loads((packet_dir / "mapping.json").read_text())
    rows = mapping.get("cells", []) if isinstance(mapping, dict) else mapping
    return {(r["paper"], r["condition"]): r["report_id"] for r in rows if "report_id" in r}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--spec", nargs=5, action="append", metavar=("SPLIT", "COND", "RUN", "PACKETS", "GRADES"),
                        required=True)
    args = parser.parse_args()
    out = Path(args.out)
    for split in PAPERS:
        for condition in ("gap_receipt_swarm", "api_once", "single_agent"):
            (out / split / condition).mkdir(parents=True, exist_ok=True)
    table = {}
    manifest = []
    for split, condition, run, packets, grades in args.spec:
        lookup = packet_lookup(Path(packets))
        grades_dir = Path(grades)
        for paper in PAPERS[split]:
            ident = lookup.get((paper, condition))
            if ident is None:
                table[(split, condition, paper)] = "pending"
                continue
            grade_path = grades_dir / f"{ident}.json"
            final_path = Path(run) / "cells" / paper / condition / "final.txt"
            if not grade_path.is_file() or not final_path.is_file():
                table[(split, condition, paper)] = "pending"
                continue
            grade = json.loads(grade_path.read_text())
            table[(split, condition, paper)] = grade["match"]
            target = out / split / condition
            shutil.copy2(final_path, target / f"{paper}.txt")
            shutil.copy2(grade_path, target / f"{paper}.json")
            manifest.append({"split": split, "condition": condition, "paper": paper,
                             "match": grade["match"], "record_id": grade.get("record_id"),
                             "final_sha256": sha(final_path)})
    lines = ["| split | paper | S s7 | A | B |", "|---|---|---|---|---|"]
    for split, papers in PAPERS.items():
        for paper in papers:
            cells = [table.get((split, c, paper), "pending") for c in
                     ("gap_receipt_swarm", "api_once", "single_agent")]
            lines.append(f"| {split} | {paper} | " + " | ".join(cells) + " |")
    summary = ["", "| split | workflow | coverage | core | partial | weighted |", "|---|---|---|---|---|---|"]
    for split, papers in PAPERS.items():
        for condition in ("gap_receipt_swarm", "api_once", "single_agent"):
            values = [table.get((split, condition, p), "pending") for p in papers]
            done = [v for v in values if v != "pending"]
            coverage = sum(v != "miss" for v in done)
            summary.append(f"| {split} | {condition} | {coverage}/{len(papers)} | "
                           f"{sum(v == 'core' for v in done)} | {sum(v == 'partial' for v in done)} | "
                           f"{sum(WEIGHT.get(v, 0) for v in done)} |")
    text = "\n".join(lines + summary)
    print(text)
    (out / "matrix.md").write_text(text + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
