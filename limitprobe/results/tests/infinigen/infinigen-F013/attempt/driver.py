"""Driver for infinigen-F013 (fx_opt.py:799, OptLM.load_cache).

The target is ``if j not in self.attn_layer[2:]:`` inside ``OptLM.load_cache``.  Step 4 reports
``call_chain_status = not_found``: there is no static path from the declared entry
(``TorchDevice.mha``) to this method (it is driven by the generation loop).  The driver therefore
calls the repository's real ``OptLM.load_cache`` method directly on an instance whose state
(``attn_layer`` for ``sep_layer=True``) is built exactly as ``OptLM.__init__`` builds it:

    layers = [InputEmbed]; for i in range(num_hidden_layers): [SelfAttention, MLP]
    attn_layer = [1, 3, 5, ...]           # index of each SelfAttention layer
    num_layers = 2 * num_hidden_layers + 2

Every value the target decision depends on (``j`` and ``self.attn_layer``) is supplied from the
harness ``inputs``; no repository code is replaced.  The stream attribute the repository's
``load_cache`` enters is a plain dummy object, which the CPU torch build accepts without touching
any accelerator (it only stores the object).
"""

import random
import sys
from pathlib import Path

_REL_FLEX_OPT = Path("speedup") / "flexgen" / "infinigen" / "flex_opt.py"


def _repo_root():
    for p in list(sys.path):
        try:
            q = Path(p or ".").resolve()
        except OSError:
            continue
        if (q / _REL_FLEX_OPT).exists():
            return q
    raise RuntimeError("repository root with speedup/flexgen/infinigen/flex_opt.py not on sys.path")


_ROOT = _repo_root()
for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _sp = str(_ROOT / _sub)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

import torch  # noqa: E402

from infinigen.flex_opt import OptLM  # noqa: E402


class _DummyStream:
    """Placeholder for a device stream: the CPU torch build only stores it on enter."""


class _FakeLayer:
    """Stand-in for the layer object touched *after* the target decision (line 800)."""

    def __init__(self):
        self.calls = 0

    def load_cache(self, cache_home, cache_read_buf, i):
        self.calls += 1


class _FakeLM:
    """Object carrying the OptLM state the target method reads."""


def run(inputs):
    random.seed(int(inputs["seed"]))
    torch.manual_seed(int(inputs["seed"]))

    n = int(inputs["num_hidden_layers"])
    num_layers = 2 * n + 2
    num_gpu_batches = int(inputs["num_gpu_batches"])
    i = int(inputs["i"])
    j = int(inputs["j"])
    k = int(inputs["k"])
    overlap = bool(inputs["overlap"])

    lm = _FakeLM()
    lm.attn_layer = [1 + 2 * t for t in range(n)]
    lm.num_layers = num_layers
    lm.num_gpu_batches = num_gpu_batches
    lm.execute_gen_len = int(inputs["execute_gen_len"])
    lm.load_cache_stream = _DummyStream()
    lm.layers = [_FakeLayer() for _ in range(num_layers)]
    lm.cache_home = [[object() for _ in range(num_gpu_batches)] for _ in range(num_layers)]
    lm.cache_read_buf = [[object() for _ in range(num_gpu_batches)] for _ in range(num_layers)]

    OptLM.load_cache(lm, i, j, k, overlap=overlap)
    return None
