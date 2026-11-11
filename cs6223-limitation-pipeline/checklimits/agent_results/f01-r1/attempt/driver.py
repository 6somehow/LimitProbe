"""Driver for F01: prefill with an existing KV cache (q_len != k_len) is rejected by an assert.

Calls the official entry `flex_prefill_attention` with tensors whose shapes come from the
harness inputs. CPU only, fixed seed, single thread. No assertions of our own and the
AssertionError under test is not caught here.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention


def run(inputs):
    seed = inputs["seed"]
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    dtype = getattr(torch, inputs["dtype"])

    batch_size = inputs["batch_size"]
    q_len = inputs["q_len"]
    k_len = inputs["k_len"]
    head_dim = inputs["head_dim"]
    block_size = inputs["block_size"]
    num_q_heads = inputs["num_q_heads"]
    num_kv_heads = inputs["num_kv_heads"]

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)

    return flex_prefill_attention(
        q,
        k,
        v,
        inputs["gamma"],
        softmax_scale=inputs["softmax_scale"],
        block_size=block_size,
    )
