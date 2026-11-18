"""Driver for nnsmith-F004: call the official entry `random_model_gen`.

The generator is pure symbolic (z3 + networkx); no GPU tensor code runs on this path, so no
stand-ins are needed.  `megabyte_lim` is the single control factor: it sets the memory-limit
constant that is added to the solver just before the checked assertion.
"""

import os

os.environ["NNSMITH_LIMNF_V"] = "0"

from nnsmith.abstract.op import Abs, Add, Mul, ReLU
from nnsmith.graph_gen import random_model_gen

OPSET = [ReLU, Add, Mul, Abs]


def run(inputs):
    gen = random_model_gen(
        opset=OPSET,
        init_rank=int(inputs["init_rank"]),
        max_nodes=int(inputs["max_nodes"]),
        seed=int(inputs["seed"]),
        timeout_ms=int(inputs["timeout_ms"]),
        megabyte_lim=int(inputs["megabyte_lim"]),
        limnf=True,
    )
    return len(gen.abstract_graph.nodes)
