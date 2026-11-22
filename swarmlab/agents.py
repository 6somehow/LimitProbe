"""Lead and worker loops with shared request/token budgets and compaction receipts."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from . import prompts
from .contract import candidate_groups, parse_finding_report, normalize_record
from .llm import assistant_message
from .util import append_jsonl, dump, estimate_tokens, norm, require


class Budget:
    def __init__(self, request_cap: int, token_cap: int, wall_seconds: int):
        self.request_cap = request_cap
        self.token_cap = token_cap
        self.wall_seconds = wall_seconds
        self.started = time.time()
        self.lock = threading.Lock()

    def spent_requests(self, client) -> int:
        return client.requests

    def remaining(self, client) -> int:
        return self.request_cap - client.requests

    def exhausted(self, client) -> bool:
        return (client.requests >= self.request_cap or client.tokens >= self.token_cap
                or time.time() - self.started > self.wall_seconds)


class Compactor:
    """Deterministic context trimming with an audit trail.

    Only tool payloads and older reasoning are shortened; the task packet, the
    system prompt, and every assistant decision stay intact.
    """

    def __init__(self, archive: Path, limit_tokens: int = 98000):
        self.archive = Path(archive)
        self.limit_tokens = limit_tokens
        self.events: list = []

    def maybe_compact(self, messages: list, label: str) -> list:
        before = estimate_tokens(messages)
        if before <= self.limit_tokens:
            return messages
        tool_index = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
        keep = set(tool_index[-4:])
        trimmed = 0
        for index in tool_index:
            if index in keep:
                continue
            content = messages[index].get("content") or ""
            if len(content) <= 900:
                continue
            messages[index]["content"] = (
                content[:900]
                + f"\n...[compacted {len(content) - 900} chars; re-read the span if needed]"
            )
            trimmed += 1
        for message in messages:
            reasoning = message.get("reasoning")
            if isinstance(reasoning, str) and len(reasoning) > 600:
                message["reasoning"] = reasoning[:600] + "...[reasoning compacted]"
        after = estimate_tokens(messages)
        event = {"kind": "compaction", "label": label, "before_tokens": before,
                 "after_tokens": after, "tool_payloads_trimmed": trimmed}
        self.events.append(event)
        append_jsonl(self.archive / "events.jsonl", event)
        return messages


def tool_schema_names(tools) -> list:
    return [row["function"]["name"] for row in tools]


def execute_tool(evidence, agent: str, name: str, args: dict) -> str:
    return evidence.call(agent, name, args)


def looks_like_final(text: str) -> bool:
    try:
        report = parse_finding_report(text)
    except ValueError:
        return False
    data = report["data"]
    return isinstance(data, dict) and "candidates" in data and data.get("paper_id") is not None


class LoopResult:
    def __init__(self, final: str, messages: list, turns: int):
        self.final = final
        self.messages = messages
        self.turns = turns


def run_lead(cell, evidence, client, task_message: str, compactor: Compactor | None = None,
             delegate=None, max_turns: int = 6) -> LoopResult:
    system = prompts.HANDOFF_SYSTEM
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": task_message},
    ]
    compactor = compactor or Compactor(cell.out)
    turns = 0
    while turns < max_turns:
        turns += 1
        messages = compactor.maybe_compact(messages, f"lead-turn-{turns}")
        remaining = cell.budget.remaining(client)
        final_now = remaining <= 1 or cell.budget.exhausted(client) or turns == max_turns
        if turns == 1 and cell.protocol.get("paper_first") and not final_now:
            response = client.chat(
                messages + [{"role": "user", "content": prompts.PAPER_FIRST_NOTE}],
                tools=[], max_tokens=cell.protocol["max_output_tokens"],
            )
            message = response["message"]
            text = message.get("content") or ""
            messages.append(assistant_message(message))
            append_jsonl(cell.out / "events.jsonl", {
                "kind": "paper_first_map", "request": response["number"],
                "finish": response["finish_reason"], "chars": len(text),
            })
            messages.append({"role": "user", "content":
                             "Now test these gaps against the pinned source with the tools. Keep the map updated in your notes."})
            continue
        must_delegate = (not cell.delegated and not final_now and turns >= 3
                         and remaining >= 4 and cell.delegate_prompts < 2
                         and turns >= int(cell.protocol.get("delegate_from_turn", 4)))
        if final_now:
            note = prompts.FINAL_NOTE
        else:
            note = prompts.BUDGET_NOTE.format(
                used=client.requests + 1, cap=cell.budget.request_cap, tokens=client.tokens)
            if must_delegate:
                note += "\n\n" + prompts.DELEGATE_REQUIRED
                cell.delegate_prompts += 1
        tools = prompts.LEAD_TOOLS
        if final_now:
            tools = []
        elif must_delegate and cell.delegate_prompts >= 2:
            tools = [prompts.DELEGATE_TOOL]
        response = client.chat(
            messages + [{"role": "user", "content": note}],
            tools=tools,
            max_tokens=cell.protocol["max_output_tokens"],
            thinking=not final_now,
        )
        message = response["message"]
        text = message.get("content") or ""
        calls = message.get("tool_calls") or []
        append_jsonl(cell.out / "events.jsonl", {
            "kind": "lead_reply", "turn": turns, "request": response["number"],
            "finish": response["finish_reason"], "tool_calls": [c["function"]["name"] for c in calls],
            "chars": len(text), "final_forced": final_now,
        })
        if calls and not final_now:
            messages.append(assistant_message(message))
            for call in calls:
                name = (call.get("function") or {}).get("name") or ""
                try:
                    args = json.loads((call.get("function") or {}).get("arguments") or "{}")
                    require(isinstance(args, dict), "tool arguments must be an object")
                except (ValueError, json.JSONDecodeError) as exc:
                    messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                                     "content": f"Tool refused: bad arguments ({exc})"})
                    continue
                if name == "delegate_gap":
                    require(delegate is not None, "delegation is not available in this condition")
                    result = delegate(args.get("question", ""), args.get("chain_summary", ""), turns)
                else:
                    try:
                        result = execute_tool(evidence, "root", name, args)
                    except ValueError as exc:
                        result = f"Tool refused: {exc}"
                        append_jsonl(cell.out / "events.jsonl", {"kind": "tool_error", "name": name, "error": str(exc)})
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": result})
            continue
        messages.append(assistant_message(message))
        if final_now:
            return LoopResult(text, messages, turns)
        if looks_like_final(text):
            if must_delegate and cell.delegate_prompts < 2:
                continue
            return LoopResult(text, messages, turns)
        if must_delegate and cell.delegate_prompts < 2:
            continue
        messages.append({"role": "user", "content": prompts.CONTINUE_NOTE})
    return LoopResult(messages[-1].get("content") or "", messages, turns)


def run_worker(cell, evidence, client, worker_id: str, question: str, chain_summary: str,
               paper_text: str, max_requests: int = 2) -> dict:
    system = prompts.WORKER_SYSTEM
    user = (
        f"Paper ID: {evidence.meta['paper_id']}\nPinned repository commit: {evidence.commit}\n\n"
        f"LEAD QUESTION\n{question}\n\nLEAD CHAIN SUMMARY\n{chain_summary}\n\n"
        f"ORIGINAL PAPER BEGIN\n{paper_text}\nORIGINAL PAPER END\n\n"
        "Answer the assigned question. Read the pinned source with the tools before citing it."
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    turns = 0
    final = ""
    while turns < max_requests:
        turns += 1
        force = turns >= max_requests or cell.budget.remaining(client) <= 2
        note = (prompts.FINAL_NOTE if force else
                f"Worker budget: {client.requests + 1} of {cell.budget.request_cap} shared requests will be used. "
                "Return the JSON answer after at most two source reads.")
        response = client.chat(messages + [{"role": "user", "content": note}],
                               tools=[] if force else prompts.TOOLS,
                               max_tokens=min(16000, cell.protocol["max_output_tokens"]),
                               thinking=not force)
        message = response["message"]
        text = message.get("content") or ""
        calls = message.get("tool_calls") or []
        append_jsonl(cell.out / "events.jsonl", {
            "kind": "worker_reply", "worker": worker_id, "turn": turns,
            "request": response["number"], "finish": response["finish_reason"],
            "tool_calls": [c["function"]["name"] for c in calls], "chars": len(text), "final_forced": force,
        })
        if calls and not force:
            messages.append(assistant_message(message))
            for call in calls:
                name = (call.get("function") or {}).get("name") or ""
                try:
                    args = json.loads((call.get("function") or {}).get("arguments") or "{}")
                    result = execute_tool(evidence, worker_id, name, args)
                except (ValueError, json.JSONDecodeError) as exc:
                    result = f"Tool refused: {exc}"
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": result})
            continue
        messages.append(assistant_message(message))
        final = text
        break
    return {"worker": worker_id, "question": question, "chain_summary": chain_summary,
            "final_text": final, "turns": turns, "messages": messages}
