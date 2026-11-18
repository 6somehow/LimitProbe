"""Driver for sparta-F001: build a weight TeSA with `filled` non-pruned elements and call
the repository's weighted_block_cover with the two block prices from the witness.

A 32x32 weight has one candidate block (or two when n_col is 64). The block price is
price_block / filled, so the caller's sparsity pattern decides whether the (1,1) element
price is cheaper; positive and negative inputs differ only in `filled`.
"""

import torch

from sparta.common import TeSA
from sparta.transformation.weighted_block_cover import weighted_block_cover


def run(inputs):
    n_row = int(inputs["n_row"])
    n_col = int(inputs["n_col"])
    filled = int(inputs["filled"])
    dtype = getattr(torch, inputs["dtype"])

    cover_sizes = {
        (1, 1): float(inputs["price_element"]),
        (32, 32): float(inputs["price_block"]),
    }
    weight = torch.zeros((n_row, n_col), dtype=dtype)
    weight.reshape(-1)[:filled] = 1
    return weighted_block_cover(TeSA(weight), cover_sizes)
