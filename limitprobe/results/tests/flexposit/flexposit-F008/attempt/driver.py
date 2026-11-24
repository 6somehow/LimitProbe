"""Driver: call the real _order_candidates with the strategy from the inputs.

The official entry (flexposit.api.quantize) only implements budget-mode planning:
its plan_windows() always sorts by sensitivity and has no random/sweep strategy,
so it never calls _order_candidates.  The target is reachable only through
flexposit.mpq.channel_window.main() in sweep mode, which needs an argparse
namespace, a HuggingFace checkpoint/tokenizer and a GPU-capable eval loop.  We
therefore call the real target function directly and record the reason in
execution.entry_reason (the task's static analysis says the chain is not_found).

Everything below the target decision is the repository's own code; no stand-ins
are used before the target.
"""

import os
import sys


def _put_repo_src_on_path():
    for entry in list(sys.path):
        src = os.path.join(entry, "src")
        if os.path.isdir(os.path.join(src, "flexposit")):
            if src not in sys.path:
                sys.path.insert(0, src)
            return


_put_repo_src_on_path()

import numpy as np  # noqa: E402

from flexposit.mpq.channel_window import _order_candidates  # noqa: E402


def run(inputs):
    strategy = inputs["strategy"]
    cands = [tuple(row) for row in inputs["cands"]]
    layer_order_map = dict(inputs["layer_order_map"])
    rng = np.random.default_rng(int(inputs["seed"]))
    return _order_candidates(cands, strategy=strategy, layer_order_map=layer_order_map, rng=rng)
