"""Fidelity measurements (SCORECARD section 3, "fidelity"): s_mod, s_mock, s_entry, s_probe.

  * AST diff: the repository working tree against the pinned commit. `git status` must be
    clean; statements of the call-chain functions are compared statement by statement
    (compound statements compared by header only, pure logging probes ignored).
  * mock on_path: computed from the recording fakes' access log and the tracer's sequence
    number of the first target hit. A mock is on the path if it was touched before the
    target line ran, or if it replaces a function that belongs to the call chain.
  * entry depth: the call-chain function that started first in the traced run.
  * causal prefix: for each observation, which stand-ins were touched before it was produced.
  * probe effect: the traced run and an untraced run must show the same observable result.
"""
from __future__ import annotations

import ast
import copy
import difflib
import subprocess
from pathlib import Path
from typing import Any, Iterator, Optional

from .models import AstDiff, CoverageScope, InfoItem, MockDecl, MockRecord, Observation

_COMPOUND = ("body", "orelse", "finalbody", "handlers", "cases")
_LOG_ROOTS = {"print", "logging", "logger", "log", "warnings"}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
                          timeout=60).stdout


def iter_stmts(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    for st in body:
        yield st
        for f in ("body", "orelse", "finalbody"):
            sub = getattr(st, f, None)
            if sub:
                yield from iter_stmts(sub)
        for h in getattr(st, "handlers", []) or []:
            yield from iter_stmts(h.body)
        for c in getattr(st, "cases", []) or []:
            yield from iter_stmts(c.body)


def _is_log_probe(st: ast.stmt) -> bool:
    if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call)):
        return False
    f = st.value.func
    while isinstance(f, ast.Attribute):
        f = f.value
    return isinstance(f, ast.Name) and f.id in _LOG_ROOTS


def _is_docstring(st: ast.stmt) -> bool:
    return isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str)


def shallow_dump(st: ast.stmt) -> str:
    n = copy.copy(st)
    for f in _COMPOUND:
        if hasattr(n, f):
            setattr(n, f, [])
    return ast.dump(n)


