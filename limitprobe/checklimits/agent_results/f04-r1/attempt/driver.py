"""Driver: call the official entry `flex_prefill_attention` with inputs from the harness.

The positive input makes the target guard reject; the negative passes it and then fails
later on the missing GPU (below the target), which the harness records as "no effect".
"""
import torch

from flex_prefill.ops.flex_prefill_attention import flex_prefill_attention

SEED = 0
NUM_Q_HEADS = 2
NUM_KV_HEADS = 1
GAMMA = 0.9
TAU = 0.1
BLOCK_SIZE = 128
DTYPE = torch.float32


def run(inputs):
    q_len = int(inputs["q_len"])
    head_dim = int(inputs["head_dim"])

    torch.manual_seed(SEED)
    torch.set_num_threads(1)

    q = torch.randn(1, q_len, NUM_Q_HEADS, head_dim, dtype=DTYPE)
    k = torch.randn(1, q_len, NUM_KV_HEADS, head_dim, dtype=DTYPE)
    v = torch.randn(1, q_len, NUM_KV_HEADS, head_dim, dtype=DTYPE)

    return flex_prefill_attention(q, k, v, GAMMA, tau=TAU, block_size=BLOCK_SIZE)
