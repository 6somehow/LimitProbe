"""Coverage scoring for selected positive reference cases."""
from __future__ import annotations

import json
import math
import re
import urllib.request
import urllib.error
import socket
from collections import defaultdict
from pathlib import Path
from typing import Protocol

FIELDS = ("mechanism", "conditions", "defeaters", "evidence_location", "category", "disclosure")
PROMPT_VERSION = "limitset-judge-v1"


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validate_record(value, schema, path="$" ):
    errors = []
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        checks = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list), "string": lambda v: isinstance(v, str), "null": lambda v: v is None}
        if not any(checks[t](value) for t in types):
            return [f"{path}: expected {' or '.join(types)}"]
    if "const" in schema and value != schema["const"] or "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: unexpected value")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0): errors.append(f"{path}: string too short")
        if "pattern" in schema and not re.search(schema["pattern"], value): errors.append(f"{path}: pattern mismatch")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): errors.append(f"{path}: too few items")
        if "items" in schema:
            for i, item in enumerate(value): errors.extend(validate_record(item, schema["items"], f"{path}[{i}]"))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value: errors.append(f"{path}.{key}: required")
        for key, subschema in schema.get("properties", {}).items():
            if key in value: errors.extend(validate_record(value[key], subschema, f"{path}.{key}"))
    return errors


def words(value):
    text = json.dumps(value, ensure_ascii=False).lower()
    # CJK bigrams preserve useful overlap without requiring a tokenizer.
    return set(re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]{2}", text))


def overlap(a, b):
    x, y = words(a), words(b)
    return bool(x and y and x & y)


def signals(label, finding):
    return {
        "category": label.get("category_code") == finding.get("category_code"),
        "evidence_location": overlap(label.get("source_locations", label.get("sources", label.get("source", []))), finding.get("evidence", [])),
        "conditions": overlap(label.get("necessary_conditions_zh", []), finding.get("conditions", [])),
        "defeaters": overlap([label.get("defeaters_zh", []), label.get("caveats_zh", [])], finding.get("caveats", [])),
        "mechanism": overlap([label.get("critical_link_zh", ""), label.get("reasoning_chain", [])], finding.get("mechanism", "")),
        "disclosure": bool(label.get("disclosure_status") and label.get("disclosure_status") == finding.get("disclosure_status")),
    }


class Judge(Protocol):
    model_id: str
    prompt_version: str
    temperature: float

    def judge(self, label: dict, finding: dict, signals: dict) -> dict: ...


class FakeJudge:
    """Deterministic test double; callers can supply explicit results in order."""
    model_id = "fake"
    prompt_version = PROMPT_VERSION
    temperature = 0.0

    def __init__(self, results=None):
        self.results = iter(results) if results is not None else None

    def judge(self, label, finding, signals):
        if self.results is not None:
            return next(self.results)
        return {"matched": bool(signals["mechanism"] and signals["conditions"]), "coverage": dict(signals)}


class JudgeUnavailable(Exception):
    """Judge could not be reached."""


class RelayJudge:
    """Independent one-request-per-finding reviewer using the pipeline relay."""
    prompt_version = PROMPT_VERSION

    def __init__(self, root, model_id, temperature=0.0, env=None, timeout=120, retries=2):
        self.root, self.model_id, self.temperature = Path(root), model_id, temperature
        self.env = env
        self.timeout, self.retries = timeout, retries

    def judge(self, label, finding, signals):
        from pipeline.e2e import Relay, RELAY_URL, PLACEHOLDER_KEY
        from pipeline.run import env as pipeline_env
        rubric = (self.root / "evaluation/RUBRIC_zh.md").read_text(encoding="utf-8")
        prompt = ("Independently assess this single prediction against the reference using the rubric. "
                  "Matching requires the same mechanism, triggering conditions and consequence; topic overlap is insufficient. "
                  "Return only JSON: {\"matched\": boolean, \"coverage\": {" +
                  ", ".join('"%s": boolean' % f for f in FIELDS) +
                  "}}. Mark a field true only when covered. Signals are heuristic, not decisions.\n" +
                  json.dumps({"reference": label, "prediction": finding, "signals": signals}, ensure_ascii=False))
        body = json.dumps({"model": self.model_id, "temperature": self.temperature,
                           "messages": [{"role": "system", "content": rubric}, {"role": "user", "content": prompt}],
                           "response_format": {"type": "json_object"}}).encode()
        for attempt in range(self.retries + 1):
            try:
                with Relay(self.env if self.env is not None else pipeline_env()):
                    request = urllib.request.Request(RELAY_URL + "/chat/completions", data=body,
                              headers={"Content-Type": "application/json", "Authorization": "Bearer " + PLACEHOLDER_KEY})
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        result = json.loads(json.load(response)["choices"][0]["message"]["content"])
                break
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == self.retries:
                    raise JudgeUnavailable("judge unreachable")

        return result


