"""Driver for finding minference-F038.

Calls the official entry ``gather_last_q_vertical_slash_topk_v4`` with q/k/v built from
``inputs`` (``k_len``, ``n_local``); the entry forwards to ``streaming_forward`` where the
target line is ``if k_len > n_local:``.

The GPU-only pieces are declared as ``sim`` mocks in form.json (torch.arange device shim
and the Triton ``_forward`` launcher); they are installed by the harness before this file
is loaded.  The batch/head/head-dim/seed choices are declared in ``design.free_parameters``.
"""
import torch

import minference.modules.minference_forward as mf

torch.manual_seed(0)
torch.set_num_threads(1)


class _Config:
    def __init__(self, n_init, n_local):
        self.streaming_kwargs = {"n_init": n_init, "n_local": n_local}

    def to_dict(self):
        return {"streaming": True}


class _Attention:
    def __init__(self, n_init, n_local, head_dim):
        self.config = _Config(n_init, n_local)
        self.head_dim = head_dim
        self.ne_inf = torch.finfo(torch.float32).min
        self.best_pattern = {}
        self.vertical = None
        self.slash = None


def run(inputs):
    k_len = int(inputs["k_len"])
    n_local = int(inputs["n_local"])
    n_init = int(inputs["n_init"])
    head_dim = int(inputs["head_dim"])
    batch_size = int(inputs["batch_size"])
    num_heads = int(inputs["num_heads"])
    seed = int(inputs["seed"])

    torch.manual_seed(seed)
    q = torch.randn(batch_size, num_heads, k_len, head_dim, dtype=torch.float32)
    k = torch.randn(batch_size, num_heads, k_len, head_dim, dtype=torch.float32)
    v = torch.randn(batch_size, num_heads, k_len, head_dim, dtype=torch.float32)

    attn = _Attention(n_init, n_local, head_dim)
    return mf.gather_last_q_vertical_slash_topk_v4(attn, q, k, v, 0)
