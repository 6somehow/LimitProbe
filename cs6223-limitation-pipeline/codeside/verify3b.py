"""Step 3b: for each code-side limitation, does the documentation state it?

Question 1 (is it written?) uses interchangeable "skills", each of which finds evidence differently:

  retrieve   BM25 over passages with queries from the condition, bindings and LLM-suggested paper
             phrases; judge the top passages. Cheapest; can miss a passage worded differently.
  fullpaper  judge one limitation against the whole paper. No retrieval miss; most tokens.
  sweep      read the paper section by section, asking about all limitations at once. Each section
             gets the model's full attention; cost scales with the paper, not with the limitations.
  consensus  run all three, then a skeptic re-judges anything that any of them found.

Every skill goes through the same gate: a result other than not_found needs a quote that occurs
verbatim in the cited passage, otherwise it is downgraded to not_found and the failure is recorded.
Questions 2 and 3 (scope, evaluated) are deterministic: see scope_check.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol

from pydantic import TypeAdapter

from codeside.doc_index import Passage, Retriever, pdf_passages, repo_passages, verify_quote
from codeside.scope_check import ScopeChecker
from schema.models import Binding, EvalPoint, Limitation, ScopeItem, Verification

# 3b-v1 -> 3b-v2: "contradicted" need not restate the code's effect. v1 made the model report a docstring
# listing a value as supported, while the code rejects that value, as not_found.
# 3b-v2 -> 3b-v3: "only reached when" is context. v2 made the model dismiss a docstring that states the
# condition and effect, because it did not also repeat an enclosing check.
PROMPT_VERSION = "3b-v3"
RESULTS = ("found", "boundary_mismatch", "weaker", "contradicted", "not_found")
SKILLS = ("retrieve", "fullpaper", "sweep", "consensus")
PAPER_SOURCES = ("paper", "appendix")
SECTION_CHARS = 12_000

SYSTEM = """You check whether a limitation found in a research prototype's code is stated in its
documentation. Copy quotes character for character from the passages. Do not infer that the authors
"probably meant" something. Reply with JSON only."""

DEFINITIONS = """Result labels. Except for contradicted, a passage counts only if it speaks about the same condition AND effect:
- found: states this condition and effect with the same boundary.
- boundary_mismatch: states this limitation, but with a different boundary or value.
- weaker: mentions it more weakly than the code behaves (e.g. "only tested with X" when the code requires X).
- contradicted: claims the opposite (e.g. says a value is supported that the code rejects). The passage need
  not mention the code's error or effect; saying that the rejected case is supported is enough.
- not_found: no passage states it.
Common errors to avoid:
- A passage that only reports the value used in an experiment (e.g. "we use X = 128") is NOT documentation
  of what happens for other values. Answer not_found, and list the passage in related_ids.
- A passage on the same topic that does not say this restriction or behaviour exists is not_found.
- A limit stated about a different component or method (e.g. a baseline) is not_found.
Do not require a passage to repeat "only reached when": that line is context for where the code runs.
Judge the condition and the effect."""

JUDGE = """Paper: {title}

Code limitation:
{limitation}

Passages (each has an id and source):
{passages}

{definitions}

Answer in JSON:
{{"result": "<label>", "evidence": [{{"passage_id": "...", "quote": "verbatim text from that passage"}}],
  "related_ids": ["passage ids on the topic that do not state it"],
  "boundary_in_doc": "the condition as the document states it, or null",
  "rationale": "one or two sentences"}}"""

EXPAND = """Paper: {title}

A research prototype's code has this limitation:
{limitation}

The paper might describe it in its own words, not with code names. List 8 short search phrases (2-6 words
each) that an author could have used for this condition or its effect. Include synonyms and the scenario
it affects. Reply with a JSON list of strings only."""

SWEEP = """Paper: {title}
Section being read: {section}

Passages from this section:
{passages}

Code limitations to look for:
{limitations}

{definitions}

Report only limitations that some passage above actually addresses, with any label except not_found.
Most sections address none of them; then answer with an empty list.
Answer in JSON: a list of
{{"limitation_id": "...", "result": "<label>", "evidence": [{{"passage_id": "...", "quote": "verbatim"}}],
  "boundary_in_doc": "... or null", "rationale": "one sentence"}}"""

SKEPTIC = """Paper: {title}