def wilson(success, total):
    if not total:
        return {"covered": success, "total": total, "fraction": None, "wilson_95": None}
    z = 1.959963984540054
    p = success / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    margin = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return {"covered": success, "total": total, "fraction": p, "wilson_95": [max(0, center-margin), min(1, center+margin)]}


def score(labels, predictions, splits, judge, label_schema=None, prediction_schema=None):
    by_case, invalid = {}, []
    for label in labels:
        cid = label.get("case_id") if isinstance(label, dict) else None
        errors = validate_record(label, label_schema) if label_schema else []
        if not isinstance(cid, str):
            invalid.append({"record": "label", "case_id": cid, "errors": errors or ["missing case_id"]})
            continue
        if cid in by_case: raise ValueError(f"duplicate label: {cid}")
        by_case[cid] = (label, errors)
    groups = defaultdict(list)
    for record in predictions:
        cid = record.get("case_id") if isinstance(record, dict) else None
        errors = validate_record(record, prediction_schema) if prediction_schema else []
        if not isinstance(cid, str) or cid not in by_case:
            if errors or not isinstance(cid, str):
                invalid.append({"record": "prediction", "case_id": cid, "errors": errors or ["missing case_id"]})
                continue
            raise ValueError(f"unknown prediction case: {cid}")
        groups[cid].append((record, errors))
    membership = {}
    for split in ("validation", "test"):
        for cid in splits[split]:
            if cid not in by_case or cid in membership: raise ValueError(f"unknown or duplicate split case: {cid}")
            membership[cid] = split
    if set(membership) != set(by_case): raise ValueError("splits must cover all labels")
    cases = []
    for cid, (label, label_errors) in by_case.items():
        repeats, case_errors = [], []
        if label_errors: case_errors.append({"record": "label", "errors": label_errors})
        for record, errors in groups.get(cid, []):
            if errors:
                case_errors.append({"record": "prediction", "errors": errors})
                continue
            if label_errors: continue
            evaluations = []
            for index, finding in enumerate(record["findings"]):
                sig = signals(label, finding)
                try:
                    result = judge.judge(label, finding, sig)
                except (JudgeUnavailable, TimeoutError, ConnectionError):
                    evaluations.append({"index": index, "signals": sig, "matched": None, "coverage": sig, "judge_unavailable": True})
                    continue
                if type(result.get("matched")) is not bool or any(type(result.get("coverage", {}).get(f)) is not bool for f in FIELDS):
                    raise ValueError("judge must return boolean matched and all coverage fields")
                evaluations.append({"index": index, "signals": sig, **result})
            matches = [e for e in evaluations if e["matched"] is True]
            unavailable = any(e.get("judge_unavailable") for e in evaluations)
            best = max(matches, key=lambda e: sum(e["coverage"].values()), default=None)
            fallback = next((e for e in evaluations if e.get("judge_unavailable")), None)
            repeats.append({"found": True if best else None if unavailable else False,
                            "coverage": best["coverage"] if best else fallback["coverage"] if fallback else {f: False for f in FIELDS},
                            "judge_unavailable": unavailable, "matched_prediction_index": best["index"] if best else None,
                            "novel_for_human_review": [e["index"] for e in evaluations if e["matched"] is False], "evaluations": evaluations})
        known = [r for r in repeats if r["found"] is not None]
        found = True if any(r["found"] is True for r in repeats) else None if any(r["found"] is None for r in repeats) or not known else False
        selected = max(repeats, key=lambda r: (r["found"] is True, sum(r["coverage"].values())), default=None)
        cases.append({"case_id": cid, "category": label.get("category_code"), "split": membership[cid], "found": found,
                      "fields": selected["coverage"] if selected else {f: None for f in FIELDS},
                      "judge_unavailable": any(r["judge_unavailable"] for r in repeats), "validation_errors": case_errors,
                      "repeats": repeats, "stability": wilson(sum(r["found"] for r in known), len(known))})
    aggregate = {}
    for dimension in ("category", "split"):
        aggregate[dimension] = {}
        for value in sorted({c[dimension] or "unknown" for c in cases}):
            rows = [c for c in cases if (c[dimension] or "unknown") == value]
            known = [c for c in rows if c["found"] is not None]
            repeat_rates = [c["stability"]["fraction"] for c in rows if c["stability"]["fraction"] is not None]
            fields = {}
            for f in FIELDS:
                observed = [c["fields"][f] for c in rows if c["fields"][f] is not None]
                fields[f] = wilson(sum(observed), len(observed))
            aggregate[dimension][value] = {"found": wilson(sum(c["found"] for c in known), len(known)),
                "mean_per_repeat_rate": sum(repeat_rates) / len(repeat_rates) if repeat_rates else None, "fields": fields}
    return {"judge": {"model_id": judge.model_id, "prompt_version": judge.prompt_version, "temperature": judge.temperature},
            "cases": cases, "invalid_records": invalid, "aggregate": aggregate}
