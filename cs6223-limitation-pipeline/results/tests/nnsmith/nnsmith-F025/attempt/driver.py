"""Driver: call PracticalHybridSearch.search_one, the official entry of the call chain.

The schedule declares a single float input (so PracticalHybridSearch takes the gradient path
and reaches SymbolNet.grad_input_gen); the tensor actually passed to the entry takes its dtype
from `dtype_code` (positive: >0 -> float32, negative: 0 -> int32).  The target decision at
symbolnet.py:238 then sees a float tensor on the positive run and an integer tensor on the
negative run.
"""

import torch

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import Input
from nnsmith.abstract.tensor import AbsTensor
from nnsmith.materialize import Instruction, Schedule
from nnsmith.materialize.torch.input_gen import PracticalHybridSearch
from nnsmith.materialize.torch.symbolnet import SymbolNet


def _schedule(shape, key):
    inp = Input(dim=len(shape))
    inp.abs_tensor = AbsTensor(shape=list(shape), dtype=DType.float32)
    return Schedule(
        [Instruction(op=inp, inputs=[], outputs=[key])],
        [key],
        [key],
        {key: inp.abs_tensor},
    )


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    shape = tuple(int(x) for x in inputs["shape"])
    key = str(inputs["input_key"])
    dtype = torch.float32 if int(inputs["dtype_code"]) > 0 else torch.int32

    if dtype.is_floating_point:
        tensor = torch.rand(shape, dtype=dtype) * 2.0 - 1.0
    else:
        tensor = torch.randint(-4, 5, shape, dtype=dtype)

    net = SymbolNet(_schedule(shape, key))
    searcher = PracticalHybridSearch(net)
    return searcher.search_one({key: tensor}, timeout_ms=int(inputs["max_time_ms"]))
