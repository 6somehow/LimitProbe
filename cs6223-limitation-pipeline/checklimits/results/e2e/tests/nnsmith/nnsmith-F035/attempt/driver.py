"""Drive GuidedGen.post_process (the target's function) after calling the official entry.

The pinned repository's official entry `random_model_gen` builds a PureSymbolGen, whose
post_process is the no-op SimpleGenerator.post_process, so it never reaches the target.
GuidedGen is not instantiated anywhere in the pinned repository; the compared decision can
only be exercised on a real GuidedGen.  We therefore call the real entry first, then construct
GuidedGen and run the documented SimpleGenerator.abstract_gen -> GuidedGen.post_process path
with max_node_size=0.  The graph is then the single initial Placeholder that
GuidedGen.__init__ inserts (rank `init_rank`), so post_process visits exactly one node and
`len(cons) == init_rank`.
"""

from nnsmith.graph_gen import GuidedGen, random_model_gen
from nnsmith.abstract.op import MatMul

_OPSETS = {"MatMul": MatMul}


def run(inputs):
    cp = float(inputs["constrain_prob"])
    seed = int(inputs["seed"])
    init_rank = int(inputs["init_rank"])
    scale = str(inputs["scale"])
    opset = {_OPSETS[str(inputs["opset_name"])]}
    random_model_gen(
        opset=opset,
        init_rank=init_rank,
        max_nodes=0,
        seed=seed,
        timeout_ms=500,
    )
    gen = GuidedGen(
        opset=opset,
        init_rank=init_rank,
        seed=seed,
        constrain_prob=cp,
        scale=scale,
    )
    gen.abstract_gen(max_node_size=0, max_gen_millisec=500)
    return None
