import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from paperprobe.evaluation import (
    CRITERIA, CSV_FIELDS, ReviewContractError, aggregate_reviews, export_review_pack,
)
from paperprobe.reporting import write_run_report


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run = self.root / "run"
        self.run.mkdir()
        candidate = {
            "candidate_id": "full-method-secret-id", "paper_id": "paper-A", "strategy": "boundary",
            "inputs": {"size": [15, 16, 17]}, "preconditions": ["size is valid"],
            "target_condition": "size < 16", "observation": "branch marker",
            "paper_evidence": [{"quote": "supported sizes", "page": 3}],
            "code_evidence": [{"path": "target.py", "line": 4, "commit": "abc", "quote": "if size < 16:"}],
            "oracle": {"status": "proposed", "relation": "valid values preserve IDs"},
            "checks": {"static_status": "passed", "human_review_status": "pending", "runtime_status": "not_run"},
        }
        self.results = {
            "run_id": "run-test", "backend": "heuristic", "mode": "demonstration",
            "methods": ["full", "code_only", "direct"],
            "tasks": [
                {"task_id": "task-A", "paper_id": "paper-A", "method": "full", "status": "generated", "candidates": [candidate]},
                {"task_id": "task-A", "paper_id": "paper-A", "method": "code_only", "status": "failed", "candidates": [], "error": "generation failed"},
                {"task_id": "task-A", "paper_id": "paper-A", "method": "direct", "status": "abstained", "candidates": []},
            ],
            "metadata": {"paper_references": {"paper-A": {"paper_url": "https://example.org/paper", "pdf_path": "/tmp/paper.pdf"}}},
        }
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        (self.run / "results.json").write_text(json.dumps(self.results), encoding="utf-8")

    def review_id(self):
        pack = export_review_pack(self.run, self.root / "pack", seed=3)
        data = json.loads(Path(pack["review_items"]).read_text())
        return data["items"][0]["review_id"]

    def scores(self, reviewer="A", values=None):
        return {"review_id": self.review_id(), "reviewer_id": reviewer,
                **{field: "yes" for field in CRITERIA}, **(values or {}), "reason": "checked independently"}

    def review_file(self, rows, name="reviews.json"):
        path = self.root / name
        path.write_text(json.dumps({"run_id": "run-test", "reviews": rows}), encoding="utf-8")
        return path

    def test_export_blinds_identifiers_and_preserves_empty_tasks(self):
        pack = export_review_pack(self.run, self.root / "pack")
        public = Path(pack["review_items"]).read_text()
        page = Path(pack["reviewer_html"]).read_text()
        for secret in ("full-method-secret-id", '"method":', '"backend":', '"checks":'):
            self.assertNotIn(secret, public)
            self.assertNotIn(secret, page)
        self.assertIn("supported sizes", page)
        self.assertIn("https://example.org/paper", page)
        self.assertIn("file:///tmp/paper.pdf", page)
        self.assertEqual(3, json.loads((self.root / "pack/run-manifest.json").read_text())["task_count"])
        with Path(pack["reviews_csv"]).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual("", rows[0]["scope_relevance"])
        self.assertEqual("", rows[0]["reviewer_id"])

    def test_blank_review_is_pending_not_zero_rating(self):
        pack = export_review_pack(self.run, self.root / "pack")
        summary = aggregate_reviews(self.run, [Path(pack["reviews_csv"])], self.root / "out")
        self.assertEqual("not_started", summary["human_review_status"])
        self.assertFalse(summary["human_conclusions_available"])
        full = summary["methods"]["full"]
        self.assertEqual({"pending": 1}, full["criteria_counts"]["scope_relevance"])
        self.assertEqual((0, 1), (full["qualified_yield_lower"], full["qualified_yield_upper"]))
        self.assertEqual((0, 1), (full["task_completion_lower"], full["task_completion_upper"]))
        code = summary["methods"]["code_only"]
        self.assertEqual(1, code["task_count"])
        self.assertEqual(0, code["qualified_yield_upper"])
        self.assertEqual(0, code["task_completion_upper"])

    def test_public_scope_hides_method_label_without_mutating_raw_result(self):
        candidate = self.results["tasks"][0]["candidates"][0]
        candidate["scope_status"] = "code_only"
        candidate["limitations"] = ["Code-only reasoning cannot confirm the paper scope."]
        self.save()
        before = (self.run / "results.json").read_text()
        pack = export_review_pack(self.run, self.root / "pack")
        data = json.loads(Path(pack["review_items"]).read_text())
        public = data["items"][0]["candidate"]
        self.assertEqual("unknown", public["scope_status"])
        self.assertNotIn('"scope_status": "code_only"', Path(pack["review_items"]).read_text())
        self.assertEqual(candidate["limitations"], public["limitations"])
        self.assertEqual(before, (self.run / "results.json").read_text())
        self.assertEqual("code_only", candidate["scope_status"])
        note = data["export_metadata"]["blinding"]
        self.assertIn("原始 results 数据保持不变", note["display_normalization"])
        self.assertIn("盲审存在", note["limitations"])
        # The public-content hash changes from the old label-bearing export.
        legacy = dict(public, scope_status="code_only")
        material = json.dumps(["run-test", "task-A", "full"], ensure_ascii=False)
        legacy_content = json.dumps(legacy, ensure_ascii=False, sort_keys=True)
        old_id = "review-" + hashlib.sha256((material + "\0" + candidate["candidate_id"] + "\0" + legacy_content).encode()).hexdigest()[:20]
        self.assertNotEqual(old_id, data["items"][0]["review_id"])

    def test_partial_single_reviewer_does_not_become_consensus(self):
        row = self.scores(values={"oracle_design": "", "observation_clarity": ""})
        summary = aggregate_reviews(self.run, [self.review_file([row])], self.root / "out")
        self.assertEqual("partial", summary["human_review_status"])
        self.assertEqual("pending", summary["candidates"][0]["qualification_status"])
        self.assertEqual(0, summary["methods"]["full"]["qualified_yield_lower"])

    def test_two_independent_reviews_and_failed_task_denominators(self):
        rows = [self.scores("A"), self.scores("B")]
        summary = aggregate_reviews(self.run, [self.review_file(rows)], self.root / "out")
        self.assertTrue(summary["human_conclusions_available"])
        self.assertEqual("qualified", summary["candidates"][0]["qualification_status"])
        self.assertEqual(1, summary["methods"]["full"]["qualified_yield_lower"])
        self.assertEqual(0, summary["methods"]["code_only"]["task_completion_lower"])
        self.assertEqual({"agree": 1, "compared": 1}, summary["pairwise_agreement"]["scope_relevance"])
        self.assertEqual(1, summary["paired_yield_differences"][0]["difference_lower"])

    def test_conflict_and_unknown_do_not_become_negative_ratings(self):
        rows = [self.scores("A"), self.scores("B", {"scope_relevance": "no", "oracle_design": "unknown"})]
        summary = aggregate_reviews(self.run, [self.review_file(rows)], self.root / "out")
        item = summary["candidates"][0]
        self.assertEqual("conflict", item["qualification_status"])
        self.assertEqual("unknown", item["criteria"]["oracle_design"])
        self.assertFalse(summary["human_conclusions_available"])
        self.assertEqual(1, summary["methods"]["full"]["qualified_yield_upper"])

    def test_conflicting_duplicate_review_is_rejected_and_identical_is_idempotent(self):
        row = self.scores()
        path = self.review_file([row, row])
        self.assertEqual(1, aggregate_reviews(self.run, [path], self.root / "out")["review_row_count"])
        other = dict(row, scope_relevance="no")
        with self.assertRaisesRegex(ReviewContractError, "conflicting duplicate"):
            aggregate_reviews(self.run, [self.review_file([row, other])], self.root / "out")

    def test_code_only_missing_paper_quote_is_not_automatic_failure(self):
        candidate = copy.deepcopy(self.results["tasks"][0]["candidates"][0])
        candidate["candidate_id"] = "code-only-secret"
        candidate["paper_evidence"] = []
        self.results["tasks"] = [dict(self.results["tasks"][1], status="generated", candidates=[candidate])]
        self.results["methods"] = ["code_only"]
        self.save()
        rows = [self.scores("A"), self.scores("B")]
        summary = aggregate_reviews(self.run, [self.review_file(rows)], self.root / "out")
        self.assertEqual(1, summary["methods"]["code_only"]["qualified_yield_lower"])

    def test_exact_duplicate_candidates_count_once_for_yield(self):
        candidate = copy.deepcopy(self.results["tasks"][0]["candidates"][0])
        candidate["candidate_id"] = "duplicate"
        self.results["tasks"][0]["candidates"].append(candidate)
        self.save()
        pack = export_review_pack(self.run, self.root / "pack")
        ids = [item["review_id"] for item in json.loads(Path(pack["review_items"]).read_text())["items"]]
        rows = [{"review_id": rid, "reviewer_id": reviewer, **{field: "yes" for field in CRITERIA}} for rid in ids for reviewer in ("A", "B")]
        summary = aggregate_reviews(self.run, [self.review_file(rows)], self.root / "out")
        self.assertEqual(2, summary["methods"]["full"]["candidate_count"])
        self.assertEqual(1, summary["methods"]["full"]["qualified_yield_lower"])

    def test_unknown_id_invalid_score_or_missing_reviewer_is_rejected(self):
        row = self.scores()
        for change in ({"review_id": "unknown"}, {"scope_relevance": "passed"}, {"reviewer_id": ""}):
            with self.subTest(change=change), self.assertRaises(ReviewContractError):
                aggregate_reviews(self.run, [self.review_file([dict(row, **change)])], self.root / "out")

    def test_modified_candidate_invalidates_old_review_and_preserves_existing_scores(self):
        row = self.scores()
        csv_path = self.root / "pack/reviews.csv"
        with csv_path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow(row)
        export_review_pack(self.run, self.root / "pack")
        self.assertIn("checked independently", csv_path.read_text())
        self.results["tasks"][0]["candidates"][0]["inputs"] = {"size": [100]}
        self.save()
        with self.assertRaisesRegex(ReviewContractError, "different candidate content"):
            export_review_pack(self.run, self.root / "pack")
        with self.assertRaisesRegex(ReviewContractError, "unknown review_id"):
            aggregate_reviews(self.run, [self.review_file([row])], self.root / "out")

    def test_candidate_cap_contract_is_not_silent_filtering(self):
        original = self.results["tasks"][0]["candidates"][0]
        self.results["tasks"][0]["candidates"] = [dict(original, candidate_id=str(index)) for index in range(6)]
        self.save()
        with self.assertRaisesRegex(ReviewContractError, "at most 5"):
            export_review_pack(self.run, self.root / "pack")

    def test_manifest_preserves_actual_three_candidate_cap_and_blank_scores(self):
        self.results["metadata"]["max_candidates"] = 3
        original = self.results["tasks"][0]["candidates"][0]
        self.results["tasks"][0]["candidates"] = [dict(original, candidate_id=str(index)) for index in range(3)]
        self.save()
        pack = export_review_pack(self.run, self.root / "pack")
        manifest = json.loads((self.root / "pack/run-manifest.json").read_text())
        self.assertEqual(3, manifest["candidate_cap_per_task"])
        self.assertEqual(3, manifest["task_count"])
        self.assertEqual(3, pack["candidate_count"])
        with Path(pack["reviews_csv"]).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(3, len(rows))
        self.assertTrue(all(not row[field] for row in rows for field in CRITERIA))

    def test_actual_cap_rejects_overflow_in_export_and_aggregation(self):
        self.results["metadata"]["max_candidates"] = 3
        original = self.results["tasks"][0]["candidates"][0]
        self.results["tasks"][0]["candidates"] = [dict(original, candidate_id=str(index)) for index in range(4)]
        self.save()
        with self.assertRaisesRegex(ReviewContractError, "at most 3"):
            export_review_pack(self.run, self.root / "pack")
        with self.assertRaisesRegex(ReviewContractError, "at most 3"):
            aggregate_reviews(self.run, [], self.root / "out")

    def test_metadata_cap_must_be_integer_between_one_and_five(self):
        for cap in [True, 3.0, "3", None, 0, -1, 6]:
            with self.subTest(cap=cap):
                self.results["metadata"]["max_candidates"] = cap
                self.save()
                with self.assertRaisesRegex(ReviewContractError, "metadata.max_candidates"):
                    export_review_pack(self.run, self.root / "pack")

    def test_missing_method_task_cannot_reduce_denominator(self):
        self.results["tasks"] = self.results["tasks"][:1]
        self.save()
        with self.assertRaisesRegex(ReviewContractError, "preserve failed tasks"):
            export_review_pack(self.run, self.root / "pack")

    def test_no_candidates_preserves_known_zero_without_human_claim(self):
        for task in self.results["tasks"]:
            task["candidates"] = []
        self.save()
        summary = aggregate_reviews(self.run, [], self.root / "out")
        self.assertEqual("no_candidates", summary["human_review_status"])
        self.assertFalse(summary["human_conclusions_available"])
        self.assertTrue(all(data["qualified_yield_upper"] == 0 for data in summary["methods"].values()))

    def test_html_escapes_model_content_and_report_does_not_invent_scores(self):
        self.results["tasks"][0]["candidates"][0]["observation"] = '<script>alert("bad")</script>'
        self.save()
        pack = export_review_pack(self.run, self.root / "pack")
        page = Path(pack["reviewer_html"]).read_text()
        self.assertNotIn('<script>alert("bad")</script>', page)
        self.assertIn("&lt;script&gt;", page)
        report = self.root / "report.md"
        write_run_report(self.results, report)
        self.assertIn("人工审查尚未完成", report.read_text())


if __name__ == "__main__":
    unittest.main()
