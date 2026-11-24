"""CPU stand-ins for the absent vLLM package.

vLLM is not installed on this CPU-only machine.  patch.py imports it in a
try/except block; without a stand-in the names vllm/ops/AttentionType/
FlashAttentionMetadata are undefined and patch_vllm_model cannot even define
flex_prefill_forward.  This module fills the declared fake_module `vllm` with
the smallest real API surface the repository code touches, so the target branch
in flex_prefill_forward is decided by the repository's own condition.
"""

import sys
import types


class AttentionType:
    DECODER = "DECODER"
    ENCODER = "ENCODER"
    ENCODER_DECODER = "ENCODER_DECODER"


class FlashAttentionMetadata:
    pass


class LLM:
    pass


def reshape_and_cache_flash(key, value, key_cache, value_cache, slot_mapping,
                            kv_cache_dtype, k_scale, v_scale):
    # The fused vLLM KV-cache write is irrelevant to the target decision; write the
    # rows into the cache with plain torch so the stand-in still does real work.
    n = key.shape[0]
    if n == 0:
        return None
    slots = slot_mapping.reshape(-1)[:n]
    flat_k = key_cache.reshape(-1, key_cache.shape[-2], key_cache.shape[-1])
    flat_v = value_cache.reshape(-1, value_cache.shape[-2], value_cache.shape[-1])
    for i in range(n):
        flat_k[int(slots[i])] = key[i]
        flat_v[int(slots[i])] = value[i]
    return None


def install_vllm_stub():
    vllm = sys.modules.get("vllm")
    if vllm is None:
        raise RuntimeError("declared fake_module 'vllm' was not installed by the harness")

    ops = types.ModuleType("vllm._custom_ops")
    ops.reshape_and_cache_flash = reshape_and_cache_flash

    attention = types.ModuleType("vllm.attention")
    backends = types.ModuleType("vllm.attention.backends")
    abstract = types.ModuleType("vllm.attention.backends.abstract")
    abstract.AttentionType = AttentionType
    flash_attn = types.ModuleType("vllm.attention.backends.flash_attn")
    flash_attn.FlashAttentionMetadata = FlashAttentionMetadata

    for name, mod in (
        ("vllm._custom_ops", ops),
        ("vllm.attention", attention),
        ("vllm.attention.backends", backends),
        ("vllm.attention.backends.abstract", abstract),
        ("vllm.attention.backends.flash_attn", flash_attn),
    ):
        sys.modules[name] = mod

    sys.modules["vllm.LLM"] = LLM

    # Resolvable attribute chain for `from vllm.attention...` imports.  LLM and
    # _custom_ops are intentionally left to the RecordingModule so their use is logged.
    vllm.attention = attention
    attention.backends = backends
    backends.abstract = abstract
    backends.flash_attn = flash_attn
    return vllm
