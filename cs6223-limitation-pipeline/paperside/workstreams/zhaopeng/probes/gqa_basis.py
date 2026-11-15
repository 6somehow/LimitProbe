"""Small independent algebra control, not an InfiniGen execution experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def rotate(v: list[float], quarter_turns: int) -> list[float]:
    x, y = v
    for _ in range(quarter_turns % 4):
        x, y = -y, x
    return [x, y]


def probe() -> dict:
    # Two query heads share each of two KV heads; all per-head dimensions agree.
    queries = [[1.0, 2.0], [3.0, 1.0], [-2.0, 4.0], [2.0, 3.0]]
    keys = [[2.0, 1.0], [1.0, -2.0]]
    groups = [0, 0, 1, 1]
    baseline = [dot(q, keys[g]) for q, g in zip(queries, groups)]
    group_bases = [1, 2]
    shared = [dot(rotate(q, group_bases[g]), rotate(keys[g], group_bases[g]))
              for q, g in zip(queries, groups)]
    per_query_bases = [1, 2, 2, 3]
    mixed = [dot(rotate(q, angle), rotate(keys[g], group_bases[g]))
             for q, g, angle in zip(queries, groups, per_query_bases)]
    duplicated = [dot(rotate(q, angle), rotate(keys[g], angle))
                  for q, g, angle in zip(queries, groups, per_query_bases)]
    errors = lambda ys: [abs(a - b) for a, b in zip(baseline, ys)]
    result = {"kind": "independent_algebra_control", "hq": 4, "hkv": 2, "head_dim": 2,
              "reference_dot_products": baseline, "group_shared_basis_errors": errors(shared),
              "mismatched_basis_errors": errors(mixed), "per_query_matched_key_errors": errors(duplicated),
              "group_shared_basis_preserves_dot_products": shared == baseline,
              "mismatched_basis_counterexample_found": mixed != baseline,
              "per_query_matched_keys_preserve_dot_products": duplicated == baseline,
              "target_repository_executed": False, "cache_bytes_measured": False,
              "limitations": ["This is not a proof of a target bug or necessary KV expansion.",
                              "A common orthogonal basis per KV group preserves the raw dot products.",
                              "Partial-column selection, RoPE order and runtime cost are not tested."]}
    assert shared == baseline and mixed != baseline and duplicated == baseline
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    result = probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
