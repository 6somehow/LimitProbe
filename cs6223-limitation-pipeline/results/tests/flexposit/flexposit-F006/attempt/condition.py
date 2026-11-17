"""Decision condition for the Region: a raise guarded by `x.dtype != torch.float32`."""

import torch


def predicate(locals):
    x = locals.get("x")
    return getattr(x, "dtype", None) != torch.float32
