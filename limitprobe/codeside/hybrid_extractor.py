"""Step 2, route B: the static route plus an LLM that only looks for what the static route cannot see.

    route A candidates ──> 1. edges     pick targets for calls A cannot resolve   (then re-run A)
                           2. discover  add behaviour switches A's rules do not cover

Route B only ever adds: every region route A reports stays in the output.

The LLM proposes and code decides what is accepted:
  * edges:    a target must be one of the definitions code found in the repo (cf. SEA);
  * discover: line, verbatim code and every name in the condition are checked against the
              function's source (cf. RepoAudit's validator).
A failed LLM call never changes results silently: A's candidates stay and the failure goes
to the metadata.
"""

from __future__ import annotations

import ast
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from codeside.extractor import ExtractConfig, RegionExtractor, _Frame
from codeside.llm_extractor import FunctionSource, LLMClient, parse_json, validate_items
from schema.models import Region

PROMPT_VERSION = "hybrid-v3"
ROUNDS_OF_EDGES = 2
MAX_CANDIDATE_TARGETS = 12
MAX_PROMPT_CHARS = 60_000
RETRIES = 3
COMMON_METHODS = frozenset(
    "append add clear copy count extend get index insert items join keys lower pop remove replace "
    "reshape shape size split startswith endswith strip sort sum mean max min update upper values "
    "view format to cpu cuda item".split())

EDGE_SYSTEM = """You trace which function actually runs at a call site in a Python repository.
Choose only from the candidate definitions shown. If none is clearly the target, choose none.
Answer with JSON only."""

EDGE_USER = """Call site in {file}, line {line}, inside {function}:
{snippet}

Candidate definitions:
{candidates}

Answer: {{"targets": ["<candidate id>", ...], "reason": "<one sentence>"}}
List every candidate that can run here given the receiver and the surrounding code, and no other."""

DISCOVER_SYSTEM = """You look for behaviour switches a rule-based analyser missed in one function of a
research prototype. Report only what the code shown proves. Quote code verbatim. Answer with JSON only."""

DISCOVER_USER = """Entry function: {entry}
Function under review:
{code}

Already found in this function (do not repeat these):
{existing}

Report branches where a caller-supplied input, configuration value, environment or earlier state
changes which algorithm or implementation runs, even if the branch does not return early.
Skip these, they are not behaviour switches:
- performance tuning (scheduling, parallelism or kernel parameters that leave the result unchanged);
- defaults for optional arguments, and compatibility shims that keep the same behaviour;
- output format or debug options, logging, ordinary data handling;
- checks of values that no caller can influence.
Most functions have nothing to report; an empty list is the usual answer.

Labels:
- mechanism_variant: selects a variant of the mechanism, or switches to another implementation of it
- fallback: silently runs a baseline, dense or simpler implementation instead
- reject: stops execution
- env_dependent: depends on installed packages, versions or GPU model
- state_dependent: depends on module-level or cached state from earlier calls
- suspicious: e.g. a hard-coded constant that ignores a parameter in scope

Return a JSON list, empty if nothing is missing. Each item:
{{"line": <int>, "code": "<verbatim text from that line>",
  "condition": "<Python boolean expression over names in this function>",
  "outcome": "<label>", "detail": "<what happens>",
  "path_prefix": ["<enclosing conditions inside this function, outermost first>"]}}"""


@dataclass
class CallSite:
    file: str
    function: str
    line: int
    name: str
    candidates: list[str]


@dataclass
class HybridResult:
    regions: list[Region]
    meta: dict = field(default_factory=dict)


