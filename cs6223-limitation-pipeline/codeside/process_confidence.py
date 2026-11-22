"""Code-side evidence that travels with every Finding (docs/11_process_confidence.md).

Step 4 says "under condition X the code at L does E". The test side (checklimits/CONFIDENCE_SPEC.md) executes
it and sets a level L0-L3. This module is the static supplement: what the code side can establish before any
test runs. It uses the test side's vocabulary (a list of reasons the statement could be wrong, each eliminated /
residual / open / refuted) but it sets NO level of its own: the level stays the test side's. Nothing is executed
and no model is called, so the same record, repo and run files always give the same block.

The block (`process_confidence` of each hand-off record, next to `limitations`; not a schema field) has four parts:

  checks       C1 location (input validity), C2 condition (the decision of the statement), C3 reachability (RIPR),
               C4 feasibility (infeasible paths, z3), C5 extraction (repeatability over the extraction runs),
               C6 effect label (the oracle fits the statement), C7 documentation (an absence claim), C8 review.
  repeats      in how many of the extraction runs the location was found; agreement of the repeated 3b checks;
               which routes (static, LLM) found it.
  testability  a prediction of what the test side can reach: how many mutants its fixed operators produce at the
               target line (fewer than n_min: D3 cannot be eliminated, so at most L1), whether an entry reaches
               the statement (no chain: D14 at most residual, so at most L2), and whether a test can be built at
               all (infeasible witness, or an effect no oracle can judge).
  importance   path (main or side path of the entry), impact (statements guarded, callers), coverage (decisions
               of the function the code side listed). These say how much it matters, never how sure it is.
"""

from __future__ import annotations

import ast
import builtins
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

from codeside.callgraph import MODULE, RepoCallGraph
from codeside.dedup import normalise
from codeside.effect_anchor import _statement_at, can_raise, canonical_snippet

FORMAT = "process-confidence-v2"
ELIMINATED, RESIDUAL, OPEN, REFUTED = "eliminated", "residual", "open", "refuted"
NAMES = {"C1": "location", "C2": "condition", "C3": "reachability", "C4": "feasibility", "C5": "extraction",
         "C6": "effect_label", "C7": "documentation", "C8": "review"}
NOTE_ONLY = ("C7",)  # about the category (is it documented), not about "does the code do this"
N_MIN_DEFAULT = 4    # checklimits Profile.n_min: fewest mutants for D3 to count as measured

_DECISIONS = (ast.If, ast.While, ast.Assert)
_BRANCHES = (ast.If, ast.While)
_CONDITIONAL = (ast.If, ast.ExceptHandler, ast.match_case)  # alternatives; loops repeat, they are counted apart
_LOOPS = (ast.While, ast.For, ast.AsyncFor)
_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_BUILTINS = set(dir(builtins))


def _check(status: str, evidence: str) -> dict:
    return {"status": status, "evidence": evidence}


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    return {id(c): p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}


def _count(stmts) -> int:
    return sum(1 for s in stmts for n in ast.walk(s) if isinstance(n, ast.stmt))


def _own_statements(fn: ast.AST) -> list[ast.stmt]:
    """Statements of a function (or module) without the bodies of nested functions and classes."""
    out, stack = [], list(getattr(fn, "body", []))
    while stack:
        n = stack.pop()
        if isinstance(n, ast.stmt):
            out.append(n)
        if isinstance(n, _DEFS):
            continue
        stack.extend(ast.iter_child_nodes(n))
    return out


def _negate(expr: str) -> str:
    try:
        node = ast.parse(expr.strip(), mode="eval").body
    except (SyntaxError, ValueError):
        return f"not ({expr})"
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return normalise(ast.unparse(node.operand))
    return normalise(f"not ({ast.unparse(node)})")


