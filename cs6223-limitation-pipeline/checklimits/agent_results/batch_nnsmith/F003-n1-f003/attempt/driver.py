"""Driver for nnsmith-F003: FuzzingLoop.run re-raises InternalError from make_testcase.

Calls the target's own function `FuzzingLoop.run`.  The only stand-in is
`FuzzingLoop.make_testcase`, declared as a patch mock in form.json: it is the failing
callee that the target's try/except inspects, and constructing a full NNSmith backend on
this CPU-only box would need a GPU toolchain.  It raises an InternalError when the input
factor is 1 and an ordinary RuntimeError otherwise, so the one differing factor is the
type of exception thrown by make_testcase.
"""

import os
import random

import nnsmith.cli.fuzz as fuzz


def run(inputs):
    failure_code = inputs["failure_code"]
    os.environ["CHECKLIMITS_SIM_MODE"] = str(failure_code)
    os.environ["CHECKLIMITS_SIM_DELAY"] = str(inputs["negative_delay_s"])
    random.seed(inputs["random_seed"])

    loop = fuzz.FuzzingLoop.__new__(fuzz.FuzzingLoop)
    loop.timeout_s = inputs["loop_timeout_s"]
    loop.cfg = {
        "model": {"type": "torch"},
        "mgen": {"max_nodes": 1},
        "backend": {"target": "cpu"},
    }
    loop.status = type("Status", (), {"n_testcases": 0, "n_bugs": 0})()
    loop.validate_and_report = lambda testcase: True
    return loop.run()
