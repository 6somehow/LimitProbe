import copy
import tempfile
import unittest
from pathlib import Path

from paperprobe.checks import check_candidate, validate_candidate_shape
from paperprobe.io import text_sha256


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "target.py").write_text("if x < 16:\n    pass\n")
        quote = "x < 16"
        self.candidate = {
            "candidate_id": "c", "paper_id": "p", "strategy": "boundary",
            "inputs": [{"x": 15}, {"x": 16}, {"x": 17}], "preconditions": [],
            "target_condition": {"variable": "x", "threshold": 16},
            "observation": "branch selection", "scope_status": "unknown",
            "code_evidence": {"path": "target.py", "line_start": 1, "line_end": 1, "quote": quote, "sha256": text_sha256(quote)},
            "paper_evidence": [], "oracle": {"type": "reachability", "status": "proposed"},
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_subline_quote_valid_but_semantics_pending(self):
        result = check_candidate(self.candidate, self.root, {"pages": []})
        self.assertEqual(result["static_status"], "passed")
        self.assertEqual(result["runtime_status"], "not_run")
        self.assertEqual(result["human_review_status"], "pending")
        self.assertEqual(next(c for c in result["checks"] if c["name"] == "scope_semantics")["status"], "unknown")

    def test_forged_quote_rejected(self):
        self.candidate["code_evidence"]["quote"] = "x < 32"
        self.candidate["code_evidence"]["sha256"] = text_sha256("x < 32")
        self.assertEqual(check_candidate(self.candidate, self.root, {})["static_status"], "failed")

    def test_path_escape_and_out_of_scope_rejected(self):
        self.candidate["code_evidence"]["path"] = "../secret.py"
        self.candidate["scope_constraints"] = [{"variable": "x", "type": "integer", "minimum": 0, "maximum": 16}]
        result = check_candidate(self.candidate, self.root, {})
        self.assertEqual(result["static_status"], "failed")
        self.assertEqual(next(c for c in result["checks"] if c["name"] == "declared_input_constraints")["status"], "fail")

    def test_nonfinite_values_rejected(self):
        self.candidate["inputs"] = [{"x": float("nan")}]
        self.assertEqual(check_candidate(self.candidate, self.root, {})["static_status"], "failed")

    def test_bad_container_types_remain_failed_candidates_with_reports(self):
        changes = [
            {"code_evidence": None}, {"code_evidence": ["not an object"]},
            {"paper_evidence": None}, {"paper_evidence": "not a list"},
            {"paper_evidence": [None, "not an evidence object", []]},
            {"target_condition": None}, {"target_condition": ["bad condition"]},
            {"target_condition": {"variable": ["x"], "threshold": 16}},
            {"inputs": None}, {"inputs": {"x": 15}}, {"inputs": [None, 17]},
            {"scope_constraints": None}, {"scope_constraints": [None, []]},
            {"oracle": None}, {"oracle": {"status": []}}, {"scope_status": []},
            {"preconditions": None},
        ]
        for change in changes:
            candidate = copy.deepcopy(self.candidate)
            candidate.update(change)
            before = copy.deepcopy(candidate)
            with self.subTest(change=change):
                result = check_candidate(candidate, self.root, {"pages": []})
                self.assertEqual("failed", result["static_status"])
                self.assertEqual("pending", result["human_review_status"])
                self.assertEqual("not_run", result["runtime_status"])
                self.assertTrue(any(check["status"] == "fail" for check in result["checks"]))
                self.assertEqual(candidate, before, "checker must not replace the raw invalid candidate")

    def test_bad_top_level_candidate_does_not_throw(self):
        for value in (None, [], "invalid", 10):
            with self.subTest(value=value):
                self.assertIn("candidate must be an object", validate_candidate_shape(value))
                result = check_candidate(value, self.root, {})
                self.assertEqual("failed", result["static_status"])
                self.assertEqual("unknown", next(c for c in result["checks"] if c["name"] == "oracle_semantics")["status"])

    def test_bad_paper_item_fields_and_extracted_pages_are_reported(self):
        quote = "Supported range"
        evidence = {"quote": quote, "page": 1, "sha256": text_sha256(quote), "paper_id": "p"}
        for page_data in (None, {"pages": None}, {"pages": [None]}, {"pages": [{"page": 1, "text": None}]},
                          {"pages": [{"page": 1, "text": quote}, {"page": 1, "text": "conflicting"}]}):
            self.candidate["paper_evidence"] = [evidence]
            with self.subTest(page_data=page_data):
                result = check_candidate(self.candidate, self.root, page_data)
                self.assertEqual("fail", next(c for c in result["checks"] if c["name"] == "paper_provenance")["status"])
        for change in ({"quote": None}, {"quote": [quote]}, {"page": [1]}, {"page": True}, {"sha256": None}):
            self.candidate["paper_evidence"] = [dict(evidence, **change)]
            with self.subTest(change=change):
                result = check_candidate(self.candidate, self.root, {"pages": [{"page": 1, "text": quote}]})
                self.assertEqual("failed", result["static_status"])

    def test_bad_code_location_types_are_not_promoted_to_provenance_pass(self):
        for change in ({"quote": ["x < 16"]}, {"path": []}, {"line_start": True}, {"line_end": None}):
            candidate = copy.deepcopy(self.candidate)
            candidate["code_evidence"].update(change)
            with self.subTest(change=change):
                result = check_candidate(candidate, self.root, {})
                self.assertEqual("fail", next(c for c in result["checks"] if c["name"] == "code_provenance")["status"])

    def test_malformed_constraints_are_failed_and_boolean_enum_is_not_integer(self):
        for constraint in (
            {"variable": []}, {"variable": "x", "minimum": "zero"},
            {"variable": "x", "maximum": float("nan")}, {"variable": "x", "enum": "123"},
            {"variable": "x", "type": []}, {"variable": "x", "minimum_inclusive": "yes"},
            {"variable": "x", "enum": [True]},
        ):
            candidate = copy.deepcopy(self.candidate)
            candidate["inputs"] = [{"x": 1}]
            candidate["scope_constraints"] = [constraint]
            with self.subTest(constraint=constraint):
                result = check_candidate(candidate, self.root, {})
                self.assertEqual("fail", next(c for c in result["checks"] if c["name"] == "declared_input_constraints")["status"])

    def test_large_json_integers_do_not_crash_float_finiteness_checks(self):
        value = 10 ** 1000
        self.candidate["inputs"] = [{"x": value - 1}, {"x": value + 1}]
        self.candidate["target_condition"]["threshold"] = value
        result = check_candidate(self.candidate, self.root, {})
        self.assertEqual("passed", result["static_status"])
        self.assertEqual("pass", next(c for c in result["checks"] if c["name"] == "boundary_relation")["status"])

    def test_invalid_candidate_does_not_prevent_checking_next_candidate(self):
        invalid = dict(self.candidate, paper_evidence=None)
        results = [check_candidate(candidate, self.root, {}) for candidate in (invalid, self.candidate)]
        self.assertEqual(["failed", "passed"], [result["static_status"] for result in results])


if __name__ == "__main__":
    unittest.main()
