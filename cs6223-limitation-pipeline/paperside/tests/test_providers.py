import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paperprobe.io import read_json, text_sha256, write_json
from paperprobe.providers import (
    COMPACT_INSTRUCTIONS, BudgetError, BudgetLedger, CodexProvider,
    ProviderError, build_prompt, response_schema,
)


class ProviderTests(unittest.TestCase):
    def make_provider(self, directory, **ledger_options):
        ledger = BudgetLedger(Path(directory) / "budget.json", **ledger_options)
        with patch("paperprobe.providers.shutil.which", return_value="/fixture/codex"), \
                patch("paperprobe.providers.disabled_skill_paths", return_value=["/fixture/skill"]):
            provider = CodexProvider(ledger, model="fixture-fixed-model")
        return provider, ledger

    def simulated_cli(self, *, tool_type=None, returncode=0, usage=None, response=True):
        """Simulate CLI files and event stream without an authenticated invocation."""
        captured = []
        usage = {"input_tokens": 8123, "output_tokens": 321} if usage is None else usage

        def run(command, **kwargs):
            captured.append((command, kwargs))
            if command[1] == "--version":
                return subprocess.CompletedProcess(command, 0, "codex-cli fixture\n", "")
            message_path = Path(command[command.index("--output-last-message") + 1])
            if response:
                write_json(message_path, {"candidates": [], "abstain_reason": "Insufficient supplied evidence"})
            events = []
            if tool_type:
                events.append({"type": "item.completed", "item": {"type": tool_type}})
            events.append({"type": "turn.completed", "usage": usage})
            return subprocess.CompletedProcess(command, returncode, "\n".join(json.dumps(e) for e in events), "fixture stderr")

        return run, captured

    def test_budget_charges_failed_and_completed_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = BudgetLedger(Path(directory) / "budget.json", call_limit=2, token_limit=25000)
            first, _ = ledger.reserve("hello")
            ledger.finish(first, "failed", None, Path(directory))
            second, _ = ledger.reserve("hello")
            ledger.finish(second, "completed", {"input_tokens": 4, "output_tokens": 2}, Path(directory))
            with self.assertRaises(BudgetError):
                ledger.reserve("third")

    def test_code_only_prompt_omits_paper_and_preserves_conditions(self):
        condition = {"condition_id": "c", "path": "index.py", "evidence": {"quote": "if n < 16"}}
        prompt = build_prompt("p", "code_only", {"evidence": [{"quote": "SECRET PAPER SCOPE"}]}, [condition])
        self.assertNotIn("SECRET PAPER SCOPE", prompt)
        self.assertIn("index.py", prompt)
        self.assertIn("Do not use any tools", prompt)
        json.dumps(response_schema())

    def test_tool_events_reject_an_otherwise_valid_response_and_charge_usage(self):
        # Disabled CLI features are defense in depth; the recorded events still
        # have to reject tool-aided output, including a valid response.json.
        for tool_type in ["command_execution", "mcp_tool_call", "web_search", "file_change"]:
            with self.subTest(tool_type=tool_type), tempfile.TemporaryDirectory() as directory:
                provider, ledger = self.make_provider(directory, call_limit=1, token_limit=25000)
                simulated, calls = self.simulated_cli(tool_type=tool_type)
                attempt = Path(directory) / "attempt"
                with patch("paperprobe.providers.subprocess.run", side_effect=simulated):
                    with self.assertRaisesRegex(ProviderError, "Protocol violation"):
                        provider.call("bounded context", attempt)
                budget = read_json(ledger.path)
                self.assertEqual(budget["calls"][0]["status"], "failed")
                self.assertEqual(budget["charged_tokens"], 8444)
                self.assertEqual(budget["calls"][0]["usage"]["input_tokens"], 8123)
                self.assertIn(tool_type, (attempt / "events.jsonl").read_text())
                self.assertTrue((attempt / "response.json").exists())
                self.assertFalse((attempt / "provenance.json").exists())
                self.assertEqual(len(calls), 1)
                with self.assertRaises(BudgetError):
                    ledger.reserve("no automatic free retry")

    def test_cli_failure_with_usage_is_not_a_free_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            provider, ledger = self.make_provider(directory, call_limit=2, token_limit=20000)
            simulated, _ = self.simulated_cli(returncode=1, usage={"input_tokens": 15000, "output_tokens": 6000})
            attempt = Path(directory) / "failed"
            with patch("paperprobe.providers.subprocess.run", side_effect=simulated):
                with self.assertRaisesRegex(ProviderError, "exited with code 1"):
                    provider.call("bounded context", attempt)
            budget = read_json(ledger.path)
            self.assertEqual(budget["calls"][0]["status"], "failed")
            self.assertEqual(budget["charged_tokens"], 21000)
            self.assertTrue(budget["token_budget_exceeded"])
            self.assertEqual((attempt / "stderr.log").read_text(), "fixture stderr")
            with self.assertRaises(BudgetError):
                ledger.reserve("next invocation")

    def test_timeout_retains_reservation_when_actual_usage_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            provider, ledger = self.make_provider(directory, call_limit=1, token_limit=25000)
            with patch("paperprobe.providers.subprocess.run", side_effect=subprocess.TimeoutExpired("fixture", 240)):
                with self.assertRaises(ProviderError):
                    provider.call("bounded context", Path(directory) / "timeout")
            budget = read_json(ledger.path)
            entry = budget["calls"][0]
            self.assertEqual(entry["status"], "failed")
            self.assertTrue(entry["usage_unavailable"])
            self.assertEqual(budget["charged_tokens"], entry["reserved_tokens"])
            with self.assertRaises(BudgetError):
                ledger.reserve("timeout still consumes an invocation")

    def test_missing_response_is_failed_but_preserves_reported_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            provider, ledger = self.make_provider(directory, call_limit=1, token_limit=25000)
            simulated, _ = self.simulated_cli(response=False)
            with patch("paperprobe.providers.subprocess.run", side_effect=simulated):
                with self.assertRaisesRegex(ProviderError, "did not produce the response file"):
                    provider.call("bounded context", Path(directory) / "missing-response")
            entry = read_json(ledger.path)["calls"][0]
            self.assertEqual(entry["status"], "failed")
            self.assertEqual(entry["total_tokens"], 8444)

    def test_success_records_fixed_model_and_compact_instructions(self):
        with tempfile.TemporaryDirectory() as directory:
            provider, ledger = self.make_provider(directory, call_limit=1, token_limit=25000)
            simulated, calls = self.simulated_cli()
            attempt = Path(directory) / "success"
            schema = response_schema(3)
            with patch("paperprobe.providers.subprocess.run", side_effect=simulated):
                response = provider.call("bounded context", attempt, schema)
            self.assertEqual(response["candidates"], [])
            command, invocation = calls[0]
            self.assertIn("--ignore-user-config", command)
            self.assertEqual(command[command.index("--model") + 1], "fixture-fixed-model")
            for feature in ["shell_tool", "multi_agent", "goals"]:
                index = command.index(feature)
                self.assertEqual(command[index - 1], "--disable")
            self.assertIn('skills.config=[{path="/fixture/skill",enabled=false}]', command)
            self.assertEqual(invocation["input"], "bounded context")
            self.assertNotEqual(Path(invocation["cwd"]), attempt)
            self.assertEqual(read_json(attempt / "response-schema.json"), schema)
            self.assertEqual((attempt / "model-instructions.txt").read_text(), COMPACT_INSTRUCTIONS)
            provenance = read_json(attempt / "provenance.json")
            self.assertEqual(provenance["model_selection"], "explicit_fixed_model")
            self.assertEqual(provenance["model_requested"], "fixture-fixed-model")
            self.assertEqual(provenance["instruction_sha256"], text_sha256(COMPACT_INSTRUCTIONS))
            self.assertEqual(provenance["tools_used"], [])
            self.assertEqual(provenance["usage"], {"input_tokens": 8123, "output_tokens": 321})
            self.assertEqual(provenance["cli_version"], "codex-cli fixture")
            self.assertEqual(read_json(ledger.path)["calls"][0]["status"], "completed")

    def test_candidate_cap_is_the_supplied_cap_and_preserves_required_fields(self):
        for cap in [1, 3, 5]:
            with self.subTest(cap=cap):
                schema = response_schema(cap)
                candidates = schema["properties"]["candidates"]
                self.assertEqual(candidates["maxItems"], cap)
                self.assertEqual(candidates.get("minItems", 0), 0)
                self.assertEqual(set(schema["required"]), {"candidates", "abstain_reason"})
                candidate = candidates["items"]
                self.assertEqual(set(candidate["required"]), set(candidate["properties"]))
                self.assertFalse(candidate["additionalProperties"])
                oracle = candidate["properties"]["oracle"]
                self.assertIn("unknown", oracle["properties"]["type"]["enum"])
                self.assertEqual(set(oracle["required"]), set(oracle["properties"]))


if __name__ == "__main__":
    unittest.main()
