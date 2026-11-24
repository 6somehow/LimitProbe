"""Driver for flexposit-F007: a ValueError for an invalid posit rounding mode.

The Region is posit_quantize's guard ``rounding not in ("nearest", "stochastic")``.
The official entry quantize() (api.py) never forwards a ``rounding`` argument: it calls
search_channels, which calls posit_quantize with the default rounding="nearest".  The guard
is therefore unreachable through quantize(), so this driver calls posit_quantize (the last
element of the Region's call chain) directly to exercise the guard.
"""
import os
import sys

for _p in list(sys.path):
    _src = os.path.join(_p, "src")
    if os.path.isdir(os.path.join(_src, "flexposit")):
        if _src not in sys.path:
            sys.path.insert(0, _src)
        break

import torch

from flexposit.formats import posit_quantize


def run(inputs):
    torch.manual_seed(0)
    dtype = getattr(torch, inputs["dtype"])
    x = torch.tensor(inputs["x_values"], dtype=dtype)
    return posit_quantize(x, nsize=int(inputs["nsize"]), es=int(inputs["es"]),
                          scale=float(inputs["scale"]), rounding=inputs["rounding"])
