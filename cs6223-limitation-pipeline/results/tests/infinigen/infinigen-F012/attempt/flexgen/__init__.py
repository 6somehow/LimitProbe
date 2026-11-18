from pathlib import Path

import _clpaths

_root = _clpaths.ensure()
_pkg = str(Path(_root) / "speedup" / "flexgen" / "flexgen")
if _pkg not in __path__:
    __path__.append(_pkg)
