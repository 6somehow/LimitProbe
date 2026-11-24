import importlib.util
import os
import sys
import types
from pathlib import Path

import torch
import torch.nn as nn

REPO = Path(sys.path[0]).resolve()
TARGET = REPO / "minference/modules/minference_forward.py"

HIDDEN_SIZE = 64
NUM_HEADS = 1
HEAD_DIM = 64
NUM_KV_HEADS = 1
BATCH_SIZE = 1
LAYER_IDX = 100
STARTING_LAYER = 0
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "f003_config.json")


def _package(name, path):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod
    return sys.modules[name]


_package("minference", REPO / "minference")
_package("minference.modules", REPO / "minference/modules")
_package("minference.ops", REPO / "minference/ops")


def apply_rotary_pos_emb(q, k, cos, sin, position_ids=None, unsqueeze_dim=1):
    return q, k


class _RotaryEmbedding(nn.Module):
    def forward(self, x, position_ids=None):
        return torch.zeros(1, 1, 1, 1), torch.zeros(1, 1, 1, 1)


class _Config:
    def __init__(self, config_path):
        self._values = {
            "is_search": True,
            "config_path": config_path,
            "starting_layer": STARTING_LAYER,
        }

    def to_dict(self):
        return dict(self._values)


class _Attention(nn.Module):
    def __init__(self):
        super().__init__()
        self.q_proj = nn.Linear(HIDDEN_SIZE, NUM_HEADS * HEAD_DIM)
        self.k_proj = nn.Linear(HIDDEN_SIZE, NUM_KV_HEADS * HEAD_DIM)
        self.v_proj = nn.Linear(HIDDEN_SIZE, NUM_KV_HEADS * HEAD_DIM)
        self.o_proj = nn.Linear(NUM_HEADS * HEAD_DIM, HIDDEN_SIZE)
        self.rotary_emb = _RotaryEmbedding()
        self.config = _Config(CONFIG_PATH)
        self.num_heads = NUM_HEADS
        self.head_dim = HEAD_DIM
        self.num_key_value_heads = NUM_KV_HEADS
        self.num_key_value_groups = NUM_HEADS // NUM_KV_HEADS
        self.hidden_size = HIDDEN_SIZE
        self.layer_idx = LAYER_IDX


_spec = importlib.util.spec_from_file_location("minference.modules.minference_forward", TARGET)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

_Attention.init_minference_parameters = _module.init_minference_parameters
_entry = _module.minference_forward()


def run(inputs):
    torch.manual_seed(0)
    q_len = int(inputs["q_len"])
    hidden_states = torch.zeros(BATCH_SIZE, q_len, HIDDEN_SIZE)
    position_ids = torch.arange(q_len, dtype=torch.long).unsqueeze(0)
    attention = _Attention()
    try:
        _entry(attention, hidden_states, None, position_ids, None, False, False)
    except Exception:
        return None
    return None
