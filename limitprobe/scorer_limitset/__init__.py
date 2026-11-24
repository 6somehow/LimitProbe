"""Reference-label coverage scoring, isolated from the generator."""
from .scoring import FakeJudge, Judge, RelayJudge, score

__all__ = ["FakeJudge", "Judge", "RelayJudge", "score"]
