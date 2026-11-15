"""Step 4: witness_hint for a code-side limitation (docs/09_step4_findings.md, format `witness-v1`).

Given the region condition, its path prefix and the paper scope, find two concrete points with z3:

  trigger    satisfies path prefix and condition: the limitation's branch is taken;
  contrast   satisfies the path prefix but not the condition, as close to `trigger` as possible:
             the normal path. Together they sit on both sides of the boundary (spec §4.4).

Both points stay inside the paper scope for every name a Binding maps to a scope item. A name that
the scope does not constrain prefers an EvalPoint value of the paper.

Names in the condition are not always plain inputs. Every sub-expression the solver cannot look into
becomes an `atom` with its own variable, and the hint says how each atom was encoded:
  input      a plain name (`q_len`)
  derived    a value computed from inputs (`q.shape[1]`, `len(x)`, `self.layer_id`)
  predicate  a truth value the test has to arrange (`is_flash_attn_2_available()`, `x is None`)
  category   compared with a string or an enum-like constant (`q.dtype == torch.bfloat16`)
  local      a local name tied to its definition by an alias (see below)
No value is guessed: anything the conditions do not mention is left out, and a condition that cannot be
translated gives status `untranslatable` with the text only.

Aliases (witness-v2): a local name assigned exactly once before the check in the same function
(`q_len = q.shape[1]`, `b, n, h, d = q.shape`) is tied to its right-hand side with an equality, so
`q_len` and `q.shape[1]` get the same value and the hint says how to build the name from the inputs.

Call chain (`binder`, codeside/chain_bind.py): when the check sits in a callee, the path prefix holds
conditions of several functions, each in its own names. With a binder, the condition and every prefix
entry are also stated in names of the entry function (`not (d in {16, 32})` becomes
`not (k.shape[3] in {16, 32})`), and names that mean one thing on the whole chain are tied to that term.
The original text stays in the problem, so the hint still gives values for the names the code uses.
If that makes the problem unsolvable, the check cannot be reached through this call chain: `infeasible`.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Optional

import z3

from codeside.scope_check import ScopeChecker, _norm, _num
from schema.models import Condition

FORMAT = "witness-v2"
REAL_SCALE = 1000  # reals are searched on a 1/1000 grid so "as close as possible" has a minimum
TIMEOUT_MS = 5000
ENUM_ROOTS = {"torch", "np", "numpy", "tl", "triton", "jnp", "jax", "dtypes", "DType", "DeviceType", "os"}


class Untranslatable(Exception):
    pass


@dataclass
class _Atom:
    key: str
    kind: str  # input | derived | predicate | category
    sort: str  # int | real | bool | str
    literals: set = field(default_factory=set)  # category: constants it is compared with


def _float_names(trees: list[ast.AST], scope_real: set[str]) -> set[str]:
    """Names that need real values: a real scope, a float constant, or compared/combined with such a name.

    Division alone does not make its operands real (`min_budget / block_size` keeps integer sizes).
    """
    out = set(scope_real)
    groups = []
    for t in trees:
        for n in ast.walk(t):
            if isinstance(n, ast.Compare):
                groups.append([n.left, *n.comparators])
            elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult)):
                groups.append([n.left, n.right])
    changed = True
    while changed:
        changed = False
        for kids in groups:
            texts = {ast.unparse(k) for k in kids if not isinstance(k, ast.Constant)}
            floaty = any(isinstance(k, ast.Constant) and isinstance(k.value, float) for k in kids) or texts & out
            if floaty and not texts <= out:
                out |= texts
                changed = True
    return out


def _enum_like(n: ast.AST) -> bool:
    if not isinstance(n, ast.Attribute):
        return False
    root = n
    while isinstance(root, ast.Attribute):
        root = root.value
    return isinstance(root, ast.Name) and (root.id in ENUM_ROOTS or root.id[:1].isupper() or n.attr.isupper())


class _Encoder:
    """Python condition -> z3 over one copy of the atoms (suffix tells trigger and contrast apart)."""

    def __init__(self, atoms: dict[str, _Atom], reals: set[str], suffix: str):
        self.atoms, self.reals, self.suffix = atoms, reals, suffix
        self.vars: dict[str, Any] = {}

    def var(self, key: str, kind: str, sort: str):
        a = self.atoms.get(key)
        if a is None:
            a = self.atoms[key] = _Atom(key, kind, sort)
        elif a.sort != sort:
            raise Untranslatable(f"`{key}` used both as {a.sort} and {sort}")
        if key not in self.vars:
            name = f"{key}@{self.suffix}"
            if sort == "bool":
                self.vars[key] = z3.Bool(name)
            elif sort == "str":
                self.vars[key] = z3.String(name)
            elif sort == "real":  # a scaled integer: value = k / REAL_SCALE
                self.vars[key] = z3.ToReal(z3.Int(name)) / REAL_SCALE
            else:
                self.vars[key] = z3.Int(name)
        return self.vars[key]

    def num_sort(self, key: str) -> str:
        return "real" if key in self.reals else "int"

    # boolean context --------------------------------------------------------
    def cond(self, n: ast.AST):
        if isinstance(n, ast.Expression):
            return self.cond(n.body)
        if isinstance(n, ast.BoolOp):
            parts = [self.cond(v) for v in n.values]
            return z3.And(*parts) if isinstance(n.op, ast.And) else z3.Or(*parts)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return z3.Not(self.cond(n.operand))
        if isinstance(n, ast.Constant) and isinstance(n.value, bool):
            return z3.BoolVal(n.value)
        if isinstance(n, ast.Compare):
            return self.compare(n)
        if isinstance(n, ast.Name):
            return self.var(n.id, "input", "bool")
        # attribute flags, calls such as is_flash_attn_2_available() or isinstance(...)
        return self.var(ast.unparse(n), "predicate", "bool")

    def compare(self, n: ast.Compare):
        parts, left = [], n.left
        for op, right in zip(n.ops, n.comparators):
            parts.append(self.one_compare(left, op, right))
            left = right
        return parts[0] if len(parts) == 1 else z3.And(*parts)

    def one_compare(self, left: ast.AST, op: ast.cmpop, right: ast.AST):
        text = f"{ast.unparse(left)} {ast.unparse(ast.Compare(left=ast.Name('_'), ops=[op], comparators=[right]))[2:]}"
        if isinstance(op, (ast.Is, ast.IsNot)):
            if isinstance(right, ast.Constant) and isinstance(right.value, bool):
                v = self.cond(left)
                eq = v == z3.BoolVal(right.value)
                return eq if isinstance(op, ast.Is) else z3.Not(eq)
            key = f"{ast.unparse(left)} is {ast.unparse(right)}"
            v = self.var(key, "predicate", "bool")
            return v if isinstance(op, ast.Is) else z3.Not(v)
        if isinstance(op, (ast.In, ast.NotIn)):
            if not isinstance(right, (ast.Set, ast.List, ast.Tuple)):
                v = self.var(f"{ast.unparse(left)} in {ast.unparse(right)}", "predicate", "bool")
                return v if isinstance(op, ast.In) else z3.Not(v)
            tests = [self.eq(left, e) for e in right.elts] or [z3.BoolVal(False)]
            test = z3.Or(*tests)
            return test if isinstance(op, ast.In) else z3.Not(test)
        if isinstance(op, (ast.Eq, ast.NotEq)):
            e = self.eq(left, right)
            return e if isinstance(op, ast.Eq) else z3.Not(e)
        a, b = self.num(left), self.num(right)
        table = {ast.Lt: lambda: a < b, ast.LtE: lambda: a <= b, ast.Gt: lambda: a > b, ast.GtE: lambda: a >= b}
        if type(op) not in table:
            raise Untranslatable(f"comparison {text}")
        return table[type(op)]()

    def eq(self, left: ast.AST, right: ast.AST):
        for a, b in ((left, right), (right, left)):
            if (isinstance(b, ast.Constant) and isinstance(b.value, str)) or _enum_like(b):
                lit = b.value if isinstance(b, ast.Constant) else ast.unparse(b)
                key = ast.unparse(a)
                v = self.var(key, "category", "str")
                self.atoms[key].literals.add(lit)
                return v == z3.StringVal(lit)
            if isinstance(b, ast.Constant) and b.value is None:
                return self.var(f"{ast.unparse(a)} is None", "predicate", "bool")
            if isinstance(b, ast.Constant) and isinstance(b.value, bool):
                return self.cond(a) == z3.BoolVal(b.value)
        return self.num(left) == self.num(right)

    # numeric context --------------------------------------------------------
    def num(self, n: ast.AST):
        if isinstance(n, ast.Constant):
            if _num(n.value):
                return z3.RealVal(Fraction(n.value)) if isinstance(n.value, float) else z3.IntVal(n.value)
            raise Untranslatable(f"constant {n.value!r} in arithmetic")
        if isinstance(n, ast.Name):
            return self.var(n.id, "input", self.num_sort(n.id))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -self.num(n.operand)
        if isinstance(n, ast.BinOp):
            a, b = self.num(n.left), self.num(n.right)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b}
            if type(n.op) in ops:
                return ops[type(n.op)]()
            if isinstance(n.op, ast.Div):
                return z3.ToReal(a) / b if z3.is_int(a) and z3.is_int(b) else a / b
            if isinstance(n.op, (ast.FloorDiv, ast.Mod)) and z3.is_int(a) and z3.is_int(b):
                return a / b if isinstance(n.op, ast.FloorDiv) else a % b  # z3 Int division floors
            raise Untranslatable(f"operator in {ast.unparse(n)}")
        if isinstance(n, ast.Call):
            fname = ast.unparse(n.func)
            if fname in ("max", "min") and len(n.args) >= 2 and not n.keywords:
                args = [self.num(x) for x in n.args]
                out = args[0]
                for x in args[1:]:
                    out = z3.If(out >= x, out, x) if fname == "max" else z3.If(out <= x, out, x)
                return out
            if fname == "abs" and len(n.args) == 1:
                x = self.num(n.args[0])
                return z3.If(x >= 0, x, -x)
            if fname in ("math.ceil", "ceil", "math.floor", "floor") and len(n.args) == 1:
                x = self.num(n.args[0])
                if z3.is_int(x):
                    return x
                f = z3.ToInt(x)  # floor
                return f if "floor" in fname else z3.If(z3.ToReal(f) == x, f, f + 1)
        if isinstance(n, (ast.Attribute, ast.Subscript, ast.Call)):
            key = ast.unparse(n)
            return self.var(key, "derived", self.num_sort(key))
        raise Untranslatable(f"{type(n).__name__} in arithmetic: {ast.unparse(n)}")


@dataclass
class WitnessInputs:
    condition: Optional[Condition]
    effect_type: str
    location: str = ""


def _value(model: z3.ModelRef, v, atom: _Atom):
    r = model.eval(v, model_completion=False)
    if z3.is_true(r):
        return True
    if z3.is_false(r):
        return False
    if z3.is_string_value(r):
        s = r.as_string()
        return s if s in atom.literals else {"not_in": sorted(atom.literals)}
    if z3.is_int_value(r):
        return r.as_long()
    if z3.is_rational_value(r):
        f = Fraction(r.numerator_as_long(), r.denominator_as_long())
        return int(f) if f.denominator == 1 else round(float(f), 6)
    return None  # not constrained by the model


def find_aliases(source: str, line: int) -> dict[str, str]:
    """name -> expression for locals assigned exactly once before `line` in the innermost function around it.

    Parameters and names assigned more than once (in any way: loops, augmented, `with ... as`) are skipped,
    because their value at the check is not the right-hand side.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    fn = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.lineno <= line <= (n.end_lineno or n.lineno):
            if fn is None or n.lineno >= fn.lineno:
                fn = n
    if fn is None:
        return {}
    params = {a.arg for a in [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]}
    params |= {a.arg for a in (fn.args.vararg, fn.args.kwarg) if a}
    stores: dict[str, int] = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            stores[n.id] = stores.get(n.id, 0) + 1
    out: dict[str, str] = {}
    for n in ast.walk(fn):
        if not isinstance(n, ast.Assign) or n.lineno >= line or len(n.targets) != 1:
            continue
        tgt, val = n.targets[0], n.value
        pairs = []
        if isinstance(tgt, ast.Name):
            pairs.append((tgt.id, val))
        elif isinstance(tgt, (ast.Tuple, ast.List)) and all(isinstance(e, ast.Name) for e in tgt.elts):
            if isinstance(val, (ast.Tuple, ast.List)) and len(val.elts) == len(tgt.elts):
                pairs += [(e.id, v) for e, v in zip(tgt.elts, val.elts)]
            elif isinstance(val, (ast.Attribute, ast.Call)) and ast.unparse(val).endswith(("shape", "size()")):
                pairs += [(e.id, ast.Subscript(value=val, slice=ast.Constant(i)))
                          for i, e in enumerate(tgt.elts) if e.id != "_"]
        for name, rhs in pairs:
            if name in params or stores.get(name) != 1 or isinstance(rhs, (ast.Lambda, ast.Constant)):
                continue
            if any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(rhs)):
                continue
            out[name] = ast.unparse(rhs)
    return out


