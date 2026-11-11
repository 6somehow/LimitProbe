"""Execution tracer built on sys.monitoring (PEP 669).

Why sys.monitoring and not sys.settrace:
  * the interpreter is 3.14, so sys.monitoring exists;
  * it has per-location DISABLE: lines and functions outside the call chain are switched
    off after their first event, so torch / transformers / triton code costs nothing,
    while sys.settrace would call a Python function for every line of every library;
  * it does not occupy the sys.settrace slot, so it cannot clash with coverage or with
    code under test that installs its own trace function.

What it records (all for the call chain of the Region only):
  * each execution of the target line: sequence number, the locals at that moment
    (summarised), the value of Region.condition.expr evaluated on them (or of an
    agent-written predicate), and the outcome of the target decision;
  * the order in which call-chain functions started (entry depth);
  * the lines executed inside call-chain functions (coverage).

Decision outcome of the target statement, found by looking at the next event in the
same frame:
  assert  next line event -> "true"; AssertionError unwinding from the target line -> "false"
  if/while  next line inside the body -> "true"; elsewhere -> "false"
  any exception from the target line that is not the assert itself -> "error"

The sequence numbers come from fakes.next_seq(), the same counter the recording mocks use.
"""
from __future__ import annotations

import ast
import builtins
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from . import fakes

mon = sys.monitoring
TOOL_ID = mon.PROFILER_ID
E = mon.events

_SAFE_BUILTINS = {n: getattr(builtins, n)
                  for n in ("len", "min", "max", "abs", "int", "float", "bool", "isinstance", "any", "all",
                            "sum", "range", "set", "tuple", "list", "dict", "str", "sorted", "round")}


@dataclass
class ChainFn:
    file: str  # repo-relative
    qualname: str


def parse_chain(chain: list[str]) -> list[ChainFn]:
    out = []
    for item in chain:
        f, _, fn = item.partition("::")
        out.append(ChainFn(f, fn))
    return out


@dataclass
class TargetSpec:
    file: str  # repo-relative
    line: int
    function: str  # qualname
    kind: str = "other"  # assert | if | while | other
    body: tuple[int, int] = (0, 0)
    cond_expr: Optional[str] = None
    predicate: Optional[Callable[[dict], Any]] = None


