"""Driver: re-evaluate the module-level FLOPS_LIM branch of `nnsmith/abstract/op.py`.

The Region target is module-level code, so it only runs when the module body executes.
The module is imported once when this driver is loaded (before the harness starts tracing);
`run` then sets NNSMITH_FLOPS_LIM from the input and reloads the real module, which executes
the real module body again inside the traced call.  Nothing from the module is replaced and
no assertion is made here: the harness reads the branch decision and evaluates the Region
condition on the module frame.  CPU only, deterministic, no network.
"""

import importlib
import os

import nnsmith.abstract.op as _op


def run(inputs):
    os.environ["NNSMITH_FLOPS_LIM"] = str(inputs["FLOPS_LIM"])
    module = importlib.reload(_op)
    return module.FLOPS_LIM
