"""Independent numeric check for sim.mha_gen (dense decoding attention)."""

import numpy as np
import torch

import _clpaths

_clpaths.ensure()

from flexgen.pytorch_backend import TorchDevice, TorchTensor  # noqa: E402


def _reference(inputs, w_q, w_k, w_v, b_v, w_out, b_out, w_ln, b_ln,
               n_head, k_cache, v_cache):
    b, tgt_s, h = inputs.shape
    src_s = k_cache.shape[0] + 1
    head_dim = h // n_head

    mu = inputs.mean(axis=-1, keepdims=True)
    var = inputs.var(axis=-1, keepdims=True)
    hidden = (inputs - mu) / np.sqrt(var + 1e-5) * w_ln + b_ln
    new_h = np.concatenate([hidden, np.ones((b, tgt_s, 1))], axis=-1)

    q = new_h @ w_q.T
    k = new_h @ w_k.T
    v = hidden @ w_v.T + b_v

    q = q.reshape(b, tgt_s, n_head, head_dim).transpose(0, 2, 1, 3)
    q = q.reshape(b * n_head, tgt_s, head_dim)
    k_new = k.reshape(b, tgt_s, n_head, head_dim).transpose(1, 0, 2, 3)
    k_new = k_new.reshape(tgt_s, b * n_head, head_dim)
    v_new = v.reshape(b, tgt_s, n_head, head_dim).transpose(1, 0, 2, 3)
    v_new = v_new.reshape(tgt_s, b * n_head, head_dim)

    k_all = np.concatenate([k_cache[:src_s - 1], k_new], axis=0)
    v_all = np.concatenate([v_cache[:src_s - 1], v_new], axis=0)

    k_mat = k_all.transpose(1, 2, 0).reshape(b * n_head, head_dim, -1)
    v_mat = v_all.transpose(1, 0, 2).reshape(b * n_head, -1, head_dim)

    scores = q @ k_mat
    scores = scores - scores.max(axis=-1, keepdims=True)
    attn = np.exp(scores)
    attn = attn / attn.sum(axis=-1, keepdims=True)
    value = (attn @ v_mat).reshape(b, n_head, tgt_s, head_dim)
    value = value.transpose(0, 2, 1, 3).reshape(b, tgt_s, h)
    value = value @ w_out.T + b_out
    return value + inputs, k_new, v_new


def check_mha_gen(sim):
    rng = np.random.default_rng(7)
    dev = TorchDevice("cpu")
    b, tgt_s, h, n_head = 1, 1, 4, 2
    head_dim = h // n_head
    src_s = 3

    def arr(*shape):
        return rng.standard_normal(shape).astype(np.float32)

    inputs_np = arr(b, tgt_s, h)
    w_q_np = arr(h, h + 1)
    w_k_np = arr(h, h + 1)
    w_v_np = arr(h, h)
    b_v_np = arr(h)
    w_out_np = arr(h, h)
    b_out_np = arr(h)
    w_ln_np = arr(h)
    b_ln_np = arr(h)
    k_cache_np = arr(src_s - 1, b * n_head, head_dim)
    v_cache_np = arr(src_s - 1, b * n_head, head_dim)

    def tt(x):
        return TorchTensor.create_from_torch(torch.from_numpy(np.ascontiguousarray(x)), dev)

    try:
        got = sim(tt(inputs_np), tt(np.ones((b, src_s), dtype=bool)),
                  tt(w_q_np), tt(b_v_np), tt(w_k_np), tt(b_v_np),
                  tt(w_v_np), tt(b_v_np), tt(w_out_np), tt(b_out_np),
                  tt(w_ln_np), tt(b_ln_np), n_head,
                  tt(k_cache_np), tt(v_cache_np), (False, False),
                  1.0, False, None, None, None, None, 0.0, 0)
    except Exception as exc:
        return {"ok": False, "detail": f"sim raised {type(exc).__name__}: {exc}", "kind": "numeric"}

    want = _reference(inputs_np, w_q_np, w_k_np, w_v_np, b_v_np, w_out_np,
                      b_out_np, w_ln_np, b_ln_np, n_head, k_cache_np, v_cache_np)
    names = ("value", "k_new", "v_new")
    for i, name in enumerate(names):
        try:
            g = got[i].data.detach().cpu().numpy()
        except Exception as exc:
            return {"ok": False, "detail": f"{name} is not tensor-like: {exc}", "kind": "numeric"}
        if g.shape != want[i].shape:
            return {"ok": False, "detail": f"{name} shape {g.shape} != {want[i].shape}", "kind": "numeric"}
        err = float(np.max(np.abs(g - want[i])))
        if not np.isfinite(err) or err > 1e-4:
            return {"ok": False, "detail": f"{name} max abs error {err:.3e}", "kind": "numeric"}
    return {"ok": True, "detail": "dense decoding attention matches reference within 1e-4", "kind": "numeric"}
