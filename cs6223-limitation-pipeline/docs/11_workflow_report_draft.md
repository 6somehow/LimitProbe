# CS6223 Limitation Pipeline: Workflow and Results Draft (2026-11-18)

> Draft. All confidence levels (L0–L3, A0–A2) are **uncalibrated** and **have not been checked by humans**; they are not accuracy measures.

## 1. Problem

Given a systems paper and its code repository, automatically find limitations that are "论文没说清、或代码里实际受限" (English: not explained clearly in the paper or constrained in the actual code), and try to test them using real code.

## 2. Workflow

```
Paper PDF + repository (fixed commit)
   │
   ├─ Code side (Wanting)   Step 2: static analysis + LLM read-through, yielding regions with code conditions/limitations
   ├─ Paper side (Zhaopeng) Steps 1/3a: find mechanisms and claims in the paper, then locate them in source code
   ├─ Verification 3b       Check whether each code limitation is stated in the paper/README/docstring
   └─ Step 4                Deduplicate, classify, set priority, and give witness hints → limitations_for_tests.json (Finding)
                                         │
                                         ▼
Test side (Shanghao, checklimits)
   ├─ Environment preflight (ENV.json) → provision as needed (CPU torch, install dependencies one by one)
   ├─ Code agent designs a test for each testable Finding (CPU substitutes for GPU code, optionally with a sim_check self-check)
   ├─ Harness reruns deterministically, checks the agent's claimed oracle, and gives a verdict + level L0–L3 + remaining defeaters
   ├─ Untestable Findings: analysis lane (static evidence → regex probes → LLM reading), level A0–A2, no yes/no
   ├─ Papers without code: paper-only mode (quotes must appear verbatim in the PDF; arithmetic checks are computed by the harness), maximum A1
   └─ Output: results/tests/<id>/, results/report/<id>/LIMITATIONS.md (one-to-one with Findings)
```

Entry point: `python -m pipeline e2e <id>` (run the `doctor` preflight first; key, proxy network interface, and base_url all come from environment variables, via a local relay).
Use `--no-run` for frozen step 4 output; use `paper-only` for papers without code.

## 3. Results overview (7 papers with code + 1 paper only)

| Paper | Finding | Tested | Test results | Untested: analysis levels |
|---|---|---|---|---|
| FlexPrefill | 65 | 29 | yes 29 (L1 16 / L2 7 / L3 6) | A2 15 / A1 18 / A0 3 |
| NNSmith | 38 | 22 | yes 20, inconclusive 2 | A2 5 / A1 8 / A0 3 |
| InfiniGen | 31 | 19 | yes 15, inconclusive 4 | A2 9 / A1 1 / A0 2 |
| MInference | 73 | 37 | yes 27, inconclusive 10 | A2 17 / A1 9 / A0 10 |
| SparTA | 82 | 2 | yes 2 (79 have no code location) | A2 49 / A1 20 / A0 11 |
| FlexPosit | 41 | 12 | yes 8, the rest inconclusive/invalid | A2 19 / A1 3 / A0 7 |
| QoServe | 50 | 9 | yes 9 | A2 32 / A1 3 / A0 6 |
| Tessera (no code) | 10 candidates | 0 | — | A1 10 (2 others discarded because quotes did not match) |

There are about 390 Findings in total, of which about 130 were tested using real code.

## 4. Limitations found in each paper (summary)

**Common categories**: Most are "代码里有、论文没写" (English: present in code but unstated in the paper) (`undisclosed`), followed by implementation deviations from the paper (`impl_deviates`) and unimplemented features (`not_implemented`). Four typical types are rejected inputs, changed execution paths, state or randomness effects, and hard-coded sizes or configurations.

**FlexPrefill** (sparse attention)
- GQA requires the number of q heads to be a multiple of the number of kv heads; otherwise an assertion fails (F003, L3).
- It requires equal q/k sequence lengths, `head_dim ∈ {16,32,64,128}`, and batch size 1 (F013/F014/F052, L3).
- Sequences shorter than about two blocks silently fall back to flash attention, so the sparse mechanism does not take effect (F026, L3).
- The patch entry point asserts for models other than `LlamaForCausalLM` (F001).

