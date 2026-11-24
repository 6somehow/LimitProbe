"""CPU stand-ins for the two GPU-only pieces the entry needs on this host.

* ``arange``: the repository module runs ``torch.arange(64, device="cuda")`` at import
  time.  The stand-in keeps the exact values and only redirects a requested CUDA device
  to the CPU, because the test host has no CUDA build of torch.
* ``convert_vertical_slash_indexes``: a plain-Python port of the loop in
  ``csrc/vertical_slash_index.cu``.  The negative run reaches it only after the target
  decision has been recorded; without it the missing extension turns the run into an
  import error instead of a post-target result.
"""
from __future__ import annotations

import torch

if not hasattr(torch, "_checklimits_real_arange"):
    torch._checklimits_real_arange = torch.arange


def arange(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and "cuda" in str(device).lower():
        kwargs["device"] = "cpu"
    return torch._checklimits_real_arange(*args, **kwargs)


def _save_blocks(offset, range_start, range_end, block_size):
    out = []
    idx = range_start
    while idx < range_end:
        out.append(idx)
        idx += block_size
    return out


def convert_vertical_slash_indexes(seqlens, vertical_indexes, slash_indexes,
                                   context_size, block_size_M, block_size_N):
    v = vertical_indexes.to(torch.int64).reshape(vertical_indexes.shape[0],
                                                 vertical_indexes.shape[1], -1)
    s = slash_indexes.to(torch.int64).reshape(slash_indexes.shape[0],
                                              slash_indexes.shape[1], -1)
    batch, heads = s.shape[0], s.shape[1]
    nnz_v, nnz_s = v.shape[2], s.shape[2]
    rows = (context_size + block_size_M - 1) // block_size_M
    block_count = torch.zeros(batch, heads, rows, dtype=torch.int32)
    block_offset = torch.zeros(batch, heads, rows, nnz_s, dtype=torch.int32)
    column_count = torch.zeros(batch, heads, rows, dtype=torch.int32)
    column_index = torch.zeros(batch, heads, rows, nnz_v, dtype=torch.int32)
    for b in range(batch):
        seqlen = int(seqlens[b])
        for h in range(heads):
            vert = [int(x) for x in v[b, h].tolist()]
            slash = [int(x) for x in s[b, h].tolist()]
            for row in range(rows):
                start_m = row * block_size_M
                if start_m >= seqlen:
                    continue
                end_m = start_m + block_size_M
                col_cnt = blk_cnt = 0
                si = vi = 0
                v_idx = vert[vi]
                vi += 1
                s_idx = slash[si]
                si += 1
                while s_idx >= end_m:
                    s_idx = slash[si]
                    si += 1
                s_idx = max(end_m - s_idx, block_size_M)
                range_start, range_end = s_idx - block_size_M, s_idx
                cols, offs = [], []
                while True:
                    if v_idx < range_end:
                        if v_idx < range_start:
                            cols.append(v_idx)
                            col_cnt += 1
                        if vi < nnz_v:
                            v_idx = vert[vi]
                            vi += 1
                        else:
                            v_idx = end_m + block_size_M
                    else:
                        if si < nnz_s:
                            s_idx = max(end_m - slash[si], block_size_M)
                            si += 1
                        else:
                            offs.extend(_save_blocks(None, range_start, range_end, block_size_N))
                            blk_cnt = len(offs)
                            break
                        if s_idx > range_end + block_size_M:
                            offs.extend(_save_blocks(None, range_start, range_end, block_size_N))
                            blk_cnt = len(offs)
                            range_start = s_idx - block_size_M
                            range_end = s_idx
                        elif s_idx > range_end:
                            range_end += block_size_M
                block_count[b, h, row] = blk_cnt
                column_count[b, h, row] = col_cnt
                for i, val in enumerate(offs[:nnz_s]):
                    block_offset[b, h, row, i] = val
                for i, val in enumerate(cols[:nnz_v]):
                    column_index[b, h, row, i] = val
    return block_count, block_offset, column_count, column_index
