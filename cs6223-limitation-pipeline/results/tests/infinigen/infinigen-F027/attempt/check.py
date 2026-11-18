def check_selected_layers(fn):
    expected = {
        0: [],
        1: [0],
        2: [1],
        3: [1],
        4: [1],
        5: [1],
    }
    for n, want in expected.items():
        got = list(fn(n))
        if got != want:
            return {
                "ok": False,
                "kind": "symbolic",
                "detail": f"selected_layers({n}) returned {got!r}, expected {want!r}",
            }
    got = list(fn(2, 5))
    if got != [2, 3, 4]:
        return {
            "ok": False,
            "kind": "symbolic",
            "detail": f"selected_layers(2, 5) returned {got!r}, expected [2, 3, 4]",
        }
    return {
        "ok": True,
        "kind": "symbolic",
        "detail": "returns only the interior layer index for n >= 2 and delegates other range signatures",
    }
