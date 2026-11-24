"""Driver: call the official entry with the inputs the harness passes in."""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention

torch.set_num_threads(1)


def run(inputs):
    torch.manual_seed(inputs["seed"])

    batch_size = inputs["batch_size"]
    q_len = inputs["q_len"]
    k_len = inputs["k_len"]
    head_dim = inputs["head_dim"]
    num_heads = inputs["num_heads"]
    dtype = getattr(torch, inputs["dtype"])

    q = torch.randn(batch_size, q_len, num_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, num_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, num_heads, head_dim, dtype=dtype)

    return flex_prefill_attention(
        q,
        k,
        v,
        inputs["gamma"],
        block_size=inputs["block_size"],
    )
