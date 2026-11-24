"""Driver for minference-F024: exercise the dilated1 branch of

`gather_last_q_vertical_slash_topk_v4` through the official entry point.

The entry function is the Region target itself (call_chain has one element), so the driver
calls it directly with a small CPU tensor batch and a minimal attention-like `self`.

The repository module has two CPU-hostile pieces at import time: `torch.arange(..., device="cuda")`
at module scope and optional GPU dependencies (`flash_attn`, `pycuda`, the compiled
`minference.cuda` extension) imported by neighbouring modules.  The driver installs CPU/import
shims for those symbols only; none of them is read by the target decision, which looks at
`self.config.to_dict()["dilated1"]`.
"""

import importlib
import sys
import types
from pathlib import Path

# Import transformers before adding the flash_attn shim: transformers probes whether flash_attn is
# installed and expects a real package spec while it does so.
import transformers.models.llama.modeling_llama  # noqa: F401

import torch


def _find_repo_package() -> Path:
    for entry in sys.path:
        cand = Path(entry or ".") / "minference" / "modules" / "minference_forward.py"
        if cand.is_file():
            return cand.parents[1]
    raise FileNotFoundError("minference package not found on sys.path")


def _install_cpu_import_shims() -> None:
    for name in ("flash_attn", "pycuda", "pycuda.autoprimaryctx", "pycuda.compiler", "minference.cuda"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["flash_attn"].flash_attn_varlen_func = lambda *a, **k: None
    sys.modules["flash_attn"].flash_attn_func = lambda *a, **k: None
    sys.modules["pycuda.compiler"].SourceModule = object
    sys.modules["minference.cuda"].convert_vertical_slash_indexes = lambda *a, **k: None

    # Load the package without running minference/__init__.py (it pulls in flash_attn via inf_llm).
    # Sub-modules are still imported from the real repository directory.
    pkg = types.ModuleType("minference")
    pkg.__path__ = [str(_find_repo_package())]
    sys.modules["minference"] = pkg


_install_cpu_import_shims()

_arange = torch.arange


def _cpu_arange(*args, **kwargs):
    if kwargs.get("device") == "cuda":
        kwargs["device"] = "cpu"
    return _arange(*args, **kwargs)


torch.arange = _cpu_arange
try:
    _mf = importlib.import_module("minference.modules.minference_forward")
finally:
    torch.arange = _arange

gather_last_q_vertical_slash_topk_v4 = _mf.gather_last_q_vertical_slash_topk_v4

_QLEN = 8
_HEADS = 1
_HEAD_DIM = 16
_BATCH = 1
_HEAD_ID = 0
_SEED = 0


class _Config:
    def __init__(self, values):
        self._values = dict(values)

    def to_dict(self):
        return dict(self._values)


class _AttentionState:
    def __init__(self, dilated1):
        self.config = _Config({"dilated1": dilated1})
        self.head_dim = _HEAD_DIM
        self.best_pattern = {}
        self.kv_cache_compressed_v4 = False
        self.ne_inf = torch.finfo(torch.float32).min


def run(inputs):
    torch.manual_seed(_SEED)
    torch.set_num_threads(1)

    state = _AttentionState(inputs["dilated1"])
    q = torch.randn(_BATCH, _HEADS, _QLEN, _HEAD_DIM, dtype=torch.float32)
    k = torch.randn(_BATCH, _HEADS, _QLEN, _HEAD_DIM, dtype=torch.float32)
    v = torch.randn(_BATCH, _HEADS, _QLEN, _HEAD_DIM, dtype=torch.float32)

    return gather_last_q_vertical_slash_topk_v4(state, q, k, v, _HEAD_ID)
