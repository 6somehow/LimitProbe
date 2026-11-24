import sys
from pathlib import Path

import numpy as np

def _add_repo_paths():
    for entry in list(sys.path):
        base = Path(entry)
        if (base / "speedup" / "flexgen" / "infinigen" / "pytorch_backend.py").exists():
            sys.path.insert(0, str(base / "speedup" / "infinigen"))
            sys.path.insert(0, str(base / "speedup" / "flexgen"))
            return
    raise RuntimeError("cannot locate the pinned repository on sys.path")

_add_repo_paths()

from infinigen.pytorch_backend import (  # noqa: E402
    DeviceType,
    TorchDevice,
    TorchMixedDevice,
    fix_recursive_import,
    general_copy,
)

fix_recursive_import()


def run(inputs):
    index_step = inputs["index_step"]
    step = None if index_step == 0 else index_step

    seq, seg, dim = 4, 2, 3
    cpu = TorchDevice("cpu")
    mixed = TorchMixedDevice([cpu])
    src = cpu.allocate((seq, seg, dim), np.float16, pin_memory=False)
    dst = mixed.allocate((seq, seg, dim), np.float16, [seg], pin_memory=False)

    src_indices = (slice(0, seq, step), slice(0, seg), slice(0, dim))
    dst_indices = (slice(0, seq), slice(0, seg), slice(0, dim))
    general_copy(dst, dst_indices, src, src_indices)
