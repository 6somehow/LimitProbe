"""CPU stand-ins for the missing GPU device used while the repository modules import.

`torch.arange(..., device="cuda")` at module import builds LAST_Q_MASK.  The mask is not
read before the target decision; the stand-in only redirects the device to the CPU and
forwards every other argument to the real torch.arange.
"""

import torch

_ORIG_ARANGE = torch.arange


def cpu_arange(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and str(device).startswith("cuda"):
        kwargs["device"] = "cpu"
    return _ORIG_ARANGE(*args, **kwargs)