class _Tracking(RegionExtractor):
    """Route A, plus: remember what was visited and which calls stayed unresolved; follow given edges."""

    def __init__(self, cfg: ExtractConfig, edges: dict[tuple, list[str]], repo_index: "_RepoIndex"):
        super().__init__(cfg)
        self.edges = edges
        self.index = repo_index
        self.sites: dict[tuple, CallSite] = {}
        self.visited: dict[tuple[str, str], tuple[ast.FunctionDef, list[str], list[str]]] = {}

    def _analyse(self, fr: _Frame) -> list[str]:
        if fr.depth <= self.cfg.max_depth and fr.func.name != "<module>":
            self.visited.setdefault((fr.file, fr.name),
                                    (fr.func, fr.chain + [f"{fr.file}::{fr.name}"], list(fr.prefix)))
        return super()._analyse(fr)

    def _follow_calls(self, fr: _Frame, stmts: list[ast.stmt], prefix: list[str]) -> None:
        if fr.depth + 1 > self.cfg.max_depth:
            return
        for root in stmts:
            for n in ast.walk(root):
                if isinstance(n, ast.Call):
                    self._one_call(fr, n, prefix)

    def _one_call(self, fr: _Frame, call: ast.Call, prefix: list[str]) -> None:
        chain = fr.chain + [f"{fr.file}::{fr.name}"]
        f = call.func
        name, cls = None, None
        if isinstance(f, ast.Name):
            name = f.id
        elif isinstance(f, ast.Attribute):
            name = f.attr
            if isinstance(f.value, ast.Name) and f.value.id == "self":
                cls = fr.cls
        if name is None:
            return
        if isinstance(f, ast.Name) or cls:
            res = self._resolve(fr.file, name, cls)
            if res is not None:
                rel, fn = res
                qual = next(k for k, v in self._funcs[rel].items() if v is fn)
                self._analyse(_Frame(file=rel, func=fn, depth=fr.depth + 1, prefix=list(prefix), chain=chain,
                                     qual=qual, cls=cls if rel == fr.file else self._class_of(rel, qual)))
                return
        key = (fr.file, call.lineno, call.col_offset, name)
        if key in self.edges:
            for target in self.edges[key]:
                rel, qual = target.split("::")
                self._load(rel)
                self._analyse(_Frame(file=rel, func=self._funcs[rel][qual], depth=fr.depth + 1,
                                     prefix=list(prefix), chain=chain, qual=qual, cls=self._class_of(rel, qual)))
            return
        candidates = self.index.candidates(fr.file, name, f, self._imports.get(fr.file, {}))
        if candidates:
            self.sites[key] = CallSite(fr.file, fr.name, call.lineno, name, candidates)


class _RepoIndex:
    """Every function definition in the repo, so that an LLM edge can only point at real code."""

    SKIP_DIRS = {".git", "test", "tests", "__pycache__", "docs"}

    def __init__(self, repo: Path):
        self.repo = Path(repo)
        self.defs: dict[str, list[str]] = {}
        self.sources: dict[str, list[str]] = {}
        self.spans: dict[str, tuple[int, int]] = {}
        self.external: dict[str, set[str]] = {}
        self.too_many = 0
        for path in sorted(self.repo.rglob("*.py")):
            rel = path.relative_to(self.repo)
            if self.SKIP_DIRS & set(rel.parts[:-1]):
                continue
            try:
                text = path.read_text(encoding="utf-8")
                tree = ast.parse(text)
            except (SyntaxError, UnicodeDecodeError, ValueError):
                continue
            self.sources[str(rel)] = text.splitlines()
            self.external[str(rel)] = {a.asname or a.name.split(".")[0] for n in ast.walk(tree)
                                       if isinstance(n, ast.Import) for a in n.names}
            for qual, fn in RegionExtractor._index_functions(tree).items():
                tid = f"{rel}::{qual}"
                self.spans[tid] = (fn.lineno, fn.end_lineno or fn.lineno)
                parts = qual.split(".")
                self.defs.setdefault(parts[-1], []).append(tid)
                if parts[-1] == "__init__" and len(parts) == 2:  # `Foo(...)` runs Foo.__init__
                    self.defs.setdefault(parts[0], []).append(tid)

    def candidates(self, file: str, name: str, func: ast.expr, imports: dict[str, str]) -> list[str]:
        if name.startswith("__") or name in COMMON_METHODS:
            return []
        node = func
        while isinstance(node, ast.Attribute):
            node = node.value
        if isinstance(node, ast.Name) and node is not func and node.id in self.external.get(file, ()):
            repo_top = {Path(p).parts[0] for p in self.sources}
            if node.id not in repo_top:  # e.g. torch.x(), np.y()
                return []
        found = self.defs.get(name, [])
        if len(found) > MAX_CANDIDATE_TARGETS:
            self.too_many += 1
            return []
        return sorted(found, key=lambda t: (not t.startswith(f"{file}::"), t))

    def show(self, tid: str, max_lines: int = 40) -> str:
        rel, _ = tid.split("::")
        start, end = self.spans[tid]
        lines = self.sources[rel]
        body = "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, min(end, start + max_lines - 1) + 1))
        return f"[{tid}]\n{body}"


