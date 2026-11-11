"""Command line.

  python -m checklimits run --attempt checklimits/attempts/flexprefill/F07
  python -m checklimits relay --port 8787
Run from the checklimits/ project directory (or with it on PYTHONPATH).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import PROJECT_ROOT


def cmd_run(a: argparse.Namespace) -> int:
    from .harness import RunOptions, run_attempt, write_outputs

    attempt = Path(a.attempt)
    opts = RunOptions.fast() if a.fast else RunOptions(repeats=a.repeats)
    result = run_attempt(attempt, options=opts)
    report = result["report"]
    out_dir = Path(a.out) if a.out else PROJECT_ROOT / "results" / report.artifact_id
    paths = write_outputs(result, out_dir, (out_dir / "raw") if a.out else (PROJECT_ROOT / "runs" / report.artifact_id))
    c = report.confidence
    print(json.dumps({
        "test_id": report.test_id, "finding_id": report.finding_id,
        "verdict": report.verdict, "final_verdict": report.final_verdict, "exec_result": report.exec_result,
        "target_reached": report.positive.target_reached,
        "positive": report.positive.observed_text, "negative": report.negative.observed_text,
        "level": c.level, "level_note": c.level_note, "calibrated": c.calibrated,
        "defeaters": {d.id: d.status for d in c.defeaters},
        "next_steps": c.next_steps, "form_integrity": report.audit.rate,
        "outputs": {k: str(v) for k, v in paths.items()},
    }, indent=1))
    return 0


def cmd_task(a: argparse.Namespace) -> int:
    from .agent_cli import task_text
    print(task_text(a.finding, a.data_dir, findings_file=a.findings_file))
    return 0


def cmd_init(a: argparse.Namespace) -> int:
    from .agent_cli import init_attempt
    files = init_attempt(a.finding, Path(a.out), a.data_dir, a.test_id, a.python, a.findings_file)
    print("created:\n" + "\n".join(f"  {f}" for f in files))
    return 0


def cmd_lint(a: argparse.Namespace) -> int:
    from .agent_cli import format_issues, lint_attempt
    issues = lint_attempt(Path(a.attempt))
    print(format_issues(issues), end="")
    return 1 if any(i.level == "error" for i in issues) else 0


def cmd_agent(a: argparse.Namespace) -> int:
    from .agent_loop import Budget, run_agent
    from .harness import RunOptions

    budget = Budget(wall_s=a.wall_s, tool_calls=a.tool_calls, tokens=a.tokens, sessions=a.sessions)
    res = run_agent(a.finding, a.run_id, budget, RunOptions.fast() if a.fast else RunOptions(), a.target_level)
    print(json.dumps(res, indent=1, default=str))
    return 0


def cmd_bench(a: argparse.Namespace) -> int:
    from .bench import run_bench
    from .harness import RunOptions

    opts = RunOptions.fast() if a.fast else RunOptions(repeats=a.repeats)
    out = Path(a.out) if a.out else PROJECT_ROOT / "results" / "bench"
    res = run_bench(a.case or None, out, opts, workers=a.workers)
    print((out / "BENCH.md").read_text())
    return 1 if res["summary"]["false_positives"] else 0


def cmd_relay(a: argparse.Namespace) -> int:
    from .relay import main as relay_main
    return relay_main(["--port", str(a.port)] + (["--log", a.log] if a.log else []))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m checklimits")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run an attempt package and write report + testcase")
    r.add_argument("--attempt", required=True, help="attempt directory")
    r.add_argument("--out", help="output directory (default: results/<artifact_id>)")
    r.add_argument("--fast", action="store_true", help="main pair only; every optional defeater stays open")
    r.add_argument("--repeats", type=int, help="independent runs for D8 (default: profile n_rep)")
    r.set_defaults(fn=cmd_run)
    t = sub.add_parser("task", help="print the task description for a finding (for the code agent)")
    t.add_argument("finding")
    t.add_argument("--data-dir", default="data/pilot_flexprefill")
    t.add_argument("--findings-file", help="step 4 hand-off, e.g. results/step4/flexprefill/limitations_for_tests.json")
    t.set_defaults(fn=cmd_task)
    i = sub.add_parser("init", help="create an attempt package skeleton for a finding")
    i.add_argument("finding")
    i.add_argument("--out", required=True)
    i.add_argument("--data-dir", default="data/pilot_flexprefill")
    i.add_argument("--findings-file", help="step 4 hand-off, e.g. results/step4/flexprefill/limitations_for_tests.json")
    i.add_argument("--test-id")
    i.add_argument("--python", help="interpreter for the code under test (default: scratch/venv311 if present)")
    i.set_defaults(fn=cmd_init)
    li = sub.add_parser("lint", help="static checks of an attempt package against T1-T9")
    li.add_argument("--attempt", required=True)
    li.set_defaults(fn=cmd_lint)
    ag = sub.add_parser("agent", help="run the code agent (opencode in a bwrap sandbox) on a finding, then audit it")
    ag.add_argument("finding")
    ag.add_argument("--run-id", required=True)
    ag.add_argument("--wall-s", type=int, default=1800)
    ag.add_argument("--tool-calls", type=int, default=250)
    ag.add_argument("--tokens", type=int, default=4_000_000)
    ag.add_argument("--sessions", type=int, default=2)
    ag.add_argument("--target-level", default="L3")
    ag.add_argument("--fast", action="store_true", help="authoritative run without optional defeaters (debugging)")
    ag.set_defaults(fn=cmd_agent)
    b = sub.add_parser("bench", help="fault-injection benchmark (writes results/bench/)")
    b.add_argument("--case", action="append", help="case id (repeatable); default: all")
    b.add_argument("--out")
    b.add_argument("--fast", action="store_true")
    b.add_argument("--repeats", type=int)
    b.add_argument("--workers", type=int, default=3)
    b.set_defaults(fn=cmd_bench)
    rl = sub.add_parser("relay", help="start the SoCLaaS relay (needs SOCLAAS_* in the environment)")
    rl.add_argument("--port", type=int, default=8787)
    rl.add_argument("--log")
    rl.set_defaults(fn=cmd_relay)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
