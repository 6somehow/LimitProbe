"""Driver for nnsmith-F010: align_bvs skips zero-extension for multiplication when the
combined operand width already reaches ARITH_MAX_WIDTH.

The target is the branch ``if max_val >= ARITH_MAX_WIDTH:`` inside
``nnsmith/abstract/arith.py::align_bvs``.  The driver first calls the official entry point
``PracticalHybridSearch.search_one`` on a trivial all-integer SymbolNet (so it takes the
CPU SamplingSearch path), then builds the multiplication witness for the target: two z3
bitvectors whose sizes are ``left_size`` / ``right_size`` and whose combined width is
compared with the module-level ``ARITH_MAX_WIDTH`` supplied by the harness.  CPU only,
fixed seed, single thread, no assertions of our own.
"""

import torch
import z3

from nnsmith.abstract import arith
from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import Input
from nnsmith.abstract.tensor import AbsTensor
from nnsmith.materialize import Instruction, Schedule
from nnsmith.materialize.torch.input_gen import PracticalHybridSearch
from nnsmith.materialize.torch.symbolnet import SymbolNet


def _trivial_searcher(tensor_len):
    key = 0
    abs_tensor = AbsTensor([tensor_len], DType.int32)
    inp = Input(1)
    inp.abs_tensor = abs_tensor
    schedule = Schedule([Instruction(inp, [], [key])], [key], [key], {key: abs_tensor})
    net = SymbolNet(schedule)
    return PracticalHybridSearch(net)


def run(inputs):
    seed = int(inputs["seed"])
    torch.manual_seed(seed)
    torch.set_num_threads(1)

    arith_max_width = int(inputs["ARITH_MAX_WIDTH"])
    left_size = int(inputs["left_size"])
    right_size = int(inputs["right_size"])
    tensor_len = int(inputs["entry_tensor_len"])
    mult = bool(inputs["mult"])

    searcher = _trivial_searcher(tensor_len)
    entry_input = torch.arange(tensor_len, dtype=torch.int32)
    searcher.search_one({"i0": entry_input})

    arith.ARITH_MAX_WIDTH = arith_max_width
    left = z3.BitVecVal(int(inputs["left_value"]), left_size)
    right = z3.BitVecVal(int(inputs["right_value"]), right_size)
    if not mult:
        return arith.align_bvs(left, right, mult=False)
    return arith.nnsmith_mul(left, right)
