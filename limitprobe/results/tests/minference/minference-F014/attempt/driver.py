"""Driver: reach the head-dimension assertion in streaming_kernel._forward.

The hand-off entry is gather_last_q_vertical_slash_topk_v4, but importing
minference/modules/minference_forward.py on this CPU-only host pulls in
flash_attn, pycuda and the precompiled minference.cuda extension at module load,
and it builds a module-level tensor on device="cuda". Those import-time
dependencies sit before the target and can only be supplied with stand-ins; the
driver therefore starts at call_chain[1], streaming_forward, which is real
repository code and calls the target through TritonMultiStageDotProductionAttention.append.
The witness values 16/32/64/128/256 are all in streaming_forward's no-padding
list, so the target sees exactly the requested Lk. This is the recorded entry_reason.
"""

import importlib.util
import sys
import types
from pathlib import Path

import torch

torch.set_num_threads(1)


def _repo_root():
    for entry in sys.path:
        if entry and (Path(entry) / "minference" / "ops" / "streaming_kernel.py").is_file():
            return Path(entry)
    raise RuntimeError("repository root with minference/ is not on sys.path")


_REPO = _repo_root()
for _name, _path in (
    ("minference", _REPO / "minference"),
    ("minference.ops", _REPO / "minference/ops"),
):
    if _name not in sys.modules:
        _pkg = types.ModuleType(_name)
        _pkg.__path__ = [str(_path)]
        _pkg.__package__ = _name
        sys.modules[_name] = _pkg

_spec = importlib.util.spec_from_file_location(
    "minference.ops.streaming_kernel", _REPO / "minference/ops/streaming_kernel.py"
)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

streaming_forward = _module.streaming_forward


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))

    Lk = int(inputs["Lk"])
    batch = int(inputs["batch"])
    heads = int(inputs["heads"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    dtype = getattr(torch, str(inputs["dtype"]))

    q = torch.randn(batch, heads, q_len, Lk, dtype=dtype)
    k = torch.randn(batch, heads, k_len, Lk, dtype=dtype)
    v = torch.randn(batch, heads, k_len, Lk, dtype=dtype)

    return streaming_forward(q, k, v, int(inputs["n_init"]), int(inputs["n_local"]))
