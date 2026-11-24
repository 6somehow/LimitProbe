"""Driver: call patch_model_config with the declared pattern/cfg pair.

patch_model_config is the target function and the second element of the Region's call chain.
The official call_chain[0] entry (flex_prefill_attention) is a low-level attention op that never
calls patch_model_config, so the target function is called directly; the reason is recorded in
form.json execution.entry_reason.
"""

import types

import torch

from flex_prefill.modules.patch import patch_model_config

torch.manual_seed(0)
torch.set_num_threads(1)


def run(inputs):
    model = types.SimpleNamespace(config=types.SimpleNamespace())
    cfg = dict(inputs["cfg"])
    patch_model_config(model, inputs["pattern"], cfg)
    return None
