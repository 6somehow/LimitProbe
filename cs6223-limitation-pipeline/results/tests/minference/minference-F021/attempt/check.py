"""Independent check for the torch.arange CPU stand-in: same values as torch.arange on CPU."""

import torch


def check(impl):
    cases = [
        ((), {"end": 8}),
        ((3,), {}),
        ((2, 9, 2), {}),
        ((0, 5, 1), {"dtype": torch.float32, "device": "cuda"}),
        ((4,), {"dtype": torch.float32, "device": "cuda"}),
    ]
    for args, kwargs in cases:
        ref_kwargs = dict(kwargs)
        if "device" in ref_kwargs:
            ref_kwargs["device"] = "cpu"
        expected = torch.arange(*args, **ref_kwargs)
        got = impl(*args, **kwargs)
        if not torch.equal(got, expected):
            return {"ok": False, "detail": f"arange{args} {kwargs} -> {got}, expected {expected}", "kind": "numeric"}
    return {"ok": True, "detail": "matches torch.arange on CPU for int and float dtypes", "kind": "numeric"}
