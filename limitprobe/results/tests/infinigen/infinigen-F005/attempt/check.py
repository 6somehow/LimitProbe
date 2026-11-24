"""Invariant check for the tokenizer stand-in used before the target."""

VOCAB_SIZE = 50257


def check_tokenizer(sim):
    try:
        tok = sim("facebook/opt-30b", padding_side="left")
        short = tok(["hello"], padding="max_length", max_length=8)
        long = tok(["hello"], padding="max_length", max_length=16)
        short_ids = short.input_ids
        long_ids = long.input_ids
    except Exception as exc:
        return {
            "ok": False,
            "detail": f"tokenizer stand-in is not callable/usable: {type(exc).__name__}: {exc}",
            "kind": "numeric",
        }

    expected = [105, 102, 109, 109, 112, 1, 1, 1]
    ok = (
        isinstance(short_ids, list)
        and len(short_ids) == 1
        and short_ids[0] == expected
        and len(long_ids) == 1
        and len(long_ids[0]) == 16
        and long_ids[0][:8] == expected
        and long_ids[0][8:] == [1] * 8
        and all(isinstance(x, int) and 1 <= x < VOCAB_SIZE for x in long_ids[0])
        and tok(["hello"], padding="max_length", max_length=8).input_ids == short_ids
    )
    return {
        "ok": bool(ok),
        "detail": f"short={short_ids!r} long_prefix={long_ids[0][:8]!r}",
        "kind": "numeric",
    }
