"""Driver: call the official entry with the inputs the harness passes in.

The entry of this Region is the target function itself, so `run` builds the minimal
`self` it needs and calls `gather_last_q_vertical_slash_topk_v4` directly.  Only
`self.config.to_dict()` is read before the target line; the two branches fail just
after the decision because the rest of the model state is intentionally absent.

The repository is imported as-is.  The `minference` package `__init__` pulls in
`models_patch`/`patch`, which no longer import cleanly against the pinned transformers
version, so the driver loads the real `minference.modules.minference_forward` module
through a package placeholder whose `__path__` points at the pinned source tree.
Missing accelerator libraries are declared as mocks in form.json, never edited here.
"""

import os
import sys
import types

import torch


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


class _StreamingConfig:
    def __init__(self, streaming):
        self._streaming = bool(streaming)

    def to_dict(self):
        return {"streaming": self._streaming}


class _MinferenceSelf:
    def __init__(self, config):
        self.config = config


def run(inputs):
    flag = int(inputs["streaming"])
    above = int(inputs["streaming_positive_above"])
    config = _StreamingConfig(flag > above)
    owner = _MinferenceSelf(config)

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

    return _GATHER(owner, q, k, v, 0)
