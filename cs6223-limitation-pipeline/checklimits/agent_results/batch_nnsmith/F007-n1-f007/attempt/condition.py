"""Region B034 condition: loss_fn.dispatch(type(op)) is not None.

The harness's expression evaluator has no `type` in its safe builtins, so the
condition is evaluated here on the real target-line locals instead.
"""

from nnsmith.materialize.torch.numeric import loss_fn


def predicate(locals):
    op = locals.get("op")
    return loss_fn.dispatch(type(op)) is not None
