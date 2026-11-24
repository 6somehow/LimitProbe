"""Driver for minference-F013: reach the head-dim assertion through the official entry.

`minference/__init__.py` imports GPU-only modules, so the package is loaded as
three namespace shims and only the modules on the dilated path are executed.
The CUDA binding is replaced by the CPU port in sim.py; the flash-attn module
is imported but never called on this path.
"""

import importlib.util
import math
import os
import sys
import types
from pathlib import Path

import torch

_ATTEMPT = Path(__file__).resolve().parent


def _load_local(name):
    spec = importlib.util.spec_from_file_location("_f013_" + name, _ATTEMPT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_SIM = _load_local("sim")


def _repo_root():
    for p in sys.path:
        if p and os.path.isdir(os.path.join(p, "minference", "modules")):
            return os.path.abspath(p)
    raise ImportError("cannot locate the MInference repository on sys.path")


_REPO = Path(_repo_root())


def _shim_package(name, path):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod
    return sys.modules[name]


_shim_package("minference", _REPO / "minference")
_shim_package("minference.modules", _REPO / "minference" / "modules")
_shim_package("minference.ops", _REPO / "minference" / "ops")

_cuda = sys.modules.get("minference.cuda")
if _cuda is None:
    _cuda = types.ModuleType("minference.cuda")
    sys.modules["minference.cuda"] = _cuda
if "convert_vertical_slash_indexes" not in vars(_cuda):
    _cuda.convert_vertical_slash_indexes = _SIM.convert_vertical_slash_indexes

_block_sparse = sys.modules.get("minference.ops.block_sparse_flash_attention")
if _block_sparse is None:
    _block_sparse = types.ModuleType("minference.ops.block_sparse_flash_attention")
    sys.modules["minference.ops.block_sparse_flash_attention"] = _block_sparse
if "block_sparse_attention" not in vars(_block_sparse):
    _block_sparse.block_sparse_attention = _SIM.cpu_block_sparse_attention

_spec = importlib.util.spec_from_file_location(
    "minference.modules.minference_forward",
    _REPO / "minference" / "modules" / "minference_forward.py",
)
_mf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mf
_spec.loader.exec_module(_mf)

_pit = sys.modules["minference.ops.pit_sparse_flash_attention_v2"]
_pit.math = math
_pit._triton_mixed_sparse_attn_fwd_kernel = _SIM.CpuKernelLauncher()

_ENTRY = _mf.gather_last_q_vertical_slash_topk_v4
_DTYPES = {"float32": torch.float32, "float64": torch.float64}


class _Config:
    def to_dict(self):
        return {"dilated1": True}


class _Attention:
    config = _Config()


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)
    dtype = _DTYPES[inputs["dtype"]]
    head_dim = int(inputs["Lk"])
    q_len = int(inputs["q_len"])
    batch = int(inputs["batch_size"])
    heads = int(inputs["num_heads"])

    q = torch.randn(batch, heads, q_len, head_dim, dtype=dtype)
    k = torch.randn(batch, heads, q_len, head_dim, dtype=dtype)
    v = torch.randn(batch, heads, q_len, head_dim, dtype=dtype)
    return _ENTRY(_Attention(), q, k, v, int(inputs["head_id"]))