def _names(expr: ast.AST) -> set[str]:
    """Names an expression reads: plain names and attribute names (`self.x` reads `self` and `x`)."""
    out = set()
    for n in ast.walk(expr):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _parts(test: ast.AST) -> list[str]:
    """Operands of a top-level `and` / `or`, normalised."""
    return [normalise(ast.unparse(v)) for v in test.values] if isinstance(test, ast.BoolOp) else []


class ProcessContext:
    """The repo of one artifact, parsed once. Without a repo every check that needs the source is `open`."""

    def __init__(self, repo: Optional[Path], package_roots: tuple[str, ...] = (".",), entry_points: Optional[list] = None,
                 graph: Optional[RepoCallGraph] = None, runs: Optional[list] = None,
                 agreement: Optional[dict] = None):
        """`runs`: the regions of each extraction run (step 2 was run several times); `agreement`: per
        limitation_id the item of 3b.detail.json (the documentation check was repeated). Both optional."""
        self.runs = [{(r["location"]["file"], r["location"]["line_start"]) for r in run if r.get("location")}
                     for run in (runs or [])]
        self.agreement = agreement or {}
        self._src: dict[str, Optional[str]] = {}
        self.repo = Path(repo) if repo and Path(repo).is_dir() else None
        self.graph = graph or (RepoCallGraph(self.repo, tuple(package_roots or (".",))) if self.repo else None)
        self.entries = [e for e in (entry_points or []) if isinstance(e, str)]
        self._parent: dict[str, dict[int, ast.AST]] = {}
        self._reach: Optional[set[str]] = None
        self._callers: Optional[Counter] = None
        self.listed: set[tuple[str, int]] = set()  # decisions the code side listed (file, line of the decision)

    # ------------------------------------------------------------------ source
    def tree(self, file: str) -> Optional[ast.Module]:
        return self.graph.trees.get(file) if self.graph else None

    def source(self, file: str) -> Optional[str]:
        if file not in self._src:
            path = self.repo / file if self.repo else None
            self._src[file] = path.read_text(errors="replace") if path and path.is_file() else None
        return self._src[file]

    def found_in_runs(self, lims: list[dict]) -> tuple[int, int]:
        """(k, n): the location was in k of the n extraction runs (the best of the merged records)."""
        locs = [(l["code_evidence"][0]["file"], l["code_evidence"][0]["line_start"]) for l in lims if l.get("code_evidence")]
        return max((sum(x in run for run in self.runs) for x in locs), default=0), len(self.runs)

    def parents(self, file: str) -> dict[int, ast.AST]:
        if file not in self._parent:
            self._parent[file] = _parents(self.tree(file))
        return self._parent[file]

    def ancestors(self, file: str, node: ast.AST) -> list[tuple[ast.AST, ast.AST]]:
        """(ancestor, the child through which the node hangs under it), innermost first, inside the function."""
        out, par = [], self.parents(file)
        child, p = node, par.get(id(node))
        while p is not None and not isinstance(p, _DEFS):
            out.append((p, child))
            child, p = p, par.get(id(p))
        return out

    def anchor(self, file: str, line: int) -> tuple[Optional[ast.stmt], Optional[ast.stmt]]:
        """The statement at file:line and the statement that decides it: itself for `if` / `while` / `assert`,
        else the innermost `if` / `while` around it (an unconditional `raise` in a branch is decided by the
        branch), else itself."""
        tree = self.tree(file)
        node = _statement_at(tree, line) if tree is not None else None
        if node is None or isinstance(node, _DECISIONS):
            return node, node
        for anc, _ in self.ancestors(file, node):
            if isinstance(anc, _BRANCHES):
                return node, anc
        return node, node

    def register(self, limitations: list[dict]) -> None:
        """Remember which decisions the code side listed (for the coverage numbers)."""
        for lim in limitations:
            if lim.get("origin") != "code" or not lim.get("code_evidence"):
                continue
            loc = lim["code_evidence"][0]
            _, anc = self.anchor(loc["file"], loc["line_start"])
            self.listed.add((loc["file"], anc.lineno if anc is not None else loc["line_start"]))

    # ------------------------------------------------------------------ call graph
    def reachable(self) -> set[str]:
        """Functions a static call chain reaches from an official entry point."""
        if self._reach is None:
            seen = {e for e in self.entries if self.graph and e in self.graph.funcs}
            todo = list(seen)
            while todo:
                for c in self.graph.calls_from(todo.pop()):
                    if c.callee not in seen:
                        seen.add(c.callee)
                        todo.append(c.callee)
            self._reach = seen
        return self._reach

    def callers(self, fid: str) -> int:
        """Call sites in the repo that the static call graph resolves to this function."""
        if self._callers is None:
            self._callers = Counter(c.callee for f in self.graph.funcs for c in self.graph.calls_from(f))
        return self._callers.get(fid, 0)

    def coverage(self) -> dict:
        """Over all functions an entry reaches: how many decisions exist and how many the code side listed."""
        if not self.graph:
            return {"measured": False, "reason": "repo not available"}
        fns = [self.graph.funcs[f] for f in sorted(self.reachable())]
        total = listed = 0
        for f in fns:
            lines = {n.lineno for n in _own_statements(f.node) if isinstance(n, _DECISIONS)}
            total += len(lines)
            listed += sum((f.file, ln) in self.listed for ln in lines)
        return {"measured": True, "entry_reachable_functions": len(fns), "decisions": total, "decisions_listed": listed,
                "listed_outside_entry_reach": len(self.listed) - listed}


