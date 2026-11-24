"""Driver for minference-F032: call gather_last_q_vertical_slash_topk_vllm with q_len 1 vs 2.

The official step-4 call chain is [gather_last_q_vertical_slash_topk_v4,
gather_last_q_vertical_slash_topk_vllm], but the static analysis found no call chain
(v4 is defined before vllm and never calls it; vllm is only called from
minference_vllm_forward, which needs a GPU vLLM install).  We therefore call the Region's
own function directly and record the reason in execution.entry_reason.
"""

import importlib.util
import pathlib
import sys
import types

import torch

torch.set_num_threads(1)


def _load_target_module():
    repo = None
    for entry in list(sys.path):
        candidate = pathlib.Path(entry) / "minference" / "modules" / "minference_forward.py"
        if candidate.is_file():
            repo = pathlib.Path(entry).resolve()
            break
    if repo is None:
        raise RuntimeError("pinned MInference repository not found on sys.path")

    # The repository package __init__ imports the vLLM/HF patch layer, which is not
    # importable with the pinned CPU environment.  These are plain package containers
    # (no computation) so the Region's own source file can be imported unchanged.
    for name, sub in (("minference", "minference"),
                      ("minference.modules", "minference/modules"),
                      ("minference.ops", "minference/ops")):
        if name not in sys.modules:
            pkg = types.ModuleType(name)
            pkg.__path__ = [str(repo / sub)]
            sys.modules[name] = pkg

    target = repo / "minference" / "modules" / "minference_forward.py"
    spec = importlib.util.spec_from_file_location("minference.modules.minference_forward", target)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_MF = _load_target_module()


def run(inputs):
    q_len = int(inputs["q_len"])
    bsz = int(inputs["bsz"])
    head_dim = int(inputs["head_dim"])
    head_id = int(inputs["head_id"])
    seed = int(inputs["seed"])
    pattern_type = str(inputs["pattern_type"])
    dtype = getattr(torch, str(inputs["dtype"]))

    torch.manual_seed(seed)
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    q = torch.randn(bsz, 1, q_len, head_dim, generator=gen, dtype=dtype)
    k = torch.randn(bsz, 1, q_len, head_dim, generator=gen, dtype=dtype)
    v = torch.randn(bsz, 1, q_len, head_dim, generator=gen, dtype=dtype)

    self = types.SimpleNamespace(best_pattern={head_id: (pattern_type, 1000, 6096, 1)})
    return _MF.gather_last_q_vertical_slash_topk_vllm(self, q, k, v, head_id)
