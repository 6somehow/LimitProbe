"""Deterministic clean-up of route B's additions (no LLM). Route A's regions are never removed.

Blind review of B's output found two kinds of repeats that code can recognise:

  1. checked upstream   a kernel re-checks what its only callers already checked
                        (e.g. `head_dim not in {...}` in triton_flash_decode, whose only caller
                        triton_flash_attention asserts the same) -> the inner one is dropped;
  2. same switch again  one configuration switch tested in several functions of one file
                        (e.g. NNSMITH_LIMNF_V in four places) -> among B's additions the first one
                        is kept and the other locations are listed in its notes. An addition with
                        the same check as a route-A region in another function is kept with a note
                        (it may be another integration, e.g. the vLLM path next to the HF path).

Conditions are compared after normalisation (`not (a == b)` and `a != b` are the same).
"Only callers" uses a name-based call graph over the repo; a name defined in more than
MAX_DEFS places is treated as unknown, so such a function is never considered checked upstream.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

from codeside.hybrid_extractor import _RepoIndex
from codeside.extractor import RegionExtractor
from schema.models import Region

MAX_DEFS = 3
MAX_DEPTH = 3
_INVERT = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In,
           ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt}


def normalise(expr: str) -> str:
    try:
        node = ast.parse(expr.strip(), mode="eval").body
    except (SyntaxError, ValueError):
        return " ".join(expr.split())
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not) and isinstance(node.operand, ast.Compare)
            and len(node.operand.ops) == 1 and type(node.operand.ops[0]) in _INVERT):
        c = node.operand
        node = ast.Compare(left=c.left, ops=[_INVERT[type(c.ops[0])]()], comparators=c.comparators)
    return ast.unparse(node)


class CallGraph:
    """function id (`file::qual`) -> ids of functions that call it, by name."""

    def __init__(self, repo: Path):
        self.index = _RepoIndex(repo)
        self.callers: dict[str, set[str]] = {}
        for rel, lines in self.index.sources.items():
            try:
                tree = ast.parse("\n".join(lines))
            except (SyntaxError, ValueError):
                continue
            for qual, fn in RegionExtractor._index_functions(tree).items():
                caller = f"{rel}::{qual}"
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call):
                        name = n.func.id if isinstance(n.func, ast.Name) else (
                            n.func.attr if isinstance(n.func, ast.Attribute) else None)
                        targets = self.index.defs.get(name or "", [])
                        if 0 < len(targets) <= MAX_DEFS:
                            for t in targets:
                                if t != caller:
                                    self.callers.setdefault(t, set()).add(caller)


def dedup_additions(repo: Path, static: list[Region], added: list[Region],
                    graph: CallGraph | None = None) -> tuple[list[Region], dict]:
    graph = graph or CallGraph(Path(repo))
    key = lambda r: (normalise(r.condition.expr), r.outcome)
    checks: dict[tuple, set[str]] = {}
    for r in static + added:
        checks.setdefault(key(r), set()).add(r.location.function or "")

    def checked_upstream(fn: str, k: tuple) -> bool:
        @lru_cache(maxsize=None)
        def covered(f: str, depth: int) -> bool:
            # f is covered if it checks k itself, or every caller of f is covered
            if f in checks[k] and f != fn:
                return True
            if depth >= MAX_DEPTH:
                return False
            callers = graph.callers.get(f, set())
            return bool(callers) and all(covered(c, depth + 1) for c in callers)
        callers = graph.callers.get(fn, set())
        return bool(callers) and all(covered(c, 1) for c in callers)

    log = {"checked_upstream": [], "merged_same_switch": []}
    survivors = []
    for r in added:
        if checked_upstream(r.location.function or "", key(r)):
            log["checked_upstream"].append(f"{r.location.file}:{r.location.line_start}")
        else:
            survivors.append(r)
    kept: list[Region] = []
    first: dict[tuple, int] = {}
    static_lines = {}
    for r in static:
        static_lines.setdefault((r.location.file, *key(r)), []).append(r.location.line_start)
    for r in sorted(survivors, key=lambda r: (r.location.file, r.location.line_start)):
        k = (r.location.file, *key(r))
        if k in static_lines:  # kept: another code path with the same check; route A is never edited
            note = f"same check as route-A region at line {static_lines[k][0]}"
            r = r.model_copy(update={"notes": f"{r.notes or ''}; {note}".lstrip("; ")})
        if k in first:
            i = first[k]
            note = kept[i].notes or ""
            kept[i] = kept[i].model_copy(update={"notes": f"{note}; same check also at line {r.location.line_start}".lstrip("; ")})
            log["merged_same_switch"].append(f"{r.location.file}:{r.location.line_start}")
        else:
            first[k] = len(kept)
            kept.append(r)
    return kept, log
