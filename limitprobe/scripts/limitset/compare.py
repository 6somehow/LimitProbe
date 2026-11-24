#!/usr/bin/env python3
"""Compare scored limitset runs without reading reference material."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scorer_limitset.scoring import wilson

CATEGORIES = ("applicability_limitation", "mechanism_origin_unclear", "method_shortcoming")


def read_jsonl(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def coverage(rows):
    available = [row for row in rows if not row.get("judge_unavailable") and row.get("found") is not None]
    result = wilson(sum(row["found"] is True for row in available), len(available))
    result["judge_unavailable"] = [row["case_id"] for row in rows if row.get("judge_unavailable")]
    result["unknown"] = [row["case_id"] for row in rows if not row.get("judge_unavailable") and row.get("found") is None]
    return result


def nested_values(obj, key):
    if isinstance(obj, dict):
        for k, value in obj.items():
            if k == key:
                yield value
            yield from nested_values(value, key)
    elif isinstance(obj, list):
        for value in obj:
            yield from nested_values(value, key)


def analyze(name, score_dir, pred_dir, split):
    score = json.loads((score_dir / "score.json").read_text(encoding="utf-8"))
    rows = [row for row in score["cases"] if row.get("split") == split]
    ids = {row["case_id"] for row in rows}
    predictions = read_jsonl(pred_dir / "predictions.jsonl") if pred_dir else []
    grouped = defaultdict(list)
    for record in predictions:
        if record.get("case_id") in ids:
            grouped[record["case_id"]].append(record)
    findings = [f for records in grouped.values() for record in records for f in record.get("findings", [])]
    # Presence is reported only when a real value is present in a finding.
    tiers = any(any(v in ("L", "A") or (isinstance(v, str) and (v.startswith("L") or v.startswith("A"))) for v in nested_values(f, key)) for f in findings for key in ("level", "tier", "evidence_level", "evidence_tier"))
    bands = any(any(v is not None and v != "" for v in nested_values(f, key)) for f in findings for key in ("confidence_band", "band"))
    costs = read_jsonl(pred_dir / "cost.jsonl") if pred_dir else []
    costs = [c for c in costs if c.get("case_id") in ids]  # Never attribute other splits to this one.
    manifest_path = pred_dir / "run_manifest.json" if pred_dir else None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path and manifest_path.exists() else {}
    def total(keys):
        values = [next((c[k] for k in keys if isinstance(c.get(k), (int, float)) and not isinstance(c[k], bool)), None) for c in costs]
        values = [v for v in values if v is not None]
        return sum(values) if values else None
    calls = total(("calls", "call_count"))
    if calls is None and costs:
        calls = len(costs)
    metrics = {"calls": calls, "prompt_tokens": total(("prompt_tokens", "input_tokens")),
               "completion_tokens": total(("completion_tokens", "output_tokens")),
               "wall_seconds": total(("wall_seconds", "elapsed_seconds", "duration_seconds"))}
    # Aggregate manifest totals are usable only when its case IDs identify exactly this split.
    if set(manifest.get("case_ids", [])) == ids and ids:
        for key in metrics:
            if metrics[key] is None and isinstance(manifest.get(key), (int, float)):
                metrics[key] = manifest[key]
    metrics["wall_seconds_per_case"] = metrics.pop("wall_seconds") / len(ids) if metrics["wall_seconds"] is not None and ids else None
    cases = {}
    for row in rows:
        repeats = row.get("repeats", [])
        known = [r for r in repeats if r.get("found") is not None and not r.get("judge_unavailable")]
        counts = [len(r.get("findings", [])) for r in grouped[row["case_id"]]]
        cases[row["case_id"]] = {"found": row.get("found"), "judge_unavailable": bool(row.get("judge_unavailable")),
            "fields": row.get("fields", {}), "stability": {"found": sum(r["found"] is True for r in known), "repeats": len(known),
            "fraction": sum(r["found"] is True for r in known) / len(known) if known else None,
            "excluded_repeats": len(repeats) - len(known)},
            "mean_findings": sum(counts) / len(counts) if counts else None}
    label_rows = [dict(label, case_id="{}:{}".format(row["case_id"], label.get("label_id", "label"))) for row in rows for label in row.get("labels", [row])]
    return {"name": name, "label_coverage": coverage(label_rows), "label_categories": {c: coverage([r for r in label_rows if r.get("category") == c]) for c in CATEGORIES}, "overall": coverage(rows), "categories": {c: coverage([r for r in rows if r.get("category") == c]) for c in CATEGORIES},
            "cases": cases, "evidence_tier_available": tiers, "confidence_band_available": bands, "cost": metrics}


def fmt(value):
    return "n/a" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)


def cov(value):
    ci = value["wilson_95"]
    return f'{value["covered"]}/{value["total"]} ({fmt(value["fraction"])}, CI {fmt(ci[0])}–{fmt(ci[1])})' if ci else f'{value["covered"]}/{value["total"]} (n/a)'


def render(report):
    lines = [f'# Limitset comparison: {report["split"]}', '', 'Coverage is found cases / available cases, with Wilson 95% confidence intervals. Judge-unavailable cases are excluded. Other unknown cases are also excluded. Confidence bands are uncalibrated; n is tiny.', '', '## Coverage', '', '| System | Overall | Judge unavailable (count: IDs) | Unknown |', '|---|---|---|---|']
    for s in report["systems"]:
        c = s["overall"]
        lines.append(f'| {s["name"]} | {cov(c)} | {len(c["judge_unavailable"])}: {", ".join(c["judge_unavailable"]) or "none"} | {", ".join(c["unknown"]) or "none"} |')
    lines += ['', '## Label coverage', '', '| System | Found / available labels | Unavailable |', '|---|---|---|']
    for s in report['systems']:
        c = s['label_coverage']
        lines.append(f'| {s["name"]} | {cov(c)} | {len(c["judge_unavailable"])} |')
    lines += ['', '## Coverage by category', '', '| System | Category | Coverage (Wilson 95% CI) | Unavailable |', '|---|---|---|---|']
    for s in report['systems']:
        for category, c in s['categories'].items():
            lines.append(f'| {s["name"]} | {category} | {cov(c)} | {len(c["judge_unavailable"])} |')
    lines += ['', '## Label coverage by category', '', '| System | Category | Found / available labels | Unavailable |', '|---|---|---|---|']
    for s in report['systems']:
        for category, c in s['label_categories'].items():
            lines.append(f'| {s["name"]} | {category} | {cov(c)} | {len(c["judge_unavailable"])} |')
    lines += ['', '## Per-case comparison', '', 'Win/loss/tie compares found status across available systems; unavailable and unknown are not ranked. Fields are those marked covered.', '', '| Case | System | Result | Found | Fields covered | Mean findings / repeat | Stability (found / available repeats) |', '|---|---|---|---|---|---|---|']
    for cid in sorted({cid for s in report['systems'] for cid in s['cases']}):
        eligible = [s['cases'][cid]['found'] for s in report['systems'] if cid in s['cases'] and not s['cases'][cid]['judge_unavailable'] and s['cases'][cid]['found'] is not None]
        for s in report['systems']:
            c = s['cases'].get(cid)
            if c is None:
                lines.append(f'| {cid} | {s["name"]} | n/a | n/a | n/a | n/a | n/a |')
                continue
            found = c['found'] if not c['judge_unavailable'] else None
            result = 'n/a' if found is None else 'tie' if len(set(eligible)) < 2 else 'win' if found else 'loss'
            fields = ', '.join(k for k, v in c['fields'].items() if v is True) or 'none'
            st = c['stability']
            lines.append(f'| {cid} | {s["name"]} | {result} | {fmt(found)} | {fields} | {fmt(c["mean_findings"])} | {st["found"]}/{st["repeats"]} ({fmt(st["fraction"])}, excluded {st["excluded_repeats"]}) |')
    lines += ['', '## Evidence capability and cost', '', 'Availability describes recorded capabilities, not quality or calibrated confidence. Costs are totals for the selected split; wall time is per case.', '', '| System | L/A tier present | Confidence band present (uncalibrated) | Calls | Prompt tokens | Completion tokens | Wall seconds / case |', '|---|---|---|---|---|---|---|']
    for s in report['systems']:
        c = s['cost']
        lines.append(f'| {s["name"]} | {s["evidence_tier_available"]} | {s["confidence_band_available"]} | {fmt(c["calls"])} | {fmt(c["prompt_tokens"])} | {fmt(c["completion_tokens"])} | {fmt(c["wall_seconds_per_case"])} |')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', action='append', required=True, metavar='NAME=SCORE_DIR[:PRED_DIR]')
    parser.add_argument('--split', choices=('validation', 'test'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    systems = []
    names = set()
    for spec in args.system:
        if '=' not in spec:
            parser.error('--system requires NAME=SCORE_DIR[:PRED_DIR]')
        name, paths = spec.split('=', 1)
        parts = paths.split(':', 1)
        if not name or name in names or not all(parts):
            parser.error('system names must be nonempty and unique, and paths nonempty')
        names.add(name)
        systems.append(analyze(name, Path(parts[0]), Path(parts[1]) if len(parts) > 1 else None, args.split))
    report = {'split': args.split, 'systems': systems}
    args.out.write_text(render(report), encoding='utf-8')
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
