"""Deterministic templates for proposed candidate specifications, not test results."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import struct
from typing import Any

_DIRECT_VARIABLE = re.compile(r"^[A-Za-z_]\w*(?:(?:\.|::|->)[A-Za-z_]\w*)*$")
_TYPES = {"int": "integer", "integer": "integer", "float": "float", "number": "number",
          "bool": "boolean", "boolean": "boolean", "str": "string", "string": "string"}


def _deduplicate(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if not any(type(value) is type(other) and value == other for other in result):
            result.append(value)
    return result


def _float32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def _next_float32(value: float, positive: bool) -> float:
    value = _float32(value)
    if value == 0:
        return struct.unpack("!f", struct.pack("!I", 1 if positive else 0x80000001))[0]
    bits = struct.unpack("!I", struct.pack("!f", value))[0]
    bits += 1 if (value > 0) == positive else -1
    return struct.unpack("!f", struct.pack("!I", bits))[0]


def _constraints(opportunity: dict[str, Any], variable: str, method: str) -> list[dict[str, Any]]:
    result = []
    for item in opportunity.get("scope_constraints", []):
        if not isinstance(item, dict):
            continue
        if item.get("variable", item.get("parameter", item.get("name"))) != variable:
            continue
        if method == "code_only" and item.get("source", "paper") != "code":
            continue
        result.append(item)
    return result


def _valid_value(value: Any, constraints: list[dict[str, Any]], expected_type: str) -> tuple[bool, str | None]:
    if expected_type == "integer" and type(value) is not int:
        return False, "Value is not an integer."
    if expected_type == "float" and type(value) is not float:
        return False, "Value is not a floating-point probe."
    if expected_type == "boolean" and type(value) is not bool:
        return False, "Value is not a Boolean."
    if expected_type == "string" and type(value) is not str:
        return False, "Value is not a string."
    if type(value) is float and not math.isfinite(value):
        return False, "Non-finite probe withheld."
    for constraint in constraints:
        kind = _TYPES.get(str(constraint.get("type", "")))
        if kind and kind != "number":
            accepted, reason = _valid_value(value, [], kind)
            if not accepted:
                return accepted, reason
        choices = constraint.get("enum", constraint.get("choices", constraint.get("allowed_values")))
        if choices is not None:
            if not isinstance(choices, list):
                return False, "Malformed enumeration constraint."
            if not any(type(value) is type(choice) and value == choice for choice in choices):
                return False, "Value is outside the supplied enumeration."
        minimum = constraint.get("minimum", constraint.get("min"))
        maximum = constraint.get("maximum", constraint.get("max"))
        if minimum is not None or maximum is not None:
            if type(value) not in (int, float):
                return False, "Numerical range is incompatible with this probe type."
            for bound, is_minimum, inclusive in (
                (minimum, True, constraint.get("minimum_inclusive", True)),
                (maximum, False, constraint.get("maximum_inclusive", True)),
            ):
                if bound is None:
                    continue
                if type(inclusive) is not bool:
                    return False, "Malformed numerical range inclusivity flag."
                if type(bound) not in (int, float) or not math.isfinite(bound):
                    return False, "Malformed numerical range constraint."
                if (is_minimum and (value < bound or (not inclusive and value == bound))) or (
                    not is_minimum and (value > bound or (not inclusive and value == bound))
                ):
                    return False, "Value is outside the supplied numerical range."
        if "operator" in constraint and "value" in constraint:
            operator, bound = constraint["operator"], constraint["value"]
            if type(value) not in (int, float) or type(bound) not in (int, float):
                return False, "Operator constraint requires numerical values."
            if not math.isfinite(bound):
                return False, "Operator constraint bound must be finite."
            relation = {"<": lambda: value < bound, "<=": lambda: value <= bound,
                        ">": lambda: value > bound, ">=": lambda: value >= bound,
                        "==": lambda: value == bound, "!=": lambda: value != bound}.get(operator)
            if relation is None:
                return False, "Unsupported constraint operator."
            if not relation():
                return False, "Value violates the supplied operator constraint."
    return True, None


def _probes(condition: dict[str, Any], constraints: list[dict[str, Any]]) -> tuple[str, list[Any], list[str], str]:
    variable, threshold = str(condition.get("variable", "")), condition.get("threshold")
    expected = _TYPES.get(str(condition.get("value_type", "unknown")), "unknown")
    for constraint in constraints:
        provided_type = _TYPES.get(str(constraint.get("type", "")))
        if provided_type and provided_type != "number":
            expected = provided_type
    limitations: list[str] = []
    if condition.get("input_binding") == "derived_expression" or not _DIRECT_VARIABLE.fullmatch(variable):
        return "requires_input_mapping", [], ["Derived expression cannot be assigned as an external input; an adapter mapping is required."], expected
    if condition.get("kind") == "state":
        return "state_transition", [], ["No legal state-transition sequence is known; internal state values are not assigned directly."], expected
    if condition.get("kind") == "boundary" and type(threshold) in (int, float):
        if not math.isfinite(threshold):
            return "boundary", [], ["Non-finite threshold cannot be instantiated."], expected
        if expected == "integer":
            if type(threshold) is int or threshold.is_integer():
                middle = int(threshold)
                return "boundary", [middle - 1, middle, middle + 1], limitations, expected
            return "boundary", [math.floor(threshold), math.ceil(threshold)], limitations, expected
        if expected in ("float", "number"):
            expected = "float"
            try:
                middle = float(threshold)
                numeric_format = condition.get("numeric_format", "float64")
                if any(item.get("dtype") in ("float32", "fp32") for item in constraints):
                    numeric_format = "float32"
                if numeric_format == "float32":
                    middle = _float32(middle)
                    probes = [_next_float32(middle, False), middle, _next_float32(middle, True)]
                else:
                    probes = [math.nextafter(middle, -math.inf), middle, math.nextafter(middle, math.inf)]
                if not math.isfinite(middle):
                    raise OverflowError
                return "boundary", probes, limitations, expected
            except (OverflowError, struct.error):
                return "boundary", [], ["Threshold is not representable in the selected floating-point format."], expected
        return "boundary", [], ["Variable numerical type is unknown; numerical probes withheld."], expected
    if expected == "boolean":
        return "configuration_differential", [False, True], limitations, expected
    choices: list[Any] = []
    for constraint in constraints:
        supplied = constraint.get("enum", constraint.get("choices", constraint.get("allowed_values")))
        if isinstance(supplied, list):
            choices.extend(supplied)
    if choices:
        return "configuration_differential", _deduplicate(choices), limitations, expected
    return "configuration_differential", [], ["Legal alternative configuration values are unknown; no alternative is invented."], expected


def _oracle(opportunity: dict[str, Any], code_evidence: dict[str, Any], variable: str,
            preconditions: list[str]) -> dict[str, Any]:
    explicit = opportunity.get("proposed_oracle", opportunity.get("semantic_property", opportunity.get("oracle")))
    if isinstance(explicit, dict) and isinstance(explicit.get("relation", explicit.get("property")), str):
        relation = explicit.get("relation", explicit.get("property", "")).strip()
        if relation:
            limitations = list(explicit.get("limitations", []))
            evidence = copy.deepcopy(explicit.get("evidence", []))
            if not evidence:
                limitations.append("Explicit proposed property has no supporting evidence; independent review is required.")
            limitations.append("No execution or independent oracle validation was performed by this generator.")
            return {"type": explicit.get("type", "invariant"), "status": "proposed", "relation": relation,
                    "preconditions": list(explicit.get("preconditions", [])), "evidence": evidence,
                    "limitations": limitations, "semantic_validation_status": "unknown"}
    return {
        "type": "reachability", "status": "proposed",
        "relation": f"Record branch or predicate observations while varying {variable}; do not infer functional correctness from a branch change.",
        "preconditions": list(preconditions), "evidence": [copy.deepcopy(code_evidence)],
        "limitations": ["Reachability is an observation check, not a semantic correctness oracle.",
                        "Execution has not been performed; semantic correctness remains unknown."],
        "semantic_validation_status": "unknown",
    }


def generate_candidates(opportunities: list[dict[str, Any]], method: str = "full",
                        max_candidates: int = 5) -> list[dict[str, Any]]:
    """Instantiate one grouped candidate per opportunity, with honest unknowns.

    Supported constraint keys are variable/parameter/name, type, minimum/maximum
    (or min/max), inclusive-bound flags, enum/choices/allowed_values, operator/value
    and dtype. ``code_only`` deliberately withholds paper-derived constraints.
    This deterministic template backend does not simulate an LLM baseline.
    """
    if type(max_candidates) is not int or max_candidates < 0:
        raise ValueError("max_candidates must be a nonnegative integer")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a nonempty label")
    candidates: list[dict[str, Any]] = []
    for opportunity in opportunities[:max_candidates]:
        condition = copy.deepcopy(opportunity.get("condition", {}))
        variable = str(condition.get("variable", ""))
        constraints = _constraints(opportunity, variable, method)
        strategy, probes, limitations, expected_type = _probes(condition, constraints)
        scope = "unknown" if method == "code_only" else opportunity.get("scope_status", "unknown")
        scope = scope if scope in {"in_scope", "out_of_scope", "unknown", "code_only", "abstain"} else "unknown"
        inputs: list[dict[str, Any]] = []
        withheld: list[dict[str, Any]] = []
        for value in _deduplicate(probes):
            valid, reason = _valid_value(value, constraints, expected_type)
            if scope in {"out_of_scope", "abstain"}:
                valid, reason = False, "Opportunity is out of scope or abstained; inputs withheld."
            if valid:
                inputs.append({variable: value})
            else:
                if type(value) is float and not math.isfinite(value):
                    # Preserve why a probe was rejected without putting NaN or
                    # Infinity into the JSON artifact's candidate input values.
                    withheld.append({"variable": variable, "value_repr": repr(value), "reason": reason})
                else:
                    withheld.append({"inputs": {variable: value}, "reason": reason})
        if scope in {"out_of_scope", "abstain"} and not probes:
            limitations.append("Opportunity is out of scope or abstained; inputs withheld.")
        if scope in {"unknown", "code_only"}:
            limitations.append("Paper-scope validity is unknown; these values are static proposals, not approved executions.")
        if condition.get("value_type_source") in {"comparison_literal_probe", "lexical_declaration"}:
            limitations.append("Variable type is inferred heuristically and needs input-contract review.")
        limitations.extend(opportunity.get("limitations", []))
        limitations.extend(condition.get("limitations", []))
        if withheld:
            limitations.append("Probes violating known type/domain constraints were withheld.")
        if strategy == "configuration_differential" and len(inputs) < 2:
            limitations.append("A legal configuration pair is unavailable; no differential comparison is claimed.")
        if strategy == "boundary" and inputs:
            operator, threshold = condition.get("operator"), condition.get("threshold")
            comparisons = {"<": lambda x: x < threshold, "<=": lambda x: x <= threshold,
                           ">": lambda x: x > threshold, ">=": lambda x: x >= threshold,
                           "==": lambda x: x == threshold, "!=": lambda x: x != threshold}
            compare = comparisons.get(operator)
            if compare and len({compare(item[variable]) for item in inputs}) < 2:
                limitations.append("Known domain constraints prevent crossing this predicate; reachability across both outcomes is unconfirmed.")
        preconditions = [str(item) for item in opportunity.get("preconditions", [])]
        preconditions.extend(str(item) for item in condition.get("activation_preconditions", []))
        preconditions.append(f"Confirm how code variable {variable!r} maps to a supported external input or configuration.")
        preconditions.append("Hold unrelated inputs and configuration constant; establish valid target setup.")
        code_evidence = copy.deepcopy(condition.get("evidence", {}))
        paper_evidence = [] if method == "code_only" else copy.deepcopy(opportunity.get("paper_evidence", []))
        oracle = _oracle(opportunity, code_evidence, variable, preconditions)
        if method == "code_only" and oracle["type"] != "reachability":
            # An oracle supplied with paper evidence is not code-only information.
            explicit = opportunity.get("proposed_oracle", opportunity.get("semantic_property", opportunity.get("oracle", {})))
            if explicit.get("source", "paper") != "code":
                oracle = _oracle({}, code_evidence, variable, preconditions)
        identifier_payload = json.dumps([opportunity.get("opportunity_id"), method, strategy, inputs],
                                        sort_keys=True, ensure_ascii=False, allow_nan=False)
        candidates.append({
            "candidate_id": "candidate-" + hashlib.sha256(identifier_payload.encode()).hexdigest()[:16],
            "opportunity_id": opportunity.get("opportunity_id"), "paper_id": opportunity.get("paper_id"),
            "strategy": strategy, "inputs": inputs, "preconditions": preconditions,
            "target_condition": condition, "observation": f"Record outcome of {condition.get('expression', variable)} and selected branch/state without asserting semantic correctness.",
            "paper_evidence": paper_evidence, "code_evidence": code_evidence,
            "oracle": oracle, "scope_status": scope, "limitations": _deduplicate(limitations),
            "withheld_inputs": withheld, "backend": "deterministic_heuristic", "method": method,
            "execution_status": "not_run", "input_binding_status": "requires_adapter_mapping",
            "scope_constraints": copy.deepcopy(constraints),
        })
    return candidates
