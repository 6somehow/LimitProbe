"""CPU stand-ins for the GPU-only parts of the MInference vLLM forward.

The target module imports three Triton/CUDA attention kernels at import time and builds
`torch.arange(..., device="cuda")`.  None of those kernels runs before the checked branch
decision.  The synthetic `minference.ops.*` modules below only satisfy those imports; each
symbol is declared as a `patch` mock in form.json and replaced by the harness after this file
is loaded.  The PagedAttention cache helpers run before the target on the negative input, so
they are real CPU implementations (and are checked in check.py).
"""
from __future__ import annotations

import importlib
import math
import sys
import types
from pathlib import Path

import torch

_ORIG_ARANGE = torch.arange


def arange(*args, **kwargs):
    """`torch.arange` with a CUDA device mapped to CPU (the module-level mask is data-independent)."""
    device = kwargs.get("device")
    if device is not None and str(device).startswith("cuda"):
        kwargs["device"] = "cpu"
    return _ORIG_ARANGE(*args, **kwargs)


def _reference_attention(q, k, v):
    scores = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(q.shape[-1])
    lq, lk = scores.shape[-2], scores.shape[-1]
    mask = torch.tril(torch.ones(lq, lk, dtype=torch.bool), diagonal=lk - lq)
    scores = scores.masked_fill(~mask, float("-inf"))
    return torch.matmul(torch.softmax(scores, -1), v)


def block_sparse_attention(q, k, v, topk=100):
    return _reference_attention(q, k, v)


def vertical_slash_sparse_attention(q, k, v, vertical_topk=None, slash=None):
    return _reference_attention(q, k, v)


def streaming_forward(q, k, v, *args, **kwargs):
    return _reference_attention(q, k, v)


def streaming_forward2(q, k, v, *args, **kwargs):
    return _reference_attention(q, k, v)


def split_kv_cache(kv_cache, num_kv_heads, head_size):
    key_cache = kv_cache[0]
    value_cache = kv_cache[1]
    block_size = key_cache.shape[-1] // (num_kv_heads * head_size)
    return (key_cache.reshape(-1, num_kv_heads, block_size, head_size),
            value_cache.reshape(-1, num_kv_heads, block_size, head_size))


def write_to_paged_cache(key, value, key_cache, value_cache, slot_mapping,
                         kv_cache_dtype=None, k_scale=1.0):
    block_size = key_cache.shape[2]
    slots = slot_mapping.to(dtype=torch.long).reshape(-1)
    for t in range(key.shape[0]):
        block, offset = divmod(int(slots[t]), block_size)
        key_cache[block, :, offset, :] = key[t]
        value_cache[block, :, offset, :] = value[t]
    return key_cache.sum() + value_cache.sum()


class PagedAttention:
    @staticmethod
    def split_kv_cache(kv_cache, num_kv_heads, head_size):
        return split_kv_cache(kv_cache, num_kv_heads, head_size)

    @staticmethod
    def write_to_paged_cache(key, value, key_cache, value_cache, slot_mapping,
                             kv_cache_dtype=None, k_scale=1.0):
        return write_to_paged_cache(key, value, key_cache, value_cache, slot_mapping,
                                    kv_cache_dtype, k_scale)

    @staticmethod
    def forward_prefix(query, *args, **kwargs):
        return query

    @staticmethod
    def forward_decode(query, *args, **kwargs):
        return query


def _repo_root():
    for entry in sys.path:
        base = Path(entry).resolve()
        for repo in (base, base / "third_party" / "MInference"):
            if (repo / "minference" / "modules" / "minference_forward.py").exists():
                return repo
    here = Path(__file__).resolve()
    for parent in here.parents:
        repo = parent / "third_party" / "MInference"
        if (repo / "minference" / "modules" / "minference_forward.py").exists():
            return repo
    raise RuntimeError("cannot locate the MInference repository from sys.path or the attempt directory")


def _install_packages(repo):
    pkg = types.ModuleType("minference")
    pkg.__path__ = [str(repo / "minference")]
    modules = types.ModuleType("minference.modules")
    modules.__path__ = [str(repo / "minference" / "modules")]
    ops = types.ModuleType("minference.ops")
    ops.__path__ = [str(repo / "minference" / "ops")]
    b = types.ModuleType("minference.ops.block_sparse_flash_attention")
    b.block_sparse_attention = block_sparse_attention
    p = types.ModuleType("minference.ops.pit_sparse_flash_attention_v2")
    p.vertical_slash_sparse_attention = vertical_slash_sparse_attention
    s = types.ModuleType("minference.ops.streaming_kernel")
    s.streaming_forward = streaming_forward
    s.streaming_forward2 = streaming_forward2
    for mod in (pkg, modules, ops, b, p, s):
        sys.modules[mod.__name__] = mod


def _prepare_target():
    name = "minference.modules.minference_forward"
    cached = sys.modules.get(name)
    if cached is not None and getattr(cached, "_checklimits_ready", False):
        return cached
    _install_packages(_repo_root())
    saved = torch.arange
    torch.arange = arange
    try:
        module = importlib.import_module(name)
    finally:
        torch.arange = saved
    module.PagedAttention = PagedAttention
    module._checklimits_ready = True
    return module


_prepare_target()
