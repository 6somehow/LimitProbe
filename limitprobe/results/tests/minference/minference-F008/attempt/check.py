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
