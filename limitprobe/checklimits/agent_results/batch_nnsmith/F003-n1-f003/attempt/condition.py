"""Region condition for `except InternalError as e:` at nnsmith/cli/fuzz.py:179.

At the line event of an `except ... as e:` header, the bound name `e` is not yet in
frame.f_locals (it is bound only when the handler body starts), so the harness cannot
evaluate `isinstance(e, InternalError)` from the captured locals.  The exception being
matched is available from sys.exc_info() during that line event; this predicate applies
the Region's own expression to that real exception object.
"""

import sys

from nnsmith.error import InternalError


def predicate(locals):
    exc = sys.exc_info()[1]
    return exc is not None and isinstance(exc, InternalError)
