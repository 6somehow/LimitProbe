"""Driver: call the official entry (the target function itself) with the inputs the harness passes in.

`gather_last_q_vertical_slash_topk_v4` reads only `self.config.to_dict()` and
`self.best_pattern` before the decision at line 434.  The repository package __init__
pulls in unrelated modules that do not import under the pinned transformers version, so
the real `minference.modules.minference_forward` source is imported through a package
placeholder whose __path__ points at the pinned tree.  Missing accelerator libraries are
declared as mocks in form.json; none of them computes anything before the target.
"""

import os
import sys
import types

import torch

torch.set_num_threads(1)


def _find_minference_package():
    for entry in sys.path:
        base = entry or os.getcwd()
        candidate = os.path.join(base, "minference")
        if os.path.isfile(os.path.join(candidate, "modules", "minference_forward.py")):
            return candidate
    raise RuntimeError("minference package was not found on sys.path")


def _import_target_module():
    package_dir = _find_minference_package()
    if "minference" not in sys.modules:
        package = types.ModuleType("minference")
        package.__path__ = [package_dir]
        package.__package__ = "minference"
        sys.modules["minference"] = package
    import minference.modules.minference_forward as target

    return target


_TARGET = _import_target_module()
_GATHER = _TARGET.gather_last_q_vertical_slash_topk_v4

_DTYPES = {"float32": torch.float32, "float64": torch.float64}


class _Config:
    def __init__(self, values):
        self._values = values

    def to_dict(self):
        return dict(self._values)


class _MinferenceSelf:
    def __init__(self, config, best_pattern):
        self.config = config
        self.best_pattern = best_pattern


def run(inputs):
    flag = int(inputs["vs_only"])
    above = int(inputs["vs_only_above"])
    config = _Config({"vs_only": flag > above})

    pattern_type = str(inputs["pattern_type"])
    head_id = int(inputs["head_id"])
    owner = _MinferenceSelf(config, {head_id: (pattern_type, 1000, 6096, 1)})

    seed = int(inputs["seed"])
    batch_size = int(inputs["batch_size"])
    num_heads = int(inputs["num_heads"])
    q_len = int(inputs["q_len"])
    head_dim = int(inputs["head_dim"])
    dtype = _DTYPES[inputs["dtype"]]

    torch.manual_seed(seed)
    shape = (batch_size, num_heads, q_len, head_dim)
    q = torch.randn(shape, dtype=dtype)
    k = torch.randn(shape, dtype=dtype)
    v = torch.randn(shape, dtype=dtype)

    return _GATHER(owner, q, k, v, head_id)
