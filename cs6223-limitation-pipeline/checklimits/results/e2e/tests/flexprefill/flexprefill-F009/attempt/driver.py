"""Driver for flexprefill-F009: call the target function of the Region directly.

The official entry `flex_prefill_attention` cannot reach line 1258 for a non-divisible head
pair: before that line it calls `get_active_blocks`, whose einsum reshapes heads with
`num_q_heads // num_kv_heads` and raises `RuntimeError: einsum(): subscript h has size ...`
on the CPU for every non-divisible (num_q_heads, num_kv_heads).  The Region's target function
`triton_block_wise_prefill_attention` is the second element of the call chain, so the driver
calls it with a real torch `block_idx` tensor; all guards before line 1258 are plain Python /
torch and run for real.  The reason is recorded in form.json execution.entry_reason.

No assertions of our own and no stand-ins: the positive run raises in the target statement
itself; the negative run passes it and only then touches GPU-only triton launchers.
"""

import torch

import flex_prefill.ops.flex_prefill_attention as _fpa

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def run(inputs):
    torch.manual_seed(int(inputs.get("seed", 0)))
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    num_block = int(inputs["num_block"])
    dtype = _DTYPES[inputs.get("dtype", "bfloat16")]

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    block_idx = torch.zeros(batch_size, num_q_heads, num_block, dtype=torch.int64)

    return _fpa.triton_block_wise_prefill_attention(
        q,
        k,
        v,
        block_idx,
        block_size,
    )
