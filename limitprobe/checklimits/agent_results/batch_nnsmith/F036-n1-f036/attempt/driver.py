"""Driver: exercise GuidedGen.post_process's guidance back-off decision.

The official entry (`random_model_gen`) hardcodes `PureSymbolGen`, so it never
instantiates `GuidedGen`; the target function is reached here directly on a real
`GuidedGen` instance.  The instance's abstract graph and solver are built with the
repository's own methods.  `conflict == 1` leaves the accumulated solver state
unsatisfiable together with the collected guidance, so the target `while` condition
is true; `conflict == 0` leaves it satisfiable, so the condition is false.
"""

import random

from nnsmith.abstract.op import Add
from nnsmith.graph_gen import GuidedGen


def run(inputs):
    seed = int(inputs["seed"])
    conflict = int(inputs["conflict"])

    random.seed(seed)
    gen = GuidedGen(opset=[Add], init_rank=1, seed=seed, constrain_prob=1.0)

    guide_dim = gen.tensor_dataflow[0].type.shape[0]
    if conflict:
        gen.solver.add(guide_dim < 0)

    gen.post_process()
    return None
