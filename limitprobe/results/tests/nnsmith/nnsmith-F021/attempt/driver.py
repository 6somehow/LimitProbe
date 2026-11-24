"""Driver for nnsmith-F021: TorchModel.make_oracle's fallback branch.

The target is the `if self.sat_inputs is None:` decision at
nnsmith/materialize/torch/__init__.py:47.  The driver builds a real TorchModel from
a minimal Schedule made of the repository's own Input op (no stand-ins), runs the
official entry PracticalHybridSearch.search_one, and then calls the target method.
`sat_found` selects whether the search result is stored in self.sat_inputs, so the
only difference between the positive and negative input is that piece of state.
"""

import torch

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import Input
from nnsmith.abstract.tensor import AbsTensor
from nnsmith.materialize import Instruction, Schedule
from nnsmith.materialize.torch import TorchModel
from nnsmith.materialize.torch.input_gen import PracticalHybridSearch

_INPUT_KEY = 0
_INPUT_SHAPE = [2, 3]


def _make_model():
    inp = Input(dim=len(_INPUT_SHAPE))
    inp.abs_tensor = AbsTensor(shape=list(_INPUT_SHAPE), dtype=DType.int32)
    schedule = Schedule(
        instructions=[Instruction(op=inp, inputs=[], outputs=[_INPUT_KEY])],
        input_keys=[_INPUT_KEY],
        leaf_keys=[_INPUT_KEY],
        key2type={_INPUT_KEY: inp.abs_tensor},
    )
    return TorchModel.from_schedule(schedule)


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)

    model = _make_model()
    searcher = PracticalHybridSearch(model.torch_model)
    start_inp = model.torch_model.get_random_inps()
    found = searcher.search_one(start_inp, timeout_ms=0)

    if int(inputs["sat_found"]) >= 1:
        model.sat_inputs = found

    return model.make_oracle()
