"""Step 4: integrate both sides into Findings (docs/03_codeside_spec.md §4, docs/09_step4_findings.md).

Inputs for one artifact:
  code side   Limitations from step 2 (origin=code) and their 3b Verifications;
  paper side  Zhaopeng's handoff package: paper_side.json (scope, eval points, bindings), limitations.json
              (origin=paper, the static deviates/absent results of 3a; the verdict is in each record's notes)
              and finding_candidates.json (his grouping of behaviours into candidate findings).

Four steps:
  1. dedup     code-side Limitations with the same function, normalised condition and effect are merged
               mechanically. Then candidate pairs are chosen by rule (paper-paper: same finding candidate of
               Zhaopeng or identical code evidence; code-paper: overlapping code locations) and an LLM judges
               whether each pair is the same issue (codeside/step4_llm.py, majority of up to 3 samples).
               Pairs judged the same are merged (union-find). Every judgement is returned for the record.
  2. classify  schema v0.2.0 categories. Code side from 3b, with one documentation rule: only the paper
               (incl. appendix), the README, other user docs and docstrings of public functions count;
               code comments (TODO/FIXME included), private docstrings and version-only notes do not.
               Paper side from 3a: deviates -> impl_deviates, absent -> not_implemented.
  3. witness   witness-v2 (codeside/witness.py): code-side conditions with aliases from the enclosing
               function; paper-side records get a condition from the LLM, checked against the cited code.
               With a call graph (codeside/callgraph.py) the hint also carries the call chain from the entry
               point to the target and the arguments at every call, and the solver states callee conditions
               in the entry function's names (codeside/chain_bind.py): a check that cannot be reached
               through any chain is `infeasible`.
  4. priority  consequence x reachability (see `priority`). The review field is filled from the blind
               review labels; a finding reviewed `wrong` drops to priority 3.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from codeside.callgraph import locate
from codeside.chain_bind import ChainBinder
from codeside.dedup import normalise
from codeside.scope_check import ScopeChecker
from codeside.verify3b import load_paper_side
from codeside.witness import find_aliases, solve
from schema.models import Condition, Finding, Limitation, Verification


def _v(x):
    """Enum or its value (the schema stores enum values)."""
    return getattr(x, "value", x)


VERSION_RE = re.compile(r"[A-Za-z][\w.\-]*\s*(==|>=|<=|~=|>|<)\s*\d|\bv?\d+\.\d+(\.\d+)?\b")
PAPER_DOCS = ("paper", "appendix")
USER_DOCS = ("paper", "appendix", "readme", "docstring", "other")

# consequence of the effect, and how much a category says "users are not told"
SEVERITY = {"reject": "high", "accuracy": "high", "state": "high",
            "path_change": "medium", "resource": "medium", "performance": "medium", "other": "low"}
WEIGHT = {"undisclosed": "high", "contradicts_docs": "high", "stated_differently": "medium", "impl_deviates": "medium",
          "docs_only": "low", "paper_stated": "low", "not_implemented": "low", "paper_hypothesis": "low"}
# when a merged finding holds several code-side categories, the one that says most is kept
CATEGORY_ORDER = ["contradicts_docs", "undisclosed", "stated_differently", "docs_only", "paper_stated",
                  "impl_deviates", "not_implemented"]
REVIEW = {"useful": "worth_testing", "real_not_useful": "real_but_minor", "wrong": "wrong"}


@dataclass
class Rules:
    strict_scope: bool = False  # True: scope `unknown` cannot reach priority 1


@dataclass
class Context:
    """Optional inputs; without them step 4 still runs (no LLM merge, no aliases, no review)."""
    repo: Optional[Path] = None
    judge: object = None  # codeside.step4_llm.Judge
    paper_groups: list[set[str]] = field(default_factory=list)  # behaviour ids per Zhaopeng finding candidate
    labels: dict = field(default_factory=dict)  # (file, line) -> blind review record
    entry_points: list[str] = field(default_factory=list)  # "file::func" from artifact.json
    conformance: dict = field(default_factory=dict)  # behaviour id -> 3a record (conformance.json)
    callgraph: object = None  # codeside.callgraph.RepoCallGraph of the repo
    known_ids: dict = field(default_factory=dict)  # sorted limitation ids of a finding -> its id in the last run
    effect_moves: dict = field(default_factory=dict)  # limitation id -> effect_anchor record of a moved target
    paper_origin: str = "v1"


def resolve_same_as_above(lim: Limitation, conformance: dict) -> Optional[str]:
    """Paper-side effect_text is the artifact-scope discrepancy of 3a; "同上" ("same as above") there means
    "same as the local-entry discrepancy" of the same 3a record. Returns the expanded text, or None."""
    if not lim.effect_text.startswith("同上"):
        return None
    le = (conformance.get(_behaviour(lim)) or {}).get("local_entry") or {}
    base = le.get("discrepancy") or le.get("actual")
    if not base:
        return None
    rest = lim.effect_text[2:].lstrip("：:，, ")
    return base + (f"（artifact 范围：{rest}）" if rest else "")


# --------------------------------------------------------------------------- classification
def not_counted(e) -> Optional[str]:
    """None if this evidence counts as stating the limitation to users, else why not."""
    if e.source == "code_comment":
        return "only a code comment"
    if e.source == "docstring":
        m = re.search(r"\((\w+)\)\s*$", e.locator or "")
        if m and m.group(1).startswith("_"):
            return "only a private docstring"
    words = re.findall(r"[A-Za-z]{3,}", VERSION_RE.sub(" ", e.quote))
    if VERSION_RE.search(e.quote) and len(words) <= 4:
        return "only a version note"
    return None


def classify(v: Optional[Verification]) -> tuple[str, list[str]]:
    """Category for a code-side limitation, plus notes explaining the decision."""
    if v is None:
        return "undisclosed", ["no 3b verification; treated as not found"]
    if v.result == "not_found":
        return "undisclosed", []
    kept = [e for e in v.matching_evidence if not_counted(e) is None]
    dropped = sorted({not_counted(e) for e in v.matching_evidence} - {None})
    if not v.matching_evidence:  # a result without quotes: trust documented_in
        sources = [d for d in v.documented_in if d in USER_DOCS]
    else:
        sources = [e.source for e in kept]
    if not sources:
        return "undisclosed", [f"3b {v.result}, but {'; '.join(dropped) or 'no user-facing source'}"
                               " (rule: does not count as stated)"]
    if v.result == "contradicted":
        return "contradicts_docs", []
    if v.result in ("boundary_mismatch", "weaker"):
        return "stated_differently", [f"3b {v.result}"]
    if any(s in PAPER_DOCS for s in sources):
        return "paper_stated", []
    return "docs_only", []


def paper_category(lim: Limitation) -> tuple[str, list[str]]:
    if lim.swarm_category:
        return "paper_hypothesis", [f"Swarm candidate ({lim.swarm_category}); hypothesis with cited paper text"]
    m = re.search(r"verdict=(\w+)", lim.notes or "")
    verdict = m.group(1) if m else None
    notes = [f"paper side (3a static): {verdict or 'no verdict'}; not a confirmed runtime effect"]
    if verdict == "absent":
        return "not_implemented", notes
    if verdict != "deviates":
        notes.append("3a verdict missing in notes; treated as deviates")
    return "impl_deviates", notes


# --------------------------------------------------------------------------- priority
def reachability(hint: Optional[dict]) -> str:
    s = (hint or {}).get("status", "")
    if s.startswith("solved") or s in ("trigger_only", "always"):
        return "yes"
    if s == "infeasible":
        return "no"
    return "unknown"


def priority(category: str, effect: str, reach: str, scope: str, review: str, rules: Rules) -> tuple[int, str]:
    """1 = test first. Returns the priority and the reason.

    p3  out of the paper's scope, unreachable (z3: condition contradicts its path), or reviewed `wrong`;
    p1  a category that says users are not told (undisclosed, contradicts_docs), a severe effect
        (reject, accuracy, state) and a witness that reaches it (and, with strict_scope, a known scope);
    p2  the same with a medium effect or unknown reachability, or a medium category
        (stated_differently, impl_deviates);
    p3  everything else.
    """
    if scope == "out_of_scope":
        return 3, "out of the paper's scope"
    if reach == "no":
        return 3, "unreachable: condition contradicts its path prefix"
    if review == "wrong":
        return 3, "reviewed as wrong"
    w, sev = WEIGHT[category], SEVERITY.get(effect, "low")
    if w == "high" and sev == "high" and reach == "yes" and not (rules.strict_scope and scope == "unknown"):
        return 1, f"{category}, {effect} effect, witness reaches it"
    if w == "high" and sev in ("high", "medium"):
        return 2, f"{category}, {effect} effect" + (", reachability unknown" if reach != "yes" else "")
    if w == "medium":
        return 2, category
    return 3, f"{category}, {effect} effect"


# --------------------------------------------------------------------------- helpers
def _key(lim: Limitation) -> tuple:
    loc = lim.code_evidence[0] if lim.code_evidence else None
    expr = normalise(lim.condition.expr) if lim.condition else lim.limitation_id
    return (loc.file if loc else "", loc.function if loc else "", expr, lim.effect_type)


def _overlap(a: Limitation, b: Limitation) -> bool:
    return any(x.file == y.file and x.line_start <= (y.line_end or y.line_start) and y.line_start <= (x.line_end or x.line_start)
               for x in a.code_evidence for y in b.code_evidence)


def _evidence_set(lim: Limitation) -> frozenset:
    return frozenset((c.file, c.line_start, c.line_end) for c in lim.code_evidence)


def _summary(lim: Limitation) -> str:
    loc = lim.code_evidence[0] if lim.code_evidence else None
    where = f" ({loc.file}:{loc.line_start})" if loc else ""
    s = f"When {lim.condition_text}: {lim.effect_text}{where}" if lim.origin == "code" else lim.effect_text
    return s if len(s) <= 400 else s[:397] + "..."


def _behaviour(lim: Limitation) -> str:
    return lim.limitation_id.split("-gap-", 1)[-1]


CHAIN_KEYS = ("call_chain", "call_sites", "other_chains", "uncertain_steps", "calls_entry")


def _chain_fields(info: dict, chosen: int = 0) -> dict:
    """The call-chain part of a witness hint (see docs/09_step4_findings.md)."""
    out = {"call_chain_status": info["status"]}
    chains = info.get("chains") or []
    if chains and chosen:
        entry = info["entry"]
        names = [[entry, *[c.callee for c in ch]] for ch in chains]
        out["call_chain"] = names[chosen]
        out["call_sites"] = [c.to_json() for c in chains[chosen]]
        out["other_chains"] = [n for i, n in enumerate(names) if i != chosen]
        unc = [f"{c.caller} -> {c.callee} ({c.resolved_by})" for c in chains[chosen] if not c.certain]
        if unc:
            out["uncertain_steps"] = unc
    else:
        out.update({k: info[k] for k in CHAIN_KEYS if k in info})
    if info["status"] in ("not_found", "module_level") and info.get("note"):
        out["call_chain_note"] = info["note"]
    return out


def code_witness(lim: Limitation, checker, ctx: Context) -> dict:
    """witness-v2 for a code-side limitation, with the call chain when the repo's call graph is known."""
    loc = lim.code_evidence[0] if lim.code_evidence else None
    effect = _v(lim.effect_type)
    info = locate(ctx.callgraph, ctx.entry_points, loc.file, loc.line_start) if ctx.callgraph and loc else None
    chains = (info or {}).get("chains") or []
    if info and info["status"] == "resolved" and lim.condition is not None:
        # one problem per chain: the first chain that reaches the check gives the witness;
        # the check is unreachable only if no chain reaches it
        hints = []
        for i, ch in enumerate(chains):
            h = solve(lim.condition, checker, effect, None, ChainBinder(ctx.callgraph, info["entry"], ch, loc.line_start))
            hints.append(h)
            if h.get("status") != "infeasible":
                break
        chosen = len(hints) - 1 if hints[-1].get("status") != "infeasible" else 0
        hint = hints[chosen]
        if hint.get("status") == "infeasible" and len(chains) > 1 and hint.get("infeasible_because") == "call_chain":
            hint["note"] += f" (all {len(chains)} call chains found were tried)"
        hint.update(_chain_fields(info, chosen))
        return hint
    al = _aliases(ctx, loc, loc.line_start) if loc else {}
    # without a chain the path prefix may mix frames; aliases of the innermost frame are only safe
    # when there is no other frame (the check is in the entry function, or there is no prefix)
    single_frame = not (lim.condition and lim.condition.path_prefix) or (loc and loc.function in ctx.entry_points)
    hint = solve(lim.condition, checker, effect, al if single_frame else None)
    if al and not single_frame:
        hint["aliases_not_applied"] = al
        hint.setdefault("note", "local definitions in the checked function, not used by the solver "
                                "because the path prefix also holds caller conditions")
    if info:
        hint.update(_chain_fields(info))
    return hint


