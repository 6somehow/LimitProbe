"""Fixture for codeside/callgraph.py and codeside/chain_bind.py: checks in callees."""


def pool(x, kernel_size, mode="avg"):
    b, n, h, d = x.shape
    assert d in {16, 32, 64}
    assert kernel_size in {16, 32, 64, 128}
    if mode == "max":
        return x
    return x


def scale(t, factor):
    t = t * 2
    assert factor > 0
    return t


class Base:
    def run(self, x):
        return self.step(x)

    def step(self, x):
        return x


class Child(Base):
    def step(self, x):
        assert x is not None
        return x


def make_hook(limit):
    def hook(v):
        assert v < limit
        return v
    return hook
