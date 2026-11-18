"""Driver: call the official entry with the inputs the harness passes in.

The host has a CPU-only torch and the repository's compiled CUDA extension is not built.
The harness-declared stand-ins replace torch.arange (import-time CUDA call) and the CUDA
index conversion.  Import-only placeholders for flash_attn / pycuda are created here after
real transformers is imported, because transformers probes flash_attn's __spec__.
"""
from __future__ import annotations

import importlib
import importlib.machinery
import sys
import types
from pathlib import Path

import torch
import transformers.models.llama.modeling_llama  # noqa: F401  (before the flash_attn placeholder)

_CUDA_AVAILABLE = torch.cuda.is_available()


def _repo_root() -> Path:
    for entry in sys.path:
        candidate = Path(entry)
        if (candidate / "minference" / "ops" / "pit_sparse_flash_attention_v2.py").is_file():
            return candidate
    raise RuntimeError("repository root not found on sys.path")


def _placeholder(name: str, **attrs):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
        sys.modules[name] = module
    for key, value in attrs.items():
        if not hasattr(module, key):
            setattr(module, key, value)
    return module


_placeholder("flash_attn", flash_attn_func=None, flash_attn_varlen_func=None)
_placeholder("pycuda")
_placeholder("pycuda.autoprimaryctx")
_placeholder("pycuda.compiler", SourceModule=None)

_REPO = _repo_root()
for _name, _path in (("minference", _REPO / "minference"),
                     ("minference.ops", _REPO / "minference" / "ops"),
                     ("minference.modules", _REPO / "minference" / "modules")):
    if _name not in sys.modules:
        _mod = types.ModuleType(_name)
        _mod.__path__ = [str(_path)]
        _mod.__spec__ = importlib.machinery.ModuleSpec(_name, loader=None, is_package=True)
        sys.modules[_name] = _mod
if "minference.cuda" in sys.modules:
    sys.modules["minference"].cuda = sys.modules["minference.cuda"]
sys.modules["minference"].ops = sys.modules["minference.ops"]
sys.modules["minference"].modules = sys.modules["minference.modules"]

_forward = importlib.import_module("minference.modules.minference_forward")
_entry = _forward.gather_last_q_vertical_slash_topk_v4


class _Config:
    def to_dict(self):
        return {"dilated1": True}


class _Model:
    config = _Config()


def run(inputs):
    head_dim = int(inputs["head_dim"])
    context_size = int(inputs["context_size"])
    batch_size = int(inputs["batch_size"])
    num_heads = int(inputs["num_heads"])
    head_id = int(inputs["head_id"])
    torch.manual_seed(int(inputs["seed"]))
    dtype = getattr(torch, inputs["dtype"])
    shape = (batch_size, num_heads, context_size, head_dim)
    q = torch.randn(shape, dtype=dtype)
    k = torch.randn(shape, dtype=dtype)
    v = torch.randn(shape, dtype=dtype)
    return _entry(_Model(), q, k, v, head_id)
