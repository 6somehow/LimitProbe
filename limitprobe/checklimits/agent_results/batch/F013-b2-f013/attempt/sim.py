"""CPU stand-in for the GPU flash-attention launcher, used only AFTER the target line.

The negative input passes the target assert and then reaches flash_attn_func (triton on this
no-GPU machine). This is a plain-torch scaled dot-product attention with optional causal masking
and GQA head expansion. It is never touched before the target decision.
"""

import math

import torch


def flash_attn_cpu(q, k, v, softmax_scale=None, causal=False, gqa_interleave=False):
    b, lq, hq, d = q.shape
    _, lk, hk, _ = k.shape
    scale = softmax_scale if softmax_scale is not None else 1.0 / math.sqrt(d)

    if hk != hq:
        rep = hq // hk
        k = k.repeat_interleave(rep, dim=2)
        v = v.repeat_interleave(rep, dim=2)

    qf = q.permute(0, 2, 1, 3).float()
    kf = k.permute(0, 2, 1, 3).float()
    vf = v.permute(0, 2, 1, 3).float()

    scores = torch.matmul(qf, kf.transpose(-1, -2)) * scale
    if causal:
        mask = torch.triu(torch.ones(lq, lk, dtype=torch.bool), diagonal=1)
        scores = scores.masked_fill(mask, float("-inf"))
    probs = torch.softmax(scores, dim=-1)
    out = torch.matmul(probs, vf)
    return out.permute(0, 2, 1, 3).to(q.dtype)
