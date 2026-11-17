"""Driver for flexposit-F002: reach src/flexposit/api.py:189 through the official entry.

The harness places the pinned repository at sys.path[0]; add its ``src`` directory so that
``flexposit`` is imported from the code under test (also in the clean-checkout replay).

A tiny one-layer model makes ``quantize`` cheap on CPU.  The number of sensitivity rows whose
layer name matches the model (``total_windows``) is the constructed counterpart of the derived
witness atom ``state.total_windows``.  With zero matching rows, ``plan_windows`` returns a zero
total and ``quantize`` raises at the target; with one matching row it proceeds with real code.
"""

import os
import sys


def _add_repo_src():
    for p in list(sys.path):
        if p and os.path.isfile(os.path.join(p, "src", "flexposit", "api.py")):
            src = os.path.join(p, "src")
            if src not in sys.path:
                sys.path.insert(0, src)
            return


_add_repo_src()

import torch
import torch.nn as nn

from flexposit.api import FlexPositConfig, quantize


class _Toy(nn.Module):
    def __init__(self, cin, cout):
        super().__init__()
        self.proj = nn.Linear(cin, cout, bias=False)
        with torch.no_grad():
            base = torch.arange(cout * cin, dtype=torch.float32).reshape(cout, cin)
            self.proj.weight.copy_((base + 1.0) / 16.0)


def _matching_rows(total_windows, cin):
    """Sensitivity rows for one layer, all valid channel windows, all matching the layer name."""
    return [("proj", 0, i + 1, -float(i + 1)) for i in range(int(total_windows))]


def run(inputs):
    torch.set_num_threads(1)
    if "seed" in inputs:
        torch.manual_seed(int(inputs["seed"]))

    config = FlexPositConfig(bits=inputs["bits"], base_nsize=inputs["base_nsize"],
                             upgrade_nsize=inputs["upgrade_nsize"], es=inputs["es"])
    model = _Toy(int(inputs["cin"]), int(inputs["cout"]))
    rows = _matching_rows(inputs["total_windows"], int(inputs["cin"]))

    if inputs["quantize"]:
        return quantize(model, config, sensitivity=rows, progress=bool(inputs["progress"]))
    return None
