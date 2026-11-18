"""Driver for flexposit-F027: call flexposit.api.quantize (the official entry and the target).

`inputs` carries the two config fields the Region condition reads (`bits`, `base_nsize`),
plus the witness flag `quantize`.  The config is built as a valid FlexPositConfig and then
its two fields are set from the inputs, so the harness's ON/OFF probes of `bits` also reach
the target guard instead of being rejected by FlexPositConfig.__post_init__ first.
"""

import sys
from pathlib import Path

import torch
import torch.nn as nn

for _entry in list(sys.path):
    for _cand in (Path(_entry), Path(_entry) / "src"):
        if (_cand / "flexposit" / "__init__.py").is_file():
            if str(_cand) not in sys.path:
                sys.path.insert(0, str(_cand))
            break
    else:
        continue
    break

from flexposit.api import FlexPositConfig, quantize

_MODEL_WIDTH = 4
_SENSITIVITY = [("proj", 0, _MODEL_WIDTH, -1.0)]


class _Tiny(nn.Module):
    def __init__(self, width: int = _MODEL_WIDTH) -> None:
        super().__init__()
        self.proj = nn.Linear(width, width, bias=False)
        with torch.no_grad():
            self.proj.weight.copy_(
                torch.linspace(-1.0, 1.0, width * width).reshape(width, width))


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.backends.cudnn.deterministic = True

    if not bool(inputs["quantize"]):
        return None

    base = int(inputs["base_nsize"])
    bits = int(inputs["bits"])
    config = FlexPositConfig(bits=float(max(base, bits)), base_nsize=base, upgrade_nsize=5, es=0)
    config.bits = bits
    config.base_nsize = base

    model = _Tiny()
    return quantize(model, config, sensitivity=list(_SENSITIVITY), progress=False)