def _tie_aliases(aliases: dict[str, str], atoms: dict, t: "_Encoder", c: "_Encoder") -> tuple[list, list, dict]:
    """Equalities name == rhs for aliases whose name or rhs is already an atom (numeric or bool), to a fixed point."""
    pt, pc, used = [], [], {}
    for _ in range(3):
        added = False
        for name, rhs in aliases.items():
            if name in used or (name not in atoms and rhs not in atoms):
                continue
            sort = (atoms.get(name) or atoms.get(rhs)).sort
            if sort not in ("int", "real", "bool"):
                continue
            snapshot = (dict(atoms), dict(t.vars), dict(c.vars))
            try:
                node = ast.parse(rhs, mode="eval").body
                pair = []
                for enc in (t, c):
                    if sort == "bool":
                        pair.append(enc.var(name, "input", "bool") == enc.cond(node))
                    else:
                        pair.append(enc.var(name, "input", sort) == enc.num(node))
            except (Untranslatable, z3.Z3Exception, SyntaxError, RecursionError):
                for live, old in zip((atoms, t.vars, c.vars), snapshot):
                    live.clear()
                    live.update(old)
                continue
            pt.append(pair[0])
            pc.append(pair[1])
            used[name] = rhs
            if atoms[name].kind == "input":
                atoms[name].kind = "local"
            added = True
        if not added:
            break
    return pt, pc, used


