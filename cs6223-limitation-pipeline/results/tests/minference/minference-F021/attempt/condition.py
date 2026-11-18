"""The guard on the target line: the loaded-config branch is taken."""

import json
import os


def predicate(locals):
    attention = locals.get("self")
    if attention is None:
        return False
    config_path = attention.config_path
    if config_path is None or not os.path.exists(config_path):
        return False
    with open(config_path) as handle:
        patterns = json.load(handle)
    return attention.layer_idx < len(patterns)
