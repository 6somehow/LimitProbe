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
import os
import time
from concurrent.futures import ThreadPoolExecutor
import re
from pathlib import Path
from typing import Any, Callable, Optional

from .analysis import ANALYSIS_VERSION, chat
from .testreport import NotRun, TestRecord, not_run_record, now_iso

PROMPT_VERSION = "paper-only-v1"
MECHANISM_PROMPT_VERSION = "paper-only-v2"
MECHANISM_KINDS = ("applicability_limitation", "mechanism_origin_unclear", "method_shortcoming")
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


MECHANISM_TASK = """Analyze the paper's core mechanisms, design choices, objectives, stopping rules and assumptions.
For each, reason about what it optimizes versus what it leaves unconstrained, when assumptions or scope
conditions fail, and observed effects whose causes the paper does not explain. Return up to {n} candidates
as a JSON object with a candidates list. Each candidate has kind (one of {kinds}), claim, mechanism
(why it arises, 1-3 sentences), conditions (list of necessary conditions for the limit to bite),
defeaters (list), reasoning (paper fact -> analysis premise -> inference), quotes (1-3 EXACT quotes
copied word for word, each <= 300 characters), and locator (section or page).

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
        kind = c.get("kind") if c.get("kind") in KINDS + MECHANISM_KINDS else "other"
        chk = run_check(c.get("check"), good)
        fid = f"{artifact_id}-P{len(recs) + 1:03d}"
        an = {"version": ANALYSIS_VERSION, "kind": "analysis_only", "tier": "A1",
              "tier_note": "paper-only: the quotes were verified against the PDF text, nothing else could be checked",
              "calibrated": False, "assessment": "supports", "reasoning": str(c.get("limitation") or "")[:600],
              "hardware_needed": False, "would_confirm": str(c.get("would_confirm") or "")[:300],
              "static": {"cited": 0, "grounded": False, "items": []}, "probes": [], "model": model, "error": None,
              "arithmetic_check": chk, "paper_only": True}
        if kind in MECHANISM_KINDS:
            an.update(kind_code=kind, mechanism=c.get("mechanism"), conditions=c.get("conditions"),
                      defeaters=c.get("defeaters"), reasoning=str(c.get("reasoning") or "")[:600])
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
    text = pdf_text(pdf)[:MAX_TEXT_CHARS]
    tdir = results_root / "tests" / artifact_id
    tdir.mkdir(parents=True, exist_ok=True)
    fn = ask or (lambda p: chat(p, model, base_url, key, timeout=900, max_tokens=40000).strip())
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    recs, dropped = [], 0
    passes = ((PROMPT_VERSION, TASK.format(n=MAX_CANDIDATES, kinds=", ".join(KINDS), text=text)),
              (MECHANISM_PROMPT_VERSION, MECHANISM_TASK.format(n=MAX_CANDIDATES, kinds=", ".join(MECHANISM_KINDS), text=text)))
    for version, prompt in passes:
        ck = hashlib.sha256((version + model + prompt).encode()).hexdigest()[:20]
        cache = tdir / "analysis_cache" / f"paper-only-{ck}.json"
        if cache.exists():
            cands = json.loads(cache.read_text())
        else:
            for attempt in range(2):
                try:
                    cands = parse_candidates(fn(prompt))
                    break
                except (ValueError, KeyError):
                    if attempt:
                        raise
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(cands, indent=1, ensure_ascii=False))
        prov = {"pdf_sha256": sha, "model": model, "prompt_version": version,
                "origin": version, "generated_at": now_iso()}
        new, count = build_records(artifact_id, cands, _flat(text), model, prov)
        dropped += count
        for record in new:
            quotes = [_flat(e["quote"]) for e in record.evidence["paper"]]
            duplicate = next((i for i, old in enumerate(recs) if any(
                q in _flat(e["quote"]) or _flat(e["quote"]) in q
                for q in quotes for e in old.evidence["paper"])), None)
            if duplicate is not None:
                if version == MECHANISM_PROMPT_VERSION and record.analysis.get("kind_code"):
                    record.finding_id = recs[duplicate].finding_id
                    recs[duplicate] = record
                continue
            record.finding_id = f"{artifact_id}-P{len(recs) + 1:03d}"
            recs.append(record)
    return _write_paper_report(artifact_id, pdf, title, venue, results_root, sha, recs, dropped)


def run_swarm_paper_only(artifact_id: str, pdf: Path, report: Path, *, title: str, venue: str,
                         results_root: Path, extractor: str) -> dict[str, Any]:
    from codeside.integrate import Context, Rules, integrate
    from paperside_bridge.swarm_to_paper_side import convert
    from schema.models import SCHEMA_VERSION

    handoff, limitations = convert(artifact_id, report, pdf, extractor=extractor)
    out = results_root / "step4" / artifact_id / "limitations_for_tests.json"
    known_ids = {}
    if out.is_file():
        previous = json.loads(out.read_text())["findings"]
        known_ids = {tuple(f["limitation_ids"]): f["finding_id"] for f in previous}
    findings, _ = integrate(artifact_id, [], [], limitations, None, Rules(),
                            Context(known_ids=known_ids, paper_origin="swarm"))
    by_id = {lim.limitation_id: lim for lim in limitations}
    records, recs = [], []
    for finding in findings:
        lim = by_id[finding.limitation_ids[0]]
        raw = finding.model_dump(mode="json")
        raw.update(limitations=[lim.model_dump(mode="json")], verifications=[], process_confidence=None)
        records.append(raw)
        rec = not_run_record(raw, "no_code_location", "paper-only Swarm candidate", {"source": "swarm",
                              **handoff["provenance"], "candidate_id": lim.swarm_provenance["candidate_id"]})
        rec.evidence["paper"] = [e.model_dump(mode="json") for e in lim.paper_evidence]
        rec.analysis = {"version": ANALYSIS_VERSION, "kind": "analysis_only", "tier": "A1",
                        "tier_note": "Paper quotes checked against the cited PDF pages",
                        "calibrated": False, "assessment": "unclear", "reasoning": lim.effect_text,
                        "static": {"cited": 0, "grounded": False, "items": []}, "probes": [], "paper_only": True}
        recs.append(rec)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema_version": SCHEMA_VERSION, "origin": "swarm", "findings": records},
                              ensure_ascii=False, indent=2) + "\n")
    dropped = sum(item["reason"] != "withdrawn or refuted" for item in handoff["dropped"])
    result = _write_paper_report(artifact_id, pdf, title, venue, results_root, handoff["provenance"]["pdf_sha256"],
                                 recs, dropped)
    return {**result, "origin": "swarm", "findings_file": str(out), "dropped_candidates": handoff["dropped"]}


def _write_paper_report(artifact_id, pdf, title, venue, results_root, sha, recs, dropped) -> dict[str, Any]:
    from .testreport import counts, render_markdown, write_record

    tdir = results_root / "tests" / artifact_id
    tdir.mkdir(parents=True, exist_ok=True)
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


MECH_V1 = "paper-only-mech-v1"
MECH_V2 = "paper-only-mech-v2"
MECH_INVENTORY = '''In English, list core mechanisms and implicit assumptions per algorithm or section.
Return JSON {{"mechanisms": [{{"mechanism": "...", "assumptions": [], "quotes": ["verbatim quote"], "locator": "..."}}]}}.
PAPER TEXT\n{text}\nCODE EXCERPTS\n{code}'''
MECH_ANALYSIS = '''In English, produce 20-30 distinct conditional method limitations from the inventory.
Consider proxy properties, objective mismatch, granularity, coupling, origins of structure, shifted costs, and changes over scale or time.
Return JSON {{"candidates": [...]}} with category_code (applicability_limitation, mechanism_origin_unclear,
or method_shortcoming), claim, mechanism, reasoning_chain (list containing paper_fact, analysis_premise,
inference, optional simplified_example, conditional_consequence), critical_link, necessary_conditions,
consequence, defeaters, do_not_infer, disclosed_or_inferred (reported_in_paper or inferred), quotes,
and locator. Quotes must be verbatim paper strings or objects with source, quote and locator.
Self-check: tag reviewer-style critiques such as few models, unfair baseline, missing statistics, and
missing comparisons as kind=evaluation_critique. Distinguish reported facts from inference.
INVENTORY\n{inventory}\nPAPER TEXT\n{text}\nCODE EXCERPTS\n{code}\nEXAMPLES\n{examples}'''
MECH_TASK = """Analyze the paper in English. Produce 15-20 method limitations as JSON {{"candidates": [...]}}.
Use only these categories: applicability_limitation: where or when the method does not apply
(scope, assumptions, settings), with explicit necessary conditions; mechanism_origin_unclear: the paper
observes an effect or limit whose cause is not explained or only partly explained; method_shortcoming:
a design choice, objective, or mechanism of the method whose consequence limits it.
Each candidate must contain category_code, claim (1-2 sentences), mechanism (a short reasoning chain:
paper fact -> premise -> inference explaining why it can fail), conditions (necessary conditions),
consequence, defeaters (what makes it false or irrelevant), disclosure (reported_in_paper or inferred),
quotes (1-3 exact quotations), and locator. Every field must be in English.
For quotes use objects with source paper or code, quote, and locator (code locator is the file path).
If code is supplied, identify design-level trade-offs visible in code, not only branches or assertions.
PAPER TEXT
{text}
CODE EXCERPTS
{code}"""


MECH_V3 = "paper-only-mech-v3"
V3_INVENTORY = """In English, inventory 8-15 core mechanisms or design decisions. For each provide verbatim quote anchors, what it optimizes, its unit and granularity, assumptions about workload, model and hardware, the regularity it exploits, and where its cost goes. Return JSON with a mechanisms list. Quotes may cite paper or supplied code; code quotes must include their file path.
PAPER TEXT\n{text}\nCODE EXCERPTS\n{code}"""
V3_SWEEP = """For EVERY mechanism apply all seven lenses, asking one short question per lens: L1 does a proxy guarantee the target property? L2 does the objective or stopping rule match the real goal? L3 do interacting mechanisms use compatible units? L4 are independent choices unnecessarily coupled? L5 where does exploited regularity originate and what change moves it? L6 where does cost move and what threshold determines net benefit? L7 does the bottleneck change over scale or time? Keep pairs where a general premise yields a non-obvious conditional consequence. Turn each unexplained observation into a causal hypothesis: why, when worse, and what refutes it. Return JSON with a sweep list.
INVENTORY\n{inventory}\nPAPER TEXT\n{text}\nCODE EXCERPTS\n{code}"""
V3_WRITE = """Write 25-30 candidates in English from the sweep. Return JSON with candidates. Each has headline in the form A does not imply or guarantee B, or A conflicts with B; claim; paper_fact (verbatim quote); premise (general knowledge); inference; optional toy_example explicitly marked not a measurement; conditional consequence; critical_link; necessary_conditions, defeaters and do_not_infer as lists; disclosure (reported, mechanism_reported_consequence_inferred, or inferred); category_code; lens; and quotes (1-3 verbatim paper or code quotes with source and locator). Use applicability_limitation for environmental conditions, mechanism_origin_unclear for unexplained origins, and method_shortcoming for design or objective limits. Include both explicit author boundaries and inferred consequences. Tag first-order evaluation critiques kind=evaluation_critique.
SWEEP\n{sweep}\nINVENTORY\n{inventory}\nPAPER TEXT\n{text}\nCODE EXCERPTS\n{code}"""
V3_FILTER = """Self-filter and rank these candidates by non-obviousness, causal clarity, and conditionality. Deduplicate by mechanism and keep the top 20 method candidates. Move first-order items such as evaluation scope and missing error bars to a separate evaluation_critiques list, marking each kind=evaluation_critique. Preserve all fields and verbatim quotes. Return JSON with candidates and evaluation_critiques lists.
CANDIDATES\n{candidates}"""


MECH_V3C = "paper-only-mech-v3c"
V3C_INVENTORY = """In English, inventory 8-15 core mechanisms or design decisions with verbatim quote anchors, what each optimizes, unit and granularity, workload, model and hardware assumptions, regularity exploited, and where cost goes. Apply all seven lenses to each: L1 proxy guarantee; L2 objective or stopping rule versus goal; L3 compatibility of units; L4 coupling of choices; L5 origin and change of regularity; L6 shifted cost and net-benefit threshold; L7 bottleneck changes over scale or time. For worthwhile pairs include a short list of lens and one-sentence conditional consequence ideas; explain unexplained observations as causal hypotheses. Return JSON with mechanisms, each containing mechanism, quotes, and sweep. Quotes may cite paper or supplied code; code quotes include their file path.
PAPER TEXT\n{text}\nCODE EXCERPTS\n{code}"""
V3C_WRITE = """Write at most 3 candidates in English for this mechanism and its lens ideas. Return JSON with candidates. Each has headline in the form A does not imply or guarantee B, or A conflicts with B; claim; paper_fact (verbatim quote); premise (general knowledge); inference; optional toy_example explicitly marked not a measurement; conditional consequence; critical_link; necessary_conditions, defeaters and do_not_infer as lists; disclosure (reported, mechanism_reported_consequence_inferred, or inferred); category_code; lens; quotes (1-3 verbatim paper or code quotes with source and locator); kind (mechanism or evaluation_critique); and integer non_obviousness from 1 to 5. Use applicability_limitation for environmental conditions, mechanism_origin_unclear for unexplained origins, and method_shortcoming for design or objective limits. Include explicit author boundaries and inferred consequences.
MECHANISM\n{mechanism}\nPAPER TEXT\n{text}\nCODE EXCERPTS\n{code}"""

def _json_object(response):
    match = re.search(r"\{.*\}", response, re.S)
    if not match:
        raise ValueError("no JSON object in the answer")
    text = match.group()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Tolerant repair: strip code fences / trailing commas; if the object is cut, close it at the last complete item.
    text = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for end in range(len(text) - 1, 0, -1):
        if text[end] not in "}]":
            continue
        head = text[: end + 1]
        stack = []
        in_str = esc = False
        for ch in head:
            if in_str:
                esc = (not esc) and ch == "\\"
                if not esc and ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch in "{[":
                stack.append("}" if ch == "{" else "]")
            elif ch in "}]" and stack:
                stack.pop()
        if in_str:
            continue
        try:
            return json.loads(head + "".join(reversed(stack)))
        except json.JSONDecodeError:
            continue
    raise ValueError("unparseable JSON in the answer")


def _ask_json(ask, prompt, tries=3, **kw):
    """One model call that must return a JSON object; a bad answer is re-asked (fresh call), not fatal."""
    last = None
    for _ in range(tries):
        try:
            return _json_object(ask(prompt, **kw))
        except ValueError as exc:
            last = exc
    raise last

def mechanism_candidates(text, code_files, ask, *, version=MECH_V1, examples_path=None, stats=None, no_filter=False):
    """Generate and verify candidates; return mechanisms, critiques and dropped count."""
    code = "\n\n".join(f"FILE {path}\n{content}" for path, content in code_files.items())
    if version == MECH_V1:
        response = ask(MECH_TASK.format(text=text[:MAX_TEXT_CHARS], code=code))
    elif version == MECH_V2:
        inventory_text = ask(MECH_INVENTORY.format(text=text[:MAX_TEXT_CHARS], code=code))
        match = re.search(r"\{.*\}", inventory_text, re.S)
        if not match:
            raise ValueError("no JSON object in inventory")
        inventory = json.loads(match.group())
        if not isinstance(inventory.get("mechanisms"), list):
            raise ValueError("no mechanisms list in inventory")
        examples = Path(examples_path).read_text(encoding="utf-8") if examples_path else "None"
        response = ask(MECH_ANALYSIS.format(inventory=json.dumps(inventory), text=text[:MAX_TEXT_CHARS], code=code, examples=examples))
    elif version == MECH_V3C:
        started = time.monotonic()
        inventory = _ask_json(ask, V3C_INVENTORY.format(text=text[:MAX_TEXT_CHARS], code=code), max_tokens=18000, timeout=600  # the reasoning model spends the budget on thinking first: 6000 gave an empty answer)
        entries = inventory.get("mechanisms")
        if not isinstance(entries, list) or not entries:
            raise ValueError("no mechanisms list in inventory")
        inventory_seconds = time.monotonic() - started
        def chunk(entry):
            start = time.monotonic()
            for attempt in range(2):
                try:
                    result = _ask_json(ask, V3C_WRITE.format(mechanism=json.dumps(entry), text=text[:MAX_TEXT_CHARS], code=code), tries=2, max_tokens=14000, timeout=600)
                    if not isinstance(result.get("candidates"), list):
                        raise ValueError("no candidates list")
                    return result["candidates"][:3], {"seconds": time.monotonic() - start, "attempts": attempt + 1}
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
            return None, {"seconds": time.monotonic() - start, "attempts": 2, "error": error}
        start = time.monotonic()
        with ThreadPoolExecutor(max_workers=max(1, int(os.environ.get("LIMITSET_MECH_THREADS", "6")))) as pool:
            chunks = list(pool.map(chunk, entries))
        failures = sum(items is None for items, _ in chunks)
        if stats is not None:
            stats.update(chunk_count=len(chunks), chunk_failures=failures, chunk_timings=[detail for _, detail in chunks], inventory_seconds=inventory_seconds, chunks_seconds=time.monotonic() - start)
        if failures == len(chunks):
            raise ValueError("all mechanism chunks failed")
        candidates = [c for items, _ in chunks if items is not None for c in items if isinstance(c, dict)]
        if not no_filter:
            def rank(c):
                score = c.get("non_obviousness")
                score = score if type(score) is int and 1 <= score <= 5 else 1
                conditions = c.get("necessary_conditions")
                return -(score * bool(conditions) if isinstance(conditions, list) else 0)
            candidates.sort(key=rank)
        response = json.dumps({"candidates": candidates})
    elif version == MECH_V3:
        inventory = _json_object(ask(V3_INVENTORY.format(text=text[:MAX_TEXT_CHARS], code=code)))
        if not isinstance(inventory.get("mechanisms"), list):
            raise ValueError("no mechanisms list in inventory")
        sweep = _json_object(ask(V3_SWEEP.format(inventory=json.dumps(inventory), text=text[:MAX_TEXT_CHARS], code=code)))
        if not isinstance(sweep.get("sweep"), list):
            raise ValueError("no sweep list")
        draft = _json_object(ask(V3_WRITE.format(sweep=json.dumps(sweep), inventory=json.dumps(inventory), text=text[:MAX_TEXT_CHARS], code=code)))
        if not isinstance(draft.get("candidates"), list):
            raise ValueError("no candidates list")
        if no_filter:
            response = json.dumps(draft)
        else:
            filtered = _json_object(ask(V3_FILTER.format(candidates=json.dumps(draft))))
            if not isinstance(filtered.get("candidates"), list) or not isinstance(filtered.get("evaluation_critiques"), list):
                raise ValueError("missing filtered candidate lists")
            response = json.dumps({"candidates": filtered["candidates"][:20] + [dict(c, kind="evaluation_critique") for c in filtered["evaluation_critiques"] if isinstance(c, dict)]})
    else:
        raise ValueError(f"unknown mechanism version: {version}")
    match = re.search(r"\{.*\}", response, re.S)
    if not match:
        raise ValueError("no JSON object in the answer")
    candidates = json.loads(match.group()).get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("no candidates list")
    mechanisms, critiques, dropped = [], [], 0
    merged = 0
    for c in (candidates if version in (MECH_V3, MECH_V3C) else candidates[:30 if version == MECH_V2 else 20]):
        if not isinstance(c, dict):
            continue
        quotes = c.get("quotes") or ([c["paper_fact"]] if isinstance(c.get("paper_fact"), str) else None)
        if not isinstance(quotes, list) or not 1 <= len(quotes) <= 3:
            dropped += 1
            continue
        evidence = []
        for q in quotes:
            if isinstance(q, str):
                q = {"source": "paper", "quote": q, "locator": c.get("locator", "")}
            if not isinstance(q, dict):
                break
            source, quote, locator = q.get("source"), q.get("quote"), q.get("locator", "")
            if not isinstance(quote, str):
                break
            valid = (quote_in_text(quote, _flat(text)) if source == "paper" else
                     source == "code" and locator in code_files and quote in code_files[locator])
            if not valid:
                break
            evidence.append({"source_id": source, "location": str(locator), "support_description": quote})
        if len(evidence) != len(quotes):
            dropped += 1
            continue
        item = {**c, "evidence": evidence}
        if version == MECH_V3C and not isinstance(item.get("necessary_conditions"), list):
            item["necessary_conditions"] = []
        if version in (MECH_V3, MECH_V3C):
            item["claim"] = c.get("claim") or c.get("headline") or ""
            item["mechanism"] = c.get("mechanism") or " ".join(str(c.get(k) or "") for k in ("premise", "inference", "consequence")).strip()
        if c.get("kind") != "evaluation_critique" and c.get("category_code") in MECHANISM_KINDS:
            if version == MECH_V2 or (version == MECH_V3C and not no_filter):
                words = set(re.findall(r"\w+", str(c.get("mechanism") or "").lower()))
                anchors = {_flat(e["support_description"]) for e in evidence}
                duplicate = False
                for old in mechanisms:
                    old_words = set(re.findall(r"\w+", str(old.get("mechanism") or "").lower()))
                    old_anchors = {_flat(e["support_description"]) for e in old["evidence"]}
                    if anchors & old_anchors or (words and old_words and len(words & old_words) / len(words | old_words) >= 0.8):
                        duplicate = True
                        break
                if duplicate:
                    merged += 1
                    continue
            mechanisms.append(item)
        else:
            item["kind"] = "evaluation_critique"
            critiques.append(item)
    if version == MECH_V3C and not no_filter:
        mechanisms = mechanisms[:20]
    if stats is not None:
        stats["merged_candidates"] = merged
    return mechanisms, critiques, dropped
