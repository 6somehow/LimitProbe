"""Checks for the CPU stand-ins in sim.py.  Each check must fail on scaled/negated/zeroed outputs."""
from __future__ import annotations

import math

import torch


def check_arange(sim):
    try:
        got = sim(6, dtype=torch.float32, device="cuda")
        ref = torch.arange(6, dtype=torch.float32)
        got_i = sim(5, device="cuda:0")
        ref_i = torch.arange(5)
        ok = (got.device.type == "cpu" and got_i.device.type == "cpu"
              and torch.allclose(got, ref) and torch.equal(got_i, ref_i))
        return {"ok": bool(ok), "detail": f"float={got.tolist()} int={got_i.tolist()}", "kind": "numeric"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(e).__name__}: {e}", "kind": "numeric"}


def _ref_split(kv_cache, num_kv_heads, head_size):
    key, value = kv_cache[0], kv_cache[1]
    block_size = key.shape[-1] // (num_kv_heads * head_size)
    return (key.reshape(-1, num_kv_heads, block_size, head_size),
            value.reshape(-1, num_kv_heads, block_size, head_size))


def check_split_kv_cache(sim):
    torch.manual_seed(0)
    nkv, hs, blocks, bs = 2, 4, 3, 5
    kv = torch.randn(2, blocks, bs * nkv * hs)
    got = sim(kv, nkv, hs)
    ref = _ref_split(kv, nkv, hs)
    ok = (isinstance(got, tuple) and len(got) == 2
          and all(torch.allclose(a, b) for a, b in zip(got, ref)))
    return {"ok": bool(ok), "detail": f"shapes={[tuple(t.shape) for t in got]}", "kind": "numeric"}


def _ref_write(key, value, key_cache, value_cache, slots):
    bs = key_cache.shape[2]
    for t, slot in enumerate(slots.tolist()):
        block, offset = divmod(int(slot), bs)
        key_cache[block, :, offset, :] = key[t]
        value_cache[block, :, offset, :] = value[t]
    return key_cache.sum() + value_cache.sum()


def check_write_to_paged_cache(sim):
    torch.manual_seed(0)
    ntok, nkv, hs, blocks, bs = 4, 2, 3, 3, 4
    key, value = torch.randn(ntok, nkv, hs), torch.randn(ntok, nkv, hs)
    kc, vc = torch.randn(blocks, nkv, bs, hs), torch.randn(blocks, nkv, bs, hs)
    slots = torch.tensor([0, 5, 7, 11])
    kc1, vc1 = kc.clone(), vc.clone()
    got = sim(key, value, kc1, vc1, slots, "auto", 1.0)
    kc2, vc2 = kc.clone(), vc.clone()
    ref = _ref_write(key, value, kc2, vc2, slots)
    ok = (torch.allclose(kc1, kc2) and torch.allclose(vc1, vc2)
          and torch.allclose(torch.as_tensor(got), torch.as_tensor(ref)))
    return {"ok": bool(ok), "detail": f"cache_sum={float(torch.as_tensor(got)):.4f}", "kind": "numeric"}


def _ref_attention(q, k, v):
    scores = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(q.shape[-1])
    lq, lk = scores.shape[-2], scores.shape[-1]
    mask = torch.tril(torch.ones(lq, lk, dtype=torch.bool), diagonal=lk - lq)
    return torch.matmul(torch.softmax(scores.masked_fill(~mask, float("-inf")), -1), v)


def _check_attention(sim, name):
    torch.manual_seed(0)
    q, k, v = torch.randn(2, 3, 4, 5), torch.randn(2, 3, 6, 5), torch.randn(2, 3, 6, 5)
    got = sim(q, k, v)
    ref = _ref_attention(q, k, v)
    ok = got.shape == ref.shape and torch.allclose(got, ref)
    return {"ok": bool(ok), "detail": f"{name} shape={tuple(got.shape)}", "kind": "numeric"}


def check_block_sparse_attention(sim):
    return _check_attention(sim, "block_sparse")


def check_vertical_slash_sparse_attention(sim):
    return _check_attention(sim, "vertical_and_slash")


def check_streaming_forward(sim):
    return _check_attention(sim, "streaming")
