from pathlib import Path

import _clpaths

_root = _clpaths.ensure()
for _sub in ("speedup/flexgen/infinigen", "speedup/infinigen/infinigen"):
    _pkg = str(Path(_root) / _sub)
    if _pkg not in __path__:
        __path__.append(_pkg)
