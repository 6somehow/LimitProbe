"""Driver for minference-F015: call the official entry with tensor inputs.

The entry module imports two GPU-only ops modules whose dependencies (flash_attn,
pycuda, the compiled minference.cuda extension) do not exist on this CPU-only
machine.  Those modules are never used on the streaming branch, so inert import
shims are installed only while the three real repository modules are loaded; the
shims are removed before transformers is imported.  The entry function and the
target function are the real repository code.
"""

import importlib.util
import os
import sys
import types

import torch


def _repo_root():
    for p in sys.path:
        if p and os.path.isdir(os.path.join(p, "minference", "ops")):
            if os.path.realpath(p).endswith(os.path.join("third_party", "MInference")):
                return p
    for p in sys.path:
        if p and os.path.isdir(os.path.join(p, "minference", "ops")):
            return p
    raise RuntimeError("repository root not found on sys.path")


_REPO = _repo_root()


def _pkg(name, path):
    mod = sys.modules.get(name)
    if mod is None or not getattr(mod, "__path__", None):
        mod = types.ModuleType(name)
        mod.__path__ = [path]
        mod.__package__ = name
        sys.modules[name] = mod
    return mod


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _shim(name, attrs=None):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
    for k, v in (attrs or {}).items():
        setattr(mod, k, v)
    return mod


class _AnyShim(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None


def _bootstrap():
    _pkg("minference", os.path.join(_REPO, "minference"))
    _pkg("minference.ops", os.path.join(_REPO, "minference", "ops"))
    _pkg("minference.modules", os.path.join(_REPO, "minference", "modules"))

    _load("minference.ops.streaming_kernel", "minference/ops/streaming_kernel.py")

    shim_names = ["flash_attn", "pycuda", "pycuda.autoprimaryctx", "pycuda.compiler", "minference.cuda"]
    for n in shim_names:
        _shim(n)
    sys.modules["flash_attn"].__class__ = _AnyShim
    sys.modules["pycuda"].__path__ = []
    sys.modules["pycuda.compiler"].SourceModule = lambda *a, **k: None
    sys.modules["minference.cuda"].convert_vertical_slash_indexes = lambda *a, **k: None
    try:
        _load("minference.ops.block_sparse_flash_attention",
              "minference/ops/block_sparse_flash_attention.py")
    finally:
        pass
    _load("minference.ops.pit_sparse_flash_attention_v2",
          "minference/ops/pit_sparse_flash_attention_v2.py")
    for n in shim_names:
        sys.modules.pop(n, None)

    _load("minference.modules.snap_kv", "minference/modules/snap_kv.py")

    # minference_forward creates a module-level device="cuda" mask.  Map the device
    # to CPU for the import only; the mask is not used on the streaming branch.
    orig_arange = torch.arange

    def _cpu_arange(*args, **kwargs):
        if kwargs.get("device") == "cuda":
            kwargs["device"] = "cpu"
        return orig_arange(*args, **kwargs)

    torch.arange = _cpu_arange
    try:
        return _load("minference.modules.minference_forward",
                     "minference/modules/minference_forward.py")
    finally:
        torch.arange = orig_arange


_MINF = _bootstrap()
_ENTRY = _MINF.gather_last_q_vertical_slash_topk_v4


class _Config:
    def __init__(self, n_init, n_local):
        self.streaming_kwargs = {"n_init": n_init, "n_local": n_local}
        self._values = {"dilated1": False, "dilated2": False, "dense": False, "streaming": True}

    def to_dict(self):
        return dict(self._values)


class _Self:
    def __init__(self, n_init, n_local, head_dim):
        self.config = _Config(n_init, n_local)
        self.head_dim = head_dim
        self.kv_cache_compressed_v4 = False
        self.vertical = None
        self.slash = None
        self.best_pattern = {}
        self.ne_inf = float("inf")


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    q_dim = int(inputs["q_dim"])
    q_len = int(inputs["q_len"])
    head_dim = int(inputs["head_dim"])
    batch = int(inputs["batch"])
    heads = int(inputs["num_heads"])

    shape = [1] * max(q_dim, 1)
    shape[0] = batch
    if q_dim >= 2:
        shape[1] = heads
    if q_dim >= 3:
        shape[2] = q_len
    if q_dim >= 4:
        shape[3] = head_dim

    q = torch.randn(*shape, dtype=torch.float32)
    k = torch.randn_like(q)
    v = torch.randn_like(q)

    module = _Self(int(inputs["n_init"]), int(inputs["n_local"]), head_dim)
    return _ENTRY(module, q, k, v, int(inputs["head_id"]))
