# Pilot: FlexPrefill

- Paper: FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference, ICLR 2025 Oral ([arXiv 2502.20766](https://arxiv.org/abs/2502.20766))
- Repository: [bytedance/FlexPrefill](https://github.com/bytedance/FlexPrefill) @ `a24b27bf117fd6ad4ba34b0db82c598e7786fd59`
- Entry: `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention` (line 1791)

## Why choose it

- Official repository, with the same authors for paper and code; core logic is concentrated in one file with a clear entry point.
- Contains nearly all signal types: asserts, configuration-dependent fallback boundaries, module-level caching, environment branches, and hard-coded constants.
- Decision logic is at the Python layer, Triton kernels can be mocked, and Shanghao can confirm most regions on CPU.
- Aligns with Shanghao's area (sparse attention), making domain review easier.

## Paper-side highlights (temporary stub; see `data/pilot_flexprefill/paper_side_stub.json`; to be replaced by Zhaopeng)

- Mechanism: per-head query-aware / vertical-slash selection (τ decision), selecting blocks by cumulative attention threshold γ.
- Evaluation configuration: block_size = 128; at least 1024 tokens per head; τ = 0.1; γ = 0.9 / 0.95; one A100 80GB; RULER 4k–128k; four models (Llama-3.1-8B、GLM-4-9B、Yi-9B-200K、Qwen2-7B), all with head_dim 128.
- The paper **does not mention**: batch size, dtype, dense handling of short sequences, decode, multi-turn / KV cache reuse / chunked prefill, or GQA handling details. There is no separate Limitations section.
- README states: "only supports inference with a batch size of 1 and has only been tested with bfloat16 precision"; the vLLM example sets `enable_chunked_prefill=False` but does not explain why.

## Gold region table (`gold_regions.json`, manually annotated, 16 entries)

| ID | Condition | Outcome | Location |
|---|---|---|---|
| R01 | batch_size != 1 | reject | 1824 |
| R02 | q_len == 1 (decode) | fallback (dense, by design) | 1825 |
| R03 | q_len != k_len (prefill on an existing KV cache) | reject | 1836 |
| R04 | head_dim ∉ {16,32,64,128} | reject | 1837 |
| R05 | block_size ∉ {16,32,64,128} | reject | 1838 |
| R06 | q_len ≤ max(2·block_size, ⌈min_budget/block_size⌉·block_size) | fallback (dense) | 1842 |
| R07 | Otherwise | mechanism | 1856 |
| R08 | dtype ≠ bfloat16 (sparse path) | reject | 1218 |
| R09 | head_dim ≤ 128 and block_size ∉ {32,64,128} | reject (contradicts R05) | 1222 |
| R10 | num_q_heads % num_kv_heads ≠ 0 | reject | 1258 |
| R11 | triton major version < 3 | env_dependent | 1267 |
| R12 | block_size ≠ 128 (hard-coded `// 128`) | suspicious | 1708 |
| R13 | Module-level causal_mask cache reused across calls | state_dependent | 1694 |
| R14 | JS divergence < τ | mechanism_variant | 1727 |
| R15 | GPU is not H100 / A100 / 4090 | env_dependent | 86 |
| R16 | flash_attn is not installed | env_dependent | 1784 |

R06's boundary depends on configuration: q_len ≤ 1024 with the paper configuration (128, 1024); ≤ 512 with the README example (min_budget=512); ≤ 256 with the default (None).

## Preliminary findings (`draft_findings.json`, draft, pending team review and execution confirmation)

| ID | Category | Description | Priority | Confidence |
|---|---|---|---|---|
| F01 | undocumented | Prefill on an existing KV cache (multi-turn, prefix reuse, chunked prefill) is rejected by an assert | 1 | mechanical |
| F02 | undocumented | Block budget is converted using hard-coded 128; γ coverage may not hold when block_size is 32/64 | 1 | llm_assisted (candidate) |
| F03 | undocumented | Module-level causal_mask cache may fail across devices or when block_size changes | 1 | llm_assisted (candidate) |
| F04 | undocumented | Models with head_dim outside {16,32,64,128} are rejected | 2 | mechanical |
| F05 | documented_elsewhere | Sparse path requires bf16; README only says it was “tested” | 2 | mechanical |
| F06 | undocumented (out of scope) | block_size=16 passes the entry check and docstring but fails in the kernel | 3 | mechanical |
| F07 | documented_elsewhere | batch size must be 1 (README only) | 3 | mechanical |

Filtered out: decode uses dense (paper discusses only prefill), short sequences use dense (boundary is below the evaluated 4K and consistent with “at least 1024 tokens”), GQA non-divisibility, triton version, optional flash_attn.

**F02 and F03 are candidates found by manually reading code; Shanghao must confirm them by execution before they can be counted as results.**

## Extractor v0 results on the pilot

```
gold regions: 16   predicted: 30
recall: 16/16 = 1.00
unmatched predictions: 10
  6: decode kernel asserts (unreachable under prefill prefix)      -> path feasibility pruning needed
  2: triton_bnhd_pool asserts (covered by entry asserts)          -> redundancy detection needed
  2: block_idx isinstance / len asserts (internal invariants)     -> internal invariant filtering needed
```


**Note: v0 rules were written against this pilot; recall 1.00 does not demonstrate generalization.** The second artifact is the real test (TASKS.md M3).

## Points to flag to Shanghao for CPU execution

- `GPU_NAME` is None without CUDA; `.lower()` in `get_num_warps_stages` will fail and needs a mock.
- The module runs `import triton` at import time; the CPU environment needs triton installed or stubbed out.
- When flash_attn is not installed, dense fallback switches to `triton_flash_attention`, which also requires bf16 and specified head_dim values.
