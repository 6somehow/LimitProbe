"""Driver for nnsmith-F018: exercise the NNSMITH_LIMNF_V branch in abstract_gen.

The repository reads NNSMITH_LIMNF_V from the environment once, at import time, into the
module global `nnsmith.graph_gen.NNSMITH_LIMNF_V`. The official entry `random_model_gen`
then consults that module global throughout generation and at the target branch. Here we
set that same module global from the input (the environment value the witness describes)
before calling the official entry, so the positive and negative runs differ only in it.
"""

import nnsmith.graph_gen as graph_gen
from nnsmith.abstract.op import Abs

_OPSETS = {"Abs": [Abs]}


def run(inputs):
    graph_gen.NNSMITH_LIMNF_V = str(inputs["NNSMITH_LIMNF_V"])
    graph_gen.random_model_gen(
        opset=_OPSETS[inputs["opset"]],
        init_rank=int(inputs["init_rank"]),
        max_nodes=int(inputs["max_nodes"]),
        seed=int(inputs["seed"]),
        timeout_ms=int(inputs["timeout_ms"]),
        limnf=True,
    )
