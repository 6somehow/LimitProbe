"""Driver: build q/k/v from `inputs` and call the target function of the declared call chain.

The repository module is imported at module level. The target function
`vertical_slash_attention` is called directly because in the pinned commit the declared
call-chain entry `flex_prefill_attention` does not call it: the real callers are the
model-specific attention forwards in flex_prefill/modules/*. Tensors are CPU, seeded and
single-threaded. No assertions of our own.
"""

import torch

from flex_prefill.ops.vertical_slash_attention import vertical_slash_attention

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

    return vertical_slash_attention(
        q,
        k,
        v,
        block_size=block_size,
        vertical_size=vertical_size,
        slash_size=slash_size,
    )
