"""Driver for infinigen-F010 (Region B002, flex_opt.py:389).

The registered call chain is [TorchDevice.mha, SelfAttention.load_cache].  TorchDevice.mha
does not call SelfAttention.load_cache anywhere in the repository (the static analysis also
reports `not_found`), so the deepest reachable official function of the chain is called
directly; the reason is recorded in form.execution.entry_reason.

All code below the driver is the repository's real code: SelfAttention, Policy, ValueHolder,
Task and TorchDevice are imported from the pinned checkout.  No GPU kernel is replaced; the
environment is simply built with CPU TorchDevices, which is what the CPU-only machine has.
The target decision `self.policy.attn_sparsity >= 1.0` only reads policy values, so it is
independent of the tensor contents and of the devices.
"""

import os
import sys
from pathlib import Path

import numpy as np
import torch


def _install_repo_on_path():
    # `infinigen` is a namespace package split over speedup/flexgen/infinigen (flex_opt.py)
    # and speedup/infinigen/infinigen (the controllers); both portions must be importable.
    for entry in list(sys.path):
        base = Path(entry or os.getcwd())
        root = None
        if (base / "speedup" / "flexgen" / "infinigen" / "flex_opt.py").exists():
            root = base
        elif (base / "infinigen" / "flex_opt.py").exists() and (base / "flexgen").is_dir():
            root = base.parent.parent
        if root is not None:
            for part in (root / "speedup" / "flexgen", root / "speedup" / "infinigen"):
                if part.is_dir() and str(part) not in sys.path:
                    sys.path.insert(0, str(part))
            return
    raise RuntimeError("could not locate the InfiniGen speedup tree in sys.path")


_install_repo_on_path()

from infinigen.flex_opt import Policy, SelfAttention  # noqa: E402
from flexgen.pytorch_backend import TorchDevice  # noqa: E402
from flexgen.utils import ExecutionEnv, Task, ValueHolder  # noqa: E402

torch.set_num_threads(1)

_DTYPES = {"float16": np.float16, "float32": np.float32}


class _Config:
    def __init__(self, n_head, input_dim):
        self.n_head = n_head
        self.input_dim = input_dim


def run(inputs):
    path = int(inputs["path"])
    sparsity = float(inputs["sparsity_milli"]) / 1000.0
    prompt_len = int(inputs["prompt_len"])
    gen_len = int(inputs["gen_len"])
    decode_step = int(inputs["decode_step"])
    n_head = int(inputs["num_heads"])
    batch_size = int(inputs["batch_size"])
    head_dim = int(inputs["head_dim"])
    dtype = _DTYPES[inputs["dtype"]]
    seed = int(inputs["seed"])

    torch.manual_seed(seed)
    np.random.seed(seed)

    cpu = TorchDevice("cpu")
    env = ExecutionEnv(gpu=cpu, cpu=cpu)

    if path == 0:
        compress_cache, cpu_cache_compute = False, False
    elif path == 1:
        compress_cache, cpu_cache_compute = False, True
    elif path == 2:
        compress_cache, cpu_cache_compute = False, True
    else:
        raise ValueError(f"unsupported path {path}")

    policy = Policy(
        gpu_batch_size=batch_size,
        num_gpu_batches=1,
        w_gpu_percent=100,
        w_cpu_percent=0,
        cache_gpu_percent=100,
        cache_cpu_percent=0,
        act_gpu_percent=100,
        act_cpu_percent=0,
        overlap=False,
        sep_layer=True,
        pin_weight=False,
        cpu_cache_compute=cpu_cache_compute,
        attn_sparsity=sparsity,
        compress_weight=False,
        comp_weight_config=None,
        compress_cache=compress_cache,
        comp_cache_config=None,
    )

    config = _Config(n_head=n_head, input_dim=n_head * head_dim)
    attention = SelfAttention(config, env, policy, layer_id=0, enable_prefetching=False)
    task = Task(inputs=None, prompt_len=prompt_len, gen_len=gen_len, cut_gen_len=None,
                do_sample=False, temperature=1.0, stop=None)
    attention.set_task(task)

    shape = (prompt_len + gen_len - 1, batch_size * n_head, head_dim)
    k_home = cpu.allocate(shape, dtype, pin_memory=False)
    v_home = cpu.allocate(shape, dtype, pin_memory=False)

    cache_home = ValueHolder()
    cache_home.store((k_home, v_home))
    cache_read_buf = ValueHolder()

    attention.load_cache(cache_home, cache_read_buf, decode_step)
    return None
