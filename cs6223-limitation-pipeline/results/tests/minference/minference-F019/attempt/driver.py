"""Driver: call the official entry with the inputs the harness passes in.

Rules: import the code under test at module level (the harness loads this file before it starts
tracing); build tensors / objects from `inputs` only; set seeds; CPU only; no assertions of your own
(the harness decides from the trace and the exception); do not catch the exception you are
looking for; do not write into the repository.
"""


def run(inputs):
    raise NotImplementedError("call the entry point with values from `inputs`")
