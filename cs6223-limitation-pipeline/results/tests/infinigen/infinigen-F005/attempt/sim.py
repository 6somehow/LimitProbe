"""Native stand-in for the offline OPT tokenizer used by run_flexgen."""


class _Encoded(dict):
    @property
    def input_ids(self):
        return self["input_ids"]


class _Tokenizer(dict):
    def __init__(self):
        super().__init__({"vocab_size": 50257, "pad_id": 1})

    def __call__(self, prompts, padding=None, max_length=None):
        n = int(max_length or 8)
        rows = []
        masks = []
        for prompt in prompts:
            raw = str(prompt)[: max(1, n * 4)].encode("utf-8", "ignore")
            ids = [(byte % (self["vocab_size"] - 1)) + 1 for byte in raw[:n]]
            if padding == "max_length" and len(ids) < n:
                ids = ids + [self["pad_id"]] * (n - len(ids))
            rows.append(ids)
            masks.append([1] * len(ids))
        return _Encoded(input_ids=rows, attention_mask=masks)


def tokenizer(*args, **kwargs):
    return _Tokenizer()
