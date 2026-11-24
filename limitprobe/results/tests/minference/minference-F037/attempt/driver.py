"""Driver for minference-F037.

Calls the official entry `minference.modules.minference_forward::gather_last_q_vertical_slash_topk_v4`
with q/k/v whose last dimension is `head_dim`, so that it reaches the streaming branch and calls
`minference.ops.streaming_kernel::streaming_forward` (target line 609).

The machine has no GPU.  This repository checkout cannot even be imported on CPU, for reasons that
have nothing to do with the finding path:
  * the top-level `minference/__init__.py` pulls in `flash_attn` and `pycuda`, which are not installed;
  * `minference/ops/pit_sparse_flash_attention_v2.py` imports a compiled `minference.cuda` extension
    that does not exist in this commit;
  * `minference/modules/minference_forward.py` runs `torch.arange(..., device="cuda")` at module scope.

So before importing the real modules we install **inert import shims**: bare module objects that only
satisfy the imports of GPU-only code paths that are never executed here, and a temporary
torch.arange wrapper that maps an explicit CUDA device to CPU for that one module-level allocation.
The code under test itself (both files of the call chain) is loaded from the repository unchanged.
None of these shims is called on the path to the target: the branch decision is made from the real
`q.shape[-1]`.  Below the target the real Triton kernel launcher runs and raises on CPU; the harness
only needs the branch decision (probe runs stop there), and the post-target error is deterministic.
"""
import importlib.machinery
import os
import sys
import types

import torch


def _repo_root():
    for p in sys.path:
        if p and os.path.isfile(os.path.join(p, "minference", "ops", "streaming_kernel.py")):
            return os.path.abspath(p)
    raise RuntimeError("cannot locate the MInference repository on sys.path")


def _stub_module(name, **attrs):
    m = types.ModuleType(name)
    m.__spec__ = importlib.machinery.ModuleSpec(name, None)
    m.__version__ = "0.0.0"
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


_REPO = _repo_root()

# inert shims for absent third-party / compiled GPU-only dependencies (import-time only)
_stub_module("flash_attn", flash_attn_func=None, flash_attn_varlen_func=None)
_stub_module("pycuda")
_stub_module("pycuda.autoprimaryctx")
_stub_module("pycuda.compiler", SourceModule=object)
_cuda = _stub_module("minference.cuda", convert_vertical_slash_indexes=None)
sys.modules["pycuda"].autoprimaryctx = sys.modules["pycuda.autoprimaryctx"]
sys.modules["pycuda"].compiler = sys.modules["pycuda.compiler"]

# synthetic top package so the real `minference/__init__.py` (which imports vLLM / flash_attn) is not run;
# submodules still resolve to the real repository files through __path__
_pkg = types.ModuleType("minference")
_pkg.__path__ = [os.path.join(_REPO, "minference")]
_pkg.__spec__ = importlib.machinery.ModuleSpec("minference", None, is_package=True)
_pkg.__spec__.submodule_search_locations = _pkg.__path__
sys.modules["minference"] = _pkg

_real_arange = torch.arange


def _arange_cpu_for_cuda(*args, **kwargs):
    dev = kwargs.get("device")
    if dev is not None and str(dev).startswith("cuda"):
        kwargs["device"] = "cpu"
    return _real_arange(*args, **kwargs)


torch.arange = _arange_cpu_for_cuda
try:
    from minference.modules.minference_forward import gather_last_q_vertical_slash_topk_v4
finally:
    torch.arange = _real_arange


class _Config:
    def __init__(self, n_init, n_local):
        self.streaming_kwargs = {"n_init": n_init, "n_local": n_local}

    def to_dict(self):
        return {"streaming": True}


class _Attention:
    """Minimal `self` for the entry method: only the streaming config is read on this path."""

    def __init__(self, head_dim, n_init, n_local):
        self.config = _Config(n_init, n_local)
        self.head_dim = head_dim
        self.ne_inf = -torch.finfo(torch.float32).max
        self.kv_cache_compressed_v4 = False


def run(inputs):
    head_dim = int(inputs["head_dim"])
    batch_size = int(inputs["batch_size"])
    num_heads = int(inputs["num_heads"])
    seq_len = int(inputs["seq_len"])
    n_init = int(inputs["n_init"])
    n_local = int(inputs["n_local"])
    seed = int(inputs["seed"])
    head_id = int(inputs["head_id"])
    dtype = getattr(torch, inputs["dtype"])

    torch.manual_seed(seed)
    try:
        torch.set_num_threads(1)
    except Exception:
        pass

    gen = torch.Generator(device="cpu").manual_seed(seed)
    q = torch.randn(batch_size, num_heads, seq_len, head_dim, generator=gen, dtype=dtype)
    k = torch.randn(batch_size, num_heads, seq_len, head_dim, generator=gen, dtype=dtype)
    v = torch.randn(batch_size, num_heads, seq_len, head_dim, generator=gen, dtype=dtype)
    attn = _Attention(head_dim, n_init, n_local)
    return gather_last_q_vertical_slash_topk_v4(attn, q, k, v, head_id)
