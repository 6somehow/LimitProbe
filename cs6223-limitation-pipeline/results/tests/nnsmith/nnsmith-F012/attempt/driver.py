"""Driver: call the official entry with the inputs the harness passes in.

The finding is about the module-level flag nnsmith.abstract.op.Z3_CONS_FLOPS.  The flag is
read inside Pool2d.requires; the official entry that reaches it is random_model_gen.  The
driver maps the input value onto that module global, builds a one-op graph of Pool2d (the
operator whose requires() holds the target) and calls the entry.
"""

import random

import nnsmith.abstract.op as op_mod
from nnsmith.graph_gen import random_model_gen


def run(inputs):
    op_mod.Z3_CONS_FLOPS = bool(inputs["Z3_CONS_FLOPS"])

    opset = [getattr(op_mod, name) for name in inputs["opset"]]
    seed = int(inputs["seed"])
    random.seed(seed)

    return random_model_gen(
        opset=opset,
        init_rank=int(inputs["init_rank"]),
        max_nodes=int(inputs["max_nodes"]),
        seed=seed,
        timeout_ms=int(inputs["timeout_ms"]),
        forward_prob=float(inputs["forward_prob"]),
        init_fp=bool(inputs["init_fp"]),
    )