Code limitation:
{limitation}

Earlier readers claim these passages document it:
{claims}

Full text of the cited passages:
{passages}

{definitions}

Try to refute the claims. Reread each quote: does it really speak about this condition and this effect, or
is it only an experimental setting, a neighbouring topic, or a different component? Keep a claim only if it
holds up. Decide the final label.

Answer in JSON:
{{"result": "<label>", "evidence": [{{"passage_id": "...", "quote": "verbatim text from that passage"}}],
  "boundary_in_doc": "... or null", "rationale": "one or two sentences"}}"""


class LLM(Protocol):
    model: str

    def complete(self, system: str, user: str, key: str) -> str: ...


class ChatLLM:
    """OpenAI-compatible chat endpoint with retries, a disk cache and usage accounting.

    A truncated or failed response raises: it must never read as "the paper does not mention it".
    """

    def __init__(self, model: str, cache_dir: Optional[Path] = None, max_tokens: int = 6000,
                 temperature: float = 0.0, reasoning_effort: str = "none", retries: int = 3):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        self._client = OpenAI(api_key=os.environ["SOCLAAS_API_KEY"],
                              base_url=os.environ["SOCLAAS_BASE_URL"].rstrip("/"), timeout=600)
        self.model, self.max_tokens, self.temperature = model, max_tokens, temperature
        self.reasoning_effort, self.retries = reasoning_effort, retries
        self.cache_dir = cache_dir
        self.resolved_model: Optional[str] = None
        self.usage = Counter()
        self._lock = threading.Lock()
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def settings(self) -> dict[str, Any]:
        return {"model": self.model, "resolved_model": self.resolved_model, "temperature": self.temperature,
                "max_tokens": self.max_tokens, "reasoning_effort": self.reasoning_effort,
                "prompt_version": PROMPT_VERSION, **self.usage}

    def complete(self, system: str, user: str, key: str) -> str:
        digest = hashlib.sha256(json.dumps([self.model, system, user, key]).encode()).hexdigest()
        path = self.cache_dir / f"{digest}.json" if self.cache_dir else None
        if path and path.is_file():
            cached = json.loads(path.read_text())
            with self._lock:
                self.usage["cache_hits"] += 1
                self.resolved_model = self.resolved_model or cached.get("model")
            return cached["content"]
        error: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                start = time.time()
                resp = self._client.chat.completions.create(
                    model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
                    reasoning_effort=self.reasoning_effort,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
                choice = resp.choices[0]
                if choice.finish_reason == "length":
                    raise RuntimeError(f"output truncated at max_tokens={self.max_tokens}")
                content = choice.message.content or ""
                with self._lock:
                    self.resolved_model = resp.model
                    self.usage["calls"] += 1
                    self.usage["seconds"] += round(time.time() - start)
                    if resp.usage:
                        self.usage["prompt_tokens"] += resp.usage.prompt_tokens
                        self.usage["completion_tokens"] += resp.usage.completion_tokens
                if path:
                    path.write_text(json.dumps({"model": resp.model, "content": content}))
                return content
            except Exception as exc:  # network, rate limit, truncation
                error = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(f"LLM call failed after {self.retries} attempts: {error}")


def parse_json(text: str) -> Any:
    """The first JSON value in a reply, ignoring fences and surrounding prose. Raises if there is none."""
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                return decoder.raw_decode(text[i:])[0]
            except json.JSONDecodeError:
                continue
    raise ValueError(f"no JSON in reply: {text[:200]!r}")


def ask_json(llm: LLM, user: str, key: str) -> Any:
    """Ask, and re-ask with a different cache key if the reply is not JSON."""
    last: Optional[Exception] = None
    for attempt in range(3):
        try:
            return parse_json(llm.complete(SYSTEM, user, f"{key}#{attempt}"))
        except ValueError as exc:
            last = exc
    raise RuntimeError(f"no parseable reply: {last}")


def describe(lim: Limitation, bindings: list[Binding]) -> str:
    cond = lim.condition
    names = set(cond.params) if cond else set()
    lines = [f"  id: {lim.limitation_id}", f"  condition: {lim.condition_text}"]
    if cond:
        lines.append(f"  condition in code: {cond.expr}")
        if cond.path_prefix:
            lines.append(f"  only reached when: {'; '.join(cond.path_prefix[:6])}")
    lines.append(f"  effect ({lim.effect_type}): {lim.effect_text}")
    for loc in lim.code_evidence[:2]:
        snippet = f"  # {loc.snippet}" if loc.snippet else ""
        lines.append(f"  location: {loc.file}:{loc.line_start}{snippet}")
    mapped = [f"  {b.code_symbol} = \"{b.paper_term}\" in the paper" for b in bindings
              if b.kind != "mechanism_entry" and (b.code_symbol in names or b.code_symbol in lim.condition_text)]
    if mapped:
        lines.append("  names in the paper:\n" + "\n".join(mapped))
    return "\n".join(lines)


def show(passages: list[Passage]) -> str:
    return "\n\n".join(f"[{p.passage_id}] ({p.source}; {p.locator})\n{p.text}" for p in passages)


@dataclass
class Judgement:
    skill: str
    result: str = "not_found"
    evidence: list[dict] = field(default_factory=list)  # passage_id, quote, source, locator
    boundary_in_doc: Optional[str] = None
    rationale: str = ""
    gate_failures: list[dict] = field(default_factory=list)
    related_ids: list[str] = field(default_factory=list)
    candidate_ids: list[str] = field(default_factory=list)


def gate(skill: str, raw: dict, passages: dict[str, Passage]) -> Judgement:
    """Keep only quotes that occur verbatim in the cited passage. No valid quote, no finding."""
    result = raw.get("result")
    j = Judgement(skill, result if result in RESULTS else "not_found", boundary_in_doc=raw.get("boundary_in_doc"),
                  rationale=str(raw.get("rationale") or ""), related_ids=list(raw.get("related_ids") or []))
    if result not in RESULTS:
        j.gate_failures.append({"reason": f"unknown result {result!r}"})
    for ev in raw.get("evidence") or []:
        if not isinstance(ev, dict):
            continue
        p = passages.get(ev.get("passage_id"))
        exact = verify_quote(ev.get("quote"), p.text) if p else None
        if exact is None:
            j.gate_failures.append({"reason": "quote not verbatim", **ev})
        elif not any(e["quote"] == exact and e["source"] == p.source for e in j.evidence):
            j.evidence.append({"passage_id": p.passage_id, "quote": exact, "source": p.source, "locator": p.locator})
    if j.result != "not_found" and not j.evidence:
        j.gate_failures.append({"reason": f"{j.result} without a verified quote"})
        j.result = "not_found"
    if j.result == "not_found":
        j.evidence = []
    return j


class Verifier:
    def __init__(self, llm: LLM, title: str, paper: list[Passage], elsewhere: list[Passage],
                 bindings: list[Binding], repeat: int = 0, top_k: int = 15, per_phrase: int = 3):
        self.llm, self.title, self.paper, self.elsewhere = llm, title, paper, elsewhere
        self.bindings, self.repeat, self.top_k, self.per_phrase = bindings, repeat, top_k, per_phrase
        self.by_id = {p.passage_id: p for p in paper + elsewhere}
        self._paper_rx = Retriever(paper)
        self._else_rx = Retriever(elsewhere)

    def _judge(self, skill: str, lim: Limitation, passages: list[Passage]) -> Judgement:
        user = JUDGE.format(title=self.title, limitation=describe(lim, self.bindings), passages=show(passages),
                            definitions=DEFINITIONS)
        raw = ask_json(self.llm, user, f"{skill}:{self.repeat}")
        j = gate(skill, raw if isinstance(raw, dict) else {}, self.by_id)
        j.candidate_ids = [p.passage_id for p in passages]
        return j

    def _query(self, lim: Limitation) -> str:
        parts = [lim.condition_text, lim.effect_text]
        if lim.condition:
            parts += [lim.condition.expr, " ".join(lim.condition.params)]
        for b in self.bindings:
            if b.code_symbol in " ".join(parts):
                parts.append(b.paper_term)
        return " ".join(parts)

    def _expand(self, lim: Limitation) -> list[str]:
        user = EXPAND.format(title=self.title, limitation=describe(lim, self.bindings))
        raw = ask_json(self.llm, user, f"expand:{self.repeat}")
        return [str(x) for x in raw if isinstance(x, str)][:12] if isinstance(raw, list) else []

    def retrieve_candidates(self, lim: Limitation, rx: Retriever, expand: bool = True) -> list[Passage]:
        seen: dict[str, Passage] = {p.passage_id: p for p in rx.search(self._query(lim), self.top_k)}
        if expand:
            for phrase in self._expand(lim):
                for p in rx.search(phrase, self.per_phrase):
                    seen.setdefault(p.passage_id, p)
        return list(seen.values())

    def skill_retrieve(self, lim: Limitation) -> Judgement:
        return self._judge("retrieve", lim, self.retrieve_candidates(lim, self._paper_rx))

    def skill_fullpaper(self, lim: Limitation) -> Judgement:
        return self._judge("fullpaper", lim, self.paper)

    def sections(self) -> list[tuple[str, list[Passage]]]:
        """Sections in order; long ones are cut at passage boundaries, short ones merged."""
        groups: list[tuple[str, list[Passage]]] = []
        name, cur, size = "", [], 0
        for p in self.paper:
            sec = p.locator.rsplit(", p.", 1)[0]
            if cur and size + len(p.text) > SECTION_CHARS:
                groups.append((name, cur))
                cur, size = [], 0
            if not cur:
                name = sec
            elif sec not in name and len(name) < 120:
                name = f"{name}; {sec}"
            cur.append(p)
            size += len(p.text)
        if cur:
            groups.append((name, cur))
        return groups

    def sweep_section(self, section: str, passages: list[Passage], lims: list[Limitation]) -> dict[str, list[dict]]:
        user = SWEEP.format(title=self.title, section=section, passages=show(passages),
                            limitations="\n\n".join(describe(l, self.bindings) for l in lims),
                            definitions=DEFINITIONS)
        raw = ask_json(self.llm, user, f"sweep:{self.repeat}")
        out: dict[str, list[dict]] = {}
        for item in raw if isinstance(raw, list) else []:
            if isinstance(item, dict) and item.get("limitation_id"):
                out.setdefault(item["limitation_id"], []).append(item)
        return out

    def merge_sweep(self, lim: Limitation, mentions: list[dict], candidate_ids: list[str]) -> Judgement:
        """Combine a limitation's per-section reports. The strongest statement decides the label."""
        order = {"contradicted": 0, "boundary_mismatch": 1, "found": 2, "weaker": 3, "not_found": 4}
        judged = [gate("sweep", m, self.by_id) for m in mentions]
        kept = sorted((j for j in judged if j.result != "not_found"), key=lambda j: order[j.result])
        failures = [f for j in judged for f in j.gate_failures]
        out = Judgement("sweep", gate_failures=failures, candidate_ids=candidate_ids)
        if kept:
            out.result, out.boundary_in_doc = kept[0].result, kept[0].boundary_in_doc
            out.rationale = kept[0].rationale
            out.evidence = [e for j in kept for e in j.evidence]
        return out

    def skeptic(self, lim: Limitation, found: list[Judgement]) -> Judgement:
        cited = {e["passage_id"] for j in found for e in j.evidence}
        claims = "\n".join(f"- {j.skill} says {j.result}: " + " / ".join(f'[{e["passage_id"]}] "{e["quote"]}"'
                                                                         for e in j.evidence)
                           for j in found)
        user = SKEPTIC.format(title=self.title, limitation=describe(lim, self.bindings), claims=claims,
                              passages=show([self.by_id[i] for i in sorted(cited)]), definitions=DEFINITIONS)
        raw = ask_json(self.llm, user, f"skeptic:{self.repeat}")
        return gate("consensus", raw if isinstance(raw, dict) else {}, self.by_id)

    def near_location(self, lim: Limitation, before: int = 5, after: int = 10) -> list[Passage]:
        """Comments and docstrings around the limitation's own code. Authors often explain a limit
        right where it is, in words that share nothing with the condition, so BM25 can't find them."""
        out = []
        for p in self.elsewhere:
            m = re.match(r"(.+?):(\d+)", p.locator) if p.source != "readme" else None
            if not m:
                continue
            for loc in lim.code_evidence:
                if m.group(1) == loc.file and loc.line_start - before <= int(m.group(2)) <= (loc.line_end or loc.line_start) + after:
                    out.append(p)
                    break
        return out

    def judge_elsewhere(self, lim: Limitation) -> Judgement:
        """README, docstrings, comments. Same judge and gate; retrieval plus the code's surroundings."""
        if not self.elsewhere:
            return Judgement("elsewhere")
        found = {p.passage_id: p for p in self.near_location(lim)}
        for p in self.retrieve_candidates(lim, self._else_rx, expand=False):
            found.setdefault(p.passage_id, p)
        return self._judge("elsewhere", lim, list(found.values()))


