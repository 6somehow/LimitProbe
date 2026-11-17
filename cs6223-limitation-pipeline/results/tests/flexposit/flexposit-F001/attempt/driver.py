"""Driver: call the official entry `flexposit.api.quantize` for finding flexposit-F001.

The claim is about the FileNotFoundError that `sensitivity_csv` raises when the
`sensitivity` argument is neither an existing file nor a shipped model short name.
Positive: a name that is not shipped. Negative: the shipped short name `gpt2-large`
(the model below uses the layer name that occurs in that CSV, so the negative run
gets past the target and finishes normally).
"""

import sys
from pathlib import Path

_REPO = Path(sys.path[0])
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch
import torch.nn as nn

from flexposit.api import FlexPositConfig, quantize


class _Container(nn.Module):
    pass


def _make_model(in_features, out_features, seed):
    torch.manual_seed(seed)
    model = _Container()
    model.transformer = _Container()
    model.transformer.h = nn.ModuleList([_Container()])
    block = model.transformer.h[0]
    block.attn = _Container()
    block.attn.c_attn = nn.Linear(in_features, out_features, bias=False)
    return model


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)
    model = _make_model(int(inputs["in_features"]), int(inputs["out_features"]), int(inputs["seed"]))
    config = FlexPositConfig(
        bits=float(inputs["bits"]),
        base_nsize=int(inputs["base_nsize"]),
        upgrade_nsize=int(inputs["upgrade_nsize"]),
        es=int(inputs["es"]),
    )
    return quantize(model, config, sensitivity=inputs["sensitivity"], progress=False)
