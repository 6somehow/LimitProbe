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


def _e2e_args(a: argparse.Namespace) -> dict:
    from .agent_batch import artifact_paths
    data_dir, ff, repo = artifact_paths(a.artifact)
    return {"findings_file": a.findings_file or ff, "data_dir": a.data_dir or data_dir, "repo_rel": a.repo or repo}


def _e2e_guard(fn):
    """Run an e2e command; map the contract's exit codes (CONTRACT_TEST_REPORT.md section 6) and print the summary."""
    from .e2e import EXIT_ERROR, EXIT_INPUT, InputError
    try:
        out = fn()
    except (InputError, FileNotFoundError) as e:
        print(json.dumps({"error": str(e), "exit_code": EXIT_INPUT}))
        return EXIT_INPUT
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"[:400], "exit_code": EXIT_ERROR}))
        return EXIT_ERROR
    print(json.dumps(out, indent=1, default=str))
    return out.get("exit_code", 0)


def cmd_test(a: argparse.Namespace) -> int:
    from .e2e import DEFAULT_RESULTS_ROOT, run_test
    return _e2e_guard(lambda: run_test(
        a.artifact, results_root=Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT,
        attempts_roots=[Path(p) for p in a.attempts_root] if a.attempts_root else None, run_agent=a.run_agent,
        only=a.only, workers=a.workers, fast=a.fast, strict=a.strict, skip_envcheck=a.skip_envcheck, python=a.python,
        provision=a.provision, analyze=a.analyze, model=a.model, **_e2e_args(a)))


def cmd_paper_only(a: argparse.Namespace) -> int:
    import os
    from .e2e import DEFAULT_RESULTS_ROOT, InputError
    from .paper_only import run_paper_only, run_swarm_paper_only

    def go():
        if a.swarm_report:
            try:
                return run_swarm_paper_only(
                    a.artifact, Path(a.pdf), Path(a.swarm_report), title=a.title or a.artifact, venue=a.venue or "",
                    results_root=Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT / "swarm",
                    extractor=a.swarm_pdf_extractor)
            except ValueError as error:
                raise InputError(str(error)) from error
        base, key = os.environ.get("SOCLAAS_BASE_URL") or "", os.environ.get("SOCLAAS_API_KEY") or ""
        if not base or not key:
            raise InputError("needs SOCLAAS_BASE_URL and SOCLAAS_API_KEY (through the relay: python -m pipeline doctor)")
        if not Path(a.pdf).is_file():
            raise InputError(f"no PDF at {a.pdf}")
        return run_paper_only(a.artifact, Path(a.pdf), title=a.title or a.artifact, venue=a.venue or "",
                              results_root=Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT,
                              model=a.model or os.environ.get("PIPELINE_MODEL") or "x-test-2", base_url=base, key=key)
    return _e2e_guard(go)


def cmd_analyze(a: argparse.Namespace) -> int:
    from .e2e import DEFAULT_RESULTS_ROOT, run_analysis
    return _e2e_guard(lambda: run_analysis(
        a.artifact, results_root=Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT,
        model=a.model, workers=a.workers, force=a.force, **_e2e_args(a)))


def cmd_report(a: argparse.Namespace) -> int:
    from .e2e import DEFAULT_RESULTS_ROOT, run_report
    def go():
        kw = _e2e_args(a)
        kw.pop("repo_rel")
        return run_report(a.artifact, results_root=Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT,
                          strict=a.strict, **kw)
    return _e2e_guard(go)


def cmd_envcheck(a: argparse.Namespace) -> int:
    from .e2e import DEFAULT_RESULTS_ROOT, envcheck
    def go():
        kw = _e2e_args(a)
        env = envcheck(a.artifact, kw["data_dir"], kw["repo_rel"], a.python)
        root = Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT
        (root / "tests" / a.artifact).mkdir(parents=True, exist_ok=True)
        (root / "tests" / a.artifact / "ENV.json").write_text(json.dumps(env, indent=1) + "\n")
        return {**env, "exit_code": 0 if env["status"] == "ok" else 4}
    return _e2e_guard(go)


def cmd_provision(a: argparse.Namespace) -> int:
    import subprocess

    from .provision import DEFAULT_PYTHON, provision
    out_dir = PROJECT_ROOT / "scratch" / "preflight" / a.name
    repo = Path(a.repo_dir) if a.repo_dir else out_dir / "repo"
    if not repo.exists():
        if not a.repo_url:
            print(json.dumps({"error": "give --repo-dir of an existing checkout or --repo-url", "exit_code": 2}))
            return 2
        out_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", a.repo_url, str(repo)], check=True, timeout=900)
    if a.commit:
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", a.commit], check=True)
    rec = provision(a.name, repo, a.commit, a.python or DEFAULT_PYTHON, a.extras, install=not a.no_install,
                    run_tests=not a.skip_tests, package_root=a.package_root)
    print(json.dumps({k: rec[k] for k in ("name", "status", "reasons", "head", "files") if k in rec}, indent=1))
    return 0 if rec["status"] == "ok" else 4


