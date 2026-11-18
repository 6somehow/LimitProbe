"""Driver for flexprefill-F019: call patch_hf_model with an HF model class name.

The Region is the else-branch raise in patch_hf_model. The hand-off's call_chain[0]
(flex_prefill_attention) never calls patch_hf_model, so the Region function patch_hf_model
(chain[1]) is called directly; see execution.entry_reason.

The positive model's class name lacks llama/glm/qwen2; the negative model's class name
contains llama, so the else branch is not taken. Both are real transformers classes built
from tiny CPU configs. pattern="default" makes the negative branch return from
patch_llama_attention immediately, so no GPU call runs after the target.
"""

import torch
from transformers import (
    LlamaConfig,
    LlamaForCausalLM,
    MistralConfig,
    MistralForCausalLM,
)

from flex_prefill.modules.patch import patch_hf_model

_MODEL_CONFIG = {
    "hidden_size": 16,
    "intermediate_size": 32,
    "num_hidden_layers": 1,
    "num_attention_heads": 2,
    "num_key_value_heads": 2,
    "vocab_size": 32,
}


def _make_model(name):
    if name == "MistralForCausalLM":
        return MistralForCausalLM(MistralConfig(**_MODEL_CONFIG))
    if name == "LlamaForCausalLM":
        return LlamaForCausalLM(LlamaConfig(**_MODEL_CONFIG))
    raise KeyError("unregistered model class " + repr(name))


def run(inputs):
    torch.manual_seed(0)
    model = _make_model(inputs["model_name"])
    return patch_hf_model(model, "default", {})
