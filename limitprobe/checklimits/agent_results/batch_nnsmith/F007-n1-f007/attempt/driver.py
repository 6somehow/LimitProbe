"""Driver for nnsmith-F007 / Region B034.

Target: the `if loss_fn.dispatch(type(op)) is not None:` test inside
SymbolNet.forward (nnsmith/materialize/torch/symbolnet.py:385).  The official
entry is PracticalHybridSearch.search_one, which for a differentiable net runs
GradSearch, enabling training and check_intermediate_numeric before calling
SymbolNet.forward.

The two searchers are built once at import time (fresh process, fixed seed) so
that the traced call really starts at search_one; the differentiability probe in
PracticalHybridSearch.__init__ would otherwise start SymbolNet.forward first.

Two presets are selected by the single design factor `case_id`:
  case_id == 1: one registered-loss op (Div) with finite inputs.
  case_id <= 0: one unregistered-loss op (Mul) whose finite float32 inputs
                overflow to +inf, i.e. the "NaN/Inf without torch_loss" case.

CPU only, single thread, fixed seed, no asserts, no stand-ins.
"""

import torch

torch.set_num_threads(1)

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import Div, Mul
from nnsmith.abstract.tensor import AbsTensor
from nnsmith.materialize import Instruction, Schedule
from nnsmith.materialize.torch.input_gen import PracticalHybridSearch
from nnsmith.materialize.torch.symbolnet import SymbolNet

_SIZE = 2
_DTYPE = DType.float32
_SEED = 0
_TIMEOUT_MS = 100
_OVERFLOW = 3e38


def _schedule(case_id):
    shape = AbsTensor([_SIZE], _DTYPE)
    key2type = {0: shape, 1: shape, 2: shape}
    op = Div() if int(case_id) == 1 else Mul()
    return Schedule([Instruction(op=op, inputs=[0, 1], outputs=[2])], [0, 1], [2], key2type)


def _inputs(case_id):
    if int(case_id) == 1:
        return {"i0": torch.ones(_SIZE, dtype=torch.float32),
                "i1": torch.ones(_SIZE, dtype=torch.float32)}
    return {"i0": torch.full((_SIZE,), _OVERFLOW, dtype=torch.float32),
            "i1": torch.full((_SIZE,), _OVERFLOW, dtype=torch.float32)}


def _searcher(case_id):
    torch.manual_seed(_SEED)
    return PracticalHybridSearch(SymbolNet(_schedule(case_id)))


_SEARCHERS = {1: _searcher(1), 0: _searcher(0)}


def run(inputs):
    case_id = 1 if int(inputs["case_id"]) == 1 else 0
    torch.manual_seed(int(inputs.get("seed", _SEED)))
    return _SEARCHERS[case_id].search_one(
        _inputs(case_id), timeout_ms=int(inputs.get("timeout_ms", _TIMEOUT_MS))
    )
