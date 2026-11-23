# Limitations report: InfiniGen: Efficient Generative Inference of Large Language Models with Dynamic KV Cache Management

- artifact: `infinigen` (OSDI 2024), repository https://github.com/snu-comparch/InfiniGen at `3754f52d13`
- input: `results/step4/infinigen/limitations_for_tests.json` (sha256 `583779a93137`), 31 Findings
- generated: 2026-11-23T11:22:09+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
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
| Findings | 31 |
| tested | 19 |
| not tested | 12 |
| verdicts | inconclusive 4, yes 15 |
| levels | L1 10, L2 5, n/a 4 |
| analysis only (not tests) | A0 2, A1 1, A2 9 |
| not tested, by reason | `no_code_location` 11, `witness_unusable` 1 |

Code side's predicted ceiling vs measured level (both uncalibrated; 15 tested Findings have both): equal 14, measured below ceiling 1, measured above ceiling 0.

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [infinigen-F001](#infinigen-f001) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:426` | **inconclusive** / n/a (uncalibrated) |
| [infinigen-F002](#infinigen-f002) | undisclosed | state | `speedup/flexgen/infinigen/flex_opt.py:442` | **yes** / L2 (uncalibrated) |
| [infinigen-F003](#infinigen-f003) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:466` | **yes** / L1 (uncalibrated) |
| [infinigen-F004](#infinigen-f004) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:710` | **yes** / L1 (uncalibrated) |
| [infinigen-F005](#infinigen-f005) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:1359` | **yes** / L2 (uncalibrated) |
| [infinigen-F006](#infinigen-f006) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:464` | **yes** / L1 (uncalibrated) |
| [infinigen-F007](#infinigen-f007) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:823` | **yes** / L1 (uncalibrated) |
| [infinigen-F008](#infinigen-f008) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:881` | **yes** / L1 (uncalibrated) |
| [infinigen-F009](#infinigen-f009) | stated_differently | path_change | `speedup/flexgen/infinigen/flex_opt.py:287` | **yes** / L2 (uncalibrated) |
| [infinigen-F010](#infinigen-f010) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:389` | **yes** / L1 (uncalibrated) |
| [infinigen-F011](#infinigen-f011) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:528` | **yes** / L1 (uncalibrated) |
| [infinigen-F012](#infinigen-f012) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:541` | **yes** / L2 (uncalibrated) |
| [infinigen-F013](#infinigen-f013) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:799` | **yes** / L1 (uncalibrated) |
| [infinigen-F014](#infinigen-f014) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:401` | **inconclusive** / n/a (uncalibrated) |
| [infinigen-F015](#infinigen-f015) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:422` | **yes** / L1 (uncalibrated) |
| [infinigen-F016](#infinigen-f016) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:479` | **inconclusive** / n/a (uncalibrated) |
| [infinigen-F017](#infinigen-f017) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:767` | **yes** / L1 (uncalibrated) |
| [infinigen-F018](#infinigen-f018) | impl_deviates | other | `accuracy/perplexity/table2.sh:27-45` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F019](#infinigen-f019) | impl_deviates | other | `accuracy/perplexity/table2.sh:27-45` | not tested: `no_code_location`, analysis A1/unclear |
| [infinigen-F020](#infinigen-f020) | impl_deviates | other | `speedup/flexgen/infinigen/flex_opt.py:282` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F021](#infinigen-f021) | impl_deviates | other | `speedup/flexgen/infinigen/flex_opt.py:513-524` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F022](#infinigen-f022) | impl_deviates | other | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F023](#infinigen-f023) | impl_deviates | other | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | not tested: `no_code_location`, analysis A0/supports |
| [infinigen-F024](#infinigen-f024) | impl_deviates | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F025](#infinigen-f025) | impl_deviates | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F026](#infinigen-f026) | impl_deviates | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location`, analysis A0/supports |
| [infinigen-F027](#infinigen-f027) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:690` | **yes** / L2 (uncalibrated) |
| [infinigen-F028](#infinigen-f028) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:326` | **inconclusive** / n/a (uncalibrated) |
| [infinigen-F029](#infinigen-f029) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:837` | not tested: `witness_unusable`, analysis A2/supports |
| [infinigen-F030](#infinigen-f030) | not_implemented | other | `accuracy/perplexity/table2.sh:27-45` | not tested: `no_code_location`, analysis A2/supports |
| [infinigen-F031](#infinigen-f031) | not_implemented | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location`, analysis A2/supports |

## infinigen-F001

**When self.policy.attn_sparsity >= 1.0: Path 2 (split GPU/CPU attention) asserts that sparsity >= 1.0, so sparse attention with mixed cache placement is rejected. (speedup/flexgen/infinigen/flex_opt.py:426)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:426` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.load_cache`
- condition: `self.policy.attn_sparsity >= 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: The assert only rejects FlexGen's top-k sparse attention baseline (attn_sparsity<1) in the mixed-cache CPU path, not InfiniGen's mechanism.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:426`): `assert self.policy.attn_sparsity >= 1.0`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect only on the negative input: boundary direction reversed

Code side predicted ceiling before the test: L1 (measured: n/a).

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: no exception at speedup/flexgen/infinigen/flex_opt.py:426
- contrast run: AssertionError at speedup/flexgen/infinigen/flex_opt.py:426
- open doubts:
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'attn_sparsity' is not an integer (value 0.999)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Region.call_chain status is not_found: TorchDevice.mha computes attention and never calls SelfAttention.load_cache. The driver therefore calls the deepest chain function directly…
- what would raise the level: D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F001/execution_report.json`

## infinigen-F002

**When k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None: Prefetch path 2 requires MIXED device with populated GPU portion; otherwise path 1. (speedup/flexgen/infinigen/flex_opt.py:442)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:442` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.prefetch_cache`
- condition: `k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None`
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:442`): `if k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:442 (later ValueError at speedup/flexgen/infinigen/flex_opt.py:467)
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:442 (later ValueError at speedup/flexgen/infinigen/flex_opt.py:467)
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Static analysis found no call chain from TorchDevice.mha to SelfAttention.prefetch_cache; TorchDevice.mha never calls prefetch_cache. The finding's own witness says call_chain_st…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F002/execution_report.json`

## infinigen-F003

**When path == 1 or path == 2: Prefetching is not implemented for CPU-compute paths 1 and 2; raises ValueError. (speedup/flexgen/infinigen/flex_opt.py:466)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:466` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.prefetch_cache`
- condition: `path == 1 or path == 2`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: prefetch_cache is called in the generation loop regardless of --cpu-cache-compute, and raises ValueError for CPU-compute paths 1/2, so InfiniGen prefetching cannot be combined with CPU attention compute.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:466`): `if path == 1 or path == 2:`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at speedup/flexgen/infinigen/flex_opt.py:467
- contrast run: no exception at speedup/flexgen/infinigen/flex_opt.py:466
- open doubts:
  - D4 oracle is specified, located, pre-registered: *residual*. oracle changed 2 time(s) after the first run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. no effect on either side: the negative input is NOT adjacent to the effect region
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The declared entry TorchDevice.mha never calls SelfAttention.prefetch_cache (step 4 reports call_chain_status not_found). The witness also calls path an input, but the repository…
- what would raise the level: D4 (residual): state the oracle as exception type + Region.location and register it before the first run; D5 (refuted): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F003/execution_report.json`

## infinigen-F004

**When not (self.policy.act_gpu_percent == 100 or self.policy.act_cpu_percent == 100 or self.policy.act_disk_percent == 100): Any policy whose activation percentages are not a single 100% tier is rejected at construction time. (speedup/flexgen/infinigen/flex_opt.py:710)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:710` in `speedup/flexgen/infinigen/flex_opt.py::OptLM.__init__`
- condition: `not (self.policy.act_gpu_percent == 100 or self.policy.act_cpu_percent == 100 or self.policy.act_disk_percent == 100)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Requiring activations to live entirely on one tier is an inherited FlexGen offloading-policy restriction unrelated to InfiniGen's KV management.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:710`): `raise NotImplementedError()`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: NotImplementedError at speedup/flexgen/infinigen/flex_opt.py:710
- contrast run: no exception at speedup/flexgen/infinigen/flex_opt.py:710
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 call chain starts at TorchDevice.mha, a runtime attention method, and static analysis found no call chain to the constructor (chain status not_found). OptLM.__init__ i…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F004/execution_report.json`

## infinigen-F005

**When args.compress_cache and args.attn_sparsity < 1.0: Combining cache compression with attention sparsity (the InfiniGen KV selection path) is not implemented; the run aborts. (speedup/flexgen/infinigen/flex_opt.py:1359)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:1359` in `speedup/flexgen/infinigen/flex_opt.py::run_flexgen`
- condition: `args.compress_cache and args.attn_sparsity < 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: This is FlexGen's own check against combining cache compression with its top-k sparse attention (attn_sparsity<1); it is not the InfiniGen KV selection path as claimed.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:1359`): `assert not (args.compress_cache and args.attn_sparsity < 1.0)`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: AssertionError at speedup/flexgen/infinigen/flex_opt.py:1359
- contrast run: no exception at speedup/flexgen/infinigen/flex_opt.py:1359 (later RuntimeError at torch/cuda/_utils.py:46)
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: transformers.AutoTokenizer.from_pretrained agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The official mha entry is downstream of run_flexgen and never calls it; the guarded branch is only reachable by calling run_flexgen directly.
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F005/execution_report.json`

## infinigen-F006

**When not (attn_sparsity >= 1.0): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:464)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:464` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `not (attn_sparsity >= 1.0)`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:464`): `assert attn_sparsity >= 1.0`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at speedup/flexgen/infinigen/pytorch_backend.py:464
- contrast run: no exception at speedup/flexgen/infinigen/pytorch_backend.py:464 (later IndexError at speedup/flexgen/infinigen/pytorch_backend.py:550)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/infinigen/infinigen-F006/execution_report.json`

## infinigen-F007

**When not (src.device.device_type != DeviceType.MIXED): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:823)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:823` in `speedup/flexgen/infinigen/pytorch_backend.py::general_copy`
- condition: `not (src.device.device_type != DeviceType.MIXED)`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:823`): `assert src.device.device_type != DeviceType.MIXED`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at speedup/flexgen/infinigen/pytorch_backend.py:823
- contrast run: no exception at speedup/flexgen/infinigen/pytorch_backend.py:823 (later RuntimeError at speedup/flexgen/infinigen/pytorch_backend.py:829)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/infinigen/infinigen-F007/execution_report.json`

## infinigen-F008

**When not (all((x.step is None for x in indices))): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:881)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:881` in `speedup/flexgen/infinigen/pytorch_backend.py::cut_indices`
- condition: `not (all((x.step is None for x in indices)))`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:881`): `assert all((x.step is None for x in indices))`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at speedup/flexgen/infinigen/pytorch_backend.py:881
- contrast run: no exception at speedup/flexgen/infinigen/pytorch_backend.py:881
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The official mha_gen -> _sparse_attention_value path cannot make the guard true: indices_src is the int64 top-k tensor and indices_tgt is built from step-less slices, so cut_indi…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F008/execution_report.json`

## infinigen-F009

**When self.layer_id > 1: partial_weight_ratio is only set for layers with layer_id > 1; layer 0 and 1 get None, so the partial-weight speculation path is disabled for the first two layers. (speedup/flexgen/infinigen/flex_opt.py:287)**

- category `stated_differently`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:287` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.__init__`
- condition: `self.layer_id > 1`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: Layers 0 and 1 always get partial_weight_ratio=None (and are excluded from prefetched cache loading), so InfiniGen speculation/selection never applies to the first two layers, which always use the full KV cache.
- paper/docs (paper, 4.3 Efficiently Prefetching KV Cache, p.10): “InfiniGen initiates speculation and prefetching from Layer 1 because the outliers, which are essential for exploiting input similarity, emerge during the computation in Layer 0.”
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:287`): `if self.layer_id > 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:287
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:287
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: step 4 reports call_chain_status=not_found for TorchDevice.mha -> SelfAttention.__init__; TorchDevice.mha never constructs a SelfAttention (it is constructed by OptLM/Transformer…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F009/execution_report.json`

## infinigen-F010

**When self.policy.attn_sparsity >= 1.0: When sparsity >= 1.0 the full V cache is copied; otherwise V is deferred (v_home, False) for later selection, changing the data movement path. (speedup/flexgen/infinigen/flex_opt.py:389)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:389` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.load_cache`
- condition: `self.policy.attn_sparsity >= 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: attn_sparsity<1 picks FlexGen's top-k sparse attention baseline rather than InfiniGen's KV selection; same branch logic as infinigen-f04.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:389`): `if self.policy.attn_sparsity >= 1.0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:389
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:389
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The registered call_chain[0] TorchDevice.mha never calls SelfAttention.load_cache anywhere in the pinned repository; step-4 static analysis reports chain status not_found. The de…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F010/execution_report.json`

## infinigen-F011

**When self.enable_prefetching: When prefetching is enabled, mha_gen is called with p_w_q, partial_k_cache, speculation_stream, alpha and max_num_kv; otherwise those are passed as None, disabling the speculation/prefetch mechanism. (speedup/flexgen/infinigen/flex_opt.py:528)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:528` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.forward`
- condition: `self.enable_prefetching`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: enable_prefetching is fixed per layer in OptLM.__init__ (off only for the first and last layers), so it is an internal design detail rather than a user-reachable switch.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:528`): `if self.enable_prefetching:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:528 (later RuntimeError at torch/nn/functional.py:2515)
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:528 (later RuntimeError at torch/nn/functional.py:2515)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The declared call_chain[0] TorchDevice.mha is the prefill compute helper that SelfAttention.forward itself calls through self.compute.mha; the call dependency is the reverse of t…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F011/execution_report.json`

## infinigen-F012

**When prev_partial_cache_read_buf is not None and self.layer_id > 1: Partial cache accumulation for the next layer only happens for layer_id > 1; earlier layers skip it. (speedup/flexgen/infinigen/flex_opt.py:541)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:541` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.forward`
- condition: `prev_partial_cache_read_buf is not None and self.layer_id > 1`
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:541`): `if prev_partial_cache_read_buf is not None and self.layer_id > 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:541
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:541
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: flexgen.pytorch_backend.TorchDevice.mha_gen error
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The region's call_chain lists TorchDevice.mha as the first frame, but mha is called by SelfAttention.forward and the target line lives in forward itself. forward is the outermost…
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F012/execution_report.json`

## infinigen-F013

**When j not in self.attn_layer[2:]: Cache loading is skipped for all attention layers except the first two (attn_layer[0], attn_layer[1]); those layers' KV caches are not loaded from cache_home, so the InfiniGen cache-load path only runs for the first two attention layers. (speedup/flexgen/infinigen/flex_opt.py:799)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:799` in `speedup/flexgen/infinigen/flex_opt.py::OptLM.load_cache`
- condition: `j not in self.attn_layer[2:]`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Skipping load_cache for attention layers after the first two is a fixed internal schedule (those layers get KV via prefetch), not a condition a user can trigger.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:799`): `if j not in self.attn_layer[2:]:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:799
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:799
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Step 4 reports call_chain_status=not_found: no static call path exists from the declared entry TorchDevice.mha to OptLM.load_cache (it is reached through the dynamic generation l…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F013/execution_report.json`

## infinigen-F014

**When p_w_q is None: In TorchDevice.mha_gen, the InfiniGen KV speculation (speculate_attention) only runs when the caller passes a partial-weight query tensor p_w_q. When p_w_q is None, prefetch_idx stays None (line 400) and the whole dynamic KV selection / prefetch mechanism is skipped, so the run degrades to plain dense attention over the full KV cache. (speedup/flexgen/infinigen/pytorch_backe...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:401` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `p_w_q is None`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: p_w_q is None only for layers built with enable_prefetching=False, so this is the same 'early layers get no speculation/full KV' limitation already covered by infinigen-10.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:401`): `if p_w_q is not None:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: KeyError at workspace/attempt/driver.py:48 before the target was reached

Code side predicted ceiling before the test: L1 (measured: n/a).

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: KeyError at workspace/attempt/driver.py:48 before the target was reached
- contrast run: KeyError at workspace/attempt/driver.py:48 before the target was reached
- open doubts:
  - D1 target statement executed: *refuted*. positive run never executed the target line
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *open*. mutation not run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. positive and negative differ in [], not in exactly one factor
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. entry index None (None = not in the call chain) and no reason recorded
- what would raise the level: D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix); D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/infinigen/infinigen-F014/execution_report.json`

## infinigen-F015

**When attn_sparsity >= 1.0: Caller-supplied attn_sparsity selects dense attention (decompress full k/v cache and dense bmm) versus sparse attention (top-k selection in _sparse_attention_value). (speedup/flexgen/infinigen/pytorch_backend.py:422)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:422` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `attn_sparsity >= 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: The dense vs attn_sparsity<1 switch selects FlexGen's own top-k sparse attention baseline, not a variant of InfiniGen.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:422`): `if attn_sparsity >= 1.0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at speedup/flexgen/infinigen/pytorch_backend.py:422 (later AssertionError at torch/cuda/__init__.py:239)
- contrast run: branch not taken at speedup/flexgen/infinigen/pytorch_backend.py:422 (later TypeError at speedup/flexgen/infinigen/pytorch_backend.py:528)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/infinigen/infinigen-F015/execution_report.json`

## infinigen-F016

**When comp_config.group_dim == 0: Caller-supplied comp_config.group_dim decides whether k_new/v_new are re-sliced to a group-aligned boundary before compression. (speedup/flexgen/infinigen/pytorch_backend.py:479)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:479` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `comp_config.group_dim == 0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: group_dim rounding is an internal detail of FlexGen cache compression whose config is hardcoded in run_flexgen (group_dim=2), not a user-facing variant of InfiniGen.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:479`): `if comp_config.group_dim == 0:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  positive run: NotImplementedError at workspace/attempt/driver.py:11 before the target was reached

Code side predicted ceiling before the test: L1 (measured: n/a).

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
- evidence: `tests/infinigen/infinigen-F016/execution_report.json`

## infinigen-F017

**When policy.cache_disk_percent == 0: When the configured disk cache percent is zero, the KV cache is split only between GPU and CPU (len_disk=0, len_cpu=shape-len_gpu), so no disk segment is allocated; otherwise the split uses cache_gpu_percent/cache_cpu_percent and the remainder goes to disk. The caller's policy config selects which cache layout the mechanism uses. (speedup/flexgen/infinigen/p...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:767` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchMixedDevice.init_cache_one_gpu_batch`
- condition: `policy.cache_disk_percent == 0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: GPU/CPU/disk KV-cache segment sizing is FlexGen offloading plumbing, not a change to the mechanism.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:767`): `if policy.cache_disk_percent == 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at speedup/flexgen/infinigen/pytorch_backend.py:767
- contrast run: branch not taken at speedup/flexgen/infinigen/pytorch_backend.py:767
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Step 4 reported call_chain_status=not_found: TorchDevice.mha has no static path to TorchMixedDevice.init_cache_one_gpu_batch (the real caller is flex_opt.py's dynamic device.init…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F017/execution_report.json`

## infinigen-F018

**论文要求覆盖受害者槽位；代码保留全部 K/V 只做注意力屏蔽（artifact 范围：无覆盖写步骤）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `accuracy/perplexity/table2.sh:27-45`
- condition: `past_key_value is not None`
- paper/docs (paper, PDF p.10): “the manager overwrites the selected victim with the newly generated key and value”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states the manager overwrites the selected victim slot. The shown attention code concatenates past_key_value with new key/value states, retaining all K/V, and table2.sh only passes an eviction policy. No overwrite step appears in the evidence. This supports the claimed implementation deviation, though the snippet does not fully show the masking mechanism.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)victim|overwrit` in `accuracy/src/modeling_opt_ours.py` expected absent: **confirmed** (0 hit(s)). No victim-slot overwrite logic appears in this attention file.
- probe `torch\.cat\(\[past_key_value\[0\], key_states\]` in `accuracy/src/modeling_opt_ours.py` expected present: **confirmed** (1 hit(s)). Old and new keys are concatenated, retaining all K/V entries.
- probe `--eviction_policy` in `accuracy/perplexity/table2.sh` expected present: **confirmed** (2 hit(s)). The script only selects an eviction policy; it does not implement overwrite.
- what would settle it: Inspect or run the cache-update path to verify whether a selected victim slot is overwritten or all K/V are concatenated and masked.

## infinigen-F019

**论文要求淘汰后更新 GPU 部分 key cache；代码无该步骤（artifact 范围：缺更新步骤）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `accuracy/perplexity/table2.sh:27-45`
- condition: `past_key_value is not None`
- paper/docs (paper, PDF p.10, text lines 31-34): “KV entry for eviction. Subsequently, the manager overwrites the selected victim with the newly generated key and value, along with updating the corresponding partial key cache re- siding in the GPU. It is noted that the order of KV entries can”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown table2.sh only passes an eviction policy; the modeling snippet is ordinary KV concatenation/assignment, not the eviction manager. Absence of an overwrite/update step in these excerpts does not establish that the artifact lacks it elsewhere. The claim needs inspection of the actual eviction code path.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)evict|victim|overwrite|partial.*cache|key_cache` in `accuracy/src/modeling_opt_ours.py` expected absent: **refuted** (8 hit(s)). No eviction/update logic in this attention file; a hit would contradict the finding.
- probe `(?i)overwrite|victim|partial.*cache|update` in `accuracy/perplexity/table2.sh` expected absent: **confirmed** (0 hit(s)). Script only selects eviction policy; no explicit victim overwrite/update step.
- what would settle it: Inspect the eviction implementation in opt.py/modeling code to see whether the selected victim's key/value and GPU partial key cache are overwritten.

## infinigen-F020

**控制平面组件集合不完整（缺Pool Manager）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:282`
- paper/docs (paper, PDF p.7, text lines 112-115): “weights. We explain each operation in Section 4.3. The sec- ond component is the Pool Manager. It manages the KV cache pool on CPU memory under CPU memory pressure, which we discuss in Section 4.4.”
- paper/docs (paper, PDF p.7): “GPU Memory CPU Memory”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper names a Pool Manager as the second control-plane component managing the CPU KV cache under memory pressure. The shown code only has prefetch_cache/prefetch_idx and per-GPU K/V cache allocation with pin_memory disabled; no Pool Manager class/module or CPU-pressure management appears. This supports the claim that the control-plane component set is incomplete.
- cited code found at the pinned commit: yes (3 location(s))
- probe `PoolManager|Pool Manager|pool_manager|class\s+Pool` in `speedup/flexgen/infinigen/flex_opt.py` expected absent: **confirmed** (0 hit(s)). No Pool Manager in flex_opt.py; control confirms file searched.
- probe `PoolManager|Pool Manager|pool_manager|class\s+Pool` in `speedup/flexgen/infinigen/pytorch_backend.py` expected absent: **confirmed** (0 hit(s)). No Pool Manager in backend; control confirms file searched.
- what would settle it: Search the full repository for any Pool Manager implementation and trace whether CPU KV-cache pressure handling exists; absence would confirm the finding.

## infinigen-F021

**论文要求A=V；代码A为V列按σq·σk排序重排，A≠V（artifact 范围：A为排序重排后的V，非论文所述A=V）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:513-524`
- condition: `warmup`
- paper/docs (paper, PDF p.9): “We then set A to orthogonal matrix V”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The code computes SVDs of query and key, multiplies singular values, sorts that product, and scatters vq columns into A. Thus A is a column permutation of V, not V itself. The paper quote says A is set to V, so the evidence supports the claimed implementation deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `_, sq, vq = torch\.svd\(query` in `speedup/infinigen/infinigen/skewing_controller.py` expected present: **confirmed** (1 hit(s)). Shows V (vq) comes from query SVD.
- probe `A = A\.scatter\(-1, ind` in `speedup/infinigen/infinigen/skewing_controller.py` expected present: **confirmed** (1 hit(s)). Shows A is built by scattering V columns by sorted indices.
- probe `sq = sq \* sk` in `speedup/infinigen/infinigen/skewing_controller.py` expected present: **confirmed** (1 hit(s)). Shows sorting key is product of query/key singular values.
- what would settle it: Run skew() on a simple non-diagonal V and check whether A equals V or a column-permuted V.

## infinigen-F022

**预取集合由 top-k(均值) 决定，而非严格 >max−alpha 的令牌集合**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/kv_selection_controller.py:28-63`
- condition: `self.policy.attn_sparsity >= 1.0`
- paper/docs (paper, PDF p.9): “We select only the tokens with an attention score greater than the maximum score subtracted by alpha”
- paper/docs (paper, PDF p.10): “InfiniGen only prefetches the keys and values of the tokens with an attention score larger than the highest attention score minus alpha”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says InfiniGen prefetches exactly the tokens with score > max−alpha. The code instead counts those tokens, averages the counts, and returns torch.topk with k=min(int(mean), max_num_kv). Thus the prefetch set is top-k by score, not the strict threshold set, matching the finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `prefetch_idx = torch\.topk\(` in `speedup/infinigen/infinigen/kv_selection_controller.py` expected present: **confirmed** (1 hit(s)). Confirms prefetch indices are produced by top-k selection.
- probe `mean = torch\.mean\(torch\.sum\(count, dim=-1\)\)\.item\(\)` in `speedup/infinigen/infinigen/kv_selection_controller.py` expected present: **confirmed** (1 hit(s)). Shows k is derived from the mean thresholded-token count.
- probe `prefetch_idx = torch\.where\(p_attn > thr_` in `speedup/infinigen/infinigen/kv_selection_controller.py` expected absent: **confirmed** (0 hit(s)). No direct threshold-mask assignment to prefetch_idx exists.
- what would settle it: Inspect or run speculate_attention on a case where the >max−alpha set size differs from the mean count and compare returned indices against the threshold mask.

## infinigen-F023

**实验路径以绝对令牌数封顶，未实现 20% 比例上限**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/kv_selection_controller.py:28-63`
- condition: `mean > max_num_kv`
- paper/docs (paper, PDF p.10): “For each layer, we allow sending up to 20% of the total KV cache to the GPU if it contains more candidates.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown selection function caps top-k with min(int(mean), max_num_kv), an absolute token count. The paper promises up to 20% of total KV cache. Although --partial-weight-ratio defaults to 0.2, the shown code does not use it in the cap; max_num_kv defaults to 400. Thus the evidence supports the deviation, subject to checking whether max_num_kv is derived from 20% elsewhere.
- cited code found at the pinned commit: yes (2 location(s))
- probe `min\(int\(mean\), max_num_kv\)` in `speedup/infinigen/infinigen/kv_selection_controller.py` expected present: **confirmed** (1 hit(s)). Top-k cap uses absolute max_num_kv, not a ratio.
- probe `partial_weight_ratio|0\.2|20\s*%|\bratio\b` in `speedup/infinigen/infinigen/kv_selection_controller.py` expected absent: **confirmed** (0 hit(s)). No ratio-based cap appears in the selection function.
- probe `partial_weight_ratio` in `speedup/flexgen/infinigen/flex_opt.py` expected absent: **refuted** (8 hit(s)). Flag is defined but never read, so 0.2 is not used.
- what would settle it: Search flex_opt.py for reads of partial_weight_ratio and trace how max_num_kv is set; if max_num_kv is never derived from 20% of KV cache, the finding is confirmed.

## infinigen-F024

**实验路径缺少K的逐元素绝对值**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- condition: `partial_weight_ratio is not None and not warmup`
- paper/docs (paper, PDF p.9): “we first take the element-wise absolute values of the skewed query and key matrices”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown index-generation function takes only `query` and computes `torch.abs(query)`; no key argument or key absolute value is used. The backend calls it with `q` only. This matches the finding that the experimental path lacks element-wise absolute values of K, though the paper says both skewed query and key matrices are used.
- cited code found at the pinned commit: yes (3 location(s))
- probe `torch\.abs\([^\n]*key` in `speedup/infinigen/infinigen/partial_weight_generation_controller.py` expected absent: **confirmed** (0 hit(s)). No key absolute value in index generation; control shows query absolute value exists.
- probe `partial_weight_index_generation\(q,` in `speedup/flexgen/infinigen/pytorch_backend.py` expected present: **confirmed** (1 hit(s)). Index generation is called with q only, not k.
- what would settle it: Inspect or run the index-generation path to verify whether any key absolute value is ever computed before top-k selection.

## infinigen-F025

**求和对象缺少K_abs项**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- paper/docs (paper, PDF p.9): “We then sum the elements in each column”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited speedup function computes top-k indices using only torch.abs(query) summed over columns; it never accepts or sums key magnitudes. The accuracy implementation separately sums both query_states and key, indicating the intended selection includes K_abs. Thus the speedup path omits the K_abs term on every call.
- cited code found at the pinned commit: yes (3 location(s))
- probe `torch\.abs\(\s*key` in `speedup/infinigen/infinigen/partial_weight_generation_controller.py` expected absent: **confirmed** (0 hit(s)). No key-absolute sum in top-k selection; query-only sum is present.
- probe `torch\.abs\(key` in `accuracy/src/modeling_opt_ours_setup.py` expected present: **confirmed** (1 hit(s)). Accuracy path includes key magnitudes, contrasting the speedup omission.
- what would settle it: Run or inspect partial_weight_index_generation with a key input where key-based top-k differs from query-only top-k and verify whether selected indices change.

## infinigen-F026

**单次topk未容纳K离群列**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- paper/docs (paper, PDF p.9): “perform top-k operation only once while accommodating the outlier columns of both query and key matrices”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The speedup path computes top-k only from the query matrix, so key-only outlier columns cannot be included in the single top-k. The accuracy path instead performs two separate top-k calls, one for query and one for key, not one combined top-k over both. This matches the claimed deviation from the paper's single top-k accommodating both query and key outliers.
- cited code found at the pinned commit: yes (3 location(s))
- probe `torch\.topk\(\s*torch\.sum\(torch\.abs\(query` in `speedup/infinigen/infinigen/partial_weight_generation_controller.py` expected present: **refuted** (0 hit(s)). Top-k source is the query matrix only.
- probe `torch\.topk\([^)]*key` in `speedup/infinigen/infinigen/partial_weight_generation_controller.py` expected absent: **confirmed** (0 hit(s)). No top-k over key matrix in speedup path.
- probe `(?s)torch\.topk\(torch\.sum\(torch\.abs\(query_states.*?torch\.topk\(torch\.sum\(torch\.abs\(key` in `accuracy/src/modeling_opt_ours_setup.py` expected present: **refuted** (0 hit(s)). Accuracy path uses two separate top-k calls, not one combined.
- what would settle it: Run the prefill selection with a key matrix whose outlier columns differ from the query's and verify whether selected indices include key-only outliers.

## infinigen-F027

**When (i == 0) or (i == (self.config.num_hidden_layers - 1)): When sep_layer is set, the first and last layers are constructed as SelfAttention with the flag False (no InfiniGen KV selection), while all middle layers get True. So the InfiniGen mechanism is only applied to interior layers; boundary layers run the plain attention path. (speedup/flexgen/infinigen/flex_opt.py:690)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:690` in `speedup/flexgen/infinigen/flex_opt.py::OptLM.__init__`
- condition: `(i == 0) or (i == (self.config.num_hidden_layers - 1))`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: The last layer still has its KV selected by the previous layer's speculation and layer 1 also runs on full KV, so 'boundary layers run plain attention, interior layers get InfiniGen' misstates the effect (the real limitation is item 10).
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:690`): `if i == 0 or i == self.config.num_hidden_layers - 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at speedup/flexgen/infinigen/flex_opt.py:690 (later RuntimeError at torch/cuda/_utils.py:46)
- contrast run: branch not taken at speedup/flexgen/infinigen/flex_opt.py:690 (later RuntimeError at torch/cuda/_utils.py:46)
- open doubts:
  - D6 verdict-bearing observations do not depend on stand-ins: *residual*. verdict-bearing observations: positive simulated:fake, negative simulated:fake; stand-in checks: flexgen.infinigen.flex_opt.range agrees
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: TorchDevice.mha has no static call path to OptLM.__init__ (call_chain_status not_found), so the driver instantiates OptLM directly to reach the branch at line 690.
- what would raise the level: D6 (residual): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/infinigen/infinigen-F027/execution_report.json`

## infinigen-F028

**When warmup or partial_weight_ratio is None: In TorchDevice.mha, the partial-weight index (which heads/rows of the query projection are used for the InfiniGen speculation) is only computed when warmup is False and partial_weight_ratio is not None. Otherwise partial_weight_index stays None (line 325) and is returned as None (line 379), so mha_gen receives p_w_q=None and the KV speculation is sil...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:326` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha`
- condition: `warmup or partial_weight_ratio is None`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: partial_weight_index being None does not make mha_gen get p_w_q=None; p_w_q comes from partial_weight_read_buf (filled by the next layer) whenever enable_prefetching is set, so speculation is not skipped as claimed.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:326`): `if not warmup and partial_weight_ratio is not None:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect only on the negative input: boundary direction reversed

Code side predicted ceiling before the test: L1 (measured: n/a).

**Level n/a, uncalibrated.** no verdict, so no level. verdict is inconclusive; no confidence is assigned to it

- trigger run: branch not taken at speedup/flexgen/infinigen/pytorch_backend.py:326 (later RuntimeError at speedup/infinigen/infinigen/skewing_controller.py:82)
- contrast run: branch taken at speedup/flexgen/infinigen/pytorch_backend.py:326
- open doubts:
  - D3 oracle can see the effect: *open*. mutation not run
  - D4 oracle is specified, located, pre-registered: *residual*. oracle changed 1 time(s) after the first run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'warmup' is not an integer (value False)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D4 (residual): state the oracle as exception type + Region.location and register it before the first run; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/infinigen/infinigen-F028/execution_report.json`

## infinigen-F029

**When not (dst.device.device_type != DeviceType.MIXED): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:837)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:837` in `speedup/flexgen/infinigen/pytorch_backend.py::general_copy`
- condition: `not (dst.device.device_type != DeviceType.MIXED)`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:837`): `assert dst.device.device_type != DeviceType.MIXED`

**Not tested** (`witness_unusable`): witness status 'infeasible': step 4 shows the condition cannot hold together with the path to the target, so the official entry cannot reach it; testing the inner function directly would not test the product

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line is exactly `assert dst.device.device_type != DeviceType.MIXED`. In Python, if `device_type` is `MIXED`, the expression is false and `AssertionError` is raised, matching the finding. The paper-disclosure aspect is not evidenced, but the code behavior is directly supported.
- cited code found at the pinned commit: yes (1 location(s))
- probe `assert\s+dst\.device\.device_type\s*!=\s*DeviceType\.MIXED` in `speedup/flexgen/infinigen/pytorch_backend.py` expected present: **confirmed** (1 hit(s)). Line asserts destination device is not MIXED, so MIXED raises AssertionError.
- what would settle it: A static check of line 837 plus a paper search for MIXED-device restrictions would settle whether the assertion is present and undisclosed.

## infinigen-F030

**论文要求饱和时全体减半；代码无该步骤（artifact 范围：无饱和减半）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `accuracy/perplexity/table2.sh:27-45`
- condition: `self.eviction_policy == "counter"`
- paper/docs (paper, PDF p.10): “If any counter becomes saturated, all the counter values are reduced by half.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown counter-eviction code computes a counter over the first half and evicts the minimum; it contains no saturation check or halving of all counters. The table2 script only passes an eviction policy. This supports the claim that the saturation-halving step is not implemented in the artifact scope shown.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)(saturat|reduc(e|ed|ing)\s+(all\s+)?(the\s+)?counter|counter\s+values?\s+.*half|half\s+.*counter)` in `accuracy/src/modeling_opt_ours.py` expected absent: **confirmed** (0 hit(s)). No saturation-triggered counter halving logic in this file.
- probe `(?i)(saturat|half|reduce.*counter)` in `accuracy/perplexity/table2.sh` expected absent: **confirmed** (0 hit(s)). Script selects eviction policies but has no saturation-halving step.
- what would settle it: Inspect the full counter-eviction implementation and run a counter-saturation case to see whether all counters are halved.

## infinigen-F031

**实验路径缺少论文指定的相加步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- paper/docs (paper, PDF p.9): “then add these two matrices together”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code computes top-k indices from the query matrix alone and, in the modeling path, builds a mask by scattering query-derived and key-derived indices separately. It never adds the two matrices together as the paper specifies, so the missing addition step is visible on every call through this path.
- cited code found at the pinned commit: yes (3 location(s))
- probe `query\s*\+\s*key|key\s*\+\s*query|torch\.add` in `speedup/infinigen/infinigen/partial_weight_generation_controller.py` expected absent: **confirmed** (0 hit(s)). No query-key matrix addition in index generation; top-k is present.
- probe `weight_mask\s*\+=` in `accuracy/src/modeling_opt_ours_setup.py` expected absent: **confirmed** (0 hit(s)). Mask is overwritten by scatter, not accumulated by addition.
- what would settle it: A direct code inspection or unit test checking whether the query and key partial-weight matrices are summed before use would settle it.