def _aliases(ctx: Context, loc, line: int) -> dict:
    if ctx.repo is None or loc is None:
        return {}
    p = ctx.repo / loc.file
    return find_aliases(p.read_text(errors="replace"), line) if p.is_file() else {}


class _UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        self.p[self.find(b)] = self.find(a)


@dataclass
class _Unit:
    """One code-side group (mechanically merged) or one paper-side Limitation."""
    lims: list[Limitation]
    category: str
    notes: list[str]
    ver: Optional[Verification] = None

    @property
    def head(self) -> Limitation:
        return self.lims[0]

    @property
    def origin(self) -> str:
        return self.head.origin


def candidate_pairs(units: list[_Unit], ctx: Context) -> list[tuple[int, int, str]]:
    out = []
    for i, a in enumerate(units):
        for j in range(i + 1, len(units)):
            b = units[j]
            if a.origin == "code" and b.origin == "code":
                continue  # code-side duplicates are merged mechanically
            if a.origin != b.origin:
                if any(_overlap(x, y) for x in a.lims for y in b.lims):
                    out.append((i, j, "overlapping code locations"))
                continue
            ba, bb = _behaviour(a.head), _behaviour(b.head)
            if any(ba in g and bb in g for g in ctx.paper_groups):
                out.append((i, j, "same paper-side finding candidate"))
            elif a.head.code_evidence and _evidence_set(a.head) == _evidence_set(b.head):
                out.append((i, j, "identical code evidence"))
    return out


