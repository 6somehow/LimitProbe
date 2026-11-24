"""Static call graph of a repo: the chain of calls from an entry point to a target function, with the
argument names at every call (docs/09_step4_findings.md, "call chain").

The test side needs two things step 4 did not hand over (checklimits/REQUESTS_TO_STEP4.md, requests 1 and 2):

  call chain   [entry, ..., function that holds the target], every step a real call site;
  arguments    at each call, which expression of the caller each parameter of the callee receives
               (`triton_bnhd_pool(k, block_size)`: x <- k, kernel_size <- block_size).

Everything here is `ast` only. A call is resolved in this order, and the way it was resolved is recorded:

  direct        `f(...)`: a nested function, a function of the same file, an imported function,
                `Class(...)` (its `__init__`), `Class.method(...)`
  self          `self.m(...)`, `cls.m(...)`, `super().m(...)`: the class or a base class in the repo
  import        `module.f(...)` where `module` is an imported module of the repo
                `obj.m(...)` where `obj` was built by `obj = Class(...)` in the same function, or
                `self.attr.m(...)` where the class sets `self.attr = Class(...)` in one place
  override      `self.m(...)` in a base class: also the `m` of every subclass in the repo that overrides
                it (which one runs depends on the object: uncertain)
  unique_name   `obj.m(...)`: the only function or method called `m` in the repo (a guess: uncertain)
  reference     a nested function that its parent hands out without calling it (returns it, installs it
                as a method, passes it as a callback). The parent does not call it; whoever receives it
                does. Uncertain, and it has no argument mapping.

What is not resolved: calls through objects whose type is unknown and whose method name is not unique
(`layer(x)`, `self.attn.forward(x)` with several `forward`), decorators, getattr, dynamic dispatch.
A target that no chain reaches gets status `not_found`; nothing is guessed.
"""

from __future__ import annotations

import ast
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SKIP_DIRS = {".git", "test", "tests", "__pycache__", "docs", "build", "dist", ".venv", "venv", "node_modules"}
UNCERTAIN = ("unique_name", "reference", "override")
MODULE = "<module>"
_FUNC = (ast.FunctionDef, ast.AsyncFunctionDef)


@dataclass
class Func:
    id: str  # "file::qual"
    file: str
    qual: str
    node: ast.AST
    cls: Optional[str] = None  # enclosing class (qualified inside the file), also for functions nested in a method
    parent: Optional[str] = None  # id of the enclosing function

    @property
    def is_method(self) -> bool:
        return self.cls is not None and self.qual == f"{self.cls}.{self.node.name}"

    def params(self) -> list[str]:
        a = self.node.args
        return [x.arg for x in [*a.posonlyargs, *a.args]]

    def all_params(self) -> set[str]:
        a = self.node.args
        return {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs]} | {x.arg for x in (a.vararg, a.kwarg) if x}


@dataclass
class CallSite:
    caller: str
    callee: str
    line: int
    resolved_by: str
    args: dict[str, str] = field(default_factory=dict)  # callee parameter -> expression in the caller
    star: bool = False  # the call uses *args / **kwargs: the mapping is incomplete

    @property
    def certain(self) -> bool:
        return self.resolved_by not in UNCERTAIN

    def to_json(self) -> dict:
        d = {"caller": self.caller, "callee": self.callee, "line": self.line, "resolved_by": self.resolved_by,
             "args": self.args}
        if self.star:
            d["star_args"] = True
        return d


def _dotted(node: ast.AST) -> Optional[str]:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        return ".".join([node.id, *reversed(parts)])
    return None


def _own_nodes(fn: ast.AST):
    """Nodes of a function body without the bodies of nested functions and classes."""
    stack = list(getattr(fn, "body", []))
    while stack:
        n = stack.pop()
        yield n
        if isinstance(n, (*_FUNC, ast.ClassDef)):
            continue
        stack.extend(ast.iter_child_nodes(n))


