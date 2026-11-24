"""CPU stand-ins for the GPU-only pieces of the FlexPrefill import and kernels.

`flash_attn_2_unavailable` is the CPU truth for the transformers availability probe: the
flash-attn package is not installed in this environment and there is no CUDA device. The two
attention stand-ins are plain-torch causal attention and are reached only AFTER the target
branch decision has been recorded.
"""

import math

import torch


def flash_attn_2_unavailable():
    return False


def _causal_attention(q, k, v, causal=True, softmax_scale=None):
    batch_size, q_len, q_heads, head_dim = q.shape
    kv_heads = k.shape[2]
    if kv_heads != q_heads:
        repeat = q_heads // kv_heads
        k = k.repeat_interleave(repeat, dim=2)
        v = v.repeat_interleave(repeat, dim=2)
    scale = (1.0 / math.sqrt(head_dim)) if softmax_scale is None else softmax_scale
    scores = torch.einsum("bihd,bjhd->bhij", q.float(), k.float()) * scale
    if causal:
        k_len = k.shape[1]
        mask = torch.tril(torch.ones(q_len, k_len, dtype=torch.bool))
        scores = scores.masked_fill(~mask, float("-inf"))
    weights = torch.softmax(scores, dim=-1)
    out = torch.einsum("bhij,bjhd->bihd", weights, v.float())
    return out.to(q.dtype)


def flash_attn_func(q, k, v, softmax_scale=None, causal=True):
    return _causal_attention(q, k, v, causal=causal, softmax_scale=softmax_scale)


def triton_vertical_slash_attention(q, k, v, block_size, vertical_topk, slash_topk,
                                    softmax_scale=None, gqa_interleave=False):
    return _causal_attention(q, k, v, causal=True, softmax_scale=softmax_scale)
