"""Call TorchDevice.mha_gen with the attn_sparsity boundary from the witness.

The entry is the target function itself.  All tensors the function reads before
the assertion are built with the repository's own TorchDevice/TorchTensor
classes on CPU; k_cache/v_cache are the mixed-device cache pair, which is not a
TorchTensor (the Region's path prefix).  Under the positive input the real
``assert attn_sparsity >= 1.0`` raises before any mixed-device code runs; under
the negative input the assertion passes and the CPU-only run stops later inside
the mixed-device attention path (after the target), which is not part of the
verdict.
"""
import sys
from pathlib import Path

import numpy as np
import torch

_REPO = None
for _entry in sys.path:
    _candidate = Path(_entry)
    if (_candidate / "speedup" / "flexgen" / "infinigen" / "pytorch_backend.py").exists():
        _REPO = _candidate
        break
if _REPO is None:
    raise RuntimeError("cannot locate the InfiniGen checkout on sys.path")

for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _p = str(_REPO / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import infinigen.pytorch_backend as pb

pb.fix_recursive_import()


def run(inputs):
    torch.manual_seed(inputs["seed"])
    torch.set_num_threads(1)

    attn_sparsity = inputs["attn_sparsity"]
    b = inputs["batch_size"]
    tgt_s = inputs["target_seq_len"]
    n_head = inputs["n_head"]
    head_dim = inputs["head_dim"]
    h = n_head * head_dim

    dev = pb.TorchDevice("cpu")
    np_dtype = np.float32

    def alloc(shape, dtype=np_dtype):
        return dev.allocate(shape, dtype, pin_memory=False)

    inputs_t = alloc((b, tgt_s, h))
    attention_mask = alloc((b, inputs["mask_len"]), bool)
    w_q = alloc((h, h + 1))
    b_q = alloc((h,))
    w_k = alloc((h, h + 1))
    b_k = alloc((h,))
    w_v = alloc((h, h))
    b_v = alloc((h,))
    w_out = alloc((h, h))
    b_out = alloc((h,))
    w_ln = alloc((h,))
    b_ln = alloc((h,))

    cache_shape = tuple(inputs["cache_shape"])
    k_cache = np.zeros(cache_shape, dtype=np_dtype)
    v_cache = np.zeros(cache_shape, dtype=np_dtype)

    return dev.mha_gen(
        inputs_t, attention_mask,
        w_q, b_q, w_k, b_k, w_v, b_v, w_out, b_out, w_ln, b_ln,
        n_head, k_cache, v_cache, list(inputs["donate"]), attn_sparsity,
        inputs["compress_cache"], None, None, None, None, None, None,
    )
