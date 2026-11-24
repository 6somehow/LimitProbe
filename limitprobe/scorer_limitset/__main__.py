import argparse
import json
from pathlib import Path

from .scoring import FakeJudge, RelayJudge, read_jsonl, score


def main():
    parser = argparse.ArgumentParser(description="Score reference coverage")
    for arg in ("pred", "root", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--splits", type=Path)
    parser.add_argument("--dataset", choices=("limitset", "limitset2"), default="limitset")
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--labels-en", type=Path)
    parser.add_argument("--judge", choices=("relay", "fake"), default="relay")
    parser.add_argument("--model", default="x-test-2")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    judge = FakeJudge() if args.judge == "fake" else RelayJudge(args.root, args.model, args.temperature)
    labels = read_jsonl(args.labels or (args.root / "labels/test_labels.jsonl" if args.dataset == "limitset" else Path("data/limitset2/labels.jsonl")))
    if args.dataset == "limitset" and not args.splits:
        parser.error("--splits is required for limitset")
    splits = json.loads(args.splits.read_text(encoding="utf-8")) if args.splits else {"validation": [], "test": list(dict.fromkeys(label["case_id"] for label in labels))}
    label_schema = json.loads((args.root / "schemas/label.schema.json").read_text(encoding="utf-8"))
    prediction_schema = json.loads((args.root / "schemas/prediction.schema.json").read_text(encoding="utf-8"))
    if args.dataset == "limitset2":
        prediction_schema.get("properties", {}).get("case_id", {})["pattern"] = r"^LS2-[0-9]+$"
        label_schema = {"type": "object", "required": ["case_id", "label_id", "category_code"],
                        "properties": {key: {"type": "string", "minLength": 1}
                                       for key in ("case_id", "label_id", "category_code")}}
    result = score(labels, read_jsonl(args.pred),
                   splits, judge,
                   label_schema, prediction_schema, workers=args.workers, labels_en=read_jsonl(args.labels_en) if args.labels_en else None)
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
        if any("labels" in v for v in groups.values()):
            lines.extend(["", "| Group | Labels found / available | Wilson 95% |", "| --- | --- | --- |"] )
            for name, values in groups.items():
                v = values["labels"]
                lines.append(f"| {name} | {v['covered']}/{v['total']} | {v['wilson_95']} |")
        lines.append("")
    (args.out / "score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
