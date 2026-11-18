"""Driver: call the official entry point random_model_gen with caller-configured values.

The target branch in SimpleGenerator.try_insert_node_type depends on self.forward_prob and on
the random uniform draw at the target line. The seed is fixed, so the draw at the first target
hit is deterministic; the integer input forward_prob_units selects a value just below/above it
with units_per_one == 2**53 (the denominator of random.random()).
"""

from nnsmith.abstract.op import Abs, Neg, ReLU, Sigmoid, Sin
from nnsmith.graph_gen import random_model_gen

_OPS = {
    "ReLU": ReLU,
    "Abs": Abs,
    "Neg": Neg,
    "Sigmoid": Sigmoid,
    "Sin": Sin,
}


def run(inputs):
    forward_prob = inputs["forward_prob_units"] / inputs["units_per_one"]
    return random_model_gen(
        opset=[_OPS[inputs["op_name"]]],
        init_rank=inputs["init_rank"],
        max_nodes=inputs["max_nodes"],
        seed=inputs["seed"],
        timeout_ms=inputs["timeout_ms"],
        forward_prob=forward_prob,
        init_fp=inputs["init_fp"],
    )
