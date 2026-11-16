"""Driver for flexprefill-F008 (target: assert on block_idx width vs triangular grid).

The run starts at the official entry `flex_prefill_attention`. On CPU that entry reaches
`get_active_blocks`, which launches Triton GPU kernels (triton_bnhd_pool / triton_bhn_sumpool); the launch
fails before the target line. We keep that real call (no stand-ins), and when it fails for lack of a GPU we
continue on the same official call chain with `triton_block_wise_attention`, which takes `block_idx`
directly. Everything from there up to (and including) the target assert is the repository's real code.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import (
    flex_prefill_attention,
    triton_block_wise_attention,
)

torch.set_num_threads(1)


def run(inputs):
    torch.manual_seed(0)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    num_block = int(inputs["num_block"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    min_budget = int(inputs["min_budget"])
    gamma = float(inputs["gamma"])
    tau = float(inputs["tau"])

    q = torch.zeros((batch_size, q_len, num_q_heads, head_dim), dtype=torch.bfloat16)
    k = torch.zeros((batch_size, k_len, num_kv_heads, head_dim), dtype=torch.bfloat16)
    v = torch.zeros((batch_size, k_len, num_kv_heads, head_dim), dtype=torch.bfloat16)
    block_idx = torch.zeros((batch_size, num_q_heads, num_block), dtype=torch.int64)

    try:
        return flex_prefill_attention(
            q,
            k,
            v,
            gamma,
            tau,
            min_budget=min_budget,
            block_size=block_size,
        )
    except RuntimeError:
        # CPU-only: the official entry stops in get_active_blocks at a GPU kernel launch before the target.
        return triton_block_wise_attention(q, k, v, block_idx, block_size)
