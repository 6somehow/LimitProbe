"""Driver for flexprefill-F007.

The official entry (flex_prefill_attention) builds block_idx itself from q and k, so
len(block_idx[0]) always equals num_q_heads there and the guard at line 1245 can never
fail through that entry. The guard constrains a caller-supplied block_idx, so this driver
calls the next function in the chain, triton_block_wise_attention, which forwards the
block_idx it receives to the target function unchanged.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import triton_block_wise_attention


def run(inputs):
    torch.manual_seed(int(inputs["torch_seed"]))

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    block_idx_heads = int(inputs["block_idx_heads"])
    block_idx_ids = [int(v) for v in inputs["block_idx_ids"]]

    q = torch.zeros(
        batch_size, q_len, num_q_heads, head_dim, dtype=torch.bfloat16
    )
    k = torch.zeros(
        batch_size, k_len, num_kv_heads, head_dim, dtype=torch.bfloat16
    )
    v = torch.zeros(
        batch_size, k_len, num_kv_heads, head_dim, dtype=torch.bfloat16
    )

    # A list[list[Tensor]] of active-block ids, as get_active_blocks returns it.
    # For single-batch inputs the last group is the same as the first; a multi-batch
    # extra negative can make the last group shorter so block_idx[0] and block_idx[-1]
    # are distinguishable.
    if batch_size > 1:
        last_heads = int(inputs["last_block_idx_heads"])
    else:
        last_heads = block_idx_heads
    heads_per_batch = [block_idx_heads] * (batch_size - 1) + [last_heads]
    block_idx = [
        [
            torch.tensor(block_idx_ids, dtype=torch.int32)
            for _ in range(heads)
        ]
        for heads in heads_per_batch
    ]

    return triton_block_wise_attention(q, k, v, block_idx, block_size)
