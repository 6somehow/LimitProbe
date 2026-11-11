"""Child process: runs attempt cases and writes a JSON result.

Started by runner.py as `python -m checklimits.child <spec.json>`. The parent supplies a
cleaned environment (no SOCLAAS_*, proxy or OpenAI variables) and a timeout.

Order of work: install import-time mocks -> import modules that need patching -> install
patches -> load the attempt's driver -> for each case: start a fresh tracer (unless
trace=false), call driver.run(inputs), stop the tracer -> write the results.

spec["cases"] is a list of {"id", "inputs", "prelude"?}; "prelude" is a list of input dicts for earlier driver
calls in the same process (state-dependent findings); only the last call is the checked one. One process runs them in order, so the expensive
imports (torch, ...) happen once. With spec["stop_after_target"] the tracer stops each case
right after the target decision (probe runs; see tracer.StopProbe).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True  # never write __pycache__ into third_party/


def _frame_str(fs: traceback.FrameSummary, repo: Path) -> str:
    p = Path(os.path.realpath(fs.filename))
    try:
        return f"{p.relative_to(repo)}:{fs.lineno}"
    except ValueError:
        parts = p.parts[-3:]
        return f"{'/'.join(parts)}:{fs.lineno}"


def _exc_info(e: BaseException, repo: Path) -> dict:
    frames = [_frame_str(f, repo) for f in traceback.extract_tb(e.__traceback__)]
    return {
        "type": type(e).__name__,
        "message": str(e)[:300],
        "raised_at": frames[-1] if frames else None,
        "frames": frames[-12:],
    }


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str]) -> int:
    spec = json.loads(Path(argv[1]).read_text())
    repo = Path(spec["repo_dir"]).resolve()
    attempt = Path(spec["attempt_dir"]).resolve()
    out = Path(spec["out"])
    sys.path.insert(0, str(repo))
    sys.path.insert(1, str(attempt))

    from . import fakes
    from .models import MockDecl
    from .tracer import StopProbe, TargetSpec, classify_target, make_tracer, parse_chain, summarize

    cases = spec.get("cases") or [{"id": "main", "inputs": spec["inputs"]}]
    results: dict[str, dict] = {}
    recorder = fakes.Recorder()
    t_setup = time.monotonic()
    try:
        decls = [MockDecl.model_validate(m) for m in spec.get("mocks", [])]
        fakes.install_import_time(decls, recorder)
        fakes.install_patches(decls, recorder, attempt)
        predicate = None
        if spec.get("predicate_file"):
            predicate = _load_module(Path(spec["predicate_file"]), "_checklimits_predicate").predicate
        driver = _load_module(attempt / spec["driver"], "_checklimits_driver")
        run = getattr(driver, spec["driver_fn"])
        t = spec["target"]
        kind, body = classify_target(repo, t["file"], t["line"])
        target = TargetSpec(t["file"], t["line"], t["function"], kind, body, spec.get("cond_expr"), predicate)
    except BaseException as e:  # noqa: BLE001
        err = {"status": "load_error", "exception": _exc_info(e, repo), "returned": None, "trace": None,
               "mock_events": [], "wall_s": round(time.monotonic() - t_setup, 3)}
        out.write_text(json.dumps({c["id"]: err for c in cases}))
        return 0

    # Accesses made while the repository and the driver were imported happen before any target hit;
    # every case keeps them, only the events of earlier cases are dropped.
    setup_events = list(recorder.events)
    for c in cases:
        recorder.events = list(setup_events)
        res: dict = {"status": "ok", "exception": None, "returned": None, "trace": None}
        tracer = None
        if spec.get("trace", True):
            tracer = make_tracer(repo, parse_chain(spec["chain"]), target, False)
        t0 = time.monotonic()
        prelude = c.get("prelude") or []
        res["final_call"] = len(prelude)
        res["target_kind"] = target.kind
        try:
            if tracer:
                tracer.start()
                tracer.stop_after_target = False
            for i, pin in enumerate(prelude):      # earlier calls that leave the state the checked call depends on
                if tracer:
                    tracer.call_index = i
                try:
                    run(pin)
                except StopProbe:
                    raise
                except BaseException:
                    res["prelude_failed"] = i
                    raise
            if tracer:
                tracer.call_index = len(prelude)
                tracer.stop_after_target = bool(spec.get("stop_after_target"))
            res["returned"] = summarize(run(c["inputs"]))
        except StopProbe:
            res["status"] = "probe_stop"
        except BaseException as e:  # noqa: BLE001  (SystemExit and KeyboardInterrupt are results too)
            res["status"] = "exception"
            res["exception"] = _exc_info(e, repo)
        finally:
            if tracer:
                tracer.stop()
        res["wall_s"] = round(time.monotonic() - t0, 3)
        if tracer:
            res["trace"] = tracer.result()
            for s in res["trace"]["starts"]:  # repo-relative, comparable in the parent
                try:
                    s["file"] = str(Path(s["file"]).relative_to(repo))
                except ValueError:
                    pass
        res["mock_events"] = recorder.events
        results[c["id"]] = res
    out.write_text(json.dumps(results, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
