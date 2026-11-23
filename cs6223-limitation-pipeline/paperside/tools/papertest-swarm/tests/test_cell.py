import json
from pathlib import Path

from swarmlab.cell import Cell
from swarmlab.util import dump, sha

PAGE = ("This paper generates valid test cases. The numerical search saves the first valid input "
        "and the differential test replays that saved input. Later inputs are not explored.")


def demo_inputs(root: Path) -> Path:
    folder = root / "inputs" / "demo"
    folder.mkdir(parents=True)
    dump(folder / "paper.json", [{"page": 1, "text": PAGE, "numbered": "1: " + PAGE}])
    dump(folder / "source.json", {"paper_id": "demo", "repo": None, "commit": None,
                                  "pdf_sha256": "0" * 64})
    (folder / "original-source-packet.txt").write_text("")
    return root / "inputs"


class MockClient:
    """Scripted provider: one lead tool round, one delegation, then a final report."""

    def __init__(self, archive: Path):
        self.archive = archive
        self.requests = 0
        self.tokens = 0
        self.usage = []
        self.lead_calls = 0

    def chat(self, messages, tools=None, tool_choice=None, max_tokens=None, thinking=True):
        self.requests += 1
        dump(self.archive / f"request-{self.requests:02d}.json",
             {"messages": messages, "tools": tools or []})
        self.tokens += 1000
        system = messages[0]["content"]
        if system.startswith("You are the worker"):
            payload = {
                "paper_id": "demo", "target_execution": "not_run", "question_answered": True,
                "findings": [{
                    "candidate_id": "W1",
                    "name": "only the first saved input is replayed",
                    "causal_argument": "the search stops at the first valid input",
                    "conditions": "same generated graph",
                    "consequence": "later valid inputs are untested",
                    "paper_quotes": [{"page_number": 1, "text": "saves the first valid input"}],
                    "source_spans": [],
                    "comparison": {"fixed": "graph", "vary": "input",
                                   "baseline": "first input", "observable": "coverage",
                                   "refuted_if": "no new bug"},
                }],
            }
        else:
            self.lead_calls += 1
            if self.lead_calls == 1:
                return self._reply({"role": "assistant", "content": "", "tool_calls": [{
                    "id": "c1", "type": "function",
                    "function": {"name": "read_paper", "arguments": '{"page": 1}'}}]},
                    "tool_calls")
            if self.lead_calls == 2:
                return self._reply({"role": "assistant", "content": "", "tool_calls": [{
                    "id": "c2", "type": "function",
                    "function": {"name": "delegate_gap", "arguments": json.dumps({
                        "question": "Does the differential test consume only the first saved input?",
                        "chain_summary": "search saves one input; verification replays it",
                        "expected_signal": "supports if only one input is replayed"})}}]},
                    "tool_calls")
            payload = {
                "paper_id": "demo", "target_execution": "not_run",
                "candidates": [{
                    "id": "L1", "title": "first saved input only", "rule": "first valid input stops search",
                    "trigger": "same graph", "mitigation": "none", "consequence": "other valid inputs untested",
                    "paper_evidence": [{"page": 1, "quote": "saves the first valid input"}],
                    "code_evidence": [], "counterevidence": "restarts may add diversity",
                    "minimal_comparison": {"fixed": "graph", "vary": "input", "baseline": "first input",
                                           "observable": "valid-input coverage", "refuted_if": "no new bug"},
                    "origin_ids": ["W1"],
                }],
                "known_boundaries": [],
            }
        return self._reply({"role": "assistant", "content": json.dumps(payload)}, "stop")

    def _reply(self, message, finish):
        return {"number": self.requests, "message": message, "finish_reason": finish,
                "usage": {"total_tokens": 1000}, "model": "mock"}


PROTOCOL = {
    "max_http_requests_per_cell": 10,
    "max_output_tokens": 2048,
    "max_actual_returned_tokens_per_cell": 750000,
    "per_request_timeout_seconds": 30,
    "per_cell_wall_seconds": 300,
    "lead_turns": 6,
    "worker_count": 1,
    "worker_replies": 1,
    "max_delegations": 1,
    "single_agent_turns": 8,
    "max_report_candidates": 3,
}


def test_swarm_handoff_ledger_end_to_end(tmp_path):
    inputs = demo_inputs(tmp_path)
    out = tmp_path / "out" / "demo" / "gap_receipt_swarm"
    client = MockClient(out)
    cell = Cell(inputs, "demo", "gap_receipt_swarm", out, PROTOCOL, client=client)
    result = cell.run()
    assert result["error"] is None
    assert (out / "final.txt").is_file()
    assert (out / "handoff.json").is_file()
    assert result["validation"]["json_parsed"], result["validation"]
    assert result["validation"]["issues"] == [], result["validation"]
    ledger = result["ledger"]
    assert len(ledger["workers"]) == 1
    for row in ledger["workers"]:
        assert row["worker_found"] == 1
        assert row["parse_retained"] == ["W1"]
        assert row["delivered_to_lead"] is True
        assert row["cited_in_final"] == ["W1"]
    # 3 lead requests + 1 worker request
    assert result["requests"] == 4


def test_budget_limits_workers_to_one(tmp_path):
    inputs = demo_inputs(tmp_path)
    out = tmp_path / "out" / "demo2" / "gap_receipt_swarm"
    protocol = dict(PROTOCOL, max_http_requests_per_cell=4)
    client = MockClient(out)
    cell = Cell(inputs, "demo", "gap_receipt_swarm", out, protocol, client=client)
    result = cell.run()
    assert len(result["ledger"]["workers"]) == 1
    assert result["requests"] <= 4


def test_parse_failure_keeps_raw_text_delivered(tmp_path):
    inputs = demo_inputs(tmp_path)
    out = tmp_path / "out" / "demo3" / "gap_receipt_swarm"
    client = MockClient(out)
    original = client.chat

    def chat(messages, tools=None, tool_choice=None, max_tokens=None, thinking=True):
        reply = original(messages, tools, tool_choice, max_tokens, thinking)
        if messages[0]["content"].startswith("You are the worker"):
            reply["message"]["content"] = "The source is ambiguous; no structured answer."
        return reply

    client.chat = chat
    cell = Cell(inputs, "demo", "gap_receipt_swarm", out, PROTOCOL, client=client)
    result = cell.run()
    rows = result["ledger"]["workers"]
    assert rows and all(row["worker_found"] is None for row in rows)
    assert all(row["parse_retained"] == [] for row in rows)
    assert all(row["delivered_to_lead"] for row in rows)
