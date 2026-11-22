"""Build the dev scoreboard: archived baselines plus the new condition."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES = {"nnsmith": "01", "minference": "02", "infinigen": "03", "sparta": "04"}
SYMBOL = {"core": "core", "partial": "part", "miss": "miss"}
ORDER = ["api_once", "single_agent", "plain_swarm", "evidence_gap_swarm", "gap_receipt_swarm"]


def load_rows(mapping_path: Path, grades_dir: Path) -> dict:
    mapping = json.loads(mapping_path.read_text())
    rows = mapping.get("cells", []) if isinstance(mapping, dict) else mapping
    out = {}
    for row in rows:
        if row.get("state") != "complete" or "report_id" not in row:
            continue
        grade_path = grades_dir / f"{row['report_id']}.json"
        if not grade_path.is_file():
            continue
        grade = json.loads(grade_path.read_text())
        out[(row["paper"], row["condition"])] = {
            "match": grade["match"], "reason": grade.get("reason", ""),
            "record_id": grade.get("record_id"), "tokens": row.get("tokens"),
            "requests": row.get("requests"),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-mapping", type=Path, required=True)
    parser.add_argument("--official-grades", type=Path, required=True)
    parser.add_argument("--run-mapping", type=Path)
    parser.add_argument("--run-grades", type=Path)
    parser.add_argument("--condition", default="gap_receipt_swarm")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = load_rows(args.official_mapping, args.official_grades)
    if args.run_mapping and args.run_grades:
        rows.update(load_rows(args.run_mapping, args.run_grades))
    conditions = [c for c in ORDER if any(k[1] == c for k in rows)]
    lines = ["| paper | " + " | ".join(conditions) + " |",
             "|---|" + "---|" * len(conditions)]
    for slug in CASES:
        cells = [SYMBOL.get(rows.get((slug, c), {}).get("match"), "—") for c in conditions]
        lines.append(f"| {slug} | " + " | ".join(cells) + " |")
    totals = []
    for condition in conditions:
        core = sum(rows.get((slug, condition), {}).get("match") == "core" for slug in CASES)
        part = sum(rows.get((slug, condition), {}).get("match") == "partial" for slug in CASES)
        totals.append(f"{core}/{part}")
    lines.append("| **core/partial** | " + " | ".join(totals) + " |")
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")


if __name__ == "__main__":
    main()
