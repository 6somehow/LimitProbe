"""Coverage-primary scoreboard for the test split.

Coverage = number of papers with at least a partial diagnosis / 4. Core and weighted
scores are reported as secondary metrics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WEIGHT = {"core": 2, "partial": 1, "miss": 0}


def load(mapping_path: Path, grades_dir: Path) -> dict:
    mapping = json.loads(mapping_path.read_text())
    rows = mapping.get("cells", []) if isinstance(mapping, dict) else mapping
    out = {}
    for row in rows:
        if row.get("state") != "complete" or "report_id" not in row:
            continue
        grade_path = Path(grades_dir) / f"{row['report_id']}.json"
        if grade_path.is_file():
            out[(row["paper"], row["condition"])] = json.loads(grade_path.read_text())["match"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", nargs=3, action="append", metavar=("NAME", "MAPPING", "GRADES"),
                        required=True)
    parser.add_argument("--papers", nargs="+", required=True)
    parser.add_argument("--conditions", nargs="+", default=["gap_receipt_swarm", "api_once"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    samples = []
    for name, mapping, grades in args.sample:
        samples.append((name, load(Path(mapping), Path(grades))))
    lines = ["| sample | condition | coverage | core | partial | miss | weighted |",
             "|---|---|---|---|---|---|---|"]
    for name, rows in samples:
        for condition in args.conditions:
            values = [rows.get((paper, condition), "miss") for paper in args.papers]
            coverage = sum(v != "miss" for v in values)
            core = sum(v == "core" for v in values)
            partial = sum(v == "partial" for v in values)
            weighted = sum(WEIGHT[v] for v in values)
            lines.append(f"| {name} | {condition} | **{coverage}/4** | {core} | {partial} | "
                         f"{4 - core - partial} | {weighted} |")
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")


if __name__ == "__main__":
    main()
