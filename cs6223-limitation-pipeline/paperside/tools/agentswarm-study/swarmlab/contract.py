"""Tolerant extraction and canonicalisation of model-produced finding lists.

Handoff losses in the previous study came from strict field names: a worker that
returned structured candidates under different keys was silently dropped. This
module keeps the raw candidate count, records every repair, and never discards a
list just because a field is named differently.
"""
from __future__ import annotations

import json
import re

CANDIDATE_KEYS = ("candidates", "findings", "results", "records", "limitations",
                  "hypotheses", "items", "method_limitations")
PAPER_KEYS = ("paper_evidence", "paper_evidence_quotes", "paper_quotes", "citations",
              "paper_citations", "evidence_paper")
CODE_KEYS = ("code_evidence", "source_evidence", "code_spans", "source_spans",
             "code_citations", "evidence_code")
COMPARISON_KEYS = ("minimal_comparison", "minimal_test", "comparison", "test_plan",
                   "controlled_comparison")


def _strip_fence(text: str) -> str:
    match = re.fullmatch(r"\s*([^\x60]*?)\x60\x60\x60(?:json)?\s*(\{.*\})\s*\x60\x60\x60\s*", text, re.S)
    return match.group(2) if match else text


def _first_object(text: str):
    """Return the first balanced JSON object, string-aware."""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
        start = text.find("{", start + 1)
    return None


def _close_brackets(prefix: str) -> str:
    stack = []
    in_string = False
    escaped = False
    for char in prefix:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if stack:
                stack.pop()
    return prefix + "".join("}" if char == "{" else "]" for char in reversed(stack))