def classify_target(repo_root: Path, file: str, line: int) -> tuple[str, tuple[int, int]]:
    tree = ast.parse((repo_root / file).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and node.lineno == line:
            if isinstance(node, ast.Assert):
                return "assert", (0, 0)
            if isinstance(node, (ast.If, ast.While)):
                return ("if" if isinstance(node, ast.If) else "while"), (node.body[0].lineno, node.body[-1].end_lineno)
    return "other", (0, 0)


def summarize(v: Any) -> str:
    if hasattr(v, "shape") and hasattr(v, "dtype"):
        try:
            return f"Tensor{tuple(v.shape)} {v.dtype}"
        except Exception:
            pass
    if isinstance(v, (int, float, bool, str, type(None))):
        return repr(v)[:80]
    return f"<{type(v).__name__}>"


@dataclass
class _Pending:
    hit: dict
    code: Any


@dataclass
class _Info:
    in_scope: bool
    has_target: bool


class Tracer:
    def __init__(self, repo_root: Path, chain: list[ChainFn], target: TargetSpec) -> None:
        self.repo_root = repo_root.resolve()
        self.chain = chain
        self.target = target
        self.scope_names = {(str((self.repo_root / c.file).resolve()), c.qualname) for c in chain}
        self.target_file_abs = str((self.repo_root / target.file).resolve())
        self.scope_names.add((self.target_file_abs, target.function))
        self.hits: list[dict] = []
        self.starts: list[dict] = []
        self.lines: dict[str, set[int]] = {}
        self._pending: dict[int, _Pending] = {}
        self._info_cache: dict[Any, _Info] = {}
        self.active = False

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        mon.use_tool_id(TOOL_ID, "checklimits")
        mon.register_callback(TOOL_ID, E.LINE, self._on_line)
        mon.register_callback(TOOL_ID, E.PY_START, self._on_start)
        mon.register_callback(TOOL_ID, E.PY_RETURN, self._on_return)
        mon.register_callback(TOOL_ID, E.PY_UNWIND, self._on_unwind)
        mon.set_events(TOOL_ID, E.LINE | E.PY_START | E.PY_RETURN | E.PY_UNWIND)
        self.active = True

    def stop(self) -> None:
        if not self.active:
            return
        mon.set_events(TOOL_ID, 0)
        for ev in (E.LINE, E.PY_START, E.PY_RETURN, E.PY_UNWIND):
            mon.register_callback(TOOL_ID, ev, None)
        mon.free_tool_id(TOOL_ID)
        self.active = False

    # -- helpers -----------------------------------------------------------
    def _info(self, code) -> _Info:
        info = self._info_cache.get(code)
        if info is None:
            try:
                fn = os.path.realpath(code.co_filename)
            except Exception:
                fn = code.co_filename
            in_scope = (fn, code.co_qualname) in self.scope_names
            info = _Info(in_scope, in_scope and fn == self.target_file_abs and code.co_qualname == self.target.function)
            self._info_cache[code] = info
        return info

    def _eval_condition(self, hit: dict, f_locals) -> None:
        loc = dict(f_locals)
        t = self.target
        try:
            if t.predicate is not None:
                hit["condition_value"] = bool(t.predicate(loc))
            elif t.cond_expr:
                hit["condition_value"] = bool(eval(t.cond_expr, {"__builtins__": _SAFE_BUILTINS}, loc))  # noqa: S307
        except Exception as e:  # not evaluable on these locals
            hit["condition_error"] = f"{type(e).__name__}: {e}"[:160]

    def _resolve(self, pend: _Pending, outcome: str) -> None:
        pend.hit["outcome"] = outcome

    # -- callbacks ---------------------------------------------------------
    def _on_start(self, code, offset):
        info = self._info(code)
        if not info.in_scope:
            return mon.DISABLE
        self.starts.append({"seq": fakes.next_seq(), "fn": code.co_qualname, "file": os.path.realpath(code.co_filename)})

    def _on_line(self, code, line):
        info = self._info(code)
        if not info.in_scope:
            return mon.DISABLE
        frame = sys._getframe(1)
        fid = id(frame)
        pend = self._pending.pop(fid, None)
        if pend is not None and pend.code is code:
            t = self.target
            if t.kind == "assert":
                self._resolve(pend, "true")
            elif t.kind in ("if", "while"):
                self._resolve(pend, "true" if t.body[0] <= line <= t.body[1] else "false")
        self.lines.setdefault(code.co_qualname, set()).add(line)
        if info.has_target and line == self.target.line:
            hit = {"seq": fakes.next_seq(), "outcome": None, "condition_value": None, "condition_error": None,
                   "locals": {}}
            f_locals = frame.f_locals
            self._eval_condition(hit, f_locals)
            for i, (k, v) in enumerate(f_locals.items()):
                if i >= 40:
                    break
                hit["locals"][k] = summarize(v)
            if len(self.hits) < 50:
                self.hits.append(hit)
            self._pending[fid] = _Pending(hit, code)

    def _on_return(self, code, offset, retval):
        info = self._info(code)
        if not info.in_scope:
            return mon.DISABLE
        pend = self._pending.pop(id(sys._getframe(1)), None)
        if pend is not None:
            self._resolve(pend, "true" if self.target.kind == "assert" else "false")

    def _on_unwind(self, code, offset, exc):
        # PY_UNWIND cannot be disabled per location (sys.monitoring raises ValueError), so
        # out-of-scope code simply returns.
        info = self._info(code)
        if not info.in_scope:
            return None
        frame = sys._getframe(1)
        pend = self._pending.pop(id(frame), None)
        if pend is not None:
            at_target = frame.f_lineno == self.target.line
            if at_target and self.target.kind == "assert" and isinstance(exc, AssertionError):
                self._resolve(pend, "false")
            else:
                self._resolve(pend, "error")

    # -- output ------------------------------------------------------------
    def result(self) -> dict[str, Any]:
        return {
            "target_hits": self.hits,
            "starts": self.starts,
            "lines": {k: sorted(v) for k, v in self.lines.items()},
        }
