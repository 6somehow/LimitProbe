"""Toy 'research prototype' used by tests: one of each signal the extractor knows."""
import importlib.util

_cache = None


def dense_attention(x):
    return x


def sparse_kernel(x, block_size):
    assert block_size in {32, 64, 128}, "kernel block sizes"
    return x


def sparse_attention(x, seq_len, block_size=128, budget=None):
    assert seq_len > 0
    if seq_len < 2 * block_size:
        return dense_attention(x)
    global _cache
    if _cache is None:
        _cache = block_size
    n_blocks = seq_len // 128
    mask = x < budget
    return sparse_kernel(x, block_size)


if importlib.util.find_spec("fast_ext") is not None:
    fast = True
else:
    fast = False


class Searcher:
    def __init__(self, max_iter=100):
        self.max_iter = max_iter

    def _step(self, x, lr):
        assert lr > 0, "learning rate must be positive"
        return x

    def search(self, x, lr, timeout_ms=None):
        if timeout_ms is not None and timeout_ms <= 0:
            return dense_attention(x)
        return self._step(x, lr)
