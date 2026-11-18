"""Checks for the CPU stand-ins declared in form.json."""

import torch


def check_cpu_arange(sim):
    """The stand-in must reproduce torch.arange, including float outputs."""
    for args, kwargs in (
        ((7,), {"dtype": torch.float32}),
        ((3, 11, 2), {"dtype": torch.float32}),
        ((5,), {"device": "cuda", "dtype": torch.float32}),
    ):
        got = sim(*args, **kwargs)
        want = torch.arange(*args, **{**kwargs, "device": "cpu"})
        if got.device.type != "cpu":
            return {"ok": False, "detail": f"device {got.device} is not cpu", "kind": "numeric"}
        if not torch.equal(got, want):
            return {
                "ok": False,
                "detail": f"arange{args}{kwargs} produced {got.tolist()} != {want.tolist()}",
                "kind": "numeric",
            }
    return {"ok": True, "detail": "matches torch.arange on cpu for int and float dtypes", "kind": "numeric"}
