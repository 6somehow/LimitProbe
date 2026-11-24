"""CPU stand-ins for GPU-only triton kernel launchers used after the target line."""

import math

import torch
import torch.nn.functional as F


def bnhd_pool(x, kernel_size, pool_type="avg"):
    b, n, h, d = x.shape
    m = math.ceil(n / kernel_size)
    if pool_type == "last":
        if n % kernel_size == 0:
            return x[:, kernel_size - 1 :: kernel_size, ...]
        return torch.cat((x[:, kernel_size - 1 :: kernel_size, ...], x[:, -1:, ...]), dim=1)
    pad = m * kernel_size - n
    xp = F.pad(x, (0, 0, 0, 0, 0, pad)) if pad else x
    xp = xp.reshape(b, m, kernel_size, h, d)
    if pool_type == "avg":
        counts = torch.full((m,), float(kernel_size), dtype=x.dtype, device=x.device)
        counts[-1] = float(n - (m - 1) * kernel_size)
        return xp.sum(dim=2) / counts.view(1, m, 1, 1)
    if pool_type == "max":
        return xp.amax(dim=2)
    if pool_type == "min":
        return xp.amin(dim=2)
    if pool_type == "maxabs":
        return xp.abs().amax(dim=2)
    return xp.sum(dim=2)


def block_wise_attention(q, k, v, block_idx, block_size, grid_offset=0, softmax_scale=None,
                         gqa_interleave=False):
    from flex_prefill.ops.flex_prefill_attention import torch_block_wise_attention

    if isinstance(block_idx, torch.Tensor):
        bi = block_idx
    else:
        per = [item.reshape(-1, 1) for sub in block_idx for item in sub]
        bi = torch.nn.utils.rnn.pad_sequence(per, batch_first=True, padding_value=0)
        bi = bi.view(len(block_idx), len(block_idx[0]), -1)
    num_block = math.ceil(grid_offset / block_size) + math.ceil(
        (q.shape[1] - grid_offset) / block_size
    )
    bi = torch.where((bi < 0) | (bi >= num_block * num_block), torch.zeros_like(bi), bi)
    return torch_block_wise_attention(q, k, v, bi, block_size, grid_offset)
