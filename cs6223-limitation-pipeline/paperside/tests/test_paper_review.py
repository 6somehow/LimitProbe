import unittest

from paperprobe.paper_review import prompt_records, validate_atomicity, validate_coverage


class PaperReviewTest(unittest.TestCase):
    def setUp(self):
        self.pages = ["Initialize every work item. Pop a work item.", "Return the graph."]
        self.original = dict(id="M01-B01", behavior="Initialize and pop",
                             precondition="Graph", kind="mechanism")
        self.catalog = {self.original["id"]: self.original}
        self.mechanisms = {"M01": dict(id="M01", name="Traversal")}
        self.replacement = dict(behavior="Initialize every work item", precondition="Graph",
                                basis="explicit", kind="mechanism", search_terms=["work item"],
                                evidence=[dict(page=1, quote="Initialize every work item.")])

    def decision(self, replacements):
        raw = dict(reviews=[dict(id="M01-B01", issues=["compound"], reason="Two operations",
                                duplicate_of=None, replacements=replacements)])
        return validate_atomicity(raw, [self.original], self.catalog, self.mechanisms,
                                  self.pages, [1])[0]

    def test_partial_invalid_split_does_not_replace_original(self):
        invalid = dict(self.replacement, behavior="Return graph",
                       evidence=[dict(page=1, quote="Return the graph.")])
        result = self.decision([self.replacement, invalid])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(len(result["replacements"]), 1)
        self.assertEqual(len(result["rejected"]), 1)

    def test_replacement_cannot_cite_unseen_page(self):
        invalid = dict(self.replacement, evidence=[dict(page=2, quote="Return the graph.")])
        result = self.decision([invalid])
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("unseen", result["validation_error"])

    def test_valid_split_keeps_origin_and_unique_replacement_ids(self):
        other = dict(self.replacement, behavior="Pop a work item",
                     evidence=[dict(page=1, quote="Pop a work item.")])
        result = self.decision([self.replacement, other])
        self.assertEqual(result["status"], "proposed_revision")
        self.assertEqual([b["id"] for b in result["replacements"]],
                         ["M01-B01-R01", "M01-B01-R02"])

    def test_missing_page_and_unknown_source_ids_are_unresolved(self):
        raw = dict(pages=[dict(page=1, anchors=[dict(name="init", disposition="covered",
                   behavior_ids=["fabricated"], reason="Exists",
                   evidence=self.replacement["evidence"])])], proposals=[])
        result = validate_coverage(raw, [1, 2], self.pages, self.catalog, self.mechanisms, "C01")
        self.assertEqual([p["status"] for p in result["pages"]], ["unresolved", "unresolved"])

    def test_model_input_has_one_evidence_schema(self):
        value = {"evidence": [{"source": "paper", "locator": "PDF p.2", "quote": "Return the graph."}]}
        self.assertEqual(prompt_records(value)["evidence"][0],
                         {"page": 2, "quote": "Return the graph."})

    def test_source_first_inventory_is_not_given_old_decomposition(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from paperprobe.source_coverage import source_first_coverage

        inventory = dict(obligations=[
            dict(page=1, behavior="Initialize every work item", precondition="Graph exists",
                 basis="explicit", kind="mechanism", quote="Initialize every work item.")
        ], pages=[dict(page=1, note="Algorithm", complete=True)])
        alignment = dict(matches=[
            dict(id="C01-O001", status="missing", behavior_ids=[], claim_indices=[],
                 mechanism_id="M01", mechanism_name="Traversal", reason="Not explicitly stated")
        ])
        with TemporaryDirectory() as tmp:
            with patch("paperprobe.source_coverage.call",
                       side_effect=[(inventory, {}), (alignment, {})]) as model:
                result, _ = source_first_coverage([1], self.pages, self.catalog, self.mechanisms,
                                                  [], "model", Path(tmp))
            self.assertEqual(set(model.call_args_list[0].args[2]), {"pages"})
            self.assertEqual(result["proposals"][0]["id"], "C01-O001")
            self.assertEqual(result["pages"][0]["anchors"][0]["disposition"], "gap")
