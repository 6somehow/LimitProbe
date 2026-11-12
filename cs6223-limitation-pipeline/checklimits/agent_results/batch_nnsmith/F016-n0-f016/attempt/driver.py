"""Driver: call the official entry (the target function ``main``) with a constructed cfg.

The witness only names a predicate (``cfg["backend"]["type"] is not None``), so the cfg is
built here.  The single boundary factor is ``backend_type_code``: 0 maps to ``None`` and any
other integer maps to a real backend name.  Everything below the target is stopped by the
declared post-target stand-in in sim.py.
"""

import random

import numpy as np
import torch
from omegaconf import OmegaConf

from nnsmith.cli import model_gen


def _backend_type(code, backend_name):
    return None if int(code) == 0 else backend_name


def run(inputs):
    seed = int(inputs["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)

    cfg = OmegaConf.create(
        {
            "mgen": {
                "init_rank": int(inputs["init_rank"]),
                "max_nodes": int(inputs["max_nodes"]),
                "timeout_ms": int(inputs["timeout_ms"]),
                "seed": seed,
                "save": "nnsmith_output",
            },
            "model": {"type": inputs["model_type"], "path": ""},
            "backend": {
                "type": _backend_type(inputs["backend_type_code"], inputs["backend_type_name"]),
                "optmax": False,
                "target": inputs["backend_target"],
            },
            "debug": {"viz": False, "viz_fmt": "png"},
        }
    )
    return model_gen.main(cfg)
