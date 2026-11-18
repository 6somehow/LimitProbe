"""Check that the arange stand-in computes what torch.arange computes on CPU."""

import torch


def check_arange(sim):
    ref = torch.arange(0.0, 5.0)
    got = sim(0.0, 5.0)
    ok = bool(torch.equal(got, ref) and got.device.type == "cpu")
    forced = sim(0.0, 4.0, device="cuda")
    ok = ok and bool(torch.equal(forced, torch.arange(0.0, 4.0)) and forced.device.type == "cpu")
    return {
        "ok": ok,
        "detail": f"values={got.tolist()} device={got.device.type} cuda_requested_device={forced.device.type}",
        "kind": "numeric",
    }
