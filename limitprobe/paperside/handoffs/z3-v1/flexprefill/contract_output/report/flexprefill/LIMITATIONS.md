> Offline contract-format demonstration only. No target, agent, environment probe or tests ran.

# Limitations report: FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference

- artifact: `flexprefill` (ICLR 2025 (Oral)), repository https://github.com/bytedance/FlexPrefill at `a24b27bf11`
- input: `limitations_for_tests.json` (sha256 `0e2250ef46d4`), 1 Findings
- generated: 2026-11-16T15:33:49+08:00 by `checklimits test` (contract `checklimits-test-report/1`)

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 1 |
| tested | 0 |
| not tested | 1 |
| not tested, by reason | `no_code_location` 1 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [flexprefill-Z3-M08-B05](#flexprefill-z3-m08-b05) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1590` | not tested: `no_code_location` |

## flexprefill-Z3-M08-B05

**K_v=min{k: 前 k 个 a_v 累计≥γ}**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1590` in `flex_prefill/ops/flex_prefill_attention.py::score_cover_topk`
- paper/docs (paper, PDF p.6, text lines 55-61): “# Sort vertical and slash attention scores Iv ← argsort(av) Is ← argsort(as) # Obtain the minimum computational budget making the sum of the scores exceeds γ Kv ← min{k : Pi∈Iv [1:k] av[i] ≥ γ} Ks ← min{k : Pi∈Is[1:k] as[i] ≥ γ}”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1590`): `topk = torch.sum(cumsum_x <= score, dim=-1) + 1`

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence); Source locations exist, but adapter.region_from_limitation refuses origin=paper. This proposed effect also needs a custom oracle: outcome 'suspicious' has no effect check yet
