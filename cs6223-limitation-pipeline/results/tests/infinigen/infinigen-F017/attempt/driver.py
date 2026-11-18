"""Driver for infinigen-F017: the KV-cache split branch of TorchMixedDevice.init_cache_one_gpu_batch.

Step 4 reported call_chain_status "not_found": no static path from TorchDevice.mha to the target,
so the deeper function is called directly with its own real parameters (execution.entry_reason).
Everything up to the target line (the function itself, its imports, the config/task/policy
objects) is the repository's real code; the three base devices are real TorchDevice("cpu")
objects because this machine has no GPU. They are only touched after the target decision, by
allocate(), which the harness stops before in its probe runs.
"""
import sys
from pathlib import Path
from types import SimpleNamespace


def _repo_root():
    for p in sys.path:
        q = Path(p)
        if (q / "speedup" / "flexgen" / "infinigen").is_dir() and (q / "speedup" / "infinigen" / "infinigen").is_dir():
            return q
    raise RuntimeError("pinned InfiniGen checkout not found on sys.path")


_ROOT = _repo_root()
sys.path.insert(0, str(_ROOT / "speedup" / "flexgen"))
sys.path.insert(0, str(_ROOT / "speedup" / "infinigen"))

import infinigen.pytorch_backend as pb  # noqa: E402  (code under test, imported at module level)


def run(inputs):
    pb.fix_recursive_import()
    disk_percent = inputs["policy.cache_disk_percent"]

    config = SimpleNamespace(n_head=2, input_dim=8)
    task = SimpleNamespace(prompt_len=2, gen_len=2)
    policy = SimpleNamespace(gpu_batch_size=2, cache_gpu_percent=50.0,
                             cache_cpu_percent=25.0, cache_disk_percent=disk_percent)

    gpu = pb.TorchDevice("cpu")
    cpu = pb.TorchDevice("cpu")
    disk = pb.TorchDevice("cpu")
    mixed = pb.TorchMixedDevice([gpu, cpu, disk])
    return mixed.init_cache_one_gpu_batch(config, task, policy)
