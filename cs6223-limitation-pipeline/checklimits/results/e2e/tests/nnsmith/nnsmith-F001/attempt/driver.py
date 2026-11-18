"""Driver for nnsmith-F001: an unrecognized NNSMITH_GRES value makes Reshape.requires raise.

The official entry random_model_gen is called with a single-op opset ([Reshape]) so that the
first inserted node is a Reshape and its checked_requires reaches Reshape.requires at
nnsmith/abstract/op.py:1563.  The environment value is the only controlled factor.
"""
import os
import random

from nnsmith.abstract.op import Reshape
from nnsmith.graph_gen import random_model_gen

SEED = 0
MAX_NODES = 3
TIMEOUT_MS = 2000
INIT_RANK = 4
FORWARD_PROB = 1.0


def run(inputs):
    os.environ["NNSMITH_GRES"] = str(inputs["gres_code"])
    random.seed(SEED)
    return random_model_gen(
        opset=[Reshape],
        init_rank=INIT_RANK,
        max_nodes=MAX_NODES,
        seed=SEED,
        timeout_ms=TIMEOUT_MS,
        forward_prob=FORWARD_PROB,
    )
