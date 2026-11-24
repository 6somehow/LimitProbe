"""Driver: construct OptLM with the policy percentages from `inputs`.

The Region target is the bare `raise NotImplementedError()` inside OptLM.__init__.  The
official call chain reported by step 4 starts at TorchDevice.mha, but static analysis found no
call chain from that runtime method to construction (chain status: not_found), so the driver
calls OptLM.__init__ directly and records that in execution.entry_reason.
"""

import os
import random
import sys
from pathlib import Path

import numpy as np
import torch

# Locate the pinned repository from the child's sys.path: checklimits.child inserts the repo
# directory first, so the same code also works in the clean-checkout replay copy.
_REPO = None
for _p in sys.path:
    _c = Path(_p)
    if (_c / "speedup" / "flexgen" / "flexgen").is_dir() and (_c / "speedup" / "infinigen" / "infinigen").is_dir():
        _REPO = str(_c)
        break
if _REPO is None:
    raise RuntimeError("cannot locate the InfiniGen repository on sys.path")

for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _p = os.path.join(_REPO, *_sub.split("/"))
    if _p not in sys.path:
        sys.path.insert(0, _p)

from flexgen.opt_config import OptConfig
from flexgen.pytorch_backend import TorchDevice
from flexgen.utils import ExecutionEnv
from infinigen.flex_opt import OptLM, Policy

random.seed(0)
np.random.seed(0)
torch.manual_seed(0)
torch.set_num_threads(1)

_DEVICE = TorchDevice("cpu")
_ENV = ExecutionEnv(gpu=_DEVICE, cpu=_DEVICE, disk=_DEVICE, mixed=_DEVICE)
_CONFIG = OptConfig(num_hidden_layers=1, max_seq_len=16, hidden_size=8, n_head=2,
                    input_dim=8, ffn_embed_dim=16, vocab_size=16)


def _policy(act_gpu_percent, act_cpu_percent):
    return Policy(
        gpu_batch_size=1,
        num_gpu_batches=1,
        w_gpu_percent=100,
        w_cpu_percent=0,
        cache_gpu_percent=100,
        cache_cpu_percent=0,
        act_gpu_percent=act_gpu_percent,
        act_cpu_percent=act_cpu_percent,
        overlap=False,
        sep_layer=True,
        pin_weight=False,
        cpu_cache_compute=False,
        attn_sparsity=1.0,
        compress_weight=False,
        comp_weight_config=None,
        compress_cache=False,
        comp_cache_config=None,
    )


def run(inputs):
    policy = _policy(inputs["act_gpu_percent"], inputs["act_cpu_percent"])
    try:
        OptLM(_CONFIG, _ENV, "/tmp/checklimits-f004-weights", policy, 0.2, 4, 400)
    except NotImplementedError:
        # The target exception: never swallow it.
        raise
    except Exception:
        # Construction continues after the target into GPU/disk-only code (CUDA streams and
        # weight loading) that cannot run on this CPU-only machine.  The negative case must
        # reach the target decision and finish, so failures strictly below the target are
        # ignored here.  A positive case cannot get here because line 710 raises first.
        return None
    return None
