"""Drive the real FuzzingLoop.run with a controlled `make_testcase`.

The finding is about what FuzzingLoop.run does with an exception from make_testcase:
an InternalError is re-raised at fuzz.py:180, while any other exception is logged and
the loop continues.  Building a whole model-generation pipeline to obtain a real
InternalError on CPU is non-deterministic, so `make_testcase` is replaced (declared as
a mock) and raises the exception selected by the witness predicate.  FuzzingLoop.run
itself, its except clauses and the `raise e` statement are the real repository code.
"""

import random
import sys

from nnsmith.cli.fuzz import FuzzingLoop


def run(inputs):
    internal = bool(inputs["isinstance(e, InternalError)"])
    sim = sys.modules.get("_checklimits_sim_sim")
    if sim is not None:
        sim.FLAG["internal"] = internal
    random.seed(int(inputs["seed"]))
    loop = FuzzingLoop.__new__(FuzzingLoop)
    loop.timeout_s = int(inputs["timeout_s"])
    loop.cfg = {"model": {"type": "mock"}, "mgen": {"max_nodes": 0}, "backend": {"target": "cpu"}}
    loop._checklimits_internal = internal
    return loop.run()
