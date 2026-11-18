"""Driver for nnsmith-F038.

The checked decision is `SymbolNet.forward` line 382:
    if self.check_intermediate_numeric or (self.use_gradient and not self.stop_updating_loss)
The witness controls the three SymbolNet attributes.  The official entry
`PracticalHybridSearch.search_one` is called with timeout_ms=0 so that its search loop does
not replace the attributes; the target decision itself is made by the real
`PracticalHybridSearch.__init__` differentiability probe, which calls the real
`SymbolNet.forward` with exactly the constructed attributes.
"""

import random

import numpy as np
import torch

torch.set_num_threads(1)

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import Input, PReLU
from nnsmith.abstract.tensor import AbsTensor
from nnsmith.materialize import Instruction, Schedule
from nnsmith.materialize.torch.input_gen import PracticalHybridSearch
from nnsmith.materialize.torch.symbolnet import SymbolNet


def _build_net(shape, dtype, use_gradient):
    inp = Input(len(shape))
    inp.abs_tensor = AbsTensor(list(shape), dtype)
    op = PReLU()
    instructions = [Instruction(inp, [], [0]), Instruction(op, [0], [1])]
    key2type = {0: AbsTensor(list(shape), dtype), 1: AbsTensor(list(shape), dtype)}
    schedule = Schedule(instructions, [0], [1], key2type)
    return SymbolNet(schedule, use_gradient=use_gradient)


def run(inputs):
    seed = int(inputs.get("seed", 0))
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    shape = [int(v) for v in inputs.get("tensor_shape", [2, 4])]
    dtype = DType.float32 if inputs.get("dtype", "float32") == "float32" else DType.float64
    use_gradient = bool(inputs["use_gradient"])

    net = _build_net(shape, dtype, use_gradient)
    net.check_intermediate_numeric = bool(inputs["check_intermediate_numeric"])
    net.stop_updating_loss = bool(inputs["stop_updating_loss"])
    net.use_gradient = use_gradient

    search = PracticalHybridSearch(net)
    start_inp = net.get_random_inps()
    return search.search_one(start_inp, timeout_ms=int(inputs.get("timeout_ms", 0)))