def run_paper_tier(v: Verifier, lims: list[Limitation], skill: str, pool: ThreadPoolExecutor) -> dict[str, dict[str, Judgement]]:
    """limitation_id -> {skill: judgement}. Consensus runs the three skills and then the skeptic."""
    out: dict[str, dict[str, Judgement]] = {l.limitation_id: {} for l in lims}
    wanted = ("retrieve", "fullpaper", "sweep") if skill == "consensus" else (skill,)
    jobs = []
    for lim in lims:
        if "retrieve" in wanted:
            jobs.append((lim, "retrieve", pool.submit(v.skill_retrieve, lim)))
        if "fullpaper" in wanted:
            jobs.append((lim, "fullpaper", pool.submit(v.skill_fullpaper, lim)))
    if "sweep" in wanted:
        sections = v.sections()
        ids = [p.passage_id for _, ps in sections for p in ps]
        futures = [pool.submit(v.sweep_section, name, ps, lims) for name, ps in sections]
        mentions: dict[str, list[dict]] = {}
        for f in futures:
            for lid, items in f.result().items():
                mentions.setdefault(lid, []).extend(items)
        for lim in lims:
            out[lim.limitation_id]["sweep"] = v.merge_sweep(lim, mentions.get(lim.limitation_id, []), ids)
    for lim, name, fut in jobs:
        out[lim.limitation_id][name] = fut.result()
    if skill == "consensus":
        by_id = {l.limitation_id: l for l in lims}
        pending = {}
        for lid, judged in out.items():
            found = [j for j in judged.values() if j.result != "not_found"]
            if found:
                pending[lid] = pool.submit(v.skeptic, by_id[lid], found)
            else:
                judged["consensus"] = Judgement("consensus", rationale="no skill found a documenting passage")
        for lid, fut in pending.items():
            out[lid]["consensus"] = fut.result()
    return out


