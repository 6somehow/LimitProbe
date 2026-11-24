#!/usr/bin/env python3
"""Acquire public paper PDFs and selected official repositories from the catalog.

Use the project's Python environment with pypdf installed. Existing PDFs and
checkouts are verified against recorded hashes/commits. No issue tracker or
model checkpoints are downloaded, and repositories are never modified/reset.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from pypdf import PdfReader


def validate_pdf(path: Path, expected_hash: str | None = None) -> dict:
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError(f"Not a PDF: {path}")
    digest = hashlib.sha256(data).hexdigest()
    if expected_hash and digest != expected_hash:
        raise ValueError(f"PDF hash mismatch: {path}")
    reader = PdfReader(path)
    if reader.is_encrypted or len(reader.pages) == 0:
        raise ValueError(f"Unreadable/encrypted PDF: {path}")
    # Reading all page objects detects truncated downloads, rather than only
    # trusting the PDF magic or the Content-Type header.
    for page in reader.pages:
        _ = page.mediabox
    return {"pdf_sha256": digest, "pdf_page_count": len(reader.pages),
            "pdf_size_bytes": len(data)}


def acquire_pdf(root: Path, paper: dict) -> dict:
    path = root / paper["pdf_path"]
    if path.exists():
        return validate_pdf(path, paper.get("pdf_sha256"))
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".pdf.partial")
    request = urllib.request.Request(paper["pdf_url"], headers={
        "User-Agent": "CS6223-paper-guided-testing/1.0 (public research artifact)"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            resolved_url = response.geturl()
            with partial.open("wb") as stream:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
        result = validate_pdf(partial, paper.get("pdf_sha256"))
        partial.replace(path)
        result["pdf_resolved_url"] = resolved_url
        return result
    finally:
        partial.unlink(missing_ok=True)


def git(*args: str, cwd: Path | None = None) -> str:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(["git", *args], cwd=cwd, env=env, check=True,
                            capture_output=True, text=True, timeout=300)
    return result.stdout.strip()


def acquire_repo(root: Path, paper: dict) -> dict:
    path = root / paper["repo_path"]
    expected = paper.get("repository_commit")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        if expected:
            # Reconstruct exactly the pinned snapshot; never follow a newer HEAD.
            git("init", str(path))
            git("remote", "add", "origin", paper["repo_url"], cwd=path)
            git("fetch", "--depth", "1", "origin", expected, cwd=path)
            git("checkout", "--detach", "FETCH_HEAD", cwd=path)
        else:
            args = ["clone", "--depth", "1", "--single-branch"]
            if paper.get("repository_ref"):
                args += ["--branch", paper["repository_ref"]]
            git(*args, paper["repo_url"], str(path))
    if not (path / ".git").exists():
        raise ValueError(f"Existing directory is not a Git checkout: {path}")
    commit = git("rev-parse", "HEAD", cwd=path)
    if expected and commit != expected:
        raise ValueError(f"Repository commit mismatch: {path}; not resetting")
    if git("status", "--porcelain", cwd=path):
        raise ValueError(f"Repository has local changes: {path}; not resetting")
    return {"repository_commit": commit,
            "repository_commit_date": git("show", "-s", "--format=%cI", "HEAD", cwd=path),
            "repository_shallow": git("rev-parse", "--is-shallow-repository", cwd=path) == "true"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    catalog_path = root / "data/catalog/papers.json"
    catalog = json.loads(catalog_path.read_text())
    papers = catalog["papers"]
    failures = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        if args.verify_only:
            pending = {pool.submit(validate_pdf, root / p["pdf_path"],
                                   p.get("pdf_sha256")): p for p in papers}
        else:
            pending = {pool.submit(acquire_pdf, root, p): p for p in papers}
        for future in as_completed(pending):
            paper = pending[future]
            try:
                paper.update(future.result())
                paper.pop("acquisition_error", None)
                paper["acquisition_status"] = "pdf_validated"
                print(f"PDF {paper['id']}: {paper['pdf_page_count']} pages", flush=True)
            except Exception as error:
                paper["acquisition_status"] = "failed"
                paper["acquisition_error"] = str(error)
                failures.append(paper["id"])
                print(f"FAILED PDF {paper['id']}: {error}", file=sys.stderr, flush=True)
    for paper in papers:
        if paper["acquisition_status"] == "failed":
            continue
        try:
            if paper["selected"]:
                if args.verify_only and not (root / paper["repo_path"]).exists():
                    raise ValueError("Missing selected repository")
                paper.update(acquire_repo(root, paper))
                print(f"REPO {paper['id']}: {paper['repository_commit']}", flush=True)
            paper["acquisition_status"] = "complete"
        except Exception as error:
            paper["acquisition_status"] = "failed"
            paper["acquisition_error"] = str(error)
            failures.append(paper["id"])
            print(f"FAILED REPO {paper['id']}: {error}", file=sys.stderr, flush=True)
    # Verify-only is read-only, including the catalog.
    if not args.verify_only:
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    print(f"Summary: {len(papers)-len(set(failures))}/{len(papers)} complete; "
          f"{sum(p['selected'] for p in papers)} selected.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
