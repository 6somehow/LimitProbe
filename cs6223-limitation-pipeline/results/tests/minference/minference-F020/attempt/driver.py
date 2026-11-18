"""Driver for minference-F020: reach MInferenceConfig.update_config_path through the real config class.

The repository package __init__ imports flash-attn / accelerator kernels that are unavailable on this CPU box.
Only minference/minference_configuration.py is needed and it has no such imports, so the driver builds a
synthetic package object for `minference` (with the repository package directory on __path__) and lets the
normal import machinery load the real submodule. No repository file is edited and no stand-in is used.
"""

import importlib
import random
import sys
import types
from pathlib import Path


def _repo_root_with_minference():
    for entry in sys.path:
        if not entry:
            continue
        base = Path(entry)
        if (base / "minference" / "minference_configuration.py").is_file():
            return base
    here = Path(__file__).resolve()
    for base in (Path.cwd(), here.parent, here.parent.parent / "third_party" / "MInference"):
        if (base / "minference" / "minference_configuration.py").is_file():
            return base
    raise ImportError("minference/minference_configuration.py not found on sys.path")


def _load_config_class():
    repo = _repo_root_with_minference()
    if "minference" not in sys.modules:
        pkg = types.ModuleType("minference")
        pkg.__package__ = "minference"
        pkg.__path__ = [str(repo / "minference")]
        sys.modules["minference"] = pkg
    module = importlib.import_module("minference.minference_configuration")
    return module.MInferenceConfig


MInferenceConfig = _load_config_class()

NONSTATIC_TYPES = ["minference", "vllm"]
ALL_TYPES = NONSTATIC_TYPES + list(MInferenceConfig.STASTIC_ATTENTION_TYPES)

random.seed(0)


def run(inputs):
    attn_type = ALL_TYPES[int(inputs["attn_index"])]
    return MInferenceConfig(
        attn_type=attn_type,
        model_name=inputs["model_name"],
        config_path=inputs["config_path"],
    )
