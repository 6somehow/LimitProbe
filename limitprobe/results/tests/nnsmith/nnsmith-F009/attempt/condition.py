"""Region condition for the harness's branch effect.

The step-4 condition `carry and max(left_size, right_size) >= ARITH_MAX_WIDTH` describes the
fallback (carry extension omitted), which is the negation of the guard at line 74. The harness's
path_hook effect is the guard body being taken, so the predicate states exactly that decision
using the real local variables at the target line.
"""


def predicate(locals):
    carry = locals.get("carry")
    left_size = locals.get("left_size")
    right_size = locals.get("right_size")
    max_width = locals.get("ARITH_MAX_WIDTH")
    return bool(carry and max(left_size, right_size) < max_width)
