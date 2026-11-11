"""Driver: exercise the Region at flex_prefill/modules/patch.py:114.

The Region lives in patch_llama_attention, which the recorded call chain places at
index 1.  Its recorded "entry" flex_prefill_attention never calls it (it is a GPU
attention kernel entry), so calling that entry could not reach the target.  The
driver therefore calls patch_llama_attention directly with a real, tiny
LlamaForCausalLM and the `pattern` value from the harness inputs.  For the positive
input the function returns at the target; for the negative input it continues past
the target and patches the model with the repository's own flex_prefill forward.
"""

import torch
from transformers import LlamaConfig
from transformers.models.llama.modeling_llama import LlamaForCausalLM

from flex_prefill.modules.patch import patch_llama_attention


def run(inputs):
    torch.manual_seed(inputs["seed"])
    config = LlamaConfig(
        vocab_size=inputs["vocab_size"],
        hidden_size=inputs["hidden_size"],
        intermediate_size=inputs["intermediate_size"],
        num_hidden_layers=inputs["num_hidden_layers"],
        num_attention_heads=inputs["num_attention_heads"],
        num_key_value_heads=inputs["num_key_value_heads"],
        max_position_embeddings=inputs["max_position_embeddings"],
    )
    model = LlamaForCausalLM(config)
    return patch_llama_attention(model, inputs["pattern"])
