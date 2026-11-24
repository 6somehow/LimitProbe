"""CPU stand-ins for the two GPU-only pieces the target module needs.

`torch.arange(..., device="cuda")` runs at import time (the module builds LAST_Q_MASK on the
GPU).  The harness machine has no CUDA, so we keep the real arange (stored on the torch module
before the harness replaces it) and map the device to CPU.

`vertical_slash_sparse_attention` is a Triton kernel launcher from minference.ops.  It runs
after the target decision; a plain-torch dense causal attention keeps the checked call
completing on CPU.
"""
import math

import torch

if "_checklimits_real_arange" not in torch.__dict__:
    _cur = torch.arange
    if not hasattr(_cur, "_fn"):  # not already a harness RecordingCallable
        torch.__dict__["_checklimits_real_arange"] = _cur

_real_arange = torch.__dict__["_checklimits_real_arange"]


def arange_cpu(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and str(device).startswith("cuda"):
        kwargs["device"] = "cpu"
    return _real_arange(*args, **kwargs)


def vertical_slash_sparse_attention(q, k, v, vertical_topk=None, slash=None, *args, **kwargs):
    scale = 1.0 / math.sqrt(q.shape[-1])
    scores = torch.matmul(q, k.transpose(-1, -2)) * scale
    q_len, kv_len = q.shape[-2], k.shape[-2]
    if q_len == kv_len:
        causal = torch.triu(torch.ones(q_len, kv_len, dtype=torch.bool, device=scores.device), diagonal=1)
        scores = scores.masked_fill(causal, float("-inf"))
    probs = torch.softmax(scores, dim=-1, dtype=torch.float32).to(v.dtype)
    return torch.matmul(probs, v)
