"""Driver: exercise GuidedGen.extra_constraints on a real op node.

The official entry random_model_gen builds a PureSymbolGen, whose post_process is a no-op and
whose extra_constraints() always returns []; it never instantiates GuidedGen, so it cannot reach
GuidedGen.extra_constraints (see execution.entry_reason in form.json).  We therefore build a real
GuidedGen and call the target function directly with a real AbsOpBase node.

inputs["op_kind"] selects the op class (the only factor that differs between the pair):
  0 -> ReLU        (class name is NOT a key of the active param_config -> config is None)
  1 -> AvgPool2d   (class name IS a key -> config is not None)
  2 -> MaxPool2d   (class name IS a key -> config is not None; neighbour probe of the negative)
inputs["seed"] fixes the RNG used by GuidedGen and the parameter-bin sampler.
"""

import random

from nnsmith.abstract.op import AvgPool2d, MaxPool2d, ReLU
from nnsmith.graph_gen import GuidedGen

_OP_KIND = {
    0: lambda: ReLU(),
    1: lambda: AvgPool2d(1, 1, 1, 0),
    2: lambda: MaxPool2d(1, 1, 1, 0),
}


def run(inputs):
    seed = int(inputs["seed"])
    random.seed(seed)
    gen = GuidedGen(opset={ReLU}, seed=seed)
    node = _OP_KIND[int(inputs["op_kind"])]()
    return gen.extra_constraints(node, [])
