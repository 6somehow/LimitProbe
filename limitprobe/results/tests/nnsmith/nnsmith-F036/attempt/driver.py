"""Driver: call the guided generator chain up to GuidedGen.post_process.

The official entry `random_model_gen` instantiates `PureSymbolGen`, whose `post_process`
is the inherited no-op `SimpleGenerator.post_process`; the target `GuidedGen.post_process`
is only reached when a `GuidedGen` is generated.  So the driver calls the real chain
method `SimpleGenerator.abstract_gen` on a real `GuidedGen` instance (call_chain index 1),
with the reason recorded in form.execution.entry_reason.  Nothing under third_party is
modified or replaced.

`megabyte_lim` is the only varying input: it sets SimpleGenerator.limit_float, which is
the capacity against which the collected guidance constraints are checked.
"""

import random

from nnsmith.abstract.op import ReLU
from nnsmith.graph_gen import GuidedGen

_OPSETS = {"relu": {ReLU}}


def run(inputs):
    seed = int(inputs["seed"])
    random.seed(seed)
    gen = GuidedGen(
        opset=_OPSETS[str(inputs["opset"])],
        init_rank=int(inputs["init_rank"]),
        seed=seed,
        megabyte_lim=int(inputs["megabyte_lim"]),
        default_bins=int(inputs["default_bins"]),
        constrain_prob=float(inputs["constrain_prob"]),
    )
    gen.abstract_gen(
        max_node_size=int(inputs["max_nodes"]),
        max_gen_millisec=int(inputs["timeout_ms"]),
    )
    return None
