"""Region condition for nnsmith-F022.

The harness's eval() of the original expression cannot resolve ``DType`` / ``self`` inside the
list comprehension (comprehension scopes read eval globals, not the supplied locals mapping),
so this predicate evaluates the same expression directly on the captured frame locals/globals.
"""


def predicate(locals):
    self = locals["self"]
    DType = locals["DType"]
    return all(DType.is_float(v.dtype) for _, v in self.net.input_like.items())
