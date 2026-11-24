"""Step 2 v0: deterministic region-table extraction with Python `ast`.

Starting from one entry function, walk statements in order while keeping the
enclosing branch conditions (the path prefix), follow calls into functions of
the same repo, and emit a Region for each of these signals:

  assert / raise                      -> reject
  early return that calls a baseline  -> fallback        (hint list, e.g. flash_attn)
  `global X` + `if X is None:`        -> state_dependent
  branch on version / availability    -> env_dependent   (the non-default branch)
  `mask = <compare with a parameter>` -> mechanism_variant (per-element tensor branch)
  arithmetic with a literal equal to a
  parameter's default (e.g. `// 128`) -> suspicious
  end of the entry function           -> mechanism       (the default path)

Known v0 gaps (see docs/05_dataset.md, extractor gaps):
  * no path-feasibility pruning: callees are analysed on every branch, so
    infeasible branches (e.g. a decode kernel under a prefill prefix) add noise;
  * callee conditions are not rewritten into the caller's names;
  * only same-file calls and simple `from x import f` inside the repo are resolved;
  * no LLM step yet for dynamic dispatch (config strings -> functions).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from schema.models import CodeLocation, Condition, Region

DEFAULT_FALLBACK_HINTS = ("flash_attn", "dense", "full_attention", "naive", "fallback", "sdpa",
                          "scaled_dot_product_attention", "torch_attention")
ENV_PATTERN = re.compile(
    r"__version__|is_available|is_\w+_available|get_device_name|gpu_name|GPU_NAME|platform|"
    r"importlib|find_spec", re.IGNORECASE)


@dataclass
class ExtractConfig:
    repo: Path
    entry: str  # "relative/path.py::function"
    artifact_id: str
    max_depth: int = 3
    fallback_hints: tuple[str, ...] = DEFAULT_FALLBACK_HINTS
    descend_into_fallbacks: bool = False
    package_roots: tuple[str, ...] = (".",)  # dirs that absolute imports are resolved against


@dataclass
class _Frame:
    file: str  # repo-relative
    func: ast.FunctionDef
    chain: list[str]
    prefix: list[str]
    depth: int
    tracked: set[str] = field(default_factory=set)
    params: set[str] = field(default_factory=set)
    globals_: set[str] = field(default_factory=set)
    qual: str = ""  # "func", "Class.method" or "outer.inner"
    cls: Optional[str] = None  # enclosing class, for resolving self.method()

    @property
    def name(self) -> str:
        return self.qual or self.func.name


class RegionExtractor:
    def __init__(self, cfg: ExtractConfig):
        self.cfg = cfg
        self.repo = Path(cfg.repo)
        self._trees: dict[str, ast.Module] = {}
        self._funcs: dict[str, dict[str, ast.FunctionDef]] = {}
        self._imports: dict[str, dict[str, str]] = {}
        self.regions: list[Region] = []
        self._seen: set[tuple[str, int, str]] = set()
        self._seen_expr: set[tuple[str, str, str, str]] = set()
        self._visiting: set[tuple[str, str]] = set()
        self._entry_defaults: dict[object, str] = {}

    # ------------------------------------------------------------------ files
    def _load(self, rel: str) -> Optional[ast.Module]:
        if rel in self._trees:
            return self._trees[rel]
        path = self.repo / rel
        if not path.is_file():
            return None
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self._trees[rel] = tree
        self._funcs[rel] = self._index_functions(tree)
        self._imports[rel] = self._index_imports(rel, tree)
        return tree

    @staticmethod
    def _index_functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
        """Top-level functions, `Class.method`, and one level of nested `outer.inner`."""
        out: dict[str, ast.FunctionDef] = {}
        for n in tree.body:
            if isinstance(n, ast.FunctionDef):
                out[n.name] = n
                for inner in n.body:
                    if isinstance(inner, ast.FunctionDef):
                        out[f"{n.name}.{inner.name}"] = inner
            elif isinstance(n, ast.ClassDef):
                for m in n.body:
                    if isinstance(m, ast.FunctionDef):
                        out[f"{n.name}.{m.name}"] = m
        return out

    def _index_imports(self, rel: str, tree: ast.Module) -> dict[str, str]:
        """name -> repo-relative file that defines it (simple `from x import f` only)."""
        out: dict[str, str] = {}
        pkg_dir = Path(rel).parent
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None and node.level == 0:
                continue
            base = pkg_dir
            for _ in range(max(node.level - 1, 0)):
                base = base.parent
            mod_parts = (node.module or "").split(".") if node.module else []
            candidates = []
            if node.level > 0:
                candidates.append(base.joinpath(*mod_parts))
            else:
                candidates += [Path(root).joinpath(*mod_parts) for root in self.cfg.package_roots]
            for cand in candidates:
                for f in (cand.with_suffix(".py"), cand / "__init__.py"):
                    if (self.repo / f).is_file():
                        for alias in node.names:
                            out[alias.asname or alias.name] = str(f)
                        break
        return out

    def _resolve(self, rel: str, name: str, cls: Optional[str] = None
                 ) -> Optional[tuple[str, ast.FunctionDef]]:
        self._load(rel)
        if cls and f"{cls}.{name}" in self._funcs.get(rel, {}):
            return rel, self._funcs[rel][f"{cls}.{name}"]
        if name in self._funcs.get(rel, {}):
            return rel, self._funcs[rel][name]
        target = self._imports.get(rel, {}).get(name)
        if target and self._load(target) is not None and name in self._funcs.get(target, {}):
            return target, self._funcs[target][name]
        return None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _names(node: ast.AST) -> set[str]:
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    @staticmethod
    def _src(node: ast.AST) -> str:
        return ast.unparse(node)

    @staticmethod
    def _call_names(nodes: Iterable[ast.AST]) -> list[str]:
        out = []
        for root in nodes:
            for n in ast.walk(root):
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Name):
                        out.append(f.id)
                    elif isinstance(f, ast.Attribute):
                        out.append(f.attr)
        return out

    def _is_fallback(self, names: Iterable[str]) -> bool:
        return any(h in n.lower() for n in names for h in self.cfg.fallback_hints)

    def _emit(self, fr: _Frame, node: ast.AST, expr: str, outcome: str, detail: str,
              prefix: list[str], notes: Optional[str] = None, line: Optional[int] = None) -> None:
        line = line or node.lineno
        key = (fr.file, line, outcome)
        dup = (fr.file, fr.name, outcome, expr)  # same check repeated in one function
        if key in self._seen or dup in self._seen_expr:
            return
        self._seen.add(key)
        self._seen_expr.add(dup)
        qual = f"{fr.file}::{fr.name}"
        try:
            expr_names = sorted(self._names(ast.parse(expr, mode="eval")))
        except SyntaxError:
            expr_names = []
        self.regions.append(Region(
            region_id=f"X{len(self.regions) + 1:03d}",
            artifact_id=self.cfg.artifact_id,
            entry_point=self.cfg.entry,
            condition=Condition(expr=expr, params=expr_names, path_prefix=list(prefix)),
            outcome=outcome,
            outcome_detail=detail,
            location=CodeLocation(file=fr.file, line_start=line,
                                  line_end=getattr(node, "end_lineno", None), function=qual,
                                  snippet=self._src(node).splitlines()[0][:200]),
            call_chain=fr.chain + [qual],
            provenance="ast",
            notes=notes,
        ))

    # ------------------------------------------------------------------ analysis
    def run(self) -> list[Region]:
        rel, fname = self.cfg.entry.split("::")
        resolved = self._resolve(rel, fname)
        if resolved is None:
            raise ValueError(f"entry not found: {self.cfg.entry}")
        rel, fn = resolved
        cls = self._class_of(rel, fname)
        self._entry_defaults = self._numeric_defaults(fn)
        self._scan_module_env(rel)
        guards = self._analyse(_Frame(file=rel, func=fn, chain=[], prefix=[], depth=0,
                                      qual=fname, cls=cls))
        last = next((s for s in reversed(fn.body) if isinstance(s, ast.Return)), fn.body[-1])
        fr = _Frame(file=rel, func=fn, chain=[], prefix=[], depth=0, qual=fname, cls=cls)
        self._emit(fr, last, "otherwise", "mechanism", "default path of the entry function",
                   guards, notes="All guards above passed.")
        return self.regions

    def _class_of(self, rel: str, qual: str) -> Optional[str]:
        head = qual.split(".")[0]
        tree = self._load(rel)
        return head if "." in qual and any(
            isinstance(n, ast.ClassDef) and n.name == head for n in tree.body) else None

    @staticmethod
    def _numeric_defaults(fn: ast.FunctionDef) -> dict[object, str]:
        args = fn.args.args[-len(fn.args.defaults):] if fn.args.defaults else []
        out: dict[object, str] = {}
        for a, d in zip(args, fn.args.defaults):
            if isinstance(d, ast.Constant) and isinstance(d.value, (int, float)) \
                    and not isinstance(d.value, bool) and d.value not in (0, 1):
                out[d.value] = a.arg
        return out

    def _scan_module_env(self, rel: str) -> None:
        tree = self._load(rel)
        dummy = ast.FunctionDef(name="<module>", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
                                kw_defaults=[], defaults=[]), body=[], decorator_list=[], lineno=1)
        fr = _Frame(file=rel, func=dummy, chain=[], prefix=[], depth=0)
        for node in tree.body:
            if isinstance(node, ast.If) and ENV_PATTERN.search(self._src(node.test)) and node.orelse:
                self._emit(fr, node.orelse[0], f"not ({self._src(node.test)})", "env_dependent",
                           self._src(node.orelse[0])[:120], [], notes="module-level environment switch")

    def _analyse(self, fr: _Frame) -> list[str]:
        key = (fr.file, fr.name)
        if key in self._visiting or fr.depth > self.cfg.max_depth:
            return []
        self._visiting.add(key)
        fr.params = {a.arg for a in fr.func.args.args + fr.func.args.kwonlyargs}
        fr.tracked = set(fr.params)
        try:
            return self._block(fr, fr.func.body, list(fr.prefix))
        finally:
            self._visiting.discard(key)

    def _block(self, fr: _Frame, body: list[ast.stmt], prefix: list[str]) -> list[str]:
        """Walk a statement list; returns the guards accumulated at its top level."""
        guards: list[str] = []
        for stmt in body:
            here = prefix + guards
            if isinstance(stmt, ast.Global):
                fr.globals_.update(stmt.names)
            elif isinstance(stmt, ast.Assign):
                self._assign(fr, stmt, here)
            elif isinstance(stmt, ast.Assert):
                if self._names(stmt.test) & (fr.tracked | fr.globals_):
                    msg = self._src(stmt.msg) if stmt.msg is not None else "AssertionError"
                    self._emit(fr, stmt, f"not ({self._src(stmt.test)})", "reject", msg, here)
                    guards.append(self._src(stmt.test))
            elif isinstance(stmt, ast.Raise):
                self._emit(fr, stmt, "True", "reject", self._src(stmt)[:120], here)
            elif isinstance(stmt, ast.If):
                guards += self._if(fr, stmt, here)
            elif isinstance(stmt, (ast.For, ast.While, ast.With, ast.Try)):
                for sub in ("body", "orelse", "finalbody"):
                    self._block(fr, getattr(stmt, sub, []) or [], here)
                for h in getattr(stmt, "handlers", []):
                    self._block(fr, h.body, here + ["<exception handler>"])
                continue
            self._literal_check(fr, stmt, here)
            if not isinstance(stmt, ast.If):
                self._follow_calls(fr, [stmt], here)
        return guards

    def _assign(self, fr: _Frame, stmt: ast.Assign, here: list[str]) -> None:
        if self._names(stmt.value) & fr.tracked:
            for t in stmt.targets:
                fr.tracked |= self._names(t)
        cmp = stmt.value
        if (isinstance(cmp, ast.Compare) and self._names(cmp) & fr.params
                and not any(isinstance(x, ast.Constant) for x in [cmp.left, *cmp.comparators])):
            self._emit(fr, stmt, self._src(stmt.value), "mechanism_variant",
                       f"per-element branch stored in {self._src(stmt.targets[0])}", here,
                       notes="Tensor mask selects behaviour per element/head; no Python `if`.")

    def _if(self, fr: _Frame, node: ast.If, here: list[str]) -> list[str]:
        test = self._src(node.test)
        names = self._names(node.test)
        # state cache: `global X` + `if X is None:`
        if isinstance(node.test, ast.Compare) and names & fr.globals_ and "is None" in test:
            self._emit(fr, node, f"{test}  # first call only", "state_dependent",
                       "module-level cache initialised on first call and reused", here)
        # environment switch: report the default (final else) branch of an if/elif chain
        if ENV_PATTERN.search(test) and not (names & (fr.tracked - {"gpu_name"})):
            tail, tests = node, [test]
            while (len(tail.orelse) == 1 and isinstance(tail.orelse[0], ast.If)
                   and ENV_PATTERN.search(self._src(tail.orelse[0].test))):
                tail = tail.orelse[0]
                tests.append(self._src(tail.test))
            branch = tail.orelse[0] if tail.orelse else tail
            cond = " and ".join(f"not ({t})" for t in tests) if tail.orelse else test
            self._emit(fr, branch, cond, "env_dependent", self._src(branch).splitlines()[0][:120], here)
            self._block(fr, node.body, here + [test])
            self._block(fr, node.orelse, here + [f"not ({test})"])
            return []
        relevant = bool(names & fr.tracked)
        returns = any(isinstance(n, ast.Return) for s in node.body for n in ast.walk(s))
        calls = self._call_names(node.body)
        guards: list[str] = []
        if relevant and returns and calls:
            fallback = self._is_fallback(calls)
            if fallback:
                self._emit(fr, node, test, "fallback", f"returns via {', '.join(sorted(set(calls)))}", here)
            guards.append(f"not ({test})")
            if fallback and not self.cfg.descend_into_fallbacks:
                self._block_no_calls(fr, node.body, here + [test])
            else:
                self._block(fr, node.body, here + [test])
        else:
            self._block(fr, node.body, here + [test])
        if node.orelse:
            self._block(fr, node.orelse, here + [f"not ({test})"])
        return guards

    def _block_no_calls(self, fr: _Frame, body: list[ast.stmt], prefix: list[str]) -> None:
        saved = self.cfg.max_depth
        self.cfg.max_depth = -1
        try:
            self._block(fr, body, prefix)
        finally:
            self.cfg.max_depth = saved

    def _literal_check(self, fr: _Frame, stmt: ast.stmt, here: list[str]) -> None:
        if not self._entry_defaults or isinstance(stmt, (ast.If, ast.FunctionDef)):
            return
        for n in ast.walk(stmt):
            if isinstance(n, ast.BinOp):
                for side in (n.left, n.right):
                    if isinstance(side, ast.Constant) and side.value in self._entry_defaults:
                        pname = self._entry_defaults[side.value]
                        if pname in fr.params:
                            self._emit(fr, stmt, f"{pname} != {side.value}", "suspicious",
                                       f"hard-coded {side.value} in `{self._src(n)}` while parameter "
                                       f"`{pname}` is in scope", here)

    def _follow_calls(self, fr: _Frame, stmts: list[ast.stmt], prefix: list[str]) -> None:
        if fr.depth + 1 > self.cfg.max_depth:
            return
        for root in stmts:
            for n in ast.walk(root):
                if not isinstance(n, ast.Call):
                    continue
                if isinstance(n.func, ast.Name):
                    name, cls = n.func.id, None
                elif (isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                      and n.func.value.id == "self" and fr.cls):
                    name, cls = n.func.attr, fr.cls
                else:
                    continue
                res = self._resolve(fr.file, name, cls)
                if res is None:
                    continue
                rel, fn = res
                qual = next(k for k, v in self._funcs[rel].items() if v is fn)
                self._analyse(_Frame(file=rel, func=fn, depth=fr.depth + 1, prefix=list(prefix),
                                     chain=fr.chain + [f"{fr.file}::{fr.name}"], qual=qual,
                                     cls=cls if rel == fr.file else self._class_of(rel, qual)))


def extract(cfg: ExtractConfig) -> list[Region]:
    return RegionExtractor(cfg).run()
