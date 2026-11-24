"""Driver: call the official entry with the inputs the harness passes in.

The Region's recorded call chain lists flex_prefill_attention first, but that function
never calls vertical_slash_attention and raises its own head_dim assertion earlier, so the
target function is called directly (declared in execution.entry_reason).
"""

import torch

from flex_prefill.ops.vertical_slash_attention import vertical_slash_attention


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)
    dtype = getattr(torch, inputs["dtype"])
    shape_q = (int(inputs["batch_size"]), int(inputs["q_len"]),
               int(inputs["num_q_heads"]), int(inputs["head_dim"]))
    shape_kv = (int(inputs["batch_size"]), int(inputs["k_len"]),
                int(inputs["num_kv_heads"]), int(inputs["head_dim"]))
    q = torch.randn(*shape_q, dtype=dtype)
    k = torch.randn(*shape_kv, dtype=dtype)
    v = torch.randn(*shape_kv, dtype=dtype)
    return vertical_slash_attention(
        q,
        k,
        v,
        block_size=int(inputs["block_size"]),
        vertical_size=int(inputs["vertical_size"]),
        slash_size=int(inputs["slash_size"]),
        gqa_interleave=bool(inputs["gqa_interleave"]),
        softmax_scale=inputs["softmax_scale"],
    )
