from . import kernels
from .kernels import Child, pool


def helper(q, k, block_size, interleave):
    if not interleave:
        avg = pool(k, block_size)
    else:
        avg = pool(k, block_size, mode="max")
    return avg


def attention(q, k, block_size=64, interleave=False, args=()):
    batch, q_len, heads, head_dim = q.shape
    batch, k_len, kv_heads, head_dim = k.shape
    assert head_dim in {16, 32, 64}
    assert block_size in {16, 32, 64}
    if q_len == 1:
        return q
    out = helper(q, k, block_size, interleave)
    kernels.scale(q, heads)
    kernels.scale(*args)
    runner = Child()
    runner.run(out)
    out.finish(1)
    return out


class Tensorish:
    def finish(self, code):
        assert code == 0
        return code


def unrelated(x):
    return attention(x, x)
