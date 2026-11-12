"""Driver for nnsmith-F004 (target: nnsmith/graph_gen.py:260).

Calls the official entry `random_model_gen`, which builds a PureSymbolGen and runs
`SimpleGenerator.abstract_gen`.  After generation the generator adds the memory-limit
constraint and asserts that the solver is still satisfiable.  `megabyte_lim` sets that
limit (`limit_float = 1024**2 * megabyte_lim // 8`); with a zero limit every graph has
more than zero floats, so the final solver call is unsat and the assertion aborts.
One megabyte keeps the same program path but leaves the constraint satisfiable.
"""

from nnsmith.graph_gen import random_model_gen
from nnsmith.abstract.op import (
    Abs,
    Atan,
    Ceil,
    Cos,
    Floor,
    GELU,
    LeakyReLU,
    Log2,
    Neg,
    ReLU,
    Round,
    Sigmoid,
    Sin,
    Sqrt,
    Tan,
)

OPSETS = {
    "unary_cpu_v1": [
        ReLU,
        Abs,
        Neg,
        Sin,
        Cos,
        Sigmoid,
        Sqrt,
        Log2,
        Ceil,
        Floor,
        Round,
        GELU,
        LeakyReLU,
        Tan,
        Atan,
    ]
}


def run(inputs):
    opset = OPSETS[inputs["opset"]]
    gen = random_model_gen(
        opset=list(opset),
        init_rank=int(inputs["init_rank"]),
        max_nodes=int(inputs["max_nodes"]),
        seed=int(inputs["seed"]),
        timeout_ms=int(inputs["timeout_ms"]),
        megabyte_lim=int(inputs["megabyte_lim"]),
        limnf=bool(inputs["limnf"]),
    )
    return len(gen.abstract_graph.nodes)
