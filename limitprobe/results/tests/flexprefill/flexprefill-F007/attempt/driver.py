"""Driver: exercise the target assertion in triton_block_wise_prefill_attention.

The Region target is `assert len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads`
inside triton_block_wise_prefill_attention. Its guard reads `block_idx`, which is a parameter of
that function but is *constructed internally* by the official entry flex_prefill_attention
(get_active_blocks always returns exactly [batch_size, num_q_heads] lists). The assertion is
therefore unreachable through the official entry; the checked factor (the head width of the
caller-supplied block_idx list) can only be varied by calling the target function directly.
That is the recorded entry_reason.

CPU only, deterministic (zeros, fixed seed, single thread), no stand-ins.
"""

import torch

torch.set_num_threads(1)

from flex_prefill.ops.flex_prefill_attention import triton_block_wise_prefill_attention


def run(inputs):
    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    num_q_heads = int(inputs["num_q_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_width = int(inputs["block_idx_head_width"])
    last_width = int(inputs["block_idx_last_width"])
    seed = int(inputs["seed"])
    grid_offset = int(inputs["grid_offset"])
    softmax_scale = inputs["softmax_scale"]
    gqa_interleave = bool(inputs["gqa_interleave"])

    torch.manual_seed(seed)

    q = torch.zeros(batch_size, q_len, num_q_heads, head_dim, dtype=torch.bfloat16)
    k = torch.zeros(batch_size, k_len, num_kv_heads, head_dim, dtype=torch.bfloat16)
    v = torch.zeros(batch_size, k_len, num_kv_heads, head_dim, dtype=torch.bfloat16)

    block_idx = []
    for b in range(batch_size):
        width = last_width if b == batch_size - 1 else head_width
        block_idx.append([torch.tensor([i], dtype=torch.int64) for i in range(width)])

    return triton_block_wise_prefill_attention(
        q,
        k,
        v,
        block_idx,
        block_size,
        grid_offset=grid_offset,
        softmax_scale=softmax_scale,
        gqa_interleave=gqa_interleave,
    )
