"""Audit recorded batch inputs and costs without rating candidate quality."""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from .io import read_json, text_sha256, write_json


def _status(checks: list[dict]) -> str:
    return "fail" if any(c["status"] == "fail" for c in checks) else "unknown" if any(c["status"] == "unknown" for c in checks) else "pass"


def _number(value: Any, integer: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if integer and type(value) is not int:
        return False
    return value >= 0 and (isinstance(value, int) or math.isfinite(value))


def _load(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return read_json(path), None
    except (OSError, ValueError) as error:
        return None, f"unreadable: {error}"


def _same(left: Any, right: Any) -> bool:
    # Preserve JSON value types: Python considers True == 1, whereas changing
    # a numeric threshold to a boolean changes the experimental context.
    return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(right, ensure_ascii=False, sort_keys=True)


def audit_run(run_path: Path, output_dir: Path | None = None) -> dict:
    """Check the frozen task matrix, arm fairness, provenance and shared-call costs.

    Missing evidence is unknown; contradictory recorded evidence is fail. This
    function does not execute the target software or assign any human rating.
    """
    run_path = Path(run_path).resolve()
    run_dir = run_path.parent if run_path.is_file() else run_path
    result_path = run_path if run_path.is_file() else run_dir / "results.json"
    output_dir = Path(output_dir).resolve() if output_dir is not None else run_dir
    checks: list[dict] = []

    def check(name: str, status: str, detail: str, **evidence: Any) -> None:
        checks.append({"name": name, "status": status, "detail": detail, **evidence})

    results, error = _load(result_path)
    if error or not isinstance(results, dict):
        check("run_record", "unknown" if error == "missing" else "fail", error or "results.json is not an object")
        results = {}
    metadata = results.get("metadata", {})
    if not isinstance(metadata, dict):
        check("metadata", "fail", "metadata is not an object")
        metadata = {}
    protocol = metadata.get("protocol", {})
    protocol = protocol if isinstance(protocol, dict) else {}
    methods = results.get("methods", [])
    if not isinstance(methods, list) or not methods or any(not isinstance(m, str) or not m for m in methods) or len(set(methods)) != len(methods):
        check("method_declaration", "fail", "methods must be unique nonempty names")
        methods = []
    elif protocol.get("methods") is None:
        check("method_declaration", "unknown", "Frozen protocol.methods is missing")
    else:
        check("method_declaration", "pass" if methods == protocol["methods"] else "fail", "Declared methods compared with frozen protocol")
    tasks = results.get("tasks", [])
    if not isinstance(tasks, list) or any(not isinstance(t, dict) for t in tasks):
        check("task_records", "fail", "tasks must be a list of objects")
        tasks = []
    paper_ids = protocol.get("paper_ids")
    frozen_ids = isinstance(paper_ids, list) and bool(paper_ids) and all(isinstance(p, str) and p for p in paper_ids) and len(set(paper_ids)) == len(paper_ids)
    if not frozen_ids:
        check("paper_declaration", "unknown" if paper_ids is None else "fail", "Frozen unique protocol.paper_ids is unavailable")
        paper_ids = sorted({t["paper_id"] for t in tasks if isinstance(t.get("paper_id"), str)})
    else:
        check("paper_declaration", "pass", "Task denominator uses frozen paper IDs, including empty and failed outputs")
    malformed_identity = any(not isinstance(t.get("paper_id"), str) or not isinstance(t.get("method"), str) for t in tasks)
    pairs = [(t.get("paper_id"), t.get("method")) for t in tasks if isinstance(t.get("paper_id"), str) and isinstance(t.get("method"), str)]
    expected = {(pid, method) for pid in paper_ids for method in methods}
    actual = set(pairs)
    matrix_errors = []
    if malformed_identity:
        matrix_errors.append("paper_id and method must be strings")
    if len(pairs) != len(actual):
        matrix_errors.append("duplicate paper/method records")
    if actual != expected:
        matrix_errors.append(f"missing={sorted(expected - actual, key=str)!r}; extra={sorted(actual - expected, key=str)!r}")
    task_ids = {}
    for task in tasks:
        pid, tid = task.get("paper_id"), task.get("task_id")
        if not isinstance(pid, str):
            continue
        if not isinstance(tid, str) or not tid or (pid in task_ids and task_ids[pid] != tid):
            matrix_errors.append("inconsistent or missing task_id across methods")
        task_ids[pid] = tid
    check("task_denominator", "fail" if matrix_errors else "pass" if frozen_ids and methods else "unknown", "; ".join(matrix_errors) or "Exactly one record per frozen paper/method, including zero outputs")
    cap = metadata.get("max_candidates", 5)
    valid_cap = type(cap) is int and 1 <= cap <= 5
    violations = []
    for task in tasks:
        candidates = task.get("candidates")
        if not isinstance(candidates, list) or any(not isinstance(c, dict) for c in candidates) or (valid_cap and len(candidates) > cap):
            violations.append(f"{task.get('paper_id')}/{task.get('method')}")
    if protocol.get("max_candidates", cap) != cap:
        violations.append("metadata cap differs from protocol cap")
    check("candidate_cap", "pass" if valid_cap and not violations else "fail", f"Frozen per-task cap={cap!r}; violations={violations}")

    method_summary = {}
    for method in methods:
        arm_tasks = [t for t in tasks if t.get("method") == method]
        candidates = [c for t in arm_tasks for c in (t["candidates"] if isinstance(t.get("candidates"), list) else [])]
        static_counts = Counter()
        for candidate in candidates:
            static = candidate.get("checks", {}) if isinstance(candidate, dict) else {}
            value = static.get("static_status", "missing") if isinstance(static, dict) else "missing"
            static_counts[value if isinstance(value, str) else "invalid"] += 1
        method_summary[method] = {
            "task_count": len(arm_tasks), "candidate_count": len(candidates),
            "generation_status_counts": dict(Counter(str(t.get("status", "missing")) for t in arm_tasks)),
            "static_status_counts": dict(static_counts), "quality_conclusion": "not_assessed",
        }
    check("generation_completion", "pass" if tasks and all(t.get("status") == "completed" for t in tasks) else "unknown", "Failed, not-started or missing outputs remain in the denominator; completion is not candidate quality")

    contexts, provenances = {}, {}
    for method in methods:
        attempt = run_dir / "model" / "batches" / method / "attempt-1"
        response, response_error = _load(attempt / "response.json")
        if response_error:
            check(f"raw_response:{method}", "unknown" if response_error == "missing" else "fail", response_error)
        else:
            records = response.get("papers") if isinstance(response, dict) else None
            valid_records = isinstance(records, list) and all(isinstance(p, dict) for p in records)
            response_ids = [p.get("paper_id") for p in records] if valid_records else []
            valid_ids = valid_records and len(response_ids) == len(paper_ids) and all(isinstance(pid, str) for pid in response_ids) and set(response_ids) == set(paper_ids)
            valid_counts = valid_records and valid_cap and all(isinstance(p.get("candidates"), list) and len(p["candidates"]) <= cap for p in records)
            check(f"raw_response:{method}", "pass" if valid_ids and valid_counts else "fail", "Raw batch preserves every paper exactly once and the frozen per-paper candidate cap")
            if valid_ids and valid_counts:
                arm_tasks = [t for t in tasks if t.get("method") == method]
                if any(t.get("status") != "completed" for t in arm_tasks) or len(arm_tasks) != len(paper_ids):
                    check(f"normalized_output_count:{method}", "unknown", "Failed or incomplete generation does not prove normalized output counts")
                else:
                    raw_counts = {p["paper_id"]: len(p["candidates"]) for p in records}
                    matching = all(isinstance(t.get("candidates"), list) and len(t["candidates"]) == raw_counts.get(t.get("paper_id")) for t in arm_tasks)
                    check(f"normalized_output_count:{method}", "pass" if matching else "fail", "Completed normalized task counts match the recorded raw response")
        prompt_path = attempt / "prompt.txt"
        prompt = None
        if not prompt_path.exists():
            check(f"prompt:{method}", "unknown", "Raw shared-batch prompt missing", path=str(prompt_path))
        else:
            try:
                prompt = prompt_path.read_text(encoding="utf-8")
                data = json.loads(prompt.split("\nDATA:\n", 1)[1])
                entries = data.get("papers") if isinstance(data, dict) else data
                if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
                    raise ValueError("DATA.papers must be an array of objects")
                ids = [e.get("paper_id") for e in entries]
                if ids != paper_ids:
                    raise ValueError("DATA paper order or IDs differ from the frozen batch")
                for entry in entries:
                    if not isinstance(entry.get("code_conditions"), list) or not isinstance(entry.get("paper_evidence"), list):
                        raise ValueError("Context requires code_conditions and paper_evidence arrays")
                    if any(not isinstance(e, dict) for field in ["code_conditions", "paper_evidence"] for e in entry[field]):
                        raise ValueError("Context arrays must contain evidence objects")
                    if any(isinstance(e, dict) and e.get("paper_id", entry["paper_id"]) != entry["paper_id"] for e in entry["paper_evidence"]):
                        raise ValueError("Paper evidence transferred between paper contexts")
                contexts[method] = {e["paper_id"]: e for e in entries}
                check(f"prompt:{method}", "pass", "Parsed exact frozen paper order and context arrays", prompt_sha256=text_sha256(prompt))
            except (OSError, ValueError, IndexError) as parse_error:
                check(f"prompt:{method}", "fail", str(parse_error), path=str(prompt_path))
        provenance_path = attempt / "provenance.json"
        provenance, provenance_error = _load(provenance_path)
        if provenance_error or not isinstance(provenance, dict):
            check(f"provenance:{method}", "unknown" if provenance_error == "missing" else "fail", provenance_error or "Provenance is not an object", path=str(provenance_path))
            continue
        provenances[method] = provenance
        if "tools_used" not in provenance:
            check(f"tools:{method}", "unknown", "tools_used is missing")
        else:
            check(f"tools:{method}", "pass" if provenance["tools_used"] == [] else "fail", "Recorded tools_used must be exactly an empty list")
        if prompt is None or not provenance.get("prompt_sha256"):
            check(f"prompt_hash:{method}", "unknown", "Prompt or provenance hash is missing")
        else:
            check(f"prompt_hash:{method}", "pass" if provenance["prompt_sha256"] == text_sha256(prompt) else "fail", "Recorded provenance compared with the actual prompt bytes")

    for field in ["code_conditions", "paper_evidence"]:
        if "full" not in contexts or "direct" not in contexts:
            check(f"full_direct:{field}", "unknown", "Both full and direct raw prompts are required")
        else:
            differing = [pid for pid in paper_ids if not _same(contexts["full"][pid][field], contexts["direct"][pid][field])]
            check(f"full_direct:{field}", "fail" if differing else "pass", f"Exact per-paper equality; differing papers={differing}")
    if "code_only" not in contexts:
        check("code_only:no_paper_evidence", "unknown", "Code-only raw prompt unavailable")
    else:
        leaked = [pid for pid in paper_ids if contexts["code_only"][pid]["paper_evidence"] != []]
        check("code_only:no_paper_evidence", "fail" if leaked else "pass", f"All paper-evidence arrays must be empty; nonempty papers={leaked}")
    if any(method not in contexts for method in ["full", "direct", "code_only"]):
        check("all_arms:same_code", "unknown", "All three parsed raw prompts are required")
    else:
        differing = [pid for pid in paper_ids if not (_same(contexts["full"][pid]["code_conditions"], contexts["direct"][pid]["code_conditions"]) and _same(contexts["full"][pid]["code_conditions"], contexts["code_only"][pid]["code_conditions"]))]
        check("all_arms:same_code", "fail" if differing else "pass", f"Same exact code-context pool for every arm; differing papers={differing}")
    for field in ["model_requested", "instruction_sha256", "cli_version"]:
        values = [provenances.get(method, {}).get(field) for method in methods]
        if not methods or any(not isinstance(v, str) or not v for v in values):
            check(f"same_provenance:{field}", "unknown", f"Every arm requires a nonempty {field}")
        else:
            expected_value = metadata.get("model_requested") if field == "model_requested" else protocol.get(field) if field == "instruction_sha256" else None
            consistent = len(set(values)) == 1 and (expected_value is None or values[0] == expected_value)
            check(f"same_provenance:{field}", "pass" if consistent else "fail", "Equal across arms and compared with recorded frozen value where present", values=values)

    batch_records = metadata.get("batches", [])
    if not isinstance(batch_records, list) or any(not isinstance(b, dict) for b in batch_records):
        check("batch_cost_records", "fail", "metadata.batches must be an array of objects")
        batch_records = []
    batches, seen = [], {}
    for number, batch in enumerate(batch_records):
        call_id = batch.get("call_id")
        identity = ("call_id", call_id) if type(call_id) is int and call_id > 0 else ("unidentified", number)
        if identity in seen:
            check("duplicate_invocation", "pass" if batch == seen[identity] else "fail", f"Invocation {call_id!r} is counted once; conflicting duplicates are invalid")
            continue
        seen[identity] = batch
        batches.append(batch)
    batch_methods = [b.get("method") for b in batches]
    complete_batches = bool(methods) and sorted(batch_methods, key=str) == sorted(methods) and all(type(b.get("call_id")) is int and b["call_id"] > 0 for b in batches)
    check("batch_cost_records", "pass" if complete_batches else "unknown", "One identifiable shared invocation per method required; missing records are not zero-cost proof")
    resource_rows, totals = [], {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0, "duration_seconds": 0.0}
    known = {field: 0 for field in totals}
    for batch in batches:
        usage = batch.get("usage", {})
        usage = usage if isinstance(usage, dict) else {}
        provenance = provenances.get(batch.get("method"), {})
        if provenance:
            matches = provenance.get("call_id") == batch.get("call_id") and provenance.get("usage") == batch.get("usage")
            check(f"batch_provenance:{batch.get('method')}", "pass" if matches else "fail", "Batch call ID and usage compared with the recorded invocation provenance")
        row = {"method": batch.get("method"), "call_id": batch.get("call_id"), "status": batch.get("status")}
        for field in totals:
            value = batch.get(field) if field == "duration_seconds" else usage.get(field)
            if _number(value, integer=field != "duration_seconds"):
                row[field] = value
                totals[field] += value
                known[field] += 1
            else:
                row[field] = None
        row["total_tokens"] = row["input_tokens"] + row["output_tokens"] if row["input_tokens"] is not None and row["output_tokens"] is not None else None
        resource_rows.append(row)
    cost_complete = complete_batches and all(known[field] == len(batches) for field in totals)
    check("shared_invocation_costs", "pass" if cost_complete else "unknown", "Tokens and duration summed once per shared invocation; missing metrics remain unknown")
    resources = {
        "counting_unit": "shared_codex_cli_invocation", "recorded_invocation_count": len(batches),
        "complete": cost_complete, "known_sums": {**totals, "total_tokens": totals["input_tokens"] + totals["output_tokens"]},
        "known_record_counts": known, "invocations": resource_rows,
        "cached_input_note": "Cached input is a separately reported subset of input tokens, never added again to total_tokens.",
        "scope": "This run's metadata.batches only; excludes other runs and does not infer global account costs.",
    }
    report = {
        "schema_version": "1.0", "run_id": results.get("run_id"), "audit_status": _status(checks),
        "checks": checks, "denominator": {"paper_ids": paper_ids, "methods": methods, "expected_task_count": len(expected), "recorded_task_count": len(tasks), "candidate_cap_per_task": cap},
        "methods": method_summary, "resources": resources,
        "human_review_status": metadata.get("human_review_status", "pending"),
        "human_quality_assessment": "not_performed_by_this_audit", "sut_executed_by_this_audit": False,
        "recorded_runtime_verification": metadata.get("runtime_verification", "unknown"),
        "generation_dependence": "One shared batch per method; paper outputs are not independent generation repetitions.",
        "limitations": ["这是记录与输入公平性的审计，pass不代表候选语义正确、oracle已验证或发现bug。", "静态状态数量只统计机械检查，人工评分另行提交；本审计不填写评分。", "没有运行被测软件；共享批次中的论文输出存在依赖，只支持描述性pilot。", "缺失raw、provenance或成本记录记为unknown；已记录的矛盾记为fail。"],
        "audit_json": str(output_dir / "experiment-audit.json"), "audit_markdown": str(output_dir / "experiment-audit.md"),
    }
    write_json(output_dir / "experiment-audit.json", report)
    lines = [f"# 实验记录审计：{report['run_id'] or 'unknown'}", "", f"审计状态：**{report['audit_status']}**。人工审查状态：{report['human_review_status']}。", "", f"冻结任务分母：{len(paper_ids)} 篇 × {len(methods)} 个方法 = {len(expected)}；记录 {len(tasks)} 个任务；每任务候选上限 {cap}。", "", "| 检查 | 状态 | 说明 |", "| --- | --- | --- |"]
    for item in checks:
        detail = item["detail"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {item['name']} | {item['status']} | {detail} |")
    lines.extend(["", "| 方法 | 任务数 | 输出数 | 生成状态 | 静态检查状态（不是质量结论） |", "| --- | ---: | ---: | --- | --- |"])
    for method, item in method_summary.items():
        lines.append(f"| {method} | {item['task_count']} | {item['candidate_count']} | {item['generation_status_counts']} | {item['static_status_counts']} |")
    sums = resources["known_sums"]
    lines.extend(["", f"共享调用记录数：{len(batches)}；成本完整：{cost_complete}。已知输入 {sums['input_tokens']}、输出 {sums['output_tokens']}、合计 {sums['total_tokens']} tokens；cached input {sums['cached_input_tokens']} 单列且不重复相加。已知调用时长合计 {sums['duration_seconds']:.3f} 秒。缺失部分保持未知。", "", "这里只汇总当前运行的共享调用，不将费用或时长乘以论文任务数，也不推断全局账户费用。", "", *[f"- {limit}" for limit in report["limitations"]], ""])
    (output_dir / "experiment-audit.md").write_text("\n".join(lines), encoding="utf-8")
    return report
