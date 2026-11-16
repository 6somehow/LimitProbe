"""Run the code agent (opencode) on one finding and close the loop with the harness (PLAN.md P2).

Trust model. The agent is an LLM that may be sloppy or may try to raise its own score, but it is not
assumed to attack the sandbox. What is enforced:

  * Credentials. The real SoCLaaS key exists only in the relay process. The agent's environment holds
    a placeholder key; the credential directories are hidden by bwrap (tmpfs over them).
  * Writes. bwrap mounts the whole file system read-only except the run directory, so the agent cannot
    edit the repository, the harness, the data or other attempts (opencode's own permissions are only
    advisory: python in a shell bypasses them).
  * Network. Not blocked (no root, so no firewall). The agent has no secret to leak; the first run of
    a fresh opencode HOME downloads its provider package, later runs start from a warmed HOME copy
    with npm in offline mode.
  * Scores. The harness recomputes every claim; the verdict and the level are computed outside the
    sandbox from the attempt package the agent leaves behind.
  * Oracle registration. Locks live in the run directory; the loop keeps its own copy outside the
    sandbox and checks that the agent's lock only grew (history preserved).

Budgets (wide by decision): wall time, tool calls and tokens per session.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .harness import RunOptions, lock_is_extension, run_attempt, write_outputs
from .models import PIPELINE_ROOT, PROJECT_ROOT

OPENCODE = PROJECT_ROOT / "scratch" / "opencode" / "node_modules" / "opencode-linux-x64" / "bin" / "opencode"
OC_CONFIG = PROJECT_ROOT / "agent" / "opencode.jsonc"
INSTRUCTIONS = PROJECT_ROOT / "agent" / "INSTRUCTIONS.md"
CL = PROJECT_ROOT / "agent" / "cl"
HOME_TEMPLATE = PROJECT_ROOT / "scratch" / "oc_home_template"
RUNS = PROJECT_ROOT / "scratch" / "agent_runs"
HIDE_DIRS = [Path.home() / d for d in ("LLM_API_KEY", ".ssh", ".aws", ".gnupg", ".kiro", ".config/gcloud")]
RELAY = "http://127.0.0.1:8787/v1"
LEVEL_RANK = {"n/a": -2, "invalid": -1, "L0": 0, "L1": 1, "L2": 2, "L3": 3}


@dataclass
class Budget:
    wall_s: int = 1800          # per agent session
    tool_calls: int = 250
    tokens: int = 4_000_000
    sessions: int = 2           # outer iterations: first session + feedback sessions
    blind: bool = False         # hide the harness source and the rule documents (S5b)


@dataclass
class SessionStats:
    wall_s: float = 0.0
    tool_calls: int = 0
    llm_steps: int = 0
    tokens: int = 0
    stopped_by: str = "finished"
    final_text: str = ""
    session_id: Optional[str] = None
    exit_code: Optional[int] = None


# Reference solutions and everything that gives them away are hidden from the agent: the hand-written
# attempts, all earlier results and benchmark runs, the tests, the notes about how the pilot was solved,
# and the git history (which contains all of those). The first agent run found and copied the hand-written
# F07 driver, so its result was thrown away (scratch/agent_runs/INVALID-*).
# agent_results/ (archived attempts of earlier agent runs, for 4 FlexPrefill Findings of the very same Finding) and the
# result write-ups were readable until 2026-11-16: an agent could copy an earlier solution. From that date they are hidden.
HIDE_PATHS_DIRS = [PROJECT_ROOT / d for d in ("attempts", "results", "locks", "runs", "tests", "scripts", "scratch",
                                              "agent_results")] + \
                  [PIPELINE_ROOT.parent / ".git"]     # PIPELINE_ROOT/results stays visible: it holds the step 4 inputs
HIDE_PATHS_FILES = [PROJECT_ROOT / f for f in ("PLAN.md", "KICKOFF_PROMPT.md", "ENV.md", "scoring_prototype.py",
                                               "AGENT_RESULTS.md", "BATCH_RESULTS.md", "NNSMITH_RESULTS.md",
                                               "PREFLIGHT_FLEXPOSIT.md")]
# blind mode: the agent is not told how each defeater is computed. The harness is not in its sandbox at all (the package
# directory is an empty tmpfs, the rule documents are hidden); `cl` there talks to a service outside, which runs the real
# command and returns the output (agent_service.py). The agent keeps the skill (agent/INSTRUCTIONS.md), the task text and
# whatever `cl lint` / `cl run` print.
# interpreters for the code under test (scratch/venv*, built by scripts/make_venv_*.sh or `provision`) and the agent runtime
SCRATCH_KEEP_RO = sorted({d.name for d in (PROJECT_ROOT / "scratch").glob("venv*")} | {"opencode"}) \
    if (PROJECT_ROOT / "scratch").is_dir() else ["opencode"]
BLIND_HIDE_FILES = [PROJECT_ROOT / f for f in ("CONFIDENCE_SPEC.md", "SCORECARD.md", "CONTRACT_TEST_REPORT.md",
                                               "REQUESTS_TO_STEP4.md", "EXPERIMENTS.md", "S4B_OTHER_EFFECTS.md")]


def sandbox_cmd(run_dir: Path, inner: list[str], blind: bool = False) -> list[str]:
    """bwrap command line. blind=True: no harness source and no rule documents in the sandbox, `cl` goes through the service."""
    cmd = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
    for d in HIDE_DIRS + HIDE_PATHS_DIRS:
        if d.is_dir():
            cmd += ["--tmpfs", str(d)]
    for f in HIDE_PATHS_FILES:
        if f.is_file():
            cmd += ["--ro-bind", "/dev/null", str(f)]
    for k in SCRATCH_KEEP_RO:          # re-expose what the agent needs inside the emptied scratch/
        if (PROJECT_ROOT / "scratch" / k).exists():
            cmd += ["--ro-bind", str(PROJECT_ROOT / "scratch" / k), str(PROJECT_ROOT / "scratch" / k)]
    if blind:
        from .agent_service import service_dir
        for f in BLIND_HIDE_FILES:
            if f.is_file():
                cmd += ["--ro-bind", "/dev/null", str(f)]
        cmd += ["--tmpfs", str(PROJECT_ROOT / "checklimits"), "--bind", str(service_dir(run_dir)), "/tmp/cl"]
    cmd += ["--bind", str(run_dir), str(run_dir), "--chdir", str(PIPELINE_ROOT), "--unshare-pid", "--die-with-parent"]
    return cmd + inner


def agent_env(run_dir: Path, blind: bool = False) -> dict[str, str]:
    home = run_dir / "home"
    return {**({"CL_SOCKET": "/tmp/cl/sock"} if blind else {}),
        "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(home), "LANG": "C.UTF-8", "TERM": "dumb",
        "XDG_CONFIG_HOME": str(home / ".config"), "XDG_DATA_HOME": str(home / ".local/share"),
        "XDG_CACHE_HOME": str(home / ".cache"), "XDG_STATE_HOME": str(home / ".local/state"),
        "OPENCODE_CONFIG": str(OC_CONFIG), "OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_DISABLE_MODELS_FETCH": "1",
        "OPENCODE_DISABLE_LSP_DOWNLOAD": "1", "OPENCODE_DISABLE_CLAUDE_CODE": "1", "OPENCODE_DISABLE_EXTERNAL_SKILLS": "1",
        "npm_config_offline": "true", "PYTHONDONTWRITEBYTECODE": "1",
        "CHECKLIMITS_SCRATCH": str(run_dir / "tmp"), "CHECKLIMITS_LOCKS_DIR": str(run_dir / "locks"),
    }


def build_prompt(finding: str, run_dir: Path, feedback: Optional[str] = None,
                 findings_file: Optional[str] = None, data_dir: Optional[str] = None) -> str:
    attempt = run_dir / "workspace" / "attempt"
    out = run_dir / "out"
    if feedback:
        return (f"Continue working on finding {finding}. The harness re-ran your attempt outside your sandbox. "
                f"Result:\n\n{feedback}\n\nFix the causes (never the report) and run the full check again with "
                f"`{CL} run --attempt {attempt} --out {out}`. Stop when the level is L3 or nothing more can be fixed by you. "
                "Finish with a short summary.")
    return (INSTRUCTIONS.read_text() + f"\n\n---\n\n# Your assignment\n\nVerify finding **{finding}**.\n\n"
            f"* `CL` = `{CL}` (use this exact path).\n* Your attempt directory: `{attempt}` (create it with `init`).\n"
            f"* Output directory for reports: `{out}`.\n* Everything else on disk is read-only.\n"
            + (f"* Input source: the step 4 hand-off. Pass `--findings-file {findings_file}"
               + (f" --data-dir {data_dir}" if data_dir and data_dir != "data/pilot_flexprefill" else "")
               + "` to `task` and `init`.\n" if findings_file else "")
            + f"Start with `{CL} task {finding}" + (f" --findings-file {findings_file}" if findings_file else "")
            + (f" --data-dir {data_dir}" if findings_file and data_dir and data_dir != "data/pilot_flexprefill" else "") + "`.")


def _kill(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_session(run_dir: Path, prompt: str, budget: Budget, session_id: Optional[str], log_name: str,
                model: str = "relay/x-test-2") -> SessionStats:
    """One opencode session inside the sandbox; events are parsed as they stream and budgets enforced."""
    inner = [str(OPENCODE), "run", "--format", "json", "--model", model, "--dir", str(PIPELINE_ROOT)]
    if session_id:
        inner += ["--session", session_id]
    inner.append(prompt)
    st = SessionStats(session_id=session_id)
    t0 = time.monotonic()
    log = (run_dir / log_name).open("w")
    proc = subprocess.Popen(sandbox_cmd(run_dir, inner, budget.blind), env=agent_env(run_dir, budget.blind), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            log.write(line)
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            st.session_id = ev.get("sessionID") or st.session_id
            part = ev.get("part") or {}
            if ev.get("type") == "tool_use" and part.get("state", {}).get("status") in ("completed", "error"):
                st.tool_calls += 1
            elif ev.get("type") == "step_finish":
                st.llm_steps += 1
                st.tokens += int((part.get("tokens") or {}).get("total") or 0)
            elif ev.get("type") == "text":
                st.final_text = part.get("text", "")
            if time.monotonic() - t0 > budget.wall_s:
                st.stopped_by = "wall_time"
            elif st.tool_calls > budget.tool_calls:
                st.stopped_by = "tool_calls"
            elif st.tokens > budget.tokens:
                st.stopped_by = "tokens"
            if st.stopped_by != "finished":
                _kill(proc)
                break
        proc.wait(timeout=30)
    except Exception:
        st.stopped_by = st.stopped_by if st.stopped_by != "finished" else "error"
        _kill(proc)
    finally:
        log.close()
    st.wall_s = round(time.monotonic() - t0, 1)
    st.exit_code = proc.returncode
    return st


def prepare_run(finding: str, run_id: str) -> Path:
    run_dir = RUNS / run_id
    if run_dir.exists():
        raise SystemExit(f"{run_dir} exists; pick a new run id")
    for d in ("workspace", "out", "tmp", "locks"):
        (run_dir / d).mkdir(parents=True)
    if HOME_TEMPLATE.exists():
        shutil.copytree(HOME_TEMPLATE, run_dir / "home")
    else:
        (run_dir / "home").mkdir()
    return run_dir


def feedback_text(report) -> str:
    c = report.confidence
    lines = [f"verdict={report.verdict} final_verdict={report.final_verdict} level={c.level} (uncalibrated)",
             f"form_integrity={report.audit.rate}", "defeaters: " + ", ".join(f"{d.id}={d.status}" for d in c.defeaters)]
    if c.level_note:
        lines.append("note: " + c.level_note)
    if c.next_steps:
        lines.append("next_steps:")
        lines += [f"  - {s}" for s in c.next_steps]
    return "\n".join(lines)


def authoritative_run(run_dir: Path, options: RunOptions) -> dict[str, Any]:
    """Run the harness on the agent's package outside the sandbox. Returns the report and tamper flags."""
    attempt = run_dir / "workspace" / "attempt"
    locks = run_dir / "locks"
    res = run_attempt(attempt, options=options, locks_dir=locks)
    r = res["report"]
    lock_file = locks / r.artifact_id / f"{r.test_id}.json"
    new_lock = json.loads(lock_file.read_text()) if lock_file.exists() else None
    saved = run_dir.parent / f"{run_dir.name}.lock.saved.json"      # outside the sandbox's writable area
    tamper = False
    if saved.exists():
        tamper = not lock_is_extension(json.loads(saved.read_text()), new_lock)
    if new_lock is not None:
        saved.write_text(json.dumps(new_lock))
    write_outputs(res, run_dir / "final")
    return {"report": r, "result": res, "lock_tampered": tamper}


