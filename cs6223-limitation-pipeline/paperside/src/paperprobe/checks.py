"""Mechanical provenance and input checks; these do not prove semantics or execution."""
from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Any

from .io import inside, text_sha256


def _finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _finite(v) for k, v in value.items())
    return value is None or isinstance(value, (str, bool, int))


def validate_candidate_shape(candidate: dict[str, Any]) -> list[str]:
    if not isinstance(candidate, dict):
        return ["candidate must be an object"]
    errors = []
    for name in ["candidate_id", "paper_id", "strategy", "observation"]:
        if not isinstance(candidate.get(name), str) or not candidate[name].strip():
            errors.append(f"{name} must be a nonempty string")
    inputs = candidate.get("inputs")
    if not isinstance(inputs, list) or not inputs or not all(isinstance(v, dict) and v for v in inputs):
        errors.append("inputs must contain at least one nonempty parameter object")
    if not _finite(inputs):
        errors.append("inputs must be finite JSON values")
    if not isinstance(candidate.get("preconditions"), list) or not all(isinstance(v, str) for v in candidate.get("preconditions", [])):
        errors.append("preconditions must be strings")
    if not isinstance(candidate.get("target_condition"), dict):
        errors.append("target_condition must be an object")
    elif candidate["target_condition"].get("variable") is not None and not isinstance(candidate["target_condition"]["variable"], str):
        errors.append("target_condition.variable must be a string when provided")
    if not isinstance(candidate.get("code_evidence"), dict):
        errors.append("code_evidence must be an object")
    if not isinstance(candidate.get("paper_evidence"), list) or not all(isinstance(item, dict) for item in candidate.get("paper_evidence", [])):
        errors.append("paper_evidence must be a list")
    oracle = candidate.get("oracle")
    if not isinstance(oracle, dict) or not isinstance(oracle.get("status"), str) or oracle.get("status") not in {"proposed", "requires_execution", "unknown", "reviewed"}:
        errors.append("oracle must declare a proposal/review status")
    if not isinstance(candidate.get("scope_status"), str) or candidate.get("scope_status") not in {"in_scope", "out_of_scope", "unknown", "code_only"}:
        errors.append("scope_status must be explicit")
    if "scope_constraints" in candidate and (not isinstance(candidate["scope_constraints"], list) or not all(isinstance(item, dict) for item in candidate["scope_constraints"])):
        errors.append("scope_constraints must be a list of objects")
    return errors


