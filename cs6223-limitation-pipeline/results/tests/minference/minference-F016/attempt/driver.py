"""Driver for minference-F016: call the official entry gather_last_q_vertical_slash_topk_v4.

The pinned module is imported on CPU.  Its package ``minference/__init__.py`` pulls in
GPU-only siblings (flash-attn, pycuda) that are not used by this call chain, and the module
itself builds a ``LAST_Q_MASK`` constant with ``torch.arange(..., device="cuda")`` at import
time.  Those import-time obstacles are bypassed with CPU-only module/constant shims; they are
not on the call chain before the target and the target module (streaming_kernel) is the real
repository code.  Everything else is built from ``inputs``.
"""
import sys
import types

import torch


def _find_repo() -> str:
    for entry in sys.path:
        from pathlib import Path

        p = Path(entry)
        if (p / "minference" / "modules" / "minference_forward.py").exists():
            return str(p)
    raise RuntimeError("pinned MInference repository is not on sys.path")


_REPO = _find_repo()

# Skip minference/__init__.py and its GPU-only imports; keep the real subpackages.
if "minference" not in sys.modules:
    _pkg = types.ModuleType("minference")
    _pkg.__path__ = [_REPO + "/minference"]
    sys.modules["minference"] = _pkg
for _sub in ("modules", "ops"):
    _name = "minference." + _sub
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        _m.__path__ = [_REPO + "/minference/" + _sub]
        sys.modules[_name] = _m

# Unused siblings imported at module import: block_sparse needs pycuda/flash_attn and
# pit_sparse needs minference.cuda, which is absent from the pinned checkout.
for _mod, _fn in (
    ("minference.ops.block_sparse_flash_attention", "block_sparse_attention"),
    ("minference.ops.pit_sparse_flash_attention_v2", "vertical_slash_sparse_attention"),
):
    if _mod not in sys.modules:
        _stub = types.ModuleType(_mod)
        setattr(_stub, _fn, lambda *a, **k: None)
        sys.modules[_mod] = _stub

# LAST_Q_MASK is built at import time on CUDA; it is only consumed by the non-streaming
# branches after the target.  Build the same constant on CPU for the import.
_orig_arange = torch.arange


def _cpu_arange(*args, **kwargs):
    if kwargs.get("device") == "cuda":
        kwargs["device"] = "cpu"
    return _orig_arange(*args, **kwargs)


torch.arange = _cpu_arange
try:
    from minference.modules.minference_forward import gather_last_q_vertical_slash_topk_v4
finally:
    torch.arange = _orig_arange


class _Config:
    def __init__(self, values, streaming_kwargs):
        self._values = dict(values)
        self.streaming_kwargs = dict(streaming_kwargs)

    def to_dict(self):
        return dict(self._values)


class _Attention:
    def __init__(self, inputs):
        self.config = _Config(
            {
                "dilated1": bool(inputs["dilated1"]),
                "dilated2": bool(inputs["dilated2"]),
                "dense": bool(inputs["dense"]),
                "streaming": bool(inputs["streaming"]),
            },
            {"n_init": int(inputs["n_init"]), "n_local": int(inputs["n_local"])},
        )
        self.head_dim = int(inputs["head_dim"])
        self.ne_inf = torch.finfo(torch.float32).min
        self.best_pattern = {}
        self.kv_cache_compressed_v4 = False


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))

    batch = int(inputs["batch"])
    heads = int(inputs["num_heads"])
    head_dim = int(inputs["head_dim"])
    dtype = getattr(torch, str(inputs["dtype"]))

    def tensor(seq_len):
        return torch.randn((batch, heads, seq_len, head_dim), dtype=dtype)

    q = tensor(int(inputs["q_len"]))
    k = tensor(int(inputs["k_len"]))
    v = tensor(int(inputs["v_len"]))

    attention = _Attention(inputs)
    return gather_last_q_vertical_slash_topk_v4(attention, q, k, v, int(inputs["head_id"]))