# --------------------------------------------------------------------------- checks
def _main_limitation(record: dict) -> Optional[dict]:
    """The code-side Limitation the Finding's witness was built from."""
    code = [l for l in record.get("limitations") or [] if l.get("origin") == "code" and l.get("code_evidence")]
    if not code:
        return None
    hint = record.get("witness_hint") or {}
    where = {str(hint.get(k, "")).split("-")[0] for k in ("location", "effect_location")}
    for l in code:
        c = l["code_evidence"][0]
        if f"{c['file']}:{c['line_start']}" in where:
            return l
    return code[0]


def _reparse(snippet: str) -> Optional[str]:
    """The snippet in the canonical form, so quote style and spacing do not count as a difference."""
    text = snippet.strip()
    try:
        return canonical_snippet(ast.parse(text + (" pass" if text.endswith(":") else "")).body[0])
    except (SyntaxError, ValueError, IndexError):
        return None


def _c1(loc: dict, node: Optional[ast.stmt], pc: ProcessContext) -> dict:
    where = f"{loc['file']}:{loc['line_start']}"
    if pc.repo is None:
        return _check(OPEN, "repo not available: the location was not compared with the source")
    path = pc.repo / loc["file"]
    if not path.is_file():
        return _check(REFUTED, f"{loc['file']} does not exist at the pinned commit")
    if pc.tree(loc["file"]) is None:
        n = len(path.read_text(errors="replace").splitlines())
        ok = 1 <= loc["line_start"] <= n
        return _check(RESIDUAL if ok else REFUTED, f"not a parsed Python file; line {loc['line_start']} "
                      + ("is in range, the text was not compared" if ok else f"is outside the file ({n} lines)"))
    if node is None:
        lines = path.read_text(errors="replace").splitlines()
        text = lines[loc["line_start"] - 1] if 1 <= loc["line_start"] <= len(lines) else None
        snippet = " ".join((loc.get("snippet") or "").split())
        if text is not None and snippet and snippet in " ".join(text.split()):
            return _check(RESIDUAL, f"the recorded text is on {where}, but no statement starts there (a `def` or "
                                    "`else` line, or the middle of a statement): a test cannot target this line")
        return _check(REFUTED, f"no statement starts at {where} and the recorded snippet is not on that line")
    snippet = loc.get("snippet")
    if not snippet:
        return _check(RESIDUAL, f"a statement starts at {where}; the record has no snippet to compare")
    actual = canonical_snippet(node)
    if " ".join(actual.split()) == " ".join(snippet.split()) or actual == _reparse(snippet):
        return _check(ELIMINATED, f"the statement at {where} is the recorded snippet")
    return _check(REFUTED, f"the statement at {where} is `{actual[:80]}`, the record says `{snippet[:80]}`")