def solve(cond: Optional[Condition], checker: Optional[ScopeChecker], effect_type: str = "",
          aliases: Optional[dict[str, str]] = None, binder=None) -> dict:
    """Return a witness-v2 dict for one condition. Never raises on odd input.

    The path prefix can hold conditions from several frames of the call chain under the same name
    (`q_len` of the caller and of the callee). Aliases come from the innermost frame only, so they may
    tie a name wrongly; if they turn a solvable problem into an infeasible one, they are dropped.

    With `binder` (a ChainBinder for one call chain) the frames are known, so the opposite holds: a problem
    that becomes infeasible with the chain's bindings stays infeasible, provided every call on the chain was
    resolved for certain. Otherwise the bindings are dropped and the hint says so.
    """
    if binder is not None:
        hint = _solve(cond, checker, effect_type, None, binder)
        if hint.get("status") != "infeasible" or not hint.get("entry_terms"):
            return hint
        plain = _solve(cond, checker, effect_type, None)
        if plain.get("status") == "infeasible":
            return plain
        if binder.certain:
            hint["infeasible_because"] = "call_chain"
            hint["note"] = ("unreachable through this call chain: once callee names are stated in the entry "
                            "function's names (entry_terms), path prefix and condition cannot hold together")
            return hint
        plain["entry_terms_dropped"] = hint["entry_terms"]
        plain["note"] = ("call-chain bindings dropped: with them the problem has no solution, but a call on the "
                         "chain was resolved by a guess, so that is no proof")
        return plain
    hint = _solve(cond, checker, effect_type, aliases)
    if aliases and hint.get("status") == "infeasible" and hint.get("aliases"):
        plain = _solve(cond, checker, effect_type, None)
        if plain.get("status") != "infeasible":
            plain["aliases_dropped"] = hint["aliases"]
            plain["note"] = ("aliases dropped: with them the path prefix (which mixes frames of the call chain) "
                             "has no solution")
            return plain
    return hint


