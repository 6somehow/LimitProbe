"""Driver: exercise MatMul.deduct_inp_ranks_and_dtype with the witness boundary.

The hand-off call chain's entry (PracticalHybridSearch.search_one) does not call the
target: shape deduction is invoked by graph_gen.try_occupy_placeholder, not by input
search.  The driver therefore calls the target function directly with a real AbsTensor
whose output rank is the boundary variable, and records that reason in the form.
"""

import random

import torch

from nnsmith.abstract.dtype import DType
from nnsmith.abstract.op import MatMul
from nnsmith.abstract.tensor import AbsTensor


def run(inputs):
    seed = int(inputs["seed"])
    random.seed(seed)
    torch.manual_seed(seed)
    out_rank = int(inputs["out_rank"])
    dim_size = int(inputs["dim_size"])
    dtype = getattr(DType, str(inputs["dtype"]))
    out_abs_tensor = [AbsTensor([dim_size] * out_rank, dtype)]
    return MatMul().deduct_inp_ranks_and_dtype(out_abs_tensor)