def _c2(lim: dict, hint: dict, file: str, node: Optional[ast.stmt], anchor: Optional[ast.stmt], pc: ProcessContext) -> dict:
    if pc.tree(file) is None or node is None:
        return _check(OPEN, "the statement was not found, so the condition was not compared with it")
    exprs = [e for e in ((lim.get("condition") or {}).get("expr"), hint.get("condition")) if e]
    parsed = []
    for e in exprs:
        try:
            parsed.append(ast.parse(e.strip(), mode="eval").body)
        except (SyntaxError, ValueError):
            pass
    if not parsed:
        return _check(OPEN, "the condition is not a Python expression: it cannot be compared with the statement")
    test = anchor.test if isinstance(anchor, _DECISIONS) else None
    if test is not None:
        t = ast.unparse(test)
        forms = {normalise(t), _negate(t)}
        if any(normalise(ast.unparse(p)) in forms for p in parsed):
            which = "this statement" if anchor is node else f"the enclosing branch at line {anchor.lineno}"
            return _check(ELIMINATED, f"the condition is the decision of {which}, or its negation")
        parts = set(_parts(test)) | {_negate(x) for x in _parts(test)}
        if any(normalise(ast.unparse(p)) in parts for p in parsed):
            return _check(RESIDUAL, f"the condition is one operand of the decision at line {anchor.lineno}, not all of it")
    # a decision inside the statement: the test of a conditional expression or the filter of a comprehension
    inner = [n.test for n in ast.walk(node) if isinstance(n, ast.IfExp)] + \
            [i for n in ast.walk(node) if isinstance(n, ast.comprehension) for i in n.ifs]
    forms = {f for t in inner for f in (normalise(ast.unparse(t)), _negate(ast.unparse(t)))}
    if any(normalise(ast.unparse(p)) in forms for p in parsed):
        return _check(ELIMINATED, "the condition is a decision inside this statement (a conditional expression or a "
                                  "comprehension filter), or its negation")
    fn = pc.graph.func_at(file, node.lineno)
    scope = fn.node if fn is not None else pc.tree(file)
    known = _names(scope) | {a.arg for n in ast.walk(scope) if isinstance(n, ast.arguments)
                             for a in [*n.posonlyargs, *n.args, *n.kwonlyargs, n.vararg, n.kwarg] if a} | _BUILTINS
    missing = sorted(_names(parsed[0]) - known)
    if missing:
        return _check(REFUTED, f"the condition uses names that do not occur in the function: {', '.join(missing[:5])}")
    return _check(RESIDUAL, "the condition is not the text of the decision (a paraphrase); its names all occur "
                            "in the function")


def _c3(hint: dict) -> dict:
    s = hint.get("call_chain_status")
    if s == "entry_is_target":
        return _check(ELIMINATED, "the statement is in an official entry function")
    if s == "module_level":
        return _check(ELIMINATED, "module-level statement: it runs when the module is imported")
    if s == "resolved":
        chain = hint.get("call_chain") or []
        unc = hint.get("uncertain_steps") or []
        if unc:
            return _check(RESIDUAL, f"call chain of {len(chain) - 1} step(s), guessed step(s): {'; '.join(unc)[:200]}")
        return _check(ELIMINATED, f"call chain of {len(chain) - 1} step(s) from {chain[0]}, every step a call site in the source")
    if hint.get("calls_entry"):
        return _check(OPEN, "no call chain from an entry: this function calls the entry (a caller-side integration)")
    return _check(OPEN, "no static call chain from an official entry to this function")