def run_agent(finding: str, run_id: str, budget: Budget = Budget(), options: Optional[RunOptions] = None,
              target_level: str = "L3", findings_file: Optional[str] = None,
              data_dir: Optional[str] = None) -> dict[str, Any]:
    run_dir = prepare_run(finding, run_id)
    svc = None
    if budget.blind:                       # the harness runs outside the agent's sandbox, for the agent (agent_service.py)
        from .agent_service import ClService
        svc = ClService(run_dir).start()
    try:
        return _agent_sessions(finding, run_dir, budget, options or RunOptions(), target_level, findings_file, data_dir)
    finally:
        if svc is not None:
            svc.stop()


def _agent_sessions(finding: str, run_dir: Path, budget: Budget, options: RunOptions, target_level: str,
                    findings_file: Optional[str], data_dir: Optional[str]) -> dict[str, Any]:
    run_id = run_dir.name
    sessions: list[SessionStats] = []
    session_id: Optional[str] = None
    feedback: Optional[str] = None
    auth: Optional[dict[str, Any]] = None
    t0 = time.monotonic()
    for i in range(budget.sessions):
        st = run_session(run_dir, build_prompt(finding, run_dir, feedback, findings_file, data_dir), budget, session_id, f"events_{i}.jsonl")
        sessions.append(st)
        session_id = st.session_id
        if not (run_dir / "workspace" / "attempt" / "manifest.json").exists():
            feedback = "No attempt package exists yet. Run `init` and build the attempt."
            continue
        try:
            auth = authoritative_run(run_dir, options)
        except Exception as e:  # a broken package is feedback, not a crash of the loop
            auth = None
            feedback = f"The harness could not run your package: {type(e).__name__}: {str(e)[:600]}"
            continue
        r = auth["report"]
        feedback = feedback_text(r)
        if LEVEL_RANK[r.confidence.level] >= LEVEL_RANK[target_level] or st.stopped_by != "finished":
            break
    summary: dict[str, Any] = {
        "finding": finding, "run_id": run_id, "sessions": [s.__dict__ for s in sessions],
        "tool_calls": sum(s.tool_calls for s in sessions), "llm_steps": sum(s.llm_steps for s in sessions),
        "tokens": sum(s.tokens for s in sessions), "wall_s": round(time.monotonic() - t0, 1),
        "lock_tampered": bool(auth and auth["lock_tampered"]),
    }
    if auth:
        r = auth["report"]
        summary.update({"test_id": r.test_id, "verdict": r.verdict, "final_verdict": r.final_verdict,
                        "level": r.confidence.level, "form_integrity": r.audit.rate,
                        "defeaters": {d.id: d.status for d in r.confidence.defeaters},
                        "next_steps": r.confidence.next_steps, "positive": r.positive.observed_text,
                        "negative": r.negative.observed_text})
    else:
        summary.update({"verdict": None, "level": None})
    (run_dir / "agent_result.json").write_text(json.dumps(summary, indent=1))
    return summary
