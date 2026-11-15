"""Local CLI for evidence preparation, generation, replay and human evaluation."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="paperprobe", description="Paper + fixed repository → proposed test specifications; no target code execution.")
    cli.add_argument("--workspace", type=Path, default=Path.cwd(), help="Project root containing data/catalog/papers.json")
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check local Python, Git and model CLI availability")
    commands.add_parser("catalog", help="Show the ten candidates and five selected development cases")
    prepare = commands.add_parser("prepare", help="Extract PDFs and statically scan selected repository components")
    prepare.add_argument("--all", action="store_true", help="Extract all ten candidate PDFs, scan selected five repositories")
    run = commands.add_parser("run", help="Generate at most five candidates per paper/method")
    run.add_argument("--backend", choices=["heuristic", "codex", "replay"], default="heuristic")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--methods", nargs="+", choices=["full", "code_only", "direct"])
    run.add_argument("--papers", nargs="+")
    run.add_argument("--max-candidates", type=int, default=3)
    run.add_argument("--replay-from", type=Path)
    review = commands.add_parser("review-export", help="Export anonymous review UI and blank human ratings")
    review.add_argument("--run", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    review.add_argument("--seed", type=int, default=0)
    audit = commands.add_parser("audit", help="Audit frozen contexts, raw responses and shared-call resource accounting")
    audit.add_argument("--run", type=Path, required=True)
    audit.add_argument("--output", type=Path)
    evaluate = commands.add_parser("evaluate", help="Validate and aggregate independent human reviews")
    evaluate.add_argument("--run", type=Path, required=True)
    evaluate.add_argument("--reviews", type=Path, nargs="+", default=[])
    evaluate.add_argument("--output", type=Path, required=True)
    serve = commands.add_parser("serve", help="Serve anonymous review and referenced sources on localhost")
    serve.add_argument("--review", type=Path, required=True)
    serve.add_argument("--port", type=int, default=8765)
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    workspace = args.workspace.resolve()
    def local(path: Path | None) -> Path | None:
        return (path if path.is_absolute() else workspace / path).resolve() if path is not None else None
    try:
        if args.command == "doctor":
            from importlib.metadata import version, PackageNotFoundError
            try:
                pdf_version = version("pypdf")
            except PackageNotFoundError:
                pdf_version = None
            codex = shutil.which("codex")
            auth = subprocess.run([codex, "login", "status"], capture_output=True, text=True, timeout=15).returncode == 0 if codex else False
            result = {"python": sys.version.split()[0], "pypdf": pdf_version, "git": shutil.which("git"), "codex_cli": codex,
                      "codex_authenticated": auth, "catalog_exists": (workspace / "data/catalog/papers.json").is_file(),
                      "note": "Availability is not a successful model call; see recorded smoke/experiment provenance."}
        elif args.command == "catalog":
            from .pipeline import load_catalog
            papers = load_catalog(workspace)["papers"]
            result = {"candidate_count": len(papers), "selected_count": sum(p["selected"] for p in papers),
                      "papers": [{k: p[k] for k in ["id", "title", "selected", "acquisition_status", "pdf_page_count"]} for p in papers]}
        elif args.command == "prepare":
            from .pipeline import prepare_workspace
            result = prepare_workspace(workspace, all_papers=args.all)
        elif args.command == "run":
            from .pipeline import run_experiment
            run = run_experiment(workspace, local(args.output), args.backend, args.methods,
                                 args.max_candidates, args.papers, local(args.replay_from))
            result = {"run_id": run["run_id"], "tasks": len(run["tasks"]),
                      "candidates": sum(len(t["candidates"]) for t in run["tasks"]),
                      "failed_tasks": sum(t["status"] == "failed" for t in run["tasks"]),
                      "human_review_status": "pending", "output": str(local(args.output))}
        elif args.command == "review-export":
            from .evaluation import export_review_pack
            result = export_review_pack(local(args.run), local(args.output), args.seed)
        elif args.command == "audit":
            from .auditing import audit_run
            result = audit_run(local(args.run), local(args.output))
        elif args.command == "evaluate":
            from .evaluation import aggregate_reviews
            result = aggregate_reviews(local(args.run), [local(p) for p in args.reviews], local(args.output))
        else:
            from .webapp import serve_review
            serve_review(local(args.review), port=args.port)
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"paperprobe: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
