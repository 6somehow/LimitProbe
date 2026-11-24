"""Transparent code/paper retrieval; semantic alignment remains a review task."""
from __future__ import annotations

import ast
import copy
import re
from pathlib import Path
from typing import Any

from .io import inside, stable_id, text_sha256
from .papers import retrieve_evidence, terms
from .scanner import _mask_noncode


_CONTEXT_CHARACTERS = 1200
_NEIGHBORHOOD_CHARACTERS = 800
_SOURCE_BYTE_LIMIT = 2000000
_CONTEXT_LIMITATION = "Nearby source is a syntactic context/contract candidate; applicability and function scope have not been verified."


def _contract_ranges(source: str, path: str) -> list[tuple[int, int, str]]:
    """Find complete syntactic statements, without attributing any contract."""
    ranges: list[tuple[int, int, str]] = []
    if Path(path).suffix.lower() in {".py", ".pyi"}:
        try:
            tree = ast.parse(source, filename=path)
        except (SyntaxError, ValueError, RecursionError):
            return ranges
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                ranges.append((node.lineno, node.end_lineno or node.lineno, "assert"))
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                called = node.exc.func
                name = called.id if isinstance(called, ast.Name) else called.attr if isinstance(called, ast.Attribute) else ""
                if name in {"ValueError", "RuntimeError"}:
                    ranges.append((node.lineno, node.end_lineno or node.lineno, name))
        return sorted(set(ranges))

    # Comments/literals are masked only to locate complete calls. Quoted
    # evidence is taken from the original source, preserving strings and bytes.
    masked = _mask_noncode(source)
    for match in re.finditer(r"\b(assert|TORCH_CHECK|ValueError|RuntimeError)\s*\(", masked):
        depth, stop = 1, match.end()
        while stop < len(masked) and depth:
            depth += (masked[stop] == "(") - (masked[stop] == ")")
            stop += 1
        if depth:
            continue
        start_line = source.count("\n", 0, match.start()) + 1
        end_line = source.count("\n", 0, stop) + 1
        ranges.append((start_line, end_line, match.group(1)))
    return sorted(set(ranges))


def attach_source_context(conditions: list[dict[str, Any]], repo_path: Path) -> list[dict[str, Any]]:
    """Attach bounded, exact nearby source without validating its applicability.

    Each result is a deep copy. The target neighborhood starts at +/- five
    lines. At most the nearest three complete contract candidates ending before
    the target and beginning within the preceding 80 lines are considered.
    The 1200-character quotation budget withholds entire contract statements;
    a large neighborhood is reduced only by removing whole outer lines.
    No inspected code is imported or executed, and paths cannot leave the repo.
    """
    results = copy.deepcopy(conditions)
    cache: dict[str, tuple[list[str], list[tuple[int, int, str]]]] = {}
    failures: dict[str, str] = {}
    for condition in results:
        condition["source_context"] = []
        condition["source_context_status"] = "unavailable"
        condition["source_context_errors"] = []
        condition["source_context_budget_limited"] = False
        path = condition.get("path")
        try:
            if not isinstance(path, str) or not path:
                raise ValueError("Condition requires a nonempty repository-relative source path")
            source_path = inside(repo_path, path)
            key = str(source_path)
            if key in failures:
                raise ValueError(failures[key])
            if key not in cache:
                try:
                    with source_path.open("rb") as handle:
                        raw = handle.read(_SOURCE_BYTE_LIMIT + 1)
                    if len(raw) > _SOURCE_BYTE_LIMIT:
                        raise ValueError("Source exceeds bounded context-reading byte limit")
                    if b"\0" in raw:
                        raise ValueError("NUL-containing source is not read as text")
                    source = raw.decode("utf-8")
                    cache[key] = (source.splitlines(keepends=True), _contract_ranges(source, path))
                except (OSError, UnicodeError, ValueError, RecursionError) as error:
                    failures[key] = str(error)
                    raise
            lines, contracts = cache[key]
            start, end = condition.get("line_start"), condition.get("line_end")
            if type(start) is not int or type(end) is not int or start < 1 or end < start or end > len(lines):
                raise ValueError("Invalid target source line range")

            context: list[dict[str, Any]] = []
            used_characters = 0
            budget_limited = False

            def append(left: int, right: int, kind: str, contract_kind: str | None = None) -> bool:
                nonlocal used_characters, budget_limited
                quote = "".join(lines[left - 1:right])
                if used_characters + len(quote) > _CONTEXT_CHARACTERS:
                    budget_limited = True
                    return False
                item: dict[str, Any] = {
                    "kind": kind, "path": path, "line_start": left, "line_end": right,
                    "quote": quote, "sha256": text_sha256(quote),
                    "applicability_status": "unverified_neighborhood",
                    "limitations": [_CONTEXT_LIMITATION],
                }
                if contract_kind is not None:
                    item["contract_kind"] = contract_kind
                context.append(item)
                used_characters += len(quote)
                return True

            left, right = max(1, start - 5), min(len(lines), end + 5)
            # Preserve the entire target's line range, even if it exceeds the
            # preferred neighborhood share; the hard budget still applies.
            while len("".join(lines[left - 1:right])) > _NEIGHBORHOOD_CHARACTERS and (left < start or right > end):
                budget_limited = True
                if right > end and (right - end >= start - left or left == start):
                    right -= 1
                else:
                    left += 1
            append(left, right, "target_neighborhood")

            eligible = [item for item in contracts if item[0] >= max(1, start - 80) and item[1] < start]
            nearest = sorted(eligible, key=lambda item: (-item[1], -item[0], item[2]))[:3]
            for contract_start, contract_end, contract_kind in nearest:
                append(contract_start, contract_end, "nearby_contract_candidate", contract_kind)
            condition["source_context"] = context
            condition["source_context_status"] = "available" if context else "withheld_budget"
            condition["source_context_budget_limited"] = budget_limited
        except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
            condition["source_context_errors"].append(str(error))
    return results


