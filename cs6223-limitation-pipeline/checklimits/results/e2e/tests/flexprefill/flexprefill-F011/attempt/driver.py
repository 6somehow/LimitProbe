"""Driver for flexprefill-F011.

The Region's condition names `kernel_size`, the second parameter of
`triton_bnhd_pool`. In the real caller chain the only call
(`flex_prefill_attention -> get_active_blocks -> triton_bnhd_pool`) passes
`block_size` as that argument, and `flex_prefill_attention` independently
asserts `block_size in {16, 32, 64, 128}` before the target. A value outside
`{16, 32, 64, 128, 256, 512}` therefore cannot reach the target through the
official entry: the earlier `block_size` assert fires first. The target is
exercised directly at its own boundary with a real tensor.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import triton_bnhd_pool

SEED = 0


def run(inputs):
    torch.manual_seed(inputs.get("seed", SEED))
    dtype = getattr(torch, inputs.get("dtype", "float32"))
    x = torch.randn(
        inputs["batch_size"],
        inputs["q_len"],
        inputs["num_kv_heads"],
        inputs["d"],
        dtype=dtype,
    )
    return triton_bnhd_pool(x, inputs["kernel_size"])
