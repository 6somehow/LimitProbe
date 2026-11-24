"""Blinded human review export and conservative task-level aggregation.

Static checks are never promoted to human scores. Missing ratings remain pending.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from .review_ui import render_review_html

CRITERIA = (
    "scope_relevance", "code_alignment", "input_concreteness",
    "strategy_appropriateness", "observation_clarity", "oracle_design",
)
QUALIFICATION_CRITERIA = CRITERIA[:5]
CSV_FIELDS = ("review_id", "reviewer_id", *CRITERIA, "reason")
SCORES = {"", "yes", "no", "unknown"}
CANDIDATE_FIELDS = (
    "strategy", "inputs", "preconditions", "target_condition", "observation",
    "paper_evidence", "code_evidence", "oracle", "scope_status", "limitations",
)
BLINDING_NOTES = {
    "display_normalization": "展示层将未提供论文范围对齐的状态统一显示为 unknown，以避免暴露生成方法标签；原始 results 数据保持不变。",
    "limitations": "候选原文措辞、限制说明和证据数量仍可能暗示生成方法；保留这些语义信息，盲审存在这种限制。",
}


class ReviewContractError(ValueError):
    """Malformed run or review data; never silently discard records."""


def _dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewContractError(f"{name} must be a nonempty string")
    return value


def _read_run(run_path: Path) -> dict:
    path = run_path / "results.json" if run_path.is_dir() else run_path
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReviewContractError("results.json must be an object")
    _identifier(data.get("run_id"), "run_id")
    methods = data.get("methods")
    if not isinstance(methods, list) or not methods or any(not isinstance(method, str) for method in methods) or len(set(methods)) != len(methods):
        raise ReviewContractError("methods must be a nonempty list of unique names")
    for method in methods:
        _identifier(method, "method")
    if not isinstance(data.get("tasks"), list):
        raise ReviewContractError("tasks must be a list")
    if not isinstance(data.get("metadata", {}), dict):
        raise ReviewContractError("metadata must be an object")
    if not isinstance(data.get("metadata", {}).get("paper_references", {}), dict):
        raise ReviewContractError("metadata.paper_references must map paper IDs to references")
    candidate_cap = data.get("metadata", {}).get("max_candidates", 5)
    if type(candidate_cap) is not int or not 1 <= candidate_cap <= 5:
        raise ReviewContractError("metadata.max_candidates must be an integer between 1 and 5")
    seen = set()
    task_papers = {}
    for task in data["tasks"]:
        if not isinstance(task, dict):
            raise ReviewContractError("each task must be an object")
        task_id = _identifier(task.get("task_id"), "task_id")
        _identifier(task.get("paper_id"), "paper_id")
        if task_id in task_papers and task_papers[task_id] != task["paper_id"]:
            raise ReviewContractError(f"task_id maps to different papers: {task_id}")
        task_papers[task_id] = task["paper_id"]
        method = _identifier(task.get("method"), "task.method")
        _identifier(task.get("status"), "task.status")
        if method not in methods:
            raise ReviewContractError(f"undeclared method: {method}")
        if (task_id, method) in seen:
            raise ReviewContractError(f"duplicate task/method: {task_id}/{method}")
        seen.add((task_id, method))
        candidates = task.get("candidates")
        if not isinstance(candidates, list) or len(candidates) > candidate_cap:
            raise ReviewContractError(f"task.candidates must be a list with at most {candidate_cap} items")
        ids = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise ReviewContractError("candidate must be an object")
            cid = _identifier(candidate.get("candidate_id"), "candidate_id")
            if cid in ids:
                raise ReviewContractError(f"duplicate candidate_id within task: {cid}")
            ids.add(cid)
            if candidate.get("paper_id", task["paper_id"]) != task["paper_id"]:
                raise ReviewContractError(f"candidate paper_id differs from task: {cid}")
    task_ids = {task["task_id"] for task in data["tasks"]}
    for method in methods:
        present = {task["task_id"] for task in data["tasks"] if task["method"] == method}
        if present != task_ids:
            raise ReviewContractError(f"missing task records for {method}: {sorted(task_ids - present)}; preserve failed tasks with empty candidates")
    return data


def _index_run(results: dict) -> tuple[list[dict], dict, list[dict]]:
    items, mapping, manifest = [], {}, []
    for task in results["tasks"]:
        material = json.dumps([results["run_id"], task["task_id"], task["method"]], ensure_ascii=False)
        anonymous_task = "task-" + hashlib.sha256(material.encode()).hexdigest()[:16]
        ids = []
        for candidate in task["candidates"]:
            public_candidate = {key: candidate.get(key) for key in CANDIDATE_FIELDS}
            if public_candidate.get("scope_status") == "code_only":
                public_candidate["scope_status"] = "unknown"
            content = json.dumps(public_candidate, ensure_ascii=False, sort_keys=True)
            rid = "review-" + hashlib.sha256((material + "\0" + candidate["candidate_id"] + "\0" + content).encode()).hexdigest()[:20]
            mapping[rid] = {
                "task_id": task["task_id"], "paper_id": task["paper_id"],
                "method": task["method"], "candidate_id": candidate["candidate_id"],
                "anonymous_task_id": anonymous_task,
            }
            items.append({
                "review_id": rid, "paper_id": task["paper_id"],
                "candidate": public_candidate,
                "source_reference": results.get("metadata", {}).get("paper_references", {}).get(task["paper_id"], {}),
                "execution_status": "not_executed_in_this_review",
            })
            ids.append(rid)
        manifest.append({
            "anonymous_task_id": anonymous_task, "paper_id": task["paper_id"],
            "status": task["status"], "candidate_count": len(ids), "review_ids": ids,
        })
    return items, mapping, manifest


def export_review_pack(run_path: Path, output_dir: Path, seed: int = 0) -> dict:
    """Export portable blinded HTML, blank CSV, source items, and private mapping."""
    run_path, output_dir = Path(run_path), Path(output_dir)
    results = _read_run(run_path)
    items, mapping, manifest = _index_run(results)
    random.Random(seed).shuffle(items)
    random.Random(seed).shuffle(manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "reviews.csv"
    preserve_csv = False
    if csv_path.exists():
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            existing = list(csv.DictReader(stream))
        has_ratings = any(any(row.get(field, "") for field in (*CRITERIA, "reason", "reviewer_id")) for row in existing)
        if has_ratings:
            if {row.get("review_id") for row in existing} != set(mapping):
                raise ReviewContractError("existing reviews.csv has ratings for different candidate content; export to a new directory")
            preserve_csv = True
    _dump(output_dir / "review-items.json", {"schema_version": "1.0", "run_id": results["run_id"], "export_metadata": {"blinding": BLINDING_NOTES}, "items": items})
    _dump(output_dir / "run-manifest.json", {
        "run_id": results["run_id"], "task_count": len(manifest), "tasks": manifest,
        "candidate_cap_per_task": results.get("metadata", {}).get("max_candidates", 5),
        "human_review_status": "pending", "export_metadata": {"blinding": BLINDING_NOTES},
    })
    _dump(output_dir / "private" / "blinding-map.json", {"run_id": results["run_id"], "items": mapping})
    if not preserve_csv:
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows({"review_id": item["review_id"]} for item in items)
    (output_dir / "reviewer.html").write_text(render_review_html(items, results["run_id"]), encoding="utf-8")
    return {
        "run_id": results["run_id"], "task_count": len(manifest), "candidate_count": len(items),
        "human_review_status": "pending", "reviewer_html": str(output_dir / "reviewer.html"),
        "review_items": str(output_dir / "review-items.json"), "reviews_csv": str(output_dir / "reviews.csv"),
        "private_mapping": str(output_dir / "private" / "blinding-map.json"),
        "export_metadata": {"blinding": BLINDING_NOTES},
    }


def _review_rows(path: Path, run_id: str) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not set(CSV_FIELDS).issubset(reader.fieldnames):
                raise ReviewContractError(f"missing CSV fields: {path}")
            return list(reader)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            if data.get("run_id") != run_id:
                raise ReviewContractError(f"review run_id mismatch: {path}")
            rows = data.get("reviews")
        else:
            raise ReviewContractError("JSON review must include run_id and reviews")
        if not isinstance(rows, list):
            raise ReviewContractError("JSON reviews must be a list")
        return rows
    raise ReviewContractError(f"review file must be .csv or .json: {path}")


def _normalize_review(row: dict, known_ids: set[str]) -> dict | None:
    if not isinstance(row, dict):
        raise ReviewContractError("review row must be an object")
    if not isinstance(row.get("review_id"), str) or row["review_id"] not in known_ids:
        raise ReviewContractError(f"unknown review_id: {row.get('review_id')}")
    normalized = {"review_id": row["review_id"]}
    for field in (*CRITERIA, "reviewer_id", "reason"):
        value = row.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ReviewContractError(f"{field} must be text")
        normalized[field] = value.strip().lower() if field in CRITERIA else value.strip()
    for field in CRITERIA:
        if normalized[field] not in SCORES:
            raise ReviewContractError(f"invalid score {field}={normalized[field]!r}")
    has_score = any(normalized[field] for field in CRITERIA)
    if not normalized["reviewer_id"]:
        if has_score or normalized["reason"]:
            raise ReviewContractError("filled review must have reviewer_id")
        return None
    return normalized


def _resolve(values: list[str], required: int) -> str:
    values = [value for value in values if value]
    if "yes" in values and "no" in values:
        return "conflict"
    if "unknown" in values:
        return "unknown"
    if len(values) < required:
        return "pending"
    return values[0] if values else "pending"


def _fingerprint(candidate: dict) -> str:
    # Only exact duplicates are removed automatically; semantic duplicates require review.
    fields = ("strategy", "inputs", "preconditions", "target_condition", "observation")
    return json.dumps({key: candidate.get(key) for key in fields}, ensure_ascii=False, sort_keys=True)


def aggregate_reviews(run_path: Path, review_files: list[Path], output_dir: Path) -> dict:
    """Aggregate independent scores with fixed task denominators and pending bounds."""
    results = _read_run(Path(run_path))
    items, mapping, manifest = _index_run(results)
    required = results.get("metadata", {}).get("reviewers_required", 2)
    if not isinstance(required, int) or isinstance(required, bool) or required < 2:
        raise ReviewContractError("reviewers_required must be an integer >= 2")
    normalized = {}
    for path in map(Path, review_files):
        for raw in _review_rows(path, results["run_id"]):
            row = _normalize_review(raw, set(mapping))
            if row is None:
                continue
            key = row["review_id"], row["reviewer_id"]
            if key in normalized and normalized[key] != row:
                raise ReviewContractError(f"conflicting duplicate review/reviewer: {key}")
            normalized[key] = row
    per_id = {rid: [] for rid in mapping}
    for row in normalized.values():
        per_id[row["review_id"]].append(row)
    candidates, agreement = [], {field: {"agree": 0, "compared": 0} for field in CRITERIA}
    full_coverage = True
    for item in items:
        rid, rows = item["review_id"], per_id[item["review_id"]]
        verdicts = {}
        for field in CRITERIA:
            values = [row[field] for row in rows if row[field]]
            full_coverage &= len(values) >= required
            verdicts[field] = _resolve(values, required)
            for i, left in enumerate(values):
                for right in values[i + 1:]:
                    agreement[field]["compared"] += 1
                    agreement[field]["agree"] += int(left == right)
        qvalues = [verdicts[field] for field in QUALIFICATION_CRITERIA]
        if all(value == "yes" for value in qvalues):
            status = "qualified"
        elif "no" in qvalues:
            status = "unqualified"
        elif "conflict" in qvalues:
            status = "conflict"
        elif "unknown" in qvalues:
            status = "unknown"
        else:
            status = "pending"
        candidates.append({
            "review_id": rid, **mapping[rid], "qualification_status": status,
            "criteria": verdicts, "reviewer_count": len(rows), "reviews": rows,
        })
    by_id = {candidate["review_id"]: candidate for candidate in candidates}
    task_summaries = []
    for task, entry in zip(results["tasks"], manifest):
        q, unresolved = set(), set()
        for candidate, rid in zip(task["candidates"], entry["review_ids"]):
            fingerprint = _fingerprint(candidate)
            status = by_id[rid]["qualification_status"]
            if status == "qualified":
                q.add(fingerprint)
            elif status not in {"unqualified"}:
                unresolved.add(fingerprint)
        upper = len(q | unresolved)
        completion = "yes" if q else ("no" if upper == 0 else "unknown")
        task_summaries.append({
            "task_id": task["task_id"], "paper_id": task["paper_id"], "method": task["method"],
            "generation_status": task["status"], "candidate_count": len(task["candidates"]),
            "qualified_yield_lower": len(q), "qualified_yield_upper": upper,
            "completion": completion, "review_ids": entry["review_ids"],
        })
    method_summaries = {}
    for method in results["methods"]:
        tasks = [task for task in task_summaries if task["method"] == method]
        method_candidates = [candidate for candidate in candidates if candidate["method"] == method]
        count = len(tasks)
        yes = sum(task["completion"] == "yes" for task in tasks)
        possible = sum(task["completion"] != "no" for task in tasks)
        method_summaries[method] = {
            "task_count": count, "candidate_count": len(method_candidates),
            "generation_status_counts": dict(Counter(task["generation_status"] for task in tasks)),
            "qualification_status_counts": dict(Counter(candidate["qualification_status"] for candidate in method_candidates)),
            "qualified_yield_lower": sum(task["qualified_yield_lower"] for task in tasks),
            "qualified_yield_upper": sum(task["qualified_yield_upper"] for task in tasks),
            "task_completion_lower": yes / count if count else None,
            "task_completion_upper": possible / count if count else None,
            "criteria_counts": {field: dict(Counter(candidate["criteria"][field] for candidate in method_candidates)) for field in CRITERIA},
        }
    scored_rows = sum(any(row[field] for field in CRITERIA) for row in normalized.values())
    human_status = ("no_candidates" if not items else
                    "not_started" if not scored_rows else "complete" if full_coverage else "partial")
    paired_tasks = {}
    for task in task_summaries:
        paired_tasks.setdefault(task["task_id"], {})[task["method"]] = {
            "lower": task["qualified_yield_lower"], "upper": task["qualified_yield_upper"],
        }
    pairs = []
    for task_id, methods in paired_tasks.items():
        if "full" in methods:
            for baseline in ("code_only", "direct"):
                if baseline in methods:
                    a, b = methods["full"], methods[baseline]
                    pairs.append({"task_id": task_id, "comparison": f"full - {baseline}",
                                  "difference_lower": a["lower"] - b["upper"],
                                  "difference_upper": a["upper"] - b["lower"]})
    summary = {
        "schema_version": "1.0", "run_id": results["run_id"], "backend": results.get("backend"),
        "mode": results.get("mode"), "human_review_status": human_status,
        "evaluation_condition": "demonstration_only" if results.get("backend") == "heuristic" else "human_review_of_generated_specifications",
        "human_conclusions_available": bool(items) and human_status == "complete" and not any(
            verdict in {"unknown", "conflict"} for candidate in candidates for verdict in candidate["criteria"].values()),
        "required_reviewers": required, "review_row_count": len(normalized),
        "task_count": len(task_summaries), "candidate_count": len(candidates),
        "tasks": task_summaries, "candidates": candidates, "methods": method_summaries,
        "pairwise_agreement": agreement, "paired_yield_differences": pairs,
        "static_checks": {"human_scores": False, "records": [
            {"review_id": rid, "checks": candidate.get("checks", {})}
            for task, entry in zip(results["tasks"], manifest)
            for candidate, rid in zip(task["candidates"], entry["review_ids"])
        ]},
        "limitations": ["未执行真实被测软件；静态检查不证明可达性或正确性。",
                        "待审、unknown 和冲突保留；上下界不是置信区间。",
                        "自动去重仅处理完全相同的测试意图字段；语义重复仍需人工核查。"],
    }
    output_dir = Path(output_dir)
    _dump(output_dir / "evaluation.json", summary)
    from .reporting import write_run_report
    write_run_report(summary, output_dir / "evaluation.md")
    write_run_report(summary, output_dir / "evaluation.html")
    return summary
