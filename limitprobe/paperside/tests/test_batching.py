import copy
import json
import unittest

from paperprobe.batching import (
    BatchContractError, batch_schema, build_batch_prompt, validate_batch_response,
)
from paperprobe.providers import response_schema


class BatchingTests(unittest.TestCase):
    def setUp(self):
        self.ids = [f"paper-{index}" for index in range(5)]
        self.contexts = [{
            "paper_id": pid,
            "code_conditions": [{"condition_id": f"{pid}-condition-{index}", "evidence": {"quote": f"if n < {index}"}, "custom_frozen_field": "preserve"} for index in range(18)],
            "paper_evidence": [{"evidence_id": f"{pid}-evidence-{index}", "quote": f"SECRET-{pid}-{index}"} for index in range(20)],
        } for pid in self.ids]

    def response(self):
        return {"papers": [{"paper_id": pid, "candidates": [{"condition_id": f"{pid}-c"}], "abstain_reason": ""} for pid in self.ids]}

    def test_schema_reuses_candidate_contract_and_exact_paper_count(self):
        schema = batch_schema(self.ids, 3)
        papers = schema["properties"]["papers"]
        self.assertEqual((5, 5), (papers["minItems"], papers["maxItems"]))
        self.assertEqual(self.ids, papers["items"]["properties"]["paper_id"]["enum"])
        self.assertEqual(response_schema(3)["properties"]["candidates"], papers["items"]["properties"]["candidates"])
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(papers["items"]["additionalProperties"])

    def test_full_direct_share_frozen_sources_without_truncation(self):
        original = copy.deepcopy(self.contexts)
        full = build_batch_prompt("full", self.contexts, 5)
        direct = build_batch_prompt("direct", self.contexts, 5)
        full_data = json.loads(full.split("\nDATA:\n", 1)[1])
        direct_data = json.loads(direct.split("\nDATA:\n", 1)[1])
        self.assertEqual(full_data, direct_data)
        self.assertEqual({"papers": self.contexts}, full_data)
        self.assertIn("SECRET-paper-4-19", full)
        self.assertIn("paper-4-condition-17", full)
        self.assertEqual(original, self.contexts)
        self.assertIn("exactly once", full)
        self.assertIn("not independent generation repetitions", full)

    def test_code_only_omits_all_paper_evidence_and_keeps_identical_code(self):
        original = copy.deepcopy(self.contexts)
        prompt = build_batch_prompt("code_only", self.contexts, 5)
        self.assertNotIn("SECRET-", prompt)
        self.assertNotIn("paper-0-evidence", prompt)
        data = json.loads(prompt.split("\nDATA:\n", 1)[1])
        for source, bounded in zip(self.contexts, data["papers"]):
            self.assertEqual([], bounded["paper_evidence"])
            self.assertEqual(source["code_conditions"], bounded["code_conditions"])
        self.assertEqual(original, self.contexts)
        self.assertIn("ALL paper_evidence arrays", prompt)
        self.assertIn("Do not use any tools", prompt)

    def test_valid_response_normalizes_order_and_preserves_empty_abstention(self):
        response = self.response()
        response["papers"].reverse()
        response["papers"][0]["candidates"] = []
        response["papers"][0]["abstain_reason"] = "no supported alignment"
        before = copy.deepcopy(response)
        parsed = validate_batch_response(response, self.ids, 5)
        self.assertEqual(self.ids, list(parsed))
        self.assertEqual([], parsed["paper-4"]["candidates"])
        self.assertEqual("no supported alignment", parsed["paper-4"]["abstain_reason"])
        self.assertEqual(before, response)
        parsed["paper-0"]["candidates"][0]["condition_id"] = "changed"
        self.assertEqual(before, response)

    def test_duplicate_missing_and_unknown_papers_rejected(self):
        response = self.response()
        response["papers"][1]["paper_id"] = "paper-0"
        with self.assertRaisesRegex(BatchContractError, "Duplicate"):
            validate_batch_response(response, self.ids, 5)
        response = self.response()
        response["papers"].pop()
        with self.assertRaisesRegex(BatchContractError, "exactly 5"):
            validate_batch_response(response, self.ids, 5)
        response = self.response()
        response["papers"][0]["paper_id"] = "other-paper"
        with self.assertRaisesRegex(BatchContractError, "Unknown"):
            validate_batch_response(response, self.ids, 5)

    def test_per_paper_candidate_cap_cannot_be_hidden_by_batch_total(self):
        response = self.response()
        response["papers"][0]["candidates"] = [{} for _ in range(6)]
        response["papers"][1]["candidates"] = []
        with self.assertRaisesRegex(BatchContractError, "at most 5"):
            validate_batch_response(response, self.ids, 5)

    def test_malformed_batch_shape_rejected(self):
        for bad in (None, [], {"papers": None}, {"papers": [], "candidates": []}):
            with self.subTest(bad=bad), self.assertRaises(BatchContractError):
                validate_batch_response(bad, self.ids, 5)
        for change in ({"candidates": None}, {"candidates": [None]}, {"abstain_reason": None}, {"extra": "not allowed"}):
            response = self.response()
            response["papers"][0].update(change)
            with self.subTest(change=change), self.assertRaises(BatchContractError):
                validate_batch_response(response, self.ids, 5)

    def test_invalid_frozen_layout_and_cap_rejected(self):
        for ids in ([], ["same", "same"], [None], [" "]):
            with self.subTest(ids=ids), self.assertRaises(BatchContractError):
                batch_schema(ids, 5)
        for cap in (0, 6, True, 1.5):
            with self.subTest(cap=cap), self.assertRaises(BatchContractError):
                batch_schema(self.ids, cap)
        with self.assertRaises(BatchContractError):
            build_batch_prompt("unfair-method", self.contexts, 5)
        duplicate = copy.deepcopy(self.contexts)
        duplicate[1]["paper_id"] = duplicate[0]["paper_id"]
        with self.assertRaises(BatchContractError):
            build_batch_prompt("full", duplicate, 5)


if __name__ == "__main__":
    unittest.main()
