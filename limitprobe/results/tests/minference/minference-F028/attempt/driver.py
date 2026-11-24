"""Driver for minference-F028.

The pinned repository imports a compiled GPU extension that is not built in this CPU
environment, so the module cannot be imported.  Instead this driver loads the exact
source of the target function (and the helper it calls) from the repository at run time with
`ast`, preserving the original line numbers so the harness trace points at the real file.  The
GPU-only sparse-attention kernel is replaced by a function that raises; it is called only after
the target decision, so it cannot affect the branch the harness observes.
"""

import ast
import math
import sys
from pathlib import Path

import torch
import torch.nn as nn

REPO = Path(sys.path[0]).resolve()
TARGET = REPO / "minference/modules/minference_forward.py"

_FUNCTIONS = ("sum_all_diagonal_matrix", "gather_last_q_vertical_slash_topk_v4")


def _make_gpu_kernel_unavailable():
    source = (
        "def _gpu_kernel_unavailable(*args, **kwargs):\n"
        "    raise RuntimeError('GPU sparse attention kernel is not available on CPU')\n"
    )
    namespace = {}
    exec(compile(source, str(TARGET), "exec"), namespace)
    return namespace["_gpu_kernel_unavailable"]


_gpu_kernel_unavailable = _make_gpu_kernel_unavailable()


def _load_functions():
    source = TARGET.read_text()
    tree = ast.parse(source)
    nodes = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    namespace = {
        "torch": torch,
        "nn": nn,
        "math": math,
        "LAST_Q_MASK": torch.arange(64)[None, None, :, None] >= torch.arange(64)[None, None, None, :],
        "vertical_slash_sparse_attention": _gpu_kernel_unavailable,
        "streaming_forward": _gpu_kernel_unavailable,
        "block_sparse_attention": _gpu_kernel_unavailable,
        "flash_attn_func": _gpu_kernel_unavailable,
    }
    for name in _FUNCTIONS:
        node = nodes[name]
        segment = ast.get_source_segment(source, node)
        padded = "\n" * (node.lineno - 1) + segment
        exec(compile(padded, str(TARGET), "exec"), namespace)
    return namespace["gather_last_q_vertical_slash_topk_v4"]


_entry = _load_functions()


class _Config:
    def __init__(self, values):
        self._values = values

    def to_dict(self):
        return dict(self._values)


class _Attention:
    def __init__(self, inputs):
        self.config = _Config({"static_pattern": int(inputs["static_pattern"])})
        self.head_dim = int(inputs["head_dim"])
        self.ne_inf = torch.finfo(_dtype(inputs)).min
        self.best_pattern = dict(inputs["best_pattern"])
        self.kv_cache_compressed_v4 = bool(inputs["kv_cache_compressed_v4"])


def _dtype(inputs):
    return {"float32": torch.float32, "float64": torch.float64}[str(inputs["dtype"])]


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    q_len = int(inputs["q_len"])
    bsz = int(inputs["bsz"])
    heads = int(inputs["num_heads"])
    head_dim = int(inputs["head_dim"])
    dtype = _dtype(inputs)
    attention = _Attention(inputs)
    q = torch.randn(bsz, heads, q_len, head_dim, dtype=dtype)
    k = torch.randn(bsz, heads, q_len, head_dim, dtype=dtype)
    v = torch.randn(bsz, heads, q_len, head_dim, dtype=dtype)
    return _entry(attention, q, k, v, int(inputs["head_id"]))
