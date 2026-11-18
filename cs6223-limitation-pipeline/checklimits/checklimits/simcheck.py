"""Is a stand-in for accelerator code faithful? Numeric and symbolic cross-checks, run by the harness (CONFIDENCE_SPEC.md §23).

A code agent may replace a GPU-only call (a CUDA or Triton kernel, a hardware block) with a CPU stand-in written in
`sim.py`. A stand-in is a claim: "on small inputs this computes what the kernel computes". The agent declares how the
claim is checked: `MockDecl.sim_check = "file::function"`. The function receives the stand-in and returns
{"ok": bool, "detail": str, "kind": "numeric" | "symbolic"}. It may compare the stand-in with a reference that runs on
CPU (the repository's own, or a closed form), test invariants on random small inputs, or prove an identity of the
formula with sympy or z3.

The agent writes the check, so the harness does not trust it blindly. It runs the check on the stand-in (must be ok)
and again on corrupted copies of the stand-in: outputs scaled, negated, zeroed. A check that still passes on a corrupted
stand-in cannot see errors and is reported `vacuous`.

Statuses: agrees | disagrees | vacuous | error. Only `disagrees` changes a level (D6 refuted). `agrees` is recorded as
evidence; the stand-in's class (repo_reference / independent_native / stub) still sets the evidence state.

Run as `python -m checklimits.simcheck <spec.json>`; the parent (`run_sim_checks`) starts it in a clean environment.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Optional

CORRUPTIONS = ("scale", "negate", "zero")
TIMEOUT_S = 120


# --------------------------------------------------------------------------- child side
def _corrupt_value(x: Any, mode: str) -> Any:
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return {"scale": x * 1.1 + 0.01, "negate": -x, "zero": 0 * x}[mode]
    if isinstance(x, (list, tuple)):
        return type(x)(_corrupt_value(i, mode) for i in x)
    if isinstance(x, dict):
        return {k: _corrupt_value(v, mode) for k, v in x.items()}
    dtype = getattr(x, "dtype", None)
    if dtype is not None and hasattr(x, "shape"):
        kind = getattr(dtype, "kind", None)
        if kind is None:                                   # torch dtype
            floating = bool(getattr(dtype, "is_floating_point", False))
        else:
            floating = kind == "f"
        if not floating:
            return x
        return {"scale": x * 1.1 + 0.01, "negate": -x, "zero": x * 0}[mode]
    return x


def corrupt(fn: Any, mode: str):
    def wrapped(*a, **k):
        return _corrupt_value(fn(*a, **k), mode)
    return wrapped


def _run_one(decl: dict[str, Any], attempt: Path) -> dict[str, Any]:
    import importlib.util
    from . import fakes
    out: dict[str, Any] = {"status": "error", "detail": "", "kind": None, "corrupted_passed": []}
    try:
        impl = fakes.load_impl(decl["impl"], attempt)
        file, _, func = decl["sim_check"].partition("::")
        spec = importlib.util.spec_from_file_location("_checklimits_simcheck_" + Path(file).stem, attempt / file)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        check = getattr(mod, func)
        res = check(impl)
        if not isinstance(res, dict) or "ok" not in res:
            out["detail"] = "the check must return a dict with an 'ok' field"
            return out
        out["kind"] = res.get("kind")
        out["detail"] = str(res.get("detail", ""))[:300]
        if not res["ok"]:
            out["status"] = "disagrees"
            return out
        for mode in CORRUPTIONS:
            try:
                bad = check(corrupt(impl, mode))
                if isinstance(bad, dict) and bad.get("ok"):
                    out["corrupted_passed"].append(mode)
            except Exception:
                pass                                       # a check that raises on a corrupted stand-in saw the error
        out["status"] = "vacuous" if out["corrupted_passed"] else "agrees"
    except BaseException as e:  # noqa: BLE001
        out["detail"] = f"{type(e).__name__}: {str(e)[:200]}"
        out["trace"] = traceback.format_exc()[-600:]
    return out


def main(argv: list[str]) -> int:
    spec = json.loads(Path(argv[1]).read_text())
    repo, attempt = Path(spec["repo_dir"]).resolve(), Path(spec["attempt_dir"]).resolve()
    sys.path.insert(0, str(repo))
    sys.path.insert(1, str(attempt))
    sys.dont_write_bytecode = True
    res = {}
    for d in spec["decls"]:
        t0 = time.monotonic()
        res[d["symbol"]] = _run_one(d, attempt)
        res[d["symbol"]]["wall_s"] = round(time.monotonic() - t0, 2)
    Path(spec["out"]).write_text(json.dumps(res))
    return 0


# --------------------------------------------------------------------------- parent side
def run_sim_checks(decls: list[Any], attempt_dir: Path, repo_dir: Path, python: Optional[str] = None,
                   timeout_s: int = TIMEOUT_S, scratch: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    """{symbol: result} for every `sim` mock that declares a sim_check. Mocks without one are not in the result."""
    from .models import scratch_root
    from .runner import clean_env, resolve_python
    todo = [d for d in decls if getattr(d, "behavior", None) == "sim" and getattr(d, "sim_check", None) and d.impl]
    if not todo:
        return {}
    root = scratch or scratch_root()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root, prefix="simcheck_") as td:
        tdp = Path(td)
        spec = {"repo_dir": str(repo_dir), "attempt_dir": str(attempt_dir), "out": str(tdp / "out.json"),
                "decls": [{"symbol": d.symbol, "impl": d.impl, "sim_check": d.sim_check} for d in todo]}
        (tdp / "spec.json").write_text(json.dumps(spec))
        try:
            subprocess.run([resolve_python(python), "-m", "checklimits.simcheck", str(tdp / "spec.json")], cwd=td,
                           env=clean_env(None), capture_output=True, text=True, timeout=timeout_s * len(todo))
        except subprocess.TimeoutExpired:
            return {d.symbol: {"status": "error", "detail": "the sim check timed out"} for d in todo}
        p = tdp / "out.json"
        res = json.loads(p.read_text()) if p.exists() else {}
    return {d.symbol: res.get(d.symbol) or {"status": "error", "detail": "the sim check child produced no result"}
            for d in todo}


if __name__ == "__main__":
    sys.exit(main(sys.argv))
