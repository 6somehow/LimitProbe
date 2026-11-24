import copy
import json
import unittest
from html.parser import HTMLParser

from paperprobe.review_ui import CRITERIA, render_review_html


class ReviewMarkup(HTMLParser):
    """Inspect the portable markup without evaluating reviewer JavaScript."""
    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.details = []
        self.depth = 0
        self.suppressed = 0
        self.visible = []
        self.hidden = []
        self.cards = []
        self.selects = []
        self.options = []
        self.textareas = []
        self.links = []
        self.raw_json = []
        self.raw_parts = None
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "details":
            self.details.append(values)
            self.depth += 1
        elif tag in {"style", "script"}:
            self.suppressed += 1
        elif tag == "article":
            self.cards.append(values)
        elif tag == "select":
            self.selects.append(values)
        elif tag == "option":
            self.options.append(values)
        elif tag == "textarea":
            self.textareas.append(values)
        elif tag == "a":
            self.links.append(values)
        elif tag == "pre" and values.get("class") == "raw-json":
            self.raw_parts = []

    def handle_endtag(self, tag):
        if tag == "details":
            self.depth -= 1
        elif tag in {"style", "script"}:
            self.suppressed -= 1
        elif tag == "pre" and self.raw_parts is not None:
            self.raw_json.append(json.loads(''.join(self.raw_parts)))
            self.raw_parts = None

    def handle_data(self, data):
        if self.raw_parts is not None:
            self.raw_parts.append(data)
        if not self.suppressed:
            (self.hidden if self.depth else self.visible).append(data)


def review_item():
    code = {"path": "kernel.py", "line_start": 20, "line_end": 21,
            "quote": "if n < 16 and enabled:\n    return n", "sha256": "code-hash-only-in-details"}
    paper = {"page": 4, "quote": "The mechanism supports bounded dimensions.",
             "sha256": "paper-hash-only-in-details", "evidence_id": "paper-e1", "paper_id": "demo"}
    target = {
        "path": "kernel.py", "line_start": 20, "line_end": 21, "symbol": "forward",
        "expression": "n < 16", "test_expression": "n < 16 and enabled", "variable": "n",
        "value_type": "integer", "input_binding": "unconfirmed",
        "activation_preconditions": ["enabled is true"], "limitations": ["target scope is unverified"],
        "backend": "original-parser-metadata", "metadata_extra": {"nested": [False, None, 17]},
        "evidence": code,
        "source_context": [{"path": "kernel.py", "line_start": 15, "line_end": 15,
                            "quote": "assert n % 8 == 0  # original nearby contract",
                            "sha256": "context-hash-only-in-details",
                            "applicability_status": "unverified_neighborhood",
                            "limitations": ["nearby applicability unverified"]}],
    }
    return {
        "review_id": "review-demo", "paper_id": "demo",
        "candidate": {
            "strategy": "boundary", "inputs": [{"n": 8}, {"n": 16}, {"n": 24}],
            "preconditions": ["Use a valid adapter setup"], "target_condition": target,
            "observation": "Record the predicate and selected branch.",
            "paper_evidence": [paper], "code_evidence": code,
            "oracle": {"type": "reachability", "status": "proposed",
                       "relation": "Record outcomes without asserting functional correctness.",
                       "preconditions": ["Maintain matched setup"], "limitations": ["oracle has not been executed"],
                       "evidence": [paper, code], "semantic_validation_status": "unknown"},
            "scope_status": "unknown", "limitations": ["external input binding requires review"],
        },
        "source_reference": {"pdf_path": "/tmp/demo/paper.pdf", "repo_path": "/tmp/demo/repo",
                             "paper_url": "https://example.org/paper", "commit": "pinned-commit-123",
                             "paper_sha256": "full-source-reference-hash"},
    }


