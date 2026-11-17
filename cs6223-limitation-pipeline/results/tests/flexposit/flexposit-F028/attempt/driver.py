"""Driver for flexposit-F028: quantize() rejects bits above base_nsize without a sensitivity ranking."""

import os
import sys

for _root in sys.path:
    if os.path.isfile(os.path.join(_root, "src", "flexposit", "api.py")):
        sys.path.insert(0, os.path.join(_root, "src"))
        break

import torch
import torch.nn as nn

from flexposit.api import FlexPositConfig, quantize


class _Tiny(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.proj = nn.Linear(in_features, out_features, bias=False)


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    model = _Tiny(int(inputs["in_features"]), int(inputs["out_features"]))
    config = FlexPositConfig(
        bits=int(inputs["bits"]),
        base_nsize=int(inputs["base_nsize"]),
        upgrade_nsize=int(inputs["upgrade_nsize"]),
        es=int(inputs["es"]),
    )
    return quantize(model, config, sensitivity=inputs["sensitivity"], progress=False)