def _c4(hint: dict) -> dict:
    s = hint.get("status")
    if s == "infeasible":
        why = "after callee names are stated in the entry's names" if hint.get("infeasible_because") == "call_chain" else ""
        return _check(REFUTED, f"z3: no values satisfy the condition and its path prefix {why}".strip())
    if s == "solved":
        dropped = hint.get("dropped_prefix") or []
        if dropped:
            return _check(RESIDUAL, f"z3 found trigger and contrast, but {len(dropped)} path-prefix condition(s) "
                                    "could not be given to the solver")
        if hint.get("aliases_not_applied"):
            return _check(RESIDUAL, "z3 found trigger and contrast; local definitions were not tied to the caller's "
                                    "conditions (no call chain)")
        if hint.get("call_chain_status") == "not_found" and hint.get("path_prefix"):
            return _check(RESIDUAL, "z3 found trigger and contrast; without a call chain the path prefix may mix "
                                    "names of different functions")
        return _check(ELIMINATED, f"z3 found trigger and contrast under {len(hint.get('path_prefix') or [])} "
                                  "path-prefix condition(s)")
    if s in ("solved_contrast_outside_scope", "trigger_only", "always"):
        return _check(RESIDUAL, f"witness status `{s}`: no contrast point inside the path and the paper's scope")
    return _check(OPEN, f"witness status `{s}`: the condition was not solved")


def _c5(code_lims: list[dict], pc: ProcessContext) -> dict:
    prov = sorted({l.get("provenance") for l in code_lims})
    if "ast" in prov or "manual" in prov:
        return _check(ELIMINATED, "found by the deterministic static route (same input, same output)"
                      + ("; the LLM route found it too" if "llm" in prov else ""))
    k, n = pc.found_in_runs(code_lims)
    if n < 2:
        return _check(RESIDUAL, "proposed by the LLM route; run-to-run agreement was not measured")
    if k == n:
        return _check(ELIMINATED, f"proposed by the LLM route in all {n} extraction runs (same file and line)")
    return _check(RESIDUAL, f"proposed by the LLM route in {k} of {n} extraction runs (same file and line)")


def _c6(effect: str, node: Optional[ast.stmt]) -> dict:
    if effect == "other":
        return _check(OPEN, "effect `other`: no effect is claimed that a test can judge at this statement")
    if node is None:
        return _check(OPEN, "the statement was not found")
    if effect == "reject":
        ok, need = can_raise(node), "a statement that can raise"
    elif effect in ("path_change", "state"):
        ok, need = isinstance(node, _BRANCHES), "an `if` or a `while`"
    else:
        return _check(RESIDUAL, f"effect `{effect}` needs a measurement (differential or resource), not a statement check")
    return _check(ELIMINATED if ok else REFUTED, f"effect `{effect}` needs {need}; the statement is "
                  f"`{type(node).__name__.lower()}`")


def _c7(record: dict, lim: dict, pc: ProcessContext) -> dict:
    vers = [v for v in record.get("verifications") or [] if v.get("limitation_id") == lim["limitation_id"]] or \
           (record.get("verifications") or [])
    if not vers:
        return _check(OPEN, "no documentation check (3b) for this limitation")
    v = vers[0]
    ag = (pc.agreement.get(lim["limitation_id"]) or {}).get("paper_agreement")
    if ag is not None and ag < 1 and not str(v.get("verifier", "")).startswith("human:"):
        return _check(RESIDUAL, f"3b `{v.get('result')}`, but its repeats disagree (agreement {ag:.2f})")
    human = str(v.get("verifier", "")).startswith("human:")
    if v.get("result") == "not_found":
        return _check(ELIMINATED if human else RESIDUAL, "3b found no statement of it: an absence, from retrieval and "
                      f"a reading by {v.get('verifier')}; it cannot be proved")
    n = len(v.get("matching_evidence") or [])
    if n:
        return _check(ELIMINATED, f"3b `{v.get('result')}` with {n} quote(s), each checked to occur verbatim in its source")
    return _check(RESIDUAL, f"3b `{v.get('result')}` without a quote")


