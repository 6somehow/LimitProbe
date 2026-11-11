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

from .models import (PROJECT_ROOT, AttemptManifest, scratch_root, ExceptionInfo, MockDecl,
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
              env_extra: dict[str, str] | None = None, scratch_root_arg: Path | None = None,
              python: Optional[str] = None) -> dict[str, dict[str, Any]]:
    """Run `cases` ([{"id", "inputs"}]) in ONE child process; returns {id: raw result}.

    A timeout or a hard crash of the child gives every case that has no result a
    status of "timeout" / "crash"."""
    root = scratch_root_arg or scratch_root()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root, prefix="case_") as td:
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
              scratch_root_arg: Path | None = None, python: Optional[str] = None) -> dict[str, Any]:
    """Single-case convenience wrapper around run_cases."""
    return run_cases(spec, [{"id": "main", "inputs": spec["inputs"], "prelude": spec.get("prelude") or []}], timeout_s, env_extra, scratch_root_arg,
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


EXCEPTION_OUTCOMES = ("reject",)
BRANCH_OUTCOMES = ("fallback", "mechanism_variant", "state_dependent")


def outcome_support(region: Any, repo_root: Path) -> tuple[bool, str]:
    """Can the harness judge Region.outcome at Region.location? (effect families, SCORECARD 3.5)

      reject                                         an exception raised at the location
      fallback, mechanism_variant, state_dependent   the branch decision at the location is taken
                                                     (state_dependent: the checked call comes after prelude calls)
    Branch effects need the target to be an `if` / `while` statement: the tracer sees which way it went.
    Anything else (an assignment, a call, an assert for a non-reject outcome) is not judged."""
    from .tracer import classify_target
    o = region.outcome
    if o in EXCEPTION_OUTCOMES:
        return True, ""
    if o in BRANCH_OUTCOMES:
        kind, _ = classify_target(repo_root, region.location.file, region.location.line_start)
        if kind in ("if", "while"):
            return True, ""
        return False, (f"outcome {o!r} is judged from a branch decision, but the target is a {kind!r} statement "
                       f"at {region.location.file}:{region.location.line_start}")
    return False, f"outcome {o!r} has no effect check yet"


def to_observation(raw: dict[str, Any], role: str, inputs: dict[str, Any], region: Any,
                   expected_exc_type: Optional[str]) -> Observation:
    """Interpret one raw result.

    reject: the effect is an exception raised AT Region.location. A run that passes the target line and fails
    later is 'no effect' and keeps the later exception in post_target_exception.
    fallback / mechanism_variant / state_dependent: the effect is that the branch decision at the location was
    taken ("true"). Only hits of the checked (last) call count; earlier calls are preludes."""
    loc = f"{region.location.file}:{region.location.line_start}"
    exc = _exc(raw.get("exception"))
    trace = raw.get("trace")
    final_call = raw.get("final_call", 0)
    hits = [TargetHit(**h) for h in (trace or {}).get("target_hits", []) if h.get("call", 0) == final_call]
    reached = bool(hits)
    status = raw["status"]
    obs = Observation(role=role, inputs=inputs, status=status, exception=exc, target_reached=reached,
                      returned=raw.get("returned"), target_kind=raw.get("target_kind"),
                      target_hits=hits, stdout_tail=(raw.get("stdout") or "")[-300:], wall_s=raw.get("wall_s", 0.0))
    starts = (trace or {}).get("starts", [])
    if starts:
        first = starts[0]
        obs.entry_first_started = f"{first['file']}::{first['fn']}"
    family = "exception" if region.outcome in EXCEPTION_OUTCOMES else "branch" if region.outcome in BRANCH_OUTCOMES else None
    if family is None:
        obs.effect = None
        obs.effect_note = f"outcome {region.outcome!r} has no effect check yet"
    elif status in ("timeout", "crash", "load_error"):
        obs.effect = None
        obs.effect_note = f"run failed before a result: {status}"
    elif raw.get("prelude_failed") is not None:
        obs.effect = None
        obs.effect_note = f"prelude call {raw['prelude_failed']} failed: {exc.type if exc else '?'} at {exc.raised_at if exc else '?'}"
    elif family == "branch":
        _branch_effect(obs, hits, exc, status, loc, raw.get("target_kind"))
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
    if family == "branch" and obs.effect is not None:
        obs.observed_text = f"branch {'taken' if obs.effect else 'not taken'} at {loc}"
        if obs.post_target_exception is not None:
            obs.observed_text += f" (later {obs.post_target_exception.type} at {obs.post_target_exception.raised_at})"
    elif obs.effect:
        obs.observed_text = f"{exc.type} at {exc.raised_at}"
    elif obs.effect is False:
        obs.observed_text = f"no exception at {loc}"
        if exc is not None:
            obs.observed_text += f" (later {exc.type} at {exc.raised_at})"
    else:
        obs.observed_text = obs.effect_note
    return obs


def _branch_effect(obs: Observation, hits: list, exc: Optional[ExceptionInfo], status: str, loc: str,
                   kind: Optional[str]) -> None:
    if kind not in ("if", "while"):
        obs.effect, obs.effect_note = None, f"target is a {kind!r} statement, not a branch decision"
        return
    if not hits:
        if exc is not None:
            obs.effect, obs.effect_note = None, f"{exc.type} at {exc.raised_at} before the target was reached"
        else:
            obs.effect, obs.effect_note = False, "run returned normally without reaching the target"
        return
    decided = [h for h in hits if h.outcome in ("true", "false")]
    if not decided:
        obs.effect, obs.effect_note = None, "the branch decision was not resolved (error while evaluating the condition?)"
        return
    obs.effect = any(h.outcome == "true" for h in decided)
    obs.effect_note = "branch taken" if obs.effect else "branch not taken"
    if exc is not None and status != "probe_stop":
        obs.post_target_exception = exc
        obs.effect_note += f"; later {exc.type} at {exc.raised_at}"
