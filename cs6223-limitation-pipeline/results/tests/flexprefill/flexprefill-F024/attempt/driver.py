"""Driver for flexprefill-F024: call the official entry flex_prefill_attention.

The target is the block-size guard inside triton_block_wise_prefill_attention.  Reaching it runs
get_active_blocks first, which only needs CPU torch code except for triton_bnhd_pool (replaced by
sim.py).  Each call resets the module-level causal_mask cache to the state a fresh process would
have, because the harness probes several block sizes in one process.
"""

import torch

import flex_prefill.ops.flex_prefill_attention as fpa
from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention


def run(inputs):
    torch.set_num_threads(1)
    torch.manual_seed(int(inputs["seed"]))
    fpa.causal_mask = None

    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])
    num_q_heads = int(inputs["num_q_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    min_budget = int(inputs["min_budget"])
    block_size = int(inputs["block_size"])
    gamma = float(inputs["gamma"])
    tau = float(inputs["tau"])

    q = torch.randn(batch_size, q_len, num_q_heads, head_dim, dtype=torch.bfloat16)
    k = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=torch.bfloat16)
    v = torch.randn(batch_size, k_len, num_kv_heads, head_dim, dtype=torch.bfloat16)

    return flex_prefill_attention(
        q, k, v, gamma, tau=tau, min_budget=min_budget, block_size=block_size
    )
