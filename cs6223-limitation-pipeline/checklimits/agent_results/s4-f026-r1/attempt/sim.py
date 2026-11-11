"""CPU stand-ins for GPU-only kernels reached AFTER the target line.

All three replace launchers that run only once the branch decision at line 1842 has
already been recorded.  Nothing here is touched before the target.
"""

import math

import torch

from flex_prefill.ops.flex_prefill_attention import torch_block_wise_attention


def _causal_attention(q, k, v, causal=True, softmax_scale=None, gqa_interleave=False):
    b, n, h, d = q.shape
    num_kv_heads = k.shape[2]
    if num_kv_heads != h:
        rep = h // num_kv_heads
        k = k.repeat_interleave(rep, dim=2)
        v = v.repeat_interleave(rep, dim=2)
    scale = (1.0 / math.sqrt(d)) if softmax_scale is None else softmax_scale
    scores = torch.einsum("bihd,bjhd->bhij", q.float(), k.float()) * scale
    if causal:
        k_len = k.shape[1]
        mask = torch.tril(torch.ones(n, k_len, dtype=torch.bool))
        scores = scores.masked_fill(~mask, float("-inf"))
    weights = torch.softmax(scores, dim=-1)
    out = torch.einsum("bhij,bjhd->bihd", weights, v.float())
    return out.to(q.dtype)


def flash_attn_func(q, k, v, *args, **kwargs):
    causal = kwargs.get("causal", True)
    scale = kwargs.get("softmax_scale", None)
    gqa = kwargs.get("gqa_interleave", False)
    return _causal_attention(q, k, v, causal=causal, softmax_scale=scale, gqa_interleave=gqa)


def triton_flash_attention(q, k, v, causal=True, softmax_scale=None, gqa_interleave=False):
    return _causal_attention(q, k, v, causal=causal, softmax_scale=softmax_scale,
                             gqa_interleave=gqa_interleave)


def bnhd_pool(x, kernel_size, pool_type="avg"):
    b, n, h, d = x.shape
    if pool_type == "last":
        if n % kernel_size == 0:
            return x[:, kernel_size - 1::kernel_size, ...]
        return torch.cat((x[:, kernel_size - 1::kernel_size, ...], x[:, -1:, ...]), dim=1)
    m = (n + kernel_size - 1) // kernel_size
    blocks = []
    for i in range(m):
        blk = x[:, i * kernel_size:(i + 1) * kernel_size]
        if pool_type == "avg":
            y = blk.float().mean(1)
        elif pool_type == "sum":
            y = blk.float().sum(1)
        elif pool_type == "max":
            y = blk.float().amax(1)
        elif pool_type == "min":
            y = blk.float().amin(1)
        elif pool_type == "maxabs":
            y = blk.float().abs().amax(1)
        else:
            y = blk.float().mean(1)
        blocks.append(y)
    return torch.stack(blocks, dim=1).to(x.dtype)


def block_wise_attention(q, k, v, block_idx, block_size, grid_offset=0,
                         softmax_scale=None, gqa_interleave=False):
    if not torch.is_tensor(block_idx):
        total_k_blocks = (grid_offset + block_size - 1) // block_size + \
            (k.shape[1] - grid_offset + block_size - 1) // block_size
        limit = total_k_blocks * total_k_blocks
        rows = []
        for sublist in block_idx:
            for item in sublist:
                idx = item.view(-1)
                rows.append(idx[idx < limit])
        block_idx = torch.nn.utils.rnn.pad_sequence(rows, batch_first=True, padding_value=0)
        block_idx = block_idx.view(q.shape[0], q.shape[2], -1)
    return torch_block_wise_attention(q, k, v, block_idx, block_size, grid_offset)
