"""Step 3b, questions 2 and 3: is a region inside the paper's scope, and was it evaluated?

Deterministic, no LLM. Region conditions are translated to z3 after mapping code names to
paper parameters through Bindings. Anything that cannot be translated yields `unknown`
or None, never a guess.
"""

from __future__ import annotations

import ast
import itertools
import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import z3

from schema.models import Binding, Condition, EvalPoint, ScopeItem


class Untranslatable(Exception):
    pass


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9Ͱ-Ͽ]+", "_", name.lower()).strip("_")


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class _Translator:
    """Python expression -> z3 term. Concrete values stay Python numbers so ceil() can fold."""

    def __init__(self, env: dict[str, Any]):
        self.env = env
        self.vars: dict[str, z3.ArithRef] = {}

    def _var(self, name: str):
        return self.vars.setdefault(name, z3.Real(name))

    def expr(self, n: ast.AST):
        if isinstance(n, ast.Expression):
            return self.expr(n.body)
        if isinstance(n, ast.Constant):
            if _num(n.value) or isinstance(n.value, bool):
                return n.value
            raise Untranslatable(f"constant {n.value!r}")
        if isinstance(n, ast.Name):
            return self.env[n.id] if n.id in self.env else self._var(n.id)
        if isinstance(n, ast.BoolOp):
            parts = [self.expr(v) for v in n.values]
            return z3.And(*parts) if isinstance(n.op, ast.And) else z3.Or(*parts)
        if isinstance(n, ast.UnaryOp):
            v = self.expr(n.operand)
            if isinstance(n.op, ast.Not):
                return (not v) if isinstance(v, bool) else z3.Not(v)
            if isinstance(n.op, ast.USub):
                return -v
            raise Untranslatable("unary op")
        if isinstance(n, ast.BinOp):
            return self._binop(n)
        if isinstance(n, ast.Compare):
            return self._compare(n)
        if isinstance(n, ast.Call):
            return self._call(n)
        raise Untranslatable(type(n).__name__)

    def _binop(self, n: ast.BinOp):
        a, b = self.expr(n.left), self.expr(n.right)
        concrete = _num(a) and _num(b)
        if isinstance(n.op, ast.Add):
            return a + b
        if isinstance(n.op, ast.Sub):
            return a - b
        if isinstance(n.op, ast.Mult):
            return a * b
        if isinstance(n.op, ast.Div):
            return a / b
        if concrete and isinstance(n.op, ast.FloorDiv):
            return a // b
        if concrete and isinstance(n.op, ast.Mod):
            return a % b
        raise Untranslatable("non-concrete // or % or unsupported operator")

    def _compare(self, n: ast.Compare):
        parts, left = [], self.expr(n.left)
        for op, comp in zip(n.ops, n.comparators):
            if isinstance(op, (ast.In, ast.NotIn)):
                if not isinstance(comp, (ast.Set, ast.List, ast.Tuple)):
                    raise Untranslatable("membership in a non-literal")
                vals = [self.expr(e) for e in comp.elts]
                eqs = [left == v for v in vals]
                test = z3.Or(*[e if not isinstance(e, bool) else z3.BoolVal(e) for e in eqs])
                parts.append(test if isinstance(op, ast.In) else z3.Not(test))
                continue
            right = self.expr(comp)
            table = {ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b, ast.Lt: lambda a, b: a < b,
                     ast.LtE: lambda a, b: a <= b, ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b}
            if type(op) not in table:
                raise Untranslatable(type(op).__name__)
            parts.append(table[type(op)](left, right))
            left = right
        parts = [z3.BoolVal(p) if isinstance(p, bool) else p for p in parts]
        return parts[0] if len(parts) == 1 else z3.And(*parts)

    def _call(self, n: ast.Call):
        name = ast.unparse(n.func)
        args = [self.expr(a) for a in n.args]
        if name == "max" and args:
            out = args[0]
            for a in args[1:]:
                out = max(out, a) if _num(out) and _num(a) else z3.If(out >= a, out, a)
            return out
        if name == "min" and args:
            out = args[0]
            for a in args[1:]:
                out = min(out, a) if _num(out) and _num(a) else z3.If(out <= a, out, a)
            return out
        if name in ("math.ceil", "ceil") and len(args) == 1 and _num(args[0]):
            return math.ceil(args[0])
        if name in ("math.floor", "floor") and len(args) == 1 and _num(args[0]):
            return math.floor(args[0])
        raise Untranslatable(f"call {name}")


@dataclass
class ScopeResult:
    scope_status: str
    evaluated_in_paper: Optional[bool]
    bound_params: list[str] = field(default_factory=list)
    unbound_names: list[str] = field(default_factory=list)
    dropped_prefix: list[str] = field(default_factory=list)
    reason: str = ""


