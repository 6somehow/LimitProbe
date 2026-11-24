"""Driver for flexprefill-F021: patch_vllm_model's attention-module selector.

The target is the `if "attention" in type(m).__name__.lower() and hasattr(m, "impl")`
decision at flex_prefill/modules/patch.py:501.  vLLM is not installed on this CPU box,
so the vllm module is a declared fake module (see form.json).  Everything that reaches
the target line (the model/engine/module hierarchy and the loop over named_modules) is
real Python; only the absent vllm.LLM base class and the vllm namespace come from the
declared stand-in.
"""

import types

import torch
import vllm

from flex_prefill.modules import patch as patch_mod
from flex_prefill.modules.patch import patch_vllm_model


class _LLM:
    """Minimal stand-in for vllm.LLM; patch_vllm_model only checks isinstance(model, vllm.LLM)."""


class _AttentionType:
    """Enum-like stand-in for vllm.attention.backends.abstract.AttentionType."""

    DECODER = "DECODER"


vllm.LLM = _LLM

# Names patch.py imports from vllm only when vllm is importable.  The nested
# flex_prefill_forward signature is evaluated when patch_vllm_model is called (before
# the target loop), so these names must resolve at definition time.
patch_mod.AttentionType = _AttentionType
patch_mod.FlashAttentionMetadata = object
patch_mod.ops = types.SimpleNamespace()

# The tracer evaluates Region.condition on the frame locals/globals with a restricted
# builtins table that does not contain type/hasattr.  Expose the real builtins in the
# module namespace so the harness can evaluate the *actual* condition expression.
patch_mod.type = type
patch_mod.hasattr = hasattr


class _ModuleContainer:
    def __init__(self, module):
        self._module = module

    def named_modules(self):
        return iter([("attention_layer", self._module)])


def _make_module(name_variant, has_impl):
    if int(name_variant) == 0:
        class_name = "AttentionModule"
    else:
        class_name = "PlainModule"
    attrs = {}
    if has_impl:
        attrs["impl"] = types.SimpleNamespace()
    cls = type(class_name, (object,), attrs)
    return cls()


def _make_model(name_variant, has_impl):
    module = _make_module(name_variant, has_impl)
    container = _ModuleContainer(module)
    runner = types.SimpleNamespace(model=container)
    driver_worker = types.SimpleNamespace(model_runner=runner)
    model_executor = types.SimpleNamespace(driver_worker=driver_worker)
    scheduler_config = types.SimpleNamespace()
    llm_engine = types.SimpleNamespace(scheduler_config=scheduler_config,
                                       model_executor=model_executor)
    model = _LLM()
    model.llm_engine = llm_engine
    return model


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)

    name_variant = int(inputs["name_variant"])
    has_impl = bool(inputs["has_impl"])
    model = _make_model(name_variant, has_impl)
    return patch_vllm_model(model, "flex_prefill", {"flex_prefill_gamma": 0.9})
