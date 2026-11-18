"""CPU stand-ins for the GPU-only pieces needed by finding minference-F038.

Two stand-ins are declared in form.json:

* torch.arange (patch, sim): the repository's ``minference/modules/minference_forward.py``
  builds a module-level constant with ``torch.arange(..., device="cuda")``.  This is a
  device shim: it forwards every call to the real torch.arange and only rewrites a
  ``cuda`` device to ``cpu`` so the real module can be imported on a CPU-only host.

* minference.ops.streaming_kernel._forward (patch, sim): the Triton flash-attention
  launcher.  ``forward_cpu`` is a plain-torch implementation of the same multi-stage
  sliding-window attention (base-2 online softmax), so the real ``streaming_forward``
  branch bodies can run on CPU.

Import-time stubs (flash_attn, pycuda, minference.cuda, minference.models_patch,
minference.patch) are installed as a side effect of loading this file; those are missing
GPU / incompatible optional dependencies of the package, not code on the call chain.
"""
import importlib.machinery
import math
import sys
import types

import torch

_REAL_ARANGE = getattr(torch, "_cl_real_arange", torch.arange)
torch._cl_real_arange = _REAL_ARANGE


def _install_stub(name, version=None):
    cur = sys.modules.get(name)
    if cur is not None and getattr(cur, "_cl_stub", False):
        return cur
    m = types.ModuleType(name)
    m.__spec__ = importlib.machinery.ModuleSpec(name, None, is_package=True)
    m.__path__ = []
    m._cl_stub = True
    if version is not None:
        m.__version__ = version

    def _ga(n, _m=m):
        if n.startswith("__"):
            raise AttributeError(n)

        def f(*a, **k):
            return None

        setattr(_m, n, f)
        return f

    m.__getattr__ = _ga
    sys.modules[name] = m
    return m


def _install_gpu_stubs():
    _install_stub("flash_attn", version="2.5.0")
    _install_stub("pycuda")
    _install_stub("pycuda.autoprimaryctx")
    _install_stub("pycuda.compiler")
    _install_stub("minference.cuda")
    _install_stub("minference.models_patch")
    _install_stub("minference.patch")


_install_gpu_stubs()


def arange_cpu(*args, **kwargs):
    dev = kwargs.get("device")
    if dev is not None and "cuda" in str(dev):
        kwargs["device"] = "cpu"
    return _REAL_ARANGE(*args, **kwargs)


def _window_mask(idx_q, idx_k, offset, size, complement):
    dist = idx_q[:, None] - idx_k[None, :] + offset
    if complement:
        return dist >= size
    return (dist >= 0) & (dist < size)


def forward_cpu(q, k, v, sm_scale, o=None, m=None, l=None, end=False,
                sliding_window=None, init=False, complement_sliding_window=False):
    """Plain-torch equivalent of the Triton ``_forward`` (base-2 online softmax).

    Mirrors ``minference/ops/streaming_kernel.py``: ``o``/``m``/``l`` are running
    accumulators between stages, the mask is ``dist = i - j + offset`` with
    ``0 <= dist < size`` (or ``dist >= size`` for the complement stage), and ``end``
    normalizes the accumulator.
    """
    B, H, Lq, D = q.shape
    Hk = k.shape[1]
    Lk = k.shape[2]
    round_len = m.shape[-1] if m is not None else math.ceil(Lq / 64) * 64

    rep = H // Hk
    kk = k.repeat_interleave(rep, dim=1) if rep > 1 else k
    vv = v.repeat_interleave(rep, dim=1) if rep > 1 else v

    log2e = 1.4426950408889634
    qf = q.to(torch.float32)
    kf = kk.to(torch.float32)
    vf = vv.to(torch.float32)
    logits = torch.matmul(qf, kf.transpose(-1, -2)) * (sm_scale * log2e)

    mask = None
    if sliding_window is not None:
        offset, size = sliding_window
        iq = torch.arange(Lq, device=q.device)
        ik = torch.arange(Lk, device=q.device)
        mask = _window_mask(iq, ik, offset, size, complement_sliding_window)
        logits = logits.masked_fill(~mask[None, None], float("-inf"))

    if init:
        m_prev = torch.full((B, H, Lq), float("-inf"), dtype=torch.float32, device=q.device)
        l_prev = torch.ones((B, H, Lq), dtype=torch.float32, device=q.device)
        acc = torch.zeros((B, H, Lq, D), dtype=torch.float32, device=q.device)
    else:
        m_prev = m[:, :, :Lq].to(torch.float32)
        l_prev = l[:, :, :Lq].to(torch.float32)
        acc = o[:, :, :Lq, :].to(torch.float32)

    m_new = torch.maximum(m_prev, logits.max(dim=-1).values)
    m_safe = torch.where(torch.isfinite(m_new), m_new, torch.zeros_like(m_new))
    p = torch.exp2(logits - m_safe[..., None])
    if mask is not None:
        p = p.masked_fill(~mask[None, None], 0.0)
    p = torch.where(torch.isfinite(logits), p, torch.zeros_like(p))

    tmp = m_prev - m_safe
    alpha = torch.where(torch.isnan(tmp), torch.ones_like(tmp), torch.exp2(tmp))
    alpha = torch.where(torch.isfinite(alpha), alpha, torch.zeros_like(alpha))

    l_new = l_prev * alpha + p.sum(dim=-1)
    acc = acc * alpha[..., None] + torch.matmul(p, vf)

    if end:
        out = acc / l_new[..., None]
        return out.to(q.dtype), m_new, l_new

    o_full = torch.zeros((B, H, round_len, D), dtype=torch.float32, device=q.device)
    m_full = torch.zeros((B, H, round_len), dtype=torch.float32, device=q.device)
    l_full = torch.zeros((B, H, round_len), dtype=torch.float32, device=q.device)
    o_full[:, :, :Lq, :] = acc
    m_full[:, :, :Lq] = m_new
    l_full[:, :, :Lq] = l_new
    return o_full, m_full, l_full


