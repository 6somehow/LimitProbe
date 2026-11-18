"""Driver for flexprefill-F013: call flex_prefill_attention with tensors built from inputs.

The target is `assert q.shape[1] == k.shape[1]` at flex_prefill_attention.py:1836.
Positive input: q_len != k_len (assert fires). Negative: q_len == k_len (assert passes).
All tensors are CPU float32; gamma is a required positional argument but is not used before the target.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])

    num_q_heads = 2
    num_kv_heads = 2
    head_dim = 64

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=torch.float32)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=torch.float32)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=torch.float32)

    return flex_prefill_attention(q, k, v, gamma=0.5)
