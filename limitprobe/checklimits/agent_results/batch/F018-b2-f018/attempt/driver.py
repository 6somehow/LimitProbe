"""Driver for flexprefill-F018.

The target `patch_hf_model` chooses the patch_*_attention implementation from
`type(model).__name__`.  It is reached through the repository's public `patch_model`
entry, which is the real caller of `patch_hf_model`.  The region call chain names
`flex_prefill_attention` as the entry, but that function is an attention kernel and
never calls `patch_hf_model`; the reason is recorded in form.json.

The control pair differs only in the model class: a real LlamaForCausalLM versus a
real Qwen2ForCausalLM.  The pattern is the repository default, so each
patch_*_attention function returns before touching any GPU kernel.
"""

import torch
from transformers import LlamaConfig, LlamaForCausalLM, Qwen2Config, Qwen2ForCausalLM

from flex_prefill.modules.patch import patch_model

_CLASSES = {
    "LlamaForCausalLM": (LlamaForCausalLM, LlamaConfig),
    "Qwen2ForCausalLM": (Qwen2ForCausalLM, Qwen2Config),
}


def run(inputs):
    torch.set_num_threads(1)
    torch.manual_seed(inputs["seed"])

    model_name = inputs["model_class"]
    model_cls, config_cls = _CLASSES[model_name]
    model = model_cls(config_cls(**inputs["model_kwargs"]))

    return patch_model(model, inputs["pattern"], inputs["cfg"])
