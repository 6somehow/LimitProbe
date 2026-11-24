"""Driver: call flex_prefill_attention (the official entry) with CPU tensors built from `inputs`.

Seeds and thread counts are fixed; no GPU is touched before the target assertion. GPU-only
kernel launchers that run after the target are replaced by declared mocks (see sim.py).
"""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention


def _dtype(name):
    return getattr(torch, name)


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    dtype = _dtype(inputs["dtype"])

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, q_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, q_len, num_kv_heads, head_dim, dtype=dtype)

    return flex_prefill_attention(
        q,
        k,
        v,
        float(inputs["gamma"]),
        tau=float(inputs["tau"]),
        min_budget=inputs["min_budget"],
        max_budget=inputs["max_budget"],
        gqa_interleave=bool(inputs["gqa_interleave"]),
        softmax_scale=inputs["softmax_scale"],
        block_size=int(inputs["block_size"]),
        return_computational_ratio=bool(inputs["return_computational_ratio"]),
    )
