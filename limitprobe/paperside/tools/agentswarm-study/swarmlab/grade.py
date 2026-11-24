"""Blinded semantic grading against the archived human reference, plus metrics."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import prompts
from .contract import parse_finding_report, parse_json
from .llm import Client
from .util import dump, load, norm, secret_env

MATCHES = {"miss": 0, "partial": 1, "core": 2}


def reference_rows(path: Path) -> dict:
    rows = {}
    for line in Path(path).read_text().splitlines():
        columns = [value.strip() for value in line.strip("|").split("|")]
        if len(columns) != 4 or not re.fullmatch(r"\d\d", columns[0]):
            continue
        case, paper, mechanism, qualifications = columns
        rows[case] = {"case": case, "paper": paper, "reference": mechanism,
                      "qualifications": qualifications}
    if not {"01", "02", "03", "04"} <= set(rows):
        raise ValueError("Reference rubric is missing a dev case")
    return rows


def report_id(root: Path, paper: str, condition: str, digest: str) -> str:
    from .util import sha
    return sha(f"{root.name}:{paper}:{condition}:{digest}".encode())[:14]


def build_packets(root: Path, out: Path, references: dict, tag: str) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    mapping = []
    for cell in sorted(Path(root).glob("cells/*/*")):
        paper, condition = cell.parent.name, cell.name
        final = cell / "final.txt"
        result = cell / "result.json"
        if not final.is_file() or not result.is_file():
            mapping.append({"paper": paper, "condition": condition, "state": "pending"})
            continue
        from .util import sha
        digest = sha(final.read_bytes())
        ident = report_id(Path(root), paper, condition, digest)
        report = parse_finding_report(final.read_text())
        records = [{k: v for k, v in record.items() if k != "status"} for record in report["records"]]
        case = next(case for case, row in references.items() if row["paper"].lower().startswith(paper.split("-")[0]))
        dump(out / f"{ident}.json", {
            "report_id": ident, "case": case, "paper": paper,
            "reference": references[case],
            "condition_hidden": True, "records": records,
            "mechanical_evidence": load(cell / "validation.json"),
            "review_fields": {"match": "miss|partial|core", "record_id": "id or null",
                              "reason": "why the single best record matches"},
            "tag": tag,
        })
        mapping.append({"paper": paper, "condition": condition, "case": case,
                        "state": "complete", "report_id": ident, "final_sha256": digest,
                        "requests": load(result).get("requests"), "tokens": load(result).get("tokens")})
    dump(out / "mapping.json", mapping)
    return {row["report_id"]: row for row in mapping if "report_id" in row}


def import_archived(study_run: Path, mapping_path: Path, out: Path, references: dict, tag: str) -> dict:
    """Turn archived baseline finals into the same blinded packet format."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    mapping = load(mapping_path)
    rows = []
    for cell in mapping["cells"]:
        if cell.get("state") != "complete":
            continue
        paper, condition = cell["paper"], cell["condition"]
        final = Path(study_run) / paper / condition / "final.txt"
        if not final.is_file():
            continue
        from .util import sha
        digest = sha(final.read_bytes())
        ident = report_id(Path(study_run), paper, condition, digest)
        try:
            report = parse_finding_report(final.read_text())
        except ValueError:
            rows.append({"paper": paper, "condition": condition, "state": "unparseable"})
            continue
        records = [{k: v for k, v in record.items() if k != "status"} for record in report["records"]]
        case = next(case for case, row in references.items() if row["paper"].lower().startswith(paper.split("-")[0]))
        dump(out / f"{ident}.json", {
            "report_id": ident, "case": case, "paper": paper,
            "reference": references[case],
            "condition_hidden": True, "records": records,
            "mechanical_evidence": {},
            "review_fields": {"match": "miss|partial|core", "record_id": "id or null", "reason": "why"},
            "tag": tag,
        })
        rows.append({"paper": paper, "condition": condition, "case": case, "state": "complete",
                     "report_id": ident, "final_sha256": digest, "tokens": cell.get("tokens")})
    dump(out / "mapping.json", rows)
    return {row["report_id"]: row for row in rows if "report_id" in row}


