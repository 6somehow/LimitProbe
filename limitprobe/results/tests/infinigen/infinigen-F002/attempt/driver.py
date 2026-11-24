"""Driver for infinigen-F002: reach SelfAttention.prefetch_cache line 442 on CPU.

The target is not on any static path from the declared entry (TorchDevice.mha does not call
prefetch_cache), so the deeper function is called directly (see execution.entry_reason).  The
objects are built with the repository's own flexgen classes; the cache tensor is split over a
TorchMixedDevice exactly as TorchMixedDevice.init_cache_one_gpu_batch would split it.
"""

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

from infinigen.flex_opt import SelfAttention, Policy
from flexgen.pytorch_backend import TorchDevice, TorchMixedDevice
from flexgen.compression import CompressionConfig
from flexgen.utils import ExecutionEnv, Task, ValueHolder

_DTYPES = {"float16": np.float16, "float32": np.float32}


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))

    dtype = _DTYPES[str(inputs["dtype"])]
    num_heads = int(inputs["num_heads"])
    head_dim = int(inputs["head_dim"])
    batch_size = int(inputs["batch_size"])
    seq_len = int(inputs["seq_len"])
    shape = (seq_len, batch_size * num_heads, head_dim)

    cpu = TorchDevice("cpu")
    mixed = TorchMixedDevice([cpu, cpu, cpu])
    env = ExecutionEnv(gpu=cpu, cpu=cpu, disk=None, mixed=mixed)

    comp = CompressionConfig(num_bits=4, group_size=64, group_dim=0, symmetric=False)
    policy = Policy(
        gpu_batch_size=batch_size, num_gpu_batches=1,
        w_gpu_percent=100, w_cpu_percent=0,
        cache_gpu_percent=int(inputs["cache_gpu_percent"]),
        cache_cpu_percent=int(inputs["cache_cpu_percent"]),
        act_gpu_percent=100, act_cpu_percent=0,
        overlap=False, sep_layer=True, pin_weight=False,
        cpu_cache_compute=bool(inputs["cpu_cache_compute"]),
        attn_sparsity=float(inputs["attn_sparsity"]),
        compress_weight=False, comp_weight_config=comp,
        compress_cache=bool(inputs["compress_cache"]), comp_cache_config=comp,
    )
    config = types.SimpleNamespace(
        n_head=num_heads, input_dim=num_heads * head_dim, dtype=dtype,
        vocab_size=4, max_seq_len=max(seq_len, 4), pad_token_id=0,
    )
    attn = SelfAttention(config, env, policy, layer_id=0, enable_prefetching=True)
    attn.task = Task(inputs=None, prompt_len=1, gen_len=2, cut_gen_len=None,
                     do_sample=False, temperature=1.0, stop=None)

    gpu_seg = max(0, min(shape[1], int(inputs["gpu_segments"])))
    if int(inputs["device_kind"]) == 1:
        lens = [gpu_seg, shape[1] - gpu_seg, 0]
        k_home = mixed.allocate(shape, dtype, seg_lengths=lens, pin_memory=False)
        v_home = mixed.allocate(shape, dtype, seg_lengths=lens, pin_memory=False)
    else:
        k_home = cpu.allocate(shape, dtype, pin_memory=False)
        v_home = cpu.allocate(shape, dtype, pin_memory=False)

    cache_home = ValueHolder()
    cache_home.store((k_home, v_home))
    cache_read_buf = ValueHolder()
    prefetch_idx = torch.zeros((1,), dtype=torch.long)
    attn.prefetch_cache(cache_home, cache_read_buf, 1, prefetch_idx, None)
