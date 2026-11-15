"""Driver: build q/k/v from `inputs` and call the target function directly.

The hand-off entry point `flex_prefill_attention` never calls `vertical_slash_attention`
(the review note says the vertical-slash baseline is not on FlexPrefill's own path), and it
has its own block_size assertion, so the only way to execute the Region at
flex_prefill/ops/vertical_slash_attention.py:553 is to call that function.  The driver imports
the repository module at module level, sets a fixed seed, uses CPU float32 and a single thread.
No assertions of our own; the harness decides from the trace and the raised exception.
"""

import torch

import flex_prefill.ops.vertical_slash_attention as _vsa

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    seq_len = int(inputs["seq_len"])
    num_heads = int(inputs["num_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    vertical_size = int(inputs["vertical_size"])
    slash_size = int(inputs["slash_size"])
    dtype = _DTYPES[inputs["dtype"]]

    q = torch.randn(batch_size, seq_len, num_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, seq_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, seq_len, num_kv_heads, head_dim, dtype=dtype)

    return _vsa.vertical_slash_attention(
        q,
        k,
        v,
        block_size=block_size,
        vertical_size=vertical_size,
        slash_size=slash_size,
    )
