"""Checks that the CPU stand-ins compute what the GPU pieces compute on small inputs."""

import torch

from sim import arange


def _dense_causal_attention(q, k, v):
    scale = q.shape[-1] ** -0.5
    scores = torch.einsum("bhmd,bhnd->bhmn", q.float(), k.float()) * scale
    n = q.shape[2]
    causal = torch.ones(n, n, dtype=torch.bool).tril()
    scores = scores.masked_fill(~causal, float("-inf"))
    weights = torch.softmax(scores, dim=-1)
    return torch.einsum("bhmn,bhnd->bhmd", weights, v.float())


def check_arange(sim):
    got = sim(64, device="cuda")
    ref = torch.arange(64)
    ok = got.shape == ref.shape and torch.equal(got, ref)
    return {"ok": bool(ok), "detail": f"CPU arange matches torch.arange: {got[:4].tolist()}", "kind": "numeric"}


def check_block_sparse(sim):
    torch.manual_seed(7)
    q = torch.randn(1, 2, 192, 8)
    k = torch.randn(1, 2, 192, 8)
    v = torch.randn(1, 2, 192, 8)
    got = sim(q, k, v, 100)
    ref = _dense_causal_attention(q, k, v)
    ok = torch.allclose(got, ref, atol=1e-4, rtol=1e-4)
    diff = float((got - ref).abs().max())
    return {"ok": bool(ok), "detail": f"192-token block-sparse output equals dense causal attention; max|diff|={diff:.2e}",
            "kind": "numeric"}
