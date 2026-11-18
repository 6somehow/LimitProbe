# Limitations report: FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference

- artifact: `flexprefill` (ICLR 2025 (Oral)), repository https://github.com/bytedance/FlexPrefill at `a24b27bf11`
- input: `results/step4/flexprefill/limitations_for_tests.json` (sha256 `0b8539b75ec0`), 65 Findings
- generated: 2026-11-18T17:55:09+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
- environment: **ok**

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* A Finding that was not tested may carry an **analysis** (tier A0 to A2): a reading of the paper and code evidence, with text probes run by the harness. It is a weaker kind of evidence than a test, has its own uncalibrated tiers, and never says yes or no.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 65 |
| tested | 29 |
| not tested | 36 |
| verdicts | yes 29 |
| levels | L1 16, L2 7, L3 6 |
| analysis only (not tests) | A0 3, A1 18, A2 15 |
| not tested, by reason | `no_code_location` 19, `outcome_unsupported` 6, `witness_unusable` 11 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [flexprefill-F001](#flexprefill-f001) | undisclosed | reject | `flex_prefill/modules/patch.py:123` | **yes** / L1 (uncalibrated) |
| [flexprefill-F002](#flexprefill-f002) | undisclosed | reject | `flex_prefill/modules/patch.py:241` | **yes** / L1 (uncalibrated) |
| [flexprefill-F003](#flexprefill-f003) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:247` | **yes** / L3 (uncalibrated) |
| [flexprefill-F006](#flexprefill-f006) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1240-1244` | **yes** / L1 (uncalibrated) |
| [flexprefill-F007](#flexprefill-f007) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1245` | **yes** / L2 (uncalibrated) |
| [flexprefill-F008](#flexprefill-f008) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1256` | **yes** / L2 (uncalibrated) |
| [flexprefill-F009](#flexprefill-f009) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1258` | **yes** / L2 (uncalibrated) |
| [flexprefill-F012](#flexprefill-f012) | undisclosed | state | `flex_prefill/ops/flex_prefill_attention.py:1695-1698` | **yes** / L1 (uncalibrated) |
| [flexprefill-F013](#flexprefill-f013) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1836` | **yes** / L3 (uncalibrated) |
| [flexprefill-F014](#flexprefill-f014) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1837` | **yes** / L3 (uncalibrated) |
| [flexprefill-F015](#flexprefill-f015) | undisclosed | reject | `flex_prefill/ops/vertical_slash_attention.py:265` | **yes** / L1 (uncalibrated) |
| [flexprefill-F016](#flexprefill-f016) | undisclosed | reject | `flex_prefill/ops/vertical_slash_attention.py:552` | **yes** / L2 (uncalibrated) |
| [flexprefill-F017](#flexprefill-f017) | undisclosed | path_change | `flex_prefill/modules/patch.py:69` | **yes** / L1 (uncalibrated) |
| [flexprefill-F018](#flexprefill-f018) | undisclosed | path_change | `flex_prefill/modules/patch.py:313` | **yes** / L1 (uncalibrated) |
| [flexprefill-F019](#flexprefill-f019) | stated_differently | reject | `flex_prefill/modules/patch.py:320` | **yes** / L1 (uncalibrated) |
| [flexprefill-F020](#flexprefill-f020) | undisclosed | path_change | `flex_prefill/modules/patch.py:424` | **yes** / L2 (uncalibrated) |
| [flexprefill-F021](#flexprefill-f021) | undisclosed | path_change | `flex_prefill/modules/patch.py:501` | **yes** / L1 (uncalibrated) |
| [flexprefill-F022](#flexprefill-f022) | stated_differently | reject | `flex_prefill/ops/flex_prefill_attention.py:672` | **yes** / L1 (uncalibrated) |
| [flexprefill-F023](#flexprefill-f023) | stated_differently | reject | `flex_prefill/ops/flex_prefill_attention.py:1218` | **yes** / L1 (uncalibrated) |
| [flexprefill-F024](#flexprefill-f024) | stated_differently | reject | `flex_prefill/ops/flex_prefill_attention.py:1222-1226` | **yes** / L1 (uncalibrated) |
| [flexprefill-F026](#flexprefill-f026) | undisclosed | path_change | `flex_prefill/ops/flex_prefill_attention.py:1842-1854` | **yes** / L3 (uncalibrated) |
| [flexprefill-F027](#flexprefill-f027) | stated_differently | reject | `flex_prefill/ops/vertical_slash_attention.py:264` | **yes** / L1 (uncalibrated) |
| [flexprefill-F028](#flexprefill-f028) | undisclosed | path_change | `flex_prefill/ops/vertical_slash_attention.py:557` | **yes** / L1 (uncalibrated) |
| [flexprefill-F029](#flexprefill-f029) | undisclosed | path_change | `flex_prefill/ops/vertical_slash_attention.py:570` | **yes** / L2 (uncalibrated) |
| [flexprefill-F030](#flexprefill-f030) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1588-1591` | not tested: `no_code_location`, analysis A2/supports |
| [flexprefill-F031](#flexprefill-f031) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F032](#flexprefill-f032) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F033](#flexprefill-f033) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | not tested: `no_code_location`, analysis A2/supports |
| [flexprefill-F034](#flexprefill-f034) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1676-1706` | not tested: `no_code_location`, analysis A2/supports |
| [flexprefill-F035](#flexprefill-f035) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1705-1716` | not tested: `no_code_location`, analysis A2/supports |
| [flexprefill-F036](#flexprefill-f036) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1707-1713` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F037](#flexprefill-f037) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F038](#flexprefill-f038) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F039](#flexprefill-f039) | docs_only | path_change | `flex_prefill/modules/patch.py:114` | **yes** / L1 (uncalibrated) |
| [flexprefill-F040](#flexprefill-f040) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:88-96` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [flexprefill-F004](#flexprefill-f004) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:865` | not tested: `witness_unusable`, analysis A2/supports |
| [flexprefill-F041](#flexprefill-f041) | stated_differently | reject | `flex_prefill/ops/flex_prefill_attention.py:868` | not tested: `witness_unusable`, analysis A2/supports |
| [flexprefill-F042](#flexprefill-f042) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:869` | not tested: `witness_unusable`, analysis A2/supports |
| [flexprefill-F043](#flexprefill-f043) | docs_only | reject | `flex_prefill/ops/flex_prefill_attention.py:870-875` | not tested: `witness_unusable`, analysis A0/supports |
| [flexprefill-F044](#flexprefill-f044) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:876` | not tested: `witness_unusable`, analysis A1/unclear |
| [flexprefill-F045](#flexprefill-f045) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:878` | not tested: `witness_unusable`, analysis A2/supports |
| [flexprefill-F005](#flexprefill-f005) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1219` | not tested: `witness_unusable`, analysis A0/contradicts |
| [flexprefill-F046](#flexprefill-f046) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1220` | not tested: `witness_unusable`, analysis A2/supports |
| [flexprefill-F047](#flexprefill-f047) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1221` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [flexprefill-F048](#flexprefill-f048) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1228-1231` | not tested: `witness_unusable`, analysis A0/supports |
| [flexprefill-F049](#flexprefill-f049) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1270-1272` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [flexprefill-F010](#flexprefill-f010) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1450` | not tested: `witness_unusable`, analysis A1/unclear |
| [flexprefill-F011](#flexprefill-f011) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1451` | not tested: `witness_unusable`, analysis A2/supports |
| [flexprefill-F050](#flexprefill-f050) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1708` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexprefill-F025](#flexprefill-f025) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1727` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexprefill-F051](#flexprefill-f051) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1787` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexprefill-F052](#flexprefill-f052) | docs_only | reject | `flex_prefill/ops/flex_prefill_attention.py:1824` | **yes** / L3 (uncalibrated) |
| [flexprefill-F053](#flexprefill-f053) | docs_only | path_change | `flex_prefill/ops/flex_prefill_attention.py:1825-1835` | **yes** / L1 (uncalibrated) |
| [flexprefill-F054](#flexprefill-f054) | docs_only | reject | `flex_prefill/ops/flex_prefill_attention.py:1838` | **yes** / L3 (uncalibrated) |
| [flexprefill-F055](#flexprefill-f055) | docs_only | reject | `flex_prefill/ops/vertical_slash_attention.py:553` | **yes** / L2 (uncalibrated) |
| [flexprefill-F056](#flexprefill-f056) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:16-45` | not tested: `no_code_location`, analysis A2/supports |
| [flexprefill-F057](#flexprefill-f057) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F058](#flexprefill-f058) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F059](#flexprefill-f059) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F060](#flexprefill-f060) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F061](#flexprefill-f061) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F062](#flexprefill-f062) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A2/supports |
| [flexprefill-F063](#flexprefill-f063) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F064](#flexprefill-f064) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |
| [flexprefill-F065](#flexprefill-f065) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location`, analysis A1/unclear |

## flexprefill-F001

**When not isinstance(model, LlamaForCausalLM): Patching a non-LlamaForCausalLM model with a non-default pattern triggers an assertion failure. (flex_prefill/modules/patch.py:123)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/modules/patch.py:123` in `flex_prefill/modules/patch.py::patch_llama_attention`
- condition: `not isinstance(model, LlamaForCausalLM)`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: Even among llama-named HF models, only LlamaForCausalLM instances are accepted, so other Llama heads such as LlamaModel or sequence classification fail the assertion; this is a narrower check than m02.
- code snippet (`flex_prefill/modules/patch.py:123`): `assert isinstance(model, LlamaForCausalLM)`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/modules/patch.py:123
- contrast run: no exception at flex_prefill/modules/patch.py:123 (later ModuleNotFoundError at flex_prefill/modules/llama/flash_attention.py:28)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'isinstance(model, LlamaForCausalLM)' is not an integer (value True)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 Region chain starts at the artifact entry point flex_prefill_attention, but the hand-off contains no call graph connecting it to patch_llama_attention (patch_llama_att…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F001/execution_report.json`

## flexprefill-F002

**When not isinstance(model, Qwen2ForCausalLM): Patching a non-Qwen2ForCausalLM model with a non-default pattern triggers an assertion failure. (flex_prefill/modules/patch.py:241)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/modules/patch.py:241` in `flex_prefill/modules/patch.py::patch_qwen2_attention`
- condition: `not isinstance(model, Qwen2ForCausalLM)`
- code snippet (`flex_prefill/modules/patch.py:241`): `assert isinstance(model, Qwen2ForCausalLM)`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/modules/patch.py:241
- contrast run: no exception at flex_prefill/modules/patch.py:241 (later ValueError at flex_prefill/modules/patch.py:274)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: call_chain[0] is flex_prefill_attention, but that function never calls patch_qwen2_attention; the step-4 adapter links them only because patch.py imports the entry. The guard can…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F002/execution_report.json`

## flexprefill-F003

**When num_q_heads % num_kv_heads != 0: GQA requires the number of query heads to be a multiple of KV heads; otherwise execution stops. (flex_prefill/ops/flex_prefill_attention.py:247)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:247` in `flex_prefill/ops/flex_prefill_attention.py::triton_flash_prefill`
- condition: `num_q_heads % num_kv_heads != 0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Requiring q heads to be a multiple of kv heads is a GQA shape invariant that every real model satisfies, not a mechanism limitation.
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:247`): `assert num_q_heads % num_kv_heads == 0`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:247
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:247 (later AttributeError at flex_prefill/ops/flex_prefill_attention.py:49)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/flexprefill/flexprefill-F003/execution_report.json`

## flexprefill-F006

**When not (isinstance(block_idx, list) and isinstance(block_idx[0], list) and isinstance(block_idx[0][0], torch.Tensor)): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1240)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1240-1244` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (isinstance(block_idx, list) and isinstance(block_idx[0], list) and isinstance(block_idx[0][0], torch.Tensor))`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1240`): `assert isinstance(block_idx, list) and isinstance(block_idx[0], list) and isinstance(block_idx[0][0], torch.Tensor)`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1241
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1240 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. an extra negative input shows the effect (or never reached the target): the no-effect region is not what the pair suggests
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: flex_prefill_attention (call_chain[0]) does not take block_idx; it builds list[list[Tensor]] internally via get_active_blocks, so the malformed list-of-Tensor shape the Region is…
- what would raise the level: D5 (refuted): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F006/execution_report.json`

## flexprefill-F007

**When not (len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1245)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1245` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1245`): `assert len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1245
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1245 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The asserted value is block_idx, which is not a parameter of the official entry flex_prefill_attention: the entry builds it internally with get_active_blocks, which always return…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F007/execution_report.json`

## flexprefill-F008

**When not (num_block <= total_q_blocks * (total_q_blocks + 1) // 2): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1256)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1256` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (num_block <= total_q_blocks * (total_q_blocks + 1) // 2)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1256`): `assert num_block <= total_q_blocks * (total_q_blocks + 1) // 2`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1256
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1256 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The Region target lives in triton_block_wise_prefill_attention and the witness supplies num_block (block_idx.shape[2]) directly. The official caller flex_prefill_attention derive…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F008/execution_report.json`

## flexprefill-F009

**When not (num_q_heads % num_kv_heads == 0): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1258)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1258` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (num_q_heads % num_kv_heads == 0)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1258`): `assert num_q_heads % num_kv_heads == 0`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1258
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1258 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The official entry flex_prefill_attention cannot reach line 1258 for a non-divisible head pair: its pre-target call get_active_blocks reshapes heads with num_q_heads // num_kv_he…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F009/execution_report.json`

## flexprefill-F012

**When causal_mask is None # first call only: module-level cache initialised on first call and reused (flex_prefill/ops/flex_prefill_attention.py:1695)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1695-1698` in `flex_prefill/ops/flex_prefill_attention.py::get_active_blocks`
- condition: `causal_mask is None # first call only`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1695`): `if causal_mask is None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/ops/flex_prefill_attention.py:1695
- contrast run: branch not taken at flex_prefill/ops/flex_prefill_attention.py:1695
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: the boundary variable is the prelude (program state): adjacency cannot be probed
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive direct, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/flexprefill/flexprefill-F012/execution_report.json`

## flexprefill-F013

**When not (q.shape[1] == k.shape[1]): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1836)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1836` in `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`
- condition: `not (q.shape[1] == k.shape[1])`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1836`): `assert q.shape[1] == k.shape[1]`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1836
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1836
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/flexprefill/flexprefill-F013/execution_report.json`

## flexprefill-F014

**When not (head_dim in {16, 32, 64, 128}): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1837)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1837` in `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`
- condition: `not (head_dim in {16, 32, 64, 128})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1837`): `assert head_dim in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1837
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1837
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/flexprefill/flexprefill-F014/execution_report.json`

## flexprefill-F015

**When q_len != k_len: Rejects inputs where query and key sequence lengths differ, so no cross-length (e.g. decode-style) attention is supported. (flex_prefill/ops/vertical_slash_attention.py:265)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/vertical_slash_attention.py:265` in `flex_prefill/ops/vertical_slash_attention.py::triton_vertical_slash_attention`
- condition: `q_len != k_len`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: vertical_slash_attention.py is the separate vertical-slash (MInference-style) baseline pattern, not the FlexPrefill path, which uses triton_block_wise_attention.
- code snippet (`flex_prefill/ops/vertical_slash_attention.py:265`): `assert q_len == k_len`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/ops/vertical_slash_attention.py:265
- contrast run: no exception at flex_prefill/ops/vertical_slash_attention.py:265 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 hand-off synthesises the chain as [flex_prefill_attention, target] without the real call graph. flex_prefill_attention cannot reach this target: for q_len == 1 it take…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F015/execution_report.json`

## flexprefill-F016

**When head_dim not in {16, 32, 64, 128}: Caller-supplied head_dim outside the fixed set aborts execution via assertion. (flex_prefill/ops/vertical_slash_attention.py:552)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `flex_prefill/ops/vertical_slash_attention.py:552` in `flex_prefill/ops/vertical_slash_attention.py::vertical_slash_attention`
- condition: `head_dim not in {16, 32, 64, 128}`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: The head_dim assert is in the vertical_slash baseline op, not in FlexPrefill's mechanism.
- code snippet (`flex_prefill/ops/vertical_slash_attention.py:552`): `assert head_dim in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at flex_prefill/ops/vertical_slash_attention.py:552
- contrast run: no exception at flex_prefill/ops/vertical_slash_attention.py:552
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The recorded call_chain[0], flex_prefill_attention, does not call vertical_slash_attention and raises its own head_dim assertion at flex_prefill_attention.py:1826 before any such…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F016/execution_report.json`

## flexprefill-F017

**When pattern == "minfer": For minfer, the config is loaded from a hard-coded JSON file chosen by cfg['model_type'] and stored as model.config.minfer_config, rather than merging ATTENTION_CONFIG_EXAMPLE defaults. (flex_prefill/modules/patch.py:69)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/modules/patch.py:69` in `flex_prefill/modules/patch.py::patch_model_config`
- condition: `pattern == "minfer"`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: The minfer config loading belongs to the MInference baseline, not to FlexPrefill.
- code snippet (`flex_prefill/modules/patch.py:69`): `if pattern == 'minfer':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/modules/patch.py:69
- contrast run: branch not taken at flex_prefill/modules/patch.py:69
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'pattern' is not an integer (value 'flex_prefill')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The official call_chain[0] entry flex_prefill_attention is the low-level attention kernel and never calls patch_model_config; the target's real caller patch_hf_model is not part …
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F017/execution_report.json`

## flexprefill-F018

**When "llama" in model_name.lower(): Model class name selects which patch_*_attention implementation is applied; non-llama/glm/qwen2 models are rejected. (flex_prefill/modules/patch.py:313)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/modules/patch.py:313` in `flex_prefill/modules/patch.py::patch_hf_model`
- condition: `"llama" in model_name.lower()`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: patch_hf_model raises ValueError for any HF model whose class name does not contain llama, glm or qwen2, so FlexPrefill only supports those model families.
- code snippet (`flex_prefill/modules/patch.py:313`): `if 'llama' in model_name.lower():`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/modules/patch.py:313
- contrast run: branch not taken at flex_prefill/modules/patch.py:313
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'model_class' is not an integer (value 'Qwen2ForCausalLM')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The Region call chain lists flex_prefill_attention as its first function, but that function is a GPU attention kernel and never calls patch_hf_model. The target is reached throug…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F018/execution_report.json`

## flexprefill-F019

**When not ("llama" in model_name.lower() or "glm" in model_name.lower() or "qwen2" in model_name.lower()): Any HF model whose class name lacks llama/glm/qwen2 is rejected outright. (flex_prefill/modules/patch.py:320)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/modules/patch.py:320` in `flex_prefill/modules/patch.py::patch_hf_model`
- condition: `not ("llama" in model_name.lower() or "glm" in model_name.lower() or "qwen2" in model_name.lower())`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: patch_hf_model raises ValueError for any model class whose name lacks llama/glm/qwen2, so other architectures cannot use FlexPrefill.
- paper/docs (readme, README.md / Supported Models): “Currently, `flex_prefill.patch_model` only supports the following models: - LLaMA: [meta-llama/Meta-Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct) - Qwen2: [Qwen/Qwen2-7B-Instruct](https://huggingface.co/Qwen/Qwen2-7B-Instruct) - ChatGLM4: [THUDM/glm-4-9b-chat-…”
- code snippet (`flex_prefill/modules/patch.py:320`): `raise ValueError(f'unsupported model type: {model_name}')`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at flex_prefill/modules/patch.py:320
- contrast run: no exception at flex_prefill/modules/patch.py:320
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'model_name' is not an integer (value 'LlamaForCausalLM')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: step-4 hand-off builds call_chain=[artifact entry point flex_prefill_attention, patch_hf_model], but flex_prefill_attention never calls patch_hf_model; patch_hf_model is the only…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F019/execution_report.json`

## flexprefill-F020

**When kv_cache is None or prefill_meta.block_tables is None or prefill_meta.block_tables.numel() == 0: Only when there is no prefix cache does the code call flex_prefill_attention; otherwise it falls back to flash_attn_varlen_func. (flex_prefill/modules/patch.py:424)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/modules/patch.py:424` in `flex_prefill/modules/patch.py::patch_vllm_model.flex_prefill_forward`
- condition: `kv_cache is None or prefill_meta.block_tables is None or prefill_meta.block_tables.numel() == 0`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: In vLLM, when the prefill has non-empty block tables (e.g. prefix caching hits), the code silently runs dense flash_attn_varlen_func instead of flex_prefill_attention.
- code snippet (`flex_prefill/modules/patch.py:424`): `if kv_cache is None or prefill_meta.block_tables is None or prefill_meta.block_tables.numel() == 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at flex_prefill/modules/patch.py:424 (later AttributeError at flex_prefill/ops/flex_prefill_attention.py:49)
- contrast run: branch not taken at flex_prefill/modules/patch.py:424 (later AssertionError at flex_prefill/modules/patch.py:459)
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: call_chain[0] flex_prefill_attention is the callee guarded by this branch, not a caller that can reach it; the decision itself is inside the nested flex_prefill_forward, so the d…
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F020/execution_report.json`

## flexprefill-F021

**When "attention" in type(m).__name__.lower() and hasattr(m, "impl"): Only modules whose class name contains 'attention' and expose an 'impl' attribute get their forward replaced; others keep the original implementation. (flex_prefill/modules/patch.py:501)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/modules/patch.py:501` in `flex_prefill/modules/patch.py::patch_vllm_model`
- condition: `"attention" in type(m).__name__.lower() and hasattr(m, "impl")`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: Matching modules by class name to patch vLLM attention is internal plumbing that every attention layer satisfies; no user condition is involved.
- code snippet (`flex_prefill/modules/patch.py:501`): `if 'attention' in type(m).__name__.lower() and hasattr(m, 'impl'):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/modules/patch.py:501
- contrast run: branch not taken at flex_prefill/modules/patch.py:501
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 hand-off builds call_chain[0] from artifact.json entry_points (flex_prefill_attention), but the real call graph is not part of the hand-off and flex_prefill_attention …
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F021/execution_report.json`

## flexprefill-F022

**When q.dtype != torch.bfloat16: triton_flash_attention rejects non-bfloat16 queries before dispatching to prefill or decode. (flex_prefill/ops/flex_prefill_attention.py:672)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:672` in `flex_prefill/ops/flex_prefill_attention.py::triton_flash_attention`
- condition: `q.dtype != torch.bfloat16`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: triton_flash_attention (used for decode/short-sequence dense paths when gqa_interleave is set or flash-attn is missing) rejects non-bf16 inputs; the sparse block-wise kernel also asserts bf16, so fp16/fp32 models cannot run.
- paper/docs (readme, README.md / FlexPrefill Sparse Attention Function): “Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precision.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:672`): `assert q.dtype == torch.bfloat16`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:672
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:672
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'dtype' is not an integer (value 'bfloat16')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/flexprefill/flexprefill-F022/execution_report.json`

## flexprefill-F023

**When not (q.dtype == torch.bfloat16): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1218)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1218` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (q.dtype == torch.bfloat16)`
- paper/docs (readme, README.md / FlexPrefill Sparse Attention Function): “Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precision.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1218`): `assert q.dtype == torch.bfloat16`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1218
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1218
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'dtype' is not an integer (value 'bfloat16')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: call_chain[1] is the target's own function. The official entry calls get_active_blocks first, which launches the GPU-only triton_bnhd_pool kernel before line 1218; reaching the t…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F023/execution_report.json`

## flexprefill-F024

**When not (block_size in {32, 64, 128}): 'only support block size in {32, 64, 128} if head_dim <= 128' (flex_prefill/ops/flex_prefill_attention.py:1222)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1222-1226` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (block_size in {32, 64, 128})`
- paper/docs (docstring, flex_prefill/ops/flex_prefill_attention.py:850 (triton_block_wise_decode_attention)): “block_size (int): Block size, only support 16, 32, 64 and 128.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1222`): `assert block_size in {32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1222
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1222 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D5 control pair differs in one factor, negative adjacent to the boundary: *open*. a neighbour probe failed before the target was decided
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D5 (open): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/flexprefill/flexprefill-F024/execution_report.json`

## flexprefill-F026

**When q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size): returns via flash_attn_func, triton_flash_attention (flex_prefill/ops/flex_prefill_attention.py:1842)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1842-1854` in `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`
- condition: `q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1842`): `if q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at flex_prefill/ops/flex_prefill_attention.py:1842
- contrast run: branch not taken at flex_prefill/ops/flex_prefill_attention.py:1842
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/flexprefill/flexprefill-F026/execution_report.json`

## flexprefill-F027

**When q.dtype != torch.bfloat16: Rejects any query tensor not in bfloat16, so callers using fp16/fp32 cannot run this kernel. (flex_prefill/ops/vertical_slash_attention.py:264)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/vertical_slash_attention.py:264` in `flex_prefill/ops/vertical_slash_attention.py::triton_vertical_slash_attention`
- condition: `q.dtype != torch.bfloat16`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: bf16 assert sits in the vertical-slash baseline kernel, not the FlexPrefill path.
- paper/docs (readme, README.md / FlexPrefill Sparse Attention Function): “Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precision.”
- code snippet (`flex_prefill/ops/vertical_slash_attention.py:264`): `assert q.dtype == torch.bfloat16`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at flex_prefill/ops/vertical_slash_attention.py:264
- contrast run: no exception at flex_prefill/ops/vertical_slash_attention.py:264 (later RuntimeError at triton/runtime/driver.py:8)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'dtype' is not an integer (value 'bfloat16')
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: call_chain[0] flex_prefill_attention never calls the target: its sparse path calls triton_block_wise_attention, while the real caller of triton_vertical_slash_attention is vertic…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/flexprefill/flexprefill-F027/execution_report.json`

## flexprefill-F028

**When seq_len <= min(vertical_size, slash_size) * block_size: For short sequences the sparse vertical/slash path is skipped and dense causal flash_attn_func is run instead. (flex_prefill/ops/vertical_slash_attention.py:557)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/vertical_slash_attention.py:557` in `flex_prefill/ops/vertical_slash_attention.py::vertical_slash_attention`
- condition: `seq_len <= min(vertical_size, slash_size) * block_size`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: The short-sequence dense fallback is in the vertical-slash baseline function, not in flex_prefill_attention.
- code snippet (`flex_prefill/ops/vertical_slash_attention.py:557`): `if seq_len <= min(vertical_size, slash_size) * block_size:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/ops/vertical_slash_attention.py:557
- contrast run: branch not taken at flex_prefill/ops/vertical_slash_attention.py:557
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: In the pinned commit the declared call-chain entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention does not call vertical_slash_attention at all (it ends in tr…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F028/execution_report.json`

## flexprefill-F029

**When seq_len <= 16 * 1024: Sequence length selects between the vertical/slash Triton kernel (<=16k) and the block-wise attention kernel (>16k) with transformed block indices. (flex_prefill/ops/vertical_slash_attention.py:570)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/vertical_slash_attention.py:570` in `flex_prefill/ops/vertical_slash_attention.py::vertical_slash_attention`
- condition: `seq_len <= 16 * 1024`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: The 16k switch is a performance choice inside the vertical_slash baseline op, not in FlexPrefill.
- paper/docs (code_comment, flex_prefill/ops/vertical_slash_attention.py:569): “seq_len <= 16k, use vertical slash to avoid block index transform”
- paper/docs (code_comment, flex_prefill/ops/vertical_slash_attention.py:589): “seq_len > 16k, use block wise attention to get faster speed”
- code snippet (`flex_prefill/ops/vertical_slash_attention.py:570`): `if seq_len <= 16 * 1024:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at flex_prefill/ops/vertical_slash_attention.py:570 (later AssertionError at flex_prefill/ops/vertical_slash_attention.py:264)
- contrast run: branch not taken at flex_prefill/ops/vertical_slash_attention.py:570 (later AssertionError at flex_prefill/ops/flex_prefill_attention.py:1218)
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The recorded call_chain[0] (flex_prefill_attention) never calls this op in the pinned source: it computes its own block indices and calls triton_block_wise_attention directly. ve…
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F029/execution_report.json`

## flexprefill-F030

**论文要求最小 k 使累计≥γ；代码取累计>γ 的最小 k（累计恰等于 γ 时多选一条），且 //128+1 放大、min/max_budget 覆盖，K_v 不再是论文定义的最小前缀（artifact 范围：>γ 而非 ≥γ，且 //128+1 与预算截断改变前缀长度）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1588-1591`
- condition: `torch.any(torch.cumsum(torch.sort(vertical, dim=-1, descending=True).values, dim=-1) == gamma) or torch.any(torch.cumsum(torch.sort(slash, dim=-1, descending=True).values, dim=-1) == gamma) or torch.…`
- paper/docs (paper, PDF p.6, text lines 69-75): “# Sort vertical and slash attention scores Iv← argsort(av) Is← argsort(as) # Obtain the minimum computational budget making the sum of the scores exceedsγ Kv← min{k :P i∈Iv [1:k] av[i]≥γ}”
- paper/docs (paper, PDF p.6, text lines 69-77): “# Sort vertical and slash attention scores Iv← argsort(av) Is← argsort(as) # Obtain the minimum computational budget making the sum of the scores exceedsγ Kv← min{k :P i∈Iv [1:k] av[i]≥γ} Ks← min{k :P i∈Is[1:k] as[i]≥γ}”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The code's score_cover_topk counts cumsum <= gamma then adds 1, so it returns the first prefix whose sum exceeds gamma (and one extra when sum equals gamma), whereas the paper defines min k with sum >= gamma. The subsequent //128+1 and min/max_budget clamps further change the prefix length. Thus the artifact deviates as claimed.
- cited code found at the pinned commit: yes (3 location(s))
- probe `def score_cover_topk\(x: torch\.Tensor, score: float\):` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms helper exists at cited location.
- probe `cumsum_x <= score` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows strict > gamma selection via <= count plus one.
- probe `score_cover_topk\(vertical, gamma\) // 128 \+ 1` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows block-count scaling after score cover.
- probe `num_vertical_blocks\[num_vertical_blocks < min_budget\] = min_budget` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows budget clamp alters prefix length.
- what would settle it: Run score_cover_topk on a vector whose cumulative sum equals gamma and compare returned k to the paper's min{k: cumsum>=gamma}.

## flexprefill-F031

**论文要求先除以 Σ¯A 再展平；代码未归一化，改以放大阈值补偿**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1661-1779`
- paper/docs (paper, PDF p.6, text lines 93-96): “# Flatten and normalize attention map ¯A← flatten( ¯A/P i, j ¯A[i,j ])”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper says normalize by the sum before flattening. The code does not explicitly divide vertical/slash by their sums, but qk is softmaxed first, so vertical already sums to 1. The claimed threshold amplification is not shown. Thus the evidence does not clearly establish the stated deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(vertical|slash)\s*/\s*(vertical|slash)\.sum\(` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **confirmed** (0 hit(s)). No explicit sum-normalization of vertical/slash in this file.
- probe `gamma\s*[*/]|[*/]\s*gamma` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **refuted** (1 hit(s)). No in-file scaling of gamma to compensate for unnormalized scores.
- probe `softmax\(qk` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). qk is row-normalized before vertical/slash, so vertical sums to 1.
- probe `score_cover_topk\((vertical|slash),\s*gamma\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). gamma is used directly as cumulative threshold on vertical/slash.
- what would settle it: Run get_active_blocks on a small input and check whether vertical/slash sum to 1 and whether gamma is scaled before score_cover_topk.

## flexprefill-F032

**论文取累计和 ≥γ 的最小前缀长度 K；代码保留累计和 ≤γ*num_blocks 的项，边界条件与阈值尺度均不同，且未显式求 K**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1661-1779`
- condition: `gamma != gamma * num_blocks`
- paper/docs (paper, PDF p.6, text lines 98-103): “Ia← argsort( ¯A) # Obtain the minimum computational budget making the sum of the scores exceedsγ K← min{k :P i∈Ia[1:k] ¯A[i]≥γ}”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper's K is min prefix with cumsum >= gamma. score_cover_topk uses sum(cumsum <= score)+1, so it returns first index with cumsum > score, a boundary difference. However the shown calls pass gamma, not gamma*num_blocks, so the claimed threshold-scale difference is not supported. The function also computes a topk count, so 'no explicit K' is overstated. Evidence is mixed.
- cited code found at the pinned commit: yes (2 location(s))
- probe `gamma\s*\*\s*num_blocks|num_blocks\s*\*\s*gamma` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **refuted** (1 hit(s)). No gamma*num_blocks scaling; contradicts threshold-scale claim.
- probe `score_cover_topk\(\s*(vertical|slash)\s*,\s*gamma\s*\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). Calls use gamma, not gamma*num_blocks.
- probe `cumsum_x\s*<=\s*score` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Code uses <= boundary, not paper's >=.
- probe `topk\s*=\s*torch\.sum\(cumsum_x\s*<=\s*score,\s*dim=-1\)\s*\+\s*1` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Explicit count+1, not min K with >=
- what would settle it: Run score_cover_topk on a cumsum with exact equality to gamma and compare to min{k: cumsum>=gamma}; also grep for gamma*num_blocks.

## flexprefill-F033

**论文要求 S 为 Ia 前 K 项；代码把 query-aware 前缀与 vertical/slash 索引取并集，S 不是纯 Ia[1:K]**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1661-1779`
- paper/docs (paper, PDF p.6): “S← Ia[1 :K]”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code computes vertical and slash scores from query/key attention, then transform_veritcal_slash_idx concatenates s_idx and v_idx and deduplicates them. Thus the active block set is a union of slash/vertical indices, not simply the first K indices Ia[1:K]. The paper's S←Ia[1:K] is therefore not implemented as stated.
- cited code found at the pinned commit: yes (2 location(s))
- probe `torch\.cat\(\(s_idx, v_idx\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows active blocks are unioned from slash and vertical indices.
- probe `vertical\[\.\.\., :1\] = torch\.inf` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows first vertical block is forced, not a pure prefix rule.
- what would settle it: Run get_active_blocks/transform_veritcal_slash_idx on a small input and compare returned block_idx to Ia[1:K].

## flexprefill-F034

**论文要求 pool(Q̂)（块池化，保留每块一个向量）与 pool(K) 相乘；代码把 Q̂ 的 block_size 行压成单一均值向量，得到 1×num_blocks 的分布，而非 num_blocks×num_blocks 的块级分布（artifact 范围：ā 的构造为 mean(Q̂)·pool(K) 而非 pool(Q̂)·pool(K)）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1676-1706`
- paper/docs (paper, PDF p.4): “where the kernel size of the pooling operation is equal to block_size”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code computes avg_qk from last_q.mean(1, keepdim=True), collapsing the block_size query rows to one vector, then multiplies by triton_bnhd_pool(k, block_size). The einsum and squeeze yield a 1×num_blocks distribution. The paper quote says the pooling kernel equals block_size, which would retain per-block Q vectors. Thus the artifact uses mean(Q̂)·pool(K), not pool(Q̂)·pool(K).
- cited code found at the pinned commit: yes (3 location(s))
- probe `last_q\.mean\(1, keepdim=True\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Q block rows are collapsed to one mean vector
- probe `avg_qk = torch\.einsum\(` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). avg_qk is built from mean Q and pooled K
- probe `triton_bnhd_pool\(k, block_size\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). K is block-pooled, unlike Q in this path
- probe `triton_bnhd_pool\(\s*(last_q|q)\b` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **confirmed** (0 hit(s)). No block pooling of Q appears in this file
- what would settle it: Run get_active_blocks on a small input and inspect avg_qk shape; it should be [b,h,num_blocks], not [b,h,num_blocks,num_blocks].

## flexprefill-F035

**池化内核无法表达论文二维 sumpool(softmax 矩阵)，实际 â 为列和向量**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1705-1716`
- paper/docs (paper, PDF p.4, text lines 60-70): “ˆa = sumpool  softmax  ˆQK⊤/ √ d  , where the kernel size of the pooling operation is equal to block_size, ¯a represents the estimated distribution and ˆa represents the true distribution.”
- paper/docs (paper, PDF p.6, text lines 31-38): “ˆa← pool  softmax  ˆQK⊤/ √ d ”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code reduces qk to a column-mean vector via qk.mean(-2) and a diagonal scalar/vector via sum_all_diagonal_matrix, then applies torch_bhn_sumpool. Both sumpool helpers accept only (b,h,n) and sum the last axis, so they cannot implement the paper's 2-D sumpool over the softmax matrix. This matches the claimed deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `vertical\s*=\s*qk\.mean\(-2\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows column-mean reduction before pooling, not 2-D softmax pooling.
- probe `def torch_bhn_sumpool\(x: torch\.Tensor, kernel_size: int\):` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms pooling helper takes a 1-D (b,h,n) tensor.
- probe `x\.view\(b, h, -1, kernel_size\)\.sum\(-1\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms sumpool sums only the last axis.
- probe `sumpool\(\s*softmax` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **confirmed** (0 hit(s)). No direct 2-D sumpool over softmax is present.
- what would settle it: A unit test comparing the code's pooled vector against a 2-D block sumpool of the softmax matrix would settle it.

## flexprefill-F036

**实验配置的 1024 预算未转化为每 head 最终激活 token 数下限，Query-Aware 头无下限**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1707-1713`
- condition: `min_budget == 1024`
- paper/docs (paper, PDF p.7): “requiring each attention head to compute at least 1024 tokens”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The snippets clamp num_vertical_blocks and num_slash_blocks to min_budget, which could be a per-head floor, but min_budget's value/units and query-aware handling are not shown. Lines 1728-1729 also set block-sparse heads to min_budget, not obviously 'no lower bound.' Thus the evidence is insufficient to decide whether the 1024-token requirement is enforced.
- cited code found at the pinned commit: yes (5 location(s))
- probe `min_budget\s*=` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). Locates min_budget assignment; value/units decide if 1024-token floor exists.
- probe `min_budget\s*=\s*1024\b` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Literal 1024 as block count would support the finding.
- probe `min_budget\s*=\s*8\b` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **refuted** (0 hit(s)). Eight blocks would convert 1024 tokens to a per-head floor.
- probe `query[_-]?aware|QueryAware|qaware` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **refuted** (0 hit(s)). Finds query-aware head logic; absence would weaken the 'no floor' claim.
- what would settle it: Inspect the min_budget assignment and log per-head selected block counts to see whether every head, including query-aware ones, gets at least 1024 tokens.

## flexprefill-F037

**ā 角色正确；â 角色由 vertical 承担，但 vertical 非论文 sumpool(softmax(Q̂Kᵀ/√d)) 块和，真实分布操作数被替换（artifact 范围：â 操作数非论文块和）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1718-1729`
- paper/docs (paper, PDF p.4): “¯a represents the estimated distribution and ˆa represents the true distribution”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited lines show `vertical` is the second argument to `square_root_js_divergence`, so it plays the true-distribution role, while `avg_qk` is the estimated distribution. However, the shown code does not define `vertical`; without its computation, the claim that it is not the paper's sumpool(softmax(QK^T/√d)) block sum is not established.
- cited code found at the pinned commit: yes (2 location(s))
- probe `vertical\s*=` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (6 hit(s)). Locates local assignment or default for `vertical`.
- probe `vertical\s*=\s*[^\n]*sumpool` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **refuted** (2 hit(s)). No local assignment ties `vertical` to sumpool.
- probe `square_root_js_divergence\(avg_qk,\s*vertical\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms `vertical` is the true-distribution operand.
- what would settle it: Trace the definition or caller of `vertical` and compare its computation to the paper's sumpool(softmax(QK^T/√d)) block sum.

## flexprefill-F038

**论文 Algorithm 2 以 JSD<τ 返回 pattern(query_specific/vertical_slash)；代码不返回模式，而用同一阈值改写预算并继续 vertical/slash 索引，阈值判定与索引选择在本机制内耦合**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1718-1729`
- paper/docs (paper, PDF p.4): “3. Distribution Comparison: We quantify the discrepancy between these distributions using the square root of the Jensen-Shannon divergence”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The code evidence clearly shows JSD<tau setting vertical/slash budgets and then calling get_active_blocks, not returning a pattern in the cited lines. However, the shown paper text only mentions sqrt-JSD and does not include Algorithm 2's return behavior, so the alleged paper/code deviation is not fully established.
- cited code found at the pinned commit: yes (2 location(s))
- probe `block_sparse_mask\s*=\s*kl_div\s*<\s*tau` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Threshold comparison creates mask used for budget rewrite.
- probe `num_vertical_blocks\[block_sparse_mask\]\s*=\s*min_budget` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Mask rewrites vertical budget instead of returning pattern.
- probe `num_slash_blocks\[block_sparse_mask\]\s*=\s*min_budget` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Mask rewrites slash budget instead of returning pattern.
- probe `get_active_blocks\(` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). Index selection continues after threshold-based budget rewrite.
- what would settle it: A trace of get_active_blocks plus the paper's Algorithm 2 text would show whether JSD<tau returns a pattern or only adjusts budgets.

## flexprefill-F039

**When pattern == "default": For the default pattern, patch_llama_attention returns without patching, leaving the original dense attention implementation in place. (flex_prefill/modules/patch.py:114)**

- category `docs_only`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/modules/patch.py:114` in `flex_prefill/modules/patch.py::patch_llama_attention`
- condition: `pattern == "default"`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: pattern=='default' is the user explicitly choosing the unpatched baseline, not a fallback of the mechanism.
- paper/docs (docstring, flex_prefill/modules/patch.py:506 (patch_model)): “- 'default': Default attention mechanism with no additional configuration.”
- code snippet (`flex_prefill/modules/patch.py:114`): `if pattern == 'default':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/modules/patch.py:114
- contrast run: branch not taken at flex_prefill/modules/patch.py:114
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'pattern' is not an integer (value 'flex_prefill')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The recorded call_chain[0] flex_prefill_attention is a GPU attention kernel entry that does not call patch_llama_attention; reaching the Region requires the deeper chain function…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F039/execution_report.json`

## flexprefill-F040

**When not ('h100' in gpu_name) and not ('a100' in gpu_name) and not ('4090' in gpu_name): if head_large and block_large: (flex_prefill/ops/flex_prefill_attention.py:88)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:88-96` in `flex_prefill/ops/flex_prefill_attention.py::get_num_warps_stages`
- condition: `not ('h100' in gpu_name) and not ('a100' in gpu_name) and not ('4090' in gpu_name)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:88`): `if head_large and block_large:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown lines only implement head_large/block_large warp/stage selection; the claimed gpu_name exclusion is not visible. It could be on an omitted preceding line, so the snippet neither confirms nor contradicts. No paper evidence is recorded.
- cited code found at the pinned commit: yes (1 location(s))
- probe `gpu_name` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (6 hit(s)). Hit shows GPU-name gating exists; miss shows no such condition.
- probe `h100|a100|4090` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (3 hit(s)). Hit shows specific GPU exclusions; miss shows none.
- probe `not\s*\(\s*['"]h100['"]\s+in\s+gpu_name\s*\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **refuted** (0 hit(s)). Hit confirms exact exclusion condition; miss refutes it.
- what would settle it: Inspect lines around 88 or search the file for the gpu_name/h100/a100/4090 exclusion; presence confirms, absence refutes.

## flexprefill-F004

**When not (q_len == 1): AssertionError (flex_prefill/ops/flex_prefill_attention.py:865)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:865` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (q_len == 1)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:865`): `assert q_len == 1`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited line is exactly `assert q_len == 1`; in Python this raises AssertionError whenever `q_len != 1`. The reachability note may affect whether it triggers in practice, but the shown code directly supports the stated conditional behavior. No paper evidence is needed to verify this code-level assertion.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+q_len\s*==\s*1` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). Hit confirms the cited assertion exists in the file.
- what would settle it: A static call-path analysis or a run with q_len != 1 reaching line 865 would confirm whether the AssertionError is actually reachable.

## flexprefill-F041

**When not (q.dtype == torch.bfloat16): AssertionError (flex_prefill/ops/flex_prefill_attention.py:868)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:868` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (q.dtype == torch.bfloat16)`
- paper/docs (readme, README.md / FlexPrefill Sparse Attention Function): “Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precision.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:868`): `assert q.dtype == torch.bfloat16`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper note says the current version has only been tested with bfloat16 precision, which is weaker than the code's hard assertion that q.dtype must equal torch.bfloat16. The shown line directly enforces bfloat16 and raises AssertionError otherwise, so the artifact is stricter than the paper's stated testing limitation.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+q\.dtype\s*==\s*torch\.bfloat16` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (5 hit(s)). Hit shows code enforces bfloat16, matching the finding.
- probe `only been tested with bfloat16` in `README.md` expected present: **not_run** (0 hit(s)). Hit shows paper states testing limitation, not hard enforcement.
- what would settle it: Run the function with a non-bfloat16 q tensor and observe whether the assertion at line 868 fails.

## flexprefill-F042

**When not (head_dim in {16, 32, 64, 128}): 'only support head_dim in {16, 32, 64, 128}' (flex_prefill/ops/flex_prefill_attention.py:869)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:869` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (head_dim in {16, 32, 64, 128})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:869`): `assert head_dim in {16, 32, 64, 128}`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The pinned code at line 869 contains exactly the asserted membership check and error message. That directly supports the claimed rejection for head_dim outside {16,32,64,128}. The 'undisclosed' label is not independently verifiable because no paper evidence is recorded, but the code-behavior portion of the finding is supported.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert head_dim in \{16, 32, 64, 128\}` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (5 hit(s)). Hit shows the exact head_dim restriction exists in the file.
- what would settle it: Static inspection of line 869, or a call with head_dim=256 producing the AssertionError, would confirm the restriction.

## flexprefill-F043

**When not (block_size in {16, 32, 64, 128}): 'only support block size in {16, 32, 64, 128}' (flex_prefill/ops/flex_prefill_attention.py:870)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:870-875` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (block_size in {16, 32, 64, 128})`
- paper/docs (docstring, flex_prefill/ops/flex_prefill_attention.py:850 (triton_block_wise_decode_attention)): “block_size (int): Block size, only support 16, 32, 64 and 128.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:870`): `assert block_size in {16, 32, 64, 128}`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The pinned code asserts block_size is in {16, 32, 64, 128} with the exact rejection message, and the paper's docstring states the same supported set. This is a documented restriction enforced by an assertion, so the evidence supports the docs_only finding rather than showing a behavioral mismatch.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert block_size in \{\s*16,\s*32,\s*64,\s*128,\s*\}` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **refuted** (0 hit(s)). Confirms the code enforces the documented block-size set.
- probe `only support 16, 32, 64 and 128` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (3 hit(s)). Confirms the paper docstring documents the same restriction.
- what would settle it: Inspect the pinned source to verify the assertion and docstring both specify the same block-size set.

## flexprefill-F044

**When not (num_blocks <= triton.cdiv(k_len, block_size)): AssertionError (flex_prefill/ops/flex_prefill_attention.py:876)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:876` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (num_blocks <= triton.cdiv(k_len, block_size))`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:876`): `assert num_blocks <= triton.cdiv(k_len, block_size)`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited line confirms an assert with that condition, so the code-level assertion exists. But no paper evidence is shown, and the Step 4 note says no values satisfy path/condition/scope, so whether this is an undisclosed, reachable discrepancy is not established.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+num_blocks\s*<=\s*triton\.cdiv\(k_len,\s*block_size\)` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms the cited assertion exists in the file.
- what would settle it: Check the paper for disclosure and run the op with num_blocks > triton.cdiv(k_len, block_size) to see whether the assertion is reachable and raises.

## flexprefill-F045

**When not (num_q_heads % num_kv_heads == 0): AssertionError (flex_prefill/ops/flex_prefill_attention.py:878)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:878` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (num_q_heads % num_kv_heads == 0)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:878`): `assert num_q_heads % num_kv_heads == 0`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code contains exactly the asserted condition: line 878 asserts num_q_heads % num_kv_heads == 0. In Python, if that condition is false, an AssertionError is raised at that line. The finding matches the visible code, and no contrary evidence is shown.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+num_q_heads\s*%\s*num_kv_heads\s*==\s*0` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (4 hit(s)). Confirms the divisibility assertion exists at the cited location.
- what would settle it: Run the code with num_q_heads not divisible by num_kv_heads and observe an AssertionError at line 878.

## flexprefill-F005

**When not (q_len == k_len): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1219)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1219` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (q_len == k_len)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1219`): `assert q_len == k_len`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. Line 1219 does contain `assert q_len == k_len`, so the assertion exists. However, the Step 4 note states this path is unreachable through the call chain; therefore the claimed rejection cannot occur. The code-level line alone does not establish the behavioral effect.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+q_len\s*==\s*k_len` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). Confirms the assert exists; does not show reachability.
- what would settle it: Trace the call chain or run the entry function with q_len != k_len to see whether line 1219 is reachable.

## flexprefill-F046

**When not (head_dim <= 256): 'only support head_dim <= 256' (flex_prefill/ops/flex_prefill_attention.py:1220)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1220` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (head_dim <= 256)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1220`): `assert head_dim <= 256`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The pinned line is an unconditional assert head_dim <= 256 with the exact message, so head_dim >256 raises AssertionError. That directly supports the stated rejection behavior. The 'undisclosed' classification cannot be verified from the shown record because no paper evidence is included, but the code-level finding is supported.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+head_dim\s*<=\s*256\s*,\s*"only support head_dim <= 256"` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Hit shows the exact hard limit assertion is present.
- what would settle it: A text search for the exact assert in the pinned file confirms the limit; running with head_dim=257 would show the AssertionError.

## flexprefill-F047

**When head_dim <= 128: For head_dim <= 128 only block_size in {32,64,128} is allowed; otherwise (128 < head_dim <= 256) only {32,64} is allowed, so the accepted block_size set depends on head_dim. (flex_prefill/ops/flex_prefill_attention.py:1221)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1221` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `head_dim <= 128`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: flex_prefill_attention already asserts head_dim in {16,32,64,128}, so the head_dim>128 branch with its {32,64} restriction is unreachable through the mechanism.
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1221`): `if head_dim <= 128:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The single shown line only establishes a head_dim<=128 branch; it does not show any block_size validation or the alternate 128<head_dim<=256 set. Without the branch body or paper evidence, the claimed dependency is not demonstrated. Text probes could locate the constraints, but the current evidence is insufficient.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if\s+head_dim\s*<=\s*128\s*:` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms the head_dim<=128 branch exists at the cited location.
- probe `block_size\s*(?:in|==|not in)\s*[^\n]*\b32\b[^\n]*\b64\b[^\n]*\b128\b` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows block_size is gated to include 32,64,128.
- probe `128\s*<\s*head_dim\s*<=\s*256` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Shows an alternate upper head_dim range branch exists.
- what would settle it: Inspect the body after line 1221 to see whether block_size is validated against {32,64,128} for head_dim<=128 and {32,64} otherwise.

## flexprefill-F048

**When not (block_size in {32, 64}): 'only support block size in {32, 64} if 128 < head_dim <= 256' (flex_prefill/ops/flex_prefill_attention.py:1228)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1228-1231` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (block_size in {32, 64})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1228`): `assert block_size in {32, 64}`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown lines contain an assert that block_size must be in {32,64} with the exact quoted message. Therefore a block_size outside that set triggers the rejection described. The snippet does not show the enclosing head_dim guard, and no paper evidence is recorded, so the 'undisclosed' aspect is not independently verified; however, the code-level rejection matches the finding.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+block_size\s+in\s+\{\s*32\s*,\s*64\s*\}` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **refuted** (0 hit(s)). Confirms code rejects block sizes outside {32,64}.
- probe `only support block size in \{32, 64\} if 128 < head_dim <= 256` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms exact rejection message quoted in finding.
- what would settle it: A unit test invoking the code path with block_size=16 and head_dim in (128,256] would confirm the assertion rejects it.

## flexprefill-F049

**When not (int(triton.__version__.split('.')[0]) >= 3): warnings.warn('triton version greater than 3.0.0 is required for faster attention') (flex_prefill/ops/flex_prefill_attention.py:1270)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1270-1272` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (int(triton.__version__.split('.')[0]) >= 3)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1270`): `warnings.warn('triton version greater than 3.0.0 is required for faster attention')`

**Not tested** (`outcome_unsupported`): effect type 'other': the effect is a warning or log line; the harness has no oracle for emitted messages yet

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown snippet only contains the warning call; it does not show the claimed `if not (int(triton.__version__.split('.')[0]) >= 3)` guard. Without the surrounding condition, the version-gating claim is not established by the evidence shown.
- cited code found at the pinned commit: yes (1 location(s))
- probe `int\s*\(\s*triton\.__version__\.split\(['"]\.['"]\)\[0\]\s*\)\s*>=\s*3` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Hit shows the version guard exists; miss leaves the finding unverified.
- what would settle it: Inspect the surrounding lines to verify the warning is inside the stated triton major-version guard.

## flexprefill-F010

**When not (d in {16, 32, 64, 128}): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1450)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1450` in `flex_prefill/ops/flex_prefill_attention.py::triton_bnhd_pool`
- condition: `not (d in {16, 32, 64, 128})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1450`): `assert d in {16, 32, 64, 128}`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Line 1450 exactly contains the asserted set membership, so the guard exists. However, the Step 4 note says the condition is unreachable through the found call chains, and no paper evidence is recorded to show the restriction is undisclosed. Thus the code fact is confirmed but the claimed runtime effect/difference is not.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert d in \{16, 32, 64, 128\}` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms the assertion guard exists at the cited line; does not prove reachability.
- what would settle it: Trace all call sites of this function to see whether d can be outside {16,32,64,128}; if none can, the assertion is unreachable.

## flexprefill-F011

**When not (kernel_size in {16, 32, 64, 128, 256, 512}): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1451)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1451` in `flex_prefill/ops/flex_prefill_attention.py::triton_bnhd_pool`
- condition: `not (kernel_size in {16, 32, 64, 128, 256, 512})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1451`): `assert kernel_size in {16, 32, 64, 128, 256, 512}`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited line is an assert statement that exactly enforces kernel_size in the allowed set; if reached with any other value, Python raises AssertionError. The reachability note is a caveat, but the finding as stated about the assertion is directly evidenced by the code. No paper evidence is needed for this code-level claim.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+kernel_size\s+in\s+\{16,\s*32,\s*64,\s*128,\s*256,\s*512\}` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (2 hit(s)). Hit shows the asserted allowed-size check is present at the cited line.
- what would settle it: Run the function with an invalid kernel_size and observe whether the assertion is reached and raises AssertionError.

## flexprefill-F050

**When block_size != 128: hard-coded 128 in `score_cover_topk(vertical, gamma) // 128` while parameter `block_size` is in scope (flex_prefill/ops/flex_prefill_attention.py:1708)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1708` in `flex_prefill/ops/flex_prefill_attention.py::get_active_blocks`
- condition: `block_size != 128`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1708`): `num_vertical_blocks = score_cover_topk(vertical, gamma) // 128 + 1`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line literally divides by 128 rather than block_size. Text search can confirm the expression and that block_size is not used in it; a signature search can confirm block_size exists in the file. This supports the hard-coded-constant claim, though exact scope at line 1708 needs enclosing-function inspection.
- cited code found at the pinned commit: yes (1 location(s))
- probe `score_cover_topk\(vertical, gamma\) // 128` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Hard-coded 128 appears in the block-count expression.
- probe `score_cover_topk\(vertical, gamma\) // block_size` in `flex_prefill/ops/flex_prefill_attention.py` expected absent: **confirmed** (0 hit(s)). Expression does not use block_size; control confirms line exists.
- probe `def [A-Za-z_][A-Za-z0-9_]*\([^)]*block_size` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). A function signature in the file accepts block_size.
- what would settle it: Inspect the enclosing function signature at line 1708 and run with block_size=64 to see whether the divisor remains 128.

## flexprefill-F025

**When kl_div < tau: per-element branch stored in block_sparse_mask (flex_prefill/ops/flex_prefill_attention.py:1727)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `in_scope`
- code: `flex_prefill/ops/flex_prefill_attention.py:1727` in `flex_prefill/ops/flex_prefill_attention.py::get_active_blocks`
- condition: `kl_div < tau`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1727`): `block_sparse_mask = kl_div < tau`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line directly assigns block_sparse_mask to the per-element boolean tensor kl_div < tau. That matches the finding that the per-element condition is stored in block_sparse_mask when kl_div is below tau. No paper evidence is needed to verify this code-level behavior.
- cited code found at the pinned commit: yes (1 location(s))
- probe `block_sparse_mask\s*=\s*kl_div\s*<\s*tau` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms the exact assignment claimed by the finding.
- what would settle it: A text search confirming the exact assignment block_sparse_mask = kl_div < tau in the pinned file would settle it.

## flexprefill-F051

**When not (is_flash_attn_2_available()): flash_attn_func = triton_flash_attention (flex_prefill/ops/flex_prefill_attention.py:1787)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1787` in `flex_prefill/ops/flex_prefill_attention.py::<module>`
- condition: `not (is_flash_attn_2_available())`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1787`): `flash_attn_func = triton_flash_attention`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code at line 1787 assigns flash_attn_func = triton_flash_attention, matching the finding. The finding states this occurs when FlashAttention 2 is unavailable; the line alone does not show the enclosing condition, but the cited line is consistent with the claim. No paper evidence is recorded, so this is an undisclosed implementation detail rather than a contradiction.
- cited code found at the pinned commit: yes (1 location(s))
- probe `flash_attn_func\s*=\s*triton_flash_attention` in `flex_prefill/ops/flex_prefill_attention.py` expected present: **confirmed** (1 hit(s)). Confirms the fallback assignment exists in the cited file.
- what would settle it: Inspect the surrounding conditional to verify that the assignment is guarded by not is_flash_attn_2_available().

## flexprefill-F052

**When not (batch_size == 1): 'only support batch size 1 for now' (flex_prefill/ops/flex_prefill_attention.py:1824)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1824` in `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`
- condition: `not (batch_size == 1)`
- paper/docs (readme, README.md / FlexPrefill Sparse Attention Function): “Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precision.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1824`): `assert batch_size == 1`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1824
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1824
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/flexprefill/flexprefill-F052/execution_report.json`

## flexprefill-F053

**When q_len == 1: returns via flash_attn_func, triton_flash_attention (flex_prefill/ops/flex_prefill_attention.py:1825)**

- category `docs_only`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1825-1835` in `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`
- condition: `q_len == 1`
- paper/docs (docstring, flex_prefill/ops/flex_prefill_attention.py:1804 (flex_prefill_attention)): “If query length is 1, will use flash decoding attention.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1825`): `if q_len == 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at flex_prefill/ops/flex_prefill_attention.py:1825
- contrast run: branch not taken at flex_prefill/ops/flex_prefill_attention.py:1825
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/flexprefill/flexprefill-F053/execution_report.json`

## flexprefill-F054

**When not (block_size in {16, 32, 64, 128}): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1838)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1838` in `flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`
- condition: `not (block_size in {16, 32, 64, 128})`
- paper/docs (docstring, flex_prefill/ops/flex_prefill_attention.py:850 (triton_block_wise_decode_attention)): “block_size (int): Block size, only support 16, 32, 64 and 128.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1838`): `assert block_size in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at flex_prefill/ops/flex_prefill_attention.py:1838
- contrast run: no exception at flex_prefill/ops/flex_prefill_attention.py:1838
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/flexprefill/flexprefill-F054/execution_report.json`

## flexprefill-F055

**When block_size not in {16, 32, 64, 128}: Caller-supplied block_size outside the fixed set aborts execution via assertion. (flex_prefill/ops/vertical_slash_attention.py:553)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/vertical_slash_attention.py:553` in `flex_prefill/ops/vertical_slash_attention.py::vertical_slash_attention`
- condition: `block_size not in {16, 32, 64, 128}`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: The assert is in vertical_slash_attention, the MInference-style vertical_slash baseline, not on FlexPrefill's own path (flex_prefill_attention).
- paper/docs (docstring, flex_prefill/ops/flex_prefill_attention.py:850 (triton_block_wise_decode_attention)): “block_size (int): Block size, only support 16, 32, 64 and 128.”
- code snippet (`flex_prefill/ops/vertical_slash_attention.py:553`): `assert block_size in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at flex_prefill/ops/vertical_slash_attention.py:553
- contrast run: no exception at flex_prefill/ops/vertical_slash_attention.py:553
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: the hand-off entry flex_prefill_attention does not call vertical_slash_attention at the pinned commit (the step-4 review note says the vertical-slash baseline is not on FlexPrefi…
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexprefill/flexprefill-F055/execution_report.json`

## flexprefill-F056

**论文要求单卡 A100 80GB；脚本未固定设备数量或型号，accelerate 可多进程运行**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:16-45`
- paper/docs (paper, PDF p.7): “Our experiments are conducted in a computing environment equipped with a single NVIDIA A100 GPU with 80GB of memory.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The scripts invoke accelerate launch repeatedly without --num_processes, --gpu_ids, CUDA_VISIBLE_DEVICES, or model/device pinning. Thus they do not enforce the paper's single A100 80GB setup; accelerate can be configured for multiple processes/GPUs. The evidence supports the mismatch, though it does not show an actual multi-GPU run.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?:--num_processes|--gpu_ids|--multi_gpu|CUDA_VISIBLE_DEVICES|--num_machines)` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). No explicit device-count pinning in RULER script.
- probe `(?:--num_processes|--gpu_ids|--multi_gpu|CUDA_VISIBLE_DEVICES|--num_machines)` in `experiments/scripts/flex_prefill/infinitebench.sh` expected absent: **confirmed** (0 hit(s)). No explicit device-count pinning in InfiniteBench script.
- the claim concerns behaviour that needs a GPU, an accelerator or a real run
- what would settle it: Inspect the accelerate configuration or run the scripts and record GPU/process count to see whether more than one A100 is used.

## flexprefill-F057

**论文要求的上界推导在实验路径无对应实现或检验**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.19): “= (1−aS) LX j=1 |vj|”
- paper/docs (paper, PDF p.19): “LetaS =P j∈Saj. Then, ak≤ aS fork∈ S, and ak≤ 1−aS fork̸∈ S.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown code is only a shell launcher configuring flex_prefill; it does not expose the attention implementation or tests. Absence of the paper's a_S/a_k upper-bound derivation in a launch script is expected and cannot establish that no corresponding implementation or check exists anywhere in the experiment path. The evidence neither confirms nor contradicts the broad missing-implementation claim.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)(aS|upper.?bound|a_k|1\s*-\s*aS)` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **refuted** (6 hit(s)). Launch script has no upper-bound derivation/check.
- probe `(?i)(aS|upper.?bound|a_k|1\s*-\s*aS)` in `experiments/benchmark/run_ruler.py` expected absent: **not_run** (0 hit(s)). Benchmark entrypoint lacks bound check; not attention implementation.
- what would settle it: Inspect the flex_prefill attention implementation and tests for any computation or assertion of the a_S and a_k bounds.

## flexprefill-F058

**论文要求显式连续松弛步骤；代码无该步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 2: Relax Binary Variables Relaxing to continuous variables:”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited evidence is only a shell launch script with flex_prefill config flags. It does not show the flex_prefill implementation, so it cannot establish that the paper's continuous-relaxation Step 2 is absent. The paper excerpt alone states a requirement; no code path implementing or omitting relaxation is shown.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)relax` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). Launch script lacks relaxation term; does not prove implementation absent.
- what would settle it: Inspect the flex_prefill attention/implementation code for any continuous relaxation or binary-variable handling corresponding to paper Step 2.

## flexprefill-F059

**论文要求构造 Lagrangian；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 3: Lagrangian Formulation Let’s form the Lagrangian for the primal problem:”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited evidence is only a shell launch script; it neither implements nor rules out a Lagrangian in the Python attention/benchmark code. The paper's Step 3 alone does not establish that the pinned code lacks it. The actual flex_prefill implementation must be inspected.
- cited code found at the pinned commit: yes (1 location(s))
- probe `Lagrangian|lagrangian|Lagrange|lagrange` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). Shell script lacks Lagrangian mention; not proof of implementation absence.
- probe `Lagrangian|lagrangian|Lagrange|lagrange` in `experiments/benchmark/run_ruler.py` expected absent: **not_run** (0 hit(s)). Benchmark entrypoint lacks Lagrangian mention; imported modules may still contain it.
- what would settle it: Inspect the flex_prefill attention implementation and its call graph for Lagrangian construction or equivalent constrained-optimization code.

## flexprefill-F060

**论文要求 KKT 条件；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 4: KKT Conditions The KKT conditions give:”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. code was found but no probe could be run on it

- reading: **unclear**. The cited code is only a shell launcher for run_ruler with flex_prefill config. It does not show the flex_prefill implementation, so absence of KKT there cannot establish that KKT conditions are unimplemented. The paper's Step 4 may be a theoretical derivation rather than a code requirement. More implementation evidence is needed.
- cited code found at the pinned commit: yes (1 location(s))
- what would settle it: Inspect the flex_prefill implementation for KKT/dual-variable logic or constrained-optimization solving; finding none would confirm the claim.

## flexprefill-F061

**论文要求该代数表达；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.19, text lines 51-61): “= X j̸∈S ajvj− 1P j∈Saj − 1 !X j′∈S aj′vj′”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. code was found but no probe could be run on it

- reading: **unclear**. The cited code is only a shell script launching run_ruler with flex_prefill config. It does not show the attention implementation, so it cannot establish that the paper's algebraic expression is absent from the code path. The paper formula is shown, but the code evidence is insufficient to support the not_implemented claim.
- cited code found at the pinned commit: yes (1 location(s))
- what would settle it: Inspect the flex_prefill attention implementation for the paper's formula terms, or run controlled inputs and compare outputs against the algebraic expression.

## flexprefill-F062

**论文要求陈述该约束问题；代码无对应形式化**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.19): “min S |A(Q, K, V )− A(Q, K, V, S)| subject to |S|≤ γS S⊆{ (i,j )| 1≤j≤i, i,j∈ Z} (4)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited script only passes flex_prefill_gamma=0.95 as a configuration flag; it shows no implementation of the paper's constrained subset-selection objective (Eq. 4). The evidence is consistent with the claim that the formalized optimization is absent from the cited code path, though a full-repo search would be needed to rule out implementation elsewhere.
- cited code found at the pinned commit: yes (1 location(s))
- probe `flex_prefill_gamma\s*=\s*0\.95` in `experiments/scripts/flex_prefill/ruler.sh` expected present: **confirmed** (2 hit(s)). Gamma is only passed as a config flag in the cited script.
- probe `subject\s+to|\|S\|\s*≤|gamma_S|min\s+S` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). No Eq. 4 constrained-optimization formalization appears in the cited script.
- what would settle it: Search the full repository for any function implementing Eq. 4 and check whether flex_prefill_gamma feeds a subset-selection optimizer.

## flexprefill-F063

**论文要求二值变量重写；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 1: Binary Variables Ifzj = 1 ifj∈S andzj = 0 otherwise, the primal objective is: max zj∈{0,1} LX j=1 zj exp(xj)PL j′=1 exp(xj′) , subject to LX j=1 zj≤γS”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper excerpt does define a binary-variable objective, but the shown code is only a launcher script passing gamma/tau settings. It does not expose the flex_prefill implementation, so it cannot establish that the binary-variable reformulation is absent from the code. The evidence is consistent with a gamma/tau heuristic but insufficient to prove the claimed gap.
- cited code found at the pinned commit: yes (1 location(s))
- probe `flex_prefill_gamma` in `experiments/scripts/flex_prefill/ruler.sh` expected present: **confirmed** (4 hit(s)). Launcher configures gamma heuristic, matching cited code path.
- probe `\b(zj|binary|objective)\b` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). No binary-variable logic in launcher; absence alone cannot prove no implementation.
- what would settle it: Inspect the flex_prefill implementation for Eq.7 binary variables/objective; if only gamma/tau budget logic exists, the finding is confirmed.

## flexprefill-F064

**论文要求平稳性条件；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “1. Stationarity: ∂L ∂zj =− exp(xj)PL j′=1 exp(xj′) +λ−µj +νj = 0”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper excerpt states a stationarity equation in a derivation, but the code evidence is only a shell script launching RULER with flex_prefill config. It does not show whether the implementation checks or enforces stationarity, nor whether the paper treats it as a runtime requirement. Absence in this script cannot establish absence in the codebase.
- cited code found at the pinned commit: yes (1 location(s))
- probe `stationarity|stationary|multiplier|\blambda\b|\bmu\b|\bnu\b` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). Script lacks stationarity terms; does not prove implementation absence.
- what would settle it: Inspect the flex_prefill implementation for stationarity or multiplier checks and clarify whether the paper's equation is only a derivation condition.

## flexprefill-F065

**论文要求互补松弛；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “2. Complementary slackness: λ( LX j=1 zj−γS) = 0 µjzj = 0 νj(zj− 1) = 0”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited code is only a shell launcher for RULER benchmark runs with flex_prefill config. It does not show the optimization implementation, so absence of complementary-slackness terms there cannot establish that the method is unimplemented. The paper's equations are mathematical conditions, not necessarily explicit code.
- cited code found at the pinned commit: yes (1 location(s))
- probe `complementary|slackness|lambda|mu|nu` in `experiments/scripts/flex_prefill/ruler.sh` expected absent: **confirmed** (0 hit(s)). Launcher lacks slackness terms, but this does not prove implementation missing.
- what would settle it: Inspect the flex_prefill attention/optimization implementation for variables or logic enforcing z, lambda, mu, nu complementary-slackness conditions.

