# Environment record (P0)

Date: 2026-11-11. Interpreter: `/home/somehow6/miniconda3/envs/findlimit/bin/python` (3.14.10). Do not use venv or uv.

## Installed packages (`findlimit`)

| Package | Version | Reason |
|---|---|---|
| pydantic | 2.14.3 | `models.py` (pydantic v2); `schema.models` also depends on it |
| pytest | 9.2.0 | Tests |
| coverage | 7.17.2 | P1b coverage measurement (the current tracer does not depend on it) |
| torch | 2.15.0+cpu | FlexPrefill import and tensor construction. Source: `--index-url https://download.pytorch.org/whl/cpu`. FlexPrefill's extra_requirements pins 2.4.0, which has no wheel for 3.14; the latest available CPU version was used |
| einops | 0.8.2 | import at line 22 of `flex_prefill_attention.py` |
| transformers | 5.22.2 | `flex_prefill/__init__.py` imports `PreTrainedModel` through `modules/patch.py`; `flex_prefill_attention.py` uses `is_flash_attn_2_available` at line 1782. The repository pins 4.44.0, which cannot be installed on 3.14; the latest version was used |
| triton | 3.9.0 | `import triton` at line 20 of `flex_prefill_attention.py`. The repository pins 3.0.0. 3.9.0 has a cp314 wheel and imports successfully, so no test double is needed |

Dependencies brought in by these packages (numpy 2.5.4, huggingface-hub 2.4.0, tokenizers 0.23.3, safetensors, tqdm, pyyaml, regex, typer, etc.) are not listed separately; use `pip list` for the complete list.

Not installed: `flash_attn` (requires CUDA). Therefore `flash_attn_func = triton_flash_attention` (lines 1782–1786).

## U4: Can FlexPrefill be imported in `findlimit`?

Conclusion: **yes**. `import flex_prefill.ops.flex_prefill_attention` succeeds and `GPU_NAME` is `None`. The repository was not modified; `git status` in `third_party/FlexPrefill` is empty.

The failures were, in order (each was resolved by installing a package):

1. `import torch` (flex_prefill_attention.py:19): not installed → installed torch CPU.
2. `from transformers import PreTrainedModel` (modules/patch.py:23): importing `flex_prefill.ops.*` first executes `flex_prefill/__init__.py`, which imports `modules.patch`. Not installed → installed transformers.
3. `import triton` (flex_prefill_attention.py:20): not installed → installed triton 3.9.0.

The versions differ from the repository pins (torch 2.4.0, transformers 4.44.0, triton 3.0.0). This deviation can affect F05, F06, F03 and F02 (which involve kernel and transformers internal behavior); it does not affect F07 or F01 because both assertions precede any kernel or transformers call.

## U5: Can F07 and F01 reach lines 1824 and 1836?

Script: `scripts/u5_probe.py`. Uses random bfloat16 tensors (seed 0), 2 heads, head_dim=128, block_size=128, `gamma=0.9`, `tau=0.1`.

| Case | Result |
|---|---|
| F07 positive `batch_size=2` | `AssertionError: only support batch size 1 for now`, at `flex_prefill_attention.py:1824` |
| F07 negative `batch_size=1` | No exception at 1824; continues and raises `RuntimeError: 0 active drivers` at triton's `runtime/driver.py:20` (no GPU) |
| F01 positive `q_len=4096, k_len=8192` | `AssertionError` (no message), at `flex_prefill_attention.py:1836` |
| F01 negative `q_len=4096, k_len=4096` | No exception at 1836; also raises `RuntimeError` at triton's `driver.py:20` |

With `--stub-downstream` (replacing `flash_attn_func`, `get_active_blocks`, and `triton_block_wise_attention` on the imported module object), both negative cases return normally.

Symbols that need replacement: **F07 and F01 do not require any symbols to be replaced**.

- `triton`: the real wheel imports; no stub is needed. A stub module was tried, but `transformers` checks the triton version and fails to import, so it was not used.
- `GPU_NAME`: value is `None`. `.lower()` is used only in `get_num_warps_stages` (called from lines 266, 553, 628 and 1276, all inside kernel wrapper functions), after both assertions. **Not on the path**.
- `flash_attn_func` / `get_active_blocks` / `triton_block_wise_attention`: after both assertions. **Not on the path**. Replacement is needed only if the negative case must return normally.