def compose(lim: Limitation, paper: Judgement, elsewhere: Judgement, scope, verifier: str, index: int) -> Verification:
    """The paper decides `result` when it speaks. Otherwise the result comes from the other docs,
    and documented_in shows where, which is what step 4 needs for documented_elsewhere."""
    primary = paper if paper.result != "not_found" else elsewhere
    evidence = list(paper.evidence) + list(elsewhere.evidence)
    docs = []
    for e in evidence:
        if e["source"] not in docs:
            docs.append(e["source"])
    note = f"paper: {paper.result}; elsewhere: {elsewhere.result}. {primary.rationale}".strip()
    if scope.reason:
        note += f" Scope: {scope.reason}."
    return Verification(
        verification_id=f"V{index + 1:03d}", limitation_id=lim.limitation_id, direction="code_to_paper",
        result=primary.result, documented_in=docs,
        matching_evidence=[{"quote": e["quote"], "source": e["source"], "locator": e["locator"]} for e in evidence],
        scope_status=scope.scope_status, evaluated_in_paper=scope.evaluated_in_paper,
        verifier=verifier, rationale=note)


def load_paper_side(path: Optional[str]) -> tuple[list[ScopeItem], list[EvalPoint], list[Binding]]:
    if not path:
        return [], [], []
    data = json.loads(Path(path).read_text())
    return ([ScopeItem.model_validate(x) for x in data.get("scope", [])],
            [EvalPoint.model_validate(x) for x in data.get("eval_points", [])],
            [Binding.model_validate(x) for x in data.get("bindings", [])])


