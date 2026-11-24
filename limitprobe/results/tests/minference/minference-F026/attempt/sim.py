"""CPU stand-in for the module-level `torch.arange(..., device="cuda")` constant.

minference_forward.py builds LAST_Q_MASK with a CUDA arange when it is imported.
On this CPU-only machine that call aborts the import.  The constant is only read
by the sparse kernels below the target line, so a CPU tensor of the same values
is a faithful replacement for anything the test reaches.
"""

import torch

_ORIG_ARANGE = torch.arange


def arange(*args, **kwargs):
    kw = dict(kwargs)
    device = kw.get("device")
    if device == "cuda" or getattr(device, "type", None) == "cuda":
        kw["device"] = "cpu"
    return _ORIG_ARANGE(*args, **kw)
