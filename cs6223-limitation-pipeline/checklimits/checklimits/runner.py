"""Run one case of an attempt in a subprocess and interpret the result.

Environment hygiene (KICKOFF constraints): the child never sees SOCLAAS_*, OPENAI_*,
ANTHROPIC_*, any *_proxy variable, or anything that looks like a key or token. It has a
hard timeout, runs in a scratch working directory, writes no bytecode, and sees no GPU.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

from .models import (PROJECT_ROOT, AttemptManifest, ExceptionInfo, MockDecl,
                     Observation, TargetHit)

_DROP = re.compile(r"(^SOCLAAS_|^OPENAI_|^ANTHROPIC_|_proxy$|^proxy$|API_KEY|SECRET|TOKEN|PASSWORD)", re.I)


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not _DROP.search(k)}
    env.update({
        "PYTHONPATH": str(PROJECT_ROOT),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "CUDA_VISIBLE_DEVICES": "",
        "OMP_NUM_THREADS": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    })
    env.update(extra or {})
    return env


def resolve_python(python: Optional[str]) -> str:
    if not python:
        return sys.executable
    p = Path(python)
    return str(p if p.is_absolute() else (PROJECT_ROOT / p))  # no resolve(): a venv python is a symlink


def run_cases(spec: dict[str, Any], cases: list[dict[str, Any]], timeout_s: int,
              env_extra: dict[str, str] | None = None, scratch_root: Path | None = None,
              python: Optional[str] = None) -> dict[str, dict[str, Any]]:
    """Run `cases` ([{"id", "inputs"}]) in ONE child process; returns {id: raw result}.

    A timeout or a hard crash of the child gives every case that has no result a
    status of "timeout" / "crash"."""
    scratch_root = scratch_root or (PROJECT_ROOT / "scratch")
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch_root, prefix="case_") as td:
        td_path = Path(td)
        spec = dict(spec, out=str(td_path / "result.json"), cases=cases)
        (td_path / "spec.json").write_text(json.dumps(spec))
        proc = subprocess.Popen(
            [resolve_python(python), "-m", "checklimits.child", str(td_path / "spec.json")],
            cwd=td, env=clean_env(env_extra), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True)
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
        out = td_path / "result.json"
        results = json.loads(out.read_text()) if out.exists() else {}
        for c in cases:
            raw = results.get(c["id"]) or {
                "status": "timeout" if timed_out else "crash", "exception": None, "returned": None,
                "trace": None, "mock_events": [], "wall_s": float(timeout_s) if timed_out else 0.0}
            raw["exit_code"] = proc.returncode
            raw["stdout"] = stdout[-2000:]
            raw["stderr"] = stderr[-2000:]
            results[c["id"]] = raw
        return results


def run_child(spec: dict[str, Any], timeout_s: int, env_extra: dict[str, str] | None = None,
              scratch_root: Path | None = None, python: Optional[str] = None) -> dict[str, Any]:
    """Single-case convenience wrapper around run_cases."""
    return run_cases(spec, [{"id": "main", "inputs": spec["inputs"]}], timeout_s, env_extra, scratch_root,
                     python)["main"]


def build_spec(manifest: AttemptManifest, attempt_dir: Path, pipeline_root: Path, region: Any,
               inputs: dict[str, Any], mocks: list[MockDecl], predicate_file: Optional[str],
               trace: bool, repo_dir: Optional[Path] = None, stop_after_target: bool = False) -> dict[str, Any]:
    return {
        "repo_dir": str((repo_dir or (pipeline_root / manifest.repo_dir)).resolve()),
        "stop_after_target": stop_after_target,
        "attempt_dir": str(attempt_dir.resolve()),
        "driver": manifest.driver,
        "driver_fn": manifest.driver_fn,
        "inputs": inputs,
        "trace": trace,
        "chain": list(region.call_chain),
        "target": {"file": region.location.file, "line": region.location.line_start,
                   "function": _qualname(region.location.function)},
        "cond_expr": None if predicate_file else region.condition.expr,
        "predicate_file": str((attempt_dir / predicate_file).resolve()) if predicate_file else None,
        "mocks": [m.model_dump(mode="json") for m in mocks],
    }


def _qualname(function: Optional[str]) -> str:
    return (function or "").partition("::")[2] or (function or "")


def _exc(raw_exc: Optional[dict]) -> Optional[ExceptionInfo]:
    return ExceptionInfo(**raw_exc) if raw_exc else None


def to_observation(raw: dict[str, Any], role: str, inputs: dict[str, Any], region: Any,
                   expected_exc_type: Optional[str]) -> Observation:
    """Interpret one raw result. Effect rule for outcome 'reject' (see PLAN/ENV notes):
    the effect is an exception raised AT Region.location. A run that passes the target line and
    fails later is 'no effect' and keeps the later exception in post_target_exception."""
    loc = f"{region.location.file}:{region.location.line_start}"
    exc = _exc(raw.get("exception"))
    trace = raw.get("trace")
    hits = [TargetHit(**h) for h in (trace or {}).get("target_hits", [])]
    reached = bool(hits)
    status = raw["status"]
    obs = Observation(role=role, inputs=inputs, status=status, exception=exc, target_reached=reached,
                      returned=raw.get("returned"),
                      target_hits=hits, stdout_tail=(raw.get("stdout") or "")[-300:], wall_s=raw.get("wall_s", 0.0))
    starts = (trace or {}).get("starts", [])
    if starts:
        first = starts[0]
        obs.entry_first_started = f"{first['file']}::{first['fn']}"
    if region.outcome != "reject":
        obs.effect = None
        obs.effect_note = f"outcome {region.outcome!r} not supported in P1"
    elif status in ("timeout", "crash", "load_error"):
        obs.effect = None
        obs.effect_note = f"run failed before a result: {status}"
    elif exc is not None and exc.raised_at == loc and (expected_exc_type is None or exc.type == expected_exc_type):
        obs.effect = True
        obs.effect_note = f"{exc.type} raised at target"
    elif reached:
        obs.effect = False
        if exc is not None:
            obs.post_target_exception = exc
            obs.effect_note = f"target passed; later {exc.type} at {exc.raised_at}"
        else:
            obs.effect_note = "target passed; run stopped by the probe" if status == "probe_stop" \
                else "target passed; run returned normally"
    elif exc is not None:
        obs.effect = None
        obs.effect_note = f"{exc.type} at {exc.raised_at} before the target was reached"
    else:
        obs.effect = False
        obs.effect_note = "run returned normally without reaching the target"
    if obs.effect:
        obs.observed_text = f"{exc.type} at {exc.raised_at}"
    elif obs.effect is False:
        obs.observed_text = f"no exception at {loc}"
        if exc is not None:
            obs.observed_text += f" (later {exc.type} at {exc.raised_at})"
    else:
        obs.observed_text = obs.effect_note
    return obs
