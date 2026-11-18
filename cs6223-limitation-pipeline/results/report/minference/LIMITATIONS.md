# Limitations report: MInference 1.0: Accelerating Pre-filling for Long-Context LLMs via Dynamic Sparse Attention

- artifact: `minference` (NeurIPS 2024), repository https://github.com/microsoft/MInference at `427b1ddbd2`
- input: `results/step4/minference/limitations_for_tests.json` (sha256 `6f02cbec16ce`), 73 Findings
- generated: 2026-11-18T17:48:34+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
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
| Findings | 73 |
| tested | 37 |
| not tested | 36 |
| verdicts | inconclusive 10, yes 27 |
| levels | L1 19, L2 4, L3 4, invalid 1, n/a 9 |
| analysis only (not tests) | A0 10, A1 9, A2 17 |
| not tested, by reason | `no_code_location` 23, `outcome_unsupported` 13 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [minference-F001](#minference-f001) | undisclosed | reject | `minference/minference_configuration.py:56` | **yes** / L1 (uncalibrated) |
| [minference-F003](#minference-f003) | undisclosed | state | `minference/modules/minference_forward.py:165-172` | **yes** / L1 (uncalibrated) |
| [minference-F004](#minference-f004) | undisclosed | state | `minference/modules/minference_forward.py:390` | **yes** / L1 (uncalibrated) |
| [minference-F006](#minference-f006) | undisclosed | reject | `minference/modules/minference_forward.py:484-488` | **inconclusive** / invalid (uncalibrated) |
| [minference-F008](#minference-f008) | undisclosed | state | `minference/modules/minference_forward.py:681` | **inconclusive** / n/a (uncalibrated) |
| [minference-F010](#minference-f010) | undisclosed | reject | `minference/ops/block_sparse_flash_attention.py:126` | **inconclusive** / n/a (uncalibrated) |
| [minference-F011](#minference-f011) | undisclosed | reject | `minference/ops/block_sparse_flash_attention.py:127` | **yes** / L3 (uncalibrated) |
| [minference-F012](#minference-f012) | undisclosed | reject | `minference/ops/pit_sparse_flash_attention_v2.py:149` | **inconclusive** / n/a (uncalibrated) |
| [minference-F013](#minference-f013) | undisclosed | reject | `minference/ops/pit_sparse_flash_attention_v2.py:150` | **yes** / L2 (uncalibrated) |
| [minference-F014](#minference-f014) | undisclosed | reject | `minference/ops/streaming_kernel.py:414` | **yes** / L2 (uncalibrated) |
| [minference-F015](#minference-f015) | undisclosed | reject | `minference/ops/streaming_kernel.py:605` | **yes** / L3 (uncalibrated) |
| [minference-F016](#minference-f016) | undisclosed | reject | `minference/ops/streaming_kernel.py:606` | **yes** / L3 (uncalibrated) |
| [minference-F017](#minference-f017) | undisclosed | reject | `minference/patch.py:207` | **inconclusive** / n/a (uncalibrated) |
| [minference-F019](#minference-f019) | undisclosed | reject | `minference/patch.py:1253` | **inconclusive** / n/a (uncalibrated) |
| [minference-F020](#minference-f020) | undisclosed | path_change | `minference/minference_configuration.py:52` | **yes** / L1 (uncalibrated) |
| [minference-F021](#minference-f021) | undisclosed | path_change | `minference/modules/minference_forward.py:63` | **inconclusive** / n/a (uncalibrated) |
| [minference-F022](#minference-f022) | undisclosed | path_change | `minference/modules/minference_forward.py:192` | **inconclusive** / n/a (uncalibrated) |
| [minference-F023](#minference-f023) | undisclosed | path_change | `minference/modules/minference_forward.py:418-419` | **yes** / L1 (uncalibrated) |
| [minference-F024](#minference-f024) | undisclosed | path_change | `minference/modules/minference_forward.py:421` | **yes** / L1 (uncalibrated) |
| [minference-F025](#minference-f025) | undisclosed | path_change | `minference/modules/minference_forward.py:423` | **yes** / L1 (uncalibrated) |
| [minference-F026](#minference-f026) | undisclosed | path_change | `minference/modules/minference_forward.py:425-426` | **yes** / L1 (uncalibrated) |
| [minference-F027](#minference-f027) | undisclosed | path_change | `minference/modules/minference_forward.py:427` | **yes** / L1 (uncalibrated) |
| [minference-F028](#minference-f028) | undisclosed | path_change | `minference/modules/minference_forward.py:432` | **yes** / L1 (uncalibrated) |
| [minference-F029](#minference-f029) | undisclosed | path_change | `minference/modules/minference_forward.py:434` | **yes** / L1 (uncalibrated) |
| [minference-F030](#minference-f030) | undisclosed | path_change | `minference/modules/minference_forward.py:521` | **yes** / L1 (uncalibrated) |
| [minference-F031](#minference-f031) | undisclosed | path_change | `minference/modules/minference_forward.py:613` | **inconclusive** / n/a (uncalibrated) |
| [minference-F032](#minference-f032) | undisclosed | path_change | `minference/modules/minference_forward.py:756` | **yes** / L1 (uncalibrated) |
| [minference-F033](#minference-f033) | undisclosed | path_change | `minference/modules/minference_forward.py:864` | **yes** / L2 (uncalibrated) |
| [minference-F034](#minference-f034) | undisclosed | path_change | `minference/modules/snap_kv.py:321` | **yes** / L1 (uncalibrated) |
| [minference-F035](#minference-f035) | undisclosed | path_change | `minference/modules/snap_kv.py:347` | **yes** / L1 (uncalibrated) |
| [minference-F037](#minference-f037) | undisclosed | path_change | `minference/ops/streaming_kernel.py:609` | **yes** / L3 (uncalibrated) |
| [minference-F038](#minference-f038) | undisclosed | path_change | `minference/ops/streaming_kernel.py:620` | **yes** / L1 (uncalibrated) |
| [minference-F039](#minference-f039) | undisclosed | path_change | `minference/ops/streaming_kernel.py:701` | **yes** / L1 (uncalibrated) |
| [minference-F040](#minference-f040) | undisclosed | path_change | `minference/patch.py:835` | **inconclusive** / n/a (uncalibrated) |
| [minference-F041](#minference-f041) | undisclosed | path_change | `minference/patch.py:840` | **yes** / L1 (uncalibrated) |
| [minference-F042](#minference-f042) | impl_deviates | other | `csrc/vertical_slash_index.cu:27-99` | not tested: `no_code_location`, analysis A0/supports |
| [minference-F043](#minference-f043) | impl_deviates | other | `experiments/README.md:13-30` | not tested: `no_code_location`, analysis A1/unclear |
| [minference-F044](#minference-f044) | impl_deviates | other | `experiments/README.md:13-30` | not tested: `no_code_location`, analysis A2/contradicts |
| [minference-F045](#minference-f045) | impl_deviates | other | `experiments/README.md:13-30` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F046](#minference-f046) | impl_deviates | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location`, analysis A1/unclear |
| [minference-F047](#minference-f047) | impl_deviates | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location`, analysis A0/contradicts |
| [minference-F048](#minference-f048) | impl_deviates | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F049](#minference-f049) | impl_deviates | other | `minference/models_patch.py:66-73` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F050](#minference-f050) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F051](#minference-f051) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A0/contradicts |
| [minference-F052](#minference-f052) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A0/contradicts |
| [minference-F053](#minference-f053) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F054](#minference-f054) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F055](#minference-f055) | impl_deviates | other | `minference/modules/minference_forward.py:199-246` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F056](#minference-f056) | impl_deviates | other | `minference/ops/block_sparse_flash_attention.py:150-165` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F002](#minference-f002) | undisclosed | other | `minference/modules/minference_forward.py:30` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F057](#minference-f057) | undisclosed | other | `minference/modules/minference_forward.py:34` | not tested: `outcome_unsupported`, analysis A2/supports |
| [minference-F058](#minference-f058) | undisclosed | state | `minference/modules/minference_forward.py:74` | **yes** / L1 (uncalibrated) |
| [minference-F059](#minference-f059) | undisclosed | other | `minference/modules/minference_forward.py:194` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F060](#minference-f060) | undisclosed | other | `minference/modules/minference_forward.py:430` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F005](#minference-f005) | undisclosed | other | `minference/modules/minference_forward.py:441` | not tested: `outcome_unsupported`, analysis A0/supports |
| [minference-F007](#minference-f007) | undisclosed | other | `minference/modules/minference_forward.py:504` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F061](#minference-f061) | undisclosed | other | `minference/modules/minference_forward.py:523` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F062](#minference-f062) | undisclosed | other | `minference/modules/minference_forward.py:526` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F009](#minference-f009) | undisclosed | other | `minference/modules/minference_forward.py:754` | not tested: `outcome_unsupported`, analysis A0/supports |
| [minference-F036](#minference-f036) | undisclosed | other | `minference/ops/block_sparse_flash_attention.py:130` | not tested: `outcome_unsupported`, analysis A2/supports |
| [minference-F063](#minference-f063) | undisclosed | other | `minference/ops/block_sparse_flash_attention.py:164` | not tested: `outcome_unsupported`, analysis A2/supports |
| [minference-F064](#minference-f064) | undisclosed | other | `minference/ops/pit_sparse_flash_attention.py:150` | not tested: `outcome_unsupported`, analysis A2/supports |
| [minference-F065](#minference-f065) | undisclosed | path_change | `minference/ops/pit_sparse_flash_attention_v2.py:188` | **yes** / L2 (uncalibrated) |
| [minference-F018](#minference-f018) | undisclosed | other | `minference/patch.py:1252` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [minference-F066](#minference-f066) | not_implemented | other | `experiments/README.md:13-30` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F067](#minference-f067) | not_implemented | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F068](#minference-f068) | not_implemented | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location`, analysis A0/supports |
| [minference-F069](#minference-f069) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F070](#minference-f070) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A2/supports |
| [minference-F071](#minference-f071) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A0/supports |
| [minference-F072](#minference-f072) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location`, analysis A0/contradicts |
| [minference-F073](#minference-f073) | not_implemented | other | `minference/modules/minference_forward.py:199-246` | not tested: `no_code_location`, analysis A0/supports |

## minference-F001

**When config_path is None and model_name not in MODEL2PATH: If no `config_path` is given, the model name must be a key of the hard-coded `MODEL2PATH` table; any other model (including a local path or a fine-tune) aborts with an AssertionError, so the mechanism is only usable for the enumerated model list unless the caller supplies a pattern file. (minference/minference_configuration.py:56)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/minference_configuration.py:56` in `minference/minference_configuration.py::MInferenceConfig.update_config_path`
- condition: `config_path is None and model_name not in MODEL2PATH`
- code snippet (`minference/minference_configuration.py:56`): `assert model_name in MODEL2PATH`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at minference/minference_configuration.py:57
- contrast run: no exception at minference/minference_configuration.py:56
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'model_name' is not an integer (value 'Qwen/Qwen2-7B-Instruct')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The hand-off entry gather_last_q_vertical_slash_topk_v4 has no static path to update_config_path (call_chain_status: not_found). The target is exercised through its only real cal…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F001/execution_report.json`

## minference-F003

**When SEARCH_MASK is None # first call only: module-level cache initialised on first call and reused (minference/modules/minference_forward.py:165)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:165-172` in `minference/modules/minference_forward.py::search_pattern`
- condition: `SEARCH_MASK is None # first call only`
- code snippet (`minference/modules/minference_forward.py:165`): `if SEARCH_MASK is None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:165
- contrast run: branch not taken at minference/modules/minference_forward.py:165
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: the boundary variable is the prelude (program state): adjacency cannot be probed
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub; stand-in checks: torch.arange vacuous, torch.full agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F003/execution_report.json`

## minference-F004

**When "vs" in self.__dict__: Static pattern reuses vertical_topk/slash cached in self.vs from an earlier call instead of recomputing them. (minference/modules/minference_forward.py:390)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:390` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4.vertical_and_slash_kernel_static`
- condition: `"vs" in self.__dict__`
- code snippet (`minference/modules/minference_forward.py:390`): `if 'vs' in self.__dict__:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:390
- contrast run: branch not taken at minference/modules/minference_forward.py:390
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: the boundary variable is the prelude (program state): adjacency cannot be probed
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:fake
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F004/execution_report.json`

## minference-F006

**When True: raise ValueError(f'The cache structure has changed since version v4.36. If you are using {self.__class__.__name__} for a (minference/modules/minference_forward.py:484)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:484-488` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `self.layer_idx is None`
- code snippet (`minference/modules/minference_forward.py:484`): `raise ValueError(f'The cache structure has changed since version v4.36. If you are using {self.__class__.__name__} for auto-regressive decoding with k/v caching, please make sure to initialize the att`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect on positive input, none on negative input

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2, D12

- trigger run: ValueError at minference/modules/minference_forward.py:484
- contrast run: no exception at minference/modules/minference_forward.py:484
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D12 Region location and snippet match the repository: *refuted*. Region snippet differs from the repository line
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D12 (refuted): re-check Region.location against the pinned commit
- evidence: `tests/minference/minference-F006/execution_report.json`

## minference-F008

**When key_states.shape[-2] != kv_seq_len: Whether SnapKV compression runs depends on `self.kv_seq_len` cached from earlier calls: on the first (prefill) call the KV is compressed and `self.kv_seq_len` registered; on later calls the else-branch just appends to the cache. So the same input produces different KV contents depending on call history, and the sparse pattern is then computed over the co...**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:681` in `minference/modules/minference_forward.py::minference_with_snapkv_forward.forward`
- condition: `key_states.shape[-2] != kv_seq_len`
- code snippet (`minference/modules/minference_forward.py:681`): `if key_states.shape[-2] == kv_seq_len:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: AttributeError at nn/modules/module.py:1976 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: AttributeError at nn/modules/module.py:1976 before the target was reached
- contrast run: prelude call 1 failed: AttributeError at nn/modules/module.py:1976
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: the boundary variable is the prelude (program state): adjacency cannot be probed
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub; stand-in checks: torch.arange vacuous
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: the declared entry gather_last_q_vertical_slash_topk_v4 is called by the target function, so the static chain status is not_found; the state-dependent witness names the target fu…
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F008/execution_report.json`

## minference-F010

**When not (Lq == Lk and Lk == Lv): AssertionError (minference/ops/block_sparse_flash_attention.py:126)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:126` in `minference/ops/block_sparse_flash_attention.py::_triton_block_sparse_attention`
- condition: `not (Lq == Lk and Lk == Lv)`
- code snippet (`minference/ops/block_sparse_flash_attention.py:126`): `assert Lq == Lk and Lk == Lv`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- contrast run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D4 oracle is specified, located, pre-registered: *refuted*. verified tier O2, pre-registered=True
  - D5 control pair differs in one factor, negative adjacent to the boundary: *open*. a neighbour probe failed before the target was decided
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F010/execution_report.json`

## minference-F011

**When not (Lk in {16, 32, 64, 128}): AssertionError (minference/ops/block_sparse_flash_attention.py:127)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:127` in `minference/ops/block_sparse_flash_attention.py::_triton_block_sparse_attention`
- condition: `not (Lk in {16, 32, 64, 128})`
- code snippet (`minference/ops/block_sparse_flash_attention.py:127`): `assert Lk in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at minference/ops/block_sparse_flash_attention.py:127
- contrast run: no exception at minference/ops/block_sparse_flash_attention.py:127 (later RuntimeError at triton/runtime/driver.py:20)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/minference/minference-F011/execution_report.json`

## minference-F012

**When not (Lq == Lk and Lk == Lv): AssertionError (minference/ops/pit_sparse_flash_attention_v2.py:149)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention_v2.py:149` in `minference/ops/pit_sparse_flash_attention_v2.py::_triton_mixed_sparse_attention`
- condition: `not (Lq == Lk and Lk == Lv)`
- code snippet (`minference/ops/pit_sparse_flash_attention_v2.py:149`): `assert Lq == Lk and Lk == Lv`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: run failed before a result: load_error

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: run failed before a result: load_error
- contrast run: run failed before a result: load_error
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D4 oracle is specified, located, pre-registered: *refuted*. verified tier O2, pre-registered=True
  - D5 control pair differs in one factor, negative adjacent to the boundary: *open*. a neighbour probe failed before the target was decided
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F012/execution_report.json`

## minference-F013

**When not (Lk in {16, 32, 64, 128}): AssertionError (minference/ops/pit_sparse_flash_attention_v2.py:150)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention_v2.py:150` in `minference/ops/pit_sparse_flash_attention_v2.py::_triton_mixed_sparse_attention`
- condition: `not (Lk in {16, 32, 64, 128})`
- code snippet (`minference/ops/pit_sparse_flash_attention_v2.py:150`): `assert Lk in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at minference/ops/pit_sparse_flash_attention_v2.py:150
- contrast run: no exception at minference/ops/pit_sparse_flash_attention_v2.py:150
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: torch.arange agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F013/execution_report.json`

## minference-F014

**When Lk not in {16, 32, 64, 128}: Head dimension (q/k/v last dim) must be one of 16/32/64/128; other model head sizes abort the streaming attention forward. (minference/ops/streaming_kernel.py:414)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/streaming_kernel.py:414` in `minference/ops/streaming_kernel.py::_forward`
- condition: `Lk not in {16, 32, 64, 128}`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: _forward asserts head_dim in {16,32,64,128}, and streaming_forward does not pad head_dim 256/512, so models with such head sizes are rejected on the A-shape/streaming path.
- code snippet (`minference/ops/streaming_kernel.py:414`): `assert Lk in {16, 32, 64, 128}`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at minference/ops/streaming_kernel.py:414
- contrast run: no exception at minference/ops/streaming_kernel.py:414 (later RuntimeError at triton/runtime/driver.py:20)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The hand-off entry gather_last_q_vertical_slash_topk_v4 imports minference/modules/minference_forward.py, which requires flash_attn, pycuda and the precompiled minference.cuda ex…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F014/execution_report.json`

## minference-F015

**When not (q.dim() == 4): AssertionError (minference/ops/streaming_kernel.py:605)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/streaming_kernel.py:605` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `not (q.dim() == 4)`
- code snippet (`minference/ops/streaming_kernel.py:605`): `assert q.dim() == 4`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at minference/ops/streaming_kernel.py:605
- contrast run: no exception at minference/ops/streaming_kernel.py:605 (later RuntimeError at triton/runtime/driver.py:20)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/minference/minference-F015/execution_report.json`

## minference-F016

**When not (q.shape == k.shape == v.shape): AssertionError (minference/ops/streaming_kernel.py:606)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/streaming_kernel.py:606` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `not (q.shape == k.shape == v.shape)`
- code snippet (`minference/ops/streaming_kernel.py:606`): `assert q.shape == k.shape == v.shape`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: AssertionError at minference/ops/streaming_kernel.py:606
- contrast run: no exception at minference/ops/streaming_kernel.py:606 (later RuntimeError at triton/runtime/driver.py:20)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/minference/minference-F016/execution_report.json`

## minference-F017

**When output_attentions: If the caller requests attention outputs, execution is aborted by the assertion. (minference/patch.py:207)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/patch.py:207` in `minference/patch.py::huggingface_forward.hf_forward`
- condition: `output_attentions`
- code snippet (`minference/patch.py:207`): `assert not output_attentions`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- contrast run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D4 oracle is specified, located, pre-registered: *refuted*. verified tier O2, pre-registered=True
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'output_attentions' is not an integer (value False)
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F017/execution_report.json`

## minference-F019

**When not (isinstance(model, LlamaForCausalLM) or isinstance(model, MistralForCausalLM) or isinstance(model, Qwen2ForCausalLM) or model.__class__.__name__ == "MiniCPMForCausalLM" or model.__class__.__name__ == "Phi3ForCausalLM" or model.__class__.__name__ == "ChatGLMForConditionalGeneration"): If the caller passes a model that is not one of the recognized classes, patch_hf raises ValueError and ...**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/patch.py:1253` in `minference/patch.py::patch_hf`
- condition: `not (isinstance(model, LlamaForCausalLM) or isinstance(model, MistralForCausalLM) or isinstance(model, Qwen2ForCausalLM) or model.__class__.__name__ == "MiniCPMForCausalLM" or model.__class__.__name_…`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: patch_hf is reached only for the inf_llm baseline (streaming2 is rejected by the config), while the MInference path goes through minference_patch, so this class whitelist limits baseline code, not the mechanism.
- code snippet (`minference/patch.py:1253`): `raise ValueError('Only supports llama, mistral and qwen2 models.')`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- contrast run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D4 oracle is specified, located, pre-registered: *refuted*. verified tier O2, pre-registered=True
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. positive and negative differ in [], not in exactly one factor
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F019/execution_report.json`

## minference-F020

**When self.attn_type in self.STASTIC_ATTENTION_TYPES: For any `attn_type` in `STASTIC_ATTENTION_TYPES` (`minference_with_dense`, `static`, `dilated1`, `dilated2`, `streaming`, `inf_llm`, `hf`) the user-supplied `config_path` is silently discarded (`return ""`), so the searched per-head pattern is never used and a fixed/static pattern or a different attention implementation runs instead. (minfere...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/minference_configuration.py:52` in `minference/minference_configuration.py::MInferenceConfig.update_config_path`
- condition: `self.attn_type in self.STASTIC_ATTENTION_TYPES`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: For non-minference attn_types (e.g. 'static'), the user's config_path is silently dropped, so the static variant always uses the hard-coded default pattern sizes.
- code snippet (`minference/minference_configuration.py:52`): `if self.attn_type in self.STASTIC_ATTENTION_TYPES:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/minference_configuration.py:52
- contrast run: branch not taken at minference/minference_configuration.py:52
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 call chain has status not_found: the listed call_chain[0] gather_last_q_vertical_slash_topk_v4 never calls update_config_path. The target's real caller is MInferenceCo…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F020/execution_report.json`

## minference-F021

**When not (self.config_path is not None and os.path.exists(self.config_path) and self.layer_idx < len(json.load(open(self.config_path)))): The searched per-head pattern is only loaded when `config_path` exists and has an entry for `self.layer_idx`; otherwise `self.best_pattern = {}` and every head uses the hard-coded default pattern (see line 430). A missing/typo'd `config_path` therefore silent...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:63` in `minference/modules/minference_forward.py::init_minference_parameters`
- condition: `not (self.config_path is not None and os.path.exists(self.config_path) and self.layer_idx < len(json.load(open(self.config_path))))`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: With a missing config_path, or one that has too few layers, best_pattern is empty and every head silently uses the default vertical_and_slash (1000, 6096) pattern instead of the searched per-head pattern.
- code snippet (`minference/modules/minference_forward.py:63`): `if self.config_path is not None and os.path.exists(self.config_path) and (self.layer_idx < len(json.load(open(self.config_path)))):`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: run failed before a result: load_error

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: run failed before a result: load_error
- contrast run: run failed before a result: load_error
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. positive and negative differ in [], not in exactly one factor
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F021/execution_report.json`

## minference-F022

**When best_ty == "stream_llm": If streaming wins the search, it is overridden to vertical_and_slash, so the streaming variant is never actually selected. (minference/modules/minference_forward.py:192)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:192` in `minference/modules/minference_forward.py::search_pattern`
- condition: `best_ty == "stream_llm"`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: The offline pattern search can never assign the A-shape (stream_llm) pattern; it is always remapped to vertical_and_slash, so one of the paper's three patterns is effectively unused.
- code snippet (`minference/modules/minference_forward.py:192`): `if best_ty == 'stream_llm':`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- contrast run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. positive and negative differ in [], not in exactly one factor
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F022/execution_report.json`

## minference-F023

**When q_len == 1: returns via dense (minference/modules/minference_forward.py:418)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:418-419` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `q_len == 1`
- code snippet (`minference/modules/minference_forward.py:418`): `if q_len == 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:418 (later NameError at minference/modules/minference_forward.py:410)
- contrast run: branch not taken at minference/modules/minference_forward.py:418 (later AttributeError at minference/modules/minference_forward.py:421)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F023/execution_report.json`

## minference-F024

**When self.config.to_dict().get("dilated1", False): Config flag switches to the fixed 'dilated1' sparse pattern (8k local with stride 2) instead of the dynamic vertical/slash topk selection. (minference/modules/minference_forward.py:421)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:421` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("dilated1", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: dilated1 is a baseline attention type selected by attn_type, not a variant of the paper's mechanism.
- code snippet (`minference/modules/minference_forward.py:421`): `if self.config.to_dict().get('dilated1', False):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:421 (later TypeError at minference/ops/pit_sparse_flash_attention_v2.py:198)
- contrast run: branch not taken at minference/modules/minference_forward.py:421 (later TypeError at minference/ops/pit_sparse_flash_attention_v2.py:198)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F024/execution_report.json`

## minference-F025

**When self.config.to_dict().get("dilated2", False): Config flag switches to the fixed 'dilated2' sparse pattern (2k dense local + 4k strided local) instead of dynamic selection. (minference/modules/minference_forward.py:423)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:423` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("dilated2", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: dilated2 is a baseline attention type selected by attn_type, not a variant of the paper's mechanism.
- code snippet (`minference/modules/minference_forward.py:423`): `if self.config.to_dict().get('dilated2', False):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:423
- contrast run: branch not taken at minference/modules/minference_forward.py:423
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'dilated2' is not an integer (value False)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/minference/minference-F025/execution_report.json`

## minference-F026

**When self.config.to_dict().get('dense', False): returns via dense (minference/modules/minference_forward.py:425)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:425-426` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get('dense', False)`
- code snippet (`minference/modules/minference_forward.py:425`): `if self.config.to_dict().get('dense', False):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:425 (later NameError at minference/modules/minference_forward.py:410)
- contrast run: branch not taken at minference/modules/minference_forward.py:425
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub; stand-in checks: torch.arange agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F026/execution_report.json`

## minference-F027

**When self.config.to_dict().get("streaming", False): Config flag switches to streaming_forward with n_init/n_local from streaming_kwargs instead of the vertical/slash mechanism. (minference/modules/minference_forward.py:427)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:427` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("streaming", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: The streaming flag is set only by attn_type='streaming', so this is the same config-driven variant switch already covered by minference-24.
- code snippet (`minference/modules/minference_forward.py:427`): `if self.config.to_dict().get('streaming', False):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:427 (later AttributeError at minference/modules/minference_forward.py:428)
- contrast run: branch not taken at minference/modules/minference_forward.py:427 (later AttributeError at minference/modules/minference_forward.py:430)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub; stand-in checks: torch.arange agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F027/execution_report.json`

## minference-F028

**When self.config.to_dict().get("static_pattern", False): Config flag switches to vertical_and_slash_kernel_static, which caches and reuses the first computed vertical/slash indices. (minference/modules/minference_forward.py:432)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:432` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("static_pattern", False)`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: The static_pattern config (attn_type='static') switches to a kernel that computes the vertical/slash indices once and reuses them, instead of estimating them online.
- code snippet (`minference/modules/minference_forward.py:432`): `if self.config.to_dict().get('static_pattern', False):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:432 (later RuntimeError at minference/modules/minference_forward.py:2)
- contrast run: branch not taken at minference/modules/minference_forward.py:432 (later RuntimeError at minference/modules/minference_forward.py:2)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F028/execution_report.json`

## minference-F029

**When self.config.to_dict().get("vs_only", False): Config flag forces the vertical_and_slash_kernel regardless of the per-head pattern type ty. (minference/modules/minference_forward.py:434)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:434` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("vs_only", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: vs_only is real but is not exposed through MInferenceConfig/attn_type and is never set by the package, so it is a hidden debug flag.
- code snippet (`minference/modules/minference_forward.py:434`): `if self.config.to_dict().get('vs_only', False):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:434 (later NameError at minference/ops/pit_sparse_flash_attention_v2.py:189)
- contrast run: branch not taken at minference/modules/minference_forward.py:434 (later AssertionError at minference/ops/block_sparse_flash_attention.py:127)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub; stand-in checks: torch.arange agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F029/execution_report.json`

## minference-F030

**When self.layer_idx >= self.starting_layer and not self.is_search: Layers below starting_layer (or in search mode) skip the sparse mechanism and use dense flash attention / gather_qkv. (minference/modules/minference_forward.py:521)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:521` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `self.layer_idx >= self.starting_layer and not self.is_search`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: Layers below the configurable starting_layer silently run dense flash attention (or gather_qkv) instead of sparse attention.
- code snippet (`minference/modules/minference_forward.py:521`): `if self.layer_idx >= self.starting_layer and (not self.is_search):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:521
- contrast run: branch not taken at minference/modules/minference_forward.py:521
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F030/execution_report.json`

## minference-F031

**When self.layer_idx >= self.starting_layer: Layers below starting_layer use dense flash_attn_func; only layers at/after starting_layer use the sparse gather_last_q_vertical_slash_topk_v4 path. starting_layer is a constructor/config attribute deciding which algorithm runs per layer. (minference/modules/minference_forward.py:613)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:613` in `minference/modules/minference_forward.py::minference_kv_cache_cpu_forward.forward`
- condition: `self.layer_idx >= self.starting_layer`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: The starting_layer config makes layers below it use dense flash attention instead of the sparse vertical-slash path.
- code snippet (`minference/modules/minference_forward.py:613`): `if self.layer_idx >= self.starting_layer:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- contrast run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. positive and negative differ in [], not in exactly one factor
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F031/execution_report.json`

## minference-F032

**When q_len == 1: In gather_last_q_vertical_slash_topk_vllm, a single query token bypasses the sparse pattern selection and runs dense flash attention. (minference/modules/minference_forward.py:756)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:756` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_vllm`
- condition: `q_len == 1`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: In the vLLM path, decode steps (q_len==1) always use dense flash attention, so sparsity applies only to prefill.
- code snippet (`minference/modules/minference_forward.py:756`): `if q_len == 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:756 (later NameError at minference/modules/minference_forward.py:749)
- contrast run: branch not taken at minference/modules/minference_forward.py:756
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub; stand-in checks: minference.ops.block_sparse_flash_attention.block_sparse_attention agrees, torch.arange vacuous
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 call chain [gather_last_q_vertical_slash_topk_v4, gather_last_q_vertical_slash_topk_vllm] is not a real path: v4 never calls vllm, and vllm is only reached from minfer…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F032/execution_report.json`

## minference-F033

**When kv_cache is None or prefill_meta.block_tables.numel() == 0: Only when there is no KV cache or empty block tables does the code run the MInference sparse prefill (minference_prefill_func); otherwise it falls to PagedAttention.forward_prefix, a different (dense/prefix) implementation. (minference/modules/minference_forward.py:864)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:864` in `minference/modules/minference_forward.py::minference_vllm_forward.forward`
- condition: `kv_cache is None or prefill_meta.block_tables.numel() == 0`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: In the vLLM integration, prefill with prefix cache or chunked prefill (non-empty block tables) silently uses dense PagedAttention.forward_prefix instead of sparse attention.
- code snippet (`minference/modules/minference_forward.py:864`): `if kv_cache is None or prefill_meta.block_tables.numel() == 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at minference/modules/minference_forward.py:864
- contrast run: branch not taken at minference/modules/minference_forward.py:864
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: minference.modules.minference_forward.PagedAttention.split_kv_cache agrees, minference.modules.minference_forward.PagedAtt…
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Step 4 recorded call_chain_status=not_found: the listed sparse-kernel entry does not statically or dynamically reach the vLLM wrapper minference_vllm_forward.forward, so the driv…
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F033/execution_report.json`

## minference-F034

**When q_len < self.max_capacity_prompt: When the prompt length is below max_capacity_prompt, update_kv returns the full key/value states unchanged, silently skipping the SnapKV compression (dense baseline) instead of applying the sparse selection. (minference/modules/snap_kv.py:321)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/snap_kv.py:321` in `minference/modules/snap_kv.py::SnapKVCluster.update_kv`
- condition: `q_len < self.max_capacity_prompt`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Skipping compression for short prompts is normal SnapKV behaviour in an optional add-on, not a limit of MInference's sparse prefill.
- code snippet (`minference/modules/snap_kv.py:321`): `if q_len < self.max_capacity_prompt:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/snap_kv.py:321
- contrast run: branch not taken at minference/modules/snap_kv.py:321
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Step 4 reports call_chain_status=not_found: gather_last_q_vertical_slash_topk_v4 builds attention masks and does not call SnapKVCluster.update_kv. In the source, update_kv is cal…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F034/execution_report.json`

## minference-F035

**When self.pooling == "avgpool": The pooling attribute (set from config.pooling in init_snapkv) selects avg_pool1d vs max_pool1d for the attention-score smoothing that drives token selection, changing which KV entries are kept. (minference/modules/snap_kv.py:347)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/snap_kv.py:347` in `minference/modules/snap_kv.py::SnapKVCluster.update_kv`
- condition: `self.pooling == "avgpool"`
- code snippet (`minference/modules/snap_kv.py:347`): `if self.pooling == 'avgpool':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/snap_kv.py:347
- contrast run: branch not taken at minference/modules/snap_kv.py:347
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'pooling' is not an integer (value 'maxpool')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Step 4 reports call_chain_status not_found: the declared entry gather_last_q_vertical_slash_topk_v4 never calls SnapKVCluster.update_kv. update_kv is invoked from minference_with…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F035/execution_report.json`

## minference-F037

**When head_dim not in [16, 32, 64, 128, 256, 512]: For head dimensions not in the hard-coded list, q/k/v are zero-padded to the next power of two before the streaming kernel runs, changing the computation path (and the padded dims are sliced off at line 633). (minference/ops/streaming_kernel.py:609)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/streaming_kernel.py:609` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `head_dim not in [16, 32, 64, 128, 256, 512]`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Zero-padding head_dim to a power of two gives the same result and is an internal kernel-compatibility detail.
- code snippet (`minference/ops/streaming_kernel.py:609`): `if head_dim not in [16, 32, 64, 128, 256, 512]:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at minference/ops/streaming_kernel.py:609 (later RuntimeError at triton/runtime/driver.py:20)
- contrast run: branch not taken at minference/ops/streaming_kernel.py:609 (later RuntimeError at triton/runtime/driver.py:20)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/minference/minference-F037/execution_report.json`

## minference-F038

**When k_len > n_local: The streaming (StreamingLLM) variant only keeps the `n_init` sink tokens when the KV length exceeds `n_local`; for shorter sequences it degenerates to plain sliding-window attention with no attention sinks, so the same head runs a different algorithm depending on the input length. `n_init`/`n_local` come from `config.streaming_kwargs`. (minference/ops/streaming_kernel.py:620)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/streaming_kernel.py:620` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `k_len > n_local`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: When k_len <= n_local the sliding window already covers every key, so skipping the sink pass gives the same result; this is an implementation detail.
- code snippet (`minference/ops/streaming_kernel.py:620`): `if k_len > n_local:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/ops/streaming_kernel.py:620
- contrast run: branch not taken at minference/ops/streaming_kernel.py:620
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: minference.ops.streaming_kernel._forward agrees, torch.arange agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F038/execution_report.json`

## minference-F039

**When len_k <= n_local + n_init: The KV cache kept for subsequent decoding is either the full h_k/h_v or a concatenation of the first n_init keys and the last n_local keys, depending on caller-supplied n_local/n_init and the accumulated length. This changes what state later calls see. (minference/ops/streaming_kernel.py:701)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/streaming_kernel.py:701` in `minference/ops/streaming_kernel.py::stream_llm_forward.forward`
- condition: `len_k <= n_local + n_init`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Truncating the KV cache to sink plus local tokens belongs to the StreamingLLM baseline forward (stream_llm_forward), not to MInference.
- code snippet (`minference/ops/streaming_kernel.py:701`): `if len_k <= n_local + n_init:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/ops/streaming_kernel.py:701 (later RuntimeError at triton/runtime/driver.py:20)
- contrast run: branch not taken at minference/ops/streaming_kernel.py:701 (later RuntimeError at triton/runtime/driver.py:20)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: step-4 static analysis reports call_chain_status=not_found: the declared entry gather_last_q_vertical_slash_topk_v4 never calls the stream_llm_forward closure, so the target is c…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F039/execution_report.json`

## minference-F040

**When config.kv_cache_cpu: Caller-supplied config flag switches to the KV-cache-on-CPU variant (minference_patch_kv_cache_cpu) instead of the standard minference_forward path. (minference/patch.py:835)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/patch.py:835` in `minference/patch.py::minference_patch`
- condition: `config.kv_cache_cpu`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: kv_cache_cpu only changes where the KV cache is placed (memory/device plumbing), not the sparse mechanism.
- code snippet (`minference/patch.py:835`): `if config.kv_cache_cpu:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- contrast run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. positive and negative differ in [], not in exactly one factor
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/minference/minference-F040/execution_report.json`

## minference-F041

**When config.use_snapkv: Caller-supplied config flag switches to the SnapKV variant (minference_patch_with_snapkv) instead of the standard minference_forward path. (minference/patch.py:840)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/patch.py:840` in `minference/patch.py::minference_patch`
- condition: `config.use_snapkv`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: The user config flag use_snapkv switches patching to a different forward (minference_with_snapkv_forward) that combines sparse prefill with SnapKV compression, which is a config-driven variant.
- code snippet (`minference/patch.py:840`): `if config.use_snapkv:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/patch.py:840
- contrast run: branch not taken at minference/patch.py:840
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: step 4 reports call_chain_status 'not_found': call_chain[0] (gather_last_q_vertical_slash_topk_v4) is not a caller of the target, it is a caller-side integration that is patched …
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/minference/minference-F041/execution_report.json`

## minference-F042

**论文要求循环守卫 s_v≤k_s；代码用 while(1)+break，s 仅在 else 分支递增，终止由 s>=NNZ_S 决定**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `csrc/vertical_slash_index.cu:27-99`
- condition: `s_idx < end_m`
- paper/docs (paper, PDF p.25, text lines 23-25): “# Merge points (vertical indexes) and ranges (slash indexes) whilesv≤ks do”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown kernel uses while(1) and exits via break when s reaches NNZ_S; s is incremented in the else branch at line 82. The paper's stated guard is s_v≤k_s. This supports the claimed implementation deviation, though the snippet alone does not prove semantic inequivalence.
- cited code found at the pinned commit: yes (2 location(s))
- probe `while\s*\(\s*1\s*\)` in `csrc/vertical_slash_index.cu` expected present: **confirmed** (1 hit(s)). Loop is unconditional while(1), not the paper's guard.
- probe `s\s*<\s*NNZ_S` in `csrc/vertical_slash_index.cu` expected present: **confirmed** (1 hit(s)). Termination depends on slash-index count NNZ_S.
- probe `else\s*\{\s*if\s*\(\s*s\s*<\s*NNZ_S\s*\)\s*\{\s*s_idx\s*=\s*max\([^;]*slash_indexes\[s\+\+\]` in `csrc/vertical_slash_index.cu` expected present: **refuted** (0 hit(s)). s increments inside the else branch when slash index available.
- probe `break\s*;` in `csrc/vertical_slash_index.cu` expected present: **confirmed** (1 hit(s)). Loop exits via break rather than a loop condition.
- what would settle it: A source-level trace of s and v at loop exit would confirm whether termination is governed by s>=NNZ_S rather than s_v≤k_s.

## minference-F043

**实验配置未体现{(1024,4096)}，实际候选为(100,800)**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/README.md:13-30`
- paper/docs (paper, PDF p.18): “We set the target FLOPs t to be the same as 1k global tokens and 4k local window tokens in the A-shape pattern.”
- paper/docs (paper, PDF p.18): “A-shape {(1024, 4096)}”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper states A-shape candidates {(1024,4096)}, but the cited code excerpt only defines parameterized search functions and never shows the candidate pairs (100,800) or (1024,4096). The README search command also omits candidate values. Thus the shown evidence does not establish what candidates are actually used.
- cited code found at the pinned commit: yes (2 location(s))
- probe `1024|4096` in `minference/modules/minference_forward.py` expected absent: **refuted** (2 hit(s)). Paper A-shape values are not in the cited search code.
- probe `100\s*,\s*800|\(100\s*,\s*800\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (3 hit(s)). Shows whether the claimed (100,800) candidate pair is hardcoded.
- probe `vertical_size|slash_size` in `minference/modules/minference_forward.py` expected present: **confirmed** (54 hit(s)). Confirms search is parameterized, so candidate values may be supplied elsewhere.
- probe `1024|4096|100|800` in `experiments/README.md` expected absent: **refuted** (10 hit(s)). README search command does not specify the disputed candidate values.
- what would settle it: Search the full candidate list used by search_pattern and compare its (vertical_size, slash_size) pairs against the paper's {(1024,4096)}.

## minference-F044

**实验配置未体现论文候选集**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/README.md:13-30`
- paper/docs (paper, PDF p.18): “Vertical-Slash {(30, 2048), (100, 1800), (500, 1500), (3000, 200)}”
- paper/docs (paper, PDF p.18): “Vertical-Slash represents the Top-K number of vertical and diagonal lines”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes agree with the reading that the Finding is wrong

- reading: **contradicts**. The paper lists four Vertical-Slash candidate pairs. The README command omits them, but search_pattern takes vertical_size/slash_size and the loop after line 178 likely hardcodes the same four pairs. If the probe hits, the implementation uses the paper's candidate set; the README omission is documentation, not an impl deviation. Thus the finding is contradicted.
- cited code found at the pinned commit: yes (2 location(s))
- probe `30,\s*2048|100,\s*1800|500,\s*1500|3000,\s*200` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). Hit shows paper candidate pairs hardcoded in search; miss would support gap.
- probe `2048|1800|1500|3000` in `experiments/README.md` expected absent: **refuted** (1 hit(s)). Miss shows README command omits candidate set; control confirms file searched.
- what would settle it: Inspect the loop after line 178 to see whether it iterates over the four paper (vertical, slash) pairs; if yes, the finding is contradicted.

## minference-F045

**配置层未体现{100}**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/README.md:13-30`
- paper/docs (paper, PDF p.18): “Block-Sparse {100}”
- paper/docs (paper, PDF p.18): “Block-Sparse represents the Top-K number of blocks retained”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper specifies Block-Sparse {100}, but the documented search command uses --topk 1, and block_sparse consumes topk_ratio. No shown config or invocation sets 100 for Block-Sparse, so the config/experiment layer does not represent the paper's {100} setting.
- cited code found at the pinned commit: yes (2 location(s))
- probe `--topk\s+100\b` in `experiments/README.md` expected absent: **confirmed** (0 hit(s)). No 100 top-k setting in documented command; control confirms command present.
- probe `block_sparse\s*\(\s*100\b|topk_ratio\s*=\s*100\b|--topk\s+100\b` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No hard-coded 100 for block-sparse; control confirms function exists.
- what would settle it: Search the full config/experiment layer for any Block-Sparse top-k value of 100 and verify whether the search command's --topk is the same parameter.

## minference-F046

**论文Table4/Fig5报告static变体结果；评估入口未暴露static选项，且底层static实现本身只覆盖VS。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type == "minference"`
- paper/docs (paper, PDF p.8): “(1) Ours w/ static, which uses a static sparse mask in the Vertical-Slash and Block-Sparse patterns”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper quote and args.py choices support that the evaluation entry omits a static option, and models_patch.py has a static branch. However, the shown code does not establish that the underlying static implementation only covers Vertical-Slash; the paper says static uses both Vertical-Slash and Block-Sparse. Thus the finding is only partially evidenced.
- cited code found at the pinned commit: yes (4 location(s))
- probe `\bstatic\b` in `experiments/infinite_bench/args.py` expected absent: **confirmed** (0 hit(s)). No static choice in eval args; control confirms choices list found.
- probe `static_pattern` in `minference/models_patch.py` expected present: **confirmed** (1 hit(s)). Static branch exists in model patch; does not prove VS-only coverage.
- probe `\bstatic\b` in `experiments/ppl/run_ppl.sh` expected absent: **confirmed** (0 hit(s)). PPL script uses minference, not static; control confirms script content.
- what would settle it: Inspect the static mask construction code for both Vertical-Slash and Block-Sparse handling, and check whether any evaluation entry accepts --attn_type static.

## minference-F047

**评估入口无'only A-shape'变体选择，无法复现Table4的该变体。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type == 'minference'`
- paper/docs (paper, PDF p.8): “(2) Ours w/ only A-shape, which is equivalent to StreamingLLM”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The paper states that 'only A-shape' is equivalent to StreamingLLM, and args.py exposes 'streaming' as an attn_type. Thus the absence of a separately named only-A-shape option does not prevent reproducing that Table 4 variant; the equivalent selection exists. The run_ppl.sh example is not the only evaluation entry.
- cited code found at the pinned commit: yes (2 location(s))
- probe `"streaming"` in `experiments/infinite_bench/args.py` expected present: **confirmed** (1 hit(s)). Streaming attn_type is selectable, matching the paper's equivalent only-A-shape variant.
- probe `only[ _-]?a[ _-]?shape` in `experiments/infinite_bench/args.py` expected absent: **confirmed** (0 hit(s)). No explicitly named only-A-shape flag; control confirms the args file was searched.
- what would settle it: Run the streaming attn_type on the Table 4 setup and compare its scores to the paper's only-A-shape/StreamingLLM row.

## minference-F048

**无变体入口，无法复现Table4的only block-sparse行。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type == "minference"`
- paper/docs (paper, PDF p.8): “(3) Ours w/ only block-sparse, which uses only the Block-Sparse pattern in the dynamic sparse calculation”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper defines an 'only block-sparse' variant, but the shown attn_type choices expose minference and minference_with_dense, not a block-sparse-only option. The PPL script also selects minference. This supports the claim that no obvious variant entry exists for reproducing the Table 4 row, though a hidden config path is not ruled out.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)block[_-]?sparse|only[_-]?block` in `experiments/infinite_bench/args.py` expected absent: **confirmed** (0 hit(s)). No block-sparse-only attention option is defined in args.
- probe `(?i)block[_-]?sparse|only[_-]?block` in `experiments/ppl/run_ppl.sh` expected absent: **confirmed** (0 hit(s)). Script does not select a block-sparse-only variant.
- what would settle it: Search the full repository for any block-sparse-only attention/config path and attempt the Table 4 row with it; if none exists, the finding is confirmed.

## minference-F049

**论文 1k 全局/4k 局部；代码 128 全局/3968 局部，两参数均不符。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/models_patch.py:66-73`
- condition: `n_init == 128 and n_local == 3968`
- paper/docs (paper, PDF p.6, text lines 32-33): “compiler PIT [ZJZ+23]. We set the target FLOPst to 1k global tokens and 4k local windows in the A-shape pattern. We set last_q = 64 andblock_size = 64 in the Vertical-Slash and Block-Sparse”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states 1k global tokens and 4k local windows, while the pinned code sets n_init=128 and n_local=3968. Both values differ from the paper, so the finding is directly supported by the shown evidence.
- cited code found at the pinned commit: yes (2 location(s))
- probe `"n_local"\s*:\s*3968` in `minference/models_patch.py` expected present: **confirmed** (2 hit(s)). Confirms local window is 3968, not paper's 4k.
- probe `"n_init"\s*:\s*128` in `minference/models_patch.py` expected present: **confirmed** (3 hit(s)). Confirms global/init tokens are 128, not paper's 1k.
- what would settle it: Inspect the pinned configuration and paper text to verify the exact n_init and n_local values used.

## minference-F050

**论文要求遍历调用方给定的初始化搜索空间 σ；代码遍历写死的候选表，σ 输入不存在（artifact 范围：无 σ 输入，候选表硬编码）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5): “fori← 1 to|σ| do”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper describes a loop over a caller-provided initialization search space σ. The cited code defines search_pattern(q, k, head) with no σ parameter and at line 177 iterates a fixed three-entry candidate list. The README search invocation also supplies no σ. Thus the implementation does not realize the paper's σ-based loop.
- cited code found at the pinned commit: yes (2 location(s))
- probe `def search_pattern\(q, k, head\):` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Signature accepts only q, k, head; no sigma parameter.
- probe `for ty, fc in \[\("stream_llm", stream_llm\), \("vertical_and_slash", vertical_and_slash\), \("block_sparse", block_sparse\)\]:` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Loop iterates a hardcoded three-entry candidate table.
- probe `def search_pattern\([^)]*sigma` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No sigma parameter in search_pattern signature; control matches the signature.
- what would settle it: Inspect search_pattern's signature and loop to verify no σ argument is accepted and candidates are hardcoded.

## minference-F051

**论文要求 dense 注意力输出 y（含 V）；代码只算注意力权重矩阵，未形成输出**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 24-26): “y← Softmax(QK⊤/ √ d)”
- paper/docs (paper, PDF p.5): “fori← 1 to|ρ| do yi← SparseAttention(QK⊤/ √ d,ρ i)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The cited search_pattern helper does compute only attention weights, but the same file contains search_pattern_v2(q,k,v,head), which calls dense flash_attn_func and sparse attention kernels that return V-weighted outputs. Thus the code does form attention outputs; the finding overgeneralizes from the pattern-search helper.
- cited code found at the pinned commit: yes (3 location(s))
- probe `def search_pattern_v2\(q, k, v, head\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Shows a variant receives V and can form outputs
- probe `flash_attn_func\(` in `minference/modules/minference_forward.py` expected present: **confirmed** (7 hit(s)). Shows dense attention output path using V
- probe `vertical_slash_sparse_attention\(` in `minference/modules/minference_forward.py` expected present: **confirmed** (6 hit(s)). Shows sparse attention output path using V
- probe `block_sparse_attention\(` in `minference/modules/minference_forward.py` expected present: **confirmed** (3 hit(s)). Shows block-sparse attention output path using V
- what would settle it: Inspect or run search_pattern_v2 to verify its dense and sparse branches return V-weighted attention outputs, not just weight matrices.

## minference-F052

**论文要求最小化与 dense 输出的偏差；代码最大化权重保留分数，方向与参照对象均不同**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5): “pbest← argmin(yi−y,p best)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The cited v2 code sets best_score to infinity, computes delta as the count of elements where |dense - candidate| exceeds 5e-3, and updates when score < best_score. That minimizes deviation from dense output, matching the paper's argmin formulation, not maximizing a weight-retention score.
- cited code found at the pinned commit: yes (2 location(s))
- probe `if score > best_score` in `minference/modules/minference_forward.py` expected absent: **refuted** (1 hit(s)). No maximization branch; control shows minimization branch exists.
- probe `ref = dense\(q, k, v\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Reference object is dense output, not weight retention.
- probe `delta = \(\(ref - score\)\.abs\(\) > 5e-3\)\.sum\(\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Score measures deviation from dense output.
- probe `float\("inf"\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Best score initialized for minimization, not maximization.
- what would settle it: Inspect which search function is invoked and run both selection loops on a sample to see whether best_score is minimized against dense or maximized retention.

## minference-F053

**论文要求六类输入；代码签名缺 V、patterns、ρ、t、σ**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 10-12): “Input: Q, K, V ∈ RS×dh, patternsp, search spaceρ, target FLOPst, initial- ized search spaceσ”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code defines search_pattern(q, k, head), while the paper's Algorithm 1 input list includes Q, K, V, patterns, search space rho, target FLOPs t, and initialized search space sigma. The signature therefore cannot accept the paper's six required inputs, matching the claimed implementation deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `def search_pattern\(q, k, head\):` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Confirms the function signature takes only q, k, and head.
- probe `def search_pattern\([^)]*\b(V|patterns|rho|t|sigma)\b` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). Shows no V, patterns, rho, t, or sigma parameter in the signature.
- what would settle it: Inspect the function definition and all call sites to verify search_pattern is invoked with only q, k, and head and never with the paper's other inputs.

## minference-F054

**论文要求空集初始化；代码以数值 0 与空字符串初始化，且该初值使负分候选永不被选**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5): “pbest←ϕ”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states pbest is initialized to the empty set, while the cited code initializes best_score to numeric 0 and best_ty to an empty string. This is a direct initialization deviation. The claim that negative-scoring candidates are never selected is plausible if the loop compares scores against best_score with a strict greater-than test, but the shown snippet does not include that comparison.
- cited code found at the pinned commit: yes (2 location(s))
- probe `best_s,\s*best_v,\s*best_score,\s*best_ty\s*=\s*0,\s*0,\s*0` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Confirms numeric-zero initialization instead of empty-set initialization.
- probe `best_score` in `minference/modules/minference_forward.py` expected present: **confirmed** (9 hit(s)). Shows the score variable is used; inspect surrounding comparison logic.
- what would settle it: Inspect the loop body to verify whether candidate scores are compared with a strict greater-than against best_score initialized to 0.

## minference-F055

**论文要求最小化 t_sparse(M)+t_overhead(M)；artifact 执行路径未实现该时间目标。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:199-246`
- paper/docs (paper, PDF p.5): “min tsparse(M ) +toverhead(M ), (2)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited selector search_pattern_v2 evaluates candidate sparse patterns by counting output differences from a dense reference (`delta = ((ref - score).abs() > 5e-3).sum()`) and picks the smallest delta. It does not measure or minimize t_sparse(M)+t_overhead(M), so the paper's stated time objective is absent from this execution path.
- cited code found at the pinned commit: yes (3 location(s))
- probe `def search_pattern_v2` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Confirms the cited pattern-selection function exists in the artifact.
- probe `delta = \(\(ref - score\)\.abs\(\) > 5e-3\)\.sum\(\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Shows selection is based on output-difference count, not runtime.
- probe `perf_counter|time\.time|elapsed_time|latency|benchmark` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). Miss shows no timing measurement in the selector; control confirms file searched.
- what would settle it: Instrument search_pattern_v2 to record candidate runtimes and verify whether selection minimizes t_sparse(M)+t_overhead(M) rather than delta count.

## minference-F056

**论文要求块级 logits 先 softmax（并除 √d）得 Â；代码省略 softmax 与缩放，仅用因果掩码后的原始点积排序（artifact 范围：无 softmax/√d 的块级注意力矩阵）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:150-165`
- paper/docs (paper, PDF p.5): “bA← softmax  bQcK⊤/ √ d +mcasual ”
- paper/docs (paper, PDF p.6): “Since the mean pooling and matrix multiplication operations are commutative, the resulting attention weights are approximately equivalent to the actual attention weights after mean pooling.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper specifies block logits as softmax(QK^T/sqrt(d) + causal mask). The cited _build_block_index computes p_pool = einsum(pooled Q, pooled K), applies a causal -inf mask, then topk. It never applies softmax or 1/sqrt(d) scaling before ranking. The later kernel softmax only affects attention within already-selected blocks, not block selection. Thus the block-index ranking deviates from the paper.
- cited code found at the pinned commit: yes (2 location(s))
- probe `p_pool\s*=\s*torch\.einsum\([^\n]*query_pool[^\n]*key_pool` in `minference/ops/block_sparse_flash_attention.py` expected present: **confirmed** (1 hit(s)). Block scores are raw pooled dot products, not softmax-scaled logits.
- probe `p_pool\s*=\s*(?:torch\.)?softmax|p_pool\s*=\s*p_pool\s*/\s*(?:math|torch)\.sqrt` in `minference/ops/block_sparse_flash_attention.py` expected absent: **confirmed** (0 hit(s)). No softmax or sqrt scaling is applied to block scores.
- what would settle it: Run _build_block_index on a small tensor and compare its selected blocks with top-k of softmax(QK^T/sqrt(d)) under the causal mask; a mismatch confirms the deviation.

## minference-F002

**When ROPE_TYPE is not None: `ROPE_TYPE` is a module-level global computed once from the *first* attention module's `rotary_emb.forward` signature and then reused for every model/layer in the process (`if ROPE_TYPE is not None: return`). Loading a second model with a different RoPE signature in the same process keeps the first model's convention, and `get_cos_sin` then calls `self.rotary_emb` wi...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:30` in `minference/modules/minference_forward.py::set_rope_type`
- condition: `ROPE_TYPE is not None`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: ROPE_TYPE caching only matters when mixing models with different RoPE signatures in one process; it is model-compat plumbing, not a limitation of the sparse mechanism.
- code snippet (`minference/modules/minference_forward.py:30`): `def set_rope_type(self):`

**Not tested** (`outcome_unsupported`): effect type 'other': the target statement has no effect check yet

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Only the line `def set_rope_type(self):` is shown; the function body and any module-level `ROPE_TYPE` assignment are absent. The claim depends on a global being set once and an early return reusing it, neither of which is visible in the provided evidence. Text probes could confirm the code pattern, but the current evidence is insufficient.
- cited code found at the pinned commit: yes (1 location(s))
- probe `^ROPE_TYPE\s*=\s*None\b` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Module-level ROPE_TYPE global exists.
- probe `global\s+ROPE_TYPE` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Function mutates module-level ROPE_TYPE.
- probe `if\s+ROPE_TYPE\s+is\s+not\s+None[\s\S]{0,80}return` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). Early return reuses first computed RoPE type.
- probe `rotary_emb\.forward|inspect\.signature|signature\(` in `minference/modules/minference_forward.py` expected present: **confirmed** (2 hit(s)). RoPE type derived from rotary_emb signature.
- what would settle it: Inspect the full `set_rope_type` body and run two models with different `rotary_emb` signatures in one process to see whether the second reuses the first `ROPE_TYPE`.

## minference-F057

**When "seq_len" in inspect.signature(self.rotary_emb.forward).parameters: ROPE_TYPE is chosen by introspecting the installed transformers rotary embedding signature, so behavior depends on the transformers version. (minference/modules/minference_forward.py:34)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:34` in `minference/modules/minference_forward.py::set_rope_type`
- condition: `"seq_len" in inspect.signature(self.rotary_emb.forward).parameters`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Detecting the RoPE call signature only adapts to the model's rotary-embedding API and does not change the sparse mechanism.
- code snippet (`minference/modules/minference_forward.py:34`): `if 'seq_len' in inspect.signature(self.rotary_emb.forward).parameters:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line directly conditions on inspect.signature(self.rotary_emb.forward).parameters, which reflects the installed transformers rotary embedding API. That makes the branch version-dependent. The line does not itself show the ROPE_TYPE assignment, but it is the exact condition cited by the finding; a nearby assignment probe can confirm the branch effect.
- cited code found at the pinned commit: yes (1 location(s))
- probe `ROPE_TYPE\s*=` in `minference/modules/minference_forward.py` expected present: **confirmed** (10 hit(s)). Shows ROPE_TYPE is assigned in this file, supporting the branch effect.
- probe `inspect\.signature\(self\.rotary_emb\.forward\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (2 hit(s)). Confirms the code introspects the installed rotary embedding signature.
- what would settle it: Inspect the branch around line 34 to verify it assigns ROPE_TYPE based on whether 'seq_len' appears in the installed transformers rotary embedding signature.

## minference-F058

**When "apply_rotary_pos_emb" not in self.__dict__: `apply_rotary_pos_emb` is rebound as a module-level global from the *first* attention module's `rotary_emb.__class__.__module__` (`getattr(import_module(model_path), "apply_rotary_pos_emb")`), and the guard `if "apply_rotary_pos_emb" not in self.__dict__` is always true because the attribute is never set on `self` (only `self.apply_rotary_pos_em...**

- category `undisclosed`, effect `state`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:74` in `minference/modules/minference_forward.py::init_minference_parameters`
- condition: `"apply_rotary_pos_emb" not in self.__dict__`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: The check is not always true: the branch sets self.apply_rotary_pos_emb = True, so it runs once per module, and cross-model global overwrite is an internal multi-model detail.
- code snippet (`minference/modules/minference_forward.py:74`): `if 'apply_rotary_pos_emb' not in self.__dict__:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at minference/modules/minference_forward.py:74
- contrast run: branch not taken at minference/modules/minference_forward.py:74
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: the boundary variable is the prelude (program state): adjacency cannot be probed
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/minference/minference-F058/execution_report.json`

## minference-F059

**When best_ty == "block_sparse": If block_sparse wins, it is replaced by hard-coded vertical_and_slash with best_v=1000, best_s=6096, ignoring the searched parameters. (minference/modules/minference_forward.py:194)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:194` in `minference/modules/minference_forward.py::search_pattern`
- condition: `best_ty == "block_sparse"`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: The offline pattern search replaces a winning block_sparse (and stream_llm) result with vertical_and_slash 1000/6096, so searched configs can never contain those patterns.
- code snippet (`minference/modules/minference_forward.py:194`): `if best_ty == 'block_sparse':`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only shown code is the condition at line 194; it does not show the branch body, any assignment to vertical_and_slash, or hard-coded best_v/best_s values. No paper evidence is recorded. Static text searches could confirm whether the claimed replacement and constants exist in the same file.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if best_ty == "block_sparse":[\s\S]{0,300}vertical_and_slash` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). Hit shows block_sparse branch assigns vertical_and_slash.
- probe `best_v\s*=\s*1000` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). Hit shows hard-coded best_v=1000 exists.
- probe `best_s\s*=\s*6096` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). Hit shows hard-coded best_s=6096 exists.
- probe `best_ty\s*=\s*"vertical_and_slash"` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Hit shows best_ty is assigned vertical_and_slash.
- what would settle it: A text search of minference_forward.py for the block_sparse branch assigning vertical_and_slash and setting best_v=1000/best_s=6096 would settle it.

## minference-F060

**When head_id not in self.best_pattern: When the per-layer pattern file (`config_path`) is missing, unreadable, or has fewer entries than `self.layer_idx`, `init_minference_parameters` sets `self.best_pattern = {}` and every head silently falls back to the hard-coded tuple `("vertical_and_slash", 1000, 6096, 1)` — i.e. vertical=1000, slash=6096 regardless of the actual head. The `ty` element is ...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:430` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `head_id not in self.best_pattern`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: Heads missing from the pattern config (or a missing/empty config_path) silently get a fixed default vertical_and_slash (1000, 6096) pattern; the 'whole sequence' claim only holds for q_len <= 6096.
- code snippet (`minference/modules/minference_forward.py:430`): `ty, vertical_size, slash_size, _ = self.best_pattern.get(head_id, ('vertical_and_slash', 1000, 6096, 1))`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Line 430 directly confirms that a missing head_id falls back to ("vertical_and_slash", 1000, 6096, 1). However, the shown evidence does not establish that a missing/unreadable/short config_path causes init_minference_parameters to set self.best_pattern = {}. The fallback mechanism is supported, but the triggering condition is not shown.
- cited code found at the pinned commit: yes (1 location(s))
- probe `self\.best_pattern\s*=\s*\{\}` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Hit shows empty-dict assignment exists in this file.
- probe `def init_minference_parameters` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Hit locates the initialization function named in the finding.
- probe `config_path` in `minference/modules/minference_forward.py` expected present: **confirmed** (8 hit(s)). Hit shows config_path is referenced in this file.
- what would settle it: Inspect init_minference_parameters to verify whether missing, unreadable, or short config_path data assigns self.best_pattern = {} before the fallback lookup.

## minference-F005

**When ty not in {"stream_llm", "vertical_and_slash", "block_sparse"}: The implementation is chosen by the `ty` string read from the user-supplied pattern JSON (`config_path`). Any other value in that file (e.g. a typo, or a pattern produced by a different search version) raises an uncaught `KeyError` at prefill time rather than falling back. (minference/modules/minference_forward.py:441)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:441` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `ty not in {"stream_llm", "vertical_and_slash", "block_sparse"}`
- code snippet (`minference/modules/minference_forward.py:441`): `}[ty]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target statement has no effect check yet

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. Line 441 shows a direct dictionary subscript `[ty]`; in Python an unknown key raises KeyError, and no fallback is visible. The snippet does not show the key set or config_path origin, but the core failure mode is directly evidenced.
- cited code found at the pinned commit: yes (1 location(s))
- probe `\}\[ty\]` in `minference/modules/minference_forward.py` expected present: **confirmed** (2 hit(s)). Direct dict lookup by ty; unknown ty raises KeyError.
- probe `ty\s*=\s*[^\n]*config` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). ty is assigned from config in this file.
- probe `"stream_llm"` in `minference/modules/minference_forward.py` expected present: **confirmed** (7 hit(s)). Expected key appears in the lookup table.
- probe `"block_sparse"` in `minference/modules/minference_forward.py` expected present: **confirmed** (5 hit(s)). Another expected key appears in the lookup table.
- what would settle it: A unit test calling the prefill path with a pattern JSON whose ty is an unknown string would confirm whether an uncaught KeyError is raised.

## minference-F007

**When self.is_search and os.path.exists(self.config_path) and self.layer_idx < len(config_list): With `is_search` enabled, if the output `config_path` already contains an entry for this layer, the forward pass hits a bare `assert False` and aborts — the search cannot be re-run into an existing file. Also, when `is_search` is true the sparse mechanism is never applied (`not self.is_search` in the...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:504` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `self.is_search and os.path.exists(self.config_path) and self.layer_idx < len(config_list)`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: In search mode the code hits assert False when the config file already has an entry for the layer (true by default, since config_path comes from the shipped MODEL2PATH file), and search mode runs dense attention.
- code snippet (`minference/modules/minference_forward.py:504`): `if self.is_search:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Only line 504 is shown, confirming an `if self.is_search:` branch exists. It does not show the alleged bare `assert False`, the `os.path.exists(self.config_path)` and `layer_idx < len(config_list)` conditions, or the `not self.is_search` sparse gating. The full Finding therefore cannot be verified from the displayed evidence alone.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert False` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Hit shows bare assert exists; miss with control shows absent
- probe `os\.path\.exists\(self\.config_path\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (2 hit(s)). Hit shows config_path existence check in file
- probe `not self\.is_search` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Hit shows sparse path gated off during search
- probe `self\.layer_idx < len\(config_list\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Hit shows layer-bound condition in file
- what would settle it: Inspect the surrounding code and run search twice into an existing config file to see whether it aborts and whether sparse logic is skipped.

## minference-F061

**When is_flash_attn_2_available(): When the sparse path is not taken, availability of flash-attn 2 decides between flash_attn_func and gather_qkv. (minference/modules/minference_forward.py:523)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:523` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `is_flash_attn_2_available()`
- code snippet (`minference/modules/minference_forward.py:523`): `if is_flash_attn_2_available():`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited line confirms an is_flash_attn_2_available() check inside an elif, but it does not show that this branch selects flash_attn_func versus gather_qkv, nor that the sparse path is bypassed. Surrounding branch code is needed to verify the claimed control flow.
- cited code found at the pinned commit: yes (1 location(s))
- probe `flash_attn_func` in `minference/modules/minference_forward.py` expected present: **confirmed** (7 hit(s)). Shows flash_attn_func appears in the file, not its branch relation.
- probe `gather_qkv` in `minference/modules/minference_forward.py` expected present: **confirmed** (4 hit(s)). Shows gather_qkv appears in the file, not its branch relation.
- probe `elif\s+is_flash_attn_2_available\(\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Confirms the availability check exists as an elif at the cited location.
- what would settle it: Inspect the full if/elif/else block around line 523 to see whether the true branch calls flash_attn_func and the alternative path calls gather_qkv after sparse handling.

## minference-F062

**When not (is_flash_attn_2_available()): attn_output = gather_qkv(q, k, v, attention_mask) (minference/modules/minference_forward.py:526)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:526` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `not (is_flash_attn_2_available())`
- code snippet (`minference/modules/minference_forward.py:526`): `attn_output = gather_qkv(q, k, v, attention_mask)`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only code evidence shown is the gather_qkv call at line 526. The claimed enclosing condition `not is_flash_attn_2_available()` is not visible, and no paper evidence is recorded. A text search could confirm whether that branch actually contains this call, but the displayed evidence alone does not establish it.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if\s+not\s+is_flash_attn_2_available\(\):[\s\S]{0,2000}?gather_qkv\(q,\s*k,\s*v,\s*attention_mask\)` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). Shows the fallback branch directly contains the gather_qkv call.
- probe `attn_output\s*=\s*gather_qkv\(q,\s*k,\s*v,\s*attention_mask\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (2 hit(s)). Confirms the exact call at issue exists in the file.
- probe `is_flash_attn_2_available` in `minference/modules/minference_forward.py` expected present: **confirmed** (2 hit(s)). Confirms the availability check is referenced in this file.
- what would settle it: A text search showing the `if not is_flash_attn_2_available():` branch encloses the `gather_qkv` call at line 526 would confirm the finding.

## minference-F009

**When head_id not in self.best_pattern: The vLLM variant indexes `self.best_pattern[head_id]` directly (unlike the HF variant's `.get(..., default)`), so a pattern file whose per-layer dict lacks an entry for some head raises `KeyError` during prefill. `self.best_pattern` is rebuilt from the caller-supplied `pattern_config[layer_idx]` on every forward (line 790), so a short/mismatched pattern fi...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:754` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_vllm`
- condition: `head_id not in self.best_pattern`
- code snippet (`minference/modules/minference_forward.py:754`): `ty, vertical_size, slash_size, _ = self.best_pattern[head_id]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. Line 754 directly indexes self.best_pattern[head_id], so a missing head_id would raise KeyError rather than using a default. The finding's core claim is supported by the shown code; the line-790 rebuild detail is not shown but is consistent and can be checked by probe. No paper evidence is needed for this code-level behavior.
- cited code found at the pinned commit: yes (1 location(s))
- probe `self\.best_pattern\[head_id\]` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Direct indexing of best_pattern by head_id exists at the cited line.
- probe `best_pattern\s*=\s*pattern_config` in `minference/modules/minference_forward.py` expected present: **refuted** (0 hit(s)). best_pattern is assigned from caller-supplied pattern_config, supporting rebuild claim.
- probe `self\.best_pattern\.get\(` in `minference/modules/minference_forward.py` expected absent: **refuted** (1 hit(s)). No default .get lookup appears in this file; control confirms search location.
- what would settle it: Call the forward/prefill path with a pattern_config whose per-layer dict omits a head_id and observe whether KeyError is raised at line 754.

## minference-F036

**When q.dtype != torch.bfloat16: The Triton kernel's compute dtype is chosen from the input dtype: bfloat16 inputs use tl.bfloat16, but any other dtype (e.g. float32 or float16) is silently forced to tl.float16, so the kernel runs a different precision path than the caller's tensor dtype. (minference/ops/block_sparse_flash_attention.py:130)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:130` in `minference/ops/block_sparse_flash_attention.py::_triton_block_sparse_attention`
- condition: `q.dtype != torch.bfloat16`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Choosing the Triton compute dtype (non-bf16 cast to fp16 inside the kernel) is a kernel precision detail, not a limit of the sparse-attention mechanism.
- code snippet (`minference/ops/block_sparse_flash_attention.py:130`): `dtype = tl.bfloat16 if q.dtype == torch.bfloat16 else tl.float16`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line explicitly selects tl.bfloat16 only when q.dtype is torch.bfloat16; every other dtype falls through to tl.float16. That directly matches the claim that non-bfloat16 inputs are silently forced to a float16 Triton compute path.
- cited code found at the pinned commit: yes (1 location(s))
- probe `dtype\s*=\s*tl\.bfloat16\s+if\s+q\.dtype\s*==\s*torch\.bfloat16\s+else\s+tl\.float16` in `minference/ops/block_sparse_flash_attention.py` expected present: **confirmed** (1 hit(s)). Confirms non-bfloat16 inputs are forced to tl.float16.
- what would settle it: A static read of line 130 confirms the ternary; a GPU run with float32 or float16 inputs would show the tl.float16 path.

## minference-F063

**When top_k > context_size // block_size_N: The requested `top_k` (derived from the searched `slash_size`/`vertical_size` in `block_sparse_kernel`) is silently clamped to `context_size // block_size_N`, so for short sequences the block-sparse pattern is denser/different than the searched budget; also `_build_block_index` is called with `block_size_N` for both the M and N block sizes (line 183), ...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:164` in `minference/ops/block_sparse_flash_attention.py::_build_block_index`
- condition: `top_k > context_size // block_size_N`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: Clamping top_k to the number of key blocks that exist is a trivial bound, and block_size_M/N are equal by default, so the mix-up is an internal detail.
- code snippet (`minference/ops/block_sparse_flash_attention.py:164`): `top_k = min(top_k, context_size // block_size_N)`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. Line 164 exactly implements min(top_k, context_size // block_size_N), so the silent clamp is present. The call-site probe can confirm whether _build_block_index receives block_size_N for both block dimensions. This supports the finding's code-level claim; the 'denser/different' wording is interpretive, but the clamp itself is directly evidenced.
- cited code found at the pinned commit: yes (1 location(s))
- probe `top_k\s*=\s*min\(top_k,\s*context_size\s*//\s*block_size_N\)` in `minference/ops/block_sparse_flash_attention.py` expected present: **confirmed** (1 hit(s)). Confirms top_k is clamped to context_size // block_size_N.
- probe `_build_block_index\([^)]*block_size_N[^)]*block_size_N` in `minference/ops/block_sparse_flash_attention.py` expected present: **confirmed** (1 hit(s)). Shows _build_block_index receives block_size_N for both block dimensions.
- what would settle it: A static check of the clamp and _build_block_index arguments, plus a short-context trace of selected blocks, would settle it.

## minference-F064

**When q.dtype != torch.bfloat16: Any query dtype other than bfloat16 (float32, float64, float16 is fine) is silently treated as float16 in the Triton kernel, so a float32 model runs the sparse kernel in half precision without any check or cast of the inputs. (minference/ops/pit_sparse_flash_attention.py:150)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention.py:150` in `minference/ops/pit_sparse_flash_attention.py::triton_sparse_forward`
- condition: `q.dtype != torch.bfloat16`
- code snippet (`minference/ops/pit_sparse_flash_attention.py:150`): `dtype = tl.bfloat16 if q.dtype == torch.bfloat16 else tl.float16`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. Line 150 directly selects tl.float16 for every q.dtype except torch.bfloat16, so float32/float64/float16 queries all enter the Triton kernel as fp16. The shown evidence does not include any explicit non-bf16 check or input cast, and no paper evidence is recorded. This supports the finding, though the absence of checks elsewhere is only inferred from the cited line.
- cited code found at the pinned commit: yes (1 location(s))
- probe `dtype\s*=\s*tl\.bfloat16\s+if\s+q\.dtype\s*==\s*torch\.bfloat16\s+else\s+tl\.float16` in `minference/ops/pit_sparse_flash_attention.py` expected present: **confirmed** (2 hit(s)). Confirms the exact non-bf16-to-fp16 dtype fallback.
- probe `q\.dtype\s*==\s*torch\.(float32|float64|float16)` in `minference/ops/pit_sparse_flash_attention.py` expected absent: **confirmed** (0 hit(s)). No explicit branch for other query dtypes; control confirms dtype comparison exists.
- probe `q\s*=\s*q\.(to|half|float)\(` in `minference/ops/pit_sparse_flash_attention.py` expected absent: **confirmed** (0 hit(s)). No visible cast of q before kernel; control confirms searched location.
- the claim concerns behaviour that needs a GPU, an accelerator or a real run
- what would settle it: Run the sparse kernel with float32 q and compare its output/precision against explicit fp16 and fp32 reference kernels on GPU.

## minference-F065

**When head_dim not in [16, 32, 64, 128, 256, 512]: For head dims outside the power-of-two list (e.g. 96, 80, 160) the q/k/v are zero-padded up to the next power of two and the kernel runs on the padded tensors; the result is then sliced back with `out[..., :context_size, :head_dim]`. The padded dims contribute zeros to the dot product, so the softmax scale `head_dim ** -0.5` is still correct, bu...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention_v2.py:188` in `minference/ops/pit_sparse_flash_attention_v2.py::vertical_slash_sparse_attention`
- condition: `head_dim not in [16, 32, 64, 128, 256, 512]`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: Zero-padding the head dim adds nothing to q.k dot products and sm_scale uses the original head_dim, so the softmax is unchanged, contrary to the claim.
- code snippet (`minference/ops/pit_sparse_flash_attention_v2.py:188`): `if head_dim not in [16, 32, 64, 128, 256, 512]:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at minference/ops/pit_sparse_flash_attention_v2.py:188 (later NameError at minference/ops/pit_sparse_flash_attention_v2.py:189)
- contrast run: branch not taken at minference/ops/pit_sparse_flash_attention_v2.py:188 (later AssertionError at minference/ops/pit_sparse_flash_attention_v2.py:150)
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: torch.arange agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/minference/minference-F065/execution_report.json`

## minference-F018

**When not isinstance(model, (LlamaForCausalLM, MistralForCausalLM, Qwen2ForCausalLM)) and model.__class__.__name__ not in {"MiniCPMForCausalLM", "Phi3ForCausalLM", "ChatGLMForConditionalGeneration"}: `patch_hf` dispatches on the concrete model class and raises `ValueError("Only supports llama, mistral and qwen2 models.")` for anything else, so the mechanism cannot be applied to other architectur...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/patch.py:1252` in `minference/patch.py::patch_hf`
- condition: `not isinstance(model, (LlamaForCausalLM, MistralForCausalLM, Qwen2ForCausalLM)) and model.__class__.__name__ not in {"MiniCPMForCausalLM", "Phi3ForCausalLM", "ChatGLMForConditionalGeneration"}`
- code snippet (`minference/patch.py:1252`): `else:`

**Not tested** (`outcome_unsupported`): effect type 'other': the target statement has no effect check yet

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only shown code is an `else:` line; it does not display the dispatch condition, the class allowlist, or the ValueError. Without the surrounding lines, the claim is plausible but unverified. Text probes can check the exact error string and class checks in the same file.
- cited code found at the pinned commit: yes (1 location(s))
- probe `Only supports llama, mistral and qwen2 models\.` in `minference/patch.py` expected present: **confirmed** (1 hit(s)). Exact rejection message exists, supporting the claimed ValueError.
- probe `(?s)isinstance\(model.*LlamaForCausalLM.*MistralForCausalLM.*Qwen2ForCausalLM` in `minference/patch.py` expected present: **refuted** (0 hit(s)). Shows dispatch checks the three listed model classes.
- probe `MiniCPMForCausalLM|Phi3ForCausalLM|ChatGLMForConditionalGeneration` in `minference/patch.py` expected present: **confirmed** (3 hit(s)). Shows the extra class-name allowlist mentioned in the finding.
- what would settle it: A text search of minference/patch.py for the exact ValueError and class-dispatch condition would confirm whether patch_hf rejects non-listed architectures.

## minference-F066

**实验入口未暴露或设定步长50**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/README.md:13-30`
- condition: `is_search`
- paper/docs (paper, PDF p.18): “The step size of ChangeSpace is set to 50”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The documented experiment entry command does not pass any step-size or ChangeSpace parameter, and the shown argument parser excerpt defines no such option. This supports the claim that the entry does not expose or set the paper's step size of 50, though the excerpt alone cannot rule out a hardcoded value elsewhere.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)step(_?size)?|change.?space|\b50\b` in `experiments/README.md` expected absent: **confirmed** (0 hit(s)). No step-size/ChangeSpace/50 in documented entry; control confirms file searched.
- probe `(?i)step(_?size)?|change.?space|\b50\b` in `experiments/infinite_bench/args.py` expected absent: **confirmed** (0 hit(s)). No step-size argument in parser excerpt; control confirms relevant parser section.
- what would settle it: Search the full experiment entry and argument parser for any step-size/ChangeSpace setting and verify whether 50 is passed or hardcoded.

## minference-F067

**无变体配置，无法复现Table7的only vertical行。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- paper/docs (paper, PDF p.21): “1) Ours w/ only vertical, which only uses vertical lines and the top-1 slash line in Vertical-Slash pattern”
- paper/docs (paper, PDF p.21): “2) Ours w/ only slash, which only uses slash lines and the top-1 vertical line in Vertical-Slash pattern”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper defines Table 7 ablation variants 'only vertical' and 'only slash', but the cited code exposes no corresponding attn_type or script configuration. args.py lists only generic attention modes, and run_ppl.sh invokes plain minference. Thus the only-vertical row has no visible reproduction path in the shown code.
- cited code found at the pinned commit: yes (2 location(s))
- probe `only[_ -]?vertical|vertical_only|only_vertical` in `experiments/infinite_bench/args.py` expected absent: **confirmed** (0 hit(s)). No only-vertical attention option is defined in args.py.
- probe `only[_ -]?vertical|vertical_only|only_vertical` in `experiments/ppl/run_ppl.sh` expected absent: **confirmed** (0 hit(s)). The PPL script does not select an only-vertical variant.
- what would settle it: Search the full repository for an only-vertical configuration or code path and run it to compare against Table 7.

## minference-F068

**无换算配置入口。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type in ("minference", "minference_with_dense")`
- paper/docs (paper, PDF p.21): “The corresponding top-K quantities are set after converting based on FLOPs in kernel.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown argument parser exposes only attn_type and related choices, and the run script passes intervals but no FLOPs-to-top-K conversion option. This is consistent with the finding, though it proves absence only in these files.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)(top[_-]?k|flops|convert|conversion)` in `experiments/infinite_bench/args.py` expected absent: **refuted** (2 hit(s)). No top-K/FLOPs conversion option in args; control confirms file.
- probe `(?i)(top[_-]?k|flops|convert|conversion)` in `experiments/ppl/run_ppl.sh` expected absent: **confirmed** (0 hit(s)). Run script passes no conversion/top-K flag; control confirms file.
- what would settle it: Search the entire repository for a CLI/config option that converts FLOPs to top-K and is read by the kernel; finding none would confirm the claim.

## minference-F069

**论文要求每候选计算真实 kernel FLOPs；代码不计算任何 FLOPs**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- condition: `is_search`
- paper/docs (paper, PDF p.5): “ti← FLOPs_in_kernel(σi)”
- paper/docs (paper, PDF p.5, text lines 45-48): “have similar computational cost. Kernel-aware here in- dicates the computational cost reflects the real FLOPs in GPU kernels, instead of conceptual estimations, which is crucial to achieve the optimal acceleration.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown search_pattern code scores candidates by attention-weight sums and pattern masks, with no FLOPs_in_kernel call or FLOPs calculation. The paper explicitly requires real kernel FLOPs per candidate, so the evidence supports that this requirement is not implemented in the shown code.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)flops?` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No FLOPs calculation in pattern search; control confirms file location.
- what would settle it: Search the full pinned commit for any FLOPs computation in the candidate scoring path; absence confirms the finding.

## minference-F070

**论文要求以目标 FLOPs 为停止条件的迭代调整；代码无该循环与调整算子**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 16-19): “while|ti−t|>ϵ do σi← ChangeSpace(σi,p i) ti← FLOPs_in_kernel(σi) end while”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited search_pattern code implements pattern candidates and a for-loop over pattern types, but shows no while loop comparing FLOPs to a target and no ChangeSpace/FLOPs_in_kernel adjustment. The README only documents an offline search invocation, not the paper's iterative FLOPs-target loop. Thus the evidence supports that the described iterative adjustment is not implemented.
- cited code found at the pinned commit: yes (2 location(s))
- probe `FLOPs_in_kernel|ChangeSpace` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No FLOPs-target adjustment operator appears in the search code.
- probe `while\s+.*FLOPs|while\s*\|` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No iterative FLOPs-target while loop appears in the search code.
- what would settle it: Inspect search_pattern for a while loop that recomputes FLOPs and adjusts the sparse pattern until within epsilon of the target.

## minference-F071

**论文要求累积 FLOPs 对齐后的候选到 ρ；代码无该累积步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 20-20): “ρ←ρ∪σi”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The paper's update ρ←ρ∪σi requires accumulating candidates. The shown search_pattern builds per-strategy scores and all_info but contains no rho/union/append accumulation; probes target that absence. The snippet is partial, but the cited Step 4 note says the gap occurs on every call. Thus evidence supports not_implemented.
- cited code found at the pinned commit: yes (2 location(s))
- probe `\brho\b|ρ` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No rho variable or union target in search code.
- probe `all_info\.(append|extend)` in `minference/modules/minference_forward.py` expected absent: **refuted** (2 hit(s)). No candidate accumulation into all_info list.
- probe `\bFLOPs?\b|\bflops?\b` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No FLOPs-aligned accumulation logic in search function.
- probe `\bunion\b|\|=` in `minference/modules/minference_forward.py` expected absent: **confirmed** (0 hit(s)). No set-union or in-place accumulation operator.
- what would settle it: Run search_pattern and inspect whether any candidate set is unioned into rho after evaluating strategies, or grep the full function for rho/all_info append.

## minference-F072

**论文要求 FlashAttention 与 V 信息参与选择；代码为稠密权重计算且完全不含 V**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 53-56): “approach leverages FlashAttention [ Dao24] to reduce GPU memory overhead and incorporates the informa- tion from the V matrix, enabling end-to-end selection of the best pattern, which further enhances performance.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The cited code does contain an older search_pattern(q,k,head) that lacks V and uses dense qk weights. However, search_pattern_v2(q,k,v,head) accepts V, calls flash_attn_func for a dense reference, and scores candidates by comparing outputs, so V and FlashAttention participate in selection. Thus the broad claim that the code is dense-only and completely lacks V is contradicted.
- cited code found at the pinned commit: yes (2 location(s))
- probe `def search_pattern_v2\(q, k, v, head\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). V2 selection function accepts V, contradicting no-V claim.
- probe `flash_attn_func\(` in `minference/modules/minference_forward.py` expected present: **confirmed** (7 hit(s)). FlashAttention is invoked, contradicting absence claim.
- probe `def search_pattern\(q, k, head\)` in `minference/modules/minference_forward.py` expected present: **confirmed** (1 hit(s)). Older search function indeed lacks V, but not whole code.
- probe `vertical_slash_sparse_attention\(q, k, v` in `minference/modules/minference_forward.py` expected present: **confirmed** (6 hit(s)). Sparse candidate uses V in attention computation.
- what would settle it: Trace which search function is called at runtime and verify whether search_pattern_v2 with V and FlashAttention is used for pattern selection.

## minference-F073

**论文要求分别定义 t_sparse 与 t_overhead；artifact 路径无对应实现。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:199-246`
- paper/docs (paper, PDF p.5): “where tsparse and toverhead represent the time spent on dynamic sparse attention computation and estimation of the approximate dynamic sparse pattern, respectively.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited forward path computes sparse patterns and calls sparse attention, but the shown code contains no t_sparse/t_overhead timing variables or timing instrumentation. The paper defines these as separate time components; the artifact path shown does not expose or measure them. This supports the claimed implementation gap, though only for the cited files.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)t_?sparse|t_?overhead` in `minference/modules/minference_forward.py` expected absent: **refuted** (1 hit(s)). No separate sparse/overhead timing variables in forward path.
- probe `(?i)t_?sparse|t_?overhead` in `minference/ops/pit_sparse_flash_attention_v2.py` expected absent: **confirmed** (0 hit(s)). No timing components in sparse attention op.
- what would settle it: A repository-wide search plus runtime profiling of the forward path would confirm whether separate t_sparse and t_overhead timings are ever measured or exposed.

