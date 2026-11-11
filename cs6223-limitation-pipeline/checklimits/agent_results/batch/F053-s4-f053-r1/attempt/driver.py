"""Driver: build q/k/v from `inputs` and call the official entry `flex_prefill_attention`.

The repository module is imported at module level. Tensors are created on CPU with a fixed
seed and a single thread. No assertions of our own; the harness decides from the trace of the
target branch, not from any check written here.
"""

import torch

import flex_prefill.ops.flex_prefill_attention as _fpa

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def run(inputs):
    seed = int(inputs.get("seed", 0))
    torch.manual_seed(seed)
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])

    num_q_heads = int(inputs.get("num_q_heads", 1))
    num_kv_heads = int(inputs.get("num_kv_heads", 1))
    gamma = float(inputs.get("gamma", 0.9))
    block_size = int(inputs.get("block_size", 128))
    dtype = _DTYPES[inputs.get("dtype", "float32")]

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)

    return _fpa.flex_prefill_attention(q, k, v, gamma, block_size=block_size)
