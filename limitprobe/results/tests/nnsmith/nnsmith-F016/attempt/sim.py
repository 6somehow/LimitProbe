"""Post-target stand-in: stop the expensive operator-narrowing stage.

``auto_opset`` is the first call below the target decision on both sides.  Running the real
implementation would enumerate and compile every operator (slow, and unrelated to the branch
we are checking).  Instead this stand-in calls a real repository validation routine that fails
fast, so the post-target exception is raised inside the pinned repository and therefore has a
checkout-independent location.  It is touched only after line 31 has already decided, so it
cannot influence the verdict-bearing branch observation.
"""

from nnsmith.materialize import Model


def post_target_stop(*args, **kwargs):
    Model.init(None)  # raises ValueError inside the repository
    raise AssertionError("unreachable: Model.init(None) always raises")