def _repair_truncated(text: str):
    """Close an object cut mid-record, keeping every complete record."""
    start = text.find("{")
    if start == -1:
        return None
    obj = text[start:]
    for cut in range(len(obj) - 1, max(len(obj) // 3, 0), -1):
        if obj[cut] not in "}]":
            continue
        try:
            value = json.loads(_close_brackets(obj[:cut + 1]))
        except ValueError:
            continue
        if isinstance(value, (dict, list)):
            return value
    return None


def parse_json(text: str, repairs: list | None = None):
    repairs = repairs if repairs is not None else []
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty reply")
    stripped = _strip_fence(text)
    attempts = [stripped]
    obj = _first_object(stripped)
    if obj and obj != stripped and stripped.find(obj) == stripped.find("{"):
        attempts.append(obj)
    for attempt in attempts:
        try:
            value = json.loads(attempt)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            repairs.append("bare_candidate_list")
            return {"candidates": value}
    repaired = _repair_truncated(stripped)
    if repaired is not None:
        repairs.append("closed_truncated_object")
        return repaired
    raise ValueError("no JSON object found in reply")


def _get(raw: dict, keys):
    for key in keys:
        if key in raw and raw[key] not in (None, "", []):
            return raw[key]
    return None


def _nested_evidence(raw: dict, keys):
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list):
            return value
    evidence = raw.get("evidence")
    if isinstance(evidence, dict):
        for key in keys:
            value = evidence.get(key)
            if isinstance(value, list):
                return value
    return []


def _paper_entries(raw: dict) -> list:
    rows = []
    for entry in _nested_evidence(raw, PAPER_KEYS):
        if isinstance(entry, dict):
            page = entry.get("page", entry.get("page_number", entry.get("physical_page")))
            quote = entry.get("quote", entry.get("text", entry.get("excerpt")))
            rows.append({"page": page, "quote": quote})
        elif isinstance(entry, str):
            rows.append({"page": raw.get("page"), "quote": entry})
    return rows


def _code_entries(raw: dict) -> list:
    rows = []
    for entry in _nested_evidence(raw, CODE_KEYS):
        if isinstance(entry, dict):
            rows.append({
                "path": entry.get("path", entry.get("file")),
                "start": entry.get("start", entry.get("start_line", entry.get("line"))),
                "end": entry.get("end", entry.get("end_line", entry.get("start", entry.get("line")))),
            })
        elif isinstance(entry, str) and ":" in entry:
            path, _, span = entry.rpartition(":")
            start, _, end = span.partition("-")
            try:
                rows.append({"path": path, "start": int(start), "end": int(end or start)})
            except ValueError:
                continue
    return rows


def _comparison(raw: dict):
    value = _get(raw, COMPARISON_KEYS)
    if isinstance(value, str):
        return {"fixed": "", "vary": value, "baseline": value, "observable": value, "refuted_if": value}
    if not isinstance(value, dict):
        return {}
    out = {}
    for field, aliases in {
        "fixed": ("fixed", "controls", "held_fixed"),
        "vary": ("vary", "changed", "manipulation"),
        "baseline": ("baseline", "compare", "comparison"),
        "observable": ("observable", "metric", "outcome", "measure"),
        "refuted_if": ("refuted_if", "refute", "falsified_if", "refutation"),
    }.items():
        out[field] = _get(value, aliases) or ""
    return out


def normalize_record(raw, index: int) -> dict:
    raw = raw if isinstance(raw, dict) else {"title": str(raw)}
    record = {
        "id": str(_get(raw, ("id", "candidate_id", "key")) or f"W{index}"),
        "title": _get(raw, ("title", "name", "summary", "headline")) or "",
        "kind": _get(raw, ("kind", "type")) or "method_hypothesis",
        "rule": _get(raw, ("rule", "causal_argument", "claim", "mechanism")) or "",
        "trigger": _get(raw, ("trigger", "conditions", "condition", "preconditions")) or "",
        "mitigation": _get(raw, ("mitigation", "existing_mitigation", "safeguard")) or "",
        "consequence": _get(raw, ("consequence", "impact", "downstream", "outcome"))
        or _get(raw, ("claim", "causal_argument")) or "",
        "paper_evidence": _paper_entries(raw),
        "code_evidence": _code_entries(raw),
        "counterevidence": _get(raw, ("counterevidence", "counter_evidence", "refutation")) or [],
        "minimal_comparison": _comparison(raw),
        "status": raw.get("status") or "hypothesis_not_executed",
    }
    origins = raw.get("origin_ids") or raw.get("origins") or []
    if isinstance(origins, str):
        origins = [origins]
    record["origin_ids"] = [o for o in origins if isinstance(o, str)]
    return record


def candidate_groups(data) -> tuple[list, str]:
    """Find every candidate-ish list in a reply, with the path that produced it."""
    groups = []
    if isinstance(data, list):
        return [(data, "root_list")]
    if not isinstance(data, dict):
        return []
    for key in CANDIDATE_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            groups.append((value, key))
    for wrapper in ("answer", "report", "result", "output", "finding_report"):
        inner = data.get(wrapper)
        if isinstance(inner, dict):
            for key in CANDIDATE_KEYS:
                value = inner.get(key)
                if isinstance(value, list):
                    groups.append((value, f"{wrapper}.{key}"))
    return groups


def parse_finding_report(text: str) -> dict:
    repairs: list[str] = []
    data = parse_json(text, repairs)
    groups = candidate_groups(data)
    raw_count = sum(len(group) for group, _ in groups)
    records = []
    for group, _ in groups:
        for raw in group:
            records.append(normalize_record(raw, len(records) + 1))
    return {
        "data": data,
        "records": records,
        "raw_candidate_count": raw_count,
        "parsed_groups": [path for _, path in groups],
        "repairs": repairs,
    }


def validate_report(data: dict, evidence, agent: str = "root", max_records: int = 3) -> dict:
    """Mechanical checks only; semantic truth is graded separately."""
    issues = []
    if not isinstance(data, dict):
        return {"json_parsed": False, "issues": ["reply is not an object"]}
    if data.get("paper_id") != evidence.meta["paper_id"]:
        issues.append("paper id mismatch")
    if data.get("target_execution") != "not_run":
        issues.append("invented execution status")
    groups = candidate_groups(data)
    total = sum(len(group) for group, _ in groups)
    if total > max_records:
        issues.append(f"too many candidates ({total}>{max_records})")
    records = [normalize_record(raw, i + 1) for group, _ in groups for i, raw in enumerate(group)]
    for record in records:
        label = record["id"]
        if not record["paper_evidence"]:
            issues.append(f"{label}: missing paper evidence")
        for entry in record["paper_evidence"]:
            if not evidence.quote_in_page(entry.get("page"), entry.get("quote")):
                issues.append(f"{label}: quote needs page/quote review")
        for entry in record["code_evidence"]:
            if not evidence.span_any_read(entry.get("path"), entry.get("start") or 0, entry.get("end") or 0):
                issues.append(f"{label}: source span was never read")
        comparison = record["minimal_comparison"]
        if not all(comparison.get(key) for key in ("fixed", "vary", "baseline", "observable", "refuted_if")):
            issues.append(f"{label}: incomplete comparison plan")
    return {"json_parsed": True, "records": len(records), "issues": issues,
            "note": "mechanical checks do not prove the diagnosis is correct"}