def check_candidate(candidate: dict[str, Any], repo_path: Path,
                    pages: dict[str, Any], expected_commit: str | None = None) -> dict[str, Any]:
    checks, warnings = [], []

    def record(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    errors = validate_candidate_shape(candidate)
    record("schema", "fail" if errors else "pass", "; ".join(errors) or "Required fields and finite input values present")
    # Keep the original candidate intact: bad fields remain visible to reviewers.
    candidate = candidate if isinstance(candidate, dict) else {}
    evidence = candidate.get("code_evidence")
    try:
        if not isinstance(evidence, dict):
            raise ValueError("Code evidence must be an object")
        if not isinstance(evidence.get("quote"), str) or not evidence["quote"]:
            raise ValueError("Missing code quotation")
        if not isinstance(evidence.get("path"), str) or not evidence["path"]:
            raise ValueError("Code evidence path must be a nonempty string")
        source = inside(repo_path, evidence["path"])
        lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
        start, end = evidence["line_start"], evidence["line_end"]
        if type(start) is not int or type(end) is not int or start < 1 or end < start or end > len(lines):
            raise ValueError("Invalid source line range")
        segment = "".join(lines[start - 1:end])
        if evidence["quote"] not in segment:
            raise ValueError("Quotation not found inside the specified line range")
        if evidence.get("sha256") != text_sha256(evidence["quote"]):
            raise ValueError("Code quotation SHA256 mismatch")
        record("code_provenance", "pass", "Exact quotation and checksum match the pinned source location")
    except (KeyError, OSError, ValueError, TypeError) as error:
        record("code_provenance", "fail", str(error))

    if expected_commit:
        try:
            actual = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
            success = actual.returncode == 0 and actual.stdout.strip() == expected_commit
            record("repository_commit", "pass" if success else "fail", "Pinned commit matches" if success else "Repository HEAD differs from the recorded commit")
        except OSError as error:
            record("repository_commit", "fail", f"Cannot verify repository commit: {error}")
    else:
        record("repository_commit", "unknown", "No expected commit provided")

    page_lookup, page_errors = {}, []
    source_pages = pages.get("pages", []) if isinstance(pages, dict) else None
    if not isinstance(source_pages, list):
        page_errors.append("Extracted pages must be a list")
    else:
        for number, page in enumerate(source_pages):
            if not isinstance(page, dict) or type(page.get("page")) is not int or not isinstance(page.get("text"), str):
                page_errors.append(f"Malformed extracted page at index {number}")
            elif page["page"] in page_lookup and page_lookup[page["page"]] != page["text"]:
                page_errors.append(f"Conflicting extracted text for page {page['page']}")
            else:
                page_lookup[page["page"]] = page["text"]
    paper_evidence = candidate.get("paper_evidence")
    if not isinstance(paper_evidence, list):
        record("paper_provenance", "fail", "Paper evidence must be a list; malformed data is not an absent citation")
    elif not paper_evidence:
        record("paper_provenance", "not_applicable", "No paper quotation supplied; this does not automatically invalidate code-only relevance")
    else:
        failures = list(page_errors)
        for number, e in enumerate(paper_evidence):
            try:
                if not isinstance(e, dict):
                    raise ValueError(f"Paper evidence item {number} must be an object")
                if not isinstance(e.get("quote"), str) or not e["quote"]:
                    raise ValueError(f"Paper evidence item {number} needs a nonempty quote")
                if type(e.get("page")) is not int:
                    raise ValueError(f"Paper evidence item {number} needs an integer page")
                if e["quote"] not in page_lookup[e["page"]]:
                    failures.append("Paper quotation/page mismatch")
                if e.get("sha256") != text_sha256(e["quote"]):
                    failures.append("Paper quotation checksum mismatch")
                if e.get("paper_id") != candidate.get("paper_id"):
                    failures.append("Paper identity mismatch")
            except (KeyError, TypeError, ValueError) as error:
                failures.append(f"Incomplete or invalid paper evidence: {error}")
        record("paper_provenance", "fail" if failures else "pass", "; ".join(failures) or "Exact extracted-page quotations and checksums match")

    condition = candidate.get("target_condition")
    condition = condition if isinstance(condition, dict) else {}
    variable, threshold = condition.get("variable"), condition.get("threshold")
    inputs = candidate.get("inputs")
    inputs = inputs if isinstance(inputs, list) else []
    values = [v[variable] for v in inputs if isinstance(v, dict) and variable in v] if isinstance(variable, str) and variable else []
    if candidate.get("strategy") == "boundary" and isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
        numbers = [v for v in values if type(v) is int or (type(v) is float and math.isfinite(v))]
        if type(threshold) is float and not math.isfinite(threshold):
            numbers = []
        crossed = any(v < threshold for v in numbers) and any(v > threshold for v in numbers)
        record("boundary_relation", "pass" if crossed else "unknown", "Abstract values lie on both sides of the numeric threshold" if crossed else "Cannot establish both-sided probing from the supplied abstract values")
    elif candidate.get("strategy") == "configuration_differential":
        distinct = {repr(v) for v in values}
        record("configuration_relation", "pass" if len(distinct) >= 2 else "unknown", "Distinct abstract configuration values supplied" if len(distinct) >= 2 else "Distinct configurations not established")
    else:
        record("test_relation", "unknown", "This strategy needs semantic or adapter-specific assessment")

    constraint_errors, constraint_count = [], 0
    constraints = candidate.get("scope_constraints", [])
    if not isinstance(constraints, list):
        constraint_errors.append("scope_constraints must be a list")
        constraints = []
    for number, constraint in enumerate(constraints):
        if not isinstance(constraint, dict) or not isinstance(constraint.get("variable"), str) or not constraint["variable"]:
            constraint_errors.append(f"Constraint {number} must have a string variable")
            continue
        name = constraint["variable"]
        malformed = False
        for bound in ("minimum", "maximum"):
            if bound in constraint and (type(constraint[bound]) not in (int, float) or (type(constraint[bound]) is float and not math.isfinite(constraint[bound]))):
                constraint_errors.append(f"{name} has invalid {bound}")
                malformed = True
        for flag in ("minimum_inclusive", "maximum_inclusive"):
            if flag in constraint and type(constraint[flag]) is not bool:
                constraint_errors.append(f"{name} has invalid {flag}")
                malformed = True
        choices = constraint.get("enum", constraint.get("choices"))
        if choices is not None and not isinstance(choices, list):
            constraint_errors.append(f"{name} choices must be a list")
            malformed = True
        if malformed:
            continue
        for item in inputs:
            if not isinstance(item, dict) or name not in item:
                continue
            constraint_count += 1
            value = item[name]
            try:
                expected_type = constraint.get("type")
                if not isinstance(expected_type, (str, type(None))):
                    constraint_errors.append(f"{name} has invalid declared type")
                elif expected_type in {"integer", "int"} and (not isinstance(value, int) or isinstance(value, bool)):
                    constraint_errors.append(f"{name} is not an integer")
                if isinstance(expected_type, str) and expected_type in {"number", "float"} and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                    constraint_errors.append(f"{name} is not numeric")
                if "minimum" in constraint and value < constraint["minimum"]:
                    constraint_errors.append(f"{name} below declared minimum")
                if "maximum" in constraint and value > constraint["maximum"]:
                    constraint_errors.append(f"{name} above declared maximum")
                if not constraint.get("minimum_inclusive", True) and value == constraint.get("minimum"):
                    constraint_errors.append(f"{name} equals exclusive minimum")
                if not constraint.get("maximum_inclusive", True) and value == constraint.get("maximum"):
                    constraint_errors.append(f"{name} equals exclusive maximum")
                if choices is not None and not any(type(value) is type(choice) and value == choice for choice in choices):
                    constraint_errors.append(f"{name} outside declared choices")
            except TypeError:
                constraint_errors.append(f"{name} has incompatible constraint type")
    record("declared_input_constraints", "fail" if constraint_errors else ("pass" if constraint_count else "unknown"), "; ".join(constraint_errors) or ("Inputs satisfy the declared constraints; their semantic basis still requires review" if constraint_count else "No independently confirmed scope constraints available"))

    record("scope_semantics", "unknown", "Paper scope and code alignment need independent human review")
    record("oracle_semantics", "unknown", "Proposed oracle is not validated by these mechanical checks")
    warnings += ["Input binding and path reachability have not been executed.", "Mechanical provenance checks do not establish a semantic oracle or a bug."]
    status = "failed" if any(c["status"] == "fail" for c in checks) else "passed"
    return {"static_status": status, "checks": checks, "runtime_status": "not_run", "human_review_status": "pending", "warnings": warnings}
