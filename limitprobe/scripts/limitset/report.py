"""Generate Markdown reports from scored cases and checklimits records."""
import argparse
import json
from pathlib import Path

from confidence_limitset import score_confidence, wilson_interval


def cell(value):
    if value is None:
        return "unknown"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\n", " ")


def coverage(cases, key):
    groups = {}
    for case in cases:
        groups.setdefault(case.get(key) or "unknown", []).append(case.get("found"))
    rows = []
    for name, values in sorted(groups.items()):
        known = [value for value in values if value is not None]
        if any(type(value) is not bool for value in known):
            raise ValueError("found must be true, false or null")
        n, found = len(known), sum(known)
        ci = wilson_interval(found, n)
        rows.append(f"| {cell(key)} | {cell(name)} | {found}/{n} | {cell(ci)} | {len(values)-n} |")
    return rows


def render_report(cases, records, reproducibility=None, title="Limitations"):
    lines = [f"# {cell(title)}", "", "## Summary", "", f"Cases: {len(cases)}; limits reported: {len(records)}. Extra findings are candidate novel limits for triage.",
             "", "## Coverage", "", "Reference limits found / scored reference limits; 95% Wilson intervals. Unknown oracle results are excluded.", "",
             "| Group | Value | Found / n | 95% CI | No oracle |", "|---|---|---:|---|---:|"]
    lines += coverage(cases, "category") + coverage(cases, "split")
    lines += ["", "## Per-limit", "", "| Claim | Category | Evidence | Confidence and items | Defeaters | Disclosure |", "|---|---|---|---|---|---|"]
    for record in records:
        finding = record.get("finding") or record
        scored = score_confidence(record, record.get("repeat_results"), record.get("cross_source"), record.get("code_available", True))
        entries = [finding.get("summary") or finding.get("claim"), finding.get("category"), record.get("evidence"),
                   f"{scored['band']} ({scored['label']}): {json.dumps(scored['items'], ensure_ascii=False, sort_keys=True)}",
                   scored["items"]["open_defeaters"], finding.get("disclosure", finding.get("disclosure_status"))]
        lines.append("| " + " | ".join(cell(x) for x in entries) + " |")
    lines += ["", "## Threats to validity", "", "The testset has 17 cases and one reference limit per case, with no negative examples. An LLM judge can err; paper-only cases lack code execution. Coverage is not precision or accuracy.",
              "", "## Reproducibility", "", "Record commit SHAs, model IDs, seeds, and input/output hashes:", "", f"`{cell(reproducibility or {})}`", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", required=True, help="score JSON with cases")
    parser.add_argument("--records", required=True, help="JSON mapping case IDs to report records")
    parser.add_argument("--out", required=True, help="output directory")
    args = parser.parse_args()
    score = json.loads(Path(args.score).read_text(encoding="utf-8"))
    records = json.loads(Path(args.records).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cases = score["cases"]
    all_records = [record for case in cases for record in records.get(case["case_id"], [])]
    (out / "SUMMARY.md").write_text(render_report(cases, all_records, score.get("reproducibility"), "Case summary"), encoding="utf-8")
    for case in cases:
        case_id = case["case_id"]
        if not case_id or Path(case_id).name != case_id or case_id in {".", ".."}:
            raise ValueError("case_id must be a single safe path component")
        destination = out / case_id
        destination.mkdir(exist_ok=True)
        (destination / "LIMITATIONS.md").write_text(render_report([case], records.get(case_id, []), score.get("reproducibility"), case_id), encoding="utf-8")


if __name__ == "__main__":
    main()
