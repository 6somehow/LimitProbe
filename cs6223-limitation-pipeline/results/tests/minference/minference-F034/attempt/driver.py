"""Driver: exercise SnapKVCluster.update_kv at the branch decision.

The step 4 call chain is `gather_last_q_vertical_slash_topk_v4 -> SnapKVCluster.update_kv`,
but static analysis reported `call_chain_status = not_found`: the entry is an attention-mask
helper and update_kv is really reached from `llama_flash_attn2_forward`, which is not the
declared entry. The task therefore allows calling the deeper function and recording the
reason. We import the real module file from the pinned repository (loading it directly avoids
the package __init__, which imports a GPU-only `flash_attn` that is not installed on CPU).
"""

import importlib.util
import sys
from pathlib import Path

import torch


def _load_snap_kv():
    for base in sys.path:
        path = Path(base) / "minference" / "modules" / "snap_kv.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("_snap_kv_under_test", str(path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise ImportError("minference/modules/snap_kv.py not found on sys.path")


_snap_kv = _load_snap_kv()
SnapKVCluster = _snap_kv.SnapKVCluster


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    q_len = int(inputs["q_len"])
    max_capacity_prompt = int(inputs["max_capacity_prompt"])
    window_size = int(inputs["window_size"])
    kernel_size = int(inputs["kernel_size"])
    head_dim = int(inputs["head_dim"])
    num_heads = int(inputs["num_heads"])
    batch_size = int(inputs["batch_size"])

    cluster = SnapKVCluster(
        window_size=window_size,
        max_capacity_prompt=max_capacity_prompt,
        kernel_size=kernel_size,
        pooling="avgpool",
    )

    shape = (batch_size, num_heads, q_len, head_dim)
    key_states = torch.randn(shape)
    query_states = torch.randn(shape)
    value_states = torch.randn(shape)
    return cluster.update_kv(key_states, query_states, value_states, None, 1)
