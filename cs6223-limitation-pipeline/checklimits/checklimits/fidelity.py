"""Fidelity measurements (SCORECARD section 3, "fidelity"): s_mod, s_mock, s_entry, s_probe.

  * AST diff: the repository working tree against the pinned commit. `git status` must be
    clean; statements of the call-chain functions are compared statement by statement
    (compound statements compared by header only, pure logging probes ignored).
  * mock on_path: computed from the recording fakes' access log and the tracer's sequence
    number of the first target hit. A mock is on the path if it was touched before the
    target line ran, or if it replaces a function that belongs to the call chain.
  * entry depth: the call-chain function that started first in the traced run.
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
             snippet: Optional[str]) -> AstDiff:
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

    old_t = stmt_at(ast.parse(_file_at_commit(repo, commit, target_file)))
    new_t = stmt_at(ast.parse((repo / target_file).read_text()))
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
        out.append(MockRecord(symbol=d.symbol, kind=d.kind, on_path=on_path, accesses_before_target=before,
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


def s_mod(changed: int, total: int) -> float:
    ratio = changed / total if total else 0.0
    return max(0.0, 1 - ratio / 0.05)


def s_mock(on_path: int, off_path: int) -> float:
    return max(0.0, 1 - 0.4 * on_path - 0.05 * off_path)


def s_entry(index: Optional[int], chain_len: int) -> float:
    if index is None:
        return 0.25
    if chain_len <= 1:
        return 1.0
    return 1 - index / (chain_len - 1)


# How far the harness trusts what a stand-in computed. Initial values, not calibrated:
#   repo_reference      the stand-in calls a reference implementation shipped in the repository
#   independent_native  plain torch re-implementation written for the test
#   stub                canned value (fake module, return_none, return_first_arg)
SIM_WEIGHT = {"repo_reference": 0.9, "independent_native": 0.75, "stub": 0.3}
SCALE_UNVERIFIED = 0.9  # scaled-down run, invariance argued but not checked
SCALE_REFUTED = 0.6     # scaled-down run, full-scale check disagreed


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


def _confidence(touched: list[MockDecl], scale_weight: float) -> float:
    c = scale_weight
    for d in touched:
        c *= SIM_WEIGHT[d.sim_class]
    return round(c, 3)


def info_items(pos: Observation, neg: Observation, raw_pos: dict, raw_neg: dict, decls: list[MockDecl],
               target_loc: str, scale_declared: bool, scale_pos_verified: Optional[bool]) -> list[InfoItem]:
    """Information produced by the runs, each with the mocks it depends on and a confidence."""
    def first_hit(raw: dict) -> Optional[int]:
        return min((h["seq"] for h in (raw.get("trace") or {}).get("target_hits", [])), default=None)

    items: list[InfoItem] = []
    if scale_declared:
        sw_pos = 1.0 if scale_pos_verified else (SCALE_REFUTED if scale_pos_verified is False else SCALE_UNVERIFIED)
        sw_neg = SCALE_UNVERIFIED
    else:
        sw_pos = sw_neg = 1.0
    sw_basis = ("" if not scale_declared else
                "; scale: positive confirmed at full scale" if scale_pos_verified else
                "; scale: invariance argued, not checked")

    # 1. positive effect at the target: only mocks touched before the target can matter
    t = first_hit(raw_pos)
    touched = mocks_touched(decls, raw_pos["mock_events"], t)
    stmt = (f"positive: {pos.exception.type} raised at {target_loc}" if pos.effect and pos.exception
            else "positive: no exception at the target")
    items.append(InfoItem(statement=stmt, run="positive", depends_on_mocks=[d.symbol for d in touched],
                          scale_weight=sw_pos, confidence=_confidence(touched, sw_pos),
                          basis="decided at the target line, before downstream stand-ins run" + sw_basis))
    # 2. negative: the target decision passed
    t = first_hit(raw_neg)
    touched = mocks_touched(decls, raw_neg["mock_events"], t)
    items.append(InfoItem(statement=f"negative: target decision passed at {target_loc}" if neg.target_reached
                          else "negative: target not reached",
                          run="negative", depends_on_mocks=[d.symbol for d in touched], scale_weight=sw_neg,
                          confidence=_confidence(touched, sw_neg),
                          basis="decided at the target line" + ("; scale invariance argued" if scale_declared else "")))
    # 3. negative: what happened after the target (every stand-in touched may matter)
    if neg.target_reached:
        touched = mocks_touched(decls, raw_neg["mock_events"], None)
        if neg.post_target_exception is not None:
            what = f"negative: failed after the target with {neg.post_target_exception.type} at {neg.post_target_exception.raised_at}"
        else:
            what = f"negative: continued past the target and returned {neg.returned}"
        items.append(InfoItem(statement=what, run="negative", depends_on_mocks=[d.symbol for d in touched],
                              scale_weight=sw_neg, confidence=_confidence(touched, sw_neg),
                              basis="downstream behaviour; depends on every stand-in that ran: "
                                    + (", ".join(f"{d.symbol} ({d.sim_class})" for d in touched) or "none")))
    return items
