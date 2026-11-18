import torch


def check_arange(sim):
    got = sim(8, device="cuda")
    ref = torch.arange(8)
    ok = got.device.type == "cpu" and got.dtype == ref.dtype and torch.equal(got, ref)
    return {
        "ok": bool(ok),
        "detail": f"arange device={got.device.type} equal={torch.equal(got, ref)}",
        "kind": "numeric",
    }


def check_full(sim):
    got = sim((3, 3), -3.5, device="cuda")
    ref = torch.full((3, 3), -3.5)
    ok = got.device.type == "cpu" and got.dtype == ref.dtype and torch.equal(got, ref)
    return {
        "ok": bool(ok),
        "detail": f"full device={got.device.type} equal={torch.equal(got, ref)}",
        "kind": "numeric",
    }
