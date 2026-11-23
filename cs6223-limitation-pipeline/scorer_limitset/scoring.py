"""Coverage scoring for selected positive reference cases."""
from __future__ import annotations

import json
import math
import re
import urllib.request
import urllib.error
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from collections import defaultdict
from pathlib import Path
from typing import Protocol

FIELDS = ("mechanism", "conditions", "defeaters", "evidence_location", "category", "disclosure")
PROMPT_VERSION = "judge-v2-batched"


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
        self.calls = 0
        self._lock = threading.Lock()

    def judge(self, label, finding, signals):
        if self.results is not None:
            with self._lock:
                return next(self.results)
        return {"matched": bool(signals["mechanism"] and signals["conditions"]), "coverage": dict(signals)}

    def judge_batch(self, label, findings, signal_list):
        with self._lock:
            self.calls += 1
        return [self.judge(label, f, sig) for f, sig in zip(findings, signal_list)]


class JudgeUnavailable(Exception):
    """Judge could not be reached."""


class RelayJudge:
    """Batch reviewer using a relay shared for the scoring run."""
    prompt_version = PROMPT_VERSION

    def __init__(self, root, model_id, temperature=0.0, env=None, timeout=None, retries=3):
        import os
        timeout = timeout or int(os.environ.get('LIMITSET_JUDGE_TIMEOUT', '420'))
        self.root, self.model_id, self.temperature = Path(root), model_id, temperature
        self.env = env
        self.timeout, self.retries = timeout, retries
        self.calls = 0
        self._lock = threading.Lock()

    def __enter__(self):
        from pipeline.e2e import Relay, relay_up
        from pipeline.run import env as pipeline_env
        self._relay = nullcontext() if relay_up() else Relay(self.env if self.env is not None else pipeline_env())
        self._relay.__enter__()
        return self

    def __exit__(self, *exc):
        return self._relay.__exit__(*exc)

    def _request(self, prompt):
        from pipeline.e2e import RELAY_URL, PLACEHOLDER_KEY
        rubric = (self.root / "evaluation/RUBRIC_zh.md").read_text(encoding="utf-8")
        body = json.dumps({"model": self.model_id, "temperature": self.temperature,
                           "messages": [{"role": "system", "content": rubric}, {"role": "user", "content": prompt}],
                           "response_format": {"type": "json_object"}}).encode()
        for attempt in range(self.retries + 1):
            try:
                request = urllib.request.Request(RELAY_URL + "/chat/completions", data=body,
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + PLACEHOLDER_KEY})
                with self._lock:
                    self.calls += 1
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(json.load(response)["choices"][0]["message"]["content"])
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == self.retries:
                    raise JudgeUnavailable("judge unreachable")

    def judge(self, label, finding, signals):
        prompt = ("Assess this prediction against the reference. Matching requires the same mechanism, "
                  "triggering conditions and consequence. Return only JSON with boolean matched and coverage "
                  "containing boolean fields " + ", ".join(FIELDS) + ". Signals are heuristic.\n" +
                  json.dumps({"reference": label, "prediction": finding, "signals": signals}, ensure_ascii=False))
        return self._request(prompt)

    def judge_batch(self, label, findings, signal_list):
        predictions = []
        for i, (finding, sig) in enumerate(zip(findings, signal_list)):
            item = dict(finding)
            for field in ("claim", "mechanism", "evidence"):
                if field in item:
                    value = item[field]
                    if isinstance(value, str): item[field] = value[:2000]
                    else: item[field] = json.dumps(value, ensure_ascii=False)[:2000]
            predictions.append({"index": i, "finding": item, "signals": sig})
        prompt = ("Independently assess each prediction against the single reference. Matching requires the same "
                  "mechanism, triggering conditions and consequence; topic overlap is insufficient. Signals are "
                  "heuristic. Return only JSON: {\"matches\":[{\"index\":i,\"matched\":boolean,"
                  "\"coverage\":{field:boolean}}]}; include every index once and all coverage fields: " +
                  ", ".join(FIELDS) + ".\n" + json.dumps({"reference": label, "predictions": predictions}, ensure_ascii=False))
        result = self._request(prompt)
        matches = result.get("matches") if isinstance(result, dict) else None
        if not isinstance(matches, list) or len(matches) != len(findings):
            raise ValueError("invalid batch")
        indexed = {}
        for item in matches:
            if not isinstance(item, dict) or type(item.get("index")) is not int or item["index"] in indexed or not valid_decision(item):
                raise ValueError("invalid batch")
            indexed[item["index"]] = {"matched": item["matched"], "coverage": item["coverage"]}
        if set(indexed) != set(range(len(findings))):
            raise ValueError("invalid batch")
        return [indexed[i] for i in range(len(findings))]


