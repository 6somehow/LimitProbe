"""Controlled make_testcase used to inject the exception the finding distinguishes.

The harness installs it as a class attribute, so it is called as self.make_testcase(seed)
without an implicit self.  The driver sets FLAG before calling FuzzingLoop.run.  The
exceptions themselves are raised by the repository's own checkers (nnsmith.error), so the
observed raise location is repository-relative and stable in a clean-checkout replay.
This is still a canned test double (sim_class stub), not a real model generator.
"""

FLAG = {"internal": False}


def make_testcase(seed):
    from nnsmith.error import ConstraintCheck, SanityCheck

    if FLAG["internal"]:
        SanityCheck.handler("synthetic internal error from make_testcase")
    ConstraintCheck.handler("synthetic ordinary error from make_testcase")
