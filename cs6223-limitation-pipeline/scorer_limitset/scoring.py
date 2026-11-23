"""Coverage scoring for selected positive reference cases."""
from __future__ import annotations

import json
import os
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
PROMPT_VERSION = "judge-v3-en"


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
        return {"matched": bool(signals["mechanism"] and signals["conditions"]), "coverage": dict(signals), **({"confidence": 1.0} if "label_id" in label else {})}

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
        rubric = "You are an independent evaluator of reference coverage. Judge semantic evidence."
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
                  "containing boolean fields " + ", ".join(FIELDS) + (" and confidence in [0,1]" if "label_id" in label else "") + ".\n" +
                  json.dumps({"reference": label, "prediction": finding}, ensure_ascii=False))
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
            predictions.append({"index": i, "finding": item})
        prompt = ("Independently assess each prediction against the single reference. Matching requires the same "
                  "mechanism, triggering conditions and consequence; topic overlap is insufficient. Return only JSON: {\"matches\":[{\"index\":i,\"matched\":boolean,"
                  "\"coverage\":{field:boolean}" + (",\"confidence\":number" if "label_id" in label else "") + "}]}; " + ("confidence must be in [0,1]; " if "label_id" in label else "") + "include every index once and all coverage fields: " +
                  ", ".join(FIELDS) + ".\n" + json.dumps({"reference": label, "predictions": predictions}, ensure_ascii=False))
        result = self._request(prompt)
        matches = result.get("matches") if isinstance(result, dict) else None
        if not isinstance(matches, list) or len(matches) != len(findings):
            raise ValueError("invalid batch")
        indexed = {}
        for item in matches:
            if not isinstance(item, dict) or type(item.get("index")) is not int or item["index"] in indexed or not valid_decision(item, "label_id" in label):
                raise ValueError("invalid batch")
            indexed[item["index"]] = {k: item[k] for k in ("matched", "coverage", "confidence") if k in item}
        if set(indexed) != set(range(len(findings))):
            raise ValueError("invalid batch")
        return [indexed[i] for i in range(len(findings))]


def valid_decision(result, require_confidence=False):
    return (isinstance(result, dict) and type(result.get("matched")) is bool and
            isinstance(result.get("coverage"), dict) and
            all(type(result["coverage"].get(f)) is bool for f in FIELDS) and
            (not require_confidence or (type(result.get("confidence")) in (int, float) and
             math.isfinite(result["confidence"]) and 0 <= result["confidence"] <= 1)))


def wilson(success, total):
    if not total:
        return {"covered": success, "total": total, "fraction": None, "wilson_95": None}
    z = 1.959963984540054
    p = success / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    margin = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return {"covered": success, "total": total, "fraction": p, "wilson_95": [max(0, center-margin), min(1, center+margin)]}


def score(labels, predictions, splits, judge, label_schema=None, prediction_schema=None, workers=4, labels_en=None):
    with judge if hasattr(judge, "__enter__") else nullcontext():
        return _score_multi(labels, predictions, splits, judge, label_schema, prediction_schema, workers, labels_en) if any("label_id" in label for label in labels) else _score(labels, predictions, splits, judge, label_schema, prediction_schema, workers, labels_en)


