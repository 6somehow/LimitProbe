"""CPU stand-ins for the two GPU-only calls that run AFTER the target assert.

Both are patched into flex_prefill.ops.flex_prefill_attention by the harness (see form.json
execution.mocks); the repository files are not edited.

bnhd_pool           replaces triton_bnhd_pool (a Triton kernel). Independent plain-torch
                    re-implementation of the 'avg' pool: mean over each block of `kernel_size`
                    tokens, the last block divided by its real length, as the kernel does.
block_wise_attention  replaces triton_block_wise_attention (a Triton kernel). Converts block_idx to a
                    tensor, then calls the repository's own torch reference
                    torch_block_wise_attention, so the numerics are the repository authors' own.
Neither is used to judge the limitation: the verdict comes from the target line.
"""
import math

import torch
import torch.nn.functional as F


def bnhd_pool(x, kernel_size, pool_type="avg"):
    if pool_type != "avg":
        raise NotImplementedError(pool_type)
    b, n, h, d = x.shape
    m = math.ceil(n / kernel_size)
    xp = F.pad(x.float(), (0, 0, 0, 0, 0, m * kernel_size - n))
    s = xp.view(b, m, kernel_size, h, d).sum(2)
    counts = torch.full((m,), float(kernel_size))
    counts[-1] = n - (m - 1) * kernel_size
    return (s / counts.view(1, m, 1, 1)).to(x.dtype)


def block_wise_attention(q, k, v, block_idx, block_size, grid_offset=0, softmax_scale=None, gqa_interleave=False):
    if softmax_scale is not None or gqa_interleave:
        raise NotImplementedError("the repository reference ignores softmax_scale / gqa_interleave")
    import flex_prefill.ops.flex_prefill_attention as m
    if not isinstance(block_idx, torch.Tensor):
        # get_active_blocks returns list[list[Tensor]] with a different length per head. The Triton
        # wrapper pads with an out-of-range index for its kernel; the torch reference needs a tensor of
        # valid indices, so pad each head by repeating its first index (the mask is idempotent).
        flat = [t.view(-1) for per_batch in block_idx for t in per_batch]
        width = max(t.numel() for t in flat)
        flat = [torch.cat([t, t[:1].expand(width - t.numel())]) for t in flat]
        block_idx = torch.stack(flat).view(len(block_idx), len(block_idx[0]), width)
    return m.torch_block_wise_attention(q, k, v, block_idx, block_size, grid_offset)
