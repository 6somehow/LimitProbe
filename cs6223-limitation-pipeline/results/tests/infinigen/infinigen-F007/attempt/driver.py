"""Call the official entry TorchDevice.mha_gen on the sparse CPU attention path.

The target ``assert src.device.device_type != DeviceType.MIXED`` is inside
``general_copy``.  mha_gen reaches it through ``_sparse_attention_value`` with
``v_cache = (v_home, v_buf)`` on the CPU branch (both branches of mha_gen call
the same real function, so the CPU branch reaches the same line).  The driver
only builds CPU tensors and one real TorchMixedDevice; it replaces nothing.
"""

import sys
from pathlib import Path

import numpy as np
import torch


def _repo_root():
    for entry in sys.path:
        if not entry:
            continue
        root = Path(entry)
        if ((root / "speedup" / "flexgen" / "infinigen" / "pytorch_backend.py").is_file()
                and (root / "speedup" / "infinigen" / "infinigen" / "skewing_controller.py").is_file()):
            return root
    raise RuntimeError("InfiniGen repository root is not on sys.path")


_REPO = _repo_root()
for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _p = str(_REPO / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import infinigen.pytorch_backend as pb

pb.fix_recursive_import()

torch.set_num_threads(1)


def _zeros(dev, shape, torch_dtype):
    return pb.TorchTensor.create_from_torch(
        torch.zeros(shape, dtype=torch_dtype, device=dev.dev), dev)


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))

    attn_sparsity = float(inputs["attn_sparsity"])
    src_is_mixed = int(inputs["src_mixed"])
    b = int(inputs["batch_size"])
    tgt_s = int(inputs["target_seq_len"])
    n_head = int(inputs["n_head"])
    head_dim = int(inputs["head_dim"])
    seq_len = int(inputs["seq_len"])
    h = n_head * head_dim

    dev = pb.TorchDevice("cpu")
    mixed = pb.TorchMixedDevice([dev])

    inputs_t = _zeros(dev, (b, tgt_s, h), torch.float32)
    attention_mask = pb.TorchTensor.create_from_torch(
        torch.ones((b, seq_len), dtype=torch.bool, device=dev.dev), dev)

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

    k_cache = _zeros(dev, (seq_len, b * n_head, head_dim), torch.float32)

    topk = int(attn_sparsity * (seq_len - 1))
    buf_shape = (topk + 1, b * n_head, head_dim)
    v_buf = mixed.allocate(buf_shape, np.float16, seg_lengths=[b * n_head], pin_memory=False)
    if src_is_mixed == 1:
        v_home = mixed.allocate((seq_len, b * n_head, head_dim), np.float16,
                                seg_lengths=[b * n_head], pin_memory=False)
    else:
        v_home = dev.allocate((seq_len, b * n_head, head_dim), np.float16, pin_memory=False)

    return dev.mha_gen(
        inputs_t, attention_mask,
        w_q, b_q, w_k, b_k, w_v, b_v, w_out, b_out, w_ln, b_ln,
        n_head, k_cache, (v_home, v_buf), [False, False], attn_sparsity,
        False, None, None, None, None, None, None,
    )
