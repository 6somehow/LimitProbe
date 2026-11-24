import unittest

from paperprobe.paper_citation_review import mechanical, validate_reviews
from paperprobe.semantic_audit import freeze


class ModelCitationReviewTest(unittest.TestCase):
    def setUp(self):
        self.pages = ["Algorithm 1. while S /0 do\n10 return G;"]
        self.record = dict(id="M02-B07", evidence=[dict(page=1, quote="return G;")])
        self.verdict = dict(id="M02-B07", support="full", citation_quality="adequate",
            rationale="算法第10行直接返回图。", supported_parts=["返回图"],
            missing_or_overstated=[], evidence=[dict(page=1, kind="algorithm",
                locator="Algorithm 1 line 10", quote="return G;")],
            recommended_statement=None)

    def test_short_exact_quote_does_not_overturn_model_support(self):
        reviewed = validate_reviews({"reviews": [self.verdict]}, [self.record], self.pages, [1])[0]
        self.assertEqual(reviewed["support"], "full")
        self.assertTrue(reviewed["mechanical_original"][0]["short_quote"])
        self.assertTrue(reviewed["mechanical_original"][0]["exact_text_match"])

    def test_visual_format_difference_does_not_overturn_model_support(self):
        record = dict(id="M02-B07", evidence=[dict(page=1, quote="while S ≠ ∅ do")])
        verdict = dict(self.verdict, citation_quality="format_only",
            evidence=[dict(page=1, kind="algorithm", locator="Algorithm 1 line 3", quote="while S ≠ ∅ do")])
        reviewed = validate_reviews({"reviews": [verdict]}, [record], self.pages, [1])[0]
        self.assertEqual(reviewed["support"], "full")
        self.assertFalse(reviewed["mechanical_original"][0]["exact_text_match"])

    def test_exact_quote_does_not_override_partial_semantic_support(self):
        verdict = dict(self.verdict, support="partial", citation_quality="incomplete",
                       missing_or_overstated=["引文未支持其他动作"])
        reviewed = validate_reviews({"reviews": [verdict]}, [self.record], self.pages, [1])[0]
        self.assertEqual(reviewed["support"], "partial")

    def test_missing_or_untraceable_review_is_unresolved(self):
        unseen = dict(self.verdict, evidence=[dict(page=2, kind="text", locator="missing", quote="return G;")])
        for raw in ({"reviews": []}, {"reviews": [unseen]},
                    {"reviews": [self.verdict, self.verdict]}):
            result = validate_reviews(raw, [self.record], self.pages, [1])[0]
            self.assertEqual(result["support"], "unresolved")
            self.assertIsNotNone(result["schema_error"])

    def test_candidate_mode_retains_citation_rejected_by_legacy_strict_mode(self):
        row = dict(claim="Return graph", behavior="Return updated graph", precondition="Worklist empty",
                   basis="explicit", kind="mechanism", search_terms=["return"],
                   evidence=[dict(page=1, quote="return G;")])
        with self.assertRaises(ValueError):
            freeze({"behaviors": [row]}, self.pages)
        records, rejected = freeze({"behaviors": [row]}, self.pages, verify_evidence=False)
        self.assertEqual(len(records), 1)
        self.assertEqual(rejected, [])

    def test_ligature_and_hyphen_normalization_is_only_a_hint(self):
        hints = mechanical([dict(page=1, quote="first decompose")], ["ﬁrst decom-\npose"])
        self.assertFalse(hints[0]["exact_text_match"])
        self.assertTrue(hints[0]["normalized_text_match"])

    def test_omitted_optional_rewrite_does_not_erase_substantive_review(self):
        verdict = {k: v for k, v in self.verdict.items() if k != "recommended_statement"}
        result = validate_reviews({"reviews": [verdict]}, [self.record], self.pages, [1])[0]
        self.assertEqual(result["support"], "full")
        self.assertIsNone(result["recommended_statement"])
        self.assertIsNone(result["schema_error"])
        self.assertTrue(result["schema_normalizations"])
