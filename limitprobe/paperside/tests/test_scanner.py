import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from paperprobe.scanner import scan_repository


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_python_negative_float_and_declared_integer(self):
        self.write("target.py", "def select(n: int, x: float):\n    if n < -3 and x >= -2.5:\n        return 1\n")
        result = scan_repository(self.root)
        self.assertEqual(result["files_scanned"], 1)
        n, x = result["conditions"]
        self.assertEqual((n["variable"], n["threshold"], n["value_type"]), ("n", -3, "integer"))
        self.assertEqual((x["operator"], x["threshold"], x["value_type"]), (">=", -2.5, "float"))
        self.assertEqual(n["symbol"], "select")
        self.assertEqual(n["activation_preconditions"], ["x >= -2.5"])
        self.assertEqual(n["scope_status"], "unknown")

    def test_chained_comparison_is_normalized_and_preserves_other_guard(self):
        self.write("range.py", "if 0 <= size < 10:\n    pass\n")
        lower, upper = scan_repository(self.root)["conditions"]
        self.assertEqual((lower["variable"], lower["operator"], lower["threshold"]), ("size", ">=", 0))
        self.assertEqual((upper["operator"], upper["threshold"]), ("<", 10))
        self.assertEqual(lower["activation_preconditions"], ["size < 10"])
        self.assertEqual(upper["activation_preconditions"], ["0 <= size"])

    def test_multiline_unicode_quotes_ranges_and_hash(self):
        source = "def 检查(n: int, enabled: bool):\n    if (\n        n < 32\n        and enabled\n    ):\n        pass\n"
        self.write("unicode.py", source)
        condition = scan_repository(self.root)["conditions"][0]
        evidence = condition["evidence"]
        self.assertEqual((evidence["line_start"], evidence["line_end"]), (3, 4))
        self.assertIn(evidence["quote"], "\n".join(source.splitlines()[2:4]))
        self.assertEqual(evidence["sha256"], hashlib.sha256(evidence["quote"].encode()).hexdigest())
        self.assertEqual(condition["symbol"], "检查")

    def test_bool_annotation_and_unknown_truthiness_are_distinguished(self):
        self.write("flags.py", "def choose(enabled: bool, collection):\n    if not enabled:\n        pass\n    if collection:\n        pass\n")
        enabled, collection = scan_repository(self.root)["conditions"]
        self.assertEqual((enabled["kind"], enabled["value_type"], enabled["operator"]), ("configuration", "boolean", "falsy"))
        self.assertEqual(collection["value_type"], "unknown")

    def test_nonliteral_threshold_and_derived_input_are_not_fabricated(self):
        self.write("complex.py", "if n < get_threshold():\n    pass\nif len(items) > 8:\n    pass\n")
        conditions = scan_repository(self.root)["conditions"]
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["variable"], "len(items)")
        self.assertEqual(conditions[0]["input_binding"], "derived_expression")

    def test_or_and_negation_keep_boolean_context(self):
        self.write("logic.py", "if x < 4 or y > 9:\n    pass\nif not (n <= 5):\n    pass\n")
        conditions = scan_repository(self.root)["conditions"]
        self.assertEqual(conditions[0]["boolean_context"], "or")
        self.assertIn("Other disjunct must be false", conditions[0]["activation_preconditions"][0])
        self.assertEqual(conditions[-1]["boolean_context"], "negated")
        self.assertEqual(conditions[-1]["test_expression"], "not n <= 5")

    def test_state_comparison_is_observation_not_transition(self):
        self.write("state.py", "class Session:\n    def step(self):\n        if self.state == 'ready':\n            pass\n")
        condition = scan_repository(self.root)["conditions"][0]
        self.assertEqual((condition["kind"], condition["threshold"]), ("state", "ready"))
        self.assertEqual(condition["symbol"], "Session.step")
        self.assertEqual(condition["verification_status"], "static_observation_not_executed")

    def test_code_is_never_executed(self):
        marker = self.root / "executed"
        self.write("danger.py", f"open({str(marker)!r}, 'w').write('bad')\nif n < 2:\n    pass\n")
        self.assertEqual(len(scan_repository(self.root)["conditions"]), 1)
        self.assertFalse(marker.exists())

    def test_literal_assignment_conflicting_types_are_unknown(self):
        self.write("mixed.py", "enabled = True\nenabled = 'auto'\nif enabled:\n    pass\n")
        self.assertEqual(scan_repository(self.root)["conditions"][0]["value_type"], "unknown")

    def test_parse_failure_is_structured_and_does_not_stop_next_file(self):
        self.write("a.py", "def broken(:\n")
        self.write("b.py", "if n < 3:\n    pass\n")
        result = scan_repository(self.root)
        self.assertEqual(result["files_scanned"], 2)
        self.assertEqual(len(result["conditions"]), 1)
        self.assertEqual(result["errors"][0]["code"], "SyntaxError")

    def test_triton_uses_python_ast_not_execution(self):
        self.write("kernel.py", "import triton\n@triton.jit\ndef kernel(n):\n    if n <= 64:\n        pass\n")
        condition = scan_repository(self.root)["conditions"][0]
        self.assertEqual(condition["language"], "triton_python")
        self.assertEqual(condition["parser"], "python_ast")

    def test_cpp_cuda_multiline_and_comment_masking(self):
        source = """// if (fake < 100) { }
const char *s = "if (also_fake < 9)";
__global__ void kernel(float x, int n, bool enabled) {
    if (n < 32 &&
        x >= -2.5f) { }
    if (enabled) { }
}
"""
        self.write("kernel.cu", source)
        conditions = scan_repository(self.root)["conditions"]
        self.assertEqual([item["variable"] for item in conditions], ["n", "x", "enabled"])
        self.assertEqual(conditions[1]["threshold"], -2.5)
        self.assertEqual(conditions[1]["numeric_format"], "float32")
        self.assertEqual(conditions[2]["value_type"], "boolean")
        self.assertEqual(conditions[0]["language"], "cuda")
        quote = conditions[0]["evidence"]["quote"]
        self.assertIn(quote, "\n".join(source.splitlines()[3:5]))

    def test_cpp_rejects_arithmetic_fragments(self):
        self.write("math.cpp", "void f(int n, int stride, int x) {\n if (n / x < 3) {}\n if (n < 32 * stride) {}\n if (n < 32) {}\n}\n")
        conditions = scan_repository(self.root)["conditions"]
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["threshold"], 32)

    def test_cpp_string_state_and_raw_string_are_distinguished(self):
        self.write("state.cpp", 'const char *s=R"tag(if (fake < 1))tag";\nvoid f() { if (state == "ready") {} }\n')
        conditions = scan_repository(self.root)["conditions"]
        self.assertEqual(len(conditions), 1)
        self.assertEqual((conditions[0]["kind"], conditions[0]["threshold"]), ("state", "ready"))

    def test_cpp_integral_radix_and_float_suffix(self):
        self.write("numbers.cpp", "void f(int n, float x) { if (n < 010) {} if (n > 0x10U) {} if (x < 0.1f) {} }\n")
        conditions = scan_repository(self.root)["conditions"]
        self.assertEqual([item["threshold"] for item in conditions[:2]], [8, 16])
        self.assertEqual(conditions[2]["numeric_format"], "float32")
        self.assertNotEqual(conditions[2]["threshold"], 0.1)

    def test_limits_include_paths_and_symlink_escape(self):
        self.write("a.py", "if n < 1:\n    pass\n")
        self.write("sub/b.py", "if n < 2:\n    pass\n")
        self.write(".git/hidden.py", "if n < 999:\n    pass\n")
        self.write("large.py", "#" * 1000)
        (self.root / "escape.py").symlink_to("/etc/passwd")
        result = scan_repository(self.root, max_files=1)
        self.assertEqual(result["files_scanned"], 1)
        self.assertTrue(result["truncated"])
        filtered = scan_repository(self.root, include_paths=["sub", "../outside"])
        self.assertEqual(filtered["files_scanned"], 1)
        self.assertEqual(filtered["conditions"][0]["path"], "sub/b.py")
        self.assertTrue(any(item["code"] == "outside_repository" for item in filtered["errors"]))
        limited = scan_repository(self.root, max_file_bytes=100)
        self.assertTrue(any(item["code"] == "file_too_large" for item in limited["errors"]))
        self.assertEqual([item["threshold"] for item in limited["conditions"]], [1, 2])

    def test_results_are_deterministic_and_json_serializable(self):
        self.write("target.py", "if n >= 4:\n    pass\n")
        first, second = scan_repository(self.root), scan_repository(self.root)
        self.assertEqual(first, second)
        json.dumps(first, allow_nan=False)

    def test_missing_repo_and_invalid_limits(self):
        self.assertEqual(scan_repository(self.root / "missing")["errors"][0]["code"], "not_directory")
        with self.assertRaises(ValueError):
            scan_repository(self.root, max_files=-1)
        with self.assertRaises(ValueError):
            scan_repository(self.root, max_file_bytes=0)


if __name__ == "__main__":
    unittest.main()
