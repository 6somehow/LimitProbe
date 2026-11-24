"""Driver: build q/k/v from the inputs and call the official op entry `vertical_slash_attention`.

`vertical_slash_attention` is the first function of the Region call chain that actually reaches
the target (the recorded call_chain[0], `flex_prefill_attention`, never calls this op in the
pinned source). The module under test is imported at module level. Tensors are made on CPU with a
fixed seed and a single thread. No assertions of our own; the harness decides from the trace.
"""

import torch

from flex_prefill.ops.vertical_slash_attention import vertical_slash_attention


def run(inputs):
    seed = int(inputs["seed"])
    torch.manual_seed(seed)
    torch.set_num_threads(1)

    seq_len = int(inputs["seq_len"])
    batch_size = int(inputs["batch_size"])
    num_heads = int(inputs["num_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    vertical_size = int(inputs["vertical_size"])
    slash_size = int(inputs["slash_size"])
    gqa_interleave = bool(inputs["gqa_interleave"])
    dtype = getattr(torch, str(inputs["dtype"]))

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
        gqa_interleave=gqa_interleave,
    )
