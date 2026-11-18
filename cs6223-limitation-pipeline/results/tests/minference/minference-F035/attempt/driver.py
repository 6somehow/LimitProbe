"""Driver: exercise SnapKVCluster.update_kv's pooling branch on CPU.

The entry named in the static call chain (gather_last_q_vertical_slash_topk_v4) does
not call update_kv; step 4 reports call_chain_status "not_found". We therefore load the
target module directly from the repository under test and call SnapKVCluster.update_kv,
the target function, recording the reason in form.execution.entry_reason.
"""

import importlib.util
import os
import sys

import torch


def _load_snap_kv():
    for root in sys.path:
        if not root:
            continue
        cand = os.path.join(root, "minference", "modules", "snap_kv.py")
        if os.path.isfile(cand):
            spec = importlib.util.spec_from_file_location("_snap_kv_under_test", cand)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise ImportError("minference/modules/snap_kv.py not found on sys.path")


_SNAP = _load_snap_kv()
SnapKVCluster = _SNAP.SnapKVCluster

torch.set_num_threads(1)


def run(inputs):
    seed = int(inputs["seed"])
    torch.manual_seed(seed)
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)

    bsz = int(inputs["batch_size"])
    heads = int(inputs["num_heads"])
    q_len = int(inputs["q_len"])
    head_dim = int(inputs["head_dim"])
    dtype = getattr(torch, inputs["dtype"])

    q = torch.randn((bsz, heads, q_len, head_dim), generator=gen, dtype=torch.float32).to(dtype)
    k = torch.randn((bsz, heads, q_len, head_dim), generator=gen, dtype=torch.float32).to(dtype)
    v = torch.randn((bsz, heads, q_len, head_dim), generator=gen, dtype=torch.float32).to(dtype)

    cluster = SnapKVCluster(
        window_size=int(inputs["window_size"]),
        max_capacity_prompt=int(inputs["max_capacity_prompt"]),
        kernel_size=int(inputs["kernel_size"]),
        pooling=inputs["pooling"],
    )
    return cluster.update_kv(k, q, v, None, 1)
