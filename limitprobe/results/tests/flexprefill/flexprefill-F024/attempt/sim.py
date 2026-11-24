"""CPU stand-in for the GPU-only block-wise sequence pool used before the target line.

triton_bnhd_pool launches bnhd_pool_kernel on the GPU.  The target assert only looks at
`block_size`, but get_active_blocks (which runs before the target) needs the pooled key tensor,
so the kernel launcher is replaced by the same average-over-each-sequence-block computation in
plain torch.  Semantics copied from bnhd_pool_kernel: every output row is the sum of the block
divided by the *actual* length of that block (the last block can be shorter).
"""

import torch


def bnhd_pool(x, kernel_size, pool_type="avg"):
    b, n, h, d = x.shape
    kernel_size = int(kernel_size)
    m = (n + kernel_size - 1) // kernel_size
    y = torch.zeros((b, m, h, d), dtype=x.dtype, device=x.device)
    for i in range(m):
        lo = i * kernel_size
        hi = min(n, lo + kernel_size)
        blk = x[:, lo:hi, :, :].float()
        if pool_type == "max":
            val = blk.amax(dim=1)
        elif pool_type == "min":
            val = blk.amin(dim=1)
        elif pool_type == "maxabs":
            val = blk.abs().amax(dim=1)
        elif pool_type == "sum":
            val = blk.sum(dim=1)
        else:
            val = blk.mean(dim=1)
        y[:, i, :, :] = val.to(x.dtype)
    return y
