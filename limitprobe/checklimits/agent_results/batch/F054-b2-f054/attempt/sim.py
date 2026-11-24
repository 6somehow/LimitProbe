"""CPU stand-ins for GPU-only attention launchers (touched only after the target assert)."""

import math

import torch


def attention(q, k, v, causal=False, softmax_scale=None, gqa_interleave=False):
    b, q_len, n_q_heads, d = q.shape
    _, k_len, n_kv_heads, _ = k.shape
    if n_kv_heads != n_q_heads:
        rep = n_q_heads // n_kv_heads
        k = k.repeat_interleave(rep, dim=2)
        v = v.repeat_interleave(rep, dim=2)

    qf = q.to(torch.float32)
    kf = k.to(torch.float32)
    vf = v.to(torch.float32)
    scale = softmax_scale if softmax_scale is not None else 1.0 / math.sqrt(d)

    scores = torch.einsum("bqhd,bkhd->bhqk", qf, kf) * scale
    if causal:
        future = torch.ones(q_len, k_len, dtype=torch.bool).triu(diagonal=1)
        scores = scores.masked_fill(future, float("-inf"))
    probs = torch.softmax(scores, dim=-1)
    out = torch.einsum("bhqk,bkhd->bqhd", probs, vf)
    return out.to(q.dtype)