def majority(judgements: list[Judgement]) -> tuple[Judgement, float]:
    """The most common label across repeats, its first supporting run, and the agreement rate."""
    counts = Counter(j.result for j in judgements)
    label, n = counts.most_common(1)[0]
    return next(j for j in judgements if j.result == label), n / len(judgements)


def run(limitations: list[Limitation], title: str, pdf: str, repo: Optional[str], paper_side: Optional[str],
        llm: LLM, skill: str = "consensus", repeats: int = 3, workers: int = 8,
        extra_code_files: tuple[str, ...] = ()) -> tuple[list[Verification], list[dict]]:
    scope, evals, bindings = load_paper_side(paper_side)
    checker = ScopeChecker(scope, evals, bindings)
    paper = pdf_passages(pdf)
    code_files = {loc.file for l in limitations for loc in l.code_evidence} | set(extra_code_files)
    elsewhere = repo_passages(repo, code_files) if repo else []
    paper_runs: list[dict[str, dict[str, Judgement]]] = []
    else_runs: list[dict[str, Judgement]] = []
    with ThreadPoolExecutor(workers) as pool:
        for r in range(repeats):
            v = Verifier(llm, title, paper, elsewhere, bindings, repeat=r)
            paper_runs.append(run_paper_tier(v, limitations, skill, pool))
            futures = {l.limitation_id: pool.submit(v.judge_elsewhere, l) for l in limitations}
            else_runs.append({k: f.result() for k, f in futures.items()})
    verifications, details = [], []
    model = getattr(llm, "resolved_model", None) or llm.model
    for i, lim in enumerate(limitations):
        lid = lim.limitation_id
        chosen, agree = majority([run_[lid][skill] for run_ in paper_runs])
        other, agree_else = majority([run_[lid] for run_ in else_runs])
        sc = checker.check(lim.condition)
        ver = compose(lim, chosen, other, sc, f"llm:{model}", i)
        verifications.append(ver)
        details.append({
            "limitation_id": lid, "condition_text": lim.condition_text, "result": ver.result,
            "paper": asdict(chosen), "elsewhere": asdict(other), "paper_agreement": agree,
            "elsewhere_agreement": agree_else, "scope": asdict(sc),
            # Temperature 0 does not make the model deterministic. A verified quote that lost the vote is
            # still real evidence, so a split decision goes to a person instead of quietly becoming not_found.
            "needs_review": agree < 1 or agree_else < 1,
            "per_run": [{name: j.result for name, j in run_[lid].items()} for run_ in paper_runs],
            "per_run_elsewhere": [run_[lid].result for run_ in else_runs],
            "gate_failures": [f for run_ in paper_runs for j in run_[lid].values() for f in j.gate_failures],
        })
    return verifications, details