# --------------------------------------------------------------------------- main entry
def integrate(artifact_id: str, code_lims: list[Limitation], code_vers: list[Verification],
              paper_lims: list[Limitation], checker: Optional[ScopeChecker], rules: Rules,
              ctx: Optional[Context] = None) -> tuple[list[Finding], dict]:
    ctx = ctx or Context()
    vers = {v.limitation_id: v for v in code_vers}
    groups: dict[tuple, list[Limitation]] = {}
    for lim in code_lims:
        groups.setdefault(_key(lim), []).append(lim)
    units: list[_Unit] = []
    for group in groups.values():
        v = next((vers[l.limitation_id] for l in group if l.limitation_id in vers), None)
        cat, notes = classify(v)
        if v is not None:
            notes.insert(0, f"3b: {_v(v.result)}" + (f" in {', '.join(_v(d) for d in v.documented_in)}"
                                                        if v.documented_in else ""))
        if len(group) > 1:
            notes.append("same check merged: " + ", ".join(l.limitation_id for l in group[1:]))
        units.append(_Unit(group, cat, notes, v))
    for lim in paper_lims:
        cat, notes = paper_category(lim)
        text = resolve_same_as_above(lim, ctx.conformance)
        if text:  # a copy for the summary and the LLM prompts; the hand-off keeps the original record
            lim = lim.model_copy(update={"effect_text": text})
            notes.append("effect_text '同上' expanded from conformance.json local_entry")
        units.append(_Unit([lim], cat, notes))

    # 1. dedup: LLM on rule-chosen pairs
    pairs = candidate_pairs(units, ctx)
    judgements, uf = [], _UF(len(units))
    if ctx.judge is not None:
        results = _pmap(lambda p: ctx.judge.same(units[p[0]].head, units[p[1]].head), pairs)
        for (i, j, why), r in zip(pairs, results):
            r["candidate_because"] = why
            judgements.append(r)
            if r["same"]:
                uf.union(i, j)
    clusters: dict[int, list[int]] = {}
    for i in range(len(units)):
        clusters.setdefault(uf.find(i), []).append(i)

    # paper-only clusters need an LLM condition; ask for all of them at once
    conditions: list[dict] = []
    paper_mains = [_main([units[i] for i in m]) for m in clusters.values()]
    paper_mains = [u.head for u in paper_mains if u.origin == "paper" and not u.head.swarm_category]
    cond_of = {}
    if ctx.judge is not None:
        cond_of = dict(zip([l.limitation_id for l in paper_mains], _pmap(ctx.judge.condition, paper_mains)))
    drafts = []
    for members in clusters.values():
        us = [units[i] for i in members]
        code = [u for u in us if u.origin == "code"]
        paper = [u for u in us if u.origin == "paper"]
        main = _main(us)
        lim, v = main.head, main.ver
        notes = list(main.notes)
        if len(us) > 1:
            notes.append("merged (LLM: same issue): " + ", ".join(u.head.limitation_id for u in us if u is not main))
        if code and paper:
            notes.append("paper side also reports: " + ", ".join(sorted({u.category for u in paper})))
        # 3. witness
        loc = lim.code_evidence[0] if lim.code_evidence else None
        if lim.origin == "code":
            hint = code_witness(lim, checker, ctx)
        else:
            hint = _paper_witness(lim, checker, ctx, cond_of.get(lim.limitation_id), conditions)
            if ctx.callgraph and loc:  # where the cited code sits on the entry's call path (no solving)
                hint.update(_chain_fields(locate(ctx.callgraph, ctx.entry_points, loc.file, loc.line_start)))
        if loc:
            hint["location"] = f"{loc.file}:{loc.line_start}" + (
                f"-{loc.line_end}" if (loc.line_end or 0) > loc.line_start else "")
            hint["function"] = loc.function
        moved = ctx.effect_moves.get(lim.limitation_id)
        if moved:  # REQUESTS_TO_STEP4.md request 5: the statement that produces the effect
            hint["effect_location"] = moved["to_location"]
            hint["labelled_location"] = moved["from_location"]
            hint["effect_location_reason"] = moved["reason"]
        # review (blind labels exist for code-side items only)
        review, review_note = "unreviewed", None
        for u in code:
            for l in u.lims:
                for c in l.code_evidence:
                    lab = ctx.labels.get((c.file, c.line_start))
                    if lab and review == "unreviewed":
                        review = REVIEW.get(lab["label"], "unreviewed")
                        review_note = (f"blind review by an LLM subagent (round {lab.get('round')}), not human: "
                                       f"{lab.get('reason', '')}")
        scope = _v(v.scope_status) if v else "unknown"
        # a merged finding takes the highest priority any of its categories gives (same effect, witness, review)
        prio, why = min(priority(c, _v(lim.effect_type), reachability(hint), scope, review, rules)
                        for c in dict.fromkeys([main.category, *(u.category for u in us)]))
        notes.append(f"priority {prio}: {why}")
        all_lims = [l for u in us for l in u.lims]
        origin = "swarm" if any(l.swarm_category for l in all_lims) else ctx.paper_origin
        kw = dict(artifact_id=artifact_id, origin=origin, category=main.category, level=lim.level or "L2",
                  limitation_ids=[l.limitation_id for l in all_lims],
                  verification_ids=[vers[l.limitation_id].verification_id for l in all_lims if l.limitation_id in vers],
                  scope_status=scope, evaluated_in_paper=v.evaluated_in_paper if v else None,
                  effect_type=lim.effect_type, summary=_summary(lim), witness_hint=hint,
                  confidence="mechanical" if (lim.provenance == "ast" and v is not None and v.verifier.startswith("human:")
                                              and len(us) == 1) else "llm_assisted",
                  priority=prio, rationale="; ".join(notes), review=review, review_note=review_note)
        drafts.append(((prio, 0 if code else 1, loc.file if loc else "", loc.line_start if loc else 0), kw, members))
    drafts.sort(key=lambda d: d[0])
    # ids are stable across runs: the test side archives results by finding id. A finding made of the same
    # limitations as in the last run keeps its id; a new one gets the next free number. The order in the
    # file is still the test order (priority first).
    ids, used = [], set()
    for _, kw, _ in drafts:
        old = ctx.known_ids.get(tuple(sorted(kw["limitation_ids"])))
        ids.append(old if old and old not in used else None)
        used.add(old)
    nums = [int(m.group(1)) for m in (re.fullmatch(rf"{re.escape(artifact_id)}-F(\d+)", i)
                                      for i in ctx.known_ids.values()) if m]
    free = max(nums, default=0)
    for k, i in enumerate(ids):
        if i is None:
            free += 1
            ids[k] = f"{artifact_id}-F{free:03d}"
    fid_of_unit = {i: ids[n] for n, d in enumerate(drafts) for i in d[2]}
    # candidate pairs judged different (or not judged) stay linked: same code region, worth reading together
    related: dict[str, set[str]] = {}
    for i, j, _ in pairs:
        a, b = fid_of_unit[i], fid_of_unit[j]
        if a != b:
            related.setdefault(a, set()).add(b)
            related.setdefault(b, set()).add(a)
    findings = []
    for n, (_, kw, _) in enumerate(drafts):
        fid = ids[n]
        if fid in related:
            kw["rationale"] += "; related (candidate pair, judged different): " + ", ".join(sorted(related[fid]))
        findings.append(Finding(finding_id=fid, **kw))
    report = _report(findings, rules, units, pairs, judgements)
    report["llm_records"] = {"same": judgements, "condition": conditions}
    return findings, report


