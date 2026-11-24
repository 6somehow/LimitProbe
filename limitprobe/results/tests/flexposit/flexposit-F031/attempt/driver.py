"""Driver: quantize a tiny model through the official entry, then export one tile.

The Region target is ``export_tile`` (src/flexposit/export.py:131). Step 4 found no
static call chain from the entry to it, so the driver calls the official entry
``quantize`` first to build the QuantState that ``export_tile`` consumes, then calls
``export_tile`` on that state (see execution.entry_reason in form.json).

The positive/negative inputs select a 2-column output window either straddling the
boundary between the base and the upgraded channel window (two Posit sizes) or lying
inside one window (a single Posit size). Everything else is identical, so the only
difference is the column window that ``export_tile`` is asked to export.
"""

from __future__ import annotations

import os
import sys

# The harness puts the repository root on sys.path; the package itself lives in its
# src/ directory, so add that directory ahead of any other flexposit installation.
for _p in list(sys.path):
    if not _p:
        continue
    _src = os.path.join(os.path.abspath(_p), "src")
    if os.path.isfile(os.path.join(_src, "flexposit", "__init__.py")):
        if _src not in sys.path:
            sys.path.insert(0, _src)
        break

import torch
import torch.nn as nn

torch.manual_seed(0)
torch.set_num_threads(1)

from flexposit.api import FlexPositConfig, quantize
from flexposit.export import export_tile


class _Tiny(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.proj = nn.Linear(4, 4, bias=False)


_WEIGHTS = torch.tensor(
    [
        [0.13, -0.27, 0.41, -0.09],
        [0.22, 0.35, -0.17, 0.28],
        [-0.31, 0.11, 0.26, -0.38],
        [0.16, -0.23, -0.44, 0.19],
    ],
    dtype=torch.float32,
)

# selection -> (col_start, n): the channel window handed to export_tile.
# "straddle" starts at column 1, so columns 1..2 span the upgraded/base boundary;
# "inside" starts at column 0 and stays inside the upgraded window 0..2.
_SELECTIONS = {"straddle": (1, 2), "inside": (0, 2)}


def run(inputs):
    torch.manual_seed(0)
    col_start, n = _SELECTIONS[inputs["selection"]]

    model = _Tiny()
    with torch.no_grad():
        model.proj.weight.copy_(_WEIGHTS)

    config = FlexPositConfig(bits=4.5, base_nsize=4, upgrade_nsize=5, es=1)
    # Upgrade output channels 0..2 to Posit(5,1); channels 2..4 stay Posit(4,1).
    sensitivity = [("proj", 0, 2, -1.0)]
    state = quantize(model, config, sensitivity=sensitivity, progress=False)

    activations = torch.ones((n, 4), dtype=torch.float32)
    return export_tile(model, state, "proj", activations, col_start=col_start, n=n)
