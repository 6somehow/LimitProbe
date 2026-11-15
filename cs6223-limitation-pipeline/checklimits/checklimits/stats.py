"""Small statistics used by the confidence rules."""
from __future__ import annotations

import math

Z95 = 1.959964  # two-sided 95 %


def wilson_lower(k: int, n: int, z: float = Z95) -> float:
    """Lower bound of the Wilson score interval for k successes in n trials (Wilson 1927).
    Used for the mutant kill rate: with few mutants the observed rate alone says little."""
    if n <= 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / denom)


def rule_of_three(n: int) -> float:
    """Approximate 95 % upper bound on a failure probability after n failure-free trials: 3/n
    (Hanley & Lippman-Hand 1983). Returned capped at 1.0."""
    return 1.0 if n <= 0 else min(1.0, 3.0 / n)