def functions_by_qualname(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    out: dict[str, Any] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = prefix + ch.name
                out[q] = ch
                visit(ch, q + ".<locals>.")
            elif isinstance(ch, ast.ClassDef):
                visit(ch, prefix + ch.name + ".")
            else:
                visit(ch, prefix)

    visit(tree, "")
    return out


def fn_statements(fn: ast.AST) -> list[ast.stmt]:
    return [s for s in iter_stmts(fn.body) if not _is_docstring(s) and not _is_log_probe(s)]


def _file_at_commit(repo: Path, commit: str, rel: str) -> str:
    return _git(repo, "show", f"{commit}:{rel}")


def ast_diff(repo: Path, commit: str, chain: list[str], target_file: str, target_line: int,
             snippet: Optional[str], target_function: str = "") -> AstDiff:
    status = _git(repo, "status", "--porcelain").splitlines()
    changed_tracked = [l for l in _git(repo, "diff", "--name-only", commit).splitlines() if l]
    changed_untracked = [l[3:] for l in status if l.startswith("??")]
    files = sorted({c.partition("::")[0] for c in chain} | {target_file})
    total = changed = 0
    for rel in files:
        old_tree = ast.parse(_file_at_commit(repo, commit, rel))
        new_tree = ast.parse((repo / rel).read_text())
        old_fns, new_fns = functions_by_qualname(old_tree), functions_by_qualname(new_tree)
        for c in chain:
            f, _, q = c.partition("::")
            if f != rel or q not in old_fns:
                continue
            old = [shallow_dump(s) for s in fn_statements(old_fns[q])]
            total += len(old)
            if q not in new_fns:
                changed += len(old)
                continue
            new = [shallow_dump(s) for s in fn_statements(new_fns[q])]
            for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
                if op != "equal":
                    changed += max(i2 - i1, j2 - j1)

    def stmt_at(tree: ast.AST) -> Optional[str]:
        for n in ast.walk(tree):
            if isinstance(n, ast.stmt) and n.lineno == target_line and not isinstance(
                    n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return ast.dump(n)  # full dump: header and predicate
        return None

    def stmts_of_function(tree: ast.AST) -> set[str]:
        fn = functions_by_qualname(tree).get(target_function)
        return {ast.dump(s) for s in iter_stmts(fn.body)} if fn is not None else set()

    # The target statement is intact if the committed statement still exists, unchanged, in the same
    # function. Matching by content (not by line) keeps a harmless insertion above it from looking like
    # an edit of the target; the moved line number is caught separately by the snippet check (D12).
    old_t = stmt_at(ast.parse(_file_at_commit(repo, commit, target_file)))
    new_t = old_t if old_t is not None and old_t in stmts_of_function(ast.parse((repo / target_file).read_text())) else None
    src_lines = (repo / target_file).read_text().splitlines()
    line_txt = src_lines[target_line - 1].strip() if 0 < target_line <= len(src_lines) else ""
    return AstDiff(
        files_checked=files,
        files_changed=sorted(set(changed_tracked) | set(changed_untracked)),
        statements_total=total, statements_changed=changed,
        target_statement_intact=(old_t is not None and old_t == new_t),
        snippet_matches_region=(snippet is None or snippet.strip() == line_txt),
        git_status_clean=not status,
    )


def coverage(repo: Path, chain: list[str], trace_lines: dict[str, list[int]]) -> CoverageScope:
    total = executed = 0
    for c in chain:
        f, _, q = c.partition("::")
        fns = functions_by_qualname(ast.parse((repo / f).read_text()))
        if q not in fns:
            continue
        lines = {s.lineno for s in fn_statements(fns[q])}
        total += len(lines)
        executed += len(lines & set(trace_lines.get(q, [])))
    return CoverageScope(lines_executed=executed, lines_total=total)


def entry_index(chain: list[str], first_started: Optional[str]) -> Optional[int]:
    """Position in call_chain of the function that started first; None = not in the chain."""
    if first_started is None:
        return None
    try:
        return chain.index(first_started)
    except ValueError:
        return None


def _module_dotted(file_rel: str) -> str:
    return file_rel[:-3].replace("/", ".") if file_rel.endswith(".py") else file_rel


def mock_records(decls: list[MockDecl], runs: list[tuple[list[dict], Optional[int]]],
                 chain: list[str]) -> list[MockRecord]:
    """runs: per executed case, (mock_events, seq of the first target hit or None)."""
    chain_symbols = {f"{_module_dotted(c.partition('::')[0])}.{c.partition('::')[2]}" for c in chain}
    out = []
    for d in decls:
        before = total = 0
        for events, target_seq in runs:
            mine = [e for e in events if e["symbol"] == d.symbol or e["symbol"].startswith(d.symbol + ".")]
            total += len(mine)
            before += sum(1 for e in mine if target_seq is None or e["seq"] < target_seq)
        on_path = before > 0 or d.symbol in chain_symbols
        out.append(MockRecord(symbol=d.symbol, kind=d.kind, sim_class=d.sim_class, on_path=on_path, accesses_before_target=before,
                              accesses_total=total, reason=d.reason))
    return out


def observable(raw: dict[str, Any]) -> tuple:
    exc = raw.get("exception") or {}
    return (raw.get("status"), exc.get("type"), exc.get("raised_at"), exc.get("message"), raw.get("returned"))


def probe_effect(traced: list[dict], untraced: list[dict]) -> tuple[bool, str]:
    if not untraced:
        return True, "no untraced run requested"
    for t, u in zip(traced, untraced):
        if observable(t) != observable(u):
            return False, f"traced {observable(t)} != untraced {observable(u)}"
    return True, "traced and untraced runs show the same observable result"


_STATE_OF_CLASS = {"repo_reference": "simulated:reference", "independent_native": "simulated:fake", "stub": "simulated:stub"}
_RANK = {"direct": 0, "simulated:reference": 1, "simulated:fake": 2, "simulated:stub": 3}


def mocks_touched(decls: list[MockDecl], events: list[dict], before_seq: Optional[int]) -> list[MockDecl]:
    """Mocks accessed (strictly before `before_seq`, or at all if None) in one run."""
    out = []
    for d in decls:
        for e in events:
            if (e["symbol"] == d.symbol or e["symbol"].startswith(d.symbol + ".")) and (
                    before_seq is None or e["seq"] < before_seq):
                out.append(d)
                break
    return out


def evidence_state(touched: list[MockDecl]) -> str:
    states = [_STATE_OF_CLASS[d.sim_class] for d in touched]
    return max(states, key=lambda s: _RANK[s], default="direct")


def info_items(pos: Observation, neg: Observation, raw_pos: dict, raw_neg: dict, decls: list[MockDecl],
               target_loc: str) -> list[InfoItem]:
    """Observations with the stand-ins in their causal past (CONFIDENCE_SPEC.md section 5)."""
    def first_hit(raw: dict) -> Optional[int]:
        # the checked call only: stand-ins touched while earlier (prelude) calls built the state are in its past too
        return min((h["seq"] for h in (raw.get("trace") or {}).get("target_hits", [])
                    if h.get("call", 0) == raw.get("final_call", 0)), default=None)

    def item(stmt, run, bearing, touched, basis):
        return InfoItem(statement=stmt, run=run, verdict_bearing=bearing,
                        depends_on_mocks=[d.symbol for d in touched], evidence_state=evidence_state(touched),
                        basis=basis)

    items: list[InfoItem] = []
    t = first_hit(raw_pos)
    touched = mocks_touched(decls, raw_pos["mock_events"], t)
    branch = pos.observed_text.startswith("branch") or neg.observed_text.startswith("branch")
    pos_stmt = (f"positive: {pos.observed_text}" if branch else
                f"positive: {pos.exception.type} raised at {target_loc}" if pos.effect and pos.exception
                else "positive: no exception at the target")
    items.append(item(pos_stmt, "positive", True, touched,
                      "decided at the target line; stand-ins touched before it: " + (", ".join(d.symbol for d in touched) or "none")))
    t = first_hit(raw_neg)
    touched = mocks_touched(decls, raw_neg["mock_events"], t)
    neg_stmt = (f"negative: {neg.observed_text}" if branch else
                f"negative: target decision passed at {target_loc}" if neg.target_reached else "negative: target not reached")
    items.append(item(neg_stmt,
                      "negative", True, touched,
                      "decided at the target line; stand-ins touched before it: " + (", ".join(d.symbol for d in touched) or "none")))
    if neg.target_reached:
        touched = mocks_touched(decls, raw_neg["mock_events"], None)
        what = (f"negative: failed after the target with {neg.post_target_exception.type} at {neg.post_target_exception.raised_at}"
                if neg.post_target_exception is not None
                else f"negative: continued past the target and returned {neg.returned}")
        items.append(item(what, "negative", False, touched,
                          "downstream behaviour; stand-ins that ran: "
                          + (", ".join(f"{d.symbol} ({d.sim_class})" for d in touched) or "none")))
    return items
