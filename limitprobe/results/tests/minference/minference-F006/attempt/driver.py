"""Driver for minference-F006: run the real minference_forward.forward on a CPU attention object.

The repository package imports GPU-only modules (flash_attn, GPU binding modules, a compiled GPU extension) in
its __init__, so the target module is loaded directly under a minimal package shim.  Those GPU
symbols are never called before the target line; the negative run uses the repository's own CPU
attention fallback (gather_qkv) because flash-attn is marked unavailable.
"""

import os
import sys
import types

import torch
import torch.nn as nn


def _repo_root():
    for p in sys.path:
        if p and os.path.isdir(os.path.join(p, "minference", "modules")):
            return os.path.abspath(p)
    raise ImportError("cannot locate the MInference repository on sys.path")


_REPO = _repo_root()


def _stub_package(name, path=None):
    mod = types.ModuleType(name)
    if path is not None:
        mod.__path__ = [path]
    sys.modules[name] = mod
    return mod


def _gpu_only(*args, **kwargs):
    raise RuntimeError("GPU-only kernel reached on CPU")


# Load minference.modules.minference_forward without executing the GPU-heavy package __init__.
_stub_package("minference", os.path.join(_REPO, "minference"))
_stub_package("minference.modules", os.path.join(_REPO, "minference", "modules"))
_stub_package("minference.ops", os.path.join(_REPO, "minference", "ops"))
_block = _stub_package("minference.ops.block_sparse_flash_attention")
_block.block_sparse_attention = _gpu_only
_pit = _stub_package("minference.ops.pit_sparse_flash_attention_v2")
_pit.vertical_slash_sparse_attention = _gpu_only
_stream = _stub_package("minference.ops.streaming_kernel")
_stream.streaming_forward = _gpu_only
_stream.streaming_forward2 = _gpu_only

_orig_arange = torch.arange


def _cpu_arange(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and str(device) != "cpu":
        kwargs["device"] = "cpu"
    return _orig_arange(*args, **kwargs)


torch.arange = _cpu_arange
try:
    import minference.modules.minference_forward as _mf
finally:
    torch.arange = _orig_arange

_mf.is_flash_attn_2_available = lambda: False


def apply_rotary_pos_emb(q, k, cos, sin, position_ids=None, unsqueeze_dim=1):
    return q, k


class _RotaryEmb(nn.Module):
    def forward(self, x, position_ids=None):
        return None, None


class _Config:
    def __init__(self, values):
        self._values = dict(values)

    def to_dict(self):
        return dict(self._values)


class _StubCache:
    def get_usable_length(self, kv_seq_len, layer_idx):
        return 0

    def update(self, key_states, value_states, layer_idx, cache_kwargs):
        return key_states, value_states


class _ToyAttention(nn.Module):
    def __init__(self, inputs):
        super().__init__()
        hidden = int(inputs["hidden_size"])
        self.q_proj = nn.Linear(hidden, int(inputs["num_heads"]) * int(inputs["head_dim"]), bias=False)
        kv_size = int(inputs["num_key_value_heads"]) * int(inputs["head_dim"])
        self.k_proj = nn.Linear(hidden, kv_size, bias=False)
        self.v_proj = nn.Linear(hidden, kv_size, bias=False)
        self.o_proj = nn.Linear(hidden, hidden, bias=False)
        self.num_heads = int(inputs["num_heads"])
        self.head_dim = int(inputs["head_dim"])
        self.num_key_value_heads = int(inputs["num_key_value_heads"])
        self.num_key_value_groups = self.num_heads // self.num_key_value_heads
        self.hidden_size = hidden
        layer_idx = inputs["layer_idx"]
        self.layer_idx = None if layer_idx == inputs["unset_sentinel"] else layer_idx
        self.rotary_emb = _RotaryEmb()
        self.config = _Config({"starting_layer": int(inputs["starting_layer"]), "is_search": False})
        self.init_minference_parameters = types.MethodType(_mf.init_minference_parameters, self)


_FORWARD = _mf.minference_forward()
_DTYPES = {"float32": torch.float32, "float64": torch.float64}


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)
    torch.set_default_dtype(_DTYPES[inputs["dtype"]])

    attn = _ToyAttention(inputs)
    past_key_value = _StubCache() if inputs["past_key_value"] else None

    bsz = int(inputs["bsz"])
    q_len = int(inputs["q_len"])
    hidden_states = torch.randn(bsz, q_len, int(inputs["hidden_size"]))
    attention_mask = torch.zeros(bsz, 1, q_len, q_len)
    position_ids = torch.arange(q_len, dtype=torch.long).unsqueeze(0)

    forward = _FORWARD.__get__(attn, _ToyAttention)
    return forward(hidden_states, attention_mask, position_ids, past_key_value, False, bool(inputs["past_key_value"]))
