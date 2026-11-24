"""Driver for infinigen-F014: call TorchDevice.mha_gen with/without a partial-weight query.

The Region condition is ``p_w_q is None`` and its trigger is ``p_w_q is None == True``.
The target statement is ``if p_w_q is not None:`` at
speedup/flexgen/infinigen/pytorch_backend.py:401.  The single declared factor
``partial_weight`` selects the witness point: 0 -> p_w_q is None (the trigger),
non-zero -> a real partial-weight query tensor (the contrast).  Every tensor the
function reads before line 401 is built with the repository's own
TorchDevice/TorchTensor classes on CPU; nothing is replaced.
"""

import sys
from pathlib import Path

import numpy as np


def _repo_root():
    for entry in sys.path:
        if not entry:
            continue
        root = Path(entry)
        if (root / "speedup" / "flexgen" / "infinigen" / "pytorch_backend.py").is_file() \
                and (root / "speedup" / "infinigen" / "infinigen" / "skewing_controller.py").is_file():
            return root
    raise RuntimeError("InfiniGen repository root is not on sys.path")


_REPO = _repo_root()
for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _p = str(_REPO / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import torch  # noqa: E402

import infinigen.pytorch_backend as pb  # noqa: E402

pb.fix_recursive_import()


def _zeros(dev, shape, torch_dtype):
    return pb.TorchTensor.create_from_torch(
        torch.zeros(shape, dtype=torch_dtype, device=dev.dev), dev)


def _run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    b = int(inputs["batch_size"])
    tgt_s = int(inputs["target_seq_len"])
    n_head = int(inputs["n_head"])
    head_dim = int(inputs["head_dim"])
    mask_len = int(inputs["mask_len"])
    cache_len = int(inputs["cache_len"])
    alpha = float(inputs["alpha"])
    max_num_kv = int(inputs["max_num_kv"])
    donate = list(inputs["donate"])
    compress_cache = bool(inputs["compress_cache"])
    h = n_head * head_dim

    dev = pb.TorchDevice("cpu")

    inputs_t = _zeros(dev, (b, tgt_s, h), torch.float32)
    attention_mask = pb.TorchTensor.create_from_torch(
        torch.ones((b, mask_len), dtype=torch.bool, device=dev.dev), dev)

    w_q = _zeros(dev, (h, h + 1), torch.float32)
    b_q = _zeros(dev, (h,), torch.float32)
    w_k = _zeros(dev, (h, h + 1), torch.float32)
    b_k = _zeros(dev, (h,), torch.float32)
    w_v = _zeros(dev, (h, h), torch.float32)
    b_v = _zeros(dev, (h,), torch.float32)
    w_out = _zeros(dev, (h, h), torch.float32)
    b_out = _zeros(dev, (h,), torch.float32)
    w_ln = _zeros(dev, (h,), torch.float32)
    b_ln = _zeros(dev, (h,), torch.float32)

    k_cache = _zeros(dev, (cache_len, b * n_head, head_dim), torch.float32)
    v_cache = _zeros(dev, (cache_len, b * n_head, head_dim), torch.float32)

    if int(inputs["partial_weight"]) == 0:
        p_w_q = None
        partial_k_cache = None
    else:
        p_w_q = _zeros(dev, (h, h + 1), torch.float32)
        partial_k_cache = torch.zeros((cache_len, b * n_head, head_dim), dtype=torch.float32)

    return dev.mha_gen(
        inputs_t, attention_mask,
        w_q, b_q, w_k, b_k, w_v, b_v, w_out, b_out, w_ln, b_ln,
        n_head, k_cache, v_cache, donate, 1.0,
        compress_cache, None, p_w_q, partial_k_cache, None, alpha, max_num_kv,
    )


def run(inputs):
    result = _run(inputs)
    return {"p_w_q_is_none": int(inputs["partial_weight"]) == 0,
            "prefetch_idx_is_none": result[3] is None}
