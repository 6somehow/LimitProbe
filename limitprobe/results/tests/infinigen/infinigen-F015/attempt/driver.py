"""Driver for infinigen-F015: call TorchDevice.mha_gen and let attn_sparsity pick the branch.

CPU only.  The target decision at pytorch_backend.py:422 happens before any attention math,
so the tensors only need shapes that satisfy the prefix and the condition.  Calls that would
need a GPU happen after the decision and are not replaced here.
"""
import sys
from pathlib import Path

import torch

_REPO = None
for _p in list(sys.path):
    if (Path(_p) / "speedup" / "flexgen" / "flexgen").is_dir():
        _REPO = Path(_p)
        break
if _REPO is not None:
    for _sub in ("speedup/flexgen", "speedup/infinigen"):
        _q = str(_REPO / _sub)
        if _q not in sys.path:
            sys.path.insert(0, _q)

from infinigen import pytorch_backend as pb


def _t(data, dev):
    return pb.TorchTensor.create_from_torch(data, dev)


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(False)

    pb.fix_recursive_import()
    dev = pb.TorchDevice("cpu")

    b, tgt_s, n_head, head_dim = 1, 1, 1, 4
    h = n_head * head_dim
    src_cache = 3

    inputs_data = torch.randn((b, tgt_s, h), dtype=torch.float32)
    attention_mask = torch.ones((b, src_cache), dtype=torch.bool)

    w_q = torch.randn((h, h + 1), dtype=torch.float32)
    w_k = torch.randn((h, h + 1), dtype=torch.float32)
    w_v = torch.randn((h, h), dtype=torch.float32)
    w_out = torch.randn((h, h), dtype=torch.float32)
    b_q = torch.zeros((h,), dtype=torch.float32)
    b_k = torch.zeros((h,), dtype=torch.float32)
    b_v = torch.zeros((h,), dtype=torch.float32)
    b_out = torch.zeros((h,), dtype=torch.float32)
    w_ln = torch.ones((h,), dtype=torch.float32)
    b_ln = torch.zeros((h,), dtype=torch.float32)

    k_cache = torch.randn((src_cache, b * n_head, head_dim), dtype=torch.float32)
    v_cache = torch.randn((src_cache, b * n_head, head_dim), dtype=torch.float32)

    donate = [False] * 14

    dev.mha_gen(
        _t(inputs_data, dev), _t(attention_mask, dev),
        _t(w_q, dev), _t(b_q, dev), _t(w_k, dev), _t(b_k, dev),
        _t(w_v, dev), _t(b_v, dev), _t(w_out, dev), _t(b_out, dev),
        _t(w_ln, dev), _t(b_ln, dev),
        n_head, _t(k_cache, dev), _t(v_cache, dev), donate,
        inputs["attn_sparsity"], False, None,
        None, None, None, None, None,
    )
