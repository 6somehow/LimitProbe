import torch as _torch

_orig_arange = _torch.arange


def cpu_arange(*args, **kwargs):
    kwargs["device"] = "cpu"
    return _orig_arange(*args, **kwargs)
