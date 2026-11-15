"""Driver for nnsmith-F012: the Z3_CONS_FLOPS guard in Pool2d.requires.

`PracticalHybridSearch.search_one` (call_chain[0]) is the input-search entry and never
constructs operator constraints, so it cannot reach `Pool2d.requires`.  The target is the
module-level flag read inside `requires`, so the driver calls that function directly and
records the reason in the form.
"""

import random

import numpy as np

import nnsmith.abstract.op as op
from nnsmith.abstract.dtype import DType
from nnsmith.abstract.tensor import AbsTensor


def run(inputs):
    random.seed(0)
    np.random.seed(0)

    op.Z3_CONS_FLOPS = bool(inputs["Z3_CONS_FLOPS"])

    pool = op.Pool2d(
        inputs["kernel_h_size"],
        inputs["kernel_w_size"],
        inputs["stride"],
        inputs["padding"],
    )
    input_shapes = [AbsTensor(list(inputs["input_shape"]), DType.from_str(inputs["dtype"]))]
    return pool.requires(input_shapes)