class RepoCallGraph:
    def __init__(self, repo: Path, package_roots: tuple[str, ...] = (".",)):
        self.repo = Path(repo)
        self.roots = tuple(package_roots) or (".",)
        self.funcs: dict[str, Func] = {}
        self.classes: dict[str, dict[str, list[str]]] = {}  # file -> class qual -> base names
        self.trees: dict[str, ast.Module] = {}
        self.imports: dict[str, dict[str, tuple]] = {}  # file -> local name -> ("sym", file, name) | ("mod", file)
        self.external: dict[str, set[str]] = {}  # file -> names imported from outside the repo
        self.by_name: dict[str, list[str]] = {}
        self._edges: dict[str, list[CallSite]] = {}
        self._types: dict[str, dict[str, tuple[str, str]]] = {}
        self._attr_types: dict[tuple[str, str], dict[str, tuple[str, str]]] = {}
        self._subclasses: Optional[dict[tuple[str, str], list[tuple[str, str]]]] = None
        for path in sorted(self.repo.rglob("*.py")):
            rel = path.relative_to(self.repo)
            if SKIP_DIRS & set(rel.parts[:-1]):
                continue
            try:
                with warnings.catch_warnings():  # invalid escape sequences in the analysed repo are not our problem
                    warnings.simplefilter("ignore")
                    tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, ValueError):
                continue
            self.trees[str(rel)] = tree
            self.classes[str(rel)] = {}
            self._index(str(rel), tree.body, "", None, None)
        for rel, tree in self.trees.items():
            self._index_imports(rel, tree)
        for f in self.funcs.values():
            self.by_name.setdefault(f.qual.split(".")[-1], []).append(f.id)

    # ------------------------------------------------------------------ index
    def _index(self, rel: str, body: list, prefix: str, cls: Optional[str], parent: Optional[str]) -> None:
        for n in body:
            if isinstance(n, _FUNC):
                fid = f"{rel}::{prefix}{n.name}"
                self.funcs.setdefault(fid, Func(fid, rel, prefix + n.name, n, cls, parent))
                self._index(rel, n.body, f"{prefix}{n.name}.", cls, fid)
            elif isinstance(n, ast.ClassDef):
                qual = prefix + n.name
                self.classes[rel][qual] = [b for b in (_dotted(x) for x in n.bases) if b]
                self._index(rel, n.body, qual + ".", qual, parent)
            else:  # defs under `if`, `try`, `with` at any level
                for part in ("body", "orelse", "finalbody"):
                    self._index(rel, getattr(n, part, None) or [], prefix, cls, parent)
                for h in getattr(n, "handlers", []):
                    self._index(rel, h.body, prefix, cls, parent)

    def _module_file(self, dotted: str, base: Optional[Path] = None) -> Optional[str]:
        parts = dotted.split(".") if dotted else []
        cands = [base.joinpath(*parts)] if base is not None else [Path(r).joinpath(*parts) for r in self.roots]
        for c in cands:
            for f in (c.with_suffix(".py"), c / "__init__.py"):
                key = str(Path(*f.parts)) if f.parts else ""
                if key in self.trees:
                    return key
        if base is None and parts:  # no package root given: a unique file whose path ends with the module path
            tails = ("/".join(parts) + ".py", "/".join(parts) + "/__init__.py")
            hits = [f for f in self.trees if any(f == t or f.endswith("/" + t) for t in tails)]
            if len(hits) == 1:
                return hits[0]
        return None

    def _index_imports(self, rel: str, tree: ast.Module) -> None:
        out: dict[str, tuple] = {}
        ext: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    f = self._module_file(a.name)
                    if f and a.asname:
                        out[a.asname] = ("mod", f)
                    elif not f:
                        ext.add(a.asname or a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                base = None
                if node.level:
                    base = Path(rel).parent
                    for _ in range(node.level - 1):
                        base = base.parent
                src = self._module_file(node.module or "", base)
                for a in node.names:
                    local = a.asname or a.name
                    sub = self._module_file(".".join(x for x in (node.module, a.name) if x), base)
                    if src and (f"{src}::{a.name}" in self.funcs or a.name in self.classes.get(src, {})):
                        out[local] = ("sym", src, a.name)
                    elif sub:
                        out[local] = ("mod", sub)
                    elif src:
                        out[local] = ("sym", src, a.name)  # maybe re-exported by an __init__: followed on lookup
                    else:
                        ext.add(local)
        self.imports[rel] = out
        self.external[rel] = ext

    def func_at(self, file: str, line: int) -> Optional[Func]:
        """The innermost function that holds `line`."""
        best = None
        for f in self.funcs.values():
            if f.file == file and f.node.lineno <= line <= (f.node.end_lineno or f.node.lineno):
                if best is None or f.node.lineno >= best.node.lineno:
                    best = f
        return best

    # ------------------------------------------------------------------ resolution
    def _symbol(self, file: str, name: str, depth: int = 0) -> Optional[tuple[str, str]]:
        """(kind, id): a function, or a class (kind 'class', id 'file::Class'), named `name` as seen from `file`."""
        if f"{file}::{name}" in self.funcs:
            return "func", f"{file}::{name}"
        if name in self.classes.get(file, {}):
            return "class", f"{file}::{name}"
        imp = self.imports.get(file, {}).get(name)
        if imp and imp[0] == "sym" and depth < 3 and (imp[1], imp[2]) != (file, name):
            return self._symbol(imp[1], imp[2], depth + 1)
        return None

    def _method(self, file: str, cls: str, name: str, depth: int = 0) -> Optional[str]:
        fid = f"{file}::{cls}.{name}"
        if fid in self.funcs:
            return fid
        if depth >= 4:
            return None
        for base in self.classes.get(file, {}).get(cls, []):
            sym = self._symbol(file, base.split(".")[-1])
            if sym and sym[0] == "class":
                bfile, bcls = sym[1].split("::")
                hit = self._method(bfile, bcls, name, depth + 1)
                if hit:
                    return hit
        return None

    def _ctor_class(self, file: str, value: ast.AST) -> Optional[tuple[str, str]]:
        """(file, class) if `value` is `Class(...)` for a class of the repo."""
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            sym = self._symbol(file, value.func.id)
            if sym and sym[0] == "class":
                return tuple(sym[1].split("::"))
        return None

    def _local_types(self, fn: Func) -> dict[str, tuple[str, str]]:
        """Local name -> class, for names assigned exactly once in the function, from `Class(...)`."""
        if fn.id not in self._types:
            stores: dict[str, int] = {}
            typed: dict[str, tuple[str, str]] = {}
            for n in _own_nodes(fn.node):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    stores[n.id] = stores.get(n.id, 0) + 1
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                    c = self._ctor_class(fn.file, n.value)
                    if c:
                        typed[n.targets[0].id] = c
            self._types[fn.id] = {k: v for k, v in typed.items() if stores.get(k) == 1}
        return self._types[fn.id]

    def _self_attr_types(self, file: str, cls: str) -> dict[str, tuple[str, str]]:
        """Attribute -> class, for `self.attr = Class(...)` set in exactly one place of the class."""
        key = (file, cls)
        if key not in self._attr_types:
            count: dict[str, int] = {}
            typed: dict[str, tuple[str, str]] = {}
            for f in self.funcs.values():
                if f.file != file or f.cls != cls:
                    continue
                for n in _own_nodes(f.node):
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(
                        n, (ast.AugAssign, ast.AnnAssign)) else []
                    for t in targets:
                        if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                            count[t.attr] = count.get(t.attr, 0) + 1
                            c = self._ctor_class(file, n.value) if isinstance(n, ast.Assign) else None
                            if c:
                                typed[t.attr] = c
            self._attr_types[key] = {k: v for k, v in typed.items() if count.get(k) == 1}
        return self._attr_types[key]

    def overrides(self, fid: str) -> list[str]:
        """Methods of subclasses (in the repo) that override the method `fid`."""
        fn = self.funcs[fid]
        if not fn.is_method:
            return []
        if self._subclasses is None:
            self._subclasses = {}
            for file, classes in self.classes.items():
                for cls, bases in classes.items():
                    for b in bases:
                        sym = self._symbol(file, b.split(".")[-1])
                        if sym and sym[0] == "class":
                            self._subclasses.setdefault(tuple(sym[1].split("::")), []).append((file, cls))
        out, todo, seen = [], [(fn.file, fn.cls)], set()
        while todo:
            for sub in self._subclasses.get(todo.pop(), []):
                if sub in seen:
                    continue
                seen.add(sub)
                todo.append(sub)
                sid = f"{sub[0]}::{sub[1]}.{fn.node.name}"
                if sid in self.funcs:
                    out.append(sid)
        return out

    def _resolve(self, fn: Func, call: ast.Call) -> Optional[tuple[str, str, bool]]:
        """(callee id, resolved_by, implicit first argument) or None."""
        f = call.func
        if isinstance(f, ast.Name):
            scope: Optional[Func] = fn
            while scope is not None:  # nested functions of this function and of the functions around it
                fid = f"{scope.file}::{scope.qual}.{f.id}"
                if fid in self.funcs:
                    return fid, "direct", False
                scope = self.funcs.get(scope.parent) if scope.parent else None
            sym = self._symbol(fn.file, f.id)
            if sym and sym[0] == "func":
                return sym[1], "direct", False
            if sym and sym[0] == "class":
                cfile, cname = sym[1].split("::")
                init = self._method(cfile, cname, "__init__")
                return (init, "direct", True) if init else None
            return None
        if not isinstance(f, ast.Attribute):
            return None
        name, value = f.attr, f.value
        is_super = isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "super"
        if fn.cls and (is_super or (isinstance(value, ast.Name) and value.id in ("self", "cls"))):
            if is_super:
                hit = next((h for b in self.classes[fn.file].get(fn.cls, []) for s in [self._symbol(fn.file, b.split(".")[-1])]
                            if s and s[0] == "class" for h in [self._method(*s[1].split("::"), name)] if h), None)
            else:
                hit = self._method(fn.file, fn.cls, name)
            if hit:
                return hit, "self", True
        dotted = _dotted(value)
        typed = None
        if isinstance(value, ast.Name):
            typed = self._local_types(fn).get(value.id)
        elif dotted and fn.cls and dotted.count(".") == 1 and dotted.startswith("self."):
            typed = self._self_attr_types(fn.file, fn.cls).get(dotted[5:])
        if typed:
            hit = self._method(*typed, name)
            if hit:
                return hit, "direct", True
        if dotted:
            imp = self.imports.get(fn.file, {}).get(dotted)
            mod = imp[1] if imp and imp[0] == "mod" else self._module_file(dotted) if "." in dotted else None
            if mod and f"{mod}::{name}" in self.funcs:
                return f"{mod}::{name}", "import", False
            sym = self._symbol(fn.file, dotted) if "." not in dotted else None
            if sym and sym[0] == "class":
                hit = self._method(*sym[1].split("::"), name)
                if hit:
                    return hit, "direct", self._is_bound(hit)
            if dotted.split(".")[0] in self.external.get(fn.file, ()):
                return None  # torch.x(...), np.y(...)
        if name.startswith("__"):
            return None
        cands = self.by_name.get(name, [])
        if len(cands) == 1 and cands[0] != fn.id:
            return cands[0], "unique_name", self.funcs[cands[0]].is_method
        return None

    def _is_bound(self, fid: str) -> bool:
        """`Class.m(...)` passes no instance, unless m is a classmethod."""
        decos = {_dotted(d) for d in self.funcs[fid].node.decorator_list}
        return "classmethod" in decos

    def _args(self, callee: Func, call: ast.Call, implicit_first: bool) -> tuple[dict[str, str], bool]:
        params = callee.params()
        decos = {_dotted(d) for d in callee.node.decorator_list}
        if implicit_first and params and "staticmethod" not in decos:
            params = params[1:]
        out, star = {}, False
        for i, a in enumerate(call.args):
            if isinstance(a, ast.Starred):
                star = True
                break
            if i < len(params):
                out[params[i]] = ast.unparse(a)
        known = callee.all_params()
        for kw in call.keywords:
            if kw.arg is None:
                star = True
            elif kw.arg in known:
                out[kw.arg] = ast.unparse(kw.value)
        return out, star

    def calls_from(self, fid: str) -> list[CallSite]:
        if fid in self._edges:
            return self._edges[fid]
        fn = self.funcs[fid]
        out: list[CallSite] = []
        called: set[int] = set()
        nodes = list(_own_nodes(fn.node))
        for n in nodes:
            if not isinstance(n, ast.Call):
                continue
            called.add(id(n.func))
            res = self._resolve(fn, n)
            if res is None or res[0] == fid:
                continue
            callee, how, implicit = res
            args, star = self._args(self.funcs[callee], n, implicit)
            out.append(CallSite(fid, callee, n.lineno, how, args, star))
            if how == "self":  # the object may be a subclass that overrides the method
                for sub in self.overrides(callee):
                    if sub != fid:
                        a2, s2 = self._args(self.funcs[sub], n, implicit)
                        out.append(CallSite(fid, sub, n.lineno, "override", a2, s2))
        # nested functions the parent hands out without calling them
        nested = {f.node.name: f.id for f in self.funcs.values() if f.parent == fid}
        seen = {c.callee for c in out}
        for n in nodes:
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in nested and id(n) not in called:
                if nested[n.id] not in seen:
                    seen.add(nested[n.id])
                    out.append(CallSite(fid, nested[n.id], n.lineno, "reference"))
        out.sort(key=lambda c: c.line)
        self._edges[fid] = out
        return out

    # ------------------------------------------------------------------ chains
    def chains(self, entry: str, target: str, max_depth: int = 8, max_chains: int = 6) -> list[list[CallSite]]:
        """Call chains from `entry` to `target`, certain and short ones first. [] if none; [[]] if entry is target."""
        if entry not in self.funcs or target not in self.funcs:
            return []
        if entry == target:
            return [[]]
        # functions that can reach the target (search backwards once, so the forward search does not wander)
        reach, frontier = {target}, [target]
        callers: dict[str, set[str]] = {}
        todo, seen = [entry], {entry}
        while todo:
            f = todo.pop()
            for c in self.calls_from(f):
                callers.setdefault(c.callee, set()).add(f)
                if c.callee not in seen:
                    seen.add(c.callee)
                    todo.append(c.callee)
        while frontier:
            f = frontier.pop()
            for c in callers.get(f, ()):
                if c not in reach:
                    reach.add(c)
                    frontier.append(c)
        if entry not in reach:
            return []
        found: list[list[CallSite]] = []

        def walk(f: str, path: list[CallSite], on_path: set[str]) -> None:
            if len(found) >= max_chains * 4 or len(path) >= max_depth:
                return
            for c in self.calls_from(f):
                if c.callee not in reach or c.callee in on_path:
                    continue
                if c.callee == target:
                    found.append(path + [c])
                else:
                    walk(c.callee, path + [c], on_path | {c.callee})

        walk(entry, [], {entry})
        found.sort(key=lambda p: (sum(not c.certain for c in p), len(p), [c.line for c in p]))
        return found[:max_chains]


def chain_names(entry: str, chain: list[CallSite]) -> list[str]:
    return [entry, *[c.callee for c in chain]]


def locate(graph: RepoCallGraph, entry_points: list[str], file: str, line: int) -> dict:
    """Call-chain record for the statement at file:line.

    status  resolved        a chain of call sites from an entry point reaches the function of the target
            entry_is_target the target is in an entry point itself
            module_level    the target is module-level code: it runs when the module is imported
            not_found       no chain from any entry point (see the module docstring for what is not resolved)
    The entry point in the same file as the target is tried first (the test side picks its entry the same way).
    """
    fn = graph.func_at(file, line)
    if fn is None:
        if file in graph.trees:
            return {"status": "module_level", "call_chain": [f"{file}::{MODULE}"], "call_sites": [], "chains": [],
                    "note": "module-level statement: it runs at import, no call chain"}
        return {"status": "not_found", "note": f"{file} is not a Python file of the repo"}
    entries = sorted(dict.fromkeys(entry_points), key=lambda e: e.partition("::")[0] != file)
    missing = [e for e in entries if e not in graph.funcs]
    best: Optional[tuple[str, list[list[CallSite]]]] = None
    for e in entries:
        chains = graph.chains(e, fn.id)
        if chains and (best is None or (not all(c.certain for c in best[1][0]) and all(c.certain for c in chains[0]))):
            best = (e, chains)
            if all(c.certain for c in chains[0]):
                break
    if best is None:
        out = {"status": "not_found", "function": fn.id,
               "note": "no static call chain from an entry point to this function (dynamic dispatch, a callback, "
                       "or it is not on the entry's path)"}
        above = [e for e in entries if e in graph.funcs and graph.chains(fn.id, e, max_chains=1)]
        if above:  # e.g. a framework integration that calls the mechanism: the function is itself an entry
            out["calls_entry"] = above
            out["note"] = ("this function calls the entry point, it is not called by it: it is a caller-side "
                           "integration and has to be driven directly")
        if missing:
            out["entry_points_not_in_repo"] = missing
        return out
    entry, chains = best
    first = chains[0]
    out = {"status": "entry_is_target" if not first else "resolved", "function": fn.id,
           "call_chain": chain_names(entry, first), "call_sites": [c.to_json() for c in first],
           "chains": chains, "entry": entry}
    if len(chains) > 1:
        out["other_chains"] = [chain_names(entry, c) for c in chains[1:]]
    if any(not c.certain for c in first):
        out["uncertain_steps"] = [f"{c.caller} -> {c.callee} ({c.resolved_by})" for c in first if not c.certain]
    return out
