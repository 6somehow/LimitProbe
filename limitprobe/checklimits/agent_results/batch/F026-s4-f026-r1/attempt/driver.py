"""Driver: call the official entry with the inputs the harness passes in.

Rules: import the code under test at module level (the harness loads this file before it starts
tracing); build tensors / objects from `inputs` only; set seeds; CPU only; no assertions of your own
(the harness decides from the trace and the exception); do not catch the exception you are
looking for; do not write into the repository.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention

NUM_HEADS = 1
GAMMA = 0.9
TAU = 0.0


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = q_len
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])
    min_budget = inputs.get("min_budget", None)
    if min_budget is not None:
        min_budget = int(min_budget)

    q = torch.randn(batch_size, q_len, NUM_HEADS, head_dim)
    k = torch.randn(batch_size, k_len, NUM_HEADS, head_dim)
    v = torch.randn(batch_size, k_len, NUM_HEADS, head_dim)

    return flex_prefill_attention(
        q,
        k,
        v,
        gamma=GAMMA,
        tau=TAU,
        min_budget=min_budget,
        block_size=block_size,
    )
