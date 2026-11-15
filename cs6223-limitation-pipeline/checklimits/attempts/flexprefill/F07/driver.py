"""F07 driver: call the official entry flex_prefill_attention with random bf16 tensors.

Imports are at module level on purpose: the harness loads this file before it starts the
tracer, so import cost and import-time side effects stay outside the trace.
No assertions here; the harness judges from the trace and the exception.
"""
import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention

_DTYPES = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}


def run(inputs):
    g = torch.Generator().manual_seed(int(inputs.get("seed", 0)))
    dtype = _DTYPES[inputs.get("dtype", "bfloat16")]
    b, q_len = inputs["batch_size"], inputs["q_len"]
    k_len = inputs.get("k_len", q_len)
    h, d = inputs["num_heads"], inputs["head_dim"]
    q = torch.randn(b, q_len, h, d, generator=g).to(dtype)
    k = torch.randn(b, k_len, h, d, generator=g).to(dtype)
    v = torch.randn(b, k_len, h, d, generator=g).to(dtype)
    return flex_prefill_attention(q, k, v, gamma=inputs["gamma"], tau=inputs["tau"],
                                  block_size=inputs.get("block_size", 128))