def _c8(record: dict) -> dict:
    review, note = record.get("review") or "unreviewed", record.get("review_note") or ""
    human = "not human" not in note and note.startswith("human")
    if review == "unreviewed":
        return _check(OPEN, "nobody reviewed it")
    if review == "wrong":
        return _check(REFUTED, "reviewed as wrong" + ("" if human else " (by an LLM reviewer, not a human)"))
    return _check(ELIMINATED if human else RESIDUAL, f"reviewed `{review}`" + ("" if human else " by an LLM reviewer, not a human"))


# --------------------------------------------------------------------------- repeats
def _repeats(lim: dict, code_lims: list[dict], pc: ProcessContext) -> dict:
    k, n = pc.found_in_runs(code_lims)
    item = pc.agreement.get(lim["limitation_id"])
    return {"extraction_runs": {"measured": True, "found_in": k, "of": n, "match": "same file and line"} if n
            else {"measured": False, "reason": "no repeated extraction runs for this artifact"},
            "documentation_check": {"measured": True, "repeats": len(item.get("per_run") or []),
                                    "paper_agreement": item.get("paper_agreement"),
                                    "elsewhere_agreement": item.get("elsewhere_agreement")} if item
            else {"measured": False, "reason": "no repeated 3b record for this limitation"},
            "routes": sorted({l.get("provenance") for l in code_lims if l.get("provenance")})}


# --------------------------------------------------------------------------- testability
_GENERATE = []