def cmd_labels(a: argparse.Namespace) -> int:
    from . import labels
    from .e2e import DEFAULT_RESULTS_ROOT
    root = Path(a.results_root) if a.results_root else DEFAULT_RESULTS_ROOT
    if a.action == "sample":
        res = labels.sample(root, Path(a.out), a.n, tuple(a.raters), a.seed, a.artifact)
    elif a.action == "llm":
        import os

        from . import llm_label
        key_file = a.key_file or os.environ.get("OPENAI_KEY_FILE")
        if not key_file:
            print(json.dumps({"error": "give --key-file or set OPENAI_KEY_FILE (a file holding the key; it is never printed)"}))
            return 2
        res = llm_label.label(Path(a.sheet), root, Path(a.out), Path(key_file), a.samples, a.model)
    elif a.action == "context":
        # one readable file per item with everything needed to judge the test (driver source included)
        from . import llm_label
        from .agent_batch import artifact_paths
        out = Path(a.out) / "context"
        out.mkdir(parents=True, exist_ok=True)
        for r in labels.read_sheet(Path(a.sheet)).values():
            text = llm_label.build_prompt(r, root, artifact_paths(r["artifact"])[2], questions=False)
            (out / f"{r['item_id']}.md").write_text(f"# {r['item_id']}  {r['finding_id']}\n\n" + text)
        res = {"written": len(list(out.glob("*.md"))), "dir": str(out)}
    elif a.action == "refresh-key":
        res = labels.refresh_key(Path(a.key), root)
    elif a.action == "baseline":
        res = labels.compare_to_baseline(Path(a.sheet), [Path(p) for p in a.sheets])
    elif a.action == "compare":
        from . import llm_label
        res = llm_label.compare([Path(p) for p in a.sheets], Path(a.key))
    else:
        res = labels.evaluate([Path(p) for p in a.sheets], Path(a.key))
    print(json.dumps(res, indent=1))
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

    budget = Budget(wall_s=a.wall_s, tool_calls=a.tool_calls, tokens=a.tokens, sessions=a.sessions, blind=a.blind)
    res = run_agent(a.finding, a.run_id, budget, RunOptions.fast() if a.fast else RunOptions(), a.target_level,
                    a.findings_file)
    print(json.dumps(res, indent=1, default=str))
    return 0


def cmd_batch(a: argparse.Namespace) -> int:
    from .agent_batch import artifact_paths, run_batch, select
    from .agent_loop import Budget

    data_dir, ff, repo = artifact_paths(a.artifact)
    a.findings_file = a.findings_file or ff
    if a.list:
        chosen, skipped = select(a.findings_file, data_dir, repo)
        print(json.dumps({"selected": chosen, "n_skipped": len(skipped), "skipped": skipped}, indent=1))
        return 0
    res = run_batch(a.findings_file, a.batch_id, a.only, a.skip, a.workers,
                    Budget(a.wall_s, a.tool_calls, a.tokens, a.sessions, a.blind), data_dir=data_dir, repo_rel=repo)
    print(json.dumps({k: v for k, v in res.items() if k != "results"}, indent=1))
    return 0