**NNSmith** (DNN fuzz testing)
- Guided constraints are randomly skipped for each node with `constrain_prob`; the mechanism is probabilistic, while the paper's wording is more definite (F035).
- After memory limit constraints are added, a solver result other than sat causes an assertion and abort (F004).
- Multiplication bit widths are no longer aligned once they reach `ARITH_MAX_WIDTH`, changing solver behavior (F010).
- Environment variables (such as `NNSMITH_GRES`, `NNSMITH_FLOPS_LIM=off`) silently change generation and acceptance rules (F001/F011).

**InfiniGen** (KV cache prefetching)
- The prefetch path depends on whether the device type is MIXED; the combination of `compress_cache` and `attn_sparsity<1` is not implemented (F002/F005).
- Partial weight speculation is enabled only for layers with `layer_id > 1`; layers 0 and 1 and the first and last layers do not use the InfiniGen path (F009/F012/F027).

**MInference** (dynamic sparse attention)
- Several kernels have hard assertions on `head_dim` and q/k/v shapes (`Lk ∈ {16,32,64,128}`, four dimensions, and all three shapes equal; F011/F013/F015/F016, L2–L3).
- A head_dim outside the list is zero-padded to a power of 2 before entering the kernel (F037).

**SparTA** (sparse tensor compilation)
- The choice of covering algorithm depends on the sparsity pattern and block prices supplied by the caller (F001).
- `wbc_matmul` supports only one block size and fails with multiple sizes (F002).
- Most of the 82 entries are paper-side descriptions with no code location, so only analysis is possible.

**FlexPosit** (Posit quantization)
- A per-column scale outside [-16, 15] cannot be written to the RTL's 5-bit field (F004).
- `nsize` must be in [2,16], imposing a hard limit on precision (F005).
- Weights must be exact Posit values or encoding fails (F003).
- Quantization aborts entirely when the sensitivity file does not match layer names (F002).
- The cause of 4 `invalid` Findings has not yet been investigated.

**QoServe** (SLO scheduling)
- For nonzero tiers, the TBT deadline uses another threshold, so behavior changes with the randomly assigned tier (F004, L3).
- The prefill search space changes when fewer than 1000 KV blocks are free (F005, L3).
- When slack ≤ 0, binary search is skipped and the minimum value 128 is returned directly (F006, L3).
- For tier ≥ 1, predicted decode time is deducted from the ttft deadline, making it dependent on the output length prediction (F007, L3).

**Tessera** (OSDI 2026, no code, paper reading observations only, all A1)
- The headline improvement of 20%–33% compares against an internal Alibaba Megatron-LM branch; only the 256-card result is publicly comparable (P001).
- Production evidence covers only the Qwen3 family, Hopper/RoCE, and private data; other models were tested only on 256 cards (P002).
- The partitioner optimizes a maximum-edge proxy objective, not the full pipeline critical path; the search is limited to the vicinity of the serial baseline (P005).
- DBO was validated separately only on Qwen3-Next-M, 256 cards, and 4K sequences (P006).
- Two improvements in the two-week production trace were attributed to Static Planner / DBO without a controlled A/B test (P007).
- The co-optimization experiment used a mock router with a uniform token distribution and disabled DBO, removing the routing randomness targeted by the design (P009).
- "零数值偏差、无质量回退" (English: zero numerical deviation, no quality regression) is supported only by bit-identical loss in one deterministic mode, without convergence curves or multiple-seed results (P010).

## 5. Known limitations (must be disclosed on delivery)

1. Step 4 reruns are **not reproducible** (SparTA 82→100, FlexPosit also changed); the cause is unknown. Use `--no-run` for existing results.
2. All levels are uncalibrated and have not been checked by humans; A2 only means "找到的文本与读法一致" (English: the text found agrees with the interpretation).
3. `sim_check` for GPU substitutes has been validated only on FlexPrefill F07; there is no symbolic execution engine.
4. Test results favor "可达的条件分支 + 断言/路径变化" (English: reachable conditional branches and assertions/path changes); tests cover performance and accuracy limitations very little.
5. Many Findings (including 79 for SparTA) have analysis only and no test.
6. Review labels come from blind LLM review, not human review.

## 6. Suggested next steps

1. Investigate why step 4 is not reproducible.
2. Sample 20 A0/A2 entries for human review to obtain an initial rough calibration dataset.
3. Investigate the 4 `invalid` FlexPosit entries.
4. Have the agent write a real `sim_check` for a new GPU Finding to validate this path.
