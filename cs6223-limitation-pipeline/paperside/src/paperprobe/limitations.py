"""Paper-side limitation workstream: retrieval, grounded drafts and handoff.

Lexical hits are unreviewed candidates. Exact citations establish provenance,
not semantic truth, absence, performance, reachability, or a confirmed bug.
This entry point does not change the frozen September generation protocol.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any

from .io import file_sha256, inside, read_json, stable_id, text_sha256, write_json
from .papers import extract_paper, terms

KINDS = {"claim", "scope", "explicit_limitation", "evaluation", "assumption", "hypothesis"}
RELATIONS = {"consistent", "potential_conflict", "paper_only_located", "code_only_located", "unassessed"}
ROLES = {"support", "context", "counter"}
RULES = {
    "explicit_limitation": r"\b(limitations?|drawbacks?|cannot|unable|overhead|declin\w*|less effective)\b",
    "scope": r"\b(support\w*|only|require\w*|restrict\w*|compatible|domain)\b",
    "evaluation": r"\b(evaluat\w*|experiment\w*|latency|speedup|accuracy|sparsity ratio|success rate)\b",
    "assumption": r"\b(assum\w*|orthogonal|similar\w*|same dimension\w*|residual|head\w*)\b",
    "claim": r"\b(we (?:propose|show|find|observe)|our (?:approach|method|design)|preserv\w*|equivalent)\b",
}


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], text=True,
                            capture_output=True, timeout=20, check=False)
    if result.returncode:
        raise ValueError(f"Cannot inspect pinned repository: {repo.name}")
    return result.stdout.strip()


def verify_catalog(workspace: Path, catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Check real PDFs and clean tracked source snapshots before any extraction."""
    if catalog.get("schema_version") != "paper-limitations/1":
        raise ValueError("Unsupported limitation catalog schema")
    indexed = {}
    for paper in catalog.get("papers", []):
        pid = paper["id"]
        if not re.fullmatch(r"[a-z0-9_-]+", pid) or pid in indexed:
            raise ValueError("Invalid or duplicate paper ID")
        pdf = inside(workspace, paper["pdf_path"])
        if file_sha256(pdf) != paper["pdf_sha256"]:
            raise ValueError(f"PDF hash mismatch: {pid}")
        repo = inside(workspace, paper["repo_path"])
        if _git(repo, "rev-parse", "HEAD") != paper["repository_commit"]:
            raise ValueError(f"Repository commit mismatch: {pid}")
        if _git(repo, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError(f"Modified tracked repository source: {pid}")
        indexed[pid] = paper
    if not indexed:
        raise ValueError("No papers in catalog")
    return indexed


def retrieve_statements(paper_id: str, pages: list[dict[str, Any]],
                        excluded: list[list[int]] | None = None) -> list[dict[str, Any]]:
    """Retrieve passages with stable page offsets; never infer numerical contracts."""
    hits = []
    in_references = False
    for page in pages:
        if any(a <= page["page"] <= b for a, b in (excluded or [])):
            continue
        text = page["text"]
        # Keep offsets against the original extracted text, including line breaks.
        for match in re.finditer(r"[^.!?]+[.!?]|[^.!?]+$", text):
            raw = match.group().strip()
            if re.search(r"(?:^|\n)\s*(?:REFERENCES|References)\s*(?:\n|$)", raw):
                in_references = True
            # A separate appendix starts after a bibliography in some papers.
            if re.search(r"(?:^|\n)[A-Z]\s+(?:Limitations|Broader Impacts|Experiment Details|ARTIFACT APPENDIX)", raw):
                in_references = False
            if in_references or not 70 <= len(raw) <= 2200:
                continue
            categories = [kind for kind, pattern in RULES.items() if re.search(pattern, raw, re.I)]
            if not categories:
                continue
            offset = text.find(raw, match.start())
            # Bibliographic citations can match keywords; leave ambiguity explicit.
            hits.append({"id": stable_id("statement", paper_id, page["page"], offset, raw),
                         "paper_id": paper_id, "pdf_page": page["page"],
                         "start_offset": offset, "end_offset": offset + len(raw),
                         "quote": raw, "sha256": text_sha256(raw),
                         "candidate_kinds": categories, "level": None,
                         "scope_contract": None, "semantic_review_status": "pending",
                         "backend": "lexical_retrieval", "automatically_confirmed": False})
    return hits


def source_index(repo: Path, paths: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Index only declared components. Never import or execute a target module."""
    repo = repo.resolve()
    found: dict[str, Path] = {}
    tracked = set(_git(repo, "ls-files", "-z").split("\0"))
    for relative in paths:
        target = inside(repo, relative)
        if not target.exists():
            raise ValueError(f"Missing declared search component: {relative}")
        files = sorted(target.rglob("*")) if target.is_dir() else [target]
        for file in files:
            if not file.is_file() or file.suffix not in {".py", ".cpp", ".h", ".cu", ".md"}:
                continue
            name = file.relative_to(repo).as_posix()
            inside(repo, name)  # Reject a symlink whose target leaves this repository.
            if file.resolve() != file.absolute():
                raise ValueError(f"Symlink source cannot stand for a pinned source blob: {name}")
            if name not in tracked:
                continue
            if len(found) >= 500 and name not in found:
                raise ValueError("Search scope exceeds 500 source files; narrow the declared components")
            found[name] = file
    index, manifest = [], []
    for name, file in sorted(found.items()):
        if file.stat().st_size > 1_000_000:
            raise ValueError(f"Source file exceeds text budget: {name}")
        text = file.read_text(encoding="utf-8")
        if "\x00" in text:
            raise ValueError(f"Binary source in declared component: {name}")
        lines = text.splitlines()
        digest = file_sha256(file)
        manifest.append({"path": name, "sha256": digest, "line_count": len(lines)})
        for start in range(0, len(lines), 16):
            quote = "\n".join(lines[start:start + 24])
            index.append({"path": name, "line_start": start + 1,
                          "line_end": min(start + 24, len(lines)), "quote": quote,
                          "sha256": text_sha256(quote), "file_sha256": digest,
                          "terms": terms(quote)})
    return index, manifest


def align_candidates(index: list[dict[str, Any]], query: list[str], limit: int = 5) -> list[dict[str, Any]]:
    vocabulary = terms(" ".join(query))
    ranked = sorted(((len(vocabulary & chunk["terms"]), chunk) for chunk in index),
                    key=lambda item: (-item[0], item[1]["path"], item[1]["line_start"]))
    result = []
    for overlap, chunk in ranked:
        if overlap == 0 or len(result) >= limit:
            break
        # Avoid multiple heavily overlapping excerpts from the same source file.
        if any(c["path"] == chunk["path"] and abs(c["line_start"] - chunk["line_start"]) < 24 for c in result):
            continue
        result.append({k: v for k, v in chunk.items() if k != "terms"} |
                      {"lexical_overlap": overlap, "semantic_alignment": "unverified"})
    return result


def check_record(record: dict[str, Any], paper: dict[str, Any], pages: list[dict[str, Any]],
                 repo: Path) -> dict[str, Any]:
    """Validate citations and the handoff contract without adjudicating a finding."""
    repo = repo.resolve()
    required = {"id", "paper_id", "title", "statement", "kind", "level", "origin", "scope",
                "assessment", "paper_evidence", "code_evidence", "alignment", "handoff", "search_terms"}
    if not required <= record.keys() or record["paper_id"] != paper["id"]:
        raise ValueError("Incomplete record or wrong paper ID")
    if not re.fullmatch(r"[a-z0-9_-]+", record["id"]):
        raise ValueError("Invalid record ID")
    if (record["kind"] not in KINDS or record["level"] not in (None, 1, 2, 3)
            or (record["level"] is not None and type(record["level"]) is not int)):
        raise ValueError("Invalid kind or reasoning level")
    if record["assessment"] not in {"paper_reported", "hypothesis", "consistent_control", "counterevidence_found", "unresolved"}:
        raise ValueError("Unreviewed drafts cannot be marked confirmed")
    if record["kind"] == "hypothesis" and record["assessment"] not in {"hypothesis", "counterevidence_found", "unresolved"}:
        raise ValueError("A hypothesis cannot be promoted to a paper-reported fact")
    if not isinstance(record["scope"], str) or not record["scope"].strip():
        raise ValueError("Explicit applicability and quantifiers are required")
    for field in ("statement", "title", "origin"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"Missing {field}")
    if not isinstance(record["search_terms"], list) or not all(isinstance(q, str) for q in record["search_terms"]):
        raise ValueError("search_terms must be a list of strings")
    if not record["paper_evidence"]:
        raise ValueError("Paper-side records need primary-paper evidence")
    page_map = {p["page"]: p["text"] for p in pages}
    for evidence in record["paper_evidence"]:
        quote = evidence["quote"]
        if (evidence["role"] not in ROLES or not isinstance(quote, str) or not quote.strip()
                or quote not in page_map.get(evidence["page"], "")
                or text_sha256(quote) != evidence["sha256"]
                or evidence["paper_sha256"] != paper["pdf_sha256"]):
            raise ValueError(f"Invalid paper evidence: {record['id']}")
    for evidence in record["code_evidence"]:
        path = inside(repo, evidence["path"])
        if (repo / evidence["path"]).absolute() != path:
            raise ValueError("Symlink/alias source cannot stand for a pinned source blob")
        if _git(repo, "ls-files", "--", evidence["path"]) != evidence["path"]:
            raise ValueError("Code evidence must belong to the pinned tracked source")
        lines = path.read_text(encoding="utf-8").splitlines()
        start, end = evidence["line_start"], evidence["line_end"]
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
            raise ValueError("Code evidence has invalid line range")
        quote = "\n".join(lines[start - 1:end])
        if (evidence["role"] not in ROLES or quote != evidence["quote"]
                or file_sha256(path) != evidence["file_sha256"]
                or text_sha256(quote) != evidence["sha256"]
                or evidence["repository_commit"] != paper["repository_commit"]):
            raise ValueError(f"Invalid code evidence: {record['id']}")
    alignment = record["alignment"]
    if alignment.get("relation") not in RELATIONS or not alignment.get("rationale"):
        raise ValueError("Alignment relation and rationale are required")
    if alignment["relation"] in {"consistent", "potential_conflict"} and not record["code_evidence"]:
        raise ValueError("A two-sided relation requires code evidence")
    if alignment["relation"] == "paper_only_located" and not alignment.get("search_limitations"):
        raise ValueError("Unmapped records must disclose incomplete search; absence is not proven")
    handoff = record["handoff"]
    for field in ("variable", "controls", "observables", "comparison", "oracle_basis", "resources", "dependencies"):
        if not isinstance(handoff.get(field), str) or not handoff[field].strip():
            raise ValueError(f"Missing actionable handoff field: {field}")
    return {"record_id": record["id"], "source_checks": "passed",
            "paper_citations": len(record["paper_evidence"]), "code_citations": len(record["code_evidence"]),
            "semantic_review_status": "pending", "execution_status": "not_run",
            "confirmed_bug": False, "independent_gold_label": False}


def _csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            # Neutralize spreadsheet formulas in both authored and retrieved text.
            writer.writerow({k: ("'" + str(row.get(k, "")) if str(row.get(k, "")).startswith(("=", "+", "-", "@"))
                                  else row.get(k, "")) for k in fields})


def export_handoff(output: Path, records: list[dict[str, Any]]) -> None:
    _csv(output / "paper-limitations.csv", ["id", "paper_id", "level", "kind", "statement", "scope", "assessment", "origin"], records)
    _csv(output / "paper-to-code.csv", ["id", "paper_id", "relation", "rationale", "code_locations", "semantic_review_status", "execution_status"],
         [{"id": r["id"], "paper_id": r["paper_id"], **r["alignment"],
           "code_locations": "; ".join(f"{c['path']}:{c['line_start']}-{c['line_end']}" for c in r["code_evidence"]),
           "semantic_review_status": "pending", "execution_status": "not_run"} for r in records])
    _csv(output / "test-handoff.csv", ["id", "paper_id", "variable", "controls", "observables", "comparison", "oracle_basis", "resources", "dependencies"],
         [{"id": r["id"], "paper_id": r["paper_id"], **r["handoff"]} for r in records])
    lines = ["# Zhaopeng：论文侧 limitation 与论文→代码核验", "",
             "这些是 AI 辅助研究草稿，来源检查通过不表示独立人评、性能验证或 bug 确认。",
             "候选已经受到 proposal 和团队讨论提示影响，属于开发案例，不能充当盲测发现结果。", ""]
    for record in records:
        lines += [f"## {record['id']} · {record['title']}", "",
                  f"论文：{record['paper_id']}；推理层级：{record['level']}；类型：{record['kind']}；判断：{record['assessment']}。", "",
                  record["statement"], "", "适用范围：" + record["scope"], "",
                  "论文证据：" + "; ".join(f"PDF p.{p['page']} {p.get('locator', '')} [{p['role']}]" for p in record["paper_evidence"]), "",
                  "代码证据：" + ("; ".join(f"{c['path']}:{c['line_start']}-{c['line_end']}" for c in record["code_evidence"]) or "尚未定位相应机制"), "",
                  "双向关系：" + record["alignment"]["relation"] + "。" + record["alignment"]["rationale"], ""]
        if record["alignment"].get("search_limitations"):
            lines += ["检索边界：" + record["alignment"]["search_limitations"], ""]
        labels = {"variable": "变化变量", "controls": "保持不变", "observables": "观察量", "comparison": "拟议比较", "oracle_basis": "判定依据及限制", "resources": "运行资源", "dependencies": "交接依赖"}
        lines += [f"- {label}：{record['handoff'][field]}" for field, label in labels.items()]
        lines += ["", "独立核验：pending；目标实现运行：not_run。", ""]
    (output / "handoff.zh.md").write_text("\n".join(lines), encoding="utf-8")


def build_workstream(workspace: Path, catalog_path: Path, annotations_path: Path | None,
                     output: Path) -> dict[str, Any]:
    workspace, output = workspace.resolve(), output.resolve()
    # Do not overwrite sources, checked-in drafts, or another frozen run.
    if output == workspace or workspace.is_relative_to(output):
        raise ValueError("Output must be a dedicated artifact directory")
    catalog = read_json(catalog_path)
    papers = verify_catalog(workspace, catalog)
    annotations = read_json(annotations_path) if annotations_path else {"schema_version": "paper-limitations/1", "records": []}
    if annotations.get("schema_version") != "paper-limitations/1":
        raise ValueError("Unsupported annotation schema")
    identity = {"catalog_sha256": file_sha256(catalog_path),
                "annotations_sha256": file_sha256(annotations_path) if annotations_path else None,
                "implementation_sha256": file_sha256(Path(__file__)),
                "dependency_sha256": {name: file_sha256(Path(__file__).with_name(name)) for name in ("io.py", "papers.py")},
                "pypdf_version": version("pypdf")}
    if output.exists() and any(output.iterdir()):
        if not (output / "manifest.json").exists() or read_json(output / "manifest.json").get("inputs") != identity:
            raise ValueError("Refusing to overwrite a different or incomplete run; choose a new output directory")
    records = copy.deepcopy(annotations.get("records", []))
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)) or any(r["paper_id"] not in papers for r in records):
        raise ValueError("Duplicate record ID or unknown paper")
    output.mkdir(parents=True, exist_ok=True)
    checks, statistics, source_files = [], [], {}
    for pid, paper in papers.items():
        extract_paper(pid, inside(workspace, paper["pdf_path"]), output / pid, paper["title"])
        pages = read_json(output / pid / "pages.json")["pages"]
        statements = retrieve_statements(pid, pages, paper.get("exclude_pages", []))
        write_json(output / pid / "statement-candidates.json", statements)
        index, source_manifest = source_index(inside(workspace, paper["repo_path"]), paper["search_paths"])
        source_files[pid] = source_manifest
        for record in (r for r in records if r["paper_id"] == pid):
            checks.append(check_record(record, paper, pages, inside(workspace, paper["repo_path"])))
            record["alignment_candidates"] = align_candidates(index, record["search_terms"])
            record["semantic_review_status"] = "pending"
            record["execution_status"] = "not_run"
        statistics.append({"paper_id": pid, "pages": len(pages), "retrieved_statements": len(statements),
                           "indexed_source_files": len(source_manifest), "draft_records": sum(r["paper_id"] == pid for r in records)})
    write_json(output / "records.json", {"schema_version": "paper-limitations/1", "records": records})
    write_json(output / "source-checks.json", checks)
    export_handoff(output, records)
    manifest = {"schema_version": "paper-limitations/1", "inputs": identity, "papers": statistics,
                "source_files": source_files, "record_count": len(records),
                "assessment_counts": dict(Counter(r["assessment"] for r in records)),
                "source_checks_passed": len(checks), "independent_reviews": 0,
                "target_executions": 0, "model_invocations": 0,
                "claim": "Auditable retrieval and AI-assisted development drafts; no autonomous semantic discovery result."}
    write_json(output / "manifest.json", manifest)
    return {k: v for k, v in manifest.items() if k not in {"source_files", "inputs"}}


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--workspace", type=Path, default=Path.cwd())
    cli.add_argument("--catalog", type=Path, default=Path("workstreams/zhaopeng/catalog.json"))
    cli.add_argument("--annotations", type=Path, help="Optional AI/human draft cards; omit for paper-only retrieval")
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args(argv)
    root = args.workspace.resolve()
    def local(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else inside(root, path)
    try:
        result = build_workstream(root, local(args.catalog), local(args.annotations) if args.annotations else None,
                                  local(args.output))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"paper-limits: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
