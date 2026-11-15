"""Driver: call the kernel entry `triton_vertical_slash_attention` with inputs from the harness.

`flex_prefill_attention` (call_chain[0]) never calls the vertical-slash kernel: its sparse path
calls `triton_block_wise_attention`, and the real caller of `triton_vertical_slash_attention` is
`vertical_slash_attention` in the same file (the hand-off note says the real call graph between
the first two chain entries is not part of the witness).  The target assertion is the kernel's own
dtype guard, so the kernel is the deepest testable entry and is called directly; the reason is
recorded in form.json (execution.entry_reason).

Tensors and index tensors are built from `inputs` only.  Seeds and thread counts are fixed.  No
assertions of our own; the harness decides from the trace and the exception raised at line 264.
"""

import torch

from flex_prefill.ops.vertical_slash_attention import triton_vertical_slash_attention

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
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    dtype = _DTYPES[inputs["dtype"]]

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, q_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, q_len, num_kv_heads, head_dim, dtype=dtype)

    num_blocks = (q_len + block_size - 1) // block_size
    vertical_index = torch.zeros((batch_size, num_q_heads, num_blocks), dtype=torch.int32)
    slash_index = torch.zeros((batch_size, num_q_heads, num_blocks), dtype=torch.int32)

    return triton_vertical_slash_attention(
        q,
        k,
        v,
        block_size,
        vertical_index,
        slash_index,
        softmax_scale=inputs["softmax_scale"],
        gqa_interleave=bool(inputs["gqa_interleave"]),
    )
