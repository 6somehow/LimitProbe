"""Driver for the guidance back-off branch in GuidedGen.post_process.

The step-4 call chain names random_model_gen as the entry, but in the pinned commit
random_model_gen instantiates PureSymbolGen, whose post_process is a no-op, so
GuidedGen.post_process is never reached from it. To exercise the Region branch we build
a real GuidedGen and call its real post_process with a controlled solver scenario.
The construction is scenario setup only: the target function, its condition, its loop and
its solver calls are the repository code.
"""

import random
from collections import defaultdict

import networkx as nx
import z3

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import AbsTensor, Input, Placeholder
from nnsmith.graph_gen import Bin, GuidedGen


def _make_gen(n_cons):
    gen = GuidedGen(opset={Input}, init_rank=1, seed=0, constrain_prob=1.0)

    if n_cons == 1:
        syms = [z3.Int("p_0")]
        solver = z3.Solver()
        solver.add(syms[0] == 0)
    else:
        syms = [z3.Int("n_%d" % i) for i in range(n_cons)]
        solver = z3.Solver()
        for sym in syms:
            solver.add(sym >= 0)
        solver.add(sum(syms) <= n_cons - 1)

    gen.solver = solver
    ph = Placeholder(AbsTensor(shape=syms, dtype=DType.float32))
    graph = nx.MultiDiGraph()
    graph.add_node(0, op=ph, itensor_idx=[])
    gen.abstract_graph = graph
    gen.tensor_dataflow = []
    gen.default_config = defaultdict(lambda: [Bin(1, None, scale="linear")])
    return gen


def run(inputs):
    random.seed(0)
    gen = _make_gen(int(inputs["n_cons"]))
    gen.post_process()
