"""Independent CPU stand-in for the GPU decode launcher reached after the target line.

`triton_flash_decode` launches Triton kernels that need a GPU. This plain-torch
scaled-dot-product attention keeps the post-target path running on CPU. It is only called
after the bfloat16 dtype assertion at the target line has already passed.
"""

import math

import torch


def flash_decode_sim(q, k, v, softmax_scale=None, gqa_interleave=False, **kwargs):
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
    weights = torch.softmax(scores, dim=-1)
    out = torch.matmul(weights, vf).to(q.dtype)
    return out.transpose(1, 2)
