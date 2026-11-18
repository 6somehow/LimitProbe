"""Driver: call the official entry `flexposit.api.quantize` with a tiny model.

The finding is about `_check_posit` rejecting an `nsize` outside [2, 16].
`quantize` forwards `config.base_nsize` to `search_channels` and then to
`posit_quantize` -> `_posit_quantize_torch` -> `_check_posit`, so the entry
input that reaches the target is the config's base_nsize.
"""

import sys
from pathlib import Path

import torch
import torch.nn as nn


def _repo_src() -> Path:
    for entry in sys.path:
        base = Path(entry or ".")
        if (base / "src" / "flexposit" / "api.py").is_file():
            return base / "src"
    for parent in Path(__file__).resolve().parents:
        cand = parent / "third_party" / "FlexPosit" / "src"
        if (cand / "flexposit" / "api.py").is_file():
            return cand
    raise RuntimeError("pinned FlexPosit checkout not found on sys.path")


_REPO_SRC = _repo_src()
if str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))

from flexposit.api import FlexPositConfig, quantize


def _model() -> nn.Module:
    model = nn.Sequential(nn.Linear(8, 4, bias=False))
    with torch.no_grad():
        for p in model.parameters():
            p.copy_(torch.linspace(-1.0, 1.0, p.numel()).reshape_as(p))
    return model


def run(inputs):
    nsize = int(inputs["nsize"])
    torch.manual_seed(0)
    torch.set_num_threads(1)
    model = _model()
    config = FlexPositConfig(bits=float(nsize), base_nsize=nsize,
                             upgrade_nsize=nsize, es=0)
    quantize(model, config, progress=False)
