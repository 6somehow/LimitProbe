#!/usr/bin/env python3
"""Union existing prediction runs without invoking a model."""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def words(finding):
    return set(re.findall(r"\w+", str(finding.get("mechanism", "")) + " " + str(finding.get("claim", "")), re.UNICODE))


def quality(finding):
    evidence = finding.get("evidence", [])
    if isinstance(evidence, dict):
        evidence = [evidence]
    quotes = sum(bool(item.get("quote")) for item in evidence if isinstance(item, dict)) if isinstance(evidence, list) else 0
    return quotes, len(str(finding.get("mechanism", "")))


def union(inputs, tags):
    runs = []
    counts = []
    cases = set()
    for path in inputs:
        by_case = defaultdict(list)
        count = 0
        try:
            with open(path, encoding="utf-8") as stream:
                for line in stream:
                    try:
                        record = json.loads(line)
                        if not isinstance(record, dict) or not isinstance(record.get("case_id"), str) or not isinstance(record.get("findings"), list):
                            continue
                        findings = [f for f in record["findings"] if isinstance(f, dict)]
                        by_case[record["case_id"]].append((record.get("repeat"), findings))
                        count += len(findings)
                    except (ValueError, TypeError):
                        continue
        except (OSError, UnicodeError) as exc:
            print(f"Warning: cannot read {path}: {exc}", file=__import__("sys").stderr)
        runs.append(by_case)
        counts.append(count)
        cases.update(by_case)
    records, origins = [], []
    for case in sorted(cases):
        repeats = max(len(run.get(case, [])) for run in runs)
        for index in range(repeats):
            merged, sources = [], []
            repeat = None
            for run, tag in zip(runs, tags):
                entries = run.get(case, [])
                if not entries:
                    continue
                entry_repeat, findings = entries[index % len(entries)]
                if repeat is None:
                    repeat = entry_repeat
                for original in findings:
                    finding = dict(original)
                    conditions = finding.get("conditions", [])
                    finding["conditions"] = conditions if isinstance(conditions, list) else ([] if conditions is None else [conditions])
                    tokens = words(finding)
                    tokens = {token.lower() for token in tokens}
                    match = None
                    for i, existing in enumerate(merged):
                        other = {token.lower() for token in words(existing)}
                        if tokens and other and len(tokens & other) / len(tokens | other) >= 0.6:
                            match = i
                            break
                    if match is None:
                        merged.append(finding)
                        sources.append([tag])
                    else:
                        if tag not in sources[match]:
                            sources[match].append(tag)
                        if quality(finding) > quality(merged[match]):
                            merged[match] = finding
            records.append({"case_id": case, "repeat": repeat if repeat is not None else index, "findings": merged})
            origins.append({"case_id": case, "repeat": records[-1]["repeat"], "findings": sources})
    return records, origins, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="inputs", action="append", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label-tag", action="append", default=[], metavar="INPUT=NAME")
    args = parser.parse_args()
    labels = {}
    for label in args.label_tag:
        if "=" not in label:
            parser.error("--label-tag requires INPUT=NAME")
        key, value = label.split("=", 1)
        labels[key] = value
    tags = [labels.get(path, labels.get(Path(path).stem, path)) for path in args.inputs]
    records, origins, counts = union(args.inputs, tags)
    output = Path(args.out)
    with output.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    output.with_suffix(".origins.json").write_text(json.dumps(origins, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"items_per_input": [{"input": path, "origin_system": tag, "items": count} for path, tag, count in zip(args.inputs, tags, counts)], "merged_count": sum(len(r["findings"]) for r in records)}
    output.with_suffix(".summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
