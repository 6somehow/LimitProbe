"""Driver: call the official entry gather_last_q_vertical_slash_topk_v4.

The entry is the target function itself.  It needs a `self` with a config whose
to_dict() reports the dispatch flags; before the target it only reads
self.config.  The GPU-only op modules are declared as stand-ins (behind the
target) and torch.arange is shimmed to CPU for the module-level CUDA constant so
that the file can be imported on this CPU-only machine.
"""

import sys
import types
from pathlib import Path

import torch


def _find_repo():
    for entry in sys.path:
        if not entry:
            continue
        cand = Path(entry) / "minference" / "modules" / "minference_forward.py"
        if cand.is_file():
            return Path(entry)
    raise RuntimeError("cannot locate the MInference repository on sys.path")


_REPO = _find_repo()

# Import the file under test without running minference/__init__.py, which pulls in
# concrete CUDA extensions that are absent here (the target function only needs the
# module itself).
_pkg = types.ModuleType("minference")
_pkg.__path__ = [str(_REPO / "minference")]
sys.modules.setdefault("minference", _pkg)

import minference.modules.minference_forward as _mf  # noqa: E402

torch.set_num_threads(1)


class _Config:
    def __init__(self, values):
        self._values = dict(values)

    def to_dict(self):
        return dict(self._values)


class _Self:
    def __init__(self, dense, head_dim, best_pattern, kv_cache_compressed_v4):
        self.config = _Config({"dense": dense})
        self.head_dim = int(head_dim)
        self.ne_inf = torch.finfo(torch.float32).min
        self.best_pattern = dict(best_pattern)
        self.kv_cache_compressed_v4 = bool(kv_cache_compressed_v4)


def run(inputs):
    q_len = int(inputs["q_len"])
    dense = inputs["dense"]
    head_count = int(inputs["head_count"])
    head_dim = int(inputs["head_dim"])
    dtype = getattr(torch, str(inputs["dtype"]))
    seed = int(inputs["seed"])
    best_pattern = dict(inputs["best_pattern"])
    kv_cache_compressed_v4 = bool(inputs["kv_cache_compressed_v4"])

    torch.manual_seed(seed)
    q = torch.randn(1, head_count, q_len, head_dim, dtype=dtype)
    k = torch.randn(1, head_count, q_len, head_dim, dtype=dtype)
    v = torch.randn(1, head_count, q_len, head_dim, dtype=dtype)

    obj = _Self(dense, head_dim, best_pattern, kv_cache_compressed_v4)
    return _mf.gather_last_q_vertical_slash_topk_v4(obj, q, k, v, 0)
