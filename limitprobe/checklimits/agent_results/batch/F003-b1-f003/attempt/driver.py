"""Driver for flexprefill-F003: call the official entry `flex_prefill_attention`.

The target is the GQA divisibility guard in triton_flash_prefill:
`assert num_q_heads % num_kv_heads == 0`. The input must keep q_len > 1 and small
enough to take the short-sequence branch, which dispatches to the repository's own
triton_flash_attention (flash_attn is not installed) and reaches the target.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    gamma = float(inputs["gamma"])
    block_size = int(inputs["block_size"])
    dtype = _DTYPES[str(inputs["dtype"])]

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)

    return flex_prefill_attention(q, k, v, gamma, block_size=block_size)
