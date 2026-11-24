"""Driver for finding nnsmith-F015.

The harness input selects the two config values that decide the target branch of
``FuzzingLoop.__init__``: ``crash_safe`` (0/1, mapped through bool() exactly as the
repository does) and ``test_timeout``.  The rest of the config keeps the pre-target
path identical: a non-tflite backend so the TFLite cleanup branch is skipped, no
comparison backend, and an unknown filter name so execution stops deterministically
right after the target decision instead of building a backend / generating models.
"""

import random

import numpy as np
import torch

from nnsmith.cli.fuzz import FuzzingLoop


def run(inputs):
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)

    cfg = {
        "backend": {"type": "torch", "target": "cpu", "optmax": 1},
        "cmp": {"with": None},
        "fuzz": {
            "crash_safe": inputs["crash_safe"],
            "test_timeout": inputs["test_timeout"],
        },
        "filter": {"type": "__checklimits_invalid__", "patch": []},
    }
    return FuzzingLoop(cfg)
