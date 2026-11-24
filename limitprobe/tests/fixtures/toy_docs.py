"""Toy module used by the 3b tests."""


def kernel(block_size):
    """Only block sizes 32 and 64 are supported."""
    # block sizes above 64 are untested
    # and may run out of memory
    return block_size
