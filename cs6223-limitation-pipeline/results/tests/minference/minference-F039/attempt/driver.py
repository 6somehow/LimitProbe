"""Driver for minference-F039.

The target is the `forward` closure returned by `stream_llm_forward(n_local, n_init)` in
minference/ops/streaming_kernel.py.  The step-4 static analysis reports `call_chain_status:
not_found` for the declared entry (`gather_last_q_vertical_slash_topk_v4` never calls this
closure), so the driver loads the target file and calls the closure directly; the reason is
recorded in execution.entry_reason.

Only the inputs `len_k`, `n_local`, `n_init`, `use_cache` decide the target branch.  The tensors
are built from `torch.arange` (no RNG), CPU only, one thread.  Everything below the target line
(the GPU Triton kernel) is left untouched: on this CPU-only machine it raises in triton after the
branch has already been decided, which is why no stand-in is needed and the observations do not
depend on one.
"""

import importlib.util
import sys
from pathlib import Path

import torch


def _load_streaming_kernel():
    for entry in sys.path:
        candidate = Path(entry) / "minference" / "ops" / "streaming_kernel.py"
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location("_f039_streaming_kernel", candidate)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("minference/ops/streaming_kernel.py not found on sys.path")


_SK = _load_streaming_kernel()
_STREAM_LLM_FORWARD = _SK.stream_llm_forward


class _PositionBias:
    """The caller-supplied rotary-embedding argument.  It is only touched after the target line."""

    _cos_cached = None
    _sin_cached = None

    def __call__(self, h_q, h_k):
        return h_q, h_k

    def apply_rotary_pos_emb_one_angle(self, x, angle):
        return x

    def apply_rotary_pos_emb(self, x, a, b, cos, sin):
        return x


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    len_q = int(inputs["len_q"])
    len_k = int(inputs["len_k"])
    n_local = int(inputs["n_local"])
    n_init = int(inputs["n_init"])
    num_heads = int(inputs["num_heads"])
    num_heads_kv = int(inputs["num_heads_kv"])
    dim_head = int(inputs["dim_head"])
    use_cache = bool(inputs["use_cache"])

    hidden_q = torch.arange(batch_size * len_q * num_heads * dim_head, dtype=torch.float32)
    hidden_q = hidden_q.reshape(batch_size, len_q, num_heads * dim_head) / 1000.0
    hidden_kv = torch.arange(batch_size * len_k * num_heads_kv * dim_head, dtype=torch.float32)
    hidden_kv = hidden_kv.reshape(batch_size, len_k, num_heads_kv * dim_head) / 1000.0

    project_q = torch.nn.Identity()
    project_k = torch.nn.Identity()
    project_v = torch.nn.Identity()
    attention_out = torch.nn.Identity()

    forward = _STREAM_LLM_FORWARD(n_local, n_init)
    return forward(
        None,
        hidden_q,
        hidden_kv,
        _PositionBias(),
        use_cache,
        None,
        project_q,
        project_k,
        project_v,
        attention_out,
        dim_head,
        num_heads,
        num_heads_kv,
    )
