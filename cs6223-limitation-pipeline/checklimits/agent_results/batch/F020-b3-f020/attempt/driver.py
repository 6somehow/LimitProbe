"""Driver: reach the prefix-cache branch in patch_vllm_model.flex_prefill_forward.

The Region's decision lives in the nested forward defined by the repository's
patch_vllm_model.  vLLM is not installed (CPU box), so the declared fake_module
`vllm` is completed by sim.py with the tiny API patch.py imports; the branch
condition itself is then evaluated by the repository code on real tensors.
"""

import types

import torch

import sim

sim.install_vllm_stub()

from flex_prefill.modules import patch as patch_mod

torch.set_num_threads(1)


class _DummyAttention(torch.nn.Module):
    def __init__(self, impl):
        super().__init__()
        self.impl = impl


class _DummyRoot(torch.nn.Module):
    def __init__(self, attention):
        super().__init__()
        self.attn = attention


def _impl(p):
    return types.SimpleNamespace(
        num_heads=p["num_heads"],
        head_size=p["head_size"],
        num_kv_heads=p["num_kv_heads"],
        kv_cache_dtype="auto",
        scale=1.0 / (p["head_size"] ** 0.5),
        sliding_window=None,
        alibi_slopes=None,
        logits_soft_cap=None,
    )


def _model(p):
    impl = _impl(p)
    attn = _DummyAttention(impl)
    root = _DummyRoot(attn)
    model = sim.LLM()
    model.llm_engine = types.SimpleNamespace(
        scheduler_config=types.SimpleNamespace(chunked_prefill_enabled=True, max_num_seqs=2),
        model_executor=types.SimpleNamespace(
            driver_worker=types.SimpleNamespace(
                model_runner=types.SimpleNamespace(model=root)
            )
        ),
    )
    return model, impl


def _metadata(p):
    prefill = types.SimpleNamespace(
        block_tables=torch.zeros(p["block_tables_numel"], dtype=torch.int32),
        seq_lens=None,
        seq_start_loc=torch.tensor([0, p["num_prefill_tokens"]], dtype=torch.int32),
        query_start_loc=torch.tensor([0, p["num_prefill_tokens"]], dtype=torch.int32),
        max_prefill_seq_len=p["num_prefill_tokens"],
        max_query_len=p["num_prefill_tokens"],
    )
    return types.SimpleNamespace(
        prefill_metadata=prefill,
        decode_metadata=None,
        num_prefill_tokens=p["num_prefill_tokens"],
        num_decode_tokens=p["num_decode_tokens"],
        slot_mapping=torch.zeros(p["num_prefill_tokens"], dtype=torch.int64),
    )


def _tensors(p):
    tokens = p["num_prefill_tokens"] + p["num_decode_tokens"]
    dt = getattr(torch, p["dtype"])
    query = torch.randn(tokens, p["num_heads"] * p["head_size"], dtype=dt)
    key = torch.randn(tokens, p["num_kv_heads"] * p["head_size"], dtype=dt)
    value = torch.randn(tokens, p["num_kv_heads"] * p["head_size"], dtype=dt)
    key_cache = torch.zeros(p["cache_blocks"], p["cache_block_size"],
                            p["num_kv_heads"], p["head_size"], dtype=dt)
    value_cache = torch.zeros_like(key_cache)
    return query, key, value, (key_cache, value_cache)


def run(inputs):
    p = dict(inputs)
    torch.manual_seed(p["seed"])
    torch.set_num_threads(1)

    model, impl = _model(p)
    cfg = {
        "flex_prefill_gamma": p["gamma"],
        "flex_prefill_tau": p["tau"],
        "flex_prefill_min_budget": p["min_budget"],
        "flex_prefill_max_budget": p["max_budget"],
    }
    patch_mod.patch_vllm_model(model, "flex_prefill", cfg)

    query, key, value, kv_cache = _tensors(p)
    attn_metadata = _metadata(p)
    return impl.forward(
        query,
        key,
        value,
        kv_cache,
        attn_metadata,
        k_scale=1.0,
        v_scale=1.0,
        attn_type=sim.AttentionType.DECODER,
    )
