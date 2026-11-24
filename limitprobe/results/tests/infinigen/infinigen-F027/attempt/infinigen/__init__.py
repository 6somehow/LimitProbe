import sys
from pathlib import Path


def _package_dir():
    for entry in sys.path:
        base = Path(entry)
        candidate = base / "speedup" / "infinigen" / "infinigen"
        if (candidate / "skewing_controller.py").is_file():
            return candidate
    raise ImportError("cannot locate the InfiniGen controller package on sys.path")


__path__ = [str(_package_dir())]