class ReviewUiTests(unittest.TestCase):
    def test_core_relation_and_limits_are_visible_metadata_is_collapsed(self):
        page = render_review_html([review_item()], "run-demo")
        markup = ReviewMarkup(page)
        visible, hidden = ''.join(markup.visible), ''.join(markup.hidden)
        for text in ["kernel.py", "行 20–21", "forward", "n < 16 and enabled", "integer", "unconfirmed",
                     "enabled is true", "Record the predicate", "第 4 页", "bounded dimensions",
                     "pinned-commit-123", "reachability", "proposed", "Record outcomes without",
                     "Maintain matched setup", "oracle has not been executed", "target scope is unverified",
                     "external input binding requires review"]:
            self.assertIn(text, visible)
        for text in ["code-hash-only-in-details", "paper-hash-only-in-details", "context-hash-only-in-details",
                     "original-parser-metadata", "original nearby contract", "full-source-reference-hash"]:
            self.assertNotIn(text, visible)
            self.assertIn(text, hidden)
        self.assertTrue(markup.details)
        self.assertTrue(all("open" not in attrs for attrs in markup.details))

    def test_full_target_and_references_can_be_recovered_without_mutation(self):
        item = review_item()
        original = copy.deepcopy(item)
        markup = ReviewMarkup(render_review_html([item], "run-demo"))
        self.assertEqual(item, original)
        self.assertIn(item["candidate"]["target_condition"], markup.raw_json)
        self.assertIn(item["candidate"]["target_condition"]["source_context"][0], markup.raw_json)
        self.assertIn(item["candidate"]["code_evidence"], markup.raw_json)
        self.assertIn(item["candidate"]["paper_evidence"][0], markup.raw_json)
        self.assertIn(item["candidate"]["oracle"], markup.raw_json)
        self.assertIn("file:///tmp/demo/paper.pdf", [attrs.get("href") for attrs in markup.links])
        self.assertIn("https://example.org/paper", [attrs.get("href") for attrs in markup.links])

    def test_scores_follow_summary_and_precede_long_evidence(self):
        page = render_review_html([review_item()], "run-demo")
        self.assertLess(page.index('<div class="candidate-summary">'), page.index('<div class="review-controls">'))
        self.assertLess(page.index('<div class="review-controls">'), page.index('<div class="evidence">'))
        self.assertLess(page.index('<textarea data-field="reason"'), page.index("The mechanism supports bounded dimensions."))

    def test_untrusted_values_are_escaped_even_in_raw_json_and_attributes(self):
        item = review_item()
        attack = '<script>alert("bad")</script><img src=x onerror="bad()">'
        item["review_id"] = 'review-" onmouseover="bad()'
        item["paper_id"] = attack
        item["candidate"]["observation"] = attack
        item["candidate"]["oracle"]["relation"] = attack
        item["candidate"]["paper_evidence"][0]["quote"] = attack
        item["candidate"]["target_condition"]["source_context"][0]["quote"] = attack
        page = render_review_html([item], "run-</script><img src=x onerror=bad()>")
        markup = ReviewMarkup(page)
        self.assertNotIn(attack, page)
        self.assertNotIn('<img src=x', page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("\\u003c/script>", page)
        self.assertEqual(markup.cards[0]["data-review-id"], item["review_id"])
        self.assertNotIn("onmouseover", markup.cards[0])
        self.assertIn(item["candidate"]["target_condition"], markup.raw_json)

    def test_forty_five_candidates_keep_existing_controls_blank_and_identifiers(self):
        items = []
        for index in range(45):
            item = review_item()
            item["review_id"] = "review-" + str(index)
            items.append(item)
        page = render_review_html(items, "run-many")
        markup = ReviewMarkup(page)
        self.assertEqual(len(markup.cards), 45)
        self.assertEqual([attrs["data-review-id"] for attrs in markup.cards], [item["review_id"] for item in items])
        self.assertEqual([attrs["data-field"] for attrs in markup.selects], list(CRITERIA) * 45)
        self.assertEqual([attrs["data-field"] for attrs in markup.textareas], ["reason"] * 45)
        self.assertTrue(all("value" not in attrs for attrs in markup.selects))
        self.assertTrue(all("selected" not in attrs for attrs in markup.options))
        self.assertEqual([attrs["value"] for attrs in markup.options], ["", "yes", "no", "unknown"] * 270)
        for text in ['id="reviewer"', 'id="exportJson"', 'id="exportCsv"', 'id="importFile"',
                     'storagePrefix="paperprobe-review:"+cfg.run_id+":"', 'reviewer.onchange=switchReviewer',
                     'localStorage.getItem(storagePrefix+activeReviewer)', 'card.dataset.reviewId']:
            self.assertIn(text, page)

    def test_legacy_partial_evidence_and_missing_values_remain_reviewable(self):
        item = review_item()
        item["candidate"]["target_condition"] = "n < 16"
        item["candidate"]["code_evidence"] = [{"path": "legacy.py", "line": 7, "quote": "if n < 16:", "commit": "legacy-commit"}]
        item["candidate"]["paper_evidence"] = []
        item["candidate"]["oracle"] = None
        page = render_review_html([item], "run-legacy")
        visible = ''.join(ReviewMarkup(page).visible)
        for text in ["n < 16", "legacy.py · 行 7", "legacy-commit", "未提供；不能由此自动判定不合格"]:
            self.assertIn(text, visible)
        self.assertIn("本 run 没有候选", render_review_html([], "run-empty"))


if __name__ == "__main__":
    unittest.main()
