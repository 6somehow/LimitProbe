"""Execution tracer built on sys.monitoring (PEP 669).

Two back-ends with identical output, chosen by make_tracer():
  * MonitoringTracer (sys.monitoring, Python >= 3.12) is the default;
  * SettraceTracer (sys.settrace) is the fallback for the Python 3.11 venv that holds the
    repository-pinned torch 2.4.0 / triton 3.0.0 (those wheels do not exist for 3.14).

Why sys.monitoring is preferred:
  * the main interpreter is 3.14, so sys.monitoring exists;
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
import collections
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from . import fakes

mon = getattr(sys, "monitoring", None)  # absent before Python 3.12
TOOL_ID = mon.PROFILER_ID if mon else None
E = mon.events if mon else None

_SAFE_BUILTINS = {n: getattr(builtins, n)
                  for n in ("len", "min", "max", "abs", "int", "float", "bool", "isinstance", "any", "all",
                            "sum", "range", "set", "tuple", "list", "dict", "str", "sorted", "round")}


class StopProbe(BaseException):
    """Raised by the tracer right after the target decision is known, in probe runs only
    (stop_after_target). Probe runs ask 'what does the target do for this input?' without
    running the code below it. They are never used for the verdict itself."""


def norm_qual(q: str) -> str:
    """co_qualname of a nested function is 'outer.<locals>.inner'; the Region says 'outer.inner'."""
    return q.replace(".<locals>", "")


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
    end_line: int = 0     # last line of the statement (assert) or of its header (if / while); 0 = same as line


def target_span(repo_root: Path, file: str, line: int) -> tuple[int, int]:
    """First and last line of the target: the whole statement for an assert or any simple statement, the header
    (up to the end of the condition) for if / while. A multi-line `assert (...)` raises on a line inside it."""
    tree = ast.parse((repo_root / file).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and node.lineno == line and not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if isinstance(node, (ast.If, ast.While)):
                return line, node.test.end_lineno
            return line, node.end_lineno
    return line, line


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


class _TracerBase:
    """Back-end independent bookkeeping. Subclasses call the handle_* methods."""

    def __init__(self, repo_root: Path, chain: list[ChainFn], target: TargetSpec,
                 stop_after_target: bool = False) -> None:
        self.repo_root = repo_root.resolve()
        self.chain = chain
        self.target = target
        self.stop_after_target = stop_after_target
        self.call_index = 0   # which driver call is running (preludes are calls 0..n-1, the checked call is last)
        self.scope_names = {(str((self.repo_root / c.file).resolve()), norm_qual(c.qualname)) for c in chain}
        self.target_file_abs = str((self.repo_root / target.file).resolve())
        self.scope_names.add((self.target_file_abs, norm_qual(target.function)))
        self.hits: list[dict] = []
        self.starts: list[dict] = []
        self.lines: dict[str, set[int]] = {}
        self._pending: dict[int, _Pending] = {}
        self._info_cache: dict[Any, _Info] = {}
        self.active = False

    def _info(self, code) -> _Info:
        info = self._info_cache.get(code)
        if info is None:
            try:
                fn = os.path.realpath(code.co_filename)
            except Exception:
                fn = code.co_filename
            qn = norm_qual(getattr(code, "co_qualname", code.co_name))  # co_qualname exists from 3.11
            in_scope = (fn, qn) in self.scope_names
            info = _Info(in_scope, in_scope and fn == self.target_file_abs and qn == norm_qual(self.target.function))
            self._info_cache[code] = info
        return info

    def _eval_condition(self, hit: dict, f_locals, f_globals=None) -> None:
        # names resolve in the frame's locals first, then in the module globals (a `global x` cache is read there)
        loc = collections.ChainMap(dict(f_locals), f_globals if f_globals is not None else {})
        t = self.target
        try:
            if t.predicate is not None:
                hit["condition_value"] = bool(t.predicate(dict(loc)))
            elif t.cond_expr:
                hit["condition_value"] = bool(eval(t.cond_expr, {"__builtins__": _SAFE_BUILTINS}, loc))  # noqa: S307
        except Exception as e:  # not evaluable on these locals
            hit["condition_error"] = f"{type(e).__name__}: {e}"[:160]

    def _resolve(self, pend: _Pending, outcome: str, may_stop: bool = True) -> None:
        pend.hit["outcome"] = outcome
        if self.stop_after_target and may_stop and outcome in ("true", "false"):
            raise StopProbe()

    # -- shared handlers (frame is the monitored frame) ---------------------
    def handle_start(self, code) -> None:
        self.starts.append({"seq": fakes.next_seq(), "fn": norm_qual(getattr(code, "co_qualname", code.co_name)),
                            "file": os.path.realpath(code.co_filename)})

    def _in_target_span(self, line: int) -> bool:
        t = self.target
        return t.line <= line <= max(t.end_line, t.line)

    def handle_line(self, code, frame, line: int) -> None:
        info = self._info(code)
        fid = id(frame)
        pend = self._pending.get(fid)
        if pend is not None and pend.code is code and self._in_target_span(line):
            # still evaluating the multi-line statement / condition: not the next statement yet
            self.lines.setdefault(norm_qual(getattr(code, "co_qualname", code.co_name)), set()).add(line)
            return
        pend = self._pending.pop(fid, None)
        if pend is not None and pend.code is code:
            t = self.target
            if t.kind == "assert":
                self._resolve(pend, "true")
            elif t.kind in ("if", "while"):
                self._resolve(pend, "true" if t.body[0] <= line <= t.body[1] else "false")
        self.lines.setdefault(norm_qual(getattr(code, "co_qualname", code.co_name)), set()).add(line)
        # The first LINE event inside the statement's span starts a hit. For a multi-line `assert (` or `if (` the
        # interpreter may report the first line of the condition instead of the keyword line (3.12+ does).
        if info.has_target and self._in_target_span(line):
            hit = {"seq": fakes.next_seq(), "outcome": None, "condition_value": None, "condition_error": None,
                   "locals": {}, "call": self.call_index}
            f_locals = frame.f_locals
            self._eval_condition(hit, f_locals, frame.f_globals)
            for i, (k, v) in enumerate(f_locals.items()):
                if i >= 40:
                    break
                hit["locals"][k] = summarize(v)
            if len(self.hits) < 50:
                self.hits.append(hit)
            self._pending[fid] = _Pending(hit, code)

    def handle_return(self, frame) -> None:
        pend = self._pending.pop(id(frame), None)
        if pend is not None:
            self._resolve(pend, "true" if self.target.kind == "assert" else "false")

    def handle_unwind(self, frame, exc) -> None:
        pend = self._pending.pop(id(frame), None)
        if pend is not None:
            at_target = self.target.line <= frame.f_lineno <= max(self.target.end_line, self.target.line)
            if at_target and self.target.kind == "assert" and isinstance(exc, AssertionError):
                self._resolve(pend, "false", may_stop=False)
            else:
                self._resolve(pend, "error", may_stop=False)

    # -- output ------------------------------------------------------------
    def result(self) -> dict[str, Any]:
        return {
            "target_hits": self.hits,
            "starts": self.starts,
            "lines": {k: sorted(v) for k, v in self.lines.items()},
        }


class MonitoringTracer(_TracerBase):
    """sys.monitoring back-end (Python >= 3.12)."""

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

    def _on_start(self, code, offset):
        if not self._info(code).in_scope:
            return mon.DISABLE
        self.handle_start(code)

    def _on_line(self, code, line):
        if not self._info(code).in_scope:
            return mon.DISABLE
        self.handle_line(code, sys._getframe(1), line)

    def _on_return(self, code, offset, retval):
        if not self._info(code).in_scope:
            return mon.DISABLE
        self.handle_return(sys._getframe(1))

    def _on_unwind(self, code, offset, exc):
        # PY_UNWIND cannot be disabled per location (sys.monitoring raises ValueError), so
        # out-of-scope code simply returns.
        if not self._info(code).in_scope:
            return None
        self.handle_unwind(sys._getframe(1), exc)


class SettraceTracer(_TracerBase):
    """sys.settrace back-end. The global trace function returns None for frames outside the
    call chain, so those frames get no line events."""

    def start(self) -> None:
        self._prev = sys.gettrace()
        sys.settrace(self._global)
        self.active = True

    def stop(self) -> None:
        if self.active:
            sys.settrace(self._prev)
            self.active = False

    def _global(self, frame, event, arg):
        code = frame.f_code
        if not self._info(code).in_scope:
            return None
        self.handle_start(code)
        return self._local

    def _local(self, frame, event, arg):
        if event == "line":
            self.handle_line(frame.f_code, frame, frame.f_lineno)
        elif event == "return":
            self.handle_return(frame)
        elif event == "exception":
            self.handle_unwind(frame, arg[1])
        return self._local


Tracer = MonitoringTracer if hasattr(sys, "monitoring") else None


def make_tracer(repo_root: Path, chain: list[ChainFn], target: TargetSpec,
                stop_after_target: bool = False) -> _TracerBase:
    force = os.environ.get("CHECKLIMITS_TRACER")  # "settrace" | "monitoring"; used by tests
    if force == "settrace" or not hasattr(sys, "monitoring"):
        return SettraceTracer(repo_root, chain, target, stop_after_target)
    return MonitoringTracer(repo_root, chain, target, stop_after_target)


