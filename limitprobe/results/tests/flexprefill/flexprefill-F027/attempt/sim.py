"""CPU stand-in for the GPU-only flash-attention launcher.

`flash_attn` is not installed on this CPU-only machine, but
`flex_prefill/ops/vertical_slash_attention.py` imports `flash_attn_func` unconditionally at module
load.  The declared fake module satisfies that import and this plain-torch scaled-dot-product
attention is what `flash_attn_func` would run if a path below the target ever called it.  It is
never touched before the target assertion at line 264.
"""

import math

import torch


def flash_attn_available():
    return torch.cuda.is_available()


def flash_attn_sim(q, k, v, causal=True, softmax_scale=None, **kwargs):
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
