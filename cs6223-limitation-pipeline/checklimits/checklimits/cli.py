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
    paths = write_outputs(result, out_dir, PROJECT_ROOT / "runs" / report.artifact_id)
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
    rl = sub.add_parser("relay", help="start the SoCLaaS relay (needs SOCLAAS_* in the environment)")
    rl.add_argument("--port", type=int, default=8787)
    rl.add_argument("--log")
    rl.set_defaults(fn=cmd_relay)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
