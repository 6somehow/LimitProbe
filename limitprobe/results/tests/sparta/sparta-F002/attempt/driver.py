"""Call the official entry, then exercise the real weighted-block-cover target.

The pinned `propagate_sparsity` only extracts sparsity metadata and returns it
(`post_sparsity = pre_sparsity`); it never calls `wbc_matmul`.  Step-4 reports the
call-chain status as `not_found`, so `wbc_matmul` (call_chain[1]) is called directly.

The local `sortedcontainers` package in this attempt directory is a vendored copy of
the pure-Python dependency the repository imports; it is not on the harness
interpreter's path.
"""

import torch

from sparta.common import TeSA
from sparta.propagation.propagate import propagate_sparsity
from sparta.transformation.weighted_block_cover import wbc_matmul


class _WeightHolder(torch.nn.Module):
    def __init__(self, weight_tesa):
        super().__init__()
        self.weight_tesa = weight_tesa


def _weight_tesa(rows, cols, pattern, region_a_rows, region_a_cols, region_b_per_half, dtype):
    t = torch.zeros((rows, cols), dtype=dtype)
    t[0:region_a_rows, 0:region_a_cols] = 1
    if pattern >= 1:
        height = rows - region_a_rows
        cells = torch.arange(height * region_a_cols, dtype=torch.int64).reshape(height, region_a_cols).reshape(-1)
        left = cells[:region_b_per_half]
        right = cells[:region_b_per_half]
        t[region_a_rows + left // region_a_cols, left % region_a_cols] = 1
        t[region_a_rows + right // region_a_cols, region_a_cols + right % region_a_cols] = 1
    return t


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    dtype = {"int32": torch.int32, "float32": torch.float32}[inputs["dtype"]]
    weights = _weight_tesa(
        int(inputs["rows"]),
        int(inputs["cols"]),
        int(inputs["pattern"]),
        int(inputs["region_a_rows"]),
        int(inputs["region_a_cols"]),
        int(inputs["region_b_per_half"]),
        dtype,
    )
    propagate_sparsity(_WeightHolder(weights))
    in_tesa = TeSA(torch.ones((1, 1), dtype=dtype))
    w_tesa = TeSA(weights)
    out_tesa = TeSA(torch.ones((1, 1), dtype=dtype))
    return wbc_matmul(in_tesa, w_tesa, out_tesa)
