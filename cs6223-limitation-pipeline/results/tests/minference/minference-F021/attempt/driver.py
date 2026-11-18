"""Driver for minference-F021 (Region B005).

The official entry is the inner ``forward`` returned by
``minference.modules.minference_forward.minference_forward``.  Its first statement is a
call to ``init_minference_parameters`` (the target).  We call the entry and let it reach
the target; the branch decision at the target depends only on ``self.config_path``,
``self.layer_idx`` and the number of entries in the JSON file.

The repository imports GPU-only modules at import time.  They are replaced by declared
stand-ins (form.execution.mocks); none of them runs before the target line.
"""

import importlib.machinery
import json
import sys
import types
from pathlib import Path

import torch


def _find_repo():
    for entry in sys.path:
        try:
            root = Path(entry)
            if (root / "minference" / "modules" / "minference_forward.py").is_file():
                return root
        except OSError:
            continue
    raise ImportError("repository root with minference/modules/minference_forward.py not found")


def _shim_package(name, path):
    """Expose the real package directory without executing minference/__init__.py.

    minference/__init__.py imports unrelated modules that do not import under the pinned
    transformers 5.x.  The code under test (minference_forward.py) is imported unchanged.
    """
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    mod.__path__ = [str(path)]
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    spec.submodule_search_locations = [str(path)]
    mod.__spec__ = spec
    sys.modules[name] = mod


def _install_cpu_exports():
    """Fill the declared external placeholders with the CPU implementations from sim.py."""
    import sim as _sim

    flash_attn = sys.modules.get("flash_attn")
    if flash_attn is not None:
        spec = importlib.machinery.ModuleSpec("flash_attn", loader=None, is_package=True)
        spec.submodule_search_locations = []
        flash_attn.__spec__ = spec
        flash_attn.__version__ = "2.0.0"
        flash_attn.flash_attn_varlen_func = _sim.flash_attn_varlen_func
        flash_attn.flash_attn_func = _sim.flash_attn_varlen_func

    compiler = sys.modules.get("pycuda.compiler")
    if compiler is not None:
        compiler.SourceModule = _sim.source_module

    cuda = sys.modules.get("minference.cuda")
    if cuda is not None:
        cuda.convert_vertical_slash_indexes = _sim.convert_vertical_slash_indexes


_REPO = _find_repo()
_shim_package("minference", _REPO / "minference")
_shim_package("minference.modules", _REPO / "minference" / "modules")
_shim_package("minference.ops", _REPO / "minference" / "ops")
_install_cpu_exports()

import minference.modules.minference_forward as _forward_module  # noqa: E402


class _Config:
    def __init__(self, values):
        self._values = values

    def to_dict(self):
        return dict(self._values)


class _Attention:
    init_minference_parameters = _forward_module.init_minference_parameters

    def __init__(self, config_path, layer_idx):
        self.config = _Config({"starting_layer": 0, "is_search": False, "config_path": config_path})
        self.layer_idx = layer_idx


def run(inputs):
    torch.manual_seed(int(inputs["seed"]))

    config_dir = Path(inputs["config_dir"])
    config_dir.mkdir(parents=True, exist_ok=True)
    n_layers = int(inputs["config_len"])
    layer_idx = int(inputs["layer_idx"])
    entry = inputs["config_entry"]

    config_path = config_dir / f"patterns_{n_layers}.json"
    config_path.write_text(json.dumps([entry for _ in range(n_layers)]))

    attention = _Attention(str(config_path), layer_idx)
    forward = _forward_module.minference_forward()
    return forward(attention, None, None, None, None, False, False)
