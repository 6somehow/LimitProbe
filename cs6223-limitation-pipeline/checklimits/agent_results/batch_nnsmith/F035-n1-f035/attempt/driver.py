"""Driver: exercise GuidedGen.post_process, the target of finding nnsmith-F035.

The official entry point named in the hand-off, random_model_gen, instantiates PureSymbolGen,
whose post_process is a no-op; GuidedGen is never instantiated anywhere in the repository. To
test the target decision itself we construct a GuidedGen directly and call its post_process.
The graph is the single initial placeholder created by the constructor, so the per-node
constraint list `cons` has one element (one placeholder dimension). The only value that varies
between runs is constrain_prob, which controls the target condition
`len(cons) == 0 or random.uniform(0, 1) > self.constrain_prob`.
"""

from nnsmith.abstract.op import Placeholder
from nnsmith.graph_gen import GuidedGen
from nnsmith.util import set_seed


def run(inputs):
    seed = int(inputs["seed"])
    init_rank = int(inputs["init_rank"])
    constrain_prob = float(inputs["constrain_prob"])

    set_seed(seed)
    gen = GuidedGen(
        opset={Placeholder},
        init_rank=init_rank,
        init_fp=True,
        constrain_prob=constrain_prob,
    )
    return gen.post_process()
