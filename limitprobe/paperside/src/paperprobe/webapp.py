"""Read-only loopback review server with a narrow evidence-file allowlist."""
from __future__ import annotations

import html
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, unquote, urlencode, urlsplit


PUBLIC_FILES = {
    "reviewer.html": "text/html; charset=utf-8",
    "review-items.json": "application/json; charset=utf-8",
    "run-manifest.json": "application/json; charset=utf-8",
    "reviews.csv": "text/csv; charset=utf-8",
}
TEXT_SUFFIXES = {".py", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".cuh", ".cu", ".rs", ".go", ".java", ".js", ".jsx", ".ts", ".tsx", ".sh", ".txt", ".md", ".json", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_PDF_BYTES = 64 * 1024 * 1024


def _safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("Invalid source path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} or part.startswith(".") for part in value.split("/")):
        raise ValueError("Source path must be an explicit non-hidden relative file")
    return path.as_posix()


def _inside(root: Path, relative: str) -> Path:
    result = (root / _safe_relative(relative)).resolve()
    if not result.is_relative_to(root):
        raise ValueError("Source path leaves the repository")
    return result


def _source_url(paper_id: str, kind: str, path: str | None = None) -> str:
    values = {"paper_id": paper_id, "kind": kind}
    if path is not None:
        values["path"] = path
    return "/api/source?" + urlencode(values)


def _load_sources(items: list[dict]) -> dict:
    sources = {}
    for item in items:
        paper_id, reference = item["paper_id"], item.get("source_reference") or {}
        pdf_value, repo_value = reference.get("pdf_path"), reference.get("repo_path")
        pdf = Path(pdf_value).resolve() if isinstance(pdf_value, str) and Path(pdf_value).is_absolute() else None
        repo = Path(repo_value).resolve() if isinstance(repo_value, str) and Path(repo_value).is_absolute() else None
        source = sources.setdefault(paper_id, {"pdf": pdf, "repo": repo, "files": set()})
        if source["pdf"] != pdf or source["repo"] != repo:
            raise ValueError("Conflicting source references for the same paper")
        evidence = (item.get("candidate") or {}).get("code_evidence") or {}
        relative = evidence.get("path") if isinstance(evidence, dict) else None
        try:
            if repo and relative:
                path = _inside(repo, relative)
                if path.suffix.lower() in TEXT_SUFFIXES:
                    source["files"].add(_safe_relative(relative))
        except (ValueError, TypeError):
            # Invalid candidate evidence remains reviewable, but is not served.
            pass
    return sources


def _review_html(raw: str, items: list[dict], sources: dict) -> bytes:
    allowed = {}
    for paper_id, source in sources.items():
        if source["pdf"]:
            allowed[str(source["pdf"])] = _source_url(paper_id, "pdf")
        if source["repo"]:
            allowed[str(source["repo"])] = _source_url(paper_id, "code")
            for relative in source["files"]:
                try:
                    allowed[str(_inside(source["repo"], relative))] = _source_url(paper_id, "code", relative)
                except ValueError:
                    pass

    def replace_link(match):
        href = html.unescape(match.group(1))
        parsed = urlsplit(href)
        target = allowed.get(unquote(parsed.path)) if parsed.scheme == "file" and not parsed.netloc else None
        return 'href="' + html.escape(target or "#", quote=True) + '"'

    raw = re.sub(r'href="(file://[^\"]*)"', replace_link, raw)
    for item in items:
        source = sources[item["paper_id"]]
        links = []
        if source["pdf"]:
            links.append('<a target="_blank" rel="noopener" href="' + html.escape(_source_url(item["paper_id"], "pdf"), quote=True) + '">打开论文全文 PDF</a>')
        evidence = (item.get("candidate") or {}).get("code_evidence") or {}
        relative = evidence.get("path") if isinstance(evidence, dict) else None
        if isinstance(relative, str) and relative in source["files"]:
            links.append('<a target="_blank" rel="noopener" href="' + html.escape(_source_url(item["paper_id"], "code", relative), quote=True) + '">打开目标代码文件：' + html.escape(relative) + '</a>')
        rid = re.escape(html.escape(str(item["review_id"]), quote=True))
        marker = r'(<article\b[^>]*\bdata-review-id="' + rid + r'"[^>]*>)'
        nav = '<nav class="evidence-links">' + ' · '.join(links) + '</nav>'
        raw = re.sub(marker, lambda match: match.group(1) + nav, raw, count=1)
    return raw.encode("utf-8")


def make_review_server(review_dir: Path, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    """Build a server for CLI use and bounded HTTP acceptance tests."""
    if host != "127.0.0.1":
        raise ValueError("Review service must bind to 127.0.0.1")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Invalid loopback port")
    root = Path(review_dir).resolve()
    document = json.loads((root / "review-items.json").read_text(encoding="utf-8"))
    items = document["items"]
    sources = _load_sources(items)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Ratings and source paths are not written to a request log.
            return

        def _send(self, status: int, data: bytes, content_type: str):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def _error(self, status=404):
            self._send(status, b"Evidence resource unavailable", "text/plain; charset=utf-8")

        def _handle(self):
            # Reject foreign Host headers; the service is not an external site.
            valid_hosts = {f"127.0.0.1:{self.server.server_port}", "127.0.0.1"}
            if self.headers.get("Host") not in valid_hosts:
                self._error(403)
                return
            request = urlsplit(self.path)
            route = unquote(request.path)
            try:
                if route == "/api/source":
                    query = parse_qs(request.query, keep_blank_values=True)
                    if set(query) - {"paper_id", "kind", "path"} or any(len(value) != 1 for value in query.values()):
                        self._error(400)
                        return
                    paper_id, kind = query.get("paper_id", [""])[0], query.get("kind", [""])[0]
                    source = sources.get(paper_id)
                    if not source:
                        self._error()
                        return
                    if kind == "pdf" and "path" not in query:
                        pdf = source["pdf"]
                        if not pdf or not pdf.is_file() or pdf.resolve() != pdf or pdf.suffix.lower() != ".pdf":
                            self._error()
                            return
                        if pdf.stat().st_size > MAX_PDF_BYTES:
                            self._error(413)
                            return
                        data = pdf.read_bytes()
                        if not data.startswith(b"%PDF-"):
                            self._error(415)
                            return
                        self._send(200, data, "application/pdf")
                        return
                    if kind == "code" and "path" not in query:
                        links = ''.join('<li><a href="' + html.escape(_source_url(paper_id, "code", name), quote=True) + '">' + html.escape(name) + '</a></li>' for name in sorted(source["files"]))
                        page = '<!doctype html><meta charset="utf-8"><h1>候选涉及的代码文件</h1><p>仅展示本审查包引用的文件。</p><ul>' + links + '</ul>'
                        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
                        return
                    if kind == "code" and "path" in query:
                        relative = _safe_relative(query["path"][0])
                        if relative not in source["files"] or not source["repo"]:
                            self._error()
                            return
                        code = _inside(source["repo"], relative)
                        if not code.is_file() or code.suffix.lower() not in TEXT_SUFFIXES:
                            self._error()
                            return
                        if code.stat().st_size > MAX_TEXT_BYTES:
                            self._error(413)
                            return
                        data = code.read_bytes()
                        if b"\x00" in data:
                            self._error(415)
                            return
                        data.decode("utf-8")
                        self._send(200, data, "text/plain; charset=utf-8")
                        return
                    self._error()
                    return
                name = "reviewer.html" if route == "/" else route.removeprefix("/")
                if name not in PUBLIC_FILES or request.query:
                    self._error()
                    return
                declared = root / name
                target = declared.resolve()
                if target != declared or not target.is_relative_to(root) or not target.is_file():
                    self._error()
                    return
                data = _review_html(target.read_text(encoding="utf-8"), items, sources) if name == "reviewer.html" else target.read_bytes()
                self._send(200, data, PUBLIC_FILES[name])
            except (OSError, UnicodeDecodeError, ValueError, TypeError):
                self._error()

        do_GET = _handle
        do_HEAD = _handle

        def do_POST(self):
            self._error(405)

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def serve_review(review_dir: Path, host: str = "127.0.0.1", port: int = 8765):
    """Block while serving the anonymous review pack; save no ratings."""
    server = make_review_server(review_dir, host, port)
    print(f"Review UI: http://127.0.0.1:{server.server_port}/ (read-only; export ratings from browser)")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
