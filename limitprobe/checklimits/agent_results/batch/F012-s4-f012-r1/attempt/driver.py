"""Driver for flexprefill-F012: call the official entry point.

The target is the module-level `causal_mask` cache in get_active_blocks (state_dependent):
a fresh process takes the `if causal_mask is None:` branch; after one earlier call the
cache is already set, so the checked call does not take it.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    block_size = int(inputs["block_size"])
    head_dim = int(inputs["head_dim"])
    min_budget = int(inputs["min_budget"])
    max_budget = int(inputs["max_budget"])
    num_heads = int(inputs["num_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    gamma = float(inputs["gamma"])
    tau = float(inputs["tau"])
    dtype = getattr(torch, str(inputs["dtype"]))

    q = torch.randn(batch_size, q_len, num_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, q_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, q_len, num_kv_heads, head_dim, dtype=dtype)

    return flex_prefill_attention(
        q,
        k,
        v,
        gamma,
        tau=tau,
        min_budget=min_budget,
        max_budget=max_budget,
        gqa_interleave=False,
        block_size=block_size,
    )
