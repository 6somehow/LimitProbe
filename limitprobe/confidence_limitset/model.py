"""Ordinal evidence bands; these are rules, not estimates of correctness."""
from math import sqrt


def wilson_interval(found, total, z=1.959963984540054):
    if not 0 <= found <= total:
        raise ValueError("found must be between zero and total")
    if not total:
        return None
    p = found / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def score_confidence(record, repeats=None, sources=None, code_available=True):
    """Score a checklimits report; repeats are matched booleans, sources a mapping.

    Source values are True (supports), False (disagrees), or None (unknown).
    Matching repeats to a claim is the caller's responsibility.
    """
    if repeats is not None and any(type(v) is not bool for v in repeats):
        raise ValueError("repeats must contain booleans")
    if sources is not None and any(v is not None and type(v) is not bool for v in sources.values()):
        raise ValueError("source values must be true, false or null")
    finding = record.get("finding") or record
    tier = record.get("level") if record.get("status") == "tested" and record.get("verdict") == "yes" else None
    if record.get("status") == "not_run":
        tier = (record.get("analysis") or {}).get("tier")
    levels = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "A0": 0, "A1": 1, "A2": 2}
    rank = levels.get(tier, 0)
    effective_tier = tier if tier in levels else None
    if not code_available:
        rank = min(rank, 1)
        if effective_tier and rank < levels[effective_tier]:
            effective_tier = "A1"
    defeaters = dict(record.get("defeaters") or {})
    for doubt in record.get("open_doubts") or []:
        if doubt.get("id"):
            defeaters[doubt["id"]] = doubt.get("status", "open")
    open_defeaters = {key: value for key, value in defeaters.items() if value != "eliminated"}
    fraction = sum(repeats) / len(repeats) if repeats else None
    source_values = sources or {}
    supporting = sum(value is True for value in source_values.values())
    disagreement = any(value is False for value in source_values.values())
    # Higher bands require additional positive evidence, never inferred from absence.
    if rank >= 3 and (fraction != 1 or len(repeats or []) < 2 or supporting < 2 or disagreement):
        rank = 2
    if rank >= 2 and (fraction is None or fraction < 0.5 or supporting < 2 or disagreement):
        rank = 1
    if open_defeaters:
        rank = min(rank, 1)
    return {"band": f"C{rank}", "label": "uncalibrated", "items": {
        "evidence_tier": tier, "effective_tier": effective_tier,
        "replication": {"found": sum(repeats) if repeats else 0, "n": len(repeats or []), "fraction": fraction},
        "sources": source_values, "open_defeaters": open_defeaters,
        "code_available": code_available},
        "importance": (finding.get("process_confidence") or {}).get("importance")}


def reliability_table(results, threshold=10):
    """Group validation observations with boolean found and band; no oracle => omit."""
    if threshold < 1:
        raise ValueError("threshold must be positive")
    groups = {}
    for row in results:
        found = row.get("found")
        if found is None:
            continue
        if type(found) is not bool or row.get("band") not in {"C0", "C1", "C2", "C3"}:
            raise ValueError("expected band C0-C3 and boolean found")
        group = groups.setdefault(row["band"], [])
        group.append(found)
    return [{"band": band, "n": len(values), "found": sum(values),
             "coverage": sum(values) / len(values), "wilson_ci": wilson_interval(sum(values), len(values)),
             "assessment": "n too small" if len(values) < threshold else "sufficient n"}
            for band, values in sorted(groups.items())]