def decision(cond: Condition) -> tuple[Condition, dict]:
    """The condition that decides the effect, and what was changed to get it (empty if nothing).

    Two shapes from route B have no contrast point although the check has one:
      * the condition is also the last (innermost) path-prefix entry: it was copied into its own path, so every
        point that reaches it satisfies it. The copy is dropped. Earlier entries with the same text are kept: they
        come from other functions of the call chain (e.g. the entry's own guard);
      * the condition is `True` (an unconditional `raise` inside a branch): the decision is the innermost
        path-prefix entry, so that entry becomes the condition.
    """
    from codeside.dedup import normalise
    prefix = list(cond.path_prefix)
    if prefix and normalise(prefix[-1]) == normalise(cond.expr):
        return cond.model_copy(update={"path_prefix": prefix[:-1]}), {"prefix_dropped": [prefix[-1]],
                "decision_note": "the last path-prefix entry repeated the condition; dropped"}
    if prefix and normalise(cond.expr) == "True":
        return cond.model_copy(update={"expr": prefix[-1], "path_prefix": prefix[:-1]}), {
            "condition_original": cond.expr,
            "decision_note": "unconditional statement inside a branch: the innermost path-prefix entry decides it"}
    return cond, {}


def _solve(cond: Optional[Condition], checker: Optional[ScopeChecker], effect_type: str,
           aliases: Optional[dict[str, str]], binder=None) -> dict:
    changed: dict = {}
    if cond is not None:
        cond, changed = decision(cond)
    hint = _solve_one(cond, checker, effect_type, aliases, binder)
    if changed:
        hint.update(changed)
    return hint


