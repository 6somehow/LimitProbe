"""CPU stand-in for the failing `FuzzingLoop.make_testcase` call.

This is a stub, not a reference implementation: it exists only to produce the exception
that the target `except InternalError as e:` statement inspects.  It returns no model.
"""

import os
import time

from nnsmith.error import InternalError


def make_testcase(seed):
    mode = int(os.environ.get("CHECKLIMITS_SIM_MODE", "0"))
    if mode == 1:
        raise InternalError("simulated internal error from make_testcase")
    time.sleep(float(os.environ.get("CHECKLIMITS_SIM_DELAY", "1.5")))
    raise RuntimeError("simulated ordinary failure from make_testcase")
