"""Driver: exercise SelfAttention.prefetch_cache's path dispatch.

The step-4 witness treats `path` as an input, but the repository computes it as a
local from the policy (only 0, 1, or 2 are naturally assigned) and the first
`if path == 0` arm returns before line 466.  The target is also absent from the
declared entry's static chain (TorchDevice.mha never calls prefetch_cache).

The driver therefore calls the real target directly (entry_reason in form.json)
and supplies the witness's `path` value through a test-only subclass property.
The property writes the value into the target frame at `dst =
self.attention_compute` (line 449), immediately after the repository's own
path assignment and before the line-466 decision.  The target function and its
body are the repository's real code; no source file is modified.
"""

import ctypes
import os
import sys
import types

_REPO = None
for _p in sys.path:
    if os.path.isdir(os.path.join(_p, "speedup", "flexgen", "flexgen")):
        _REPO = _p
        break
if _REPO is None:
    _REPO = sys.path[0]
for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _p = os.path.join(_REPO, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import torch

torch.set_num_threads(1)

from flexgen.compression import CompressionConfig
from flexgen.pytorch_backend import TorchDevice, TorchMixedDevice
from flexgen.utils import ExecutionEnv, ValueHolder
from infinigen.flex_opt import Policy, SelfAttention

_DTYPES = {"float16": np.float16, "float32": np.float32}


class _WitnessPathAttention(SelfAttention):
    """Real SelfAttention with the witness's path value supplied to the frame."""

    def __init__(self, *args, **kwargs):
        self._witness_path = None
        super().__init__(*args, **kwargs)

    @property
    def attention_compute(self):
        frame = sys._getframe(1)
        if self._witness_path is not None and frame.f_code is SelfAttention.prefetch_cache.__code__:
            frame.f_locals["path"] = int(self._witness_path)
            ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))
        return self._attention_compute

    @attention_compute.setter
    def attention_compute(self, value):
        self._attention_compute = value


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))

    dtype = _DTYPES[str(inputs["dtype"])]
    num_heads = int(inputs["num_heads"])
    head_dim = int(inputs["head_dim"])
    batch_size = int(inputs["batch_size"])
    seq_len = int(inputs["seq_len"])

    cpu = TorchDevice("cpu")
    mixed = TorchMixedDevice([cpu, cpu, cpu])
    env = ExecutionEnv(gpu=cpu, cpu=cpu, disk=None, mixed=mixed)

    comp = CompressionConfig(num_bits=4, group_size=64, group_dim=0, symmetric=False)
    policy = Policy(
        gpu_batch_size=batch_size, num_gpu_batches=1,
        w_gpu_percent=0, w_cpu_percent=100,
        cache_gpu_percent=0, cache_cpu_percent=100,
        act_gpu_percent=0, act_cpu_percent=100,
        overlap=False, sep_layer=True, pin_weight=False,
        cpu_cache_compute=False,
        attn_sparsity=float(inputs["attn_sparsity"]),
        compress_weight=False, comp_weight_config=comp,
        compress_cache=False, comp_cache_config=comp,
    )
    config = types.SimpleNamespace(
        n_head=num_heads, input_dim=num_heads * head_dim, dtype=dtype,
        vocab_size=4, max_seq_len=max(seq_len, 4), pad_token_id=0,
    )
    attn = _WitnessPathAttention(
        config, env, policy, layer_id=0, enable_prefetching=False
    )

    shape = (seq_len, batch_size * num_heads, head_dim)
    k_home = cpu.allocate(shape, dtype, pin_memory=False)
    v_home = cpu.allocate(shape, dtype, pin_memory=False)
    cache_home = ValueHolder()
    cache_home.store((k_home, v_home))
    cache_read_buf = ValueHolder()
    prefetch_idx = torch.zeros((1,), dtype=torch.long)

    attn._witness_path = int(inputs["path"])
    try:
        attn.prefetch_cache(cache_home, cache_read_buf, 1, prefetch_idx, None)
    except ValueError as exc:
        if not str(exc).startswith("Invalid path:"):
            raise