def _solve_one(cond: Optional[Condition], checker: Optional[ScopeChecker], effect_type: str,
               aliases: Optional[dict[str, str]], binder=None) -> dict:
    kind = "event_sequence" if effect_type == "state" else "input_value"
    hint: dict[str, Any] = {"format": FORMAT, "kind": kind, "status": "untranslatable",
                            "condition": cond.expr if cond else None,
                            "path_prefix": list(cond.path_prefix) if cond else []}
    if kind == "event_sequence":
        hint["sequence_note"] = ("state-dependent: earlier calls must leave the program in the trigger state; "
                                 "the values below describe that state at the checked call")
    if cond is None:
        hint["note"] = "no machine-readable condition; use the limitation text"
        return hint
    try:
        main = ast.parse(cond.expr.strip(), mode="eval")
    except SyntaxError:
        hint["note"] = "condition is not a Python expression"
        return hint
    prefix, dropped = [], []
    for p in cond.path_prefix:
        try:
            prefix.append(ast.parse(p.strip(), mode="eval"))
        except SyntaxError:
            dropped.append(p)

    by_symbol = checker.by_symbol if checker else {}
    scope_real = {s for s, it in by_symbol.items() if it.kind == "interval" and any(
        isinstance(x, float) for x in (it.lower, it.upper) if x is not None)}
    reals = _float_names([main, *prefix], scope_real)
    atoms: dict[str, _Atom] = {}
    t, c = _Encoder(atoms, reals, "t"), _Encoder(atoms, reals, "c")
    try:
        ct, cc = t.cond(main), c.cond(main)
    except (Untranslatable, z3.Z3Exception, RecursionError) as exc:
        hint["note"] = f"cannot translate condition: {exc}"
        return hint
    pt, pc = [], []
    for p in prefix:
        snapshot = (dict(atoms), dict(t.vars), dict(c.vars))
        try:
            a, b = t.cond(p), c.cond(p)
            pt.append(a)
            pc.append(b)
        except (Untranslatable, z3.Z3Exception, RecursionError):
            for live, old in zip((atoms, t.vars, c.vars), snapshot):
                live.clear()
                live.update(old)
            dropped.append(ast.unparse(p))
    hint["dropped_prefix"] = dropped
    extra_t, extra_c = [], []  # the condition again, in the entry function's names: trigger holds it, contrast does not
    if binder is not None:
        terms: dict[str, Any] = {}
        todo = [("condition", cond.expr.strip(), binder.last)]
        todo += [("path_prefix", ast.unparse(p), binder.frame_of(ast.unparse(p))) for p in prefix
                 if ast.unparse(p) not in dropped]
        for kind, text, frame in todo:
            new = binder.rewrite(text, frame)
            if new is None:
                continue
            snapshot = (dict(atoms), dict(t.vars), dict(c.vars))
            try:
                node = ast.parse(new, mode="eval")
                a, b = t.cond(node), c.cond(node)
            except (Untranslatable, z3.Z3Exception, SyntaxError, RecursionError):
                for live, old in zip((atoms, t.vars, c.vars), snapshot):
                    live.clear()
                    live.update(old)
                continue
            if kind == "condition":
                extra_t.append(a)
                extra_c.append(z3.Not(b))
                terms["condition"] = new
            else:
                pt.append(a)
                pc.append(b)
                terms.setdefault("path_prefix", {})[text] = new
        names = {k: binder.term(k) for k in list(atoms)}
        at, ac, used = _tie_aliases({k: v for k, v in names.items() if v}, atoms, t, c)
        pt += at
        pc += ac
        if used:
            terms["names"] = used
            hint["aliases"] = dict(used)  # same reading as before: how to build a name; here in entry names
        if terms:
            hint["entry_terms"] = terms
        if binder.ambiguous:
            hint["ambiguous_names"] = dict(binder.ambiguous)
    if aliases:
        at, ac, used = _tie_aliases(aliases, atoms, t, c)
        pt += at
        pc += ac
        if used:
            hint["aliases"] = used

    scope_t, scope_c, from_paper = [], [], {}
    for key, a in atoms.items():
        item = by_symbol.get(key)
        if item is None or a.sort not in ("int", "real"):
            continue
        for enc, out in ((t, scope_t), (c, scope_c)):
            v = enc.vars.get(key)
            if v is None:
                continue
            if item.kind == "interval":
                if item.lower is not None:
                    out.append(v >= item.lower)
                if item.upper is not None:
                    out.append(v <= item.upper)
                from_paper[key] = f"scope {item.param}: [{item.lower}, {item.upper}]"
            elif item.kind == "set" and item.values and all(_num(x) for x in item.values):
                out.append(z3.Or(*[v == x for x in item.values]))
                from_paper[key] = f"scope {item.param}: one of {item.values}"
    prefs = _eval_preferences(atoms, by_symbol, checker)

    def constraints(with_contrast: bool, contrast_scope: bool) -> list:
        out = [ct, *extra_t, *pt, *scope_t]
        if with_contrast:
            out += [z3.Not(cc), *extra_c, *pc, *(scope_c if contrast_scope else [])]
        return out

    def optimise(with_contrast: bool, contrast_scope: bool):
        opt = z3.Optimize()
        opt.set("timeout", TIMEOUT_MS)
        opt.add(*constraints(with_contrast, contrast_scope))
        # objectives are lexicographic in the order added
        # 1) sizes and counts are rarely negative: prefer trigger values >= 1 (soft, so `x < 0` still solves)
        for key, v in t.vars.items():
            if atoms[key].sort in ("int", "real"):
                opt.add_soft(v >= (1 if atoms[key].sort == "int" else 0), weight=1, id="positive")
        # 2) both points as close as possible: the two sides of the boundary
        if with_contrast:
            dist = []
            for key, a in atoms.items():
                if key not in t.vars or key not in c.vars:
                    continue
                x, y = t.vars[key], c.vars[key]
                if a.sort in ("int", "real"):
                    d = x - y
                    d = z3.If(d >= 0, d, -d)
                    dist.append(z3.ToInt(d * REAL_SCALE) if a.sort == "real" else d)
                else:
                    dist.append(z3.If(x == y, 0, 1))
            if dist:
                opt.minimize(z3.Sum(*dist))
            for key, v in c.vars.items():
                if atoms[key].sort in ("int", "real"):
                    opt.add_soft(v >= (1 if atoms[key].sort == "int" else 0), weight=1, id="positive_contrast")
        # 3) paper evaluation values where the scope leaves a name free
        for key, val in prefs.items():
            for enc in (t, c) if with_contrast else (t,):
                if key in enc.vars:
                    opt.add_soft(enc.vars[key] == val, weight=1, id="eval")
        res = opt.check()
        if res == z3.sat:
            return res, opt.model(), True
        if res == z3.unknown:  # e.g. non-linear integer terms: settle for any point, not the closest
            plain = z3.Solver()
            plain.set("timeout", TIMEOUT_MS)
            plain.add(*constraints(with_contrast, contrast_scope))
            r = plain.check()
            return r, (plain.model() if r == z3.sat else None), False
        return res, None, True

    try:
        minimal = True
        res, model, minimal = optimise(True, True)
        status = "solved"
        if res == z3.unsat:
            res, model, minimal = optimise(True, False)
            status = "solved_contrast_outside_scope"
        if res == z3.unsat:
            res, model, minimal = optimise(False, False)
            status = "trigger_only"
    except z3.Z3Exception as exc:
        hint["note"] = f"solver error: {exc}"
        return hint
    if res == z3.unknown:
        hint.update(status="unknown", note="solver gave up (timeout or non-linear terms)")
        return hint
    if res != z3.sat:
        hint.update(status="infeasible", note="no values satisfy path prefix, condition and scope together")
        return hint
    if not minimal:
        hint["closest"] = False  # points are valid but not guaranteed to be the nearest pair

    def point(enc: _Encoder) -> dict:
        out = {}
        for key, v in enc.vars.items():
            val = _value(model, v, atoms[key])
            if val is not None:
                out[key] = val
        return out

    hint["status"] = status
    hint["trigger"] = point(t)
    if status != "trigger_only":
        hint["contrast"] = point(c)
    else:
        hint["note"] = "the condition holds on every point that reaches it; no contrast point exists"
    hint["atoms"] = {k: {"kind": a.kind, "sort": a.sort} for k, a in sorted(atoms.items())}
    if from_paper:
        hint["from_paper"] = from_paper
    if prefs:
        hint["eval_preference"] = prefs
    return hint


def _eval_preferences(atoms: dict[str, _Atom], by_symbol: dict, checker: Optional[ScopeChecker]) -> dict:
    """Numeric names -> a value from the paper's EvalPoints (a soft preference, never a constraint).

    A name bound to a scope item looks up that item's param or the code name; an unbound plain input
    looks up its own name (e.g. `block_size` in an EvalPoint config). The first EvalPoint that sets it wins.
    """
    out = {}
    if not checker:
        return out
    for key, a in atoms.items():
        if a.sort not in ("int", "real"):
            continue
        item = by_symbol.get(key)
        if item is None and a.kind != "input":
            continue
        names = [_norm(key)] + ([_norm(item.param)] if item is not None else [])
        for ep in checker.eval_points:
            config = {_norm(k): v for k, v in ep.config.items()}
            v = next((config[n] for n in names if _num(config.get(n))), None)
            if v is not None:
                out[key] = round(v * REAL_SCALE) / REAL_SCALE if a.sort == "real" else int(v)
                break
    return out
