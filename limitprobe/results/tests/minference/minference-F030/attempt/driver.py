"""Driver for minference-F030 (minference/modules/minference_forward.py:521).

The official entry is the nested function ``minference_forward.forward``.  The module that holds it
imports three CUDA/Triton kernel modules at import time (pycuda, flash_attn, the CUDA extension) and
builds a CUDA tensor at module level.  Those imports are never executed on the path to the target, so
this loader supplies empty placeholder modules for the operations and runs the module-level tensor on
CPU; the source file itself is left untouched.  The target's function, its callers and every operation
before the target are the real repository code (and real transformers functions).
"""

import importlib
import importlib.util
import sys
import types
from pathlib import Path

import torch
from transformers.models.llama.modeling_llama import apply_rotary_pos_emb, repeat_kv

torch.set_num_threads(1)


def _repo_root():
    for entry in sys.path:
        p = Path(entry)
        if (p / "minference" / "modules" / "minference_forward.py").is_file():
            return p
    raise ImportError("cannot locate the pinned MInference checkout on sys.path")


_REPO = _repo_root()


def _package(name, rel):
    mod = types.ModuleType(name)
    mod.__path__ = [str(_REPO / rel)]
    sys.modules[name] = mod
    return mod


def _kernel_stub(name, attrs):
    mod = types.ModuleType(name)
    for attr in attrs:
        def _unavailable(*args, _attr=attr, **kwargs):
            raise RuntimeError(f"GPU kernel {name}.{_attr} is unavailable on this CPU host")
        setattr(mod, attr, _unavailable)
    sys.modules[name] = mod
    return mod


def _load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, _REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_target():
    _package("minference", "minference")
    _package("minference.modules", "minference/modules")
    _package("minference.ops", "minference/ops")
    _kernel_stub("minference.ops.block_sparse_flash_attention", ["block_sparse_attention"])
    _kernel_stub("minference.ops.pit_sparse_flash_attention_v2", ["vertical_slash_sparse_attention"])
    _kernel_stub("minference.ops.streaming_kernel", ["streaming_forward", "streaming_forward2"])
    _load_module("minference.modules.snap_kv", "minference/modules/snap_kv.py")

    # The pinned module builds a CUDA index tensor at import time.  Redirect only the device argument
    # while the file is executed; the repository file is not changed.
    real_arange = torch.arange

    def cpu_arange(*args, **kwargs):
        if kwargs.get("device") == "cuda":
            kwargs["device"] = "cpu"
        return real_arange(*args, **kwargs)

    torch.arange = cpu_arange
    try:
        mod = _load_module("minference.modules.minference_forward",
                           "minference/modules/minference_forward.py")
    finally:
        torch.arange = real_arange

    # This transformers build no longer exports the helper through the llama star import.  On a CPU
    # host flash-attn is not available, so the dense fallback branch must use gather_qkv.
    if "is_flash_attn_2_available" not in mod.__dict__:
        mod.is_flash_attn_2_available = lambda: False
    return mod


_TARGET = _load_target()
_FORWARD = _TARGET.minference_forward()


class _Rotary(torch.nn.Module):
    """Identity rotary embedding: the target decision cannot depend on the rotation values."""

    def forward(self, hidden_states, position_ids):
        bsz, _heads, q_len, head_dim = hidden_states.shape
        cos = torch.ones(bsz, q_len, head_dim, dtype=hidden_states.dtype)
        sin = torch.zeros(bsz, q_len, head_dim, dtype=hidden_states.dtype)
        return cos, sin


class _Config:
    def __init__(self, values):
        self._values = values

    def to_dict(self):
        return dict(self._values)


class _Attention(torch.nn.Module):
    """Minimal Llama-style attention module carrying the fields minference_forward.forward reads."""

    def __init__(self, layer_idx, starting_layer, is_search, num_heads, head_dim, kv_groups, dtype):
        super().__init__()
        self.config = _Config({
            "layer_idx": layer_idx,
            "starting_layer": starting_layer,
            "is_search": is_search,
            "config_path": "",
        })
        self.layer_idx = layer_idx
        self.starting_layer = -1
        self.is_search = False
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.hidden_size = num_heads * head_dim
        self.num_key_value_heads = num_heads // kv_groups
        self.num_key_value_groups = kv_groups
        self.q_proj = torch.nn.Linear(self.hidden_size, self.num_heads * head_dim, bias=False, dtype=dtype)
        self.k_proj = torch.nn.Linear(self.hidden_size, self.num_key_value_heads * head_dim, bias=False, dtype=dtype)
        self.v_proj = torch.nn.Linear(self.hidden_size, self.num_key_value_heads * head_dim, bias=False, dtype=dtype)
        self.o_proj = torch.nn.Linear(self.num_heads * head_dim, self.hidden_size, bias=False, dtype=dtype)
        self.rotary_emb = _Rotary()

    def init_minference_parameters(self):
        return _TARGET.init_minference_parameters(self)

    def gather_last_q_vertical_slash_topk_v4(self, q, k, v, head_id):
        # CPU stand-in for the GPU sparse kernel, reached only AFTER the target decision.
        weights = torch.matmul(q, k.transpose(2, 3)) / (q.shape[-1] ** 0.5)
        weights = torch.nn.functional.softmax(weights, dim=-1)
        return torch.matmul(weights, v)


def run(inputs):
    seed = int(inputs["seed"])
    dtype = getattr(torch, inputs["dtype"])
    torch.manual_seed(seed)

    self = _Attention(
        layer_idx=int(inputs["layer_idx"]),
        starting_layer=int(inputs["starting_layer"]),
        is_search=bool(inputs["is_search"]),
        num_heads=int(inputs["num_heads"]),
        head_dim=int(inputs["head_dim"]),
        kv_groups=int(inputs["kv_groups"]),
        dtype=dtype,
    )

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    hidden_states = torch.randn(batch_size, q_len, self.hidden_size, dtype=dtype)
    attention_mask = torch.zeros(1, 1, q_len, q_len, dtype=dtype)

    # The installed transformers' apply_rotary_pos_emb takes `unsqueeze_dim` as its fifth argument; the
    # pinned code passes `position_ids` there.  The identity rotary fixture makes 1 the correct value.
    position_ids = 1
    output = _FORWARD(self, hidden_states, attention_mask, position_ids, None, False, False)
    return output[0]
