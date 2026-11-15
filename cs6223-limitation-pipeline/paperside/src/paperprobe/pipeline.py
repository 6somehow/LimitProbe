"""Five-paper preparation, three controlled generation arms, and cache replay."""
from __future__ import annotations

import copy
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from .alignment import attach_source_context, code_context_pool, discover_opportunities
from .checks import check_candidate
from .generation import generate_candidates
from .io import file_sha256, inside, read_json, stable_id, text_sha256, write_json
from .papers import extract_paper, retrieve_evidence
from .providers import BudgetLedger, CodexProvider, COMPACT_INSTRUCTIONS, build_prompt, response_schema
from .scanner import scan_repository


METHODS = ["full", "code_only", "direct"]


def _config(workspace: Path) -> dict[str, Any]:
    return read_json(workspace / "configs/default.json")


def _scopes(workspace: Path) -> dict[str, Any]:
    path = workspace / "configs/discovery-scopes.json"
    return read_json(path) if path.exists() else {"selection_mode": "whole_repository_bounded_scan", "scopes": {}}


def _git(repository: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repository), *args], capture_output=True,
                          text=True, check=True, timeout=30).stdout.strip()


def load_catalog(workspace: Path) -> dict[str, Any]:
    catalog = read_json(Path(workspace) / "data/catalog/papers.json")
    ids = [p["id"] for p in catalog["papers"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate paper IDs in the catalog")
    return catalog


def prepare_workspace(workspace: Path, all_papers: bool = False,
                      progress: Callable[[str], None] = print) -> dict[str, Any]:
    workspace = Path(workspace).resolve()
    catalog = load_catalog(workspace)
    config, scopes = _config(workspace), _scopes(workspace)
    index = {"schema_version": "1.0", "papers": [], "target_code_executed": False}
    for paper in catalog["papers"]:
        if not paper["selected"] and not all_papers:
            continue
        progress(f"Preparing {paper['id']}: PDF evidence" )
        pdf = inside(workspace, paper["pdf_path"])
        if file_sha256(pdf) != paper["pdf_sha256"]:
            raise ValueError(f"PDF checksum mismatch: {paper['id']}")
        out = workspace / "data/processed" / paper["id"]
        profile = extract_paper(paper["id"], pdf, out, paper["title"], config["max_profile_claims"])
        record = {"paper_id": paper["id"], "selected": paper["selected"], "evidence_count": len(profile["evidence"]), "page_count": profile["page_count"]}
        if paper["selected"]:
            progress(f"Preparing {paper['id']}: static repository scan")
            scope = scopes["scopes"].get(paper["id"], {})
            if scope.get("repository_commit", paper["repository_commit"]) != paper["repository_commit"]:
                raise ValueError(f"Scope pinned to a different commit: {paper['id']}")
            scan = scan_repository(inside(workspace, paper["repo_path"]), config["max_repo_files"],
                                   config["max_file_bytes"], scope.get("include_paths"))
            scan["component_scope"] = scope
            scan["selection_mode"] = scopes["selection_mode"]
            if scan["commit"] != paper["repository_commit"]:
                raise ValueError(f"Repository commit mismatch: {paper['id']}")
            for condition in scan["conditions"]:
                condition["evidence"]["commit"] = scan["commit"]
            scan["conditions"] = attach_source_context(scan["conditions"], inside(workspace, paper["repo_path"]))
            write_json(out / "scan.json", scan)
            record.update({"conditions": len(scan["conditions"]), "files_scanned": scan["files_scanned"], "scan_errors": len(scan["errors"]), "repository_commit": scan["commit"]})
        index["papers"].append(record)
    write_json(workspace / "data/processed/index.json", index)
    return index


def normalize_response(response: dict[str, Any], paper_id: str, method: str,
                       profile: dict[str, Any], conditions: list[dict[str, Any]],
                       max_candidates: int) -> list[dict[str, Any]]:
    raw = response.get("candidates")
    if not isinstance(raw, list) or len(raw) > max_candidates:
        raise ValueError("Response candidate list is missing or exceeds the frozen candidate cap")
    condition_lookup = {c["condition_id"]: c for c in conditions}
    evidence_lookup = {e["evidence_id"]: e for e in profile.get("evidence", [])}
    candidates = []
    for number, item in enumerate(raw):
        condition = copy.deepcopy(condition_lookup.get(item.get("condition_id"), {}))
        limitations = list(item.get("limitations", []))
        if not condition:
            limitations.append("Model cited a condition ID outside the supplied context; provenance check will fail.")
        try:
            inputs = json.loads(item.get("inputs_json", ""))
        except (ValueError, TypeError):
            inputs = []
            limitations.append("Model inputs_json was not parseable; candidate retained as a failed specification.")
        paper_ids = item.get("paper_evidence_ids", [])
        quotes = []
        for eid in paper_ids:
            if eid in evidence_lookup and method != "code_only":
                quotes.append(copy.deepcopy(evidence_lookup[eid]))
            else:
                quotes.append({"evidence_id": eid, "paper_id": paper_id, "page": None, "quote": "", "sha256": None})
                limitations.append("Paper evidence ID is not available in this method/context.")
        oracle = copy.deepcopy(item.get("oracle", {}))
        oracle["invalid_evidence_ids"] = [eid for eid in oracle.get("evidence_ids", []) if eid not in evidence_lookup or method == "code_only"]
        oracle["evidence"] = [copy.deepcopy(evidence_lookup[eid]) for eid in oracle.get("evidence_ids", []) if eid in evidence_lookup and method != "code_only"]
        oracle["semantic_validation_status"] = "unknown"
        if oracle.get("type") != "unknown" and not oracle.get("evidence"):
            oracle.setdefault("limitations", []).append("Proposed relation has no supplied paper grounding; assess independently against code and contract.")
        candidate = {
            "candidate_id": stable_id("candidate", paper_id, method, number, item),
            "opportunity_id": stable_id("op", paper_id, item.get("condition_id"), method),
            "paper_id": paper_id, "strategy": item.get("strategy", "observation"),
            "inputs": inputs, "preconditions": item.get("preconditions", []),
            "target_condition": condition, "observation": item.get("observation", ""),
            "paper_evidence": quotes, "code_evidence": condition.get("evidence", {}),
            "oracle": oracle, "scope_status": item.get("scope_status", "unknown"),
            "scope_constraints": [], "alignment_reason": item.get("alignment_reason", ""),
            "limitations": limitations + ["Model-proposed scope/alignment is not a human-approved claim.", "Target code and proposed tests have not been executed."],
            "backend": "codex_cli", "execution_status": "not_run", "input_binding_status": "requires_adapter_mapping",
        }
        candidates.append(candidate)
    return candidates


def _metadata(workspace: Path, papers: list[dict], backend: str, max_candidates: int) -> dict[str, Any]:
    references = {}
    for p in papers:
        references[p["id"]] = {
            "pdf_path": str(inside(workspace, p["pdf_path"])), "paper_url": p["paper_url"],
            "repo_path": str(inside(workspace, p["repo_path"])), "repo_url": p["repo_url"],
            "commit": p["repository_commit"], "paper_sha256": p["pdf_sha256"],
            "paper_version_note": p["paper_version_note"],
        }
    return {
        "max_candidates": max_candidates, "required_reviewers": 2,
        "paper_references": references, "runtime_verification": False,
        "human_review_status": "pending", "dataset_role": "development_selected_cases",
        "discovery_mode": _scopes(workspace)["selection_mode"],
        "discovery_limit": "Repository components are frozen manually; condition extraction within them is automatic. This is guided synthesis, not unrestricted repository discovery.",
        "code_context_selection": "same paper-independent automatically scanned condition pool for all methods",
        "backend_note": "Heuristic demonstration only; not an LLM baseline experiment" if backend == "heuristic" else "Recorded model-assisted static candidate generation; semantic ratings await independent humans",
        "catalog_sha256": file_sha256(workspace / "data/catalog/papers.json"),
    }


def _prepared_sources(workspace: Path, papers: list[dict]) -> tuple[dict, dict]:
    prepared, hashes = {}, {}
    for paper in papers:
        pid = paper["id"]
        directory = workspace / "data/processed" / pid
        if not (directory / "scan.json").exists():
            raise ValueError(f"{pid} has not been prepared; run paperprobe prepare")
        profile = read_json(directory / "profile.json")
        pages, scan = read_json(directory / "pages.json"), read_json(directory / "scan.json")
        repository = inside(workspace, paper["repo_path"])
        if file_sha256(inside(workspace, paper["pdf_path"])) != paper["pdf_sha256"]:
            raise ValueError(f"Current PDF checksum differs: {pid}")
        if _git(repository, "rev-parse", "HEAD") != paper["repository_commit"] or _git(repository, "status", "--porcelain"):
            raise ValueError(f"Repository must be at the clean pinned commit: {pid}")
        if profile["paper_sha256"] != paper["pdf_sha256"] or pages["paper_sha256"] != paper["pdf_sha256"] or scan["commit"] != paper["repository_commit"]:
            raise ValueError(f"Prepared source version mismatch: {pid}")
        if scan.get("component_scope", {}) != _scopes(workspace)["scopes"].get(pid, {}):
            raise ValueError(f"Prepared component scope differs: {pid}; prepare again")
        prepared[pid] = (profile, pages, scan)
        hashes[pid] = {name: file_sha256(directory / name) for name in ["pages.json", "profile.json", "scan.json"]}
    return prepared, hashes


def _freeze_context(output: Path, paper_id: str, profile: dict, scan: dict,
                    max_candidates: int, prompt_cap: int) -> tuple[list[dict], dict, dict]:
    pool = code_context_pool(scan, 12)
    retrieved_profile = copy.deepcopy(profile)
    query = " ".join(str(c.get(k, "")) for c in pool for k in ["path", "symbol", "variable", "expression"])
    retrieved_profile["evidence"] = retrieve_evidence(profile, query, 14)
    full_prompt = build_prompt(paper_id, "full", retrieved_profile, pool, max_candidates, prompt_cap)
    bounded = json.loads(full_prompt.split("\nDATA:\n", 1)[1])
    kept = {c["condition_id"] for c in bounded["code_conditions"]}
    pool = [c for c in pool if c["condition_id"] in kept]
    model_profile = copy.deepcopy(profile)
    model_profile["evidence"] = bounded["paper_evidence"]
    path = output / "contexts" / f"{paper_id}.json"
    context = {"conditions": pool, "model_conditions": bounded["code_conditions"], "paper_evidence": model_profile["evidence"]}
    if path.exists() and read_json(path) != context:
        raise ValueError(f"Frozen generation context changed: {paper_id}")
    write_json(path, context)
    return pool, model_profile, bounded


def _run_batches(workspace: Path, output: Path, results: dict, papers: list[dict],
                 contexts: dict, prepared: dict, provider: CodexProvider,
                 methods: list[str], max_candidates: int, progress: Callable[[str], None]) -> None:
    from .batching import batch_schema, build_batch_prompt, validate_batch_response
    ids = [p["id"] for p in papers]
    batch_data = [contexts[pid][2] for pid in ids]
    results["metadata"].setdefault("batches", [])
    for method in methods:
        tasks = [t for t in results["tasks"] if t["method"] == method]
        if all(t["status"] in {"completed", "failed"} for t in tasks):
            progress(f"Cached shared {method} batch ({len(ids)} paper tasks)")
            continue
        if any(t["status"] != "not_started" for t in tasks):
            raise ValueError("A shared batch must checkpoint all its paper tasks together")
        progress(f"Generating shared {method} batch: {', '.join(ids)}")
        prompt = build_batch_prompt(method, batch_data, max_candidates)
        attempt = output / "model/batches" / method / "attempt-1"
        provenance_path = attempt / "provenance.json"
        started = time.monotonic()
        batch = {"method": method, "paper_ids": ids, "status": "failed", "error": None,
                 "counting_unit": "one_shared_codex_cli_invocation", "attempt": 1}
        try:
            if provenance_path.exists():
                provenance = read_json(provenance_path)
                if provenance["prompt_sha256"] != text_sha256(prompt) or provenance.get("tools_used"):
                    raise ValueError("Cached raw batch differs from frozen prompt/protocol")
                response = read_json(attempt / "response.json")
                batch["recovered_cached_response"] = True
            else:
                if attempt.exists():
                    raise ValueError("An incomplete previous attempt is preserved; automatic retry is disabled")
                response = provider.call(prompt, attempt, batch_schema(ids, max_candidates))
                provenance = read_json(provenance_path)
            indexed = validate_batch_response(response, ids, max_candidates)
            normalized = {}
            for p in papers:
                pid = p["id"]
                pool, model_profile, _ = contexts[pid]
                candidates = normalize_response(indexed[pid], pid, method, model_profile, pool, max_candidates)
                for candidate in candidates:
                    candidate["checks"] = check_candidate(candidate, inside(workspace, p["repo_path"]), prepared[pid][1], p["repository_commit"])
                normalized[pid] = candidates
            for task in tasks:
                task.update({"status": "completed", "candidates": normalized[task["paper_id"]],
                             "error": None, "abstain_reason": indexed[task["paper_id"]]["abstain_reason"],
                             "shared_invocation_id": provenance["call_id"], "duration_seconds": 0,
                             "duration_note": "Wall duration and tokens counted once in metadata.batches"})
            batch.update({"status": "completed", "call_id": provenance["call_id"], "usage": provenance["usage"], "tools_used": provenance["tools_used"]})
        except Exception as error:
            batch["error"] = f"{type(error).__name__}: {error}"
            progress(f"FAILED shared {method} batch: {batch['error']}")
            for task in tasks:
                task.update({"status": "failed", "candidates": [], "error": batch["error"], "duration_seconds": 0})
        batch["duration_seconds"] = round(time.monotonic() - started, 3)
        results["metadata"]["batches"].append(batch)
        write_json(output / "results.json", results)


def run_experiment(workspace: Path, output: Path, backend: str = "heuristic",
                   methods: list[str] | None = None, max_candidates: int = 5,
                   paper_ids: list[str] | None = None, replay_from: Path | None = None,
                   progress: Callable[[str], None] = print) -> dict[str, Any]:
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    methods = list(METHODS if methods is None else methods)
    if not methods or len(methods) != len(set(methods)) or not set(methods) <= set(METHODS):
        raise ValueError("Methods must be unique known method names")
    if not 1 <= max_candidates <= 5:
        raise ValueError("Candidate cap must be between one and five")
    if backend not in {"heuristic", "codex", "replay"}:
        raise ValueError("Unknown backend")
    papers = [p for p in load_catalog(workspace)["papers"] if p["selected"] and (paper_ids is None or p["id"] in paper_ids)]
    if not papers:
        raise ValueError("No selected papers match the requested run")
    if paper_ids is not None and set(paper_ids) != {p["id"] for p in papers}:
        raise ValueError("Requested paper IDs must all be selected catalog papers")
    config = _config(workspace)
    prepared, prepared_hashes = _prepared_sources(workspace, papers)
    output.mkdir(parents=True, exist_ok=True)
    metadata = _metadata(workspace, papers, backend, max_candidates)
    protocol = {"paper_ids": [p["id"] for p in papers], "methods": methods,
                "max_candidates": max_candidates, "prepared_hashes": prepared_hashes,
                "config": config, "scopes": _scopes(workspace),
                "instruction_sha256": text_sha256(COMPACT_INSTRUCTIONS),
                "prompt_code_sha256": file_sha256(Path(__file__).with_name("providers.py")),
                "alignment_code_sha256": file_sha256(Path(__file__).with_name("alignment.py")),
                "implementation_sha256": {name: file_sha256(Path(__file__).with_name(name)) for name in ["pipeline.py", "batching.py", "papers.py", "scanner.py", "generation.py", "checks.py"]},
                "attempts_per_task": 1}
    metadata["protocol"] = protocol
    metadata["prepared_hashes"] = prepared_hashes
    metadata["protocol_sha256"] = text_sha256(json.dumps(protocol, ensure_ascii=False, sort_keys=True))
    metadata["model_requested"] = config["model"] if backend == "codex" else None
    metadata["generation_batch_mode"] = config["generation_batch_mode"] if backend == "codex" else "not_applicable_to_template_demo_or_replay"
    metadata["generation_dependence"] = "One shared invocation per method; paper outputs are not independent generation repetitions. Descriptive development pilot only." if backend == "codex" else "Deterministic demonstration/cache replay; no independent model-generation samples."
    if (output / "results.json").exists():
        results = read_json(output / "results.json")
        if results["backend"] != backend or results["metadata"]["protocol_sha256"] != metadata["protocol_sha256"] or results["metadata"]["catalog_sha256"] != metadata["catalog_sha256"]:
            raise ValueError("Existing run differs in frozen protocol or sources; use a new output directory")
    else:
        tasks = [{"task_id": p["id"], "paper_id": p["id"], "method": m, "status": "not_started", "candidates": [], "error": None} for p in papers for m in methods]
        results = {"schema_version": "1.0", "run_id": stable_id("run", output.name, metadata["protocol_sha256"], backend), "backend": backend, "mode": "guided_synthesis", "methods": methods, "tasks": tasks, "metadata": metadata}
        write_json(output / "results.json", results)
    previous = None
    if backend == "replay":
        if not replay_from:
            raise ValueError("Replay requires --replay-from")
        previous = read_json(Path(replay_from) / "results.json")
        if previous["metadata"]["catalog_sha256"] != metadata["catalog_sha256"] or previous["metadata"]["protocol_sha256"] != metadata["protocol_sha256"]:
            raise ValueError("Replay frozen protocol/source versions differ from the original run")
        results["metadata"]["source_run"] = str(Path(replay_from).resolve())
        results["metadata"]["source_backend"] = previous["backend"]
    provider = CodexProvider(BudgetLedger(workspace / "runs/model-budget.json", config["llm_call_limit"], config["llm_token_limit"]), model=config["model"], timeout=config["model_timeout_seconds"]) if backend == "codex" else None
    frozen_contexts = {p["id"]: _freeze_context(output, p["id"], prepared[p["id"]][0], prepared[p["id"]][2], max_candidates, config["max_prompt_characters"]) for p in papers}
    if backend == "codex" and config["generation_batch_mode"] == "by_method":
        _run_batches(workspace, output, results, papers, frozen_contexts, prepared, provider, methods, max_candidates, progress)
    for paper in papers:
        paper_id = paper["id"]
        profile, pages, scan = prepared[paper_id]
        pool, model_profile, bounded = frozen_contexts[paper_id]
        for method in methods:
            existing = next((t for t in results["tasks"] if t["task_id"] == paper_id and t["method"] == method), None)
            if existing and existing["status"] in {"completed", "failed"}:
                progress(f"Cached {paper_id}/{method}")
                continue
            progress(f"Generating {paper_id}/{method} via {backend}")
            task = {"task_id": paper_id, "paper_id": paper_id, "method": method, "status": "failed", "candidates": [], "error": None}
            started = time.monotonic()
            try:
                if backend == "heuristic":
                    opportunities = discover_opportunities(paper_id, profile, scan, method)
                    task["candidates"] = generate_candidates(opportunities, method, max_candidates)
                elif backend == "replay":
                    original = next((t for t in previous["tasks"] if t["task_id"] == paper_id and t["method"] == method), None)
                    if original is None:
                        raise ValueError("Source replay task is missing")
                    task = copy.deepcopy(original)
                    task["replayed"] = True
                else:
                    prompt = build_prompt(paper_id, method, model_profile, pool, max_candidates, config["max_prompt_characters"])
                    response = provider.call(prompt, output / "model" / paper_id / method / "attempt-1", response_schema(max_candidates))
                    task["candidates"] = normalize_response(response, paper_id, method, model_profile, pool, max_candidates)
                    task["abstain_reason"] = response.get("abstain_reason", "")
                for candidate in task["candidates"]:
                    candidate["checks"] = check_candidate(candidate, inside(workspace, paper["repo_path"]), pages, paper["repository_commit"])
                if backend != "replay" or task.get("status") != "failed":
                    task["status"] = "completed"
            except Exception as error:
                task["error"] = f"{type(error).__name__}: {error}"
                progress(f"FAILED {paper_id}/{method}: {task['error']}")
            task["duration_seconds"] = round(time.monotonic() - started, 3)
            if existing:
                results["tasks"].remove(existing)
            results["tasks"].append(task)
            write_json(output / "results.json", results)
    # Explicit empty records keep all frozen tasks in evaluation denominators.
    for p in papers:
        for method in methods:
            if not any(t["task_id"] == p["id"] and t["method"] == method for t in results["tasks"]):
                results["tasks"].append({"task_id": p["id"], "paper_id": p["id"], "method": method, "status": "not_started", "candidates": [], "error": "No result recorded"})
    write_json(output / "results.json", results)
    from .reporting import write_run_report
    write_run_report(results, output / "report.md")
    write_run_report(results, output / "report.html")
    return results
