import sys
from pathlib import Path


def _repo_root():
    for entry in sys.path:
        base = Path(entry)
        if (base / "speedup" / "flexgen" / "flexgen" / "__init__.py").is_file():
            return base
    raise ImportError("cannot locate the InfiniGen repository root on sys.path")


_repo = _repo_root()
__path__ = [
    str(_repo / "speedup" / "flexgen" / "flexgen"),
    str(_repo / "speedup" / "flexgen"),
]
