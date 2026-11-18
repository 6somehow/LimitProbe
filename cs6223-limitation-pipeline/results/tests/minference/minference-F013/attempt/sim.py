"""CPU stand-ins for the GPU-only pieces on the way to the F013 target.

The target itself (`assert Lk in {16, 32, 64, 128}`) only looks at the head
dimension.  Two accelerator pieces are on the path from the official entry:

* `minference.cuda.convert_vertical_slash_indexes` is a CUDA extension that is
  not shipped in this checkout; `convert_vertical_slash_indexes` below is a
  literal CPU port of `csrc/vertical_slash_index.cu` (same loops, same output
  tensors).
* `torch.arange(..., device="cuda")` is used at import time and in `dialted`;
  `cpu_arange` runs the same range on CPU.

`CpuKernelLauncher` is used only after the target line, so the runs that pass
the assertion the original way do not try to launch Triton on a CPU-only host.
"""

import torch

_ORIG_ARANGE = torch.arange


def cpu_arange(*args, **kwargs):
    device = kwargs.get("device")
    if device is not None and str(device) != "cpu":
        kwargs["device"] = "cpu"
    return _ORIG_ARANGE(*args, **kwargs)


def convert_vertical_slash_indexes(
    seqlens,
    vertical_indexes,
    slash_indexes,
    context_size,
    block_size_M,
    block_size_N,
):
    """CPU port of csrc/vertical_slash_index.cu::convert_vertical_slash_indexes."""
    batch_size = int(slash_indexes.shape[0])
    num_heads = int(slash_indexes.shape[1])
    nnz_slash = int(slash_indexes.shape[2])
    nnz_vertical = int(vertical_indexes.shape[2])
    num_rows = (int(context_size) + int(block_size_M) - 1) // int(block_size_M)

    opts = {"dtype": seqlens.dtype}
    block_count = torch.zeros((batch_size, num_heads, num_rows), **opts)
    block_offset = torch.zeros((batch_size, num_heads, num_rows, nnz_slash), **opts)
    column_count = torch.zeros((batch_size, num_heads, num_rows), **opts)
    column_index = torch.zeros((batch_size, num_heads, num_rows, nnz_vertical), **opts)

    seq = seqlens.detach().to("cpu", torch.int64).reshape(-1).tolist()
    vert = vertical_indexes.detach().to("cpu", torch.int64).tolist()
    slash = slash_indexes.detach().to("cpu", torch.int64).tolist()
    bc = block_count.numpy()
    bo = block_offset.numpy()
    cc = column_count.numpy()
    ci = column_index.numpy()

    for b in range(batch_size):
        seqlen = int(seq[b])
        for h in range(num_heads):
            vrow = vert[b][h]
            srow = slash[b][h]
            for m in range(num_rows):
                start_m = m * int(block_size_M)
                if start_m >= seqlen:
                    continue
                end_m = start_m + int(block_size_M)

                tmp_col = 0
                tmp_blk = 0

                def save_blocks(range_start, range_end):
                    nonlocal tmp_blk
                    idx = range_start
                    while idx < range_end:
                        if tmp_blk < nnz_slash:
                            bo[b, h, m, tmp_blk] = idx
                        tmp_blk += 1
                        idx += int(block_size_N)

                sv = 0
                ss = 0
                v_idx = int(vrow[sv])
                sv += 1
                s_idx = int(srow[ss])
                ss += 1

                while s_idx >= end_m:
                    if ss < len(srow):
                        s_idx = int(srow[ss])
                        ss += 1
                    else:
                        s_idx = -(10**9)
                        break

                s_idx = max(end_m - s_idx, int(block_size_M))
                range_start = s_idx - int(block_size_M)
                range_end = s_idx

                while True:
                    if v_idx < range_end:
                        if v_idx < range_start:
                            if tmp_col < nnz_vertical:
                                ci[b, h, m, tmp_col] = v_idx
                            tmp_col += 1
                        if sv < len(vrow):
                            v_idx = int(vrow[sv])
                            sv += 1
                        else:
                            v_idx = end_m + int(block_size_M)
                    else:
                        if ss < len(srow):
                            s_idx = max(end_m - int(srow[ss]), int(block_size_M))
                            ss += 1
                        else:
                            save_blocks(range_start, range_end)
                            break
                        if s_idx > range_end + int(block_size_M):
                            save_blocks(range_start, range_end)
                            range_start = s_idx - int(block_size_M)
                            range_end = s_idx
                        elif s_idx > range_end:
                            range_end += int(block_size_M)

                bc[b, h, m] = tmp_blk
                cc[b, h, m] = tmp_col

    return block_count, block_offset, column_count, column_index


def cpu_block_sparse_attention(query, key, value, topk=None, **kwargs):
    """Unused on the dilated path; a plain CPU attention fallback for import."""
    scale = query.shape[-1] ** -0.5
    scores = torch.matmul(query, key.transpose(-2, -1)) * scale
    q_len = query.shape[-2]
    mask = torch.tril(torch.ones(q_len, q_len, dtype=torch.bool, device=query.device))
    scores = scores.masked_fill(~mask, float("-inf"))
    weights = torch.softmax(scores, dim=-1)
    return torch.matmul(weights, value)


class CpuKernelLauncher:
    """`kernel[grid](...)` shaped launcher that does nothing (post-target only)."""

    def __getitem__(self, grid):
        def launch(*args, **kwargs):
            return None

        return launch


def cpu_attn_launcher():
    return CpuKernelLauncher()
