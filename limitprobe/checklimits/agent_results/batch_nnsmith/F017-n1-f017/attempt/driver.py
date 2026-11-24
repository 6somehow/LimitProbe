"""Driver for nnsmith-F017: exercise the NNSMITH_LIMNF_V branch in SimpleGenerator.abstract_gen.

The official entry is nnsmith.graph_gen.random_model_gen.  NNSMITH_LIMNF_V is read from the
environment into a module-level constant at import time; the driver sets that module attribute
from the input value before calling the entry, which is exactly the value the target line reads.
"""

import random

import numpy as np

import nnsmith.graph_gen as graph_gen
from nnsmith.abstract.op import Add, Mul, ReLU
from nnsmith.graph_gen import random_model_gen

OPSETS = {"core3": [Add, Mul, ReLU]}


def run(inputs):
    graph_gen.NNSMITH_LIMNF_V = str(inputs["NNSMITH_LIMNF_V"])
    seed = int(inputs["seed"])
    random.seed(seed)
    np.random.seed(seed)
    random_model_gen(
        opset=OPSETS[inputs["opset"]],
        init_rank=int(inputs["init_rank"]),
        seed=seed,
        max_nodes=int(inputs["max_nodes"]),
        timeout_ms=int(inputs["timeout_ms"]),
        limnf=bool(inputs["limnf"]),
    )
    return None
