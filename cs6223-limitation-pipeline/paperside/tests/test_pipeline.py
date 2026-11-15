"""Integration with an actual isolated Git repository; the target is never imported."""
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from paperprobe.io import file_sha256, read_json, text_sha256, write_json
from paperprobe.papers import build_profile
from paperprobe.pipeline import run_experiment
from paperprobe.scanner import scan_repository
from paperprobe.evaluation import aggregate_reviews, export_review_pack


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        repo = self.root / "data/repos/fixture"
        repo.mkdir(parents=True)
        (repo / "core.py").write_text('raise RuntimeError("target must never execute")\n\ndef choose(n: int):\n    if n < 16:\n        return "small"\n    return "large"\n')
        def git(*args):
            return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q")
        git("add", "core.py")
        git("-c", "user.name=Test Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Fixture")
        commit = git("rev-parse", "HEAD")
        pdf = self.root / "data/papers/fixture/paper.pdf"
        pdf.parent.mkdir(parents=True)
        pdf.write_bytes(b"%PDF-1.4\nunit-test hash fixture, not an extraction input\n")
        paper = {"id": "fixture", "title": "Index boundary fixture", "selected": True,
                 "pdf_path": "data/papers/fixture/paper.pdf", "pdf_sha256": file_sha256(pdf),
                 "repo_path": "data/repos/fixture", "repository_commit": commit,
                 "paper_url": "https://example.invalid/paper", "repo_url": "https://example.invalid/repo",
                 "paper_version_note": "Synthetic test fixture only"}
        write_json(self.root / "data/catalog/papers.json", {"papers": [paper]})
        config = read_json(Path(__file__).parents[1] / "configs/default.json")
        write_json(self.root / "configs/default.json", config)
        quote = "The index switches its allocation policy when the size threshold is exceeded."
        pages = [{"page": 1, "text": quote, "sha256": text_sha256(quote)}]
        profile = build_profile("fixture", pages, paper["pdf_sha256"], paper["title"])
        directory = self.root / "data/processed/fixture"
        write_json(directory / "profile.json", profile)
        write_json(directory / "pages.json", {"paper_id": "fixture", "paper_sha256": paper["pdf_sha256"], "pages": pages})
        scan = scan_repository(repo)
        for c in scan["conditions"]:
            c["evidence"]["commit"] = commit
        write_json(directory / "scan.json", scan)

    def test_generation_review_pending_and_replay_without_target_execution(self):
        run = run_experiment(self.root, self.root / "runs/demo", max_candidates=2, progress=lambda _: None)
        self.assertEqual(len(run["tasks"]), 3)
        self.assertTrue(all(t["status"] == "completed" for t in run["tasks"]))
        self.assertTrue(all(c["checks"]["runtime_status"] == "not_run" for t in run["tasks"] for c in t["candidates"]))
        pack = export_review_pack(self.root / "runs/demo", self.root / "runs/review")
        self.assertGreater(pack["candidate_count"], 0)
        summary = aggregate_reviews(self.root / "runs/demo", [], self.root / "runs/eval")
        self.assertEqual(summary["human_review_status"], "not_started")
        replay = run_experiment(self.root, self.root / "runs/replay", backend="replay", max_candidates=2, replay_from=self.root / "runs/demo", progress=lambda _: None)
        self.assertEqual([len(t["candidates"]) for t in run["tasks"]], [len(t["candidates"]) for t in replay["tasks"]])
        self.assertFalse((self.root / "runs/model-budget.json").exists())

    def test_changed_cap_or_prepared_evidence_cannot_mix_cached_results(self):
        output = self.root / "runs/demo"
        run_experiment(self.root, output, max_candidates=2, progress=lambda _: None)
        with self.assertRaisesRegex(ValueError, "frozen protocol"):
            run_experiment(self.root, output, max_candidates=3, progress=lambda _: None)
        profile_path = self.root / "data/processed/fixture/profile.json"
        profile = read_json(profile_path)
        profile["title"] += " changed"
        write_json(profile_path, profile)
        with self.assertRaisesRegex(ValueError, "frozen protocol"):
            run_experiment(self.root, output, max_candidates=2, progress=lambda _: None)
        with self.assertRaisesRegex(ValueError, "frozen protocol/source"):
            run_experiment(self.root, self.root / "runs/replay", backend="replay", max_candidates=2, replay_from=output, progress=lambda _: None)

    def test_dirty_source_or_unknown_paper_rejected_before_any_generation(self):
        with self.assertRaisesRegex(ValueError, "Requested paper IDs"):
            run_experiment(self.root, self.root / "runs/demo", paper_ids=["fixture", "missing"], progress=lambda _: None)
        source = self.root / "data/repos/fixture/core.py"
        source.write_text(source.read_text() + "\n# changed\n")
        with self.assertRaisesRegex(ValueError, "clean pinned commit"):
            run_experiment(self.root, self.root / "runs/demo", progress=lambda _: None)

    def test_batched_provider_preserves_all_arms_and_uses_cached_terminal_tasks(self):
        calls = []
        class FixtureProvider:
            def __init__(self, *args, **kwargs):
                pass
            def call(self, prompt, output_dir, schema):
                calls.append(prompt)
                data = json.loads(prompt.split("\nDATA:\n", 1)[1])
                write_json(output_dir / "provenance.json", {"prompt_sha256": text_sha256(prompt), "tools_used": [], "call_id": len(calls), "usage": {"input_tokens": 1, "output_tokens": 1}})
                return {"papers": [{"paper_id": c["paper_id"], "candidates": [], "abstain_reason": "Fixture abstention"} for c in data["papers"]]}
        with patch("paperprobe.pipeline.CodexProvider", FixtureProvider):
            run = run_experiment(self.root, self.root / "runs/model", backend="codex", max_candidates=2, progress=lambda _: None)
            self.assertEqual(len(calls), 3)
            self.assertTrue(all(t["status"] == "completed" and t["candidates"] == [] for t in run["tasks"]))
            code_only = json.loads(calls[1].split("\nDATA:\n", 1)[1])
            self.assertTrue(all(c["paper_evidence"] == [] for c in code_only["papers"]))
            run_experiment(self.root, self.root / "runs/model", backend="codex", max_candidates=2, progress=lambda _: None)
            self.assertEqual(len(calls), 3)
            summary = aggregate_reviews(self.root / "runs/model", [], self.root / "runs/model-eval")
            self.assertEqual(summary["human_review_status"], "no_candidates")
            self.assertTrue(all(m["qualified_yield_lower"] == 0 and m["qualified_yield_upper"] == 0 for m in summary["methods"].values()))

    def test_invalid_shared_batch_keeps_failure_for_every_task_without_auto_retry(self):
        calls = []
        class InvalidProvider:
            def __init__(self, *args, **kwargs):
                pass
            def call(self, prompt, output_dir, schema):
                calls.append(prompt)
                write_json(output_dir / "provenance.json", {"prompt_sha256": text_sha256(prompt), "tools_used": [], "call_id": len(calls), "usage": {"input_tokens": 1, "output_tokens": 1}})
                return {"papers": []}
        with patch("paperprobe.pipeline.CodexProvider", InvalidProvider):
            run = run_experiment(self.root, self.root / "runs/model", backend="codex", max_candidates=2, progress=lambda _: None)
            self.assertEqual(len(run["tasks"]), 3)
            self.assertTrue(all(t["status"] == "failed" and t["candidates"] == [] and t["error"] for t in run["tasks"]))
            run_experiment(self.root, self.root / "runs/model", backend="codex", max_candidates=2, progress=lambda _: None)
            self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
