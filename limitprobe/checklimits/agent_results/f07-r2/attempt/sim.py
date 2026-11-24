"""CPU stand-ins for the two Triton kernel launchers touched *after* the target assertion.

Both are only reached on the negative (batch_size == 1) run, after line 1824.  `bnhd_pool` is a
plain-torch block average pool written to match the Triton kernel's avg branch; `block_wise_attention`
delegates to the repository's own `torch_block_wise_attention` reference implementation.
"""

import math

import torch


def bnhd_pool(x, kernel_size, pool_type="avg"):
    b, n, h, d = x.shape
    m = math.ceil(n / kernel_size)
    y = torch.empty(b, m, h, d, dtype=x.dtype, device=x.device)
    for i in range(m):
        chunk = x[:, i * kernel_size : min((i + 1) * kernel_size, n)].float()
        if pool_type == "avg":
            val = chunk.mean(1)
        elif pool_type == "sum":
            val = chunk.sum(1)
        elif pool_type == "max":
            val = chunk.amax(1)
        elif pool_type == "min":
            val = chunk.amin(1)
        elif pool_type == "maxabs":
            val = chunk.abs().amax(1)
        else:
            val = chunk.mean(1)
        y[:, i] = val.to(x.dtype)
    return y


def block_wise_attention(q, k, v, block_idx, block_size, grid_offset=0,
                         softmax_scale=None, gqa_interleave=False):
    from flex_prefill.ops.flex_prefill_attention import torch_block_wise_attention

    if not isinstance(block_idx, torch.Tensor):
        batch_size, q_len, num_heads, _ = q.shape
        k_len = k.shape[1]
        flat = [item.view(-1, 1) for sublist in block_idx for item in sublist]
        padded = torch.nn.utils.rnn.pad_sequence(flat, batch_first=True, padding_value=0)
        block_idx = padded.view(batch_size, num_heads, -1)
    block_idx = block_idx.sort(-1).values
    return torch_block_wise_attention(q, k, v, block_idx, block_size, grid_offset)
