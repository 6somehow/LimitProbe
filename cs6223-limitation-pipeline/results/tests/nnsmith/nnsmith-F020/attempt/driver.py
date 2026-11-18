"""Driver: exercise the reshape-group binning branch in __GROUP_RESHAPE.

The official entry random_model_gen builds a PureSymbolGen whose extra_constraints
returns [] and whose extra_constraints call sites are commented out, so the
PARAM_CONFIG1["Reshape"] callable __GROUP_RESHAPE cannot be reached from it.
The driver therefore calls the Region function directly on a reshape node whose
destination group has `group_len` dimensions.  With an empty parameter list, a
non-disabled destination index takes the body and fails to index it; the disabled
index skips the body.  Seeds are fixed so the shuffled disable list is stable.
"""

import random

from nnsmith.graph_gen import __GROUP_RESHAPE


class _ReshapeNode:
    num_var_param = None

    def __init__(self, group_len):
        self.src_group = [list(range(group_len))]
        self.dst_group = [list(range(group_len))]
        self.ng = 1


def run(inputs):
    group_len = int(inputs["group_len"])
    random.seed(int(inputs["seed"]))
    node = _ReshapeNode(group_len)
    return __GROUP_RESHAPE(node, None, {}, bin=True)