def reference_streaming(q, k, v, n_init, n_local):
    """Closed-form reference for the two-stage streaming call made by ``streaming_forward``.

    Query i attends to the local window {i-n_local+1..i} and, when ``k_len > n_local``,
    also to the ``n_init`` sink keys at the front.
    """
    B, H, Lq, D = q.shape
    Lk = k.shape[2]
    sm_scale = 1.0 / math.sqrt(D)
    iq = torch.arange(Lq, device=q.device)
    ik = torch.arange(Lk, device=q.device)
    local = (iq[:, None] - ik[None, :] >= 0) & (iq[:, None] - ik[None, :] < n_local)
    if Lk > n_local:
        sinks = ik[None, :] < n_init
        mask = local | sinks
    else:
        mask = local
    qf = q.to(torch.float32)
    kf = k.to(torch.float32)
    vf = v.to(torch.float32)
    logits = torch.matmul(qf, kf.transpose(-1, -2)) * sm_scale
    logits = logits.masked_fill(~mask[None, None], float("-inf"))
    p = torch.softmax(logits, dim=-1)
    return torch.matmul(p, vf).to(q.dtype)


def check_arange(sim):
    """The device shim must still return the same values as torch.arange, on CPU."""
    got = sim(0, 5, dtype=torch.float32, device="cuda")
    ref = torch.arange(0, 5, dtype=torch.float32)
    ok = got.device.type == "cpu" and got.shape == ref.shape and torch.equal(got, ref)
    return {"ok": ok, "detail": f"device={got.device}, values={got.tolist()}", "kind": "numeric"}


def check_forward(sim):
    """Numeric check: the stand-in reproduces the streaming attention reference."""
    torch.manual_seed(1234)
    ok_all = True
    detail = []
    for (Lq, Lk, n_init, n_local) in [(3, 3, 1, 1), (4, 4, 1, 2), (2, 2, 1, 1)]:
        q = torch.randn(1, 2, Lq, 16)
        k = torch.randn(1, 2, Lk, 16)
        v = torch.randn(1, 2, Lk, 16)
        sm_scale = 1.0 / math.sqrt(16)
        if Lk > n_local:
            o, m, l = sim(q, k, v, sm_scale, init=True, sliding_window=(0, n_local))
            o2, _, _ = sim(q, k[:, :, :n_init, :], v[:, :, :n_init, :], sm_scale, o, m, l,
                           end=True, sliding_window=(Lk - Lq, n_local),
                           complement_sliding_window=True)
            got = o2
        else:
            got, _, _ = sim(q, k, v, sm_scale, end=True, init=True, sliding_window=(0, n_local))
        ref = reference_streaming(q, k, v, n_init, n_local)
        diff = (got.to(torch.float64) - ref.to(torch.float64)).abs().max().item()
        detail.append(f"L={Lq}/{Lk},n_local={n_local}: max|diff|={diff:.2e}")
        if not (diff < 1e-5):
            ok_all = False
    return {"ok": ok_all, "detail": "; ".join(detail), "kind": "numeric"}
