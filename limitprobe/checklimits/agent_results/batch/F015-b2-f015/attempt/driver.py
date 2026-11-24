"""Driver: build q/k/v from `inputs` and call the function that contains the target guard.

The step-4 hand-off builds the call chain as [entry point, target function] without the real
call graph.  The target lives in `triton_vertical_slash_attention`, whose real caller
`vertical_slash_attention` is not part of that synthetic chain and reaches GPU-only code before
the guard.  We therefore call the target function itself (call_chain index 1) and record the
reason in the form.  The repository module is imported at module level; tensors are built on CPU
with a fixed seed and one thread.  No assertions of our own.
"""

import importlib.machinery
import sys

import torch

# `flash_attn` is an optional GPU dependency that is not installed on this CPU host, while the
# module under test imports it unconditionally at load time.  The declared fake module gives the
# import a target; transformers' optional-dependency probe needs a non-None __spec__ before it can
# report the package as unavailable.  Its bound `flash_attn_func` is the declared CPU sim; neither
# is executed before the target line.
_flash = sys.modules.get("flash_attn")
if _flash is not None and getattr(_flash, "__spec__", None) is None:
    _flash.__spec__ = importlib.machinery.ModuleSpec("flash_attn", None)
    _flash.__path__ = []

import flex_prefill.ops.vertical_slash_attention as _vsa

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def run(inputs):
    seed = int(inputs["seed"])
    torch.manual_seed(seed)
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    block_size = int(inputs["block_size"])
    dtype = _DTYPES[inputs["dtype"]]

    q = torch.zeros(batch_size, q_len, num_q_heads, head_dim, dtype=dtype)
    k = torch.zeros(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)
    v = torch.zeros(batch_size, k_len, num_kv_heads, head_dim, dtype=dtype)

    vertical_index = torch.zeros(batch_size, num_q_heads, 1, dtype=torch.int64)
    slash_index = torch.zeros(batch_size, num_q_heads, 1, dtype=torch.int64)

    return _vsa.triton_vertical_slash_attention(
        q, k, v, block_size, vertical_index, slash_index
    )
