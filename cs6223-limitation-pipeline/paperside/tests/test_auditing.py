import copy
import json
import tempfile
import unittest
from pathlib import Path

from paperprobe.auditing import audit_run
from paperprobe.batching import build_batch_prompt
from paperprobe.io import read_json, text_sha256, write_json


class AuditingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Path(self.temp.name) / "run"
        self.methods = ["full", "code_only", "direct"]
        self.paper_ids = [f"paper-{i}" for i in range(5)]
        self.contexts = [{
            "paper_id": pid,
            "code_conditions": [{"condition_id": f"condition-{pid}", "evidence": {"quote": "if n < 16:"}}],
            "paper_evidence": [{"paper_id": pid, "evidence_id": f"evidence-{pid}", "quote": "The supported domain is bounded."}],
        } for pid in self.paper_ids]
        self.results = {
            "run_id": "audit-fixture", "backend": "codex", "methods": self.methods,
            "tasks": [{"task_id": pid, "paper_id": pid, "method": method, "status": "completed", "candidates": [{"candidate_id": pid, "checks": {"static_status": "passed"}}], "duration_seconds": 99} for pid in self.paper_ids for method in self.methods],
            "metadata": {
                "max_candidates": 3, "model_requested": "fixed-model", "human_review_status": "pending", "runtime_verification": False,
                "protocol": {"paper_ids": self.paper_ids, "methods": self.methods, "max_candidates": 3, "instruction_sha256": "instruction-hash"},
                "batches": [],
            },
        }
        for number, method in enumerate(self.methods, 1):
            attempt = self.attempt(method)
            prompt = build_batch_prompt(method, self.contexts, 3)
            attempt.mkdir(parents=True)
            (attempt / "prompt.txt").write_text(prompt)
            usage = {"input_tokens": 100, "output_tokens": 10, "cached_input_tokens": 25}
            write_json(attempt / "response.json", {"papers": [{"paper_id": pid, "candidates": [{}], "abstain_reason": ""} for pid in self.paper_ids]})
            write_json(attempt / "provenance.json", {"call_id": number, "model_requested": "fixed-model", "instruction_sha256": "instruction-hash", "cli_version": "fixture-cli", "tools_used": [], "prompt_sha256": text_sha256(prompt), "usage": usage})
            self.results["metadata"]["batches"].append({"method": method, "call_id": number, "status": "completed", "usage": usage, "duration_seconds": 2})
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def attempt(self, method):
        return self.run / "model/batches" / method / "attempt-1"

    def save(self):
        write_json(self.run / "results.json", self.results)

    def mutate_prompt(self, method, contexts):
        attempt = self.attempt(method)
        prompt = build_batch_prompt(method, contexts, 3)
        (attempt / "prompt.txt").write_text(prompt)
        provenance = read_json(attempt / "provenance.json")
        provenance["prompt_sha256"] = text_sha256(prompt)
        write_json(attempt / "provenance.json", provenance)

    def check_status(self, report, name):
        return next(c["status"] for c in report["checks"] if c["name"] == name)

    def test_fair_recorded_run_counts_costs_once_and_never_rates_quality(self):
        report = audit_run(self.run)
        self.assertEqual(report["audit_status"], "pass")
        self.assertEqual(report["denominator"]["expected_task_count"], 15)
        self.assertEqual(report["denominator"]["candidate_cap_per_task"], 3)
        self.assertEqual(report["resources"]["recorded_invocation_count"], 3)
        self.assertEqual(report["resources"]["known_sums"]["total_tokens"], 330)
        self.assertEqual(report["resources"]["known_sums"]["cached_input_tokens"], 75)
        self.assertEqual(report["resources"]["known_sums"]["duration_seconds"], 6)
        self.assertEqual(report["methods"]["full"]["candidate_count"], 5)
        self.assertEqual(report["methods"]["full"]["static_status_counts"], {"passed": 5})
        self.assertEqual(report["methods"]["full"]["quality_conclusion"], "not_assessed")
        self.assertEqual(report["human_review_status"], "pending")
        self.assertFalse(report["sut_executed_by_this_audit"])
        self.assertIn("not independent", report["generation_dependence"])
        self.assertTrue((self.run / "experiment-audit.json").exists())
        self.assertIn("不是质量结论", (self.run / "experiment-audit.md").read_text())

    def test_paper_context_mismatch_is_rejected_even_with_correct_prompt_hash(self):
        contexts = copy.deepcopy(self.contexts)
        contexts[0]["paper_evidence"][0]["quote"] = "Counterfactual paper claim"
        self.mutate_prompt("direct", contexts)
        report = audit_run(self.run)
        self.assertEqual(report["audit_status"], "fail")
        self.assertEqual(self.check_status(report, "full_direct:paper_evidence"), "fail")
        self.assertEqual(self.check_status(report, "prompt_hash:direct"), "pass")

    def test_code_only_paper_leak_and_unequal_code_pools_fail(self):
        # Manually adulterate serialized DATA after the builder removes paper evidence.
        attempt = self.attempt("code_only")
        prompt = (attempt / "prompt.txt").read_text()
        prefix, data_text = prompt.split("\nDATA:\n", 1)
        data = json.loads(data_text)
        data["papers"][0]["paper_evidence"] = self.contexts[0]["paper_evidence"]
        data["papers"][1]["code_conditions"][0]["evidence"]["quote"] = "Different code pool"
        changed = prefix + "\nDATA:\n" + json.dumps(data)
        (attempt / "prompt.txt").write_text(changed)
        provenance = read_json(attempt / "provenance.json")
        provenance["prompt_sha256"] = text_sha256(changed)
        write_json(attempt / "provenance.json", provenance)
        report = audit_run(self.run)
        self.assertEqual(self.check_status(report, "code_only:no_paper_evidence"), "fail")
        self.assertEqual(self.check_status(report, "all_arms:same_code"), "fail")

    def test_failed_missing_raw_records_remain_unknown_and_keep_zero_task_denominator(self):
        for task in self.results["tasks"]:
            if task["method"] == "full":
                task.update(status="failed", candidates=[])
        self.results["metadata"]["batches"][0] = {"method": "full", "status": "failed", "duration_seconds": 2}
        self.save()
        for filename in ["prompt.txt", "provenance.json", "response.json"]:
            (self.attempt("full") / filename).unlink()
        report = audit_run(self.run)
        self.assertEqual(report["audit_status"], "unknown")
        self.assertEqual(report["denominator"]["recorded_task_count"], 15)
        self.assertEqual(report["methods"]["full"]["candidate_count"], 0)
        self.assertEqual(report["methods"]["full"]["generation_status_counts"], {"failed": 5})
        self.assertEqual(self.check_status(report, "raw_response:full"), "unknown")
        self.assertEqual(self.check_status(report, "same_provenance:model_requested"), "unknown")
        self.assertFalse(report["resources"]["complete"])
        self.assertEqual(report["resources"]["known_sums"]["total_tokens"], 220)

    def test_missing_task_record_and_over_cap_are_failures(self):
        self.results["tasks"].pop()
        self.results["tasks"][0]["candidates"] *= 4
        self.save()
        report = audit_run(self.run)
        self.assertEqual(report["audit_status"], "fail")
        self.assertEqual(self.check_status(report, "task_denominator"), "fail")
        self.assertEqual(self.check_status(report, "candidate_cap"), "fail")
        self.assertEqual(report["denominator"]["expected_task_count"], 15)

    def test_conflicting_provenance_and_tool_usage_fail(self):
        path = self.attempt("direct") / "provenance.json"
        provenance = read_json(path)
        provenance.update(model_requested="other-model", tools_used=["web_search"])
        write_json(path, provenance)
        report = audit_run(self.run)
        self.assertEqual(report["audit_status"], "fail")
        self.assertEqual(self.check_status(report, "same_provenance:model_requested"), "fail")
        self.assertEqual(self.check_status(report, "tools:direct"), "fail")

    def test_duplicate_cost_record_is_counted_once_but_conflicting_duplicate_fails(self):
        duplicate = copy.deepcopy(self.results["metadata"]["batches"][0])
        self.results["metadata"]["batches"].append(duplicate)
        self.save()
        report = audit_run(self.run)
        self.assertEqual(report["resources"]["known_sums"]["total_tokens"], 330)
        self.assertEqual(report["audit_status"], "pass")
        duplicate["usage"]["output_tokens"] = 999
        self.save()
        report = audit_run(self.run)
        self.assertEqual(report["audit_status"], "fail")
        self.assertEqual(report["resources"]["known_sums"]["total_tokens"], 330)

    def test_raw_response_overflow_and_missing_cached_usage_are_not_passed(self):
        response_path = self.attempt("full") / "response.json"
        response = read_json(response_path)
        response["papers"][0]["candidates"] = [{}] * 4
        write_json(response_path, response)
        # Missing cached usage is unknown, not an invented zero.
        for batch in self.results["metadata"]["batches"]:
            batch["usage"].pop("cached_input_tokens")
            path = self.attempt(batch["method"]) / "provenance.json"
            provenance = read_json(path)
            provenance["usage"] = batch["usage"]
            write_json(path, provenance)
        self.save()
        report = audit_run(self.run / "results.json", Path(self.temp.name) / "audit")
        self.assertEqual(self.check_status(report, "raw_response:full"), "fail")
        self.assertEqual(self.check_status(report, "shared_invocation_costs"), "unknown")
        self.assertTrue(all(row["cached_input_tokens"] is None for row in report["resources"]["invocations"]))

    def test_completed_outputs_cannot_invent_candidates_absent_from_raw_response(self):
        self.results["tasks"][0]["candidates"].append({"candidate_id": "invented"})
        self.save()
        report = audit_run(self.run)
        self.assertEqual(self.check_status(report, "normalized_output_count:full"), "fail")

    def test_exact_context_comparison_preserves_boolean_vs_numeric_types(self):
        for context in self.contexts:
            context["code_conditions"][0]["threshold"] = 1
        for method in self.methods:
            self.mutate_prompt(method, self.contexts)
        changed = copy.deepcopy(self.contexts)
        changed[0]["code_conditions"][0]["threshold"] = True
        self.mutate_prompt("direct", changed)
        report = audit_run(self.run)
        self.assertEqual(self.check_status(report, "full_direct:code_conditions"), "fail")


if __name__ == "__main__":
    unittest.main()