class HybridExtractor:
    def __init__(self, cfg: ExtractConfig, client: LLMClient, workers: int = 6):
        self.cfg, self.client, self.workers = cfg, client, workers
        self.index = _RepoIndex(cfg.repo)
        self.calls = 0
        self.failed: list[dict] = []
        self._edge_rejected: list[dict] = []

    # ------------------------------------------------------------------ LLM plumbing
    def _ask(self, stage: str, tag: str, system: str, user: str, expect: type):
        last = ""
        for _ in range(RETRIES):
            self.calls += 1
            try:
                return parse_json(self.client.complete(system, user), expect)
            except Exception as exc:  # malformed output, truncation, or the provider SDK's API errors
                last = f"{type(exc).__name__}: {exc}"
        self.failed.append({"stage": stage, "tag": tag, "error": last[:300]})
        return None

    def _map(self, fn, items):
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            return list(pool.map(fn, items))

    def _numbered(self, file: str, qual: str) -> tuple[str, dict[tuple[str, int], str], int, int]:
        fn = self._static._funcs[file][qual]
        lines = self.index.sources.get(file) or (Path(self.cfg.repo) / file).read_text(encoding="utf-8").splitlines()
        start = min([d.lineno for d in fn.decorator_list] + [fn.lineno])
        end = fn.end_lineno or fn.lineno
        shown = {(file, i): lines[i - 1] for i in range(start, end + 1)}
        text = "\n".join(f"{file}:{i}: {lines[i - 1]}" for i in range(start, end + 1))
        return f"# --- {file}::{qual}\n{text}", shown, start, end

    # ------------------------------------------------------------------ 1. edges
    def _run_static(self, edges: dict[tuple, list[str]]) -> _Tracking:
        rx = _Tracking(self.cfg, edges, self.index)
        rx.run()
        return rx

    def _resolve_edges(self) -> tuple[_Tracking, dict[tuple, list[str]], dict]:
        edges: dict[tuple, list[str]] = {}
        log = {"sites_asked": 0, "accepted": [], "rejected": []}
        rx = self._run_static(edges)
        for _ in range(ROUNDS_OF_EDGES):
            sites = [(k, s) for k, s in sorted(rx.sites.items()) if k not in edges]
            if not sites:
                break
            log["sites_asked"] += len(sites)
            for (key, site), targets in zip(sites, self._map(self._ask_edge, sites)):
                edges[key] = targets
                log["accepted"] += [{"site": f"{site.file}:{site.line}", "call": site.name, "target": t} for t in targets]
            log["rejected"] += self._edge_rejected
            self._edge_rejected = []
            rx = self._run_static(edges)
        return rx, edges, log

    def _ask_edge(self, item: tuple[tuple, CallSite]) -> list[str]:
        _, site = item
        lines = self.index.sources.get(site.file, [])
        lo, hi = max(site.line - 4, 1), min(site.line + 2, len(lines))
        snippet = "\n".join(f"{i}: {lines[i - 1]}" for i in range(lo, hi + 1))
        cands = "\n\n".join(self.index.show(t) for t in site.candidates)
        ans = self._ask("edges", f"{site.file}:{site.line}", EDGE_SYSTEM,
                        EDGE_USER.format(file=site.file, line=site.line, function=site.function,
                                         snippet=snippet, candidates=cands), dict)
        if ans is None:
            return []
        raw = ans.get("targets") or []
        good = [t for t in raw if t in site.candidates]
        self._edge_rejected += [{"site": f"{site.file}:{site.line}", "target": str(t),
                                 "reason": "not a candidate definition"} for t in raw if t not in site.candidates]
        return good

    # ------------------------------------------------------------------ 2. discover
    def _discover(self, rx: _Tracking, regions: list[Region]) -> tuple[list[Region], dict]:
        funcs = sorted(rx.visited)
        by_fn: dict[str, list[Region]] = {}
        for r in regions:
            by_fn.setdefault(r.location.function or "", []).append(r)
        results = self._map(lambda k: self._discover_one(k, rx, by_fn.get(f"{k[0]}::{k[1]}", [])), funcs)
        added: list[Region] = []
        log = {"functions": len(funcs), "raw": 0, "rejected": [], "duplicates": 0}
        for new, raw, rejected, dups in results:
            added += new
            log["raw"] += raw
            log["rejected"] += rejected
            log["duplicates"] += dups
        added.sort(key=lambda r: (r.location.file, r.location.line_start))
        added = [r.model_copy(update={"region_id": f"D{i + 1:03d}"}) for i, r in enumerate(added)]
        return added, log

    def _discover_one(self, key: tuple[str, str], rx: _Tracking, existing: list[Region]):
        file, qual = key
        if qual not in rx._funcs.get(file, {}):
            return [], 0, [], 0
        text, shown, start, end = self._numbered(file, qual)
        if len(text) > MAX_PROMPT_CHARS:
            self.failed.append({"stage": "discover", "tag": f"{file}::{qual}", "error": "function too long, skipped"})
            return [], 0, [], 0
        listed = "\n".join(f"- line {r.location.line_start}: {r.outcome}: {r.condition.expr}" for r in existing) or "(none)"
        ans = self._ask("discover", f"{file}::{qual}", DISCOVER_SYSTEM,
                        DISCOVER_USER.format(entry=self.cfg.entry, code=text, existing=listed), list)
        if not ans:
            return [], 0, [], 0
        taken = {r.location.line_start for r in existing}
        fs = FunctionSource(file, qual, start, end, text)
        good, rejected, dups = [], [], 0
        _, chain, prefix = rx.visited[key]
        for it in ans:
            if not isinstance(it, dict):
                rejected.append({"item": str(it)[:200], "_reason": "not an object"})
                continue
            line, code = it.get("line"), str(it.get("code") or "").strip()
            if it.get("outcome") == "mechanism":
                rejected.append({**it, "_reason": "mechanism is not a discovery"})
            elif not isinstance(line, int) or len(code) < 3 or code not in shown.get((file, line), ""):
                rejected.append({**it, "_reason": "code quote not on that line"})
            elif line in taken:
                dups += 1
            else:
                regs, bad = validate_items([{**it, "file": file, "function": qual}], [fs], self.cfg)
                rejected += bad
                for r in regs:
                    taken.add(line)
                    cond = r.condition.model_copy(update={"path_prefix": prefix + r.condition.path_prefix})
                    good.append(r.model_copy(update={"condition": cond, "call_chain": chain}))
        return good, len(ans), rejected, dups

    # ------------------------------------------------------------------ driver
    def run(self) -> HybridResult:
        t0 = time.time()
        rx, edges, edge_log = self._resolve_edges()
        self._static = rx
        llm_targets = {t for ts in edges.values() for t in ts}
        candidates = [r.model_copy(update={"provenance": "llm", "notes": "reached through an LLM-selected call edge"})
                      if set(r.call_chain) & llm_targets else r for r in rx.regions]
        added, discover_log = self._discover(rx, candidates)
        raw = discover_log["raw"] + len(edge_log["accepted"]) + len(edge_log["rejected"])
        rejected = len(discover_log["rejected"]) + len(edge_log["rejected"])
        meta = {
            "route": "hybrid", "prompt_version": PROMPT_VERSION, "llm_calls": self.calls,
            "seconds": round(time.time() - t0, 1),
            "candidates_from_static": len(candidates), "added_regions": len(added),
            "final_regions": len(candidates) + len(added),
            "failed_calls": self.failed, "raw_items": raw, "rejected": rejected,
            "hallucination_rate": rejected / raw if raw else 0.0,
            "edges": edge_log, "discover": discover_log,
            "unresolved_too_many_candidates": self.index.too_many,
        }
        return HybridResult(regions=candidates + added, meta=meta)


def extract_hybrid(cfg: ExtractConfig, client: LLMClient, workers: int = 6) -> HybridResult:
    return HybridExtractor(cfg, client, workers).run()
