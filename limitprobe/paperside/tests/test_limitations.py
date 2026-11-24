"""Evidence-contract and inference-boundary checks for the paper workstream."""
import copy
import csv
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

from paperprobe.io import file_sha256, text_sha256, write_json
from paperprobe.limitations import (align_candidates, build_workstream, check_record,
                                    export_handoff, retrieve_statements, source_index)


class PaperLimitationsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.file = self.repo / "core.py"
        self.file.write_text("def search(inputs):\n    return inputs\n", encoding="utf-8")
        for args in (("init",), ("add", "core.py"),
                     ("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")):
            subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, check=True)
        commit = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        self.paper = {"id": "p", "pdf_sha256": "pdf-hash", "repository_commit": commit}
        self.text = "Our method requires equal dimensions. Evaluation tests 50% and 90% sparsity."
        self.pages = [{"page": 1, "text": self.text}]
        quote = "requires equal dimensions"
        code = "    return inputs"
        self.record = {"id": "p-case", "paper_id": "p", "title": "dimension hypothesis", "statement": "Test the dimension assumption.",
                       "kind": "hypothesis", "level": 3, "origin": "development reading", "scope": "The specified operator only.",
                       "assessment": "hypothesis", "search_terms": ["inputs", "search"],
                       "paper_evidence": [{"page": 1, "quote": quote, "sha256": text_sha256(quote),
                                           "paper_sha256": "pdf-hash", "role": "context"}],
                       "code_evidence": [{"path": "core.py", "line_start": 2, "line_end": 2, "quote": code,
                                          "sha256": text_sha256(code), "file_sha256": file_sha256(self.file),
                                          "repository_commit": commit, "role": "context"}],
                       "alignment": {"relation": "unassessed", "rationale": "needs semantic review"},
                       "handoff": {k: "explicit requirement" for k in ("variable", "controls", "observables", "comparison", "oracle_basis", "resources", "dependencies")}}

    def check(self, record=None):
        return check_record(self.record if record is None else record, self.paper, self.pages, self.repo)

    def test_grounded_draft_stays_unreviewed_and_unexecuted(self):
        result = self.check()
        self.assertEqual(result["source_checks"], "passed")
        self.assertEqual(result["semantic_review_status"], "pending")
        self.assertEqual(result["execution_status"], "not_run")
        self.assertFalse(result["confirmed_bug"])
        self.assertFalse(result["independent_gold_label"])

    def test_paper_citation_must_match_the_page_and_pdf(self):
        for key, value in (("page", 2), ("quote", "not in paper"), ("paper_sha256", "different"), ("sha256", "different")):
            record = copy.deepcopy(self.record)
            record["paper_evidence"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(record)

    def test_code_citation_requires_exact_lines_file_and_version(self):
        for key, value in (("line_start", 0), ("line_end", 99), ("quote", "different"), ("repository_commit", "other"), ("file_sha256", "other")):
            record = copy.deepcopy(self.record)
            record["code_evidence"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(record)

    def test_path_escape_and_symlink_escape_rejected(self):
        outside = self.root / "outside.py"
        outside.write_text("unrelated")
        (self.repo / "escape.py").symlink_to(outside)
        for path in ("../outside.py", "escape.py"):
            record = copy.deepcopy(self.record)
            record["code_evidence"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.check(record)

    def test_untracked_source_cannot_be_cited_as_pinned_code(self):
        (self.repo / "new.py").write_text("new")
        self.record["code_evidence"][0]["path"] = "new.py"
        with self.assertRaisesRegex(ValueError, "tracked source"):
            self.check()

    def test_missing_code_is_unmapped_not_a_proven_absence(self):
        self.record["code_evidence"] = []
        self.record["alignment"]["relation"] = "paper_only_located"
        with self.assertRaisesRegex(ValueError, "absence"):
            self.check()
        self.record["alignment"]["search_limitations"] = "Only core.py checked; historical versions not checked."
        self.assertEqual(self.check()["source_checks"], "passed")

    def test_two_sided_relation_requires_both_sources(self):
        self.record["code_evidence"] = []
        self.record["alignment"]["relation"] = "consistent"
        with self.assertRaisesRegex(ValueError, "two-sided"):
            self.check()

    def test_hypothesis_cannot_be_promoted_to_paper_reported_fact(self):
        self.record["assessment"] = "paper_reported"
        with self.assertRaisesRegex(ValueError, "hypothesis"):
            self.check()

    def test_counterevidence_role_is_preserved(self):
        self.record["paper_evidence"][0]["role"] = "counter"
        self.record["assessment"] = "counterevidence_found"
        self.assertEqual(self.check()["source_checks"], "passed")
        self.assertEqual(self.record["paper_evidence"][0]["role"], "counter")

    def test_handoff_requires_an_independent_oracle_requirement(self):
        del self.record["handoff"]["oracle_basis"]
        with self.assertRaisesRegex(ValueError, "oracle_basis"):
            self.check()

    def test_evaluation_points_do_not_become_scope_contracts(self):
        text = "In our evaluation, we tested sparsity ratios from 50% to 90% and observed a speedup."
        results = retrieve_statements("p", [{"page": 1, "text": text}])
        self.assertEqual(len(results), 1)
        self.assertIn("evaluation", results[0]["candidate_kinds"])
        self.assertIsNone(results[0]["scope_contract"])
        self.assertIsNone(results[0]["level"])
        self.assertFalse(results[0]["automatically_confirmed"])

    def test_excluded_checklist_pages_and_reference_passages_are_not_claims(self):
        pages = [{"page": 1, "text": "REFERENCES\nA survey of limitations and evaluation of many systems requires several experiments."},
                 {"page": 2, "text": "A Limitations\nOur method cannot support the adversarial workload described in this section of the appendix."},
                 {"page": 3, "text": "The reviewers require authors to discuss limitations and describe their assumptions in all experiments."}]
        results = retrieve_statements("p", pages, [[3, 3]])
        self.assertEqual({r["pdf_page"] for r in results}, {2})

    def test_source_index_ignores_untracked_and_retrieval_remains_unverified(self):
        (self.repo / "untracked.py").write_text("inputs = 'target answer'")
        index, manifest = source_index(self.repo, ["."])
        self.assertEqual([f["path"] for f in manifest], ["core.py"])
        candidates = align_candidates(index, ["search", "inputs"])
        self.assertEqual(candidates[0]["semantic_alignment"], "unverified")
        self.assertEqual(align_candidates(index, ["unrelatedword"]), [])

    def test_csv_export_keeps_human_status_blank_and_escapes_formulas(self):
        self.record["statement"] = "=UNTRUSTED()"
        export_handoff(self.root, [self.record])
        with (self.root / "paper-limitations.csv").open(encoding="utf-8-sig") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["statement"], "'=UNTRUSTED()")
        with (self.root / "paper-to-code.csv").open(encoding="utf-8-sig") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["semantic_review_status"], "pending")
        self.assertEqual(row["execution_status"], "not_run")

    def test_gqa_control_refutes_universal_incompatibility_without_target_claim(self):
        path = Path(__file__).resolve().parents[1] / "workstreams/zhaopeng/probes/gqa_basis.py"
        spec = importlib.util.spec_from_file_location("gqa_basis", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.probe()
        self.assertTrue(result["group_shared_basis_preserves_dot_products"])
        self.assertTrue(result["mismatched_basis_counterexample_found"])
        self.assertFalse(result["target_repository_executed"])
        self.assertFalse(result["cache_bytes_measured"])


if __name__ == "__main__":
    unittest.main()
