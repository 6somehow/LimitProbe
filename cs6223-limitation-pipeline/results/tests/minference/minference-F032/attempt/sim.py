"""CPU stand-ins for the GPU-only pieces used by the Region.

* arange: the repository module builds LAST_Q_MASK at import time with
  torch.arange(..., device="cuda"); on this CPU box that raises before the target line.
  The stand-in computes exactly torch.arange on CPU and ignores only the device request.
* block_sparse_attention: the Triton/CUDA block-sparse kernel.  This is a plain-torch
  reimplementation of the repository's own block-choice rule
  (_build_block_index in minference/ops/block_sparse_flash_attention.py) followed by a
  masked softmax attention.  It is used only after the target decision (q_len != 1).
"""

import torch

_ORIG_ARANGE = torch._C._VariableFunctions.arange


def arange(*args, **kwargs):
    kwargs.pop("device", None)
    return _ORIG_ARANGE(*args, **kwargs)


def _build_block_index(query, key, top_k, block_size):
    bsz, num_heads, ctx, _ = query.shape
    q_pool = query.reshape(bsz, num_heads, -1, block_size, query.shape[-1]).mean(-2)
    k_pool = key.reshape(bsz, num_heads, -1, block_size, key.shape[-1]).mean(-2)
    m_blocks = q_pool.shape[-2]
    n_blocks = k_pool.shape[-2]
    a_m = _ORIG_ARANGE(m_blocks, dtype=torch.float32, device=query.device) * block_size
    a_n = _ORIG_ARANGE(n_blocks, dtype=torch.float32, device=key.device) * block_size
    scores = torch.einsum("bhmk,bhnk->bhmn", q_pool, k_pool)
    scores = scores.masked_fill(a_m[None, None, :, None] < a_n[None, None, None, :], float("-inf"))
    k_blocks = min(top_k, ctx // block_size)
    if k_blocks <= 0:
        return torch.empty((bsz, num_heads, m_blocks, 0), dtype=torch.long, device=query.device)
    return torch.topk(scores, k_blocks, dim=-1).indices.sort(dim=-1).values


def block_sparse_attention(query, key, value, top_k, block_size_M=64, block_size_N=64):
    bsz, num_heads, ctx, head_dim = query.shape
    bs = block_size_M
    pad = bs - (ctx & (bs - 1))
    q = torch.nn.functional.pad(query, [0, 0, 0, pad, 0, 0, 0, 0])
    k = torch.nn.functional.pad(key, [0, 0, 0, pad, 0, 0, 0, 0])
    v = torch.nn.functional.pad(value, [0, 0, 0, pad, 0, 0, 0, 0])
    index = _build_block_index(q, k, top_k, block_size_N)

    padded = q.shape[2]
    qf, kf, vf = q.float(), k.float(), v.float()
    out = torch.zeros_like(q)
    scale = head_dim ** -0.5
    n_rows = padded // block_size_M
    n_sel = index.shape[-1]

    for row in range(n_rows):
        count = min((row + 1) * block_size_M // block_size_N, n_sel)
        if count <= 0:
            continue
        blocks = index[:, :, row, :count].reshape(bsz, num_heads, -1)
        cols = (blocks[..., None] * block_size_N +
                _ORIG_ARANGE(block_size_N, dtype=torch.long, device=q.device)).reshape(bsz, num_heads, -1)
        gather_idx = cols[..., None].expand(bsz, num_heads, cols.shape[-1], head_dim)
        kg = torch.gather(kf, 2, gather_idx)
        vg = torch.gather(vf, 2, gather_idx)
        q_rows = _ORIG_ARANGE(row * block_size_M, (row + 1) * block_size_M,
                              dtype=torch.long, device=q.device)
        qm = qf[:, :, q_rows, :]
        scores = torch.einsum("bhmd,bhnd->bhmn", qm, kg) * scale
        causal = cols[:, :, None, :] <= q_rows[None, None, :, None]
        scores = scores.masked_fill(~causal, float("-inf"))
        row_max = scores.max(-1, keepdim=True).values
        row_max = torch.where(torch.isfinite(row_max), row_max, torch.zeros_like(row_max))
        weights = torch.exp(scores - row_max)
        denom = weights.sum(-1, keepdim=True)
        weights = weights / torch.clamp(denom, min=1e-30)
        out[:, :, q_rows, :] = torch.einsum("bhmn,bhnd->bhmd", weights, vg).to(out.dtype)

    return out[..., :ctx, :]
