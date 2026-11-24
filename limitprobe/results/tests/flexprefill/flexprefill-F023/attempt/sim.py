"""CPU stand-ins for GPU-only helpers reached AFTER the target assertion.

The target line is `assert q.dtype == torch.bfloat16` at flex_prefill_attention.py:1218.
On the negative (bfloat16) run the guard passes and execution continues into the Triton
launch path, which cannot run on this CPU-only host.  These functions replace only that
post-target path; nothing here is touched before the guard is decided.
"""

import flex_prefill.ops.flex_prefill_attention as _fpa


def column_count_cumsum(x, num_columns):
    """Repository reference implementation of the Triton column-count cumsum."""
    return _fpa.torch_column_count_cumsum(x, num_columns)


def num_warps_stages(head_dim, block_size, gpu_name):
    """GPU_NAME is None on CPU; the real helper calls .lower() on it. Value is unused
    because the Triton kernel launcher itself is replaced below the target."""
    return 4, 2