def _mutant_generator():
    """The test side's mutant generator (its fixed operator set), or None when checklimits is not importable.
    Using the same function is what makes the count a prediction of its D3 and not a second definition."""
    if not _GENERATE:
        # loaded by path: from the repo root `checklimits/` is a directory that holds the package, not the package
        path = Path(__file__).resolve().parents[1] / "checklimits" / "checklimits" / "mutate.py"
        gen = None
        if path.is_file():
            spec = importlib.util.spec_from_file_location("_checklimits_mutate", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod  # dataclasses look the module up while the class is built
            spec.loader.exec_module(mod)
            gen = mod.generate
        _GENERATE.append(gen)
    return _GENERATE[0]


def _testability(loc: dict, hint: dict, checks: dict, pc: ProcessContext) -> dict:
    """What the test side can reach for this Finding, from its own level rules (CONFIDENCE_SPEC.md):
    L2 needs D3 eliminated, which needs n_min mutants of the target line; L3 needs D14 eliminated, which needs
    the official entry to reach the statement. A ceiling, not a forecast: a test can always end lower."""
    st = {k: c["status"] for k, c in checks.items()}
    if st["C4"] == REFUTED:
        return {"measured": True, "testable": False, "expect_not_run": "witness_unusable",
                "because": "C4: the solver shows the condition cannot hold on the path"}
    if st["C6"] == OPEN and checks["C6"]["evidence"].startswith("effect `other`"):
        return {"measured": True, "testable": False, "expect_not_run": "outcome_unsupported",
                "because": "C6: effect `other`, no oracle can judge it"}
    gen, src = _mutant_generator(), pc.source(loc["file"])
    if gen is None or src is None or pc.tree(loc["file"]) is None:
        return {"measured": False, "reason": "repo source or the test side's mutant generator not available"}
    try:
        ops = [m.operator for m in gen(src, loc["line_start"])]
    except (SyntaxError, ValueError):
        ops = []
    limits = []
    if len(ops) < N_MIN_DEFAULT:
        limits.append(f"D3: {len(ops)} mutant(s) of the target line, fewer than n_min={N_MIN_DEFAULT}; it cannot be eliminated")
    if st["C3"] == OPEN:
        limits.append("D14: no call chain from an official entry; a test has to call a deeper function, at most residual")
    ceiling = "L1" if len(ops) < N_MIN_DEFAULT else "L2" if st["C3"] == OPEN else "L3"
    try:
        has_calls = any(isinstance(n, ast.Call) for n in ast.walk(ast.parse(hint.get("condition") or "", mode="eval")))
    except (SyntaxError, ValueError):
        has_calls = None
    sorts = {a.get("sort") for a in (hint.get("atoms") or {}).values() if isinstance(a, dict)}
    return {"measured": True, "testable": True, "mutants": len(ops), "mutants_needed": N_MIN_DEFAULT,
            "mutant_operators": dict(sorted(Counter(ops).items())),
            "ceiling": ceiling, "limited_by": limits,
            "condition_has_calls": has_calls,  # a condition with calls cannot be evaluated directly (D2)
            "integer_boundary": (sorts == {"int"}) if sorts else None,  # ON/OFF neighbours need integers (D5)
            "note": "ceiling of the test level under the test side's rules; uncalibrated, a test can end lower"}


# --------------------------------------------------------------------------- numbers
def _describe(anc: ast.AST, child: ast.AST) -> Optional[str]:
    """One enclosing construct that makes the code below it conditional, as text."""
    if isinstance(anc, ast.If):
        t = ast.unparse(anc.test)[:80]
        return f"else of `if {t}`" if any(c is child for c in anc.orelse) else f"if {t}"
    if isinstance(anc, ast.ExceptHandler):
        return f"except {ast.unparse(anc.type)[:60] if anc.type else ''}".strip()
    if isinstance(anc, ast.match_case):
        return f"case {ast.unparse(anc.pattern)[:60]}"
    return None


def _enclosing(pc: ProcessContext, file: str, node: ast.AST) -> list[str]:
    return [d for d in (_describe(a, c) for a, c in pc.ancestors(file, node) if isinstance(a, _CONDITIONAL)) if d]


def _statement_holding(tree: ast.Module, line: int) -> Optional[ast.stmt]:
    """The innermost statement whose lines include `line` (a call can sit in the middle of a statement)."""
    best = None
    for n in ast.walk(tree):
        if isinstance(n, ast.stmt) and not isinstance(n, _DEFS) and n.lineno <= line <= (n.end_lineno or n.lineno):
            if best is None or n.lineno >= best.lineno:
                best = n
    return best


def _numbers(hint: dict, file: str, anchor: Optional[ast.stmt], pc: ProcessContext) -> tuple[dict, dict, dict]:
    if anchor is None or pc.graph is None:
        why = "repo not available" if pc.graph is None else "the statement was not found"
        na = {"measured": False, "reason": why}
        return dict(na), dict(na), dict(na)
    own = _enclosing(pc, file, anchor)
    conditional_calls = []
    for site in hint.get("call_sites") or []:
        cfile = site["caller"].partition("::")[0]
        tree = pc.tree(cfile)
        stmt = _statement_holding(tree, site["line"]) if tree is not None else None
        enc = _enclosing(pc, cfile, stmt) if stmt is not None else []
        if enc:
            conditional_calls.append(f"{site['caller']} -> {site['callee']} at line {site['line']}: {enc[0]}")
    status = hint.get("call_chain_status")
    if own or conditional_calls:
        on = "side"
    elif status in ("entry_is_target", "module_level", "resolved"):
        on = "main"
    else:
        on = "unknown"
    loops = sum(isinstance(a, _LOOPS) for a, _ in pc.ancestors(file, anchor))
    path = {"measured": True, "decision_on": on, "enclosing_conditions": own, "enclosing_loops": loops,
            "conditional_call_sites": conditional_calls,
            "path_prefix_conditions": len(hint.get("path_prefix") or []),
            "chain_depth": max(len(hint.get("call_chain") or []) - 1, 0) if status in ("resolved", "entry_is_target") else None}
    if on == "unknown":
        path["note"] = "not nested in its own function, but no call chain: the callers were not seen"

    fn = pc.graph.func_at(file, anchor.lineno)
    scope = fn.node if fn is not None else pc.tree(file)
    stmts = _own_statements(scope)
    if isinstance(anchor, _BRANCHES):
        kind, guarded = "branch_body", _count(anchor.body)
        extra = {"else_statements": _count(anchor.orelse)}
    else:
        kind, guarded = "rest_of_function", sum(1 for s in stmts if s.lineno > (anchor.end_lineno or anchor.lineno))
        extra = {}
    impact = {"measured": True, "guards": kind, "guarded_statements": guarded, **extra, "function_statements": len(stmts),
              "call_chains_from_entry": (1 + len(hint.get("other_chains") or [])) if hint.get("call_chain") else 0,
              "call_sites_of_function": pc.callers(fn.id) if fn is not None else None}

    lines = {n.lineno for n in stmts if isinstance(n, _DECISIONS)}
    coverage = {"measured": True, "function": fn.id if fn is not None else f"{file}::{MODULE}",
                "function_decisions": len(lines), "function_decisions_listed": sum((file, ln) in pc.listed for ln in lines),
                "function_reached_from_entry": (fn.id in pc.reachable()) if fn is not None else None}
    return path, impact, coverage


# --------------------------------------------------------------------------- entry
def assess(record: dict, pc: ProcessContext) -> Optional[dict]:
    """The process-confidence block of one hand-off record (Finding fields + `limitations` + `verifications`).
    None for a Finding without a code-side Limitation: this is the code side's process, not the paper side's."""
    lim = _main_limitation(record)
    if lim is None:
        return None
    hint = record.get("witness_hint") or {}
    loc = lim["code_evidence"][0]
    node, anchor = pc.anchor(loc["file"], loc["line_start"])
    code_lims = [l for l in record["limitations"] if l.get("origin") == "code"]
    checks = {"C1": _c1(loc, node, pc), "C2": _c2(lim, hint, loc["file"], node, anchor, pc), "C3": _c3(hint),
              "C4": _c4(hint), "C5": _c5(code_lims, pc), "C6": _c6(record.get("effect_type") or "", node),
              "C7": _c7(record, lim, pc), "C8": _c8(record)}
    for k, c in checks.items():
        c["name"] = NAMES[k]
    path, impact, coverage = _numbers(hint, loc["file"], anchor, pc)
    return {"format": FORMAT, "calibrated": False, "limitation_id": lim["limitation_id"],
            "checks": {k: {"name": c["name"], "status": c["status"], "evidence": c["evidence"]} for k, c in checks.items()},
            "open_doubts": [k for k, c in checks.items() if c["status"] != ELIMINATED and k not in NOTE_ONLY],
            "repeats": _repeats(lim, code_lims, pc),
            "testability": _testability(loc, hint, checks, pc),
            "importance": {"path": path, "impact": impact, "coverage": coverage}}


def _ceiling(block: dict) -> str:
    t = block["testability"]
    return "not_measured" if not t.get("measured") else t["ceiling"] if t.get("testable") else "not_testable"


def assess_all(records: list[dict], pc: ProcessContext) -> dict:
    """Fill `process_confidence` in every record (in place) and return the summary of the artifact."""
    for r in records:
        pc.register(r.get("limitations") or [])
    for r in records:
        r["process_confidence"] = assess(r, pc)
    done = [r["process_confidence"] for r in records if r["process_confidence"]]
    return {"format": FORMAT, "calibrated": False, "findings": len(records), "assessed": len(done),
            "not_assessed_paper_only": len(records) - len(done),
            "repo_available": pc.repo is not None,
            "ceiling": dict(sorted(Counter(_ceiling(b) for b in done).items())),
            "by_check": {k: dict(sorted(Counter(b["checks"][k]["status"] for b in done).items())) for k in NAMES},
            "decision_on": dict(sorted(Counter(b["importance"]["path"].get("decision_on", "not_measured") for b in done).items())),
            "coverage": pc.coverage()}
