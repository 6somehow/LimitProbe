"""Driver for minference-F008 (state-dependent SnapKV compression branch).

The region's call-chain entry is declared as gather_last_q_vertical_slash_topk_v4, but the
repository calls that method FROM the target function, so the driver calls the target function
minference_with_snapkv_forward.forward directly.  The positive run makes the first (prefill)
call on a fresh cache; the negative run first makes one shorter call, which leaves
self.kv_seq_len registered, and then uses the same final input as the positive run.
"""
import importlib.util
import sys
import types
from pathlib import Path

import torch
import torch.nn as nn
from transformers import LlamaConfig
from transformers.cache_utils import DynamicCache
from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding
from transformers.models.llama.modeling_llama import apply_rotary_pos_emb as _llama_apply_rotary

TARGET_FILE = "minference/modules/minference_forward.py"

HIDDEN_SIZE = 64
NUM_HEADS = 2
HEAD_DIM = 8
NUM_KV_HEADS = 1
LAYER_IDX = 0
STARTING_LAYER = 10
SEED = 0


def _repo_root():
    for entry in sys.path:
        candidate = Path(entry)
        if (candidate / TARGET_FILE).is_file():
            return candidate.resolve()
    raise RuntimeError("repository root not found on sys.path")


def _package(name, path):
    mod = types.ModuleType(name)
    mod.__path__ = [str(path)]
    sys.modules[name] = mod
    return mod


def _load(target_path):
    name = "minference.modules.minference_forward"
    spec = importlib.util.spec_from_file_location(name, target_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    sys.modules["minference.modules"].minference_forward = mod
    spec.loader.exec_module(mod)
    return mod


def _load_snap(path):
    name = "minference.modules.snap_kv"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    sys.modules["minference.modules"].snap_kv = mod
    spec.loader.exec_module(mod)
    return mod


_REPO = _repo_root()
_PKG = _package("minference", _REPO / "minference")
_MODULES = _package("minference.modules", _REPO / "minference/modules")
_OPS = _package("minference.ops", _REPO / "minference/ops")
_PKG.modules = _MODULES
_PKG.ops = _OPS
_LOADED_SNAP = _load_snap(_REPO / "minference/modules/snap_kv.py")
_MFN = _load(_REPO / TARGET_FILE)
_FORWARD = _MFN.minference_with_snapkv_forward()


def apply_rotary_pos_emb(q, k, cos, sin, position_ids=None, unsqueeze_dim=1):
    return _llama_apply_rotary(q, k, cos, sin, unsqueeze_dim=unsqueeze_dim)


class _Rotary(nn.Module):
    def __init__(self):
        super().__init__()
        config = LlamaConfig(
            hidden_size=HIDDEN_SIZE,
            num_attention_heads=NUM_HEADS,
            num_key_value_heads=NUM_KV_HEADS,
            head_dim=HEAD_DIM,
            max_position_embeddings=128,
        )
        self.inner = LlamaRotaryEmbedding(config)

    def forward(self, x, seq_len):
        position_ids = torch.arange(int(seq_len), dtype=torch.long).unsqueeze(0)
        return self.inner(x, position_ids)


class _Config:
    def __init__(self):
        self.window_size = 4
        self.max_capacity_prompt = 8
        self.kernel_size = 3
        self.pooling = "avgpool"
        self._values = {"starting_layer": STARTING_LAYER, "is_search": False, "config_path": ""}

    def to_dict(self):
        return dict(self._values)


class _Attention(nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(SEED)
        self.q_proj = nn.Linear(HIDDEN_SIZE, NUM_HEADS * HEAD_DIM, bias=False)
        self.k_proj = nn.Linear(HIDDEN_SIZE, NUM_KV_HEADS * HEAD_DIM, bias=False)
        self.v_proj = nn.Linear(HIDDEN_SIZE, NUM_KV_HEADS * HEAD_DIM, bias=False)
        self.o_proj = nn.Linear(NUM_HEADS * HEAD_DIM, HIDDEN_SIZE, bias=False)
        self.rotary_emb = _Rotary()
        self.config = _Config()
        self.num_heads = NUM_HEADS
        self.head_dim = HEAD_DIM
        self.num_key_value_heads = NUM_KV_HEADS
        self.num_key_value_groups = NUM_HEADS // NUM_KV_HEADS
        self.hidden_size = HIDDEN_SIZE
        self.layer_idx = LAYER_IDX


class _Cache(DynamicCache):
    def get_usable_length(self, new_seq_length, layer_idx=0):
        return self.get_seq_length(layer_idx)


_ATTN = _Attention()
_CACHE = None


def _reset():
    global _ATTN, _CACHE
    _ATTN = _Attention()
    _CACHE = None


def run(inputs):
    global _CACHE
    action = inputs["action"]
    if action == "reset":
        _reset()
        return None
    if _CACHE is None:
        _CACHE = _Cache()

    if action == "prelude":
        q_len = int(inputs["prelude_q_len"])
    else:
        q_len = int(inputs["q_len"])

    past_len = _CACHE.get_seq_length(0)
    torch.manual_seed(SEED)
    hidden_states = torch.randn(1, q_len, HIDDEN_SIZE)
    attention_mask = torch.zeros(1, 1, q_len, q_len + past_len)
    position_ids = torch.arange(q_len, dtype=torch.long).unsqueeze(0)
    return _FORWARD(_ATTN, hidden_states, attention_mask, position_ids, _CACHE, False, True)
