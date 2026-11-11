"""Driver for flexprefill-F023.

The Region target is the dtype guard at the top of
`flex_prefill.ops.flex_prefill_attention.triton_block_wise_prefill_attention`
(`assert q.dtype == torch.bfloat16`, line 1218), which is call_chain[1].  The official
entry `flex_prefill_attention` reaches it only after `get_active_blocks`, and that helper
launches the GPU-only `triton_bnhd_pool` kernel *before* the target.  To keep every
stand-in strictly after the target we call the target function itself (call_chain[1]) and
record the reason in execution.entry_reason.

The module under test is imported at module level; tensors are built from `inputs` on CPU
with a fixed seed and a single thread.  No assertions are written here.
"""

import torch

import flex_prefill.ops.flex_prefill_attention as _fpa

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
    k_len = q_len
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    num_activated_blocks = int(inputs["num_activated_blocks"])
    dtype = _DTYPES[str(inputs["dtype"])]
    grid_offset = int(inputs["grid_offset"])
    gqa_interleave = bool(inputs["gqa_interleave"])
    softmax_scale = inputs["softmax_scale"]

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    block_idx = torch.zeros(
        batch_size, num_q_heads, num_activated_blocks, dtype=torch.int64
    )

    return _fpa.triton_block_wise_prefill_attention(
        q,
        k,
        v,
        block_idx,
        block_size,
        grid_offset=grid_offset,
        softmax_scale=softmax_scale,
        gqa_interleave=gqa_interleave,
    )
