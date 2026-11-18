"""Paper-only analysis: a paper with no public code (CONFIDENCE_SPEC.md §22).

There is nothing to run and nothing to search, so every result here is a *reading* of the paper and has the lowest
tier (A1). What the harness still checks itself:
  * every quote a candidate cites must appear in the PDF text, word for word (a candidate with an invented quote is
    dropped and counted);
  * an arithmetic check a candidate proposes ("the 2.3x in the abstract against the table values 41.2 / 17.9") is
    evaluated by the harness; every number in it must appear in a cited quote.
The output is one TestRecord per candidate (status `not_run`, code `no_code_location`, an `analysis` block), so the
same 1:1 check and LIMITATIONS.md rendering as for artifacts with code apply.
"""
from __future__ import annotations

import ast
import hashlib
import json
import operator
import re
from pathlib import Path
from typing import Any, Callable, Optional

from .analysis import ANALYSIS_VERSION, chat
from .testreport import NotRun, TestRecord, now_iso

PROMPT_VERSION = "paper-only-v1"
MAX_CANDIDATES = 12
MAX_TEXT_CHARS = 140_000
KINDS = ("assumption", "evaluation_scope", "unsupported_claim", "internal_inconsistency", "missing_comparison",
         "reproducibility", "other")

SYSTEM = ("You are a careful reviewer of systems papers. Judge only from the paper text. "
          "Answer with one JSON object and nothing else.")

TASK = """Below is the full text of a systems paper whose code is not public. List up to {n} limitations a careful reader \
could establish from the text alone: assumptions the results depend on, evaluation scope (scale, hardware, workloads, \
baselines) narrower than the claims, claims without supporting evidence, numbers that disagree with each other, missing \
comparisons, anything that blocks reproduction.

For each give:
  "kind": one of {kinds}
  "claim": what the paper claims (<= 40 words)
  "limitation": the limitation (<= 60 words)
  "quotes": 1 to 3 EXACT quotes from the paper (copy them word for word, each <= 300 characters)
  "locator": section or page
  "check": null, or {{"expr": "<arithmetic expression using only numbers copied from the quotes>", \
"expect": "<what the paper's claim requires, e.g. 'about 2.3'>", "meaning": "<15 words>"}}
  "would_confirm": one sentence: what experiment or code access would settle it
Rank by how much a reader's trust in the headline result depends on it. Return {{"candidates": [...]}}.

PAPER TEXT
{text}"""


# --------------------------------------------------------------------------- PDF text
def pdf_text(pdf: Path) -> str:
    import pymupdf
    with pymupdf.open(pdf) as d:
        return "\n".join(f"[page {i + 1}]\n{p.get_text()}" for i, p in enumerate(d))


def _flat(s: str) -> str:
    s = s.replace("­", "").replace("-\n", "")          # soft hyphen, hyphenation at a line break
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_in_text(quote: str, flat_text: str) -> bool:
    q = _flat(quote)
    return len(q) >= 12 and q in flat_text


# --------------------------------------------------------------------------- arithmetic check
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg}
_NUM = re.compile(r"\d+(?:\.\d+)?")


def safe_eval(expr: str) -> float:
    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 8:
                raise ValueError("exponent too large")
            return _OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("only numbers and + - * / ** are allowed")
    return ev(ast.parse(expr.strip(), mode="eval"))


def run_check(check: Optional[dict[str, Any]], quotes: list[str]) -> Optional[dict[str, Any]]:
    if not check or not check.get("expr"):
        return None
    out = {"expr": check["expr"], "expect": check.get("expect", ""), "meaning": check.get("meaning", ""),
           "status": "not_run", "value": None}
    nums = _NUM.findall(check["expr"])
    quoted = set(_NUM.findall(" ".join(quotes)))
    missing = [n for n in nums if n not in quoted]
    if missing:
        out["note"] = f"number(s) {missing} are not in the cited quotes"
        return out
    try:
        out["value"] = round(safe_eval(check["expr"]), 6)
        out["status"] = "evaluated"
    except Exception as e:
        out["note"] = f"{type(e).__name__}: {str(e)[:80]}"
    return out


# --------------------------------------------------------------------------- candidates -> records
def parse_candidates(text: str) -> list[dict[str, Any]]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in the answer")
    c = json.loads(m.group(0)).get("candidates")
    if not isinstance(c, list):
        raise ValueError("no candidates list")
    return [x for x in c if isinstance(x, dict)][:MAX_CANDIDATES]


