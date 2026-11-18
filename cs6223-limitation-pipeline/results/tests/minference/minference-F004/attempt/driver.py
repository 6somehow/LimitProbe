"""Driver for minference-F004 (state-dependent static-pattern cache in self.vs).

The target module cannot be imported as part of the installed package here: it imports several
GPU-only modules (pycuda / flash_attn / triton) at module scope and builds a GPU tensor at
import time.  The harness already replaced torch.arange and the vertical/slash kernel; this
file only supplies the remaining import scaffolding (parent packages and unused GPU module
placeholders) and then executes the real repository file found on the child's sys.path.
"""
import importlib.util
import json
import math
import sys
import types
from pathlib import Path

import torch
import torch.nn as nn

from checklimits.models import PIPELINE_ROOT

_MANIFEST = json.loads((Path(__file__).with_name("manifest.json")).read_text())
_TARGET_FILE = "minference/modules/minference_forward.py"


def _repo_root():
    for entry in sys.path:
        candidate = Path(entry)
        if (candidate / _TARGET_FILE).is_file():
            return candidate.resolve()
    return (PIPELINE_ROOT / _MANIFEST["repo_dir"]).resolve()


def _module(name, **attrs):
    mod = types.ModuleType(name)
    mod.__path__ = []
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


def _unused_gpu_standin(*args, **kwargs):
    return args[0] if args else None


def _load_target():
    pkg = _module("minference")
    ops = _module("minference.ops")
    modules = _module("minference.modules")
    pkg.ops = ops
    pkg.modules = modules

    block_sparse = _module("minference.ops.block_sparse_flash_attention",
                           block_sparse_attention=_unused_gpu_standin)
    streaming = _module("minference.ops.streaming_kernel",
                        streaming_forward=_unused_gpu_standin,
                        streaming_forward2=_unused_gpu_standin)
    snap = _module("minference.modules.snap_kv")
    ops.block_sparse_flash_attention = block_sparse
    ops.streaming_kernel = streaming
    modules.snap_kv = snap

    pit_name = "minference.ops.pit_sparse_flash_attention_v2"
    if pit_name in sys.modules:
        ops.pit_sparse_flash_attention_v2 = sys.modules[pit_name]

    path = _repo_root() / _TARGET_FILE
    name = "minference.modules.minference_forward"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(torch=torch, nn=nn, math=math)
    sys.modules[name] = mod
    modules.minference_forward = mod
    spec.loader.exec_module(mod)
    return mod


_MFN = _load_target()
_ENTRY = _MFN.gather_last_q_vertical_slash_topk_v4
_Q_LEN = 64


class _Config:
    def __init__(self, values):
        self._values = dict(values)

    def to_dict(self):
        return dict(self._values)


class _Attention:
    def __init__(self):
        self.config = _Config({"static_pattern": True})
        self.best_pattern = {}
        self.kv_cache_compressed_v4 = False
        self.ne_inf = float("-inf")


_SELF = _Attention()


def run(inputs):
    action = inputs["action"]
    if action == "reset":
        _SELF.__dict__.pop("vs", None)
        return None
    if action == "setup":
        _SELF.__dict__.pop("vs", None)

    torch.manual_seed(int(inputs["seed"]))
    batch = int(inputs["batch"])
    heads = int(inputs["heads"])
    head_dim = int(inputs["head_dim"])
    q = torch.randn(batch, heads, _Q_LEN, head_dim)
    k = torch.randn(batch, heads, _Q_LEN, head_dim)
    v = torch.randn(batch, heads, _Q_LEN, head_dim)
    return _ENTRY(_SELF, q, k, v, 0)
