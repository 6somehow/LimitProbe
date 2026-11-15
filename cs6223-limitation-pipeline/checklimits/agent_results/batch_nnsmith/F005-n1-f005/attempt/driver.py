"""Driver for nnsmith-F005 (Region B016, nnsmith/graph_gen.py:524).

Calls the official entry `random_model_gen` with only ExpandLast2 in the op set, so every
backward-insertion attempt is `SimpleGenerator.try_backward_insert(Expand)` and evaluates the
target guard.  The initial placeholder rank is the boundary variable: rank 1 is skipped by the
guard (condition true), rank 2 is kept (condition false).

Imports the repository module at module level, seeds Python/numpy/z3 through the repository's
own entry, uses CPU only, and has no assertions of its own.
"""

from nnsmith.abstract.op import ExpandLast2
from nnsmith.graph_gen import random_model_gen
from nnsmith.util import set_seed

_OP_BY_LAST_DIM = {2: ExpandLast2}


def run(inputs):
    seed = int(inputs["seed"])
    set_seed(seed)

    op_t = _OP_BY_LAST_DIM[int(inputs["expand_last_dim"])]
    return random_model_gen(
        opset=[op_t],
        init_rank=int(inputs["placeholder_ndims"]),
        max_nodes=int(inputs["max_nodes"]),
        seed=seed,
        timeout_ms=int(inputs["timeout_ms"]),
        forward_prob=float(inputs["forward_prob"]),
        limnf=bool(inputs["limnf"]),
    )
