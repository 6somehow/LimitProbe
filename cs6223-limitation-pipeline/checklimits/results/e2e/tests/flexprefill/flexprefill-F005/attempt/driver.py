"""Driver for Region X014: the length-equality guard in the block-wise prefill kernel.

The official entry `flex_prefill_attention` enforces `assert q.shape[1] == k.shape[1]`
(which is q_len == k_len) before dispatching, so the same guard at the target line is
unreachable through it.  We call the target function directly (call-chain index 1) with
q/k/v built from the witness inputs; everything the target needs is real repository code.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import triton_block_wise_prefill_attention


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    block_size = int(inputs["block_size"])
    head_dim = int(inputs["head_dim"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    num_block = int(inputs["num_block"])
    dtype = getattr(torch, str(inputs["q_dtype"]).split(".")[-1])

    q = torch.randn((batch_size, q_len, num_q_heads, head_dim), dtype=dtype)
    k = torch.randn((batch_size, k_len, num_kv_heads, head_dim), dtype=dtype)
    v = torch.randn((batch_size, k_len, num_kv_heads, head_dim), dtype=dtype)
    block_idx = torch.zeros((batch_size, num_q_heads, num_block), dtype=torch.int32)

    return triton_block_wise_prefill_attention(q, k, v, block_idx, block_size)
