"""Driver for flexprefill-F002: exercise the Qwen2 patch guard directly.

The official entry ``flex_prefill_attention`` never calls ``patch_qwen2_attention``
(the step-4 call chain only links them through an import), so the driver calls the
target function itself and records the reason in the form. A tiny GPT-2 model is a
real non-Qwen2 ``PreTrainedModel``; a tiny Qwen2 model is the contrast case. The only
input factor that changes is the model family. The pattern is a non-default string as
required by the path prefix; after the target it hits the unknown-pattern branch,
which avoids loading a GPU attention module on the negative run.
"""

import torch
from transformers import GPT2Config, GPT2LMHeadModel, Qwen2Config
from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM

from flex_prefill.modules.patch import patch_qwen2_attention


def _build_model(model_kind):
    if int(model_kind) == 1:
        cfg = Qwen2Config(
            vocab_size=16,
            hidden_size=8,
            intermediate_size=16,
            num_hidden_layers=1,
            num_attention_heads=2,
            num_key_value_heads=1,
            max_position_embeddings=16,
        )
        return Qwen2ForCausalLM(cfg)
    cfg = GPT2Config(vocab_size=16, n_embd=8, n_layer=1, n_head=2, n_positions=16)
    return GPT2LMHeadModel(cfg)


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))
    torch.set_num_threads(1)
    model = _build_model(inputs["model_kind"])
    return patch_qwen2_attention(model, str(inputs["pattern"]))
