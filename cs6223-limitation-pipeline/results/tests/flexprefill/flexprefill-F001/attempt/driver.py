"""Driver for flexprefill-F001: patch_llama_attention rejects non-LlamaForCausalLM models.

The step-4 Region call chain is [artifact entry point, target function]; no code path connects
flex_prefill_attention to patch_llama_attention, so the target function is called directly and
execution.entry_reason records why (D14).
"""

import torch
from transformers import LlamaConfig
from transformers.models.llama.modeling_llama import LlamaForCausalLM, LlamaModel

from flex_prefill.modules.patch import patch_llama_attention


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    cfg = LlamaConfig(**dict(inputs["model_config"]))
    cfg._attn_implementation = "eager"
    if inputs["isinstance(model, LlamaForCausalLM)"]:
        model = LlamaForCausalLM(cfg)
    else:
        model = LlamaModel(cfg)
    return patch_llama_attention(model, str(inputs["pattern"]))
