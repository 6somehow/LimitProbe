"""Faithfulness check for the CPU arange stand-in."""
from __future__ import annotations

import torch


def check_arange(sim):
    cases = [
        ((5,), {}),
        ((2, 7), {}),
        ((1, 10, 3), {}),
        ((0, 6), {"dtype": torch.float32}),
        ((1, 5, 2), {"dtype": torch.float32}),
    ]
    for args, kwargs in cases:
        got = sim(*args, **kwargs)
        want = torch.arange(*args, **kwargs)
        if got.shape != want.shape or got.dtype != want.dtype or not torch.equal(got, want):
            return {"ok": False,
                    "detail": f"arange{args}{kwargs} gave {got.tolist()} ({got.dtype}), want {want.tolist()} ({want.dtype})",
                    "kind": "numeric"}
    return {"ok": True, "detail": "matches torch.arange on integer and float ranges", "kind": "numeric"}
