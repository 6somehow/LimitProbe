"""Fixture for codeside/effect_anchor.py: statements an effect label can point at."""
import os


def check(flag, msg):
    if not flag:
        raise ValueError(msg)


def run(x, mode, retries):
    assert x >= 0, "x must be non-negative"
    if x > 100:
        raise ValueError("too large")
    while retries > 3:
        retries -= 1
    if mode == "slow":
        x = x * 2
    elif mode == "fast":
        x = x + 1
    level = os.getenv("LEVEL", "1")
    check(x != 7, "seven")
    try:
        x = int(level) + x
    except ValueError as e:
        raise e
    return x