def _score(labels, predictions, splits, judge, label_schema, prediction_schema, workers, labels_en):
    by_case, invalid = {}, []
    for label in labels:
        cid = label.get("case_id") if isinstance(label, dict) else None
        errors = validate_record(label, label_schema) if label_schema else []
        if not isinstance(cid, str):
            invalid.append({"record": "label", "case_id": cid, "errors": errors or ["missing case_id"]})
            continue
        if cid in by_case: raise ValueError(f"duplicate label: {cid}")
        by_case[cid] = (label, errors)
    english = {}
    if labels_en is not None:
        for label in labels_en:
            cid = label.get("case_id") if isinstance(label, dict) else None
            if not isinstance(cid, str) or cid in english:
                raise ValueError("invalid or duplicate English label case_id")
            english[cid] = label
        if set(english) != set(by_case):
            raise ValueError("English labels must cover exactly the reference cases")
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
        reference = english.get(label["case_id"], label)
        sigs = [signals(reference, f) for f in findings]
        sigs_zh = [signals(label, f) for f in findings]
        evaluations = []
        size = int(os.environ.get("LIMITSET_JUDGE_CHUNK", "30")) if ("label_id" in label or len(findings) > 60) else max(1, len(findings))
        for start in range(0, len(findings), size):
            chunk = findings[start:start + size]
            chunk_sigs = sigs[start:start + len(chunk)]
            try:
                results = judge.judge_batch(reference, chunk, chunk_sigs)
                if not isinstance(results, list) or len(results) != len(chunk) or not all(valid_decision(r, "label_id" in label) for r in results):
                    raise ValueError("invalid batch")
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                results = []
                for finding, sig in zip(chunk, chunk_sigs):
                    try:
                        result = judge.judge(reference, finding, sig)
                        if not valid_decision(result, "label_id" in label):
                            raise ValueError("judge must return boolean matched and all coverage fields")
                        results.append(result)
                    except (JudgeUnavailable, TimeoutError, ConnectionError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                        results.append(None)
            except (JudgeUnavailable, TimeoutError, ConnectionError):
                results = [None] * len(chunk)
            for offset, (sig, result) in enumerate(zip(chunk_sigs, results)):
                if result is None:
                    evaluations.append({"index": start + offset, "signals": sig, "signals_zh": sigs_zh[start + offset], "matched": None, "coverage": {f: None for f in FIELDS}, "judge_unavailable": True})
                else:
                    evaluations.append({"index": start + offset, "signals": sig, "signals_zh": sigs_zh[start + offset], **result})
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
            selected = max(repeats, key=lambda r: (r["found"] is True, sum(v is True for v in r["coverage"].values())), default=None)
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


def _score_multi(labels, predictions, splits, judge, label_schema, prediction_schema, workers, labels_en):
    if labels_en is not None:
        raise ValueError("multi-label references must already be English")
    grouped = defaultdict(list)
    seen = set()
    for label in labels:
        key = (label.get("case_id"), label.get("label_id"))
        if not all(isinstance(x, str) and x for x in key) or key in seen:
            raise ValueError("labels require unique case_id and label_id")
        seen.add(key)
        grouped[key[0]].append(label)
    # Score each label with the established validation and judge behavior.
    results = {}
    for cid, refs in grouped.items():
        records = [p for p in predictions if isinstance(p, dict) and p.get("case_id") == cid]
        split = next((s for s in ("validation", "test") if cid in splits.get(s, [])), None)
        if split is None:
            raise ValueError(f"missing split case: {cid}")
        for ref in refs:
            sub = _score([ref], records, {"validation": [cid] if split == "validation" else [], "test": [cid] if split == "test" else []}, judge, label_schema, prediction_schema, workers, None)
            results[(cid, ref["label_id"])] = sub["cases"][0]
    if set(sum((splits.get(s, []) for s in ("validation", "test")), [])) != set(grouped) or sum(len(splits.get(s, [])) for s in ("validation", "test")) != len(grouped):
        raise ValueError("splits must cover all labels exactly once")
    if any(not isinstance(p, dict) or p.get("case_id") not in grouped for p in predictions):
        raise ValueError("unknown prediction case")
    cases = []
    for cid, refs in grouped.items():
        rows = [results[(cid, ref["label_id"])] for ref in refs]
        for ri in range(max((len(row["repeats"]) for row in rows), default=0)):
            candidates = []
            for li, row in enumerate(rows):
                if ri >= len(row["repeats"]):
                    continue
                for e in row["repeats"][ri]["evaluations"]:
                    if e["matched"] is True and not row["repeats"][ri]["judge_unavailable"]:
                        confidence = e.get("confidence")
                        confidence = confidence if isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and math.isfinite(confidence) else 0
                        candidates.append((-confidence, li, e["index"], e))
            assigned, used = {}, set()
            for _, li, index, e in sorted(candidates, key=lambda x: x[:3]):
                if li not in assigned and index not in used:
                    assigned[li] = e
                    used.add(index)
            for li, row in enumerate(rows):
                if ri >= len(row["repeats"]):
                    continue
                repeat = row["repeats"][ri]
                match = assigned.get(li)
                repeat["found"] = True if match else None if repeat["judge_unavailable"] else False
                repeat["matched_prediction_index"] = match["index"] if match else None
                repeat["coverage"] = match["coverage"] if match else {f: None if repeat["judge_unavailable"] else False for f in FIELDS}
        for ref, row in zip(refs, rows):
            repeats = row["repeats"]
            known = [r for r in repeats if r["found"] is not None]
            row["found"] = True if any(r["found"] is True for r in repeats) else None if any(r["found"] is None for r in repeats) or not known else False
            selected = max(repeats, key=lambda r: (r["found"] is True, sum(v is True for v in r["coverage"].values())), default=None)
            row["fields"] = selected["coverage"] if selected else {f: None for f in FIELDS}
            row["stability"] = wilson(sum(r["found"] is True for r in known), len(known))
            row["label_id"] = ref["label_id"]
            row["category"] = ref.get("category_code")
        # Case repeats preserve the existing comparison interface.
        repeats = []
        for ri in range(max((len(row["repeats"]) for row in rows), default=0)):
            rs = [row["repeats"][ri] for row in rows if ri < len(row["repeats"])]
            available = [r for r in rs if not r["judge_unavailable"] and r["found"] is not None]
            found = any(r["found"] is True for r in available) if available else None
            repeats.append({"found": found, "judge_unavailable": not available and any(r["judge_unavailable"] for r in rs)})
        known = [r for r in repeats if r["found"] is not None]
        available_labels = [r for r in rows if not r["judge_unavailable"] and r["found"] is not None]
        found = any(r["found"] is True for r in available_labels) if available_labels else None
        case = dict(rows[0], found=found, labels=rows, repeats=repeats,
                    judge_unavailable=not available_labels and any(r["judge_unavailable"] for r in rows),
                    stability=wilson(sum(r["found"] is True for r in known), len(known)))
        cases.append(case)
    aggregate = {}
    for dimension in ("category", "split"):
        aggregate[dimension] = {}
        values = sorted({(r[dimension] or "unknown") for c in cases for r in c["labels"]})
        for value in values:
            label_rows = [r for c in cases for r in c["labels"] if (r[dimension] or "unknown") == value]
            case_rows = []
            for c in cases:
                relevant = [r for r in c["labels"] if (r[dimension] or "unknown") == value]
                if relevant:
                    available = [r for r in relevant if not r["judge_unavailable"] and r["found"] is not None]
                    found = any(r["found"] is True for r in available) if available else None
                    case_rows.append(dict(c, found=found, judge_unavailable=not available and any(r["judge_unavailable"] for r in relevant)))
            def summary(rows):
                available = [r for r in rows if r["found"] is not None and not r["judge_unavailable"]]
                return wilson(sum(r["found"] is True for r in available), len(available))
            fields = {f: wilson(sum(r["fields"][f] is True for r in label_rows if not r["judge_unavailable"] and r["fields"][f] is not None), sum(not r["judge_unavailable"] and r["fields"][f] is not None for r in label_rows)) for f in FIELDS}
            rates = [r["stability"]["fraction"] for r in label_rows if r["stability"]["fraction"] is not None]
            aggregate[dimension][value] = {"found": summary(case_rows), "cases": summary(case_rows), "labels": summary(label_rows), "judge_unavailable_cases": sum(c["judge_unavailable"] for c in case_rows), "judge_unavailable_labels": sum(r["judge_unavailable"] for r in label_rows), "fields": fields, "mean_per_repeat_rate": sum(rates)/len(rates) if rates else None}
    return {"judge": {"model_id": judge.model_id, "prompt_version": judge.prompt_version, "temperature": judge.temperature, "calls": judge.calls}, "cases": cases, "invalid_records": [], "aggregate": aggregate}
