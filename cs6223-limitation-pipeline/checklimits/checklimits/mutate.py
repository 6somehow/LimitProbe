"""Mutants of the target decision (SCORECARD "mutation"; CONFIDENCE_SPEC defeater D3).

Operators (fixed set): negate the condition, swap a comparison operator (== <-> !=, < <-> <=,
> <-> >=), delete the statement (assert / raise), add 1 to / subtract 1 from an integer constant.
Only the statement at Region.location is mutated. Edits are made on the source text so every
mutant has the same line count as the original: location-based oracles keep working.
Mutants are written into a temporary copy of the repository, never into third_party/.
Equivalent mutants are possible, which is why the rule uses a Wilson lower bound, not 1.0.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

_SWAP = {"==": "!=", "!=": "==", "<": "<=", "<=": "<", ">": ">=", ">=": ">"}
_OP_SYMBOL = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}
_OP_RE = re.compile(r"==|!=|<=|>=|<|>")


@dataclass
class Mutant:
    operator: str
    line: int
    original: str  # the statement's first line
    mutated: str   # the same line after the edit
    source: str    # complete mutated file text


class _Text:
    """Maps (lineno, utf-8 col) positions of the AST to character offsets in the source."""

    def __init__(self, src: str) -> None:
        self.src = src
        self.lines = src.splitlines(keepends=True)
        self.starts = [0]
        for l in self.lines:
            self.starts.append(self.starts[-1] + len(l))

    def off(self, lineno: int, col: int) -> int:
        line = self.lines[lineno - 1]
        return self.starts[lineno - 1] + len(line.encode()[:col].decode())

    def span(self, node: ast.AST) -> tuple[int, int]:
        return self.off(node.lineno, node.col_offset), self.off(node.end_lineno, node.end_col_offset)


def _target_stmt(tree: ast.AST, line: int):
    for n in ast.walk(tree):
        if isinstance(n, ast.stmt) and n.lineno == line and not isinstance(
                n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return n
    return None


def generate(src: str, line: int) -> list[Mutant]:
    tree = ast.parse(src)
    st = _target_stmt(tree, line)
    if st is None:
        return []
    t = _Text(src)
    out: list[tuple[str, str]] = []  # (operator, new full source)

    def replace(a: int, b: int, new: str) -> str:
        return src[:a] + new + src[b:]

    test = getattr(st, "test", None) if isinstance(st, (ast.Assert, ast.If, ast.While)) else None
    if test is not None:
        a, b = t.span(test)
        out.append(("negate_condition", replace(a, b, f"not ({src[a:b]})")))
        for cmp_node in [n for n in ast.walk(test) if isinstance(n, ast.Compare)]:
            left_end = t.span(cmp_node.left)[1]
            for op, comp in zip(cmp_node.ops, cmp_node.comparators):
                sym = _OP_SYMBOL.get(type(op))
                if sym is None:
                    continue
                c_start = t.span(comp)[0]
                m = _OP_RE.search(src, left_end, c_start)
                if m and m.group(0) == sym:
                    out.append((f"swap_comparison {sym}->{_SWAP[sym]}", replace(m.start(), m.end(), _SWAP[sym])))
                left_end = t.span(comp)[1]
        for c in [n for n in ast.walk(test) if isinstance(n, ast.Constant)
                  and isinstance(n.value, int) and not isinstance(n.value, bool)]:
            ca, cb = t.span(c)
            out.append((f"constant {c.value}->{c.value + 1}", replace(ca, cb, str(c.value + 1))))
            out.append((f"constant {c.value}->{c.value - 1}", replace(ca, cb, str(c.value - 1))))
    if isinstance(st, (ast.Assert, ast.Raise)):
        a, b = t.span(st)
        out.append(("delete_statement", replace(a, b, "pass" + "\n" * (st.end_lineno - st.lineno))))

    first_line = lambda s: s.splitlines()[line - 1]
    mutants, seen = [], set()
    for op, new in out:
        if new == src or new in seen or new.count("\n") != src.count("\n"):
            continue
        try:
            ast.parse(new)
        except SyntaxError:
            continue
        seen.add(new)
        mutants.append(Mutant(op, line, first_line(src).strip(), first_line(new).strip(), new))
    return mutants
