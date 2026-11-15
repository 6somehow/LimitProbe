import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from paperprobe.alignment import attach_source_context, code_context_pool


class SourceContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, path, source):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.encode("utf-8"))

    def condition(self, path, start, end=None):
        return {"condition_id": "cond-1", "path": path, "line_start": start,
                "line_end": start if end is None else end, "expression": "n < 16",
                "kind": "boundary", "threshold": 16, "symbol": "f",
                "evidence": {"quote": "n < 16", "sha256": "original-checksum"}}

    def assert_exact(self, result):
        for item in result["source_context"]:
            source = (self.root / item["path"]).read_bytes().decode("utf-8")
            lines = source.splitlines(keepends=True)
            self.assertEqual(item["quote"], "".join(lines[item["line_start"] - 1:item["line_end"]]))
            self.assertEqual(item["sha256"], hashlib.sha256(item["quote"].encode("utf-8")).hexdigest())
            self.assertEqual(item["applicability_status"], "unverified_neighborhood")
            self.assertTrue(item["limitations"])
        self.assertLessEqual(sum(len(item["quote"]) for item in result["source_context"]), 1200)

    def test_target_neighborhood_and_multiline_python_contracts_are_exact(self):
        self.write("target.py", "def f(n):\n    assert (\n        n > 0\n    ), '维度必须合法'\n    if n < 16:\n        return n\n")
        result = attach_source_context([self.condition("target.py", 5)], self.root)[0]
        self.assertEqual(result["source_context_status"], "available")
        self.assertEqual(result["source_context"][0]["kind"], "target_neighborhood")
        contract = result["source_context"][1]
        self.assertEqual((contract["line_start"], contract["line_end"]), (2, 4))
        self.assertIn("维度必须合法", contract["quote"])
        self.assert_exact(result)

    def test_cpp_balanced_macro_ignores_comments_and_strings(self):
        self.write("kernel.cpp", '// TORCH_CHECK(fake > 0);\nconst char *s="assert(fake)";\nTORCH_CHECK(\n  n % 8 == 0,\n  "head size (must be valid)");\nif (n < 16) {}\n')
        result = attach_source_context([self.condition("kernel.cpp", 6)], self.root)[0]
        contracts = [item for item in result["source_context"] if item["kind"] == "nearby_contract_candidate"]
        self.assertEqual(len(contracts), 1)
        self.assertEqual((contracts[0]["line_start"], contracts[0]["line_end"]), (3, 5))
        self.assertEqual(contracts[0]["contract_kind"], "TORCH_CHECK")
        self.assert_exact(result)

    def test_only_three_nearest_candidates_within_eighty_lines(self):
        lines = ["# spacer\n"] * 101
        for line in (1, 20, 40, 80, 97):
            lines[line - 1] = f"assert n != {line}\n"
        lines[99] = "if n < 16:\n"
        lines[100] = "    pass\n"
        self.write("target.py", "".join(lines))
        result = attach_source_context([self.condition("target.py", 100)], self.root)[0]
        contracts = [item for item in result["source_context"] if item["kind"] == "nearby_contract_candidate"]
        self.assertEqual([item["line_start"] for item in contracts], [97, 80, 40])
        self.assert_exact(result)

    def test_raise_candidates_remain_unverified_across_function_boundaries(self):
        self.write("target.py", "def earlier():\n    raise ValueError(\n        'invalid shape'\n    )\n    raise RuntimeError('device unavailable')\ndef later(n):\n    if n < 16:\n        return n\n")
        result = attach_source_context([self.condition("target.py", 7)], self.root)[0]
        contracts = [item for item in result["source_context"] if item["kind"] == "nearby_contract_candidate"]
        self.assertEqual([item["contract_kind"] for item in contracts], ["RuntimeError", "ValueError"])
        self.assertEqual((contracts[1]["line_start"], contracts[1]["line_end"]), (2, 4))
        self.assertTrue(all(item["applicability_status"] == "unverified_neighborhood" for item in contracts))
        self.assert_exact(result)

    def test_path_and_symlink_escapes_do_not_read_external_source(self):
        external = self.root.parent / "external.py"
        external.write_text("secret = 'outside-content'\n", encoding="utf-8")
        (self.root / "escape.py").symlink_to(external)
        for path in ("../external.py", str(external), "escape.py"):
            result = attach_source_context([self.condition(path, 1)], self.root)[0]
            self.assertEqual(result["source_context"], [])
            self.assertEqual(result["source_context_status"], "unavailable")
            self.assertTrue(result["source_context_errors"])
            self.assertNotIn("outside-content", json.dumps(result))

    def test_target_code_is_never_imported_or_executed(self):
        marker = self.root / "ran.txt"
        self.write("danger.py", f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\nassert n > 0\nif n < 16:\n    pass\n")
        result = attach_source_context([self.condition("danger.py", 4)], self.root)[0]
        self.assertFalse(marker.exists())
        self.assert_exact(result)

    def test_character_budget_withholds_entire_large_contract(self):
        self.write("kernel.cu", 'TORCH_CHECK(n > 0, "' + "x" * 1300 + '");\n// spacer\nif (n < 16) {}\n')
        result = attach_source_context([self.condition("kernel.cu", 3)], self.root)[0]
        self.assertTrue(result["source_context_budget_limited"])
        self.assertFalse(any(item["kind"] == "nearby_contract_candidate" for item in result["source_context"]))
        self.assertNotIn("x" * 100, json.dumps(result["source_context"]))
        self.assert_exact(result)

    def test_oversized_target_is_withheld_without_cutting_the_original_condition(self):
        self.write("target.cpp", "if (n < 16) { /* " + "x" * 1300 + " */ }\n")
        original = self.condition("target.cpp", 1)
        result = attach_source_context([original], self.root)[0]
        self.assertEqual(result["source_context"], [])
        self.assertEqual(result["source_context_status"], "withheld_budget")
        self.assertTrue(result["source_context_budget_limited"])
        self.assertEqual(result["evidence"], original["evidence"])

    def test_crlf_and_unicode_quotations_preserve_exact_source_bytes(self):
        self.write("target.py", "assert n > 0  # 合法\r\nif n < 16:\r\n    pass\r\n")
        result = attach_source_context([self.condition("target.py", 2)], self.root)[0]
        self.assertIn("\r\n", result["source_context"][0]["quote"])
        self.assert_exact(result)

    def test_missing_bad_encoding_and_invalid_lines_are_structured(self):
        (self.root / "invalid.py").write_bytes(b"\xff")
        self.write("target.py", "pass\n")
        conditions = [self.condition("missing.py", 1), self.condition("invalid.py", 1),
                      self.condition("target.py", 0), self.condition("target.py", True),
                      self.condition("target.py", 2)]
        results = attach_source_context(conditions, self.root)
        self.assertTrue(all(item["source_context"] == [] for item in results))
        self.assertTrue(all(item["source_context_errors"] for item in results))

    def test_deep_copy_determinism_and_pool_selection_are_preserved(self):
        self.write("target.py", "assert n > 0\nif n < 16:\n    pass\n")
        conditions = [self.condition("target.py", 2)]
        original = copy.deepcopy(conditions)
        first = attach_source_context(conditions, self.root)
        second = attach_source_context(conditions, self.root)
        self.assertEqual(first, second)
        self.assertEqual(conditions, original)
        self.assertEqual([item["condition_id"] for item in code_context_pool({"conditions": first})],
                         [item["condition_id"] for item in code_context_pool({"conditions": conditions})])
        first[0]["evidence"]["quote"] = "changed"
        self.assertEqual(conditions, original)
        self.assertEqual(attach_source_context(second, self.root), second)


if __name__ == "__main__":
    unittest.main()
