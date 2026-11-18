"""Driver: call the official entry with tensors built from the witness names.

Finding minference-F011: _triton_block_sparse_attention asserts that the head
dimension Lk is one of {16, 32, 64, 128}.  The positive input uses Lk=127, the
negative Lk=128.

The repository's minference_forward.py cannot be imported on this CPU-only box
as-is: block_sparse_flash_attention.py imports pycuda and flash_attn (not
installed, GPU-only), pit_sparse_flash_attention_v2 imports the precompiled
minference.cuda extension (not shipped), and minference_forward.py builds a
module-level torch tensor on device="cuda".  Those import-time dependencies
are not touched by the target decision.  The module shims below only satisfy
the imports; the entry function and every function on the call chain are the
real repository code.  The CUDA arange is mapped to CPU for the import only
(LAST_Q_MASK is unused by the block_sparse path).
"""

import importlib.machinery
import sys
import types
from pathlib import Path


def _repo_root() -> Path:
    for entry in sys.path:
        if entry and (Path(entry) / "minference" / "ops" / "block_sparse_flash_attention.py").is_file():
            return Path(entry)
    raise RuntimeError("repository root with minference/ is not on sys.path")


_REPO = _repo_root()


def _noop(*args, **kwargs):
    return None


def _install_import_shim(name, attrs, version=None):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    try:
        module.__path__ = []
        module.__file__ = "<checklimits import shim %s>" % name
        module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
        if version is not None:
            module.__version__ = version
    except Exception:
        pass
    for key, value in attrs.items():
        setattr(module, key, value)


_install_import_shim("pycuda", {}, version="2024.1")
_install_import_shim("pycuda.autoprimaryctx", {})
_install_import_shim("pycuda.compiler", {"SourceModule": object})
_install_import_shim("flash_attn", {"flash_attn_varlen_func": _noop, "flash_attn_func": _noop}, version="2.5.0")
_install_import_shim("minference.cuda", {"convert_vertical_slash_indexes": _noop})

# namespace package object: load the real entry module without running
# minference/__init__.py (which imports unrelated optional/GPU modules)
if "minference" not in sys.modules:
    _pkg = types.ModuleType("minference")
    _pkg.__path__ = [str(_REPO / "minference")]
    _pkg.__file__ = str(_REPO / "minference" / "__init__.py")
    sys.modules["minference"] = _pkg

import torch  # noqa: E402

_ORIGINAL_ARANGE = torch.arange


def _cpu_arange(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and "cuda" in str(device):
        kwargs["device"] = "cpu"
    return _ORIGINAL_ARANGE(*args, **kwargs)


torch.arange = _cpu_arange
try:
    from minference.modules.minference_forward import gather_last_q_vertical_slash_topk_v4 as _ENTRY
finally:
    torch.arange = _ORIGINAL_ARANGE


class _Config:
    def __init__(self, flags):
        self._flags = dict(flags)

    def to_dict(self):
        return dict(self._flags)


class _AttentionState:
    def __init__(self, head_dim, flags, pattern):
        self.head_dim = head_dim
        self.config = _Config(flags)
        self.best_pattern = pattern
        self.ne_inf = float("inf")
        self.kv_cache_compressed_v4 = False


def run(inputs):
    torch.set_num_threads(1)
    torch.manual_seed(int(inputs["seed"]))

    batch = int(inputs["batch"])
    heads = int(inputs["heads"])
    seq_len = int(inputs["seq_len"])
    head_dim = int(inputs["Lk"])
    head_id = int(inputs["head_id"])
    dtype = getattr(torch, str(inputs["dtype"]))

    q = torch.randn(batch, heads, seq_len, head_dim, dtype=dtype)
    k = torch.randn(batch, heads, seq_len, head_dim, dtype=dtype)
    v = torch.randn(batch, heads, seq_len, head_dim, dtype=dtype)

    state = _AttentionState(head_dim, {}, {head_id: (str(inputs["pattern"]), 100, 1, 1)})
    return _ENTRY(state, q, k, v, head_id)
