"""Driver for infinigen-F028.

Calls the official entry TorchDevice.mha on CPU with the InfiniGen PyTorch backend of the
pinned repository.  Positive input takes the partial-weight-index branch (warmup=False,
partial_weight_ratio=0.5); the negative input keeps warmup=False but sets
partial_weight_ratio=None, the neighbouring point on the other side of the
`partial_weight_ratio is not None` boundary, so the branch is skipped.
"""

import os
import sys

_REPO = None
for _p in sys.path:
    if os.path.isdir(os.path.join(_p, "speedup", "flexgen", "infinigen")):
        _REPO = _p
        break
if _REPO is None:
    _REPO = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "third_party", "InfiniGen")

sys.path.insert(0, os.path.join(_REPO, "speedup", "flexgen"))
sys.path.insert(0, os.path.join(_REPO, "speedup", "infinigen"))

import torch

from infinigen.pytorch_backend import TorchDevice, TorchTensor, fix_recursive_import

fix_recursive_import()
torch.set_num_threads(1)

_B, _S, _N_HEAD, _HEAD_DIM = 1, 4, 2, 8
_H = _N_HEAD * _HEAD_DIM


def _tt(t, dev):
    return TorchTensor.create_from_torch(t, dev)


def run(inputs):
    torch.manual_seed(0)
    warmup = inputs["warmup"]
    partial_weight_ratio = inputs["partial_weight_ratio"]

    dev = TorchDevice("cpu")
    inputs_t = torch.randn(_B, _S, _H)
    attention_mask = torch.ones(_B, _S, dtype=torch.bool)

    w_q = _tt(torch.randn(_H, _H + 1), dev)
    b_q = _tt(torch.randn(_H), dev)
    w_k = _tt(torch.randn(_H, _H + 1), dev)
    b_k = _tt(torch.randn(_H), dev)
    w_v = _tt(torch.randn(_H, _H), dev)
    b_v = _tt(torch.randn(_H), dev)
    w_out = _tt(torch.randn(_H, _H), dev)
    b_out = _tt(torch.randn(_H), dev)
    w_ln = _tt(torch.ones(_H), dev)
    b_ln = _tt(torch.zeros(_H), dev)
    donate = [False] * 14

    return dev.mha(_tt(inputs_t, dev), _tt(attention_mask, dev),
                   w_q, b_q, w_k, b_k, w_v, b_v, w_out, b_out, w_ln, b_ln,
                   _N_HEAD, donate, False, None, warmup, partial_weight_ratio)
