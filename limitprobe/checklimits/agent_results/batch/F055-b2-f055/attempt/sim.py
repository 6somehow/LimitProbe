"""Independent CPU stand-in for the GPU flash-attention launcher reached after the target.

The repository's vertical-slash module imports `flash_attn_func` at import time.  That package is
not installed on this CPU machine, so the declared fake module provides the name and this plain
torch scaled-dot-product attention (causal mask, grouped-query expansion) is the implementation
bound to it.  It is only reached after the block_size assertion at line 553 has been passed.
"""

import math

import torch


def flash_attn_func(q, k, v, causal=True, softmax_scale=None, gqa_interleave=False, **kwargs):
    if softmax_scale is None:
        softmax_scale = 1.0 / math.sqrt(q.shape[-1])

    num_q_heads = q.shape[2]
    num_kv_heads = k.shape[2]
    if num_kv_heads != num_q_heads:
        repeat = num_q_heads // num_kv_heads
        k = k.repeat_interleave(repeat, dim=2)
        v = v.repeat_interleave(repeat, dim=2)

    qf = q.transpose(1, 2).float()
    kf = k.transpose(1, 2).float()
    vf = v.transpose(1, 2).float()
    scores = torch.matmul(qf, kf.transpose(-2, -1)) * softmax_scale

    if causal:
        q_len, k_len = scores.shape[-2], scores.shape[-1]
        mask = torch.ones(q_len, k_len, dtype=torch.bool).tril(diagonal=k_len - q_len)
        scores = scores.masked_fill(~mask, float("-inf"))

    weights = torch.softmax(scores, dim=-1)
    out = torch.matmul(weights, vf).to(q.dtype)
    return out.transpose(1, 2)


def is_flash_attn_2_available():
    """Faithful CPU answer for transformers' probe: no usable flash-attn without CUDA."""
    try:
        import torch

        if not torch.cuda.is_available():
            return False
        if not torch.version.cuda:
            return False
        import importlib.metadata
        from packaging import version

        return version.parse(importlib.metadata.version("flash_attn")) >= version.parse("2.1.0")
    except Exception:
        return False
