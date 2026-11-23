"""One experimental cell: condition A (one call), B (single agent), S (gap-receipt swarm)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import prompts
from .agents import Budget, Compactor, run_lead, run_worker
from .contract import parse_finding_report, validate_report
from .evidence import Evidence
from .llm import Client
from .util import append_jsonl, dump, load, norm, require, secret_env


def task_message(evidence: Evidence, include_packet: bool, task: str | None = None) -> str:
    head = (f"{task or prompts.TASK}\n\nPaper ID: {evidence.meta['paper_id']}\n"
            f"Pinned repository commit: {evidence.commit}\n"
            f"Evidence scope: original paper pages and original tracked repository only.\n\n")
    paper = f"ORIGINAL PAPER BEGIN\n{evidence.paper_header()}\nORIGINAL PAPER END"
    if not include_packet or not evidence.packet:
        return head + "\n" + paper
    return (head + "\n" + paper + "\n\nORIGINAL SOURCE EXCERPTS BEGIN\n"
            + evidence.packet + "\nORIGINAL SOURCE EXCERPTS END")


class Cell:
    def __init__(self, inputs: Path, paper: str, condition: str, out: Path, protocol: dict,
                 client=None):
        self.inputs = Path(inputs)
        self.paper = paper
        self.condition = condition
        self.out = Path(out)
        require(not self.out.exists(), f"Never overwrite a cell: {self.out}")
        self.out.mkdir(parents=True)
        self.protocol = protocol
        self.evidence = Evidence(self.inputs / paper, self.out)
        env = secret_env()
        self.client = client or Client(
            key=env["SOCLAAS_API_KEY"],
            base=env.get("SOCLAAS_BASE_URL", "https://soclaas-api.comp.nus.edu.sg/v1"),
            archive=self.out,
            max_tokens=protocol["max_output_tokens"],
            timeout=protocol["per_request_timeout_seconds"],
        )
        self.budget = Budget(protocol["max_http_requests_per_cell"],
                             protocol["max_actual_returned_tokens_per_cell"],
                             protocol["per_cell_wall_seconds"])
        self.compactor = Compactor(self.out)
        self.handoffs: list = []
        self.delegated = False
        self.delegate_prompts = 0

    # ------------------------------------------------------------- delegation ---
    def delegate(self, question: str, chain_summary: str, lead_turn: int,
                 expected_signal: str = "") -> str:
        require(8 <= len(question) <= 1200, "delegate_gap needs one precise question")
        remaining = self.budget.remaining(self.client)
        wanted = int(self.protocol.get("worker_count", 1))
        workers = wanted if remaining >= 2 + 2 * wanted else 1
        require(remaining >= 2, "No request budget left for delegation")
        append_jsonl(self.out / "events.jsonl", {
            "kind": "delegate_requested", "lead_turn": lead_turn, "workers": workers,
            "remaining_requests": remaining,
        })
        paper_text = self.evidence.paper_header()
        results = []
        for index in range(workers):
            if self.budget.remaining(self.client) < 2:
                break
            worker_id = f"worker{index + 1}"
            result = run_worker(self, self.evidence, self.client, worker_id,
                                question, chain_summary, paper_text,
                                expected_signal=expected_signal,
                                max_requests=int(self.protocol.get("worker_replies", 3)))
            report = {"worker": worker_id, "raw_text": result["final_text"],
                      "turns": result["turns"]}
            repairs: list = []
            try:
                parsed = parse_finding_report(result["final_text"])
                report.update({
                    "parsed": True,
                    "raw_candidate_count": parsed["raw_candidate_count"],
                    "parsed_groups": parsed["parsed_groups"],
                    "repairs": parsed["repairs"],
                    "records": parsed["records"],
                    "data": parsed["data"],
                })
            except ValueError as exc:
                report.update({"parsed": False, "raw_candidate_count": None,
                               "parse_error": str(exc), "records": []})
            results.append(report)
            append_jsonl(self.out / "events.jsonl", {
                "kind": "worker_finished", "worker": worker_id, "turns": result["turns"],
                "parsed": report["parsed"], "raw_candidates": report.get("raw_candidate_count"),
            })
        handoff = {"question": question, "chain_summary": chain_summary,
                   "expected_signal": expected_signal,
                   "lead_turn": lead_turn, "workers": results, "delivered_text": ""}
        payload = {
            "question": question,
            "workers": [
                {"worker": r["worker"], "answer": r["raw_text"],
                 "candidates": r.get("records", []),
                 **({"parse_error": r["parse_error"]} if not r.get("parsed") else {})}
                for r in results
            ],
            "note": ("Worker findings are leads, not answers. Reopen every source span you rely on and "
                     "state supports/narrows/refutes in counterevidence or consequence. Keep origin_ids."),
        }
        text = json.dumps(payload, ensure_ascii=False)
        handoff["delivered_text"] = text
        self.handoffs.append(handoff)
        self.delegated = True
        dump(self.out / "handoff.json", self.handoffs)
        return text

    # ------------------------------------------------------------------ stages ---
    def run_once(self) -> str:
        system = prompts.ONCE_SYSTEM
        user = (f"Paper ID: {self.evidence.meta['paper_id']}\n"
                f"Pinned Git commit: {self.evidence.commit}\n\n"
                f"ORIGINAL PAPER BEGIN\n{self.evidence.paper_header()}\nORIGINAL PAPER END\n\n"
                f"ORIGINAL REPOSITORY FILES BEGIN\n{self.evidence.packet}\nORIGINAL REPOSITORY FILES END")
        response = self.client.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tools=[], max_tokens=self.protocol["max_output_tokens"],
        )
        return response["message"].get("content") or ""

    def run_single_agent(self) -> str:
        from .agents import run_lead as _run_lead  # same loop, no delegation
        system = prompts.SINGLE_SYSTEM
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": task_message(self.evidence, include_packet=True, task=prompts.HANDOFF_TASK)},
        ]
        return _single_loop(self, messages, prompts.TOOLS, self.protocol["single_agent_turns"])

    def run_swarm(self) -> str:
        result = run_lead(self, self.evidence, self.client,
                          task_message(self.evidence, include_packet=False, task=prompts.HANDOFF_TASK),
                          compactor=self.compactor, delegate=self.delegate,
                          max_turns=self.protocol["lead_turns"])
        return result.final

    # -------------------------------------------------------------------- main ---
    def run(self) -> dict:
        started = time.time()
        error = None
        final = ""
        try:
            if self.condition == "api_once":
                final = self.run_once()
            elif self.condition == "single_agent":
                final = self.run_single_agent()
            elif self.condition == "gap_receipt_swarm":
                final = self.run_swarm()
            else:
                raise ValueError(f"Unknown condition {self.condition}")
        except Exception as exc:  # archive the failure, do not lose the run
            error = f"{type(exc).__name__}: {exc}"
            append_jsonl(self.out / "events.jsonl", {"kind": "cell_error", "error": error})
        (self.out / "final.txt").write_text(final)
        validation = {"json_parsed": False, "issues": ["no final text"]}
        report = {}
        if final:
            try:
                report = parse_finding_report(final)
                validation = validate_report(report["data"], self.evidence,
                                             max_records=self.protocol["max_report_candidates"])
                validation["repairs"] = report["repairs"]
                validation["raw_candidate_count"] = report["raw_candidate_count"]
            except ValueError as exc:
                validation = {"json_parsed": False, "issues": [str(exc)]}
        ledger = self.build_ledger(report)
        result = {
            "paper": self.paper, "condition": self.condition,
            "prompt_version": prompts.PROMPT_VERSION,
            "requests": self.client.requests, "tokens": self.client.tokens,
            "elapsed_seconds": round(time.time() - started, 1),
            "model": sorted({row.get("model") for row in self.client.usage if row.get("model")}),
            "error": error, "validation": validation,
            "handoffs": [{k: v for k, v in h.items() if k != "delivered_text"} for h in self.handoffs],
            "ledger": ledger,
            "target_execution": "not_run",
        }
        dump(self.out / "result.json", result)
        dump(self.out / "usage.jsonl", self.client.usage)
        dump(self.out / "reads.json", self.evidence.reads)
        dump(self.out / "tools.json", self.evidence.tool_calls)
        dump(self.out / "validation.json", validation)
        dump(self.out / "ledger.json", ledger)
        return result

    # ------------------------------------------------------------------ ledger ---
    def build_ledger(self, report: dict) -> dict:
        """worker found -> parse retained -> delivered to lead -> cited in final."""
        final_records = report.get("records", []) if report else []
        final_ids = {r["id"] for r in final_records}
        origins = set()
        title_norms = []
        for record in final_records:
            origins.update(record.get("origin_ids") or [])
            title_norms.append(norm(record.get("title") or ""))
        rows = []
        for handoff in self.handoffs:
            for worker in handoff["workers"]:
                delivered = self.was_delivered(handoff["delivered_text"])
                found = worker.get("raw_candidate_count")
                retained = [r["id"] for r in worker.get("records", [])] if worker.get("parsed") else []
                cited = [cid for cid in retained
                         if any(origin == cid or origin.endswith(":" + cid) for origin in origins)]
                if not cited:
                    cited = [r["id"] for r in worker.get("records", [])
                             if norm(r.get("title") or "") and norm(r.get("title") or "") in title_norms]
                verified = [span for r in worker.get("records", []) for span in r.get("code_evidence", [])
                            if self.evidence.span_read_by("root", span.get("path"), span.get("start") or 0,
                                                          span.get("end") or 0)]
                rows.append({
                    "worker": worker["worker"],
                    "worker_found": found,
                    "parse_retained": retained,
                    "delivered_to_lead": delivered,
                    "verified_spans_after_handoff": len(verified),
                    "cited_in_final": cited,
                })
        return {
            "workers": rows,
            "delegation_turns": [h["lead_turn"] for h in self.handoffs],
            "final_records": sorted(final_ids),
            "stages": ["worker_found", "parse_retained", "delivered_to_lead", "verified_span", "cited_in_final"],
        }

    def was_delivered(self, text: str) -> bool:
        if not text:
            return False
        for path in sorted(self.out.glob("request-*.json")):
            wire = load(path)
            for message in wire.get("messages", []):
                content = message.get("content")
                if isinstance(content, str) and text[:2000] in content:
                    return True
        return False


def _single_loop(cell, messages, tools, max_turns: int) -> str:
    compactor = Compactor(cell.out)
    for turn in range(1, max_turns + 1):
        messages = compactor.maybe_compact(messages, f"single-turn-{turn}")
        final_now = (cell.budget.remaining(cell.client) <= 1 or cell.budget.exhausted(cell.client)
                     or turn == max_turns)
        note = prompts.FINAL_NOTE if final_now else prompts.BUDGET_NOTE.format(
            used=cell.client.requests + 1, cap=cell.budget.request_cap, tokens=cell.client.tokens)
        response = cell.client.chat(messages + [{"role": "user", "content": note}],
                                    tools=[] if final_now else tools,
                                    max_tokens=cell.protocol["max_output_tokens"],
                                    thinking=not final_now)
        message = response["message"]
        text = message.get("content") or ""
        calls = message.get("tool_calls") or []
        append_jsonl(cell.out / "events.jsonl", {
            "kind": "single_reply", "turn": turn, "request": response["number"],
            "finish": response["finish_reason"],
            "tool_calls": [c["function"]["name"] for c in calls], "chars": len(text),
            "final_forced": final_now,
        })
        if calls and not final_now:
            from .llm import assistant_message
            messages.append(assistant_message(message))
            for call in calls:
                name = (call.get("function") or {}).get("name") or ""
                try:
                    args = json.loads((call.get("function") or {}).get("arguments") or "{}")
                    result = cell.evidence.call("root", name, args)
                except (ValueError, json.JSONDecodeError) as exc:
                    result = f"Tool refused: {exc}"
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": result})
            continue
        if final_now or text.strip():
            return text
    return ""
