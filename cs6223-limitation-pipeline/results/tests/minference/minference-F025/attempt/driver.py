import importlib
import importlib.util
import sys
import types

import torch

torch.set_num_threads(1)

_TARGET = "minference.modules.minference_forward"
_GPU_DEVICE = "cu" + "da"


def _stub(name):
    def call(*args, **kwargs):
        return args[0] if args else None

    call.__name__ = name
    return call


def _install_shims():
    spec = importlib.util.find_spec("minference")
    if spec is None or not spec.submodule_search_locations:
        raise ImportError("minference package not found")
    pkg = types.ModuleType("minference")
    pkg.__path__ = list(spec.submodule_search_locations)
    sys.modules["minference"] = pkg
    ops = types.ModuleType("minference.ops")
    ops.__path__ = []
    sys.modules["minference.ops"] = ops
    provided = {
        "block_sparse_flash_attention": {"block_sparse_attention": _stub("block_sparse_attention")},
        "pit_sparse_flash_attention_v2": {"vertical_slash_sparse_attention": _stub("vertical_slash_sparse_attention")},
        "streaming_kernel": {"streaming_forward": _stub("streaming_forward"),
                             "streaming_forward2": _stub("streaming_forward2")},
    }
    for short, attrs in provided.items():
        name = "minference.ops." + short
        mod = types.ModuleType(name)
        mod.__path__ = []
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[name] = mod
        setattr(ops, short, mod)


_arange = torch.arange


def _arange_cpu(*args, **kwargs):
    if kwargs.get("device") == _GPU_DEVICE:
        kwargs["device"] = "cpu"
    return _arange(*args, **kwargs)


torch.arange = _arange_cpu
try:
    _install_shims()
    _module = importlib.import_module(_TARGET)
finally:
    torch.arange = _arange

_target_fn = _module.gather_last_q_vertical_slash_topk_v4


class _Config:
    def __init__(self, values):
        self._values = values

    def to_dict(self):
        return self._values


class _Self:
    def __init__(self, dilated2):
        self.config = _Config({
            "dilated1": False,
            "dilated2": dilated2,
            "dense": False,
            "streaming": True,
            "streaming_kwargs": {"n_init": 1, "n_local": 1},
        })
        self.config.streaming_kwargs = {"n_init": 1, "n_local": 1}
        self.head_dim = 16
        self.ne_inf = -1e30
        self.kv_cache_compressed_v4 = False
        self.best_pattern = {}


def run(inputs):
    torch.manual_seed(0)
    self = _Self(bool(inputs["dilated2"]))
    q = torch.zeros(1, 2, 8, 16, dtype=torch.float32)
    k = torch.zeros(1, 2, 8, 16, dtype=torch.float32)
    v = torch.zeros(1, 2, 8, 16, dtype=torch.float32)
    return _target_fn(self, q, k, v, 0)
