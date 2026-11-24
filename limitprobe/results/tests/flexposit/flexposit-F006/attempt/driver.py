"""Driver: exercise the posit float32 guard in the pinned FlexPosit repository.

`flexposit.formats.posit_quantize` is the public quantizer (exported by the package) and the
first function of the step-4 call chain that does not coerce its input: `api.quantize` and
`core.search_channels` both call `.float()` on the weights before reaching it, so the guard at
formats.py:103 is not reachable through them.  The module is imported from the harness-provided
repository path at module level so the tracer sees the real, pinned code.
"""

import os
import sys

_REPO_DIR = next((p for p in sys.path if p.endswith(os.path.join("third_party", "FlexPosit"))), None)
if _REPO_DIR is not None:
    sys.path.insert(0, os.path.join(_REPO_DIR, "src"))

import torch

from flexposit.formats import posit_quantize

_DTYPES = {
    "float32": torch.float32,
    "float64": torch.float64,
}


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    dtype = _DTYPES[inputs["weight_dtype"]]
    x = torch.tensor([[-1.5, -0.25, 0.0, 0.25, 1.5, 3.0]], dtype=dtype)
    return posit_quantize(x, nsize=4, es=1, scale=1.0)
