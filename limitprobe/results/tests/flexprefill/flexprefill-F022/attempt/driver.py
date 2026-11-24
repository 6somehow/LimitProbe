"""Driver: build q/k/v from `inputs` and call the official entry `flex_prefill_attention`.

The repository module is imported at module level. `gqa_interleave=True` with `q_len == 1`
makes the entry dispatch through the real `triton_flash_attention`, whose bfloat16 dtype
assertion is the target line. Only the tensor dtype differs between the positive and the
negative input.
"""

import torch

import flex_prefill.ops.flex_prefill_attention as _fpa

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}

SEED = 0
NUM_Q_HEADS = 1
NUM_KV_HEADS = 1
GAMMA = 0.9


def run(inputs):
    torch.manual_seed(SEED)
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])
    dtype = _DTYPES[str(inputs["dtype"])]

    q = torch.randn(batch_size, q_len, NUM_Q_HEADS, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, NUM_KV_HEADS, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, NUM_KV_HEADS, head_dim, dtype=dtype)

    return _fpa.flex_prefill_attention(q, k, v, GAMMA, gqa_interleave=True)
