"""Driver for minference-F012.

The official entry `gather_last_q_vertical_slash_topk_v4` is taken from the repository source with
`ast.get_source_segment` and compiled under the real file name. Importing
`minference.modules.minference_forward` would pull in GPU-only modules
(`block_sparse_flash_attention`, `streaming_kernel`, pycuda) at module level, which are unrelated to
the target and would have to be stubbed before the target runs. The executed statements are
byte-for-byte the repository's.

The package names are registered as namespace shims so the target module
`minference/ops/pit_sparse_flash_attention_v2.py` can be imported normally. The compiled CUDA
extension `minference.cuda` is supplied by the harness as a declared fake module plus a CPU port of
`convert_vertical_slash_indexes` (see form.json); it runs before the target, so it is an explicit
stand-in rather than a hidden one.

`LAST_Q_MASK` is a module-level constant in minference_forward.py built with
`torch.arange(64, device="cuda")`. We build the same boolean mask on CPU here because the module
itself is not imported; it is data, not code under test.
"""

import ast
import math
import sys
import types
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

REPO = Path(sys.path[0]).resolve()
TARGET_MF = REPO / "minference/modules/minference_forward.py"


def _package(name, path):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod
    return sys.modules[name]


_package("minference", REPO / "minference")
_package("minference.modules", REPO / "minference/modules")
_package("minference.ops", REPO / "minference/ops")

import minference.ops.pit_sparse_flash_attention_v2 as _pit  # noqa: E402


def _unused(*args, **kwargs):
    raise RuntimeError("branch is not taken by this driver")


_LAST_Q = 64
_LAST_Q_MASK = torch.arange(_LAST_Q)[None, None, :, None] >= torch.arange(_LAST_Q)[None, None, None, :]


def _load_entry():
    src = TARGET_MF.read_text()
    tree = ast.parse(src)
    nodes = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    namespace = {
        "torch": torch,
        "nn": nn,
        "F": F,
        "math": math,
        "LAST_Q_MASK": _LAST_Q_MASK,
        "vertical_slash_sparse_attention": _pit.vertical_slash_sparse_attention,
        "streaming_forward": _unused,
        "flash_attn_func": _unused,
        "block_sparse_attention": _unused,
    }
    for name in ("sum_all_diagonal_matrix", "gather_last_q_vertical_slash_topk_v4"):
        segment = ast.get_source_segment(src, nodes[name])
        exec(compile(segment, str(TARGET_MF), "exec"), namespace)
    return namespace["gather_last_q_vertical_slash_topk_v4"]


_entry = _load_entry()


class _Config:
    def to_dict(self):
        return {"dilated1": True}


class _Self:
    head_dim = 256
    ne_inf = torch.finfo(torch.float32).min
    kv_cache_compressed_v4 = False
    config = _Config()
    best_pattern = {0: ("vertical_and_slash", 30, 50, 1)}


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    lq = int(inputs["Lq"])
    lk = int(inputs["Lk"])
    lv = int(inputs["Lv"])
    batch, heads, q_len = 1, 1, 64
    q = torch.randn(batch, heads, q_len, lq, dtype=torch.float32)
    k = torch.randn(batch, heads, q_len, lk, dtype=torch.float32)
    v = torch.randn(batch, heads, q_len, lv, dtype=torch.float32)
    return _entry(_Self(), q, k, v, 0)
