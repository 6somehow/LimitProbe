"""CPU stand-ins for GPU-only imports of the target module.

Only ``arange_cpu`` is used before the target (the module-level ``torch.arange(..., device="cuda")``).
The other exports keep the GPU-only modules importable; none of them is called before the target.
"""

import torch


def arange_cpu(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and str(device).startswith("cuda"):
        kwargs["device"] = "cpu"
    return torch.arange(*args, **kwargs)


def flash_attn_varlen_func(q, k, v, cu_seqlens_q, cu_seqlens_k, max_seqlen_q, max_seqlen_k,
                           dropout_p=0.0, softmax_scale=None, causal=False, **kwargs):
    scale = softmax_scale if softmax_scale is not None else q.shape[-1] ** -0.5
    out = torch.empty_like(q)
    q_offsets = cu_seqlens_q.tolist()
    k_offsets = cu_seqlens_k.tolist()
    for i in range(len(q_offsets) - 1):
        qs, qe = q_offsets[i], q_offsets[i + 1]
        ks, ke = k_offsets[i], k_offsets[i + 1]
        if qe <= qs:
            continue
        scores = torch.einsum("qhd,khd->hqk", q[qs:qe].float(), k[ks:ke].float()) * scale
        if causal:
            qn, kn = scores.shape[-2], scores.shape[-1]
            mask = torch.ones(qn, kn, dtype=torch.bool).tril(diagonal=kn - qn)
            scores = scores.masked_fill(~mask, float("-inf"))
        probs = torch.softmax(scores, dim=-1)
        out[qs:qe] = torch.einsum("hqk,khd->qhd", probs, v[ks:ke].float()).to(q.dtype)
    return out


def source_module(*args, **kwargs):
    raise NotImplementedError("pycuda SourceModule is not available on CPU")


def convert_vertical_slash_indexes(seqlens, v_idx, s_idx, context_size, block_size_M, block_size_N):
    batch = int(seqlens.shape[0])
    heads = int(v_idx.shape[1])
    blocks = (context_size + block_size_M - 1) // block_size_M + 1
    columns = (context_size + block_size_N - 1) // block_size_N + 1
    zeros = lambda *shape: torch.zeros(shape, dtype=torch.int32)
    return zeros(batch, heads, blocks), zeros(batch, heads, blocks, 2), zeros(batch, heads), zeros(batch, heads, columns)
