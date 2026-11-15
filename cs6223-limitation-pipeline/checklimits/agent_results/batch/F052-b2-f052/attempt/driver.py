"""Driver for flexprefill-F052: batch_size guard in flex_prefill_attention."""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention


def _randn(batch, seq, heads, dim, seed):
    g = torch.Generator(device="cpu").manual_seed(seed)
    return torch.randn(batch, seq, heads, dim, generator=g)


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    batch = int(inputs["batch_size"])
    q = _randn(batch, 1, 2, 16, 101)
    k = _randn(batch, 1, 2, 16, 202)
    v = _randn(batch, 1, 2, 16, 303)
    return flex_prefill_attention(q, k, v, 0.5)
