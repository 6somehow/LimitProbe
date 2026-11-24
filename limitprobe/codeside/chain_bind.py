"""Step 4: express names of a callee in terms of the entry function, along one call chain.

A region's path prefix holds conditions from several functions of the call chain, each in its own names
(`head_dim` in the entry, `d` in a kernel three calls down). The witness solver treated them as unrelated
inputs, so it could "solve" `d not in {16, 32, 64, 128}` under `head_dim in {16, 32, 64, 128}` although `d`
is the same value (checklimits/REQUESTS_TO_STEP4.md, request 2).

`ChainBinder.term(expr)` rewrites an expression of any function on the chain into names of the entry function:

  1. a local name is replaced by its definition in that function (`b, n, h, d = x.shape` gives `d -> x.shape[3]`);
  2. a parameter is replaced by the argument at the call site (`triton_bnhd_pool(k, block_size)`: `x -> k`),
     or by its constant default when the call does not pass it;
  3. the result is rewritten again in the caller, up to the entry function.

A rewrite is refused (None) whenever the value at the check may differ from the text:
  * a local without a single definition before the line (assigned in a loop or a branch, augmented, ...);
  * a definition whose right-hand side is re-assigned between the definition and the line;
  * a parameter that is re-assigned before the line (`q = q.transpose(1, 2)`), or that the call fills
    through *args / **kwargs;
  * a name that several functions of the chain define with different meanings (reported as ambiguous).
Names that no function on the chain defines (globals, modules, builtins) are kept as they are.

Which function does a path-prefix entry belong to? `ChainBinder.frame_of(expr)` answers from the source:
the function on the chain that has this test (or its negation) in an `if` / `while` / `assert` before the
call. If no function or several have it, the names decide (all owned by one function), else it is left alone.
The region's own condition always belongs to the last function of the chain.
"""

from __future__ import annotations

import ast
from typing import Optional

from codeside.callgraph import CallSite, Func, RepoCallGraph, _own_nodes
from codeside.dedup import normalise


