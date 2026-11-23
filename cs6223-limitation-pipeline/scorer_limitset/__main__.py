import argparse
import json
from pathlib import Path

from .scoring import FakeJudge, RelayJudge, read_jsonl, score


def main():
    parser = argparse.ArgumentParser(description="Score reference coverage")
    for arg in ("pred", "root", "splits", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--judge", choices=("relay", "fake"), default="relay")
    parser.add_argument("--model", default="x-test-2")
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    judge = FakeJudge() if args.judge == "fake" else RelayJudge(args.root, args.model, args.temperature)
    result = score(read_jsonl(args.root / "labels/test_labels.jsonl"), read_jsonl(args.pred),
                   json.loads(args.splits.read_text(encoding="utf-8")), judge)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "score.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Reference coverage", "", "Each case-repeat is an observation; unsubmitted cases are unreviewed.", ""]
    for dimension, groups in result["aggregate"].items():
        lines.extend([f"## {dimension}", "", "| Group | Found | Total | Wilson 95% |", "| --- | ---: | ---: | --- |"])
        for name, values in groups.items():
            v = values["found"]
            lines.append(f"| {name} | {v['covered']} | {v['total']} | {v['wilson_95']} |")
        lines.append("")
    (args.out / "score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
