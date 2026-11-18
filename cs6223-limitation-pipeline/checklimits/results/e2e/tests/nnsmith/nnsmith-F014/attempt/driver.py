"""Driver for finding nnsmith-F014 (Reshape.requires, nnsmith/abstract/op.py:1587).

The step-4 call chain entry (PracticalHybridSearch.search_one) never calls Reshape.requires in the
pinned repository, so the target is exercised through the real public wrapper
Reshape.checked_requires, which calls Reshape.requires.  `cons_reshape` is the derived value of
NNSMITH_CONS_RESHAPE: 0 maps to the contrast value "off", any other integer is used verbatim.
"""

import os
import random

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import Reshape
from nnsmith.abstract.tensor import AbsTensor


def run(inputs):
    random.seed(int(inputs["seed"]))
    os.environ["NNSMITH_CONS_RESHAPE"] = (
        "off" if int(inputs["cons_reshape"]) == 0 else str(int(inputs["cons_reshape"]))
    )
    op = Reshape(*[int(v) for v in inputs["target_shape"]])
    inp = AbsTensor([int(v) for v in inputs["input_shape"]], DType.float32)
    return op.checked_requires([inp])
