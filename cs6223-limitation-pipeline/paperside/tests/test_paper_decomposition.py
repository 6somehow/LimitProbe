import unittest

from paperprobe.paper_decomposition import inventory, split_group


class PaperDecompositionTest(unittest.TestCase):
    def setUp(self):
        self.pages = ["Initialize every graph node. Remove one graph node.", "Unclassified page."]
        self.quote = [{"page": 1, "quote": "Initialize every graph node."}]
        self.mechanism = dict(name="Graph traversal", description="Walk graph", pages=[1],
                              depends_on=[], evidence=self.quote)

    def test_missing_page_and_rejected_topic_stay_visible(self):
        bad = dict(self.mechanism, name="Fabricated", evidence=[dict(page=2, quote="Missing citation.")])
        mapped = inventory(dict(mechanisms=[self.mechanism, bad], claims=[], coverage=[
            dict(page=1, role="technical", note="Algorithm", topics=["Graph traversal", "Fabricated"])
        ]), self.pages)
        self.assertEqual(mapped["coverage"][0]["mechanisms"], ["M01"])
        self.assertEqual(mapped["coverage"][0]["unresolved_topics"], ["Fabricated"])
        self.assertEqual(mapped["coverage"][1]["role"], "unreviewed")
        self.assertEqual(mapped["rejected"][0]["type"], "mechanism")

    def test_keeps_valid_behavior_and_reports_partial_group(self):
        record = dict(behavior="Initialize nodes", precondition="Graph exists", basis="explicit",
                      kind="mechanism", search_terms=["graph"], evidence=self.quote)
        invalid = dict(record, behavior="Update graph", evidence=[dict(page=2, quote="Initialize every graph node.")])
        group = split_group(dict(groups=[dict(id="M01", behaviors=[record, invalid], open_questions=[])]),
                            dict(self.mechanism, id="M01"), self.pages)
        self.assertEqual(group["status"], "partial")
        self.assertEqual(group["behaviors"][0]["id"], "M01-B01")
        self.assertEqual(len(group["rejected"]), 1)
