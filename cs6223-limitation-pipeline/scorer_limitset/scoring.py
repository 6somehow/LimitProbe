"""Coverage scoring for selected positive reference cases."""
from __future__ import annotations

import json
import math
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Protocol

FIELDS = ("mechanism", "conditions", "defeaters", "evidence_location", "category", "disclosure")
PROMPT_VERSION = "limitset-judge-v1"


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


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


class RelayJudge:
    """Independent one-request-per-finding reviewer using the pipeline relay."""
    prompt_version = PROMPT_VERSION

    def __init__(self, root, model_id, temperature=0.0, env=None):
        self.root, self.model_id, self.temperature = Path(root), model_id, temperature
        self.env = env

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
        with Relay(self.env if self.env is not None else pipeline_env()):
            request = urllib.request.Request(RELAY_URL + "/chat/completions", data=body,
                      headers={"Content-Type": "application/json", "Authorization": "Bearer " + PLACEHOLDER_KEY})
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(json.load(response)["choices"][0]["message"]["content"])
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


def score(labels, predictions, splits, judge):
    by_case = {}
    for label in labels:
        cid = label["case_id"]
        if cid in by_case:
            raise ValueError(f"duplicate label: {cid}")
        by_case[cid] = label
    groups = defaultdict(list)
    for record in predictions:
        cid = record["case_id"]
        if cid not in by_case:
            raise ValueError(f"unknown prediction case: {cid}")
        groups[cid].append(record)
    membership = {}
    for split in ("validation", "test"):
        for cid in splits[split]:
            if cid not in by_case or cid in membership:
                raise ValueError(f"unknown or duplicate split case: {cid}")
            membership[cid] = split
    if set(membership) != set(by_case):
        raise ValueError("splits must cover all labels")
    cases = []
    for cid, label in by_case.items():
        repeats = []
        for record in groups.get(cid, []):
            evaluations = []
            for index, finding in enumerate(record["findings"]):
                sig = signals(label, finding)
                result = judge.judge(label, finding, sig)
                if type(result.get("matched")) is not bool or any(type(result.get("coverage", {}).get(f)) is not bool for f in FIELDS):
                    raise ValueError("judge must return boolean matched and all coverage fields")
                evaluations.append({"index": index, "signals": sig, **result})
            matches = [e for e in evaluations if e["matched"]]
            # Select one whole finding deterministically; never combine unrelated predictions.
            best = max(matches, key=lambda e: sum(e["coverage"].values()), default=None)
            repeats.append({"found": bool(best), "coverage": best["coverage"] if best else {f: False for f in FIELDS},
                            "matched_prediction_index": best["index"] if best else None,
                            "novel_for_human_review": [e["index"] for e in evaluations if not e["matched"]],
                            "evaluations": evaluations})
        cases.append({"case_id": cid, "category": label["category_code"], "split": membership[cid],
                      "repeats": repeats, "stability": wilson(sum(r["found"] for r in repeats), len(repeats))})
    aggregate = {}
    for dimension in ("category", "split"):
        aggregate[dimension] = {}
        for value in sorted({c[dimension] for c in cases}):
            # Each case-repeat is one observation; missing predictions are unreviewed, not failures.
            rows = [r for c in cases if c[dimension] == value for r in c["repeats"]]
            aggregate[dimension][value] = {"found": wilson(sum(r["found"] for r in rows), len(rows)),
                "fields": {f: wilson(sum(r["coverage"][f] for r in rows), len(rows)) for f in FIELDS}}
    return {"judge": {"model_id": judge.model_id, "prompt_version": judge.prompt_version, "temperature": judge.temperature},
            "cases": cases, "aggregate": aggregate}
