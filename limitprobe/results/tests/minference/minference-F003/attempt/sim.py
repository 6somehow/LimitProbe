import torch as _torch

_orig_arange = _torch.arange
_orig_full = _torch.full


def cpu_arange(*args, **kwargs):
    kwargs["device"] = "cpu"
    return _orig_arange(*args, **kwargs)


def cpu_full(*args, **kwargs):
    kwargs["device"] = "cpu"
    return _orig_full(*args, **kwargs)
