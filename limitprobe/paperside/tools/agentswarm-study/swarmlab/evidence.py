"""Frozen paper + pinned-repository evidence with a receipt ledger.

Only two input kinds are reachable: extracted original paper pages and Git blobs
of the author repository at a fixed commit. Nothing is executed.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path, PurePosixPath

from .util import git, load, norm, require, sha


class Evidence:
    def __init__(self, folder: Path, archive: Path):
        self.folder = Path(folder)
        self.archive = Path(archive)
        self.meta = load(self.folder / "source.json")
        self.pages = load(self.folder / "paper.json")
        self.packet_path = self.folder / "original-source-packet.txt"
        self.packet = self.packet_path.read_text() if self.packet_path.is_file() else ""
        self.repo = self.meta.get("repo")
        self.commit = self.meta.get("commit")
        self.paths: dict[str, dict] = {}
        if self.repo:
            rows = git(self.repo, "ls-tree", "-r", "--long", self.commit).decode().splitlines()
            for row in rows:
                info, name = row.split("\t", 1)
                mode, kind, obj, size = info.split()
                if kind == "blob" and size.isdigit() and int(size) <= 500_000:
                    self.paths[name] = {"mode": mode, "size": int(size), "sha": obj}
        self.cache: dict[str, str] = {}
        self.reads: list = []
        self.tool_calls: list = []
        self.page_reads: list = []

    # ---------------------------------------------------------------- paper ---
    def paper_header(self) -> str:
        return "\n\n".join(
            f"PHYSICAL PDF PAGE {p['page']}\n{p.get('numbered') or p['text']}" for p in self.pages
        )

    def page(self, number: int) -> dict:
        require(type(number) is int and 1 <= number <= len(self.pages), "Invalid physical page")
        page = self.pages[number - 1]
        require(page["page"] == number, "Page numbering mismatch")
        self.pages_read_receipt(number)
        return page

    def pages_read_receipt(self, number: int) -> None:
        self.page_reads.append(number)

    def search_paper(self, query: str, limit: int = 20) -> dict:
        require(2 <= len(query) <= 160, "Bounded literal query required")
        hits = []
        total = 0
        needle = norm(query)
        for page in self.pages:
            text = page.get("numbered") or page["text"]
            for line in text.splitlines():
                if needle in norm(line):
                    total += 1
                    if len(hits) < limit:
                        hits.append({"page": page["page"], "line": line[:300]})
        return {"hits": hits, "total": total}

    # --------------------------------------------------------------- source ---
    def blob(self, path: str) -> str:
        require(self.repo, "This paper has no author repository")
        require(path in self.paths, "Not an allowed original tracked blob")
        require(self.paths[path]["mode"] != "120000", "Symlinks are not readable")
        if path not in self.cache:
            raw = git(self.repo, "show", f"{self.commit}:{path}")
            require(b"\x00" not in raw, "Binary source not readable")
            self.cache[path] = raw.decode("utf-8", errors="replace")
        return self.cache[path]

    # ----------------------------------------------------------------- tools ---
    def call(self, agent: str, name: str, args: dict) -> str:
        record = {"agent": agent, "name": name, "args": args}
        if name == "read_paper":
            page = self.page(int(args.get("page", 0)))
            result = json.dumps(page, ensure_ascii=False)
        elif name == "search_paper":
            result = json.dumps(self.search_paper(args.get("query", "")), ensure_ascii=False)
        elif not self.repo:
            raise ValueError("This paper has no author repository")
        elif name == "list_repo":
            prefix = args.get("prefix", "") or ""
            paths = [p for p in self.paths if p.startswith(prefix)]
            result = json.dumps({"paths": paths[:100], "total": len(paths)}, ensure_ascii=False)
        elif name == "search_repo":
            query = args.get("query", "")
            scope = args.get("prefix", "") or ""
            require(2 <= len(query) <= 160, "Bounded literal query required")
            require(not scope.startswith(("/", ":")), "Invalid search scope")
            require(".." not in PurePosixPath(scope).parts, "Invalid search scope")
            command = ["git", "-C", self.repo, "grep", "-n", "-I", "-i", "-F", "-e", query, self.commit, "--"]
            if scope:
                command.append(scope)
            import subprocess

            found = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            require(found.returncode in (0, 1), "Original Git search failed")
            hits, total = [], 0
            for row in found.stdout.decode("utf-8", errors="replace").splitlines():
                path, number, line = row.removeprefix(self.commit + ":").split(":", 2)
                if path not in self.paths:
                    continue
                total += 1
                if len(hits) < 32:
                    hits.append({"path": path, "line": int(number), "text": line[:300]})
            result = json.dumps({"hits": hits, "total": total}, ensure_ascii=False)
        elif name == "read_repo":
            path = args.get("path", "")
            start = args.get("start", 1)
            end = args.get("end", None)
            require(type(start) is int and start >= 1, "Invalid start line")
            if end is None:
                end = start + 120
            require(type(end) is int and start <= end <= start + 159, "Read at most 160 lines")
            lines = self.blob(path).splitlines()
            end = min(end, len(lines))
            require(start <= end, "Invalid source range")
            self.reads.append({"agent": agent, "path": path, "start": start, "end": end})
            result = json.dumps(
                {"path": path, "commit": self.commit, "start": start, "end": end,
                 "text": "\n".join(f"{i}: {lines[i-1]}" for i in range(start, end + 1))},
                ensure_ascii=False,
            )
        else:
            raise ValueError(f"Tool not allowed: {name}")
        record["result_sha256"] = sha(result.encode())
        record["result_chars"] = len(result)
        self.tool_calls.append(record)
        return result

    # ----------------------------------------------------------- validation ---
    def span_read_by(self, agent: str, path: str, start: int, end: int) -> bool:
        return any(
            r["agent"] == agent and r["path"] == path and r["start"] <= start and end <= r["end"]
            for r in self.reads
        )

    def span_any_read(self, path: str, start: int, end: int) -> bool:
        return any(r["path"] == path and r["start"] <= start and end <= r["end"] for r in self.reads)

    def quote_in_page(self, page: int, quote: str) -> bool:
        if not isinstance(quote, str) or not quote.strip() or type(page) is not int:
            return False
        if not 1 <= page <= len(self.pages):
            return False
        return norm(quote) in norm(self.pages[page - 1]["text"])

    def image_b64(self, number: int) -> str:
        path = self.folder / "images" / f"{number}.png"
        if not path.is_file():
            return ""
        return base64.b64encode(path.read_bytes()).decode()