def _main(us: list[_Unit]) -> _Unit:
    """The unit a merged finding is built from: the code side if present (it has a condition and 3b)."""
    code = [u for u in us if u.origin == "code"]
    if code:
        return min(code, key=lambda u: CATEGORY_ORDER.index(u.category))
    return next((u for u in us if u.category == "impl_deviates"), us[0])


def _pmap(fn, items: list, workers: int = 4) -> list:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(fn, items))


def _paper_witness(lim: Limitation, checker, ctx: Context, r: Optional[dict], log: list) -> dict:
    base = {"format": "witness-v2", "kind": "input_value", "status": "no_condition", "condition": None,
            "path_prefix": [], "code_locations": [f"{c.file}:{c.line_start}-{c.line_end or c.line_start}"
                                                  for c in lim.code_evidence]}
    if r is None:
        base["note"] = "paper-side gap: condition only in text (condition_text)"
        return base
    log.append({"limitation_id": lim.limitation_id, **r})
    if r["kind"] == "always":
        base.update(status="always", note="the gap shows on every call through the cited code; any input reaching "
                                          "it is a witness. " + r["reason"])
        return base
    if r["kind"] == "not_input":
        base.update(note="not decided by input values: " + r["reason"])
        return base
    if r["kind"] != "condition":
        base["note"] = "LLM gave no usable condition" + (f": {r['rejected_because']}" if r.get("rejected_because") else "")
        return base
    loc = lim.code_evidence[0] if lim.code_evidence else None
    hint = solve(Condition(expr=r["expr"], params=[], path_prefix=r["path_prefix"]), checker, _v(lim.effect_type),
                 _aliases(ctx, loc, (loc.line_end or loc.line_start) + 1) if loc else None)
    hint["code_locations"] = base["code_locations"]
    hint["condition_source"] = f"LLM ({r.get('model')}) from the paper-side text; names checked against the cited code"
    return hint


