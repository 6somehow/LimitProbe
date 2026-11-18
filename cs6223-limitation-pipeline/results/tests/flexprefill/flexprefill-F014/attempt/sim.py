"""Independent CPU stand-in for the GPU attention launcher used after the target line.

`flash_attn_func` is a thin dispatcher onto Triton kernels that need a GPU. This implementation
computes the same scaled-dot-product attention with plain torch on CPU, including the causal
mask and grouped-query attention expansion. It is only reached after the head_dim assertion.
"""

import math

import torch


def flash_attn_sim(q, k, v, causal=True, softmax_scale=None, gqa_interleave=False, **kwargs):
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
