def selected_layers(*args):
    if len(args) != 1:
        return list(range(*args))
    n = args[0]
    if not isinstance(n, int) or isinstance(n, bool):
        return list(range(*args))
    if n <= 0:
        return []
    if n == 1:
        return [0]
    return [1]
