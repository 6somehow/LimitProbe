"""Driver: exercise GuidedGen.extra_constraints's `config is None` branch.

The Region names `random_model_gen` as the official entry, but that function always
constructs a PureSymbolGen (GuidedGen is never instantiated anywhere in the repository),
so the Region's branch can only be reached by calling GuidedGen.extra_constraints, the
real target function, directly. That deeper entry is recorded in execution.entry_reason.

`config` is derived, not an input: it is
`self.param_config.get(node.__class__.__name__, None)`. The single boundary variable is
`config_present`: 0 selects an op class absent from PARAM_CONFIG1 (config is None), any
non-zero value selects one present in it (config is not None).
"""

import random

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import AbsTensor, MaxPool2d, ReLU
from nnsmith.graph_gen import GuidedGen

_OP_BUILDERS = {
    "ReLU": lambda: ReLU(),
    "MaxPool2d": lambda: MaxPool2d(2, 2, 1, 0),
}


def run(inputs):
    seed = int(inputs.get("seed", 0))
    random.seed(seed)

    config_present = int(inputs["config_present"])
    op_name = (
        inputs.get("negative_op", "MaxPool2d")
        if config_present != 0
        else inputs.get("positive_op", "ReLU")
    )
    shape = inputs.get("in_shape", [1, 3, 8, 8])

    gen = GuidedGen(opset={ReLU}, init_rank=1, seed=seed, limnf=False)
    node = _OP_BUILDERS[op_name]()
    input_shapes = [AbsTensor(shape=list(shape), dtype=DType.float32)]
    return gen.extra_constraints(node, input_shapes)
