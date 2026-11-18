"""Driver for minference-F001: call the public MInferenceConfig constructor.

The hand-off's call chain starts at gather_last_q_vertical_slash_topk_v4, but the static
analysis found no path from there to update_config_path (chain status: not_found).  The
target is reached through the public constructor MInferenceConfig(...): its __init__ calls
update_config_path(config_path, model_name), which is the second function of the chain.
"""

import importlib
import os
import sys
import types


def _import_minference_configuration():
    pkg = sys.modules.get("minference")
    if pkg is None:
        pkg_dir = None
        for base in sys.path:
            cand = os.path.join(base or os.getcwd(), "minference", "minference_configuration.py")
            if os.path.isfile(cand):
                pkg_dir = os.path.dirname(cand)
                break
        if pkg_dir is None:
            raise ImportError("cannot locate the pinned minference package")
        pkg = types.ModuleType("minference")
        pkg.__path__ = [pkg_dir]
        pkg.__package__ = "minference"
        sys.modules["minference"] = pkg
    return importlib.import_module("minference.minference_configuration")


_mc = _import_minference_configuration()
MInferenceConfig = _mc.MInferenceConfig


def run(inputs):
    cfg = MInferenceConfig(
        attn_type=inputs["attn_type"],
        model_name=inputs["model_name"],
        config_path=inputs["config_path"],
    )
    return cfg.config_path is not None