def build_records(artifact_id: str, cands: list[dict[str, Any]], flat_text: str, model: str,
                  provenance: dict[str, Any]) -> tuple[list[TestRecord], int]:
    recs: list[TestRecord] = []
    dropped = 0
    for c in cands:
        quotes = [q for q in (c.get("quotes") or []) if isinstance(q, str)][:3]
        good = [q for q in quotes if quote_in_text(q, flat_text)]
        if not good or len(good) < len(quotes):
            dropped += 1                              # an invented or altered quote: the whole candidate is dropped
            continue
        kind = c.get("kind") if c.get("kind") in KINDS else "other"
        chk = run_check(c.get("check"), good)
        fid = f"{artifact_id}-P{len(recs) + 1:03d}"
        an = {"version": ANALYSIS_VERSION, "kind": "analysis_only", "tier": "A1",
              "tier_note": "paper-only: the quotes were verified against the PDF text, nothing else could be checked",
              "calibrated": False, "assessment": "supports", "reasoning": str(c.get("limitation") or "")[:600],
              "hardware_needed": False, "would_confirm": str(c.get("would_confirm") or "")[:300],
              "static": {"cited": 0, "grounded": False, "items": []}, "probes": [], "model": model, "error": None,
              "arithmetic_check": chk, "paper_only": True}
        recs.append(TestRecord(
            finding_id=fid, artifact_id=artifact_id, status="not_run",
            not_run=NotRun(code="no_code_location", reason="no public code: the candidate is a reading of the paper text"),
            finding={"category": "paper_only:" + kind, "step4_level": None, "effect_type": "other", "priority": None,
                     "summary": str(c.get("claim") or "")[:300], "review": "unreviewed", "review_note": None,
                     "scope_status": "unknown", "witness_status": None, "location": None, "function": None,
                     "condition": None},
            evidence={"paper": [{"quote": q, "source": "paper", "locator": c.get("locator")} for q in good], "code": []},
            provenance={**provenance, "source": "paper_only"}, analysis=an))
    return recs, dropped


def run_paper_only(artifact_id: str, pdf: Path, *, title: str, venue: str, results_root: Path, model: str,
                   base_url: str, key: str, ask: Optional[Callable[[str], str]] = None) -> dict[str, Any]:
    from .testreport import counts, render_markdown, write_record
    text = pdf_text(pdf)[:MAX_TEXT_CHARS]
    prompt = TASK.format(n=MAX_CANDIDATES, kinds=", ".join(KINDS), text=text)
    tdir = results_root / "tests" / artifact_id
    tdir.mkdir(parents=True, exist_ok=True)
    ck = hashlib.sha256((PROMPT_VERSION + model + prompt).encode()).hexdigest()[:20]
    cache = tdir / "analysis_cache" / f"paper-only-{ck}.json"
    if cache.exists():
        cands = json.loads(cache.read_text())
    else:
        fn = ask or (lambda p: chat(p, model, base_url, key, timeout=900, max_tokens=40000).strip())
        cands = None
        for attempt in range(2):
            try:
                cands = parse_candidates(fn(prompt))
                break
            except (ValueError, KeyError):
                if attempt:
                    raise
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(cands, indent=1, ensure_ascii=False))
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    prov = {"pdf_sha256": sha, "model": model, "prompt_version": PROMPT_VERSION, "generated_at": now_iso()}
    recs, dropped = build_records(artifact_id, cands, _flat(text), model, prov)
    for r in recs:
        write_record(tdir / r.finding_id, r)
    art = {"artifact_id": artifact_id, "paper_title": title, "venue": venue, "repo_url": "none (no public code)",
           "commit": ""}
    md = render_markdown(art, recs, None, f"paper text of {pdf.name}", sha)
    rdir = results_root / "report" / artifact_id
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "LIMITATIONS.md").write_text(md)
    index = {"schema_version": "checklimits-test-report/1", "artifact_id": artifact_id, "mode": "paper_only",
             "n_records": len(recs), "dropped_for_unverified_quotes": dropped, "counts": counts(recs),
             "generated_at": now_iso(), "findings": [{"finding_id": r.finding_id, "status": r.status,
                                                      "not_run": r.not_run.code if r.not_run else None} for r in recs]}
    (tdir / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    return {"artifact": artifact_id, "mode": "paper_only", "n_records": len(recs), "dropped": dropped,
            "counts": counts(recs), "report": str(rdir / "LIMITATIONS.md"), "exit_code": 0}