def grade(packet_dir: Path, grades_dir: Path, model_client: Client) -> None:
    grades_dir = Path(grades_dir)
    grades_dir.mkdir(parents=True, exist_ok=True)
    for packet_path in sorted(Path(packet_dir).glob("*.json")):
        if packet_path.name == "mapping.json":
            continue
        ident = packet_path.stem
        if (grades_dir / f"{ident}.json").exists():
            continue
        packet = load(packet_path)
        user = {
            "reference": packet["reference"],
            "records": packet["records"],
            "mechanical_evidence": packet.get("mechanical_evidence"),
        }
        response = model_client.chat(
            [{"role": "system", "content": prompts.GRADER_SYSTEM},
             {"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
            tools=[], max_tokens=4000, thinking=False,
        )
        text = response["message"].get("content") or ""
        try:
            verdict = parse_json(text)
        except ValueError:
            verdict = {"match": "miss", "record_id": None,
                       "reason": "grader produced no parsable JSON", "raw": text[:400]}
        if verdict.get("match") not in MATCHES or not verdict.get("reason"):
            raise ValueError(f"Bad grade for {ident}: {verdict}")
        ids = {record["id"] for record in packet["records"]}
        if verdict.get("record_id") and verdict["record_id"] not in ids:
            verdict["record_id"] = None
        for field in ("test_ready_ids", "supported_ids"):
            verdict[field] = [x for x in (verdict.get(field) or []) if x in ids]
        verdict.update({"report_id": ident, "final_sha256": None, "packet": packet_path.name})
        dump(grades_dir / f"{ident}.json", verdict)
        print(f"graded {ident}: {verdict['match']} {verdict.get('record_id')}", flush=True)


def summarize(packet_dirs, grades_dir: Path, baselines=("api_once", "single_agent"),
              challenger="gap_receipt_swarm") -> dict:
    rows = []
    for packet_dir in packet_dirs:
        mapping_path = Path(packet_dir) / "mapping.json"
        if not mapping_path.is_file():
            continue
        loaded = load(mapping_path)
        rows.extend(loaded.get("cells", []) if isinstance(loaded, dict) else loaded)
    by_condition: dict[str, list] = {}
    for row in rows:
        if row.get("state") != "complete":
            continue
        grade_path = Path(grades_dir) / f"{row['report_id']}.json"
        if not grade_path.exists():
            continue
        grade = load(grade_path)
        by_condition.setdefault(row["condition"], []).append({**row, "match": grade["match"],
                                                               "reason": grade["reason"]})
    summary = {"conditions": {}}
    for condition, condition_rows in by_condition.items():
        summary["conditions"][condition] = {
            "n": len(condition_rows),
            "core": sum(r["match"] == "core" for r in condition_rows),
            "partial": sum(r["match"] == "partial" for r in condition_rows),
            "miss": sum(r["match"] == "miss" for r in condition_rows),
            "rows": [{k: r.get(k) for k in ("paper", "match", "reason", "tokens")}
                     for r in condition_rows],
        }
    if challenger in by_condition:
        def score(condition_rows):
            return {r["paper"]: MATCHES[r["match"]] for r in condition_rows}

        challenger_scores = score(by_condition[challenger])
        summary["paired"] = {}
        for baseline in baselines:
            if baseline not in by_condition:
                continue
            base = score(by_condition[baseline])
            pairs = [(challenger_scores[p] - base[p]) for p in challenger_scores if p in base]
            summary["paired"][baseline] = {
                "n": len(pairs),
                "wins": sum(delta > 0 for delta in pairs),
                "losses": sum(delta < 0 for delta in pairs),
                "ties": sum(delta == 0 for delta in pairs),
                "core_delta": sum((challenger_scores[p] == 2) - (base.get(p) == 2)
                                  for p in challenger_scores if p in base),
            }
    return summary


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("packet")
    prep.add_argument("root", type=Path)
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--reference", type=Path, required=True)
    arch = sub.add_parser("import-archived")
    arch.add_argument("study_run", type=Path)
    arch.add_argument("mapping", type=Path)
    arch.add_argument("--out", type=Path, required=True)
    arch.add_argument("--reference", type=Path, required=True)
    arch.add_argument("--tag", default="archived")
    grade_p = sub.add_parser("grade")
    grade_p.add_argument("packet", type=Path)
    grade_p.add_argument("--out", type=Path, required=True)
    summ = sub.add_parser("summarize")
    summ.add_argument("packets", nargs="+", type=Path)
    summ.add_argument("--grades", type=Path, required=True)
    summ.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    references = reference_rows(Path("/Users/pp/Desktop/AgentSwarm/reference/reference-rubric-20261121.md"))
    if args.action == "packet":
        rows = build_packets(args.root, args.out, references, tag="")
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    elif args.action == "import-archived":
        rows = import_archived(args.study_run, args.mapping, args.out, references, args.tag)
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    elif args.action == "grade":
        env = secret_env()
        client = Client(env["SOCLAAS_API_KEY"],
                        env.get("SOCLAAS_BASE_URL", "https://soclaas-api.comp.nus.edu.sg/v1"),
                        archive=args.out / "requests", max_tokens=1500, timeout=300)
        grade(args.packet, args.out, client)
    else:
        dump(args.out, summarize(args.packets, args.grades))
        print(json.dumps(load(args.out), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
