"""Driver for infinigen-F001: call SelfAttention.load_cache on the mixed-cache path.

The hand-off call chain is [TorchDevice.mha, SelfAttention.load_cache] with status
not_found: TorchDevice.mha performs the attention maths and never calls load_cache.
The driver therefore calls the deeper chain function directly and records the reason
in form.json (execution.entry_reason).  Both the target function and everything it
calls before line 426 are the repository's real CPU implementations; no stand-ins.
"""

import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np


def _repo_root():
    for entry in sys.path:
        if not entry:
            continue
        root = Path(entry)
        if ((root / "speedup" / "flexgen" / "flexgen" / "pytorch_backend.py").is_file()
                and (root / "speedup" / "infinigen" / "infinigen" / "skewing_controller.py").is_file()):
            return root
    raise RuntimeError("InfiniGen repository root is not on sys.path")


_REPO = _repo_root()
for _pkg in (_REPO / "speedup" / "infinigen", _REPO / "speedup" / "flexgen"):
    if str(_pkg) not in sys.path:
        sys.path.insert(0, str(_pkg))

import torch

from flexgen.pytorch_backend import TorchDevice, TorchMixedDevice
from flexgen.utils import ExecutionEnv, Task, ValueHolder
from infinigen.flex_opt import Policy, SelfAttention

torch.set_num_threads(1)


def _build(inputs):
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)

    # Small CPU shapes.  Line 426 depends only on attn_sparsity and on the mixed
    # device having a non-empty first shard, not on these sizes.
    n_head = 2
    head_dim = 4
    input_dim = n_head * head_dim
    gpu_batch_size = 2
    prompt_len = 4
    gen_len = 2
    layer_id = 0
    enable_prefetching = False
    i = 1

    config = SimpleNamespace(n_head=n_head, input_dim=input_dim, dtype=np.float16)
    task = Task(inputs=None, prompt_len=prompt_len, gen_len=gen_len,
                cut_gen_len=None, do_sample=False, temperature=1.0, stop=None)
    policy = Policy(
        gpu_batch_size=gpu_batch_size,
        num_gpu_batches=1,
        w_gpu_percent=0.0,
        w_cpu_percent=100.0,
        cache_gpu_percent=50.0,
        cache_cpu_percent=50.0,
        act_gpu_percent=0.0,
        act_cpu_percent=100.0,
        overlap=False,
        sep_layer=True,
        pin_weight=False,
        cpu_cache_compute=True,
        attn_sparsity=float(inputs["attn_sparsity"]),
        compress_weight=False,
        comp_weight_config=None,
        compress_cache=False,
        comp_cache_config=None,
    )

    cpu = TorchDevice("cpu")
    other_cpu = TorchDevice("cpu")
    backing_cpu = TorchDevice("cpu")
    mixed = TorchMixedDevice([cpu, other_cpu, backing_cpu])
    env = ExecutionEnv(gpu=cpu, cpu=cpu, disk=None, mixed=mixed)

    cpu.init_attention_compute_workspace(config, task, policy)

    attn = SelfAttention(config, env, policy, layer_id=layer_id,
                         enable_prefetching=enable_prefetching)
    attn.set_task(task)

    if int(inputs["path"]) == 2:
        k_home, v_home = mixed.init_cache_one_gpu_batch(config, task, policy)
    else:
        k_home, v_home = cpu.init_cache_one_gpu_batch(config, task, policy)

    cache_home = ValueHolder()
    cache_home.store((k_home, v_home))
    cache_read_buf = ValueHolder()

    return attn, cache_home, cache_read_buf, i


def run(inputs):
    attn, cache_home, cache_read_buf, i = _build(inputs)
    attn.load_cache(cache_home, cache_read_buf, i)
    return {"path": int(inputs["path"]), "attn_sparsity": float(inputs["attn_sparsity"])}