def _stores(fn: ast.AST) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for n in _own_nodes(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            out.setdefault(n.id, []).append(n.lineno)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.setdefault(n.name, []).append(n.lineno)
    return out


def _pairs(stmt: ast.stmt) -> list[tuple[str, ast.AST]]:
    """(name, defining expression) for `a = e`, `a, b = e1, e2` and `a, b = x.shape`."""
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return []
    tgt, val = stmt.targets[0], stmt.value
    if isinstance(tgt, ast.Name):
        return [(tgt.id, val)]
    if isinstance(tgt, (ast.Tuple, ast.List)) and all(isinstance(e, ast.Name) for e in tgt.elts):
        if isinstance(val, (ast.Tuple, ast.List)) and len(val.elts) == len(tgt.elts):
            return [(e.id, v) for e, v in zip(tgt.elts, val.elts)]
        if isinstance(val, (ast.Attribute, ast.Call)) and ast.unparse(val).endswith(("shape", "size()")):
            return [(e.id, ast.Subscript(value=val, slice=ast.Constant(i), ctx=ast.Load()))
                    for i, e in enumerate(tgt.elts) if e.id != "_"]
    return []


def frame_definitions(fn: ast.AST, line: int) -> dict[str, ast.AST]:
    """Local name -> the expression that defines its value at `line`.

    A name qualifies when it is assigned once in the whole function, or when all its assignments are plain
    statements of the function body (not inside a loop or a branch) and the last one before `line` is taken.
    The right-hand side must not mention the name itself, and none of its names may be re-assigned between
    the definition and `line`.
    """
    stores = _stores(fn)
    top: dict[str, list[tuple[int, ast.AST]]] = {}
    nested: dict[str, list[tuple[int, ast.AST]]] = {}
    body = set(map(id, fn.body))
    for n in _own_nodes(fn):
        if isinstance(n, ast.Assign):
            for name, rhs in _pairs(n):
                (top if id(n) in body else nested).setdefault(name, []).append((n.lineno, rhs))
    out: dict[str, ast.AST] = {}
    for name, count in stores.items():
        defs = sorted(top.get(name, []), key=lambda d: d[0])
        if len(count) == 1 and not defs:
            defs = nested.get(name, [])
        elif len(defs) != len(count):  # some assignment is not a plain top-level one
            continue
        before = [d for d in defs if d[0] < line]
        if not before:
            continue
        at, rhs = before[-1]
        if isinstance(rhs, ast.Lambda):
            continue
        names = {x.id for x in ast.walk(rhs) if isinstance(x, ast.Name)}
        if name in names:
            continue
        if any(at < ln < line for m in names for ln in stores.get(m, [])):
            continue
        out[name] = rhs
    return out


class _Sub(ast.NodeTransformer):
    def __init__(self, table: dict[str, ast.AST]):
        self.table = table

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id in self.table:
            return ast.parse(ast.unparse(self.table[node.id]), mode="eval").body  # a fresh copy
        return node


def _names(node: ast.AST) -> set[str]:
    return {x.id for x in ast.walk(node) if isinstance(x, ast.Name)}


class _Frame:
    def __init__(self, fn: Func, line: int, call: Optional[CallSite]):
        self.fn, self.line, self.call = fn, line, call
        self.params = fn.all_params()
        self.stores = _stores(fn.node)
        self.defs = frame_definitions(fn.node, line)
        a = fn.node.args
        pos = [*a.posonlyargs, *a.args]
        self.defaults = {p.arg: d for p, d in zip(pos[len(pos) - len(a.defaults):], a.defaults)}
        self.defaults.update({p.arg: d for p, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None})
        self.tests: set[str] = set()  # conditions that hold or fail on the way to `line`, normalised, both signs
        for n in _own_nodes(fn.node):
            test = getattr(n, "test", None) if isinstance(n, (ast.If, ast.While, ast.Assert, ast.IfExp)) else None
            if test is not None and n.lineno <= line:
                src = ast.unparse(test)
                self.tests |= {normalise(src), normalise(f"not ({src})")}

    def owns(self, name: str) -> bool:
        return name in self.params or name in self.stores


class ChainBinder:
    """Rewrites names of the functions on one call chain into names of the entry function."""

    def __init__(self, graph: RepoCallGraph, entry: str, chain: list[CallSite], target_line: int):
        self.chain = chain
        ids = [entry, *[c.callee for c in chain]]
        lines = [*[c.line for c in chain], target_line]
        self.frames = [_Frame(graph.funcs[f], ln, chain[i - 1] if i else None)
                       for i, (f, ln) in enumerate(zip(ids, lines))]
        self.certain = all(c.certain and not c.star for c in chain)
        self.ambiguous: dict[str, list[str]] = {}
        self.refused: dict[str, str] = {}

    def _in_frame(self, node: ast.AST, i: int) -> Optional[ast.AST]:
        """`node` (names of frame i) rewritten into names of frame i-1 (or of the entry if i == 0)."""
        fr = self.frames[i]
        for _ in range(6):  # local definitions, to a fixed point
            hit = {n: fr.defs[n] for n in _names(node) if n in fr.defs}
            if not hit:
                break
            node = ast.fix_missing_locations(_Sub(hit).visit(node))
        table: dict[str, ast.AST] = {}
        for n in _names(node):
            if n in fr.defs:
                raise _Refuse(f"definition of `{n}` is circular")
            if n in fr.params:
                if any(ln < fr.line for ln in fr.stores.get(n, [])):
                    raise _Refuse(f"parameter `{n}` is re-assigned before line {fr.line}")
                if i == 0:
                    continue
                if n in fr.call.args:
                    table[n] = ast.parse(fr.call.args[n], mode="eval").body
                elif fr.call.star or fr.call.resolved_by == "reference":
                    raise _Refuse(f"the call does not show what `{n}` receives")
                elif isinstance(fr.defaults.get(n), ast.Constant):
                    table[n] = fr.defaults[n]
                else:
                    raise _Refuse(f"the call passes no `{n}`")
            elif n in fr.stores:
                raise _Refuse(f"local `{n}` has no single definition before line {fr.line}")
        if table:
            node = ast.fix_missing_locations(_Sub(table).visit(node))
        return node

    def _term_from(self, expr: str, i: int) -> str:
        node = ast.parse(expr, mode="eval").body
        for j in range(i, -1, -1):
            node = self._in_frame(node, j)
        return ast.unparse(node)

    def frame_of(self, expr: str) -> Optional[int]:
        """Index of the function on the chain that a path-prefix entry was taken from, or None."""
        try:
            names = _names(ast.parse(expr, mode="eval"))
        except SyntaxError:
            return None
        key = normalise(expr)
        by_test = [i for i, fr in enumerate(self.frames) if key in fr.tests]
        if len(by_test) == 1:
            return by_test[0]
        owners = [i for i, fr in enumerate(self.frames) if any(fr.owns(n) for n in names)]
        if by_test:
            owners = [i for i in owners if i in by_test]
        return owners[0] if len(owners) == 1 else None

    def rewrite(self, expr: str, frame: Optional[int]) -> Optional[str]:
        """`expr`, read in function `frame` of the chain, in names of the entry function. None if refused or unchanged."""
        if frame is None:
            return None
        try:
            out = self._term_from(expr, frame)
        except _Refuse as r:
            self.refused[expr] = f"{self.frames[frame].fn.id}: {r}"
            return None
        except (SyntaxError, RecursionError, ValueError):
            return None
        return None if normalise(out) == normalise(expr) else out

    @property
    def last(self) -> int:
        return len(self.frames) - 1

    def term(self, expr: str) -> Optional[str]:
        """`expr` in names of the entry function, or None (same text, refused, or ambiguous)."""
        try:
            names = _names(ast.parse(expr, mode="eval"))
        except SyntaxError:
            return None
        owners = [i for i, fr in enumerate(self.frames) if any(fr.owns(n) for n in names)]
        if not owners:
            return None
        results = {}
        for i in owners:
            # in frame i the names it does not own are free names (closure or global): they keep their text
            try:
                results[i] = self._term_from(expr, i)
            except _Refuse as r:
                self.refused[expr] = f"{self.frames[i].fn.id}: {r}"
                return None
            except (SyntaxError, RecursionError, ValueError):
                return None
        distinct = sorted(set(results.values()))
        if len(distinct) > 1:
            self.ambiguous[expr] = [f"{self.frames[i].fn.qual}: {t}" for i, t in results.items()]
            return None
        self.refused.pop(expr, None)
        return None if distinct[0] == expr else distinct[0]


class _Refuse(Exception):
    pass