See "Contradictions and ambiguities" in the final report for handling the negative cases: they crash after the target line because there is no GPU.

## Relay

Binding outbound traffic only to the eth0 source address times out (the default route uses eth1, and packets with an eth0 source address are dropped). `SO_BINDTODEVICE` is required (root is not required on this machine). Implemented in `relay.py` and tested: binding only the address timed out after 10 seconds; binding the device connected in 0.04 seconds.

## Python 3.11 venv (repository-pinned versions, evening of 2026-11-11)

For the F07/F01 negative cases to finish the downstream code, the repository-pinned triton 3.0.0 is needed (the `block pointer` API was removed in triton 3.9, and the 3.9 interpreter raises `NotImplementedError` directly). These versions have no 3.14 wheels, so a temporary venv was created:

- Location: `checklimits/scratch/venv311/` (git ignored, can be deleted at any time); script: `scripts/make_venv311.sh`.
- The interpreter comes from Python 3.11.16 in the conda environment `ravel`; it is used only to create the venv, without modifying that environment.
- Packages: torch 2.4.0+cpu, numpy 1.26.4, triton 3.0.0, transformers 4.44.0, einops 0.8.0, pydantic 2.14.3 (the child process must import `checklimits.models`).
- The attempt's `manifest.json` specifies it with `"python": "scratch/venv311/bin/python"`. `findlimit` (3.14) remains the harness interpreter.
- 3.11 has no `sys.monitoring`; the child automatically switches to the `sys.settrace` backend (`tracer.SettraceTracer`). Both backends run the same tests with consistent results.

### Tried but unusable: `TRITON_INTERPRET=1`

Running the real kernel directly in the venv using triton's CPU interpreter (q_len=512): `get_active_blocks` and `triton_block_wise_attention` return (computational ratio 0.625), but the process randomly aborts around exit with `corrupted size vs. prev_size` / `double free` (nonzero exit in 4 of 4 runs; faulthandler points to the interpreter call in `triton_block_wise_attention`). Heap corruption cannot be used as a source of evidence, so CPU test doubles were used instead:

| Replaced symbol | Test double | Category | Weight |
|---|---|---|---|
| `triton_bnhd_pool` | `sim.py::bnhd_pool`, torch-only avg pool, dividing the last block by its actual length | independent_native | 0.75 |
| `triton_block_wise_attention` | `sim.py::block_wise_attention`, converts `list[list[Tensor]]` to a tensor and calls the repository's `torch_block_wise_attention` | repo_reference | 0.9 |

`get_active_blocks` (torch only) runs the real code. Both doubles are called after the target line, so neither is on the path (`s_mock = 1 − 0.05×2 = 0.9`). The scale is reduced to 1/8 (F07: q_len 512; F01: q_len 512 / k_len 1024 versus 512); the form's `design.scale` records the reason and the invariance argument. The positive case stops at the target line, so the harness also reruns it at full witness scale (4096 / 8192) as a scale check.

## Harness services needed for the defect list (2026-11-11)

| Service | Purpose | Child processes (F07, `n_rep=5`) |
|---|---|---|
| Main run | One process each for positive and negative cases, with tracer | 2 |
| Run without tracer | D7 | 2 |
| Repeats | D8, 4 additional rounds of positive and negative cases | 8 |
| Boundary probe | D5, D10, run 4 inputs in one process, stopping at the target decision | 1 |
| Mutation | D3, one process per mutant (one positive and one negative input) | 5 |
| Replay | D9, fresh checkout and fresh attempt copy | 2 |

A full F07 run takes about 31 seconds (importing torch 2.4.0 in the venv takes about 1 second). `--fast` runs only the main run; the other defeaters remain `open`.
`git clone --local` fails across filesystems because hard links fail; replay was changed to use `--no-hardlinks` (found in unit tests).

## Packages added after merging `wanting/step4-findings` (2026-11-11)

| Package | Version | Reason |
|---|---|---|
| z3-solver | 5.4.1.0 | The merged `codeside/scope_check.py` needs it at import; repository `pyproject.toml` lists it as an optional `solver` dependency. Only needed to run the other side's tests |
| rank-bm25 | See `pip list` | Required by the merged `codeside/doc_index.py`; listed as an optional `verify` dependency. Same reason as above |

Neither is used by `checklimits`. After the merge, all of the other side's `tests/` passed (2 skipped).
