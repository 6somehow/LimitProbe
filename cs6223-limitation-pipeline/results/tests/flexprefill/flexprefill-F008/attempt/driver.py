"""Driver: exercise the target assert in triton_block_wise_prefill_attention.

The Region's target is the assert at flex_prefill/ops/flex_prefill_attention.py:1256 inside
triton_block_wise_prefill_attention.  The witness supplies `num_block` (the width of the padded
block_idx tensor, block_idx.shape[2]) directly, so the driver calls that function with an explicit
block_idx list of the requested width.  All arguments (q/k/v shapes, block_size) are built from the
harness inputs; nothing in the repository is modified and no GPU kernel needs to run before the
target decision.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import triton_block_wise_prefill_attention


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    dtype = getattr(torch, inputs["dtype"])

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    num_block = int(inputs["num_block"])

    q = torch.zeros((batch_size, q_len, num_q_heads, head_dim), dtype=dtype)
    k = torch.zeros((batch_size, k_len, num_kv_heads, head_dim), dtype=dtype)
    v = torch.zeros((batch_size, k_len, num_kv_heads, head_dim), dtype=dtype)

    block_idx = [
        [torch.arange(num_block, dtype=torch.int64) for _ in range(num_q_heads)]
        for _ in range(batch_size)
    ]

    return triton_block_wise_prefill_attention(q, k, v, block_idx, block_size)
