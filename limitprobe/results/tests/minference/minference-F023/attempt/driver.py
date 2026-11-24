"""Driver for finding minference-F023.

The target is the module-level function
``minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4``.
Its target statement is ``if q_len == 1:`` where ``q_len = q.shape[2]``.

The repository package imports GPU-only modules (flash_attn, pycuda, triton kernels)
at import time.  The target decision only reads ``q.shape[2]`` and ``k.size(2)``, so the
driver loads the real source file from the pinned checkout with the GPU-only sibling
modules left unexecuted (they are never called before the target).  No behaviour of the
target function or of its inputs is replaced.
"""

import importlib.util
import math
import sys
import types
from pathlib import Path

import torch

torch.manual_seed(0)
torch.set_num_threads(1)
torch.cuda.is_available()  # CPU-only run; does not enable CUDA

HEAD_DIM = 8
NUM_HEADS = 1
BATCH = 1
MIN_KV_LEN = 4


def _find_repo():
    for entry in sys.path:
        if not entry:
            continue
        root = Path(entry)
        candidate = root / "minference" / "modules" / "minference_forward.py"
        if candidate.is_file():
            return root.resolve()
    raise RuntimeError("pinned MInference checkout not found on sys.path")


def _ensure_package(name, path):
    mod = types.ModuleType(name)
    mod.__path__ = [str(path)]
    mod.__package__ = name
    sys.modules[name] = mod
    parent, _, child = name.rpartition(".")
    if parent and parent in sys.modules:
        setattr(sys.modules[parent], child, mod)
    return mod


def _stub_module(name, **attrs):
    mod = types.ModuleType(name)
    mod.__path__ = []
    mod.__package__ = name.rpartition(".")[0]
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    parent, _, child = name.rpartition(".")
    if parent and parent in sys.modules:
        setattr(sys.modules[parent], child, mod)
    return mod


def _load_minference_forward():
    repo = _find_repo()
    _ensure_package("minference", repo / "minference")
    _ensure_package("minference.modules", repo / "minference" / "modules")
    _ensure_package("minference.ops", repo / "minference" / "ops")

    def unavailable(*args, **kwargs):
        raise NotImplementedError("GPU-only kernel is not available on CPU")

    _stub_module("minference.ops.block_sparse_flash_attention", block_sparse_attention=unavailable)
    _stub_module("minference.ops.pit_sparse_flash_attention_v2", vertical_slash_sparse_attention=unavailable)
    _stub_module("minference.ops.streaming_kernel", streaming_forward=unavailable, streaming_forward2=unavailable)
    _stub_module("minference.modules.snap_kv")

    real_arange = torch.arange

    def cpu_arange(*args, **kwargs):
        device = kwargs.get("device")
        if device is not None and str(device).startswith("cuda"):
            kwargs["device"] = "cpu"
        return real_arange(*args, **kwargs)

    torch.arange = cpu_arange
    try:
        path = repo / "minference" / "modules" / "minference_forward.py"
        spec = importlib.util.spec_from_file_location("minference.modules.minference_forward", path)
        module = importlib.util.module_from_spec(spec)
        module.__dict__["torch"] = torch
        module.__dict__["math"] = math
        module.__dict__["nn"] = torch.nn
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        torch.arange = real_arange
    return module


minference_forward = _load_minference_forward()
gather_last_q_vertical_slash_topk_v4 = minference_forward.gather_last_q_vertical_slash_topk_v4


class _AttentionSelf:
    """Minimal receiver: the target reads no self attribute before the decision."""


def run(inputs):
    q_len = int(inputs["q_len"])
    kv_len = max(q_len, MIN_KV_LEN)
    q = torch.zeros(BATCH, NUM_HEADS, q_len, HEAD_DIM, dtype=torch.float32)
    k = torch.zeros(BATCH, NUM_HEADS, kv_len, HEAD_DIM, dtype=torch.float32)
    v = torch.zeros(BATCH, NUM_HEADS, kv_len, HEAD_DIM, dtype=torch.float32)
    return gather_last_q_vertical_slash_topk_v4(_AttentionSelf(), q, k, v, 0)
