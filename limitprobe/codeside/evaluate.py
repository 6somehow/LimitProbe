"""Compare an extracted region table with a gold one.

A predicted region matches a gold region when
  * both are in the same file and function,
  * the outcome is the same, and
  * the predicted line lies inside the gold line range widened by `tol`
    (for `mechanism` regions the line is ignored: the default path has no single line).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from schema.models import Region


def _func(r: Region) -> tuple[str, str]:
    fn = r.location.function or ""
    return r.location.file, fn.split("::")[-1]


def _match(p: Region, g: Region, tol: int) -> bool:
    if _func(p) != _func(g) or p.outcome != g.outcome:
        return False
    if g.outcome == "mechanism":
        return True
    lo = g.location.line_start - tol
    hi = (g.location.line_end or g.location.line_start) + tol
    return lo <= p.location.line_start <= hi


@dataclass
class RegionEval:
    matched: dict[str, list[str]]  # gold id -> predicted ids
    missed: list[str]
    extra: list[str]

    @property
    def recall(self) -> float:
        total = len(self.matched) + len(self.missed)
        return len(self.matched) / total if total else 0.0

    def report(self, gold: list[Region], pred: list[Region]) -> str:
        g = {r.region_id: r for r in gold}
        p = {r.region_id: r for r in pred}
        lines = [f"gold regions: {len(gold)}   predicted: {len(pred)}",
                 f"recall: {len(self.matched)}/{len(gold)} = {self.recall:.2f}",
                 f"unmatched predictions (review: noise, or missing from gold?): {len(self.extra)}", "",
                 "missed gold regions:"]
        for gid in self.missed:
            r = g[gid]
            lines.append(f"  {gid} {r.outcome:<17} {_func(r)[1]}:{r.location.line_start}  {r.condition.expr}")
        lines += ["", "unmatched predictions:"]
        for pid in self.extra:
            r = p[pid]
            lines.append(f"  {pid} {r.outcome:<17} {_func(r)[1]}:{r.location.line_start}  {r.condition.expr[:80]}")
        return "\n".join(lines)


def _distance(p: Region, g: Region) -> int:
    if g.outcome == "mechanism":
        return 0
    lo, hi = g.location.line_start, g.location.line_end or g.location.line_start
    line = p.location.line_start
    return 0 if lo <= line <= hi else min(abs(line - lo), abs(line - hi))


def _one_to_one(pred: list[Region], gold: list[Region], tol: int) -> RegionEval:
    """Each prediction can claim one gold region; the nearest pairs are taken first."""
    pairs = sorted((_distance(p, g), i, j) for i, p in enumerate(pred) for j, g in enumerate(gold)
                   if _match(p, g, tol))
    matched: dict[str, list[str]] = {}
    used: set[str] = set()
    for _, i, j in pairs:
        pid, gid = pred[i].region_id, gold[j].region_id
        if pid not in used and gid not in matched:
            matched[gid] = [pid]
            used.add(pid)
    return RegionEval(matched=matched, missed=[g.region_id for g in gold if g.region_id not in matched],
                      extra=[p.region_id for p in pred if p.region_id not in used])


def evaluate_regions(pred: list[Region], gold: list[Region], tol: int = 2, one_to_one: bool = False) -> RegionEval:
    if one_to_one:
        return _one_to_one(pred, gold, tol)
    matched: dict[str, list[str]] = {}
    used: set[str] = set()
    for g in gold:
        hits = [p.region_id for p in pred if _match(p, g, tol)]
        if hits:
            matched[g.region_id] = hits
            used.update(hits)
    missed = [g.region_id for g in gold if g.region_id not in matched]
    extra = [p.region_id for p in pred if p.region_id not in used]
    return RegionEval(matched=matched, missed=missed, extra=extra)


def _norm(expr: str) -> Optional[str]:
    """Canonical text of a condition; folds `not (a OP b)` into `a NEG(OP) b`.

    This is a cheap proxy for semantic equivalence; replace with a z3 check later.
    """
    import ast as _ast

    neg = {_ast.Eq: _ast.NotEq, _ast.NotEq: _ast.Eq, _ast.Lt: _ast.GtE, _ast.GtE: _ast.Lt,
           _ast.Gt: _ast.LtE, _ast.LtE: _ast.Gt, _ast.In: _ast.NotIn, _ast.NotIn: _ast.In,
           _ast.Is: _ast.IsNot, _ast.IsNot: _ast.Is}

    class _Fold(_ast.NodeTransformer):
        def visit_UnaryOp(self, node):
            self.generic_visit(node)
            t = node.operand
            if (isinstance(node.op, _ast.Not) and isinstance(t, _ast.Compare)
                    and len(t.ops) == 1 and type(t.ops[0]) in neg):
                return _ast.Compare(left=t.left, ops=[neg[type(t.ops[0])]()], comparators=t.comparators)
            return node

    try:
        tree = _Fold().visit(_ast.parse(expr, mode="eval"))
        return _ast.unparse(_ast.fix_missing_locations(tree))
    except SyntaxError:
        return None


def compare_routes(gold: list[Region], routes: dict[str, list[Region]], tol: int = 2,
                   meta: Optional[dict[str, dict]] = None, one_to_one: bool = False) -> str:
    """One row per route, same gold and same matching rule for every route.

    cond_exact: among matched regions whose gold condition is a Python expression,
                share whose predicted condition is identical after normalisation
                (a proxy for "got the boundary right").
    """
    meta = meta or {}
    header = ("route", "pred", "recall", "extra", "cond_exact", "rejected", "halluc_rate")
    rows = [header]
    for name, pred in routes.items():
        ev = evaluate_regions(pred, gold, tol, one_to_one)
        p = {r.region_id: r for r in pred}
        g = {r.region_id: r for r in gold}
        exact = total = 0
        for gid, pids in ev.matched.items():
            gn = _norm(g[gid].condition.expr)
            if gn is None or g[gid].outcome == "mechanism":
                continue
            total += 1
            exact += any(_norm(p[x].condition.expr) == gn for x in pids)
        m = meta.get(name, {})
        rows.append((name, str(len(pred)), f"{len(ev.matched)}/{len(gold)}", str(len(ev.extra)),
                     f"{exact}/{total}", str(m.get("rejected", "-")),
                     f"{m['hallucination_rate']:.2f}" if "hallucination_rate" in m else "-"))
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    return "\n".join("  ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows)


def region_signature(r: Region) -> tuple:
    return (r.location.function or "", r.outcome, r.location.line_start)


def stability(runs: list[list[Region]], gold: Optional[list[Region]] = None, tol: int = 0) -> dict[str, float]:
    """Mean pairwise Jaccard across repeated runs, of the regions and of the gold regions found."""

    def jaccard(a: set, b: set) -> float:
        return len(a & b) / len(a | b) if a | b else 1.0

    def mean_pairs(sets: list[set]) -> float:
        vals = [jaccard(a, b) for i, a in enumerate(sets) for b in sets[i + 1:]]
        return sum(vals) / len(vals) if vals else 1.0

    out = {"regions_jaccard": mean_pairs([{region_signature(r) for r in run} for run in runs])}
    if gold is not None:
        out["gold_jaccard"] = mean_pairs([set(evaluate_regions(run, gold, tol, True).matched) for run in runs])
    return out
