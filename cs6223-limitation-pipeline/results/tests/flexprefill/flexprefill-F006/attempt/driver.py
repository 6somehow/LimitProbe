"""Driver for flexprefill-F006.

The official entry (flex_prefill_attention) builds `block_idx` internally via get_active_blocks,
which always returns list[list[Tensor]]; the value is never an argument, so the malformed shape the
Region is about cannot be supplied through that entry without replacing code that runs before the
target.  The driver therefore calls the target function triton_block_wise_prefill_attention
(call_chain index 1) with a real q/k/v and an explicitly built block_idx.  See
execution.entry_reason in form.json.

`block_idx_nesting` is the single factor of the control pair (layout "base"):
  1 -> [Tensor, Tensor]              (block_idx[0] is not a list -> Region condition true -> assert fails)
  2 -> [[Tensor, Tensor]]            (list of list of Tensor -> Region condition false -> assert passes)
  3 -> [[[Tensor, Tensor]]]          (neighbour probe: block_idx[0][0] is a list -> assert fails)

`block_idx_layout` selects extra negative shapes that only exist to separate the index-constant
mutants of the Region statement from the original; they must still show no effect.
"""

import torch

from flex_prefill.ops.flex_prefill_attention import triton_block_wise_prefill_attention

SEED = 0
NUM_Q_HEADS = 2
NUM_KV_HEADS = 2


def _block_idx(nesting, layout):
    t = torch.tensor([0, 1], dtype=torch.long)
    u = torch.tensor([2, 3], dtype=torch.long)
    if layout == "row2":
        return [[t, u], [t, u]]
    if layout == "sublist":
        return [[t, [u]]]
    if layout != "base":
        raise ValueError(f"unsupported block_idx_layout: {layout!r}")
    if nesting == 1:
        return [t, u]
    if nesting == 2:
        return [[t, u]]
    if nesting == 3:
        return [[[t, u]]]
    raise ValueError(f"unsupported block_idx_nesting: {nesting!r}")


def run(inputs):
    torch.manual_seed(SEED)
    batch_size = int(inputs["batch_size"])
    q_len = int(inputs["q_len"])
    k_len = int(inputs["k_len"])
    head_dim = int(inputs["head_dim"])
    block_size = int(inputs["block_size"])

    q = torch.randn(batch_size, q_len, NUM_Q_HEADS, head_dim, dtype=torch.bfloat16)
    k = torch.randn(batch_size, k_len, NUM_KV_HEADS, head_dim, dtype=torch.bfloat16)
    v = torch.randn(batch_size, k_len, NUM_KV_HEADS, head_dim, dtype=torch.bfloat16)

    block_idx = _block_idx(int(inputs["block_idx_nesting"]), str(inputs["block_idx_layout"]))
    return triton_block_wise_prefill_attention(q, k, v, block_idx, block_size)
