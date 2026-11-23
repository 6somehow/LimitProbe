import argparse
import json
from pathlib import Path

from .scoring import FakeJudge, RelayJudge, read_jsonl, score


def main():
    parser = argparse.ArgumentParser(description="Score reference coverage")
    for arg in ("pred", "root", "splits", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--labels-en", type=Path)
    parser.add_argument("--judge", choices=("relay", "fake"), default="relay")
    parser.add_argument("--model", default="x-test-2")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    judge = FakeJudge() if args.judge == "fake" else RelayJudge(args.root, args.model, args.temperature)
    result = score(read_jsonl(args.root / "labels/test_labels.jsonl"), read_jsonl(args.pred),
                   json.loads(args.splits.read_text(encoding="utf-8")), judge,
                   json.loads((args.root / "schemas/label.schema.json").read_text(encoding="utf-8")),
                   json.loads((args.root / "schemas/prediction.schema.json").read_text(encoding="utf-8")), workers=args.workers, labels_en=read_jsonl(args.labels_en) if args.labels_en else None)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "score.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Reference coverage", "", "One observation per case; unreviewed cases are excluded. Repeats of the same case are dependent.", ""]
    for dimension, groups in result["aggregate"].items():
        lines.extend([f"## {dimension}", "", "| Group | Found / cases | Wilson 95% | Mean per-case repeat rate |", "| --- | --- | --- | --- |"])
        for name, values in groups.items():
            v = values["found"]
            lines.append(f"| {name} | {v['covered']}/{v['total']} | {v['wilson_95']} | {values['mean_per_repeat_rate']} |")
        lines.extend(["", "| Group | Field | Covered / cases | Wilson 95% |", "| --- | --- | --- | --- |"])
        for name, values in groups.items():
            for field, v in values["fields"].items():
                lines.append(f"| {name} | {field} | {v['covered']}/{v['total']} | {v['wilson_95']} |")
        lines.append("")
    (args.out / "score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
