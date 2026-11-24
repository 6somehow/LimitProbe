"""CPU port of torch/csrc `convert_vertical_slash_indexes` (csrc/vertical_slash_index.cu).

The kernel returns int32 tensors. We return float32 tensors holding the same integer values so the
harness corruption pass (scale/negate/zero only touch floating tensors) can observe the stand-in's
output. In this test the four tensors are only passed to `_triton_mixed_sparse_attention`, whose
first statements are the asserted shape checks; their values are never consumed before the target.
"""

import torch


def _save_blocks(out, range_start, range_end, block_size, cap):
    idx = range_start
    while idx < range_end and len(out) < cap:
        out.append(idx)
        idx += block_size


def convert_vertical_slash_indexes_cpu(seqlens, vertical_indexes, slash_indexes,
                                       context_size, block_size_M, block_size_N):
    assert int(block_size_M) == 64 and int(block_size_N) == 64
    batch, heads, nnz_s = slash_indexes.shape
    nnz_v = vertical_indexes.shape[2]
    num_rows = (int(context_size) + int(block_size_M) - 1) // int(block_size_M)

    seq = seqlens.detach().cpu().tolist()
    vi = vertical_indexes.detach().cpu().tolist()
    si = slash_indexes.detach().cpu().tolist()

    block_count = [[[0] * num_rows for _ in range(heads)] for _ in range(batch)]
    block_offset = [[[[0] * nnz_s for _ in range(num_rows)] for _ in range(heads)] for _ in range(batch)]
    column_count = [[[0] * num_rows for _ in range(heads)] for _ in range(batch)]
    column_index = [[[[0] * nnz_v for _ in range(num_rows)] for _ in range(heads)] for _ in range(batch)]

    for bb in range(batch):
        seqlen = int(seq[bb])
        for hh in range(heads):
            vlist = [int(x) for x in vi[bb][hh]]
            slist = [int(x) for x in si[bb][hh]]
            for rr in range(num_rows):
                start_m = rr * 64
                if start_m >= seqlen:
                    continue
                end_m = start_m + 64
                tmp_col, tmp_blk = [], []
                s = v = 0
                v_idx = vlist[v] if v < nnz_v else end_m + 64
                if v < nnz_v:
                    v += 1
                s_idx = slist[s] if s < nnz_s else end_m + 64
                if s < nnz_s:
                    s += 1
                while s_idx >= end_m and s < nnz_s:
                    s_idx = slist[s]
                    s += 1
                if s_idx >= end_m:
                    s_idx = end_m - 64
                s_idx = max(end_m - s_idx, 64)
                range_start, range_end = s_idx - 64, s_idx
                while True:
                    if v_idx < range_end:
                        if v_idx < range_start and len(tmp_col) < nnz_v:
                            tmp_col.append(v_idx)
                        if v < nnz_v:
                            v_idx = vlist[v]
                            v += 1
                        else:
                            v_idx = end_m + 64
                    else:
                        if s < nnz_s:
                            s_idx = max(end_m - slist[s], 64)
                            s += 1
                        else:
                            _save_blocks(tmp_blk, range_start, range_end, 64, nnz_s)
                            break
                        if s_idx > range_end + 64:
                            _save_blocks(tmp_blk, range_start, range_end, 64, nnz_s)
                            range_start, range_end = s_idx - 64, s_idx
                        elif s_idx > range_end:
                            range_end += 64
                block_count[bb][hh][rr] = len(tmp_blk)
                block_offset[bb][hh][rr][:len(tmp_blk)] = tmp_blk
                column_count[bb][hh][rr] = len(tmp_col)
                column_index[bb][hh][rr][:len(tmp_col)] = tmp_col

    return (torch.tensor(block_count, dtype=torch.float32),
            torch.tensor(block_offset, dtype=torch.float32),
            torch.tensor(column_count, dtype=torch.float32),
            torch.tensor(column_index, dtype=torch.float32))
