import unittest

from paperprobe.papers import build_profile, retrieve_evidence
from paperprobe.io import text_sha256


class PaperTests(unittest.TestCase):
    def test_experiment_range_not_promoted_to_contract(self):
        text = "We evaluate attention on sequences between 16 and 128 tokens. The sparse kernel requires aligned blocks and supports causal attention only."
        profile = build_profile("demo", [{"page": 2, "text": text}], "digest", max_claims=5)
        self.assertEqual(profile["scope_constraints"], [])
        self.assertTrue(profile["evidence"])
        for e in profile["evidence"]:
            self.assertIn(e["quote"], text)
            self.assertEqual(e["sha256"], text_sha256(e["quote"]))
            self.assertEqual(e["review_status"], "pending")

    def test_retrieval_relevance_and_stable_identity(self):
        pages = [{"page": 1, "text": "The cache requires token prefetching during attention computation. The index supports insertion and split adaptation for numeric keys."}]
        a = build_profile("demo", pages, "digest")
        b = build_profile("demo", pages, "digest")
        self.assertEqual(a, b)
        selected = retrieve_evidence(a, "index insertion split", 1)
        self.assertIn("index", selected[0]["quote"])


if __name__ == "__main__":
    unittest.main()
