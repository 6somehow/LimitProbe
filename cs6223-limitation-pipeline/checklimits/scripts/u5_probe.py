"""U5 probe: can F07 / F01 reach flex_prefill_attention.py lines 1824 / 1836 on CPU?

Not part of the harness. Run from anywhere:
  python scripts/u5_probe.py [--stub-downstream]

--stub-downstream  replace functions that run AFTER the two asserts (flash_attn_func,
                   get_active_blocks, triton_block_wise_attention) so the counter-example
                   returns normally. Without it the counter-example runs the real code
                   and fails later on CPU (the failure line is printed).
The repository is never modified: patches are applied to the imported module object.
"""
import argparse
import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPO = os.path.join(ROOT, "third_party", "FlexPrefill")
TARGET = os.path.join(REPO, "flex_prefill", "ops", "flex_prefill_attention.py")

ap = argparse.ArgumentParser()
ap.add_argument("--stub-downstream", action="store_true")
args = ap.parse_args()

sys.dont_write_bytecode = True
sys.path.insert(0, REPO)

import torch  # noqa: E402
import flex_prefill.ops.flex_prefill_attention as m  # noqa: E402

if args.stub_downstream:
    m.flash_attn_func = lambda q, k, v, **kw: q
    m.get_active_blocks = lambda *a, **k: [[None]]
    m.triton_block_wise_attention = lambda q, *a, **k: q


def call(batch_size=1, q_len=4096, k_len=None, heads=2, head_dim=128, block_size=128):
    k_len = q_len if k_len is None else k_len
    g = torch.Generator().manual_seed(0)
    q = torch.randn(batch_size, q_len, heads, head_dim, generator=g, dtype=torch.bfloat16)
    k = torch.randn(batch_size, k_len, heads, head_dim, generator=g, dtype=torch.bfloat16)
    v = torch.randn(batch_size, k_len, heads, head_dim, generator=g, dtype=torch.bfloat16)
    try:
        m.flex_prefill_attention(q, k, v, gamma=0.9, tau=0.1, block_size=block_size)
        return "returned normally", None
    except BaseException as e:  # noqa: BLE001
        tb = traceback.extract_tb(e.__traceback__)
        last = tb[-1]
        where = f"{os.path.relpath(last.filename, REPO)}:{last.lineno}"
        return f"{type(e).__name__}: {str(e)[:70]}", where


cases = [
    ("F07 positive  batch_size=2", dict(batch_size=2), "flex_prefill/ops/flex_prefill_attention.py:1824"),
    ("F07 negative  batch_size=1", dict(batch_size=1), None),
    ("F01 positive  q_len=4096,k_len=8192", dict(q_len=4096, k_len=8192), "flex_prefill/ops/flex_prefill_attention.py:1836"),
    ("F01 negative  q_len=4096,k_len=4096", dict(q_len=4096, k_len=4096), None),
]
bad = 0
print(f"torch {torch.__version__}  GPU_NAME={m.GPU_NAME!r}  stub_downstream={args.stub_downstream}")
for name, kw, expect in cases:
    what, where = call(**kw)
    if expect:
        ok = where == expect and what.startswith("AssertionError")
    else:
        ok = where not in ("flex_prefill/ops/flex_prefill_attention.py:1824",
                           "flex_prefill/ops/flex_prefill_attention.py:1836")
    bad += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:40s} -> {what} @ {where}")
sys.exit(1 if bad else 0)
