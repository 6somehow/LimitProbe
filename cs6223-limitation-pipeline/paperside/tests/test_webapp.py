"""HTTP acceptance tests for the local, read-only evidence boundary."""
from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from paperprobe.review_ui import render_review_html
from paperprobe.webapp import make_review_server


class ReviewServerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.review = self.root / "review"
        self.review.mkdir()
        (self.review / "private").mkdir()
        (self.review / "private/blinding-map.json").write_text('{"method":"secret"}')
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "target.py").write_text("if value < 16:\n    return value\n")
        (self.repo / "other.py").write_text("not cited, do not serve")
        (self.repo / ".git").mkdir()
        (self.repo / ".git/config").write_text("private repository metadata")
        self.pdf = self.root / "paper.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\nfull paper fixture")
        self.item = {
            "review_id": "review-anonymous", "paper_id": "demo",
            "candidate": {"code_evidence": {"path": "target.py", "line_start": 1}},
            "source_reference": {"pdf_path": str(self.pdf), "repo_path": str(self.repo)},
        }
        (self.review / "review-items.json").write_text(json.dumps({"items": [self.item]}))
        (self.review / "reviewer.html").write_text(render_review_html([self.item], "run-fixture"))
        (self.review / "run-manifest.json").write_text('{"tasks": []}')
        (self.review / "reviews.csv").write_text("review_id,reviewer_id\nreview-anonymous,\n")
        self.server = make_review_server(self.review, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, path, method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def source(self, kind, path=None):
        query = {"paper_id": "demo", "kind": kind}
        if path is not None:
            query["path"] = path
        return "/api/source?" + urlencode(query)

    def test_html_rewrites_file_links_and_adds_candidate_code_link(self):
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        text = body.decode()
        self.assertNotIn('href="file://', text)
        self.assertIn("/api/source?paper_id=demo&amp;kind=pdf", text)
        self.assertIn("kind=code&amp;path=target.py", text)
        self.assertIn("打开目标代码文件", text)
        self.assertNotIn("secret", text)

    def test_pdf_code_and_candidate_only_listing(self):
        status, headers, data = self.request(self.source("pdf"))
        self.assertEqual((status, headers["Content-Type"], data), (200, "application/pdf", self.pdf.read_bytes()))
        status, headers, data = self.request(self.source("code", "target.py"))
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(data, (self.repo / "target.py").read_bytes())
        status, _, body = self.request(self.source("code"))
        self.assertEqual(status, 200)
        self.assertIn(b"target.py", body)
        self.assertNotIn(b"other.py", body)

    def test_only_public_review_artifacts_are_exposed(self):
        for path in ["/reviewer.html", "/review-items.json", "/run-manifest.json", "/reviews.csv"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 200)
        for path in ["/private/blinding-map.json", "/private", "/../repo/target.py", "/%2e%2e/repo/target.py", "/%252e%252e/repo/target.py", "/reviewer.html?x=1"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_path_traversal_hidden_and_uncited_source_files_are_rejected(self):
        for path in ["../paper.pdf", "/etc/passwd", ".git/config", "other.py", "./target.py", "target.py/../other.py", "target.py\\..\\other.py"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(self.source("code", path))[0], 404)
        self.assertEqual(self.request(self.source("pdf", str(self.pdf)))[0], 404)
        self.assertEqual(self.request("/api/source?paper_id=unknown&kind=pdf")[0], 404)
        self.assertEqual(self.request("/api/source?paper_id=demo&kind=pdf&paper_id=unknown")[0], 400)

    def test_symlink_escape_and_binary_text_are_rejected(self):
        (self.repo / "target.py").unlink()
        (self.repo / "target.py").symlink_to(self.root / "paper.pdf")
        self.assertEqual(self.request(self.source("code", "target.py"))[0], 404)
        (self.repo / "target.py").unlink()
        (self.repo / "target.py").write_bytes(b"binary\x00payload")
        self.assertEqual(self.request(self.source("code", "target.py"))[0], 415)

    def test_static_symlink_escape_is_rejected(self):
        (self.review / "reviews.csv").unlink()
        (self.review / "reviews.csv").symlink_to(self.root / "paper.pdf")
        self.assertEqual(self.request("/reviews.csv")[0], 404)

    def test_private_file_cannot_be_exposed_through_public_symlink(self):
        (self.review / "reviews.csv").unlink()
        (self.review / "reviews.csv").symlink_to(self.review / "private/blinding-map.json")
        self.assertEqual(self.request("/reviews.csv")[0], 404)

    def test_swapped_pdf_symlink_is_rejected(self):
        alternate = self.root / "alternate.pdf"
        alternate.write_bytes(b"%PDF-1.7\nnot the declared paper")
        self.pdf.unlink()
        self.pdf.symlink_to(alternate)
        self.assertEqual(self.request(self.source("pdf"))[0], 404)

    def test_no_ratings_writes_and_no_external_bind_or_host(self):
        before = (self.review / "reviews.csv").read_bytes()
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            with self.subTest(method=method):
                self.assertEqual(self.request("/reviews.csv", method)[0], 405)
        self.assertEqual(before, (self.review / "reviews.csv").read_bytes())
        self.assertEqual(self.request("/", headers={"Host": "example.com"})[0], 403)
        with self.assertRaises(ValueError):
            make_review_server(self.review, host="0.0.0.0", port=0)

    def test_head_returns_headers_without_file_body(self):
        status, headers, body = self.request(self.source("pdf"), "HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(int(headers["Content-Length"]), self.pdf.stat().st_size)
        self.assertEqual(body, b"")


if __name__ == "__main__":
    unittest.main()
