"""Driver for flexposit-F004: export_tile's signed 5-bit per-column scale check.

The Region's call chain is api.quantize -> export.export_tile, but the pinned source has no
static call edge between them (quantize produces a QuantState; export_tile consumes it later).
The driver therefore calls export_tile directly with a real QuantState / model and records the
reason in execution.entry_reason.  All values below are built from `inputs`.
"""

import os
import sys

import torch
import torch.nn as nn


def _add_repo_src():
    """The pinned checkout is a src-layout repository; the harness puts its root on sys.path."""
    for entry in list(sys.path):
        src = os.path.join(entry or ".", "src")
        if os.path.isfile(os.path.join(src, "flexposit", "export.py")):
            if src not in sys.path:
                sys.path.insert(0, src)
            return


_add_repo_src()

from flexposit.api import FlexPositConfig, LayerState, QuantState
from flexposit.export import export_tile

LAYER = "proj"


def _build_model(cin: int, cout: int) -> nn.Module:
    model = nn.Module()
    model.proj = nn.Linear(cin, cout, bias=False)
    with torch.no_grad():
        model.proj.weight.zero_()
    return model


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    cout = len(inputs["scales"])
    cin = int(inputs["cin"])
    nsize = int(inputs["nsize"])
    es = int(inputs["es"])

    # per-column scale = -log2_scale, taken directly from the input vector
    log2_scale = torch.tensor([-int(s) for s in inputs["scales"]], dtype=torch.int8)

    state = QuantState(config=FlexPositConfig())
    state.layers[LAYER] = LayerState(
        nsize=torch.full((cout,), nsize, dtype=torch.int8),
        log2_scale=log2_scale,
        es=es,
        shape=(cout, cin),
        conv1d=False,
    )
    model = _build_model(cin, cout)
    activations = torch.zeros((cout, cin), dtype=torch.float32)
    return export_tile(model, state, LAYER, activations, col_start=0, n=cout)
