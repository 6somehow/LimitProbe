"""Driver for infinigen-F009: construct a real SelfAttention and let __init__ decide.

The finding's Region is the guard `if self.layer_id > 1:` in
speedup/flexgen/infinigen/flex_opt.py::SelfAttention.__init__.  The witness controls
`self.layer_id` (2 -> branch taken, 1 -> branch not taken).

The pinned repository ships the code as two editable packages under
third_party/InfiniGen/speedup (flexgen and infinigen).  The child process puts the
repository root on sys.path, so the driver locates the active checkout from sys.path
(this also makes the fresh-checkout replay use its own copy) and adds the two package
directories before importing the code under test at module level.

The call chain recorded by step 4 is TorchDevice.mha -> SelfAttention.__init__, but
TorchDevice.mha never constructs a SelfAttention (the static analysis reports
call_chain_status "not_found").  There is therefore no path from that entry to the
target; the driver calls the target function itself and records the reason in
execution.entry_reason.
"""
import sys
from pathlib import Path

import numpy as np
import torch

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)


def _activate_repo_packages():
    roots = []
    for entry in sys.path:
        if not entry:
            continue
        candidate = Path(entry)
        if (candidate / "speedup" / "flexgen" / "infinigen" / "flex_opt.py").is_file():
            roots.append(candidate)
    if not roots:
        raise RuntimeError("cannot locate the InfiniGen checkout on sys.path")
    root = roots[0]
    for sub in ("speedup/flexgen", "speedup/infinigen"):
        pkg_dir = str(root / sub)
        if pkg_dir not in sys.path:
            sys.path.insert(0, pkg_dir)
    return root


REPO_ROOT = _activate_repo_packages()

import infinigen.flex_opt as flex_opt
from flexgen.compression import CompressionConfig
from flexgen.pytorch_backend import TorchDevice
from flexgen.utils import ExecutionEnv

# CPU-only environment: the target line only reads policy flags and stores env.gpu,
# so both roles use a real TorchDevice over CPU (no GPU kernel runs before the guard).
_CPU_DEVICE = TorchDevice("cpu")
_ENV = ExecutionEnv(gpu=_CPU_DEVICE, cpu=_CPU_DEVICE, disk=None, mixed=None)

_NO_COMPRESSION = CompressionConfig(num_bits=8, group_size=-1, group_dim=1,
                                    symmetric=False, enabled=False)
_POLICY = flex_opt.Policy(
    gpu_batch_size=1,
    num_gpu_batches=1,
    w_gpu_percent=0.0,
    w_cpu_percent=100.0,
    cache_gpu_percent=0.0,
    cache_cpu_percent=100.0,
    act_gpu_percent=0.0,
    act_cpu_percent=100.0,
    overlap=False,
    sep_layer=True,
    pin_weight=False,
    cpu_cache_compute=False,
    attn_sparsity=1.0,
    compress_weight=False,
    comp_weight_config=_NO_COMPRESSION,
    compress_cache=False,
    comp_cache_config=_NO_COMPRESSION,
)

_CONFIG = flex_opt.get_opt_config("opt-125m")


def run(inputs):
    layer_id = int(inputs["self.layer_id"])
    return flex_opt.SelfAttention(
        _CONFIG, _ENV, _POLICY, layer_id,
        False,               # enable_prefetching
        0.2,                 # partial_weight_ratio
        4,                   # alpha
        400,                 # max_num_kv
    )
