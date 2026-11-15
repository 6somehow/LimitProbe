#!/usr/bin/env python3
"""Fetch just the four workstream sources. Read/download only; no target install."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from urllib.request import urlopen

from paperprobe.io import file_sha256, inside, read_json
from paperprobe.limitations import verify_catalog


def run_git(repo: Path, *args: str) -> None:
    result = subprocess.run(["git", "-C", str(repo), *args], text=True,
                            capture_output=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError(f"Git failed for {repo.name}: {result.stderr[:300]}")


def acquire(root: Path, catalog: dict, verify_only: bool = False) -> None:
    for paper in catalog["papers"]:
        pdf = inside(root, paper["pdf_path"])
        if not pdf.exists() and not verify_only:
            pdf.parent.mkdir(parents=True, exist_ok=True)
            if not paper["pdf_url"].startswith("https://"):
                raise ValueError("Only HTTPS primary paper URLs are accepted")
            with urlopen(paper["pdf_url"], timeout=45) as response:
                payload = response.read(32_000_001)
            if len(payload) > 32_000_000 or not payload.startswith(b"%PDF-"):
                raise ValueError("Invalid or oversized PDF")
            temporary = pdf.with_suffix(".part")
            temporary.write_bytes(payload)
            if file_sha256(temporary) != paper["pdf_sha256"]:
                temporary.unlink()
                raise ValueError(f"Downloaded PDF differs from pinned version: {paper['id']}")
            temporary.replace(pdf)
        repo = inside(root, paper["repo_path"])
        if not repo.exists() and not verify_only:
            repo.mkdir(parents=True)
            run_git(repo, "init")
            run_git(repo, "remote", "add", "origin", paper["repo_url"])
            run_git(repo, "fetch", "--depth", "1", "origin", paper["repository_commit"])
            run_git(repo, "checkout", "--detach", "FETCH_HEAD")
    indexed = verify_catalog(root, catalog)
    print(f"Verified {len(indexed)} PDFs and pinned repositories; installed/executed target packages: 0")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[1])
    cli.add_argument("--verify-only", action="store_true")
    args = cli.parse_args()
    root = args.workspace.resolve()
    acquire(root, read_json(root / "workstreams/zhaopeng/catalog.json"), args.verify_only)
