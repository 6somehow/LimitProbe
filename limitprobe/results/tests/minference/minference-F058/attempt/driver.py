"""Driver for minference-F058 (state-dependent branch in init_minference_parameters).

The official entry is the closure `minference_forward.forward`; it calls
`self.init_minference_parameters()` as its first statement, which is the target line.

The repository module imports GPU-only kernel modules at import time (pycuda / flash_attn /
the compiled minference.cuda extension) and builds a CUDA tensor at module scope
(`torch.arange(..., device="cuda")`). None of that is on the path to the target, so the
driver installs empty stand-ins for those three ops modules and temporarily redirects
`torch.arange(..., device="cuda")` to CPU while the real `minference_forward.py` is loaded.
The real target function, its caller, and the real `LlamaRotaryEmbedding` are used; the
stand-in kernels are never called on this path (they raise if they are).

`self` is a real `nn.Module` attention stand-in carrying a real LlamaRotaryEmbedding, so
`self.rotary_emb.__class__.__module__` resolves to the real transformers llama module.
It is cached in a module-level slot: the harness runs a prelude call in the same process
before the checked call, and that earlier call is what puts
`apply_rotary_pos_emb` into `self.__dict__`.

The forward path below the target is written for an older transformers signature
(`apply_rotary_pos_emb(q, k, cos, sin, position_ids)`); with transformers 5.23 it fails
after the target decision has been taken. That post-target failure is swallowed only so
the prelude call can complete; the target is the first executable statement of the entry.
"""

import importlib.util
import sys
import types
from pathlib import Path

import torch


def _find_repo_root() -> Path:
    for entry in sys.path:
        base = Path(entry or ".")
        if (base / "minference" / "modules" / "minference_forward.py").is_file():
            return base.resolve()
    raise RuntimeError("cannot locate the MInference repository on sys.path")


_REPO = _find_repo_root()


def _install_import_shims() -> None:
    pkg = types.ModuleType("minference")
    pkg.__path__ = [str(_REPO / "minference")]
    sys.modules["minference"] = pkg
    modules = types.ModuleType("minference.modules")
    modules.__path__ = [str(_REPO / "minference" / "modules")]
    sys.modules["minference.modules"] = modules
    pkg.modules = modules
    ops = types.ModuleType("minference.ops")
    ops.__path__ = [str(_REPO / "minference" / "ops")]
    sys.modules["minference.ops"] = ops
    pkg.ops = ops

    def _unavailable(*args, _name="gpu kernel", **kwargs):
        raise RuntimeError(f"{_name} is a GPU kernel and is not available on CPU")

    gpu_modules = {
        "block_sparse_flash_attention": ["block_sparse_attention"],
        "pit_sparse_flash_attention_v2": ["vertical_slash_sparse_attention"],
        "streaming_kernel": ["streaming_forward", "streaming_forward2"],
    }
    for short, names in gpu_modules.items():
        name = f"minference.ops.{short}"
        mod = types.ModuleType(name)
        for fn in names:
            setattr(mod, fn, _unavailable)
        mod.__dict__["__checklimits_note__"] = "empty GPU-kernel stand-in; never called on this path"
        sys.modules[name] = mod
        setattr(ops, short, mod)


def _load_minference_forward():
    _install_import_shims()
    original_arange = torch.arange

    def _arange_cpu(*args, **kwargs):
        device = kwargs.get("device", None)
        if not torch.cuda.is_available() and device is not None and str(device).startswith("cuda"):
            kwargs = dict(kwargs)
            kwargs["device"] = "cpu"
        return original_arange(*args, **kwargs)

    torch.arange = _arange_cpu
    try:
        spec = importlib.util.spec_from_file_location(
            "minference.modules.minference_forward",
            str(_REPO / "minference" / "modules" / "minference_forward.py"),
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        torch.arange = original_arange


_MF = _load_minference_forward()
_FORWARD = _MF.minference_forward()

from transformers.models.llama.configuration_llama import LlamaConfig  # noqa: E402
from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding  # noqa: E402

torch.manual_seed(0)
torch.set_num_threads(1)

_HIDDEN = 8
_Q_LEN = 2
_SELF = None


class _AttentionStandIn(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        config = LlamaConfig(
            hidden_size=_HIDDEN,
            num_attention_heads=1,
            num_key_value_heads=1,
            max_position_embeddings=16,
        )
        config.starting_layer = 100
        self.config = config
        self.layer_idx = 0
        self.starting_layer = 100
        self.hidden_size = _HIDDEN
        self.num_heads = 1
        self.head_dim = _HIDDEN
        self.num_key_value_heads = 1
        self.num_key_value_groups = 1
        self.rotary_emb = LlamaRotaryEmbedding(config)
        self.q_proj = torch.nn.Linear(_HIDDEN, _HIDDEN)
        self.k_proj = torch.nn.Linear(_HIDDEN, _HIDDEN)
        self.v_proj = torch.nn.Linear(_HIDDEN, _HIDDEN)
        self.o_proj = torch.nn.Linear(_HIDDEN, _HIDDEN)
        self.init_minference_parameters = _MF.init_minference_parameters.__get__(self, _AttentionStandIn)


def _get_self() -> _AttentionStandIn:
    global _SELF
    if _SELF is None:
        _SELF = _AttentionStandIn()
    return _SELF


def run(inputs):
    self = _get_self()
    hidden_states = torch.zeros((1, _Q_LEN, _HIDDEN), dtype=torch.float32)
    attention_mask = torch.zeros((1, 1, _Q_LEN, _Q_LEN), dtype=torch.float32)
    position_ids = torch.zeros((1, _Q_LEN), dtype=torch.long)
    try:
        return _FORWARD(self, hidden_states, attention_mask, position_ids, None, False, False)
    except Exception:
        return None
