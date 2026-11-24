"""Acceptance checks for the acquired, version-pinned development corpus.

Offline source checkouts may omit all large inputs. Such absence is reported as
a skip, never as an acquisition pass. Partially missing inputs are failures.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlparse


WORKSPACE = Path(__file__).resolve().parents[1]
CATALOG = WORKSPACE / "data/catalog/papers.json"


class CatalogAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CATALOG.is_file():
            raise unittest.SkipTest(
                "Catalog data absent: acquire the 10 PDFs and 5 repositories; "
                "this skip is not corpus acceptance."
            )
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.papers = cls.catalog["papers"]
        cls.selected = [paper for paper in cls.papers if paper["selected"]]

    def test_catalog_counts_ids_and_metadata(self):
        self.assertEqual(self.catalog["catalog_version"], "1.0")
        self.assertEqual(len(self.papers), 10, "The frozen candidate corpus has exactly 10 papers")
        self.assertEqual(len(self.selected), 5, "Exactly 5 development repositories are selected")
        ids = [paper["id"] for paper in self.papers]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(len({paper["pdf_sha256"] for paper in self.papers}), 10)
        for paper in self.papers:
            with self.subTest(paper=paper["id"]):
                self.assertRegex(paper["id"], r"^[a-z][a-z0-9_]*$")
                for key in ["title", "venue", "selection_reason", "paper_version_note"]:
                    self.assertIsInstance(paper[key], str)
                    self.assertTrue(paper[key].strip(), key)
                self.assertIs(type(paper["selected"]), bool)
                self.assertIs(type(paper["year"]), int)
                self.assertGreaterEqual(paper["year"], 2000)
                self.assertEqual(paper["acquisition_status"], "complete")
                self.assertRegex(paper["pdf_sha256"], r"^[0-9a-f]{64}$")
                self.assertIs(type(paper["pdf_page_count"]), int)
                self.assertGreater(paper["pdf_page_count"], 0)
                self.assertGreater(paper["pdf_size_bytes"], 0)
                self.assertEqual(paper["pdf_path"], f"data/papers/{paper['id']}/paper.pdf")
                self.assertIsInstance(paper["metadata_sources"], list)
                self.assertTrue(paper["metadata_sources"])
                for url in [paper["paper_url"], paper["pdf_url"], paper["repo_url"], *paper["metadata_sources"]]:
                    parsed = urlparse(url)
                    self.assertEqual(parsed.scheme, "https", url)
                    self.assertTrue(parsed.netloc, url)
                    self.assertFalse(parsed.username or parsed.password, "Catalog URLs must not contain credentials")
                if paper["selected"]:
                    self.assertEqual(paper["repo_path"], f"data/repos/{paper['id']}")
                    self.assertRegex(paper["repository_commit"], r"^[0-9a-f]{40}$")
                    self.assertIs(paper["repository_shallow"], True)
                else:
                    self.assertIsNone(paper["repo_path"])
                    self.assertIsNone(paper["repository_commit"])

    def test_all_ten_pdfs_exist_match_hash_and_parse(self):
        paths = [(paper, WORKSPACE / paper["pdf_path"]) for paper in self.papers]
        if not any(path.exists() for _, path in paths):
            self.skipTest(
                "All PDF data absent: run scripts/acquire_papers.py. "
                "A skipped PDF check does not establish acquisition success."
            )
        from pypdf import PdfReader

        for paper, path in paths:
            with self.subTest(paper=paper["id"]):
                self.assertTrue(path.is_file(), f"Partially acquired corpus: missing {path}")
                raw = path.read_bytes()
                self.assertTrue(raw.startswith(b"%PDF-"), "Downloaded input is not a PDF")
                self.assertEqual(len(raw), paper["pdf_size_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), paper["pdf_sha256"])
                reader = PdfReader(path)
                self.assertFalse(reader.is_encrypted)
                self.assertGreater(len(reader.pages), 0)
                self.assertEqual(len(reader.pages), paper["pdf_page_count"])
                for page in reader.pages:
                    self.assertGreater(float(page.mediabox.width), 0)
                    self.assertGreater(float(page.mediabox.height), 0)

    def test_five_repositories_exist_and_match_pinned_commits(self):
        paths = [(paper, WORKSPACE / paper["repo_path"]) for paper in self.selected]
        if not any(path.exists() for _, path in paths):
            self.skipTest(
                "All repository data absent: run scripts/acquire_papers.py. "
                "A skipped commit check does not establish acquisition success."
            )
        for paper, path in paths:
            with self.subTest(paper=paper["id"]):
                self.assertTrue((path / ".git").exists(), f"Partially acquired corpus: missing repository {path}")
                def git(*args):
                    return subprocess.run(
                        ["git", "-C", str(path), *args],
                        capture_output=True, text=True, check=True, timeout=30,
                    ).stdout.strip()
                self.assertEqual(git("rev-parse", "HEAD"), paper["repository_commit"])
                self.assertEqual(git("rev-parse", "--is-shallow-repository"), "true")
                self.assertEqual(git("remote", "get-url", "origin").removesuffix(".git"), paper["repo_url"].removesuffix(".git"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