def valid_decision(result):
    return (isinstance(result, dict) and type(result.get("matched")) is bool and
            isinstance(result.get("coverage"), dict) and
            all(type(result["coverage"].get(f)) is bool for f in FIELDS))


def wilson(success, total):
    if not total:
        return {"covered": success, "total": total, "fraction": None, "wilson_95": None}
    z = 1.959963984540054
    p = success / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    margin = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return {"covered": success, "total": total, "fraction": p, "wilson_95": [max(0, center-margin), min(1, center+margin)]}


def score(labels, predictions, splits, judge, label_schema=None, prediction_schema=None, workers=4):
    with judge if hasattr(judge, "__enter__") else nullcontext():
        return _score(labels, predictions, splits, judge, label_schema, prediction_schema, workers)


def _score(labels, predictions, splits, judge, label_schema, prediction_schema, workers):
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
    def evaluate_repeat(label, record):
        findings = record["findings"]
        sigs = [signals(label, f) for f in findings]
        evaluations = []
        for start in range(0, len(findings), 30 if len(findings) > 60 else max(1, len(findings))):
            chunk = findings[start:start + (30 if len(findings) > 60 else len(findings))]
            chunk_sigs = sigs[start:start + len(chunk)]
            try:
                results = judge.judge_batch(label, chunk, chunk_sigs)
                if not isinstance(results, list) or len(results) != len(chunk) or not all(valid_decision(r) for r in results):
                    raise ValueError("invalid batch")
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                results = []
                for finding, sig in zip(chunk, chunk_sigs):
                    try:
                        result = judge.judge(label, finding, sig)
                        if not valid_decision(result):
                            raise ValueError("judge must return boolean matched and all coverage fields")
                        results.append(result)
                    except (JudgeUnavailable, TimeoutError, ConnectionError):
                        results.append(None)
            except (JudgeUnavailable, TimeoutError, ConnectionError):
                results = [None] * len(chunk)
            for offset, (sig, result) in enumerate(zip(chunk_sigs, results)):
                if result is None:
                    evaluations.append({"index": start + offset, "signals": sig, "matched": None, "coverage": sig, "judge_unavailable": True})
                else:
                    evaluations.append({"index": start + offset, "signals": sig, **result})
        matches = [e for e in evaluations if e["matched"] is True]
        unavailable = any(e.get("judge_unavailable") for e in evaluations)
        best = max(matches, key=lambda e: sum(e["coverage"].values()), default=None)
        fallback = next((e for e in evaluations if e.get("judge_unavailable")), None)
        return {"found": True if best else None if unavailable else False,
                "coverage": best["coverage"] if best else fallback["coverage"] if fallback else {f: False for f in FIELDS},
                "judge_unavailable": unavailable, "matched_prediction_index": best["index"] if best else None,
                "novel_for_human_review": [e["index"] for e in evaluations if e["matched"] is False], "evaluations": evaluations}

    cases = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {(cid, i): executor.submit(evaluate_repeat, label, record)
                   for cid, (label, label_errors) in by_case.items() if not label_errors
                   for i, (record, errors) in enumerate(groups.get(cid, [])) if not errors}
        for cid, (label, label_errors) in by_case.items():
            repeats, case_errors = [], []
            if label_errors: case_errors.append({"record": "label", "errors": label_errors})
            for i, (record, errors) in enumerate(groups.get(cid, [])):
                if errors:
                    case_errors.append({"record": "prediction", "errors": errors})
                elif not label_errors:
                    repeats.append(pending[cid, i].result())
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
    return {"judge": {"model_id": judge.model_id, "prompt_version": judge.prompt_version, "temperature": judge.temperature, "calls": judge.calls},
            "cases": cases, "invalid_records": invalid, "aggregate": aggregate}
