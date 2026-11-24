"""Driver for flexposit-F003: posit_encode rejects values outside the Posit table.

Step 4 reports call_chain status ``not_found``: ``quantize`` only fake-quantizes weights
to exact Posit values and never calls the export module, so it cannot reach
``posit_encode``.  The driver still calls the official entry ``quantize`` (with weights
built from the input), then calls the target ``posit_encode`` directly on the same scalar
value, as permitted for a ``not_found`` chain.
"""
from pathlib import Path
import sys

import torch
import torch.nn as nn

for _p in list(sys.path):
    _src = Path(_p) / "src"
    if (_src / "flexposit" / "export.py").is_file():
        sys.path.insert(0, str(_src))
        break

from flexposit.api import FlexPositConfig, quantize
from flexposit.export import posit_encode

NSIZE = 4
ES = 1


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    value = float(inputs["value"])

    model = nn.Sequential(nn.Linear(2, 2, bias=False))
    with torch.no_grad():
        model[0].weight.fill_(value)
    quantize(model, FlexPositConfig(bits=4.0, base_nsize=NSIZE, upgrade_nsize=5, es=ES), progress=False)

    values = torch.tensor([value], dtype=torch.float32)
    return posit_encode(values, NSIZE, ES)
