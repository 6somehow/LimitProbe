import unittest
from unittest.mock import patch

from paperprobe.team_paper_side import evidence, export, extract_model


class TeamPaperSideTests(unittest.TestCase):
    def test_evidence_is_page_bound_and_preserves_original_whitespace(self):
        row = {"evidence": [{"page": 1, "quote": "We evaluate 50 percent sparsity."}]}
        pages = ["We evaluate\n50 percent sparsity.", "Another page."]
        self.assertIn("\n", evidence(row, pages)[0]["quote"])
        row["evidence"][0]["page"] = 2
        with self.assertRaises(ValueError):
            evidence(row, pages)

    def test_evaluation_does_not_become_support_and_model_cannot_supply_binding(self):
        result = export({"id": "paper"}, ["We evaluate 50 percent sparsity."], {
            "eval_points": [{"config": {"sparsity": 0.5},
                             "evidence": [{"page": 1, "quote": "We evaluate 50 percent sparsity."}]}],
            "bindings": [{"paper_term": "sparsity", "code_symbol": "s"}],
        })
        self.assertEqual(result["scope"], [])
        self.assertEqual(result["bindings"], [])
        self.assertEqual(result["eval_points"][0]["config"], {"sparsity": 0.5})

    @patch("paperprobe.team_paper_side.gateway")
    def test_model_records_resolved_id_and_rejects_truncation(self, gateway):
        choice = {"finish_reason": "stop", "message": {"content": '{"claims": []}'}}
        gateway.return_value = {"model": "actual-model", "choices": [choice]}
        body, meta = extract_model(["public paper text"], "gateway-alias")
        self.assertEqual(body, {"claims": []})
        self.assertEqual(meta["resolved_model"], "actual-model")
        self.assertEqual(gateway.call_args.args[0], "/chat/completions")
        choice["finish_reason"] = "length"
        with self.assertRaises(ValueError):
            extract_model(["public paper text"], "gateway-alias")