def condition_priority(condition: dict[str, Any]) -> float:
    path = condition.get("path", "").lower()
    score = 0.0
    if any(part in path.split("/") for part in ["test", "tests", "examples", "benchmarks"]):
        score -= 20
    if any(word in path for word in ["attention", "core/", "propagat", "cache", "index", "kernel", "sparse", "linear"]):
        score += 8
    if condition.get("kind") == "boundary":
        score += 4
    if condition.get("kind") == "configuration":
        score += 3
    if condition.get("threshold") not in [None, 0, 1, -1]:
        score += 2
    if condition.get("symbol"):
        score += 1
    return score


def code_context_pool(scan: dict[str, Any], limit: int = 16) -> list[dict[str, Any]]:
    # The same paper-independent pool is supplied to all three methods.
    conditions = sorted(scan.get("conditions", []), key=lambda c: (-condition_priority(c), c.get("path", ""), c.get("line_start", 0)))
    # Keep the leading context useful even if the shared prompt budget drops its
    # tail: first take one condition per file, then revisit files for diversity.
    first, remainder, file_seen = [], [], set()
    for condition in conditions:
        path = condition.get("path")
        if path in file_seen:
            remainder.append(condition)
        else:
            first.append(condition)
            file_seen.add(path)
    chosen, used, per_file = [], set(), {}
    for condition in first + remainder:
        identity = (condition.get("path"), condition.get("line_start"), condition.get("expression"))
        if identity in used or per_file.get(condition.get("path"), 0) >= 3:
            continue
        used.add(identity)
        per_file[condition.get("path")] = per_file.get(condition.get("path"), 0) + 1
        chosen.append(condition)
        if len(chosen) == limit:
            break
    return chosen


def discover_opportunities(paper_id: str, profile: dict[str, Any], scan: dict[str, Any],
                           method: str = "full", max_opportunities: int = 12) -> list[dict[str, Any]]:
    if method not in {"full", "code_only", "direct"}:
        raise ValueError(f"Unknown method: {method}")
    opportunities = []
    for condition in code_context_pool(scan, max_opportunities):
        query = " ".join(str(condition.get(k, "")) for k in ["path", "symbol", "variable", "expression"])
        evidence = [] if method == "code_only" else retrieve_evidence(profile, query, 2)
        overlap = max([e.get("lexical_overlap", 0) for e in evidence], default=0)
        opportunities.append({
            "opportunity_id": stable_id("op", paper_id, condition["condition_id"], method),
            "paper_id": paper_id, "condition": condition,
            "paper_evidence": evidence, "scope_status": "unknown",
            "scope_constraints": profile.get("scope_constraints", []) if method != "code_only" else [],
            "alignment_reason": "Code-only candidate" if method == "code_only" else f"Lexical retrieval shares {overlap} terms; semantic alignment is unverified.",
            "alignment_score": overlap, "backend": "deterministic_heuristic",
            "limitations": ["Input binding, paper relevance, and applicability require independent review."],
        })
    if method == "full":
        opportunities.sort(key=lambda o: (-o["alignment_score"], -condition_priority(o["condition"])))
    return opportunities
