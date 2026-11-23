"""Prepare and run experimental cells."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .cell import Cell
from .prompts import PROMPT_VERSION
from .util import dump, load, sha

DEV = {"01": "nnsmith", "02": "minference", "03": "infinigen", "04": "sparta"}
TEST = {"05": "prompt-cache", "07": "spinquant", "09": "kvquant", "14": "dx100"}

DEFAULT_PROTOCOL = {
    "version": "gap-receipt-swarm/1",
    "model_alias": "x-test-2",
    "expected_backend": "deepseek-v4.1-flash-1017",
    "split": {"dev": DEV, "test": TEST},
    "conditions": ["api_once", "single_agent", "gap_receipt_swarm"],
    "max_http_requests_per_cell": 10,
    "max_output_tokens": 32768,
    "max_actual_returned_tokens_per_cell": 750000,
    "per_request_timeout_seconds": 600,
    "per_cell_wall_seconds": 3600,
    "lead_turns": 7,
    "worker_replies": 3,
    "worker_count": 1,
    "delegate_from_turn": 4,
    "paper_first": False,
    "prompt_version": PROMPT_VERSION,
    "single_agent_turns": 8,
    "max_report_candidates": 3,
    "global_model_concurrency": 2,
    "target_execution": "not_run",
    "reference_allowed_in_generation": False,
}


def prepare(root: Path, inputs: Path) -> Path:
    root = Path(root)
    index = load(Path(inputs) / "input-index.json")
    for relative, digest in index.items():
        path = Path(inputs) / relative
        if sha(path.read_bytes()) != digest:
            raise ValueError(f"Frozen input changed: {path}")
    if root.exists():
        raise ValueError(f"Run directory exists: {root}")
    root.mkdir(parents=True)
    dump(root / "protocol.json", DEFAULT_PROTOCOL)
    dump(root / "input-index.json", index)
    (root / "inputs").symlink_to(Path(inputs).resolve())
    return root


def _run_cell(inputs: Path, paper: str, condition: str, root: Path, protocol: dict):
    cell_dir = root / "cells" / paper / condition
    cell_dir.parent.mkdir(parents=True, exist_ok=True)
    result = Cell(inputs, paper, condition, cell_dir, protocol).run()
    dump(cell_dir / "summary.json", result)
    print(json.dumps({k: result[k] for k in ("paper", "condition", "requests", "tokens", "error")},
                     ensure_ascii=False), flush=True)
    return result


async def run(root: Path, split: str, conditions: list[str], papers_filter=None) -> list[dict]:
    root = Path(root)
    protocol = load(root / "protocol.json")
    inputs = (root / "inputs").resolve()
    papers = list(protocol["split"][split].values())
    if papers_filter:
        if unknown := set(papers_filter) - set(papers):
            raise ValueError(f"Unknown papers in {split}: {sorted(unknown)}")
        papers = [p for p in papers if p in papers_filter]
    index = load(root / "input-index.json")
    for slug in papers:
        for name in ("paper.json", "source.json", "original-source-packet.txt"):
            relative = f"{slug}/{name}"
            if relative not in index or sha((inputs / relative).read_bytes()) != index[relative]:
                raise ValueError(f"Missing or changed study input: {relative}")
    pending = []
    for slug in papers:
        for condition in conditions:
            cell_dir = root / "cells" / slug / condition
            if (cell_dir / "result.json").is_file():
                continue
            if cell_dir.exists():
                raise ValueError(f"Non-terminal cell archive: {cell_dir}")
            pending.append((slug, condition))
    semaphore = asyncio.Semaphore(protocol["global_model_concurrency"])

    async def guarded(item):
        async with semaphore:
            return await asyncio.to_thread(_run_cell, inputs, item[0], item[1], root, protocol)

    results = await asyncio.gather(*(guarded(item) for item in pending), return_exceptions=True)
    rows = []
    for item, result in zip(pending, results):
        if isinstance(result, Exception):
            print(f"CELL FAILED {item}: {result}", flush=True)
            rows.append({"paper": item[0], "condition": item[1], "error": str(result)})
        else:
            rows.append(result)
    return rows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("root", type=Path)
    prep.add_argument("--inputs", type=Path, required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("root", type=Path)
    run_p.add_argument("--split", default="dev", choices=["dev", "test"])
    run_p.add_argument("--allow-posthoc-test", action="store_true")
    run_p.add_argument("--conditions", nargs="+", default=["gap_receipt_swarm"])
    run_p.add_argument("--papers", nargs="+")
    args = parser.parse_args(argv)
    if args.action == "prepare":
        print(prepare(args.root, args.inputs))
    else:
        if args.split == "test" and not args.allow_posthoc_test:
            parser.error("Test papers are an exposed evaluation set. Add --allow-posthoc-test to run them.")
        rows = asyncio.run(run(args.root, args.split, args.conditions, args.papers))
        dump(Path(args.root) / "run-summary.json", rows)
        print(json.dumps(rows, ensure_ascii=False))


if __name__ == "__main__":
    main()