def main() -> None:
    ap = argparse.ArgumentParser(prog="verify3b", description=__doc__.splitlines()[0])
    ap.add_argument("--limitations", required=True, help="JSON list of Limitation(origin=code)")
    ap.add_argument("--artifact", required=True, help="data/<id>/artifact.json")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--paper-side", help="JSON with scope, eval_points and bindings")
    ap.add_argument("--model", required=True)
    ap.add_argument("--skill", choices=SKILLS, default="consensus")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    llm = ChatLLM(a.model, cache_dir=out.parent / "llm_cache")
    lims = TypeAdapter(list[Limitation]).validate_json(Path(a.limitations).read_text())
    art = json.loads(Path(a.artifact).read_text())
    vers, details = run(lims, art["paper_title"], a.pdf, a.repo, a.paper_side, llm, a.skill, a.repeats, a.workers)
    out.write_text(json.dumps([v.model_dump(mode="json") for v in vers], indent=2, ensure_ascii=False) + "\n")
    out.with_suffix(".detail.json").write_text(json.dumps(
        {"settings": {**llm.settings(), "skill": a.skill, "repeats": a.repeats}, "items": details},
        indent=2, ensure_ascii=False))
    print(f"{len(vers)} verifications -> {out}")
    print(Counter(v.result for v in vers), llm.settings())


if __name__ == "__main__":
    sys.exit(main())
