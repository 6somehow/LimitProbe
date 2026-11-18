"""Driver for minference-F041 (Region B037, minference/patch.py:840).

The code under test is ``minference_patch`` from the pinned repository file
``minference/patch.py``.  Its module cannot be imported on this CPU-only host: patch.py
pulls in GPU/accelerator-only modules at import time (flash_attn, the device-context
bindings, the package's compiled device extension) and ``minference_forward.py`` runs a device-side
``torch.arange(...)`` at module scope.  None of that is needed for the branch at line 840,
which reads only ``config.use_snapkv``.

So the driver loads the *real* source text of ``minference_patch`` (and of the helper
``patch_glm_4_1m`` it calls below the target) from the pinned repository file, compiles it
with the same filename and line numbers, and calls it.  The target function and its body are
100% repository code; only names the function references *after* the target decision
(``minference_patch_with_snapkv`` and the standard forward-patching helpers) are supplied as
no-op stand-ins, so that the negative run can continue and the traced/untraced runs stay
comparable.  No repository file is modified.  The model is a one-layer torch nn.Module
skeleton: the decision at line 840 never inspects the model, only the config flag.
"""

import ast
import pathlib
import sys
import types

import torch


def _repo_root():
    for entry in sys.path:
        if not entry:
            continue
        candidate = pathlib.Path(entry) / "minference" / "patch.py"
        if candidate.is_file():
            return pathlib.Path(entry)
    raise RuntimeError("cannot locate minference/patch.py on sys.path")


_REPO = _repo_root()
_PATCH_FILE = _REPO / "minference" / "patch.py"
_UTILS_FILE = _REPO / "minference" / "utils.py"


def _extract_function_code(path, name):
    """Compile one top-level function of `path`, padded so its line numbers are unchanged."""
    source = path.read_text()
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    segment = ast.get_source_segment(source, node)
    return compile("\n" * (node.lineno - 1) + segment, str(path), "exec")


class _Attention(torch.nn.Module):
    pass


class _DecoderLayer(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.self_attn = _Attention()


class _Inner(torch.nn.Module):
    def __init__(self, num_layers):
        super().__init__()
        self.layers = torch.nn.ModuleList([_DecoderLayer() for _ in range(num_layers)])
        self.config = types.SimpleNamespace()


class _Model(torch.nn.Module):
    def __init__(self, num_layers):
        super().__init__()
        self.model = _Inner(num_layers)
        self.config = types.SimpleNamespace()


def _noop(*args, **kwargs):
    return None


def _forward_factory(*args, **kwargs):
    return _noop


# module namespace in which the real minference_patch source is executed
_NS = {"__name__": "minference.patch"}
exec(_extract_function_code(_UTILS_FILE, "patch_glm_4_1m"), _NS)
exec(_extract_function_code(_PATCH_FILE, "minference_patch"), _NS)
_NS.update({
    "minference_patch_kv_cache_cpu": lambda model: model,
    "minference_patch_with_snapkv": lambda model: model,
    "minference_forward": _forward_factory,
    "init_minference_parameters": _noop,
    "gather_last_q_vertical_slash_topk_v4": _noop,
    "forward_llama_decoder_layer": _noop,
    "hf_437_prepare_inputs_for_generation": _noop,
    "_prepare_decoder_attention_mask_inference": _noop,
    "forward_llama_model": _noop,
    "forward_llama_for_causal_lm": _noop,
})
minference_patch = _NS["minference_patch"]


def run(inputs):
    torch.set_num_threads(1)
    torch.manual_seed(int(inputs["seed"]))
    config = types.SimpleNamespace(
        use_snapkv=inputs["use_snapkv"],
        kv_cache_cpu=bool(inputs["kv_cache_cpu"]),
        kv_cache_cpu_device=str(inputs["kv_cache_cpu_device"]),
    )
    model = _Model(int(inputs["num_layers"]))
    return minference_patch(model, config)