class ScopeChecker:
    def __init__(self, scope: list[ScopeItem], eval_points: list[EvalPoint], bindings: list[Binding]):
        self.eval_points = eval_points
        items = {_norm(s.param): s for s in scope}
        self.by_symbol: dict[str, ScopeItem] = {}
        for b in bindings:
            if b.kind == "mechanism_entry":
                continue
            item = items.get(_norm(b.paper_term)) or items.get(_norm(b.code_symbol))
            if item is not None:
                self.by_symbol[b.code_symbol] = item

    @staticmethod
    def _parse(expr: str) -> Optional[ast.Expression]:
        try:
            return ast.parse(expr, mode="eval")
        except SyntaxError:
            return None

    def _solve(self, trees: list[ast.Expression], env: dict[str, Any], extra=()) -> bool:
        try:
            return self._solve_z3(trees, env, extra)
        except z3.Z3Exception as exc:  # e.g. `not x` where x translated to an integer
            raise Untranslatable(f"z3 rejected the condition: {exc}") from exc

    def _solve_z3(self, trees: list[ast.Expression], env: dict[str, Any], extra=()) -> bool:
        tr = _Translator(env)
        solver = z3.Solver()
        solver.set("timeout", 5000)
        for t in trees:
            term = tr.expr(t)
            if isinstance(term, bool):
                term = z3.BoolVal(term)
            elif not z3.is_bool(term):  # e.g. a bare integer name used as a truth value
                raise Untranslatable(f"not a boolean condition: {ast.unparse(t)}")
            solver.add(term)
        for fn in extra:
            fn(tr, solver)
        res = solver.check()
        if res == z3.unknown:
            raise Untranslatable("solver returned unknown")
        return res == z3.sat

    def check(self, condition: Optional[Condition]) -> ScopeResult:
        tree = self._parse(condition.expr) if condition else None
        if tree is None:
            return ScopeResult("unknown", None, reason="condition is not a Python expression")
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        trees, dropped = [tree], []
        for p in condition.path_prefix:
            pt = self._parse(p)
            if pt is None:
                dropped.append(p)
                continue
            try:
                self._solve([pt], {})
                trees.append(pt)
            except Untranslatable:
                dropped.append(p)
        bound = sorted(names & set(self.by_symbol))
        unbound = sorted(names - set(self.by_symbol))
        res = ScopeResult("unknown", None, bound, unbound, dropped)
        if not bound:
            res.reason = "no Binding connects this condition to a scope item"
            return res
        try:
            feasible = self._in_scope(trees, names)
            res.evaluated_in_paper = self._evaluated(trees)
        except Untranslatable as exc:
            res.reason = f"cannot translate: {exc}"
            return res
        if not feasible:
            res.scope_status, res.reason = "out_of_scope", "condition has no solution inside the scope"
        elif any(not self.by_symbol[s].explicit for s in bound):
            res.scope_status, res.reason = "scope_edge", "only meets scope inferred from the evaluation"
        else:
            res.scope_status, res.reason = "in_scope", "condition has a solution inside the scope"
        return res

    def _in_scope(self, trees: list[ast.Expression], names: set[str]) -> bool:
        sets, intervals = {}, {}
        for sym in set(self.by_symbol) & self._all_names(trees):
            item = self.by_symbol[sym]
            if item.kind == "set" and item.values and all(_num(v) for v in item.values):
                sets[sym] = item.values
            elif item.kind == "interval":
                intervals[sym] = item
        def bounds(tr: _Translator, solver: z3.Solver) -> None:
            for sym, it in intervals.items():
                if it.lower is not None:
                    solver.add(tr._var(sym) >= it.lower)
                if it.upper is not None:
                    solver.add(tr._var(sym) <= it.upper)
        keys = list(sets)
        for combo in itertools.product(*(sets[k] for k in keys)):
            if self._solve(trees, dict(zip(keys, combo)), extra=[bounds]):
                return True
        return False

    @staticmethod
    def _all_names(trees: list[ast.Expression]) -> set[str]:
        return {n.id for t in trees for n in ast.walk(t) if isinstance(n, ast.Name)}

    def _evaluated(self, trees: list[ast.Expression]) -> Optional[bool]:
        """True: a point satisfies the condition. False: none can. None: points don't pin it down."""
        if not self.eval_points:
            return None
        names = self._all_names(trees)
        undecided = False
        for ep in self.eval_points:
            config = {_norm(k): v for k, v in ep.config.items()}
            env = {}
            for sym in names:
                item = self.by_symbol.get(sym)
                if item is None:
                    continue
                v = config.get(_norm(item.param))
                if not _num(v):  # EvalPoint configs may use the short name (e.g. `tau`, not the scope param)
                    v = config.get(_norm(sym))
                if _num(v):
                    env[sym] = v
            if not self._solve(trees, env):
                continue
            if names <= set(env):
                return True
            undecided = True
        return None if undecided else False
