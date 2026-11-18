"""CPU stand-in for the GPU-only flash_attn package.

The repository's flex_prefill/ops/vertical_slash_attention.py unconditionally does
`from flash_attn import flash_attn_func`, so this module exists only to make that import
resolve on a CPU-only machine.  The function is declared as a `sim` mock in form.json and
is replaced by a recording wrapper before the driver runs; it only executes on the negative
path AFTER the target assertion.
"""

import math

import torch


def flash_attn_func(q, k, v, softmax_scale=None, causal=False, **kwargs):
    scale = softmax_scale if softmax_scale is not None else 1.0 / math.sqrt(q.shape[-1])
    scores = torch.einsum("bqhd,bkhd->bhqk", q.float(), k.float()) * scale
    if causal:
        q_len, k_len = scores.shape[-2], scores.shape[-1]
        mask = torch.ones(q_len, k_len, dtype=torch.bool).tril(diagonal=k_len - q_len)
        scores = scores.masked_fill(~mask, float("-inf"))
    probs = torch.softmax(scores, dim=-1)
    out = torch.einsum("bhqk,bkhd->bqhd", probs, v.float())
    return out.to(q.dtype)
