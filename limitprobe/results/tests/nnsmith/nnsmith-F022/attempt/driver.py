"""Driver for nnsmith-F022: construct a minimal SymbolNet and call the official entry.

The net has one symbolic input whose dtype is chosen by the integer input ``use_float``.
Positive (use_float > 0): float input, so the target condition is true and __init__ runs
the differentiability probe. Negative (use_float <= 0): int input, so the condition is
false and the else branch is taken. The Region target lives in PracticalHybridSearch.__init__,
which necessarily runs when the instance is built before search_one can be called.
"""

import torch

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.tensor import AbsTensor
from nnsmith.materialize import Schedule
from nnsmith.materialize.torch.input_gen import PracticalHybridSearch
from nnsmith.materialize.torch.symbolnet import SymbolNet


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    shape = [int(dim) for dim in inputs["shape"]]
    if int(inputs["use_float"]) > 0:
        dtype = DType.from_str(inputs["float_dtype"])
    else:
        dtype = DType.from_str(inputs["int_dtype"])

    schedule = Schedule(
        instructions=[],
        input_keys=[0],
        leaf_keys=[0],
        key2type={0: AbsTensor(shape, dtype)},
    )
    net = SymbolNet(schedule, use_gradient=False)
    net.eval()

    searcher = PracticalHybridSearch(net)
    start_inp = {"i0": torch.zeros(shape, dtype=dtype.torch())}
    return searcher.search_one(start_inp, timeout_ms=int(inputs["timeout_ms"]))
