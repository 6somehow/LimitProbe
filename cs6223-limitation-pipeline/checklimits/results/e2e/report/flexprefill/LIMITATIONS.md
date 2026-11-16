# Limitations report: FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference

- artifact: `flexprefill` (ICLR 2025 (Oral)), repository https://github.com/bytedance/FlexPrefill at `a24b27bf11`
- input: `results/step4/flexprefill/limitations_for_tests.json` (sha256 `0b8539b75ec0`), 65 Findings
- generated: 2026-11-17T02:18:11+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
- environment: **ok**

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 65 |
| tested | 29 |
| not tested | 36 |
| verdicts | yes 29 |
| levels | L1 16, L2 7, L3 6 |
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
| [flexprefill-F030](#flexprefill-f030) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1588-1591` | not tested: `no_code_location` |
| [flexprefill-F031](#flexprefill-f031) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | not tested: `no_code_location` |
| [flexprefill-F032](#flexprefill-f032) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | not tested: `no_code_location` |
| [flexprefill-F033](#flexprefill-f033) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | not tested: `no_code_location` |
| [flexprefill-F034](#flexprefill-f034) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1676-1706` | not tested: `no_code_location` |
| [flexprefill-F035](#flexprefill-f035) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1705-1716` | not tested: `no_code_location` |
| [flexprefill-F036](#flexprefill-f036) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1707-1713` | not tested: `no_code_location` |
| [flexprefill-F037](#flexprefill-f037) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | not tested: `no_code_location` |
| [flexprefill-F038](#flexprefill-f038) | impl_deviates | other | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | not tested: `no_code_location` |
| [flexprefill-F039](#flexprefill-f039) | docs_only | path_change | `flex_prefill/modules/patch.py:114` | **yes** / L1 (uncalibrated) |
| [flexprefill-F040](#flexprefill-f040) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:88-96` | not tested: `outcome_unsupported` |
| [flexprefill-F004](#flexprefill-f004) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:865` | not tested: `witness_unusable` |
| [flexprefill-F041](#flexprefill-f041) | stated_differently | reject | `flex_prefill/ops/flex_prefill_attention.py:868` | not tested: `witness_unusable` |
| [flexprefill-F042](#flexprefill-f042) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:869` | not tested: `witness_unusable` |
| [flexprefill-F043](#flexprefill-f043) | docs_only | reject | `flex_prefill/ops/flex_prefill_attention.py:870-875` | not tested: `witness_unusable` |
| [flexprefill-F044](#flexprefill-f044) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:876` | not tested: `witness_unusable` |
| [flexprefill-F045](#flexprefill-f045) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:878` | not tested: `witness_unusable` |
| [flexprefill-F005](#flexprefill-f005) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1219` | not tested: `witness_unusable` |
| [flexprefill-F046](#flexprefill-f046) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1220` | not tested: `witness_unusable` |
| [flexprefill-F047](#flexprefill-f047) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1221` | not tested: `outcome_unsupported` |
| [flexprefill-F048](#flexprefill-f048) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1228-1231` | not tested: `witness_unusable` |
| [flexprefill-F049](#flexprefill-f049) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1270-1272` | not tested: `outcome_unsupported` |
| [flexprefill-F010](#flexprefill-f010) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1450` | not tested: `witness_unusable` |
| [flexprefill-F011](#flexprefill-f011) | undisclosed | reject | `flex_prefill/ops/flex_prefill_attention.py:1451` | not tested: `witness_unusable` |
| [flexprefill-F050](#flexprefill-f050) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1708` | not tested: `outcome_unsupported` |
| [flexprefill-F025](#flexprefill-f025) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1727` | not tested: `outcome_unsupported` |
| [flexprefill-F051](#flexprefill-f051) | undisclosed | other | `flex_prefill/ops/flex_prefill_attention.py:1787` | not tested: `outcome_unsupported` |
| [flexprefill-F052](#flexprefill-f052) | docs_only | reject | `flex_prefill/ops/flex_prefill_attention.py:1824` | **yes** / L3 (uncalibrated) |
| [flexprefill-F053](#flexprefill-f053) | docs_only | path_change | `flex_prefill/ops/flex_prefill_attention.py:1825-1835` | **yes** / L1 (uncalibrated) |
| [flexprefill-F054](#flexprefill-f054) | docs_only | reject | `flex_prefill/ops/flex_prefill_attention.py:1838` | **yes** / L3 (uncalibrated) |
| [flexprefill-F055](#flexprefill-f055) | docs_only | reject | `flex_prefill/ops/vertical_slash_attention.py:553` | **yes** / L2 (uncalibrated) |
| [flexprefill-F056](#flexprefill-f056) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:16-45` | not tested: `no_code_location` |
| [flexprefill-F057](#flexprefill-f057) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F058](#flexprefill-f058) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F059](#flexprefill-f059) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F060](#flexprefill-f060) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F061](#flexprefill-f061) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F062](#flexprefill-f062) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F063](#flexprefill-f063) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F064](#flexprefill-f064) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |
| [flexprefill-F065](#flexprefill-f065) | not_implemented | other | `experiments/scripts/flex_prefill/ruler.sh:21-29` | not tested: `no_code_location` |

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
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: flex_prefill_attention (call_chain[0]) has no block_idx parameter: it calls get_active_blocks, whose transform_veritcal_slash_idx builds the list as [ [unique(...) for h in range…
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
  - D14 official entry point was called: *residual*. the official entry started first but the target line did not run inside it; reason recorded: The official entry flex_prefill_attention is called first. On CPU it reaches get_active_blocks, which launches Triton GPU kern…
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

## flexprefill-F031

**论文要求先除以 Σ¯A 再展平；代码未归一化，改以放大阈值补偿**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1661-1779`
- paper/docs (paper, PDF p.6, text lines 93-96): “# Flatten and normalize attention map ¯A← flatten( ¯A/P i, j ¯A[i,j ])”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F032

**论文取累计和 ≥γ 的最小前缀长度 K；代码保留累计和 ≤γ*num_blocks 的项，边界条件与阈值尺度均不同，且未显式求 K**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1661-1779`
- condition: `gamma != gamma * num_blocks`
- paper/docs (paper, PDF p.6, text lines 98-103): “Ia← argsort( ¯A) # Obtain the minimum computational budget making the sum of the scores exceedsγ K← min{k :P i∈Ia[1:k] ¯A[i]≥γ}”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F033

**论文要求 S 为 Ia 前 K 项；代码把 query-aware 前缀与 vertical/slash 索引取并集，S 不是纯 Ia[1:K]**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1661-1779`
- paper/docs (paper, PDF p.6): “S← Ia[1 :K]”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F034

**论文要求 pool(Q̂)（块池化，保留每块一个向量）与 pool(K) 相乘；代码把 Q̂ 的 block_size 行压成单一均值向量，得到 1×num_blocks 的分布，而非 num_blocks×num_blocks 的块级分布（artifact 范围：ā 的构造为 mean(Q̂)·pool(K) 而非 pool(Q̂)·pool(K)）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1676-1706`
- paper/docs (paper, PDF p.4): “where the kernel size of the pooling operation is equal to block_size”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F035

**池化内核无法表达论文二维 sumpool(softmax 矩阵)，实际 â 为列和向量**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1705-1716`
- paper/docs (paper, PDF p.4, text lines 60-70): “ˆa = sumpool  softmax  ˆQK⊤/ √ d  , where the kernel size of the pooling operation is equal to block_size, ¯a represents the estimated distribution and ˆa represents the true distribution.”
- paper/docs (paper, PDF p.6, text lines 31-38): “ˆa← pool  softmax  ˆQK⊤/ √ d ”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F036

**实验配置的 1024 预算未转化为每 head 最终激活 token 数下限，Query-Aware 头无下限**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1707-1713`
- condition: `min_budget == 1024`
- paper/docs (paper, PDF p.7): “requiring each attention head to compute at least 1024 tokens”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F037

**ā 角色正确；â 角色由 vertical 承担，但 vertical 非论文 sumpool(softmax(Q̂Kᵀ/√d)) 块和，真实分布操作数被替换（artifact 范围：â 操作数非论文块和）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1718-1729`
- paper/docs (paper, PDF p.4): “¯a represents the estimated distribution and ˆa represents the true distribution”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F038

**论文 Algorithm 2 以 JSD<τ 返回 pattern(query_specific/vertical_slash)；代码不返回模式，而用同一阈值改写预算并继续 vertical/slash 索引，阈值判定与索引选择在本机制内耦合**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1718-1729`
- paper/docs (paper, PDF p.4): “3. Distribution Comparison: We quantify the discrepancy between these distributions using the square root of the Jensen-Shannon divergence”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

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

## flexprefill-F004

**When not (q_len == 1): AssertionError (flex_prefill/ops/flex_prefill_attention.py:865)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:865` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (q_len == 1)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:865`): `assert q_len == 1`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F041

**When not (q.dtype == torch.bfloat16): AssertionError (flex_prefill/ops/flex_prefill_attention.py:868)**

- category `stated_differently`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:868` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (q.dtype == torch.bfloat16)`
- paper/docs (readme, README.md / FlexPrefill Sparse Attention Function): “Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precision.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:868`): `assert q.dtype == torch.bfloat16`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F042

**When not (head_dim in {16, 32, 64, 128}): 'only support head_dim in {16, 32, 64, 128}' (flex_prefill/ops/flex_prefill_attention.py:869)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:869` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (head_dim in {16, 32, 64, 128})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:869`): `assert head_dim in {16, 32, 64, 128}`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F043

**When not (block_size in {16, 32, 64, 128}): 'only support block size in {16, 32, 64, 128}' (flex_prefill/ops/flex_prefill_attention.py:870)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:870-875` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (block_size in {16, 32, 64, 128})`
- paper/docs (docstring, flex_prefill/ops/flex_prefill_attention.py:850 (triton_block_wise_decode_attention)): “block_size (int): Block size, only support 16, 32, 64 and 128.”
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:870`): `assert block_size in {16, 32, 64, 128}`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F044

**When not (num_blocks <= triton.cdiv(k_len, block_size)): AssertionError (flex_prefill/ops/flex_prefill_attention.py:876)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:876` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (num_blocks <= triton.cdiv(k_len, block_size))`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:876`): `assert num_blocks <= triton.cdiv(k_len, block_size)`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F045

**When not (num_q_heads % num_kv_heads == 0): AssertionError (flex_prefill/ops/flex_prefill_attention.py:878)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:878` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_decode_attention`
- condition: `not (num_q_heads % num_kv_heads == 0)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:878`): `assert num_q_heads % num_kv_heads == 0`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F005

**When not (q_len == k_len): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1219)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1219` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (q_len == k_len)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1219`): `assert q_len == k_len`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F046

**When not (head_dim <= 256): 'only support head_dim <= 256' (flex_prefill/ops/flex_prefill_attention.py:1220)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1220` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (head_dim <= 256)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1220`): `assert head_dim <= 256`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F047

**When head_dim <= 128: For head_dim <= 128 only block_size in {32,64,128} is allowed; otherwise (128 < head_dim <= 256) only {32,64} is allowed, so the accepted block_size set depends on head_dim. (flex_prefill/ops/flex_prefill_attention.py:1221)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1221` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `head_dim <= 128`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: flex_prefill_attention already asserts head_dim in {16,32,64,128}, so the head_dim>128 branch with its {32,64} restriction is unreachable through the mechanism.
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1221`): `if head_dim <= 128:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## flexprefill-F048

**When not (block_size in {32, 64}): 'only support block size in {32, 64} if 128 < head_dim <= 256' (flex_prefill/ops/flex_prefill_attention.py:1228)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1228-1231` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (block_size in {32, 64})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1228`): `assert block_size in {32, 64}`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F049

**When not (int(triton.__version__.split('.')[0]) >= 3): warnings.warn('triton version greater than 3.0.0 is required for faster attention') (flex_prefill/ops/flex_prefill_attention.py:1270)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1270-1272` in `flex_prefill/ops/flex_prefill_attention.py::triton_block_wise_prefill_attention`
- condition: `not (int(triton.__version__.split('.')[0]) >= 3)`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1270`): `warnings.warn('triton version greater than 3.0.0 is required for faster attention')`

**Not tested** (`outcome_unsupported`): effect type 'other': the effect is a warning or log line; the harness has no oracle for emitted messages yet

## flexprefill-F010

**When not (d in {16, 32, 64, 128}): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1450)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1450` in `flex_prefill/ops/flex_prefill_attention.py::triton_bnhd_pool`
- condition: `not (d in {16, 32, 64, 128})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1450`): `assert d in {16, 32, 64, 128}`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F011

**When not (kernel_size in {16, 32, 64, 128, 256, 512}): AssertionError (flex_prefill/ops/flex_prefill_attention.py:1451)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1451` in `flex_prefill/ops/flex_prefill_attention.py::triton_bnhd_pool`
- condition: `not (kernel_size in {16, 32, 64, 128, 256, 512})`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1451`): `assert kernel_size in {16, 32, 64, 128, 256, 512}`

**Not tested** (`witness_unusable`): witness status 'infeasible' (call_chain): step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

## flexprefill-F050

**When block_size != 128: hard-coded 128 in `score_cover_topk(vertical, gamma) // 128` while parameter `block_size` is in scope (flex_prefill/ops/flex_prefill_attention.py:1708)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1708` in `flex_prefill/ops/flex_prefill_attention.py::get_active_blocks`
- condition: `block_size != 128`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1708`): `num_vertical_blocks = score_cover_topk(vertical, gamma) // 128 + 1`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## flexprefill-F025

**When kl_div < tau: per-element branch stored in block_sparse_mask (flex_prefill/ops/flex_prefill_attention.py:1727)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `in_scope`
- code: `flex_prefill/ops/flex_prefill_attention.py:1727` in `flex_prefill/ops/flex_prefill_attention.py::get_active_blocks`
- condition: `kl_div < tau`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1727`): `block_sparse_mask = kl_div < tau`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## flexprefill-F051

**When not (is_flash_attn_2_available()): flash_attn_func = triton_flash_attention (flex_prefill/ops/flex_prefill_attention.py:1787)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `flex_prefill/ops/flex_prefill_attention.py:1787` in `flex_prefill/ops/flex_prefill_attention.py::<module>`
- condition: `not (is_flash_attn_2_available())`
- code snippet (`flex_prefill/ops/flex_prefill_attention.py:1787`): `flash_attn_func = triton_flash_attention`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

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

## flexprefill-F057

**论文要求的上界推导在实验路径无对应实现或检验**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.19): “= (1−aS) LX j=1 |vj|”
- paper/docs (paper, PDF p.19): “LetaS =P j∈Saj. Then, ak≤ aS fork∈ S, and ak≤ 1−aS fork̸∈ S.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F058

**论文要求显式连续松弛步骤；代码无该步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 2: Relax Binary Variables Relaxing to continuous variables:”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F059

**论文要求构造 Lagrangian；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 3: Lagrangian Formulation Let’s form the Lagrangian for the primal problem:”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F060

**论文要求 KKT 条件；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 4: KKT Conditions The KKT conditions give:”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F061

**论文要求该代数表达；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.19, text lines 51-61): “= X j̸∈S ajvj− 1P j∈Saj − 1 !X j′∈S aj′vj′”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F062

**论文要求陈述该约束问题；代码无对应形式化**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.19): “min S |A(Q, K, V )− A(Q, K, V, S)| subject to |S|≤ γS S⊆{ (i,j )| 1≤j≤i, i,j∈ Z} (4)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F063

**论文要求二值变量重写；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “Step 1: Binary Variables Ifzj = 1 ifj∈S andzj = 0 otherwise, the primal objective is: max zj∈{0,1} LX j=1 zj exp(xj)PL j′=1 exp(xj′) , subject to LX j=1 zj≤γS”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F064

**论文要求平稳性条件；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “1. Stationarity: ∂L ∂zj =− exp(xj)PL j′=1 exp(xj′) +λ−µj +νj = 0”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexprefill-F065

**论文要求互补松弛；代码无**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/scripts/flex_prefill/ruler.sh:21-29`
- paper/docs (paper, PDF p.20): “2. Complementary slackness: λ( LX j=1 zj−γS) = 0 µjzj = 0 νj(zj− 1) = 0”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

