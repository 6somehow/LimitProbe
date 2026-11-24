"""Driver: exercise the real align_bvs carry-alignment decision on CPU.

The step-4 call chain [PracticalHybridSearch.search_one, align_bvs] is synthetic: search_one
reaches align_bvs only through a full torch network and takes no operand widths. We therefore
call the real target function directly, with zero-width-derived z3 bitvectors, and record why
(execution.entry_reason). No stand-ins are used and the repository is not modified.
"""

import random

import z3

from nnsmith.abstract import arith

random.seed(0)


def run(inputs):
    arith.ARITH_MAX_WIDTH = int(inputs["ARITH_MAX_WIDTH"])
    carry = bool(inputs["carry"])
    left_size = int(inputs["left_size"])
    right_size = int(inputs["right_size"])
    value = int(inputs["operand_value"])
    mult = bool(inputs["mult"])

    left = z3.BitVecVal(value, left_size)
    right = z3.BitVecVal(value, right_size)
    return arith.align_bvs(left, right, carry=carry, mult=mult)
