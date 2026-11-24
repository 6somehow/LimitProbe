"""Recording stand-ins (SCORECARD "mock must be observable").

Every access to a stand-in (attribute read, call, item read, iteration) gets a sequence
number from one process-wide counter. The tracer takes its sequence number from the same
counter when the target line runs, so "was this mock touched before the target?" is
computed from the records, never declared by the agent.

Mock kinds (see models.MockDecl):
  fake_module  sys.modules[symbol] = RecordingModule (installed before any repo import)
  patch        module attribute replaced by a RecordingFake after the module is imported
  env_var      environment variable set; recorded as one access at install time

Behaviors (closed vocabulary): return_first_arg, return_none, record_only (returns a child fake),
sim (a patch that runs a real implementation from the attempt directory, recorded like any fake).
Limit: a RecordingModule has no real __spec__ or version, so libraries that probe it at
import time (e.g. transformers probing triton) may fail. Use `patch` for those cases.
"""
from __future__ import annotations

import importlib
import importlib.util
import itertools
import os
import sys
import types
from pathlib import Path
from typing import Any

_counter = itertools.count(1)


def next_seq() -> int:
    """Process-wide, strictly increasing sequence number."""
    return next(_counter)


class Recorder:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, symbol: str, op: str, name: str = "") -> int:
        seq = next_seq()
        self.events.append({"seq": seq, "symbol": symbol, "op": op, "name": name})
        return seq

    def accesses(self, root_symbol: str) -> list[dict[str, Any]]:
        """Events whose symbol is root_symbol or a descendant of it."""
        return [e for e in self.events
                if e["symbol"] == root_symbol or e["symbol"].startswith(root_symbol + ".")]


class RecordingFake:
    """Proxy that records everything done to it."""

    def __init__(self, symbol: str, recorder: Recorder, behavior: str = "return_first_arg",
                 root: str | None = None) -> None:
        object.__setattr__(self, "_symbol", symbol)
        object.__setattr__(self, "_rec", recorder)
        object.__setattr__(self, "_behavior", behavior)
        object.__setattr__(self, "_root", root or symbol)

    def _child(self, name: str) -> "RecordingFake":
        return RecordingFake(f"{self._symbol}.{name}", self._rec, "record_only", self._root)

    def __getattr__(self, name: str):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)  # keep inspect / copy / pickle probes quiet and unrecorded
        self._rec.record(self._symbol, "getattr", name)
        return self._child(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._rec.record(self._symbol, "setattr", name)

    def __call__(self, *args: Any, **kwargs: Any):
        self._rec.record(self._symbol, "call")
        if self._behavior == "return_first_arg" and args:
            return args[0]
        if self._behavior == "return_none":
            return None
        return self._child("<return>")

    def __getitem__(self, item: Any):
        self._rec.record(self._symbol, "getitem", repr(item)[:40])
        return self._child("[]")

    def __iter__(self):
        self._rec.record(self._symbol, "iter")
        return iter(())

    def __bool__(self) -> bool:
        return True

    def __enter__(self):
        self._rec.record(self._symbol, "enter")
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def __repr__(self) -> str:
        return f"<RecordingFake {self._symbol}>"


class RecordingModule(types.ModuleType):
    def __init__(self, name: str, recorder: Recorder, behavior: str) -> None:
        super().__init__(name)
        self.__dict__["_rec"] = recorder
        self.__dict__["_behavior"] = behavior
        self.__path__ = []  # lets `import name.sub` resolve through sys.modules

    def __getattr__(self, name: str):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        sub = sys.modules.get(f"{self.__name__}.{name}")
        if sub is not None:
            self._rec.record(self.__name__, "getattr", name)
            return sub
        self._rec.record(self.__name__, "getattr", name)
        return RecordingFake(f"{self.__name__}.{name}", self._rec, self._behavior, self.__name__)


def install_import_time(decls: list[Any], recorder: Recorder) -> None:
    """fake_module and env_var mocks. Must run before the repository is imported."""
    for d in decls:
        if d.kind == "fake_module":
            sys.modules[d.symbol] = RecordingModule(d.symbol, recorder, d.behavior)
        elif d.kind == "env_var":
            os.environ[d.symbol] = d.value or ""
            recorder.record(d.symbol, "setenv", d.value or "")


def _resolve(symbol: str) -> tuple[Any, str]:
    """Split 'pkg.mod.attr' into (imported module, attr)."""
    parts = symbol.split(".")
    for i in range(len(parts) - 1, 0, -1):
        modname = ".".join(parts[:i])
        try:
            mod = importlib.import_module(modname)
        except ImportError:
            continue
        obj = mod
        for p in parts[i:-1]:
            obj = getattr(obj, p)
        return obj, parts[-1]
    raise ImportError(f"cannot resolve {symbol}")


class RecordingCallable:
    """Runs `fn`, recording every call with a sequence number (behavior "sim")."""

    def __init__(self, symbol: str, recorder: Recorder, fn: Any) -> None:
        self._symbol, self._rec, self._fn = symbol, recorder, fn
        self.__name__ = getattr(fn, "__name__", symbol)

    def __call__(self, *args: Any, **kwargs: Any):
        self._rec.record(self._symbol, "call")
        return self._fn(*args, **kwargs)


def load_impl(impl: str, attempt_dir: Path) -> Any:
    file, _, func = impl.partition("::")
    spec = importlib.util.spec_from_file_location(f"_checklimits_sim_{Path(file).stem}", attempt_dir / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, func)


def install_patches(decls: list[Any], recorder: Recorder, attempt_dir: Path | None = None) -> None:
    for d in decls:
        if d.kind == "patch":
            owner, attr = _resolve(d.symbol)
            if d.behavior == "sim":
                if not d.impl or attempt_dir is None:
                    raise ValueError(f"mock {d.symbol}: behavior 'sim' needs impl and an attempt directory")
                setattr(owner, attr, RecordingCallable(d.symbol, recorder, load_impl(d.impl, attempt_dir)))
            else:
                setattr(owner, attr, RecordingFake(d.symbol, recorder, d.behavior))
