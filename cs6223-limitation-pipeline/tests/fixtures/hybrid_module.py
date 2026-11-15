"""Fixture for route B: things the static route alone cannot follow or does not flag."""
import torch


def skew(x):
    return x


class Base:
    def helper(self, x, mode):
        assert mode in {"a", "b"}, "mode"
        return x


class Unrelated:
    def helper(self, x, mode):
        assert mode == "never", "not on the path"
        return x


class Impl(Base):
    def run(self, x, mode):
        return Base.helper(self, x, mode)


def internal(x):
    y = [x]
    assert isinstance(y, list)
    return y


def top(x, mode, warm=False):
    assert x is not None
    if warm:
        x = skew(x)
    internal(x)
    torch.save(x, "f")
    return Impl().run(x, mode)
