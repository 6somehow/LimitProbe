import sys
from pathlib import Path


def repo_root():
    for entry in sys.path:
        if not entry:
            continue
        root = Path(entry)
        if (root / "speedup" / "flexgen" / "infinigen" / "flex_opt.py").is_file():
            return root
    raise RuntimeError("InfiniGen repository root not found on sys.path")


def ensure():
    root = repo_root()
    for sub in ("speedup/flexgen", "speedup/infinigen"):
        p = str(root / sub)
        if p not in sys.path:
            sys.path.append(p)
    return root