def _report(findings: list[Finding], rules: Rules, units: list[_Unit], pairs: list, judgements: list) -> dict:
    is_paper = lambda f, i: i.startswith(f"{f.artifact_id}-gap-")
    return {
        "rules": asdict(rules),
        "code_limitations": sum(len(u.lims) for u in units if u.origin == "code"),
        "paper_limitations": sum(1 for u in units if u.origin == "paper"),
        "units_before_llm_merge": len(units), "candidate_pairs": len(pairs),
        "pairs_judged_same": sum(1 for j in judgements if j["same"]),
        "findings": len(findings),
        "findings_with_code_side": sum(1 for f in findings if any(not is_paper(f, i) for i in f.limitation_ids)),
        "findings_merged_both_sides": sum(1 for f in findings if any(is_paper(f, i) for i in f.limitation_ids)
                                          and any(not is_paper(f, i) for i in f.limitation_ids)),
        "by_category": dict(Counter(_v(f.category) for f in findings)),
        "by_priority": dict(Counter(f.priority for f in findings)),
        "by_category_priority": dict(Counter(f"{_v(f.category)}/p{f.priority}" for f in findings)),
        "by_review": dict(Counter(_v(f.review) for f in findings)),
        "witness_status": dict(Counter(f.witness_hint.get("status") for f in findings if f.witness_hint)),
        "call_chain_status": dict(Counter(f.witness_hint.get("call_chain_status", "none") for f in findings
                                          if f.witness_hint)),
        "scope_status": dict(Counter(_v(f.scope_status) for f in findings)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--artifact", required=True, help="data/<id>/artifact.json")
    ap.add_argument("--code-limitations", required=True)
    ap.add_argument("--code-verifications", required=True, help="3b output (list of Verification)")
    ap.add_argument("--paper-dir", help="paper-side handoff dir with paper_side.json and limitations.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--strict-scope", action="store_true")
    a = ap.parse_args()
    art = json.loads(Path(a.artifact).read_text())
    load = lambda p, m: [m.model_validate(x) for x in json.loads(Path(p).read_text())]
    code_lims, code_vers = load(a.code_limitations, Limitation), load(a.code_verifications, Verification)
    paper_lims, checker = [], None
    if a.paper_dir:
        pd = Path(a.paper_dir)
        checker = ScopeChecker(*load_paper_side(str(pd / "paper_side.json")))
        if (pd / "limitations.json").is_file():
            paper_lims = load(pd / "limitations.json", Limitation)
    from codeside.verify3b import paper_side_origin
    origin = paper_side_origin(pd / "paper_side.json") if a.paper_dir else "v1"
    findings, report = integrate(art["artifact_id"], code_lims, code_vers, paper_lims, checker,
                                 Rules(a.strict_scope), Context(paper_origin=origin))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([f.model_dump(mode="json") for f in findings], indent=1, ensure_ascii=False))
    out.with_suffix(".report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in report.items() if k != "llm_records"}))


if __name__ == "__main__":
    main()