def cmd_reaudit(a: argparse.Namespace) -> int:
    from .agent_batch import reaudit

    res = reaudit(Path(a.root), Path(a.out), a.workers)
    changed = [r for r in res["rows"] if (r["before_verdict"], r["before_level"]) != (r["after_verdict"], r["after_level"])]
    print(json.dumps({"rows": len(res["rows"]), "changed": [(r["name"], r["before_level"], r["after_level"]) for r in changed]}, indent=1))
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
    ag.add_argument("--findings-file", help="use the step 4 hand-off instead of the pilot data")
    ag.add_argument("--fast", action="store_true", help="authoritative run without optional defeaters (debugging)")
    ag.add_argument("--blind", action="store_true", help="hide the harness source and the rule documents from the agent")
    ag.set_defaults(fn=cmd_agent)
    ba = sub.add_parser("batch", help="run the agent over every step 4 Finding the harness can judge")
    ba.add_argument("--artifact", default="flexprefill")
    ba.add_argument("--findings-file", help="default: results/step4/<artifact>/limitations_for_tests.json")
    ba.add_argument("--batch-id", default="batch1")
    ba.add_argument("--only", action="append")
    ba.add_argument("--skip", action="append")
    ba.add_argument("--workers", type=int, default=3)
    ba.add_argument("--wall-s", type=int, default=1800)
    ba.add_argument("--tool-calls", type=int, default=250)
    ba.add_argument("--tokens", type=int, default=4_000_000)
    ba.add_argument("--sessions", type=int, default=2)
    ba.add_argument("--blind", action="store_true", help="hide the harness source and the rule documents from the agent")
    ba.add_argument("--list", action="store_true", help="only list what would run and why the rest is skipped")
    ba.set_defaults(fn=cmd_batch)
    ra = sub.add_parser("reaudit", help="re-run the harness on archived agent packages (after a rule change)")
    ra.add_argument("--root", default="agent_results/batch")
    ra.add_argument("--out", required=True)
    ra.add_argument("--workers", type=int, default=3)
    ra.set_defaults(fn=cmd_reaudit)
    def _common(sp, with_repo=True):
        sp.add_argument("artifact", help="artifact_id as registered in data/*/artifact.json")
        sp.add_argument("--findings-file", help="default: results/step4/<artifact>/limitations_for_tests.json")
        sp.add_argument("--data-dir", help="default: the data/* directory whose artifact.json has this id")
        sp.add_argument("--repo", help="repository dir relative to the pipeline root; default third_party/<repo name>")
        sp.add_argument("--results-root", help="default: checklimits/results/e2e (the pipeline passes <root>/results)")
        sp.add_argument("--python", help="interpreter of the code under test; default scratch/venv_<artifact>")
    te = sub.add_parser("test", help="end to end: step 4 Findings -> one report.json per Finding + LIMITATIONS.md")
    _common(te)
    te.add_argument("--attempts-root", action="append", help="where to look for existing test packages (repeatable)")
    te.add_argument("--run-agent", action="store_true", help="run the code agent for judgeable Findings without a package")
    te.add_argument("--only", action="append", help="test only this finding id (repeatable); the rest keep earlier records")
    te.add_argument("--workers", type=int, default=3)
    te.add_argument("--fast", action="store_true")
    te.add_argument("--strict", action="store_true", help="exit 4 if any Finding is not_run for env/agent/harness reasons")
    te.add_argument("--skip-envcheck", action="store_true")
    te.add_argument("--provision", action="store_true",
                    help="if the environment check fails and the repository is checked out, build scratch/venv_<artifact> first")
    te.add_argument("--analyze", action="store_true",
                    help="add an analysis (tier A0-A2, not a verdict) to every Finding that was not tested; needs the relay")
    te.add_argument("--model", default=None, help="model for --analyze (default PIPELINE_MODEL, else x-test-2)")
    te.set_defaults(fn=cmd_test)
    po = sub.add_parser("paper-only", help="a paper with no public code: reading-based candidates, tier A1 at most")
    po.add_argument("artifact")
    po.add_argument("--pdf", required=True)
    po.add_argument("--title")
    po.add_argument("--venue")
    po.add_argument("--model", default=None)
    po.add_argument("--results-root", default=None)
    po.add_argument("--swarm-report")
    po.add_argument("--swarm-pdf-extractor", choices=["pypdf", "pymupdf"], default="pypdf")
    po.set_defaults(fn=cmd_paper_only)
    an = sub.add_parser("analyze", help="add analyses to the not-tested Findings already on disk (no test is run)")
    _common(an)
    an.add_argument("--model", default=None)
    an.add_argument("--workers", type=int, default=3)
    an.add_argument("--force", action="store_true", help="redo analyses that already exist (answers stay cached)")
    an.set_defaults(fn=cmd_analyze)
    rp = sub.add_parser("report", help="regenerate LIMITATIONS.md from the records on disk")
    _common(rp)
    rp.add_argument("--strict", action="store_true")
    rp.set_defaults(fn=cmd_report)
    ec = sub.add_parser("envcheck", help="check repository commit, interpreter and entry imports; writes ENV.json")
    _common(ec)
    ec.set_defaults(fn=cmd_envcheck)
    pv = sub.add_parser("provision", help="build the venv of the code under test, run the repository's tests, write PREFLIGHT.md")
    pv.add_argument("name", help="artifact id; the venv is scratch/venv_<name>")
    pv.add_argument("--repo-url")
    pv.add_argument("--repo-dir", help="existing checkout (default: scratch/preflight/<name>/repo, cloned from --repo-url)")
    pv.add_argument("--commit", help="pinned commit to check out")
    pv.add_argument("--python", help="interpreter used only to create the venv (default: Python 3.11 of the ravel env)")
    pv.add_argument("--extras", action="append", help="pip extras of the package, e.g. dev (repeatable)")
    pv.add_argument("--package-root", default="src")
    pv.add_argument("--no-install", action="store_true")
    pv.add_argument("--skip-tests", action="store_true")
    pv.set_defaults(fn=cmd_provision)
    lb = sub.add_parser("labels", help="human labelling: sample sheets of tested Findings / compute agreement")
    lb.add_argument("action", choices=["sample", "evaluate", "llm", "compare", "context", "baseline", "refresh-key"])
    lb.add_argument("--sheet", help="llm: the sheet to label (any rater's, they are identical)")
    lb.add_argument("--key-file", help="llm: file with the OpenAI key (or env OPENAI_KEY_FILE)")
    lb.add_argument("--model", default="gpt-6.1-sol")
    lb.add_argument("--samples", type=int, default=3, help="llm: independent answers per item (each becomes a sheet)")
    lb.add_argument("--results-root")
    lb.add_argument("--out", default="scratch/labels")
    lb.add_argument("--n", type=int, default=20)
    lb.add_argument("--seed", type=int, default=6223)
    lb.add_argument("--raters", nargs="+", default=["r1", "r2", "r3"])
    lb.add_argument("--artifact", action="append")
    lb.add_argument("--sheets", nargs="+")
    lb.add_argument("--key")
    lb.set_defaults(fn=cmd_labels)
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
