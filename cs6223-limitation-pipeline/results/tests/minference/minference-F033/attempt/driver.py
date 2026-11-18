"""Driver for the vLLM MInference prefill decision.

The official entry from the static chain (`gather_last_q_vertical_slash_topk_v4`) is a sparse
kernel launcher that does not call this vLLM wrapper.  The static analysis recorded
`call_chain_status: not_found`, so the driver calls the target closure directly and records
that reason in form.json.  The object passed as `self` is a minimal stand-in for the vLLM
attention layer; every value below comes from `inputs`.
"""
import math
from types import SimpleNamespace

import torch

import minference.modules.minference_forward as mf


class _AttentionLayer:
    pass


def _sparse_out(q_head, k_head, v_head, head):
    return torch.zeros_like(q_head)


def run(inputs):
    seed = int(inputs["seed"])
    torch.manual_seed(seed)
    torch.set_num_threads(1)

    num_tokens = int(inputs["num_tokens"])
    num_heads = int(inputs["num_heads"])
    num_kv_heads = int(inputs["num_kv_heads"])
    head_size = int(inputs["head_size"])
    num_blocks = int(inputs["num_blocks"])
    block_size = int(inputs["block_size"])
    layer_idx = int(inputs["layer_idx"])
    kv_is_none = bool(inputs["kv_cache is None"])
    table_size = int(inputs["prefill_meta.block_tables.numel()"])

    query = torch.randn(num_tokens, num_heads * head_size, dtype=torch.float32)
    key = torch.randn(num_tokens, num_kv_heads * head_size, dtype=torch.float32)
    value = torch.randn(num_tokens, num_kv_heads * head_size, dtype=torch.float32)

    if kv_is_none:
        kv_cache = None
    else:
        kv_cache = torch.zeros(2, num_blocks, block_size * num_kv_heads * head_size,
                               dtype=torch.float32)

    block_tables = torch.zeros(1, table_size, dtype=torch.int32)
    prefill_meta = SimpleNamespace(
        block_tables=block_tables,
        seq_start_loc=torch.tensor([0, num_tokens], dtype=torch.int32),
        max_prompt_len=torch.tensor(num_tokens, dtype=torch.int32),
        subquery_start_loc=torch.tensor([0, num_tokens], dtype=torch.int32),
        prompt_lens_tensor=torch.tensor([num_tokens], dtype=torch.int32),
        context_lens=torch.tensor([0], dtype=torch.int32),
        max_subquery_len=num_tokens,
    )
    attn_metadata = SimpleNamespace(
        num_prefill_tokens=num_tokens,
        num_decode_tokens=0,
        prefill_metadata=prefill_meta,
        decode_metadata=None,
        slot_mapping=torch.tensor(list(range(num_tokens)), dtype=torch.long),
        kv_cache_dtype=torch.float32,
    )

    layer = _AttentionLayer()
    layer.best_pattern = {}
    layer.num_heads = num_heads
    layer.num_kv_heads = num_kv_heads
    layer.head_size = head_size
    layer.scale = 1.0 / math.sqrt(head_size)
    layer.alibi_slopes = None
    layer.sliding_window = None
    layer.gather_last_q_vertical_slash_topk_vllm = _sparse_out

    pattern_config = {
        layer_idx: {head: ("vertical_and_slash", 1000, 100, 1) for head in range(num_heads)}
    }
    forward = mf.minference_vllm_forward(pattern_config)
    return forward(layer, query, key, value, kv_cache, attn_metadata, 1.0, layer_idx)
