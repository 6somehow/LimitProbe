"""Numeric check for the torch.arange device stand-in."""

import torch


def check_arange(sim):
    ref_float = torch.arange(0, 7, dtype=torch.float32)
    got_float = sim(0, 7, dtype=torch.float32, device="cuda")
    ref_int = torch.arange(3, 10, dtype=torch.int64)
    got_int = sim(3, 10, dtype=torch.int64)
    ok = (
        torch.equal(got_float, ref_float)
        and got_float.device.type == "cpu"
        and torch.equal(got_int, ref_int)
    )
    return {
        "ok": bool(ok),
        "detail": "cpu_arange matches torch.arange on a CPU reference and redirects a cuda device to cpu",
        "kind": "numeric",
    }
