# Limitations report: QoServe: Breaking the Silos of LLM Inference Serving (Niyama)

- artifact: `qoserve` (ASPLOS 2026), repository https://github.com/microsoft/sarathi-serve at `72339db5b1`
- input: `results/step4/qoserve/limitations_for_tests.json` (sha256 `79eb69f6ac71`), 50 Findings
- generated: 2026-11-18T00:48:58+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
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
| Findings | 50 |
| tested | 9 |
| not tested | 41 |
| verdicts | yes 9 |
| levels | L1 4, L3 5 |
| not tested, by reason | `no_code_location` 36, `outcome_unsupported` 5 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [qoserve-F001](#qoserve-f001) | undisclosed | reject | `sarathi/core/scheduler/deadline_scheduler.py:251` | **yes** / L1 (uncalibrated) |
| [qoserve-F002](#qoserve-f002) | undisclosed | reject | `sarathi/core/scheduler/deadline_scheduler.py:253` | **yes** / L1 (uncalibrated) |
| [qoserve-F003](#qoserve-f003) | docs_only | other | `sarathi/core/datatypes/sequence.py:73` | not tested: `outcome_unsupported` |
| [qoserve-F004](#qoserve-f004) | undisclosed | path_change | `sarathi/core/datatypes/sequence.py:114` | **yes** / L3 (uncalibrated) |
| [qoserve-F005](#qoserve-f005) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:120` | **yes** / L3 (uncalibrated) |
| [qoserve-F006](#qoserve-f006) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:130` | **yes** / L3 (uncalibrated) |
| [qoserve-F007](#qoserve-f007) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:231` | **yes** / L3 (uncalibrated) |
| [qoserve-F008](#qoserve-f008) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:233` | **yes** / L1 (uncalibrated) |
| [qoserve-F009](#qoserve-f009) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:276` | **yes** / L1 (uncalibrated) |
| [qoserve-F010](#qoserve-f010) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:300` | **yes** / L3 (uncalibrated) |
| [qoserve-F011](#qoserve-f011) | impl_deviates | other | `README.md:1-129` | not tested: `no_code_location` |
| [qoserve-F012](#qoserve-f012) | impl_deviates | other | `chunk_size_predictor/predictor.py:1-41` | not tested: `no_code_location` |
| [qoserve-F013](#qoserve-f013) | impl_deviates | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F014](#qoserve-f014) | impl_deviates | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F015](#qoserve-f015) | impl_deviates | other | `paper_plot_scripts/fig7_cap.py:13-47` | not tested: `no_code_location` |
| [qoserve-F016](#qoserve-f016) | impl_deviates | other | `paper_plot_scripts/fig_10_11.py:1-20` | not tested: `no_code_location` |
| [qoserve-F017](#qoserve-f017) | impl_deviates | other | `paper_plot_scripts/fig_10_11.py:19-37` | not tested: `no_code_location` |
| [qoserve-F018](#qoserve-f018) | impl_deviates | other | `sarathi/config/config.py:284-311` | not tested: `no_code_location` |
| [qoserve-F019](#qoserve-f019) | impl_deviates | other | `sarathi/config/config.py:284-311` | not tested: `no_code_location` |
| [qoserve-F020](#qoserve-f020) | impl_deviates | other | `sarathi/core/datatypes/sequence.py:70-80` | not tested: `no_code_location` |
| [qoserve-F021](#qoserve-f021) | impl_deviates | other | `sarathi/core/datatypes/sequence.py:88-109` | not tested: `no_code_location` |
| [qoserve-F022](#qoserve-f022) | impl_deviates | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location` |
| [qoserve-F023](#qoserve-f023) | impl_deviates | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location` |
| [qoserve-F024](#qoserve-f024) | undisclosed | other | `sarathi/core/datatypes/sequence.py:80` | not tested: `outcome_unsupported` |
| [qoserve-F025](#qoserve-f025) | undisclosed | other | `sarathi/core/scheduler/deadline_scheduler.py:92` | not tested: `outcome_unsupported` |
| [qoserve-F026](#qoserve-f026) | undisclosed | other | `sarathi/core/scheduler/deadline_scheduler.py:211` | not tested: `outcome_unsupported` |
| [qoserve-F027](#qoserve-f027) | undisclosed | other | `sarathi/core/scheduler/deadline_scheduler.py:305` | not tested: `outcome_unsupported` |
| [qoserve-F028](#qoserve-f028) | not_implemented | other | `chunk_size_predictor/predictor.py:1-41` | not tested: `no_code_location` |
| [qoserve-F029](#qoserve-f029) | not_implemented | other | `fig10_11.sh:103-129` | not tested: `no_code_location` |
| [qoserve-F030](#qoserve-f030) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F031](#qoserve-f031) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F032](#qoserve-f032) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F033](#qoserve-f033) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F034](#qoserve-f034) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F035](#qoserve-f035) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F036](#qoserve-f036) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location` |
| [qoserve-F037](#qoserve-f037) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location` |
| [qoserve-F038](#qoserve-f038) | impl_deviates | other | `fig8.sh:37-69` | not tested: `no_code_location` |
| [qoserve-F039](#qoserve-f039) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location` |
| [qoserve-F040](#qoserve-f040) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location` |
| [qoserve-F041](#qoserve-f041) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location` |
| [qoserve-F042](#qoserve-f042) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location` |
| [qoserve-F043](#qoserve-f043) | not_implemented | other | `paper_plot_scripts/fig_10_11.py:19-37` | not tested: `no_code_location` |
| [qoserve-F044](#qoserve-f044) | not_implemented | other | `run_exp.sh:1-27` | not tested: `no_code_location` |
| [qoserve-F045](#qoserve-f045) | not_implemented | other | `sarathi/config/config.py:284-311` | not tested: `no_code_location` |
| [qoserve-F046](#qoserve-f046) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | not tested: `no_code_location` |
| [qoserve-F047](#qoserve-f047) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | not tested: `no_code_location` |
| [qoserve-F048](#qoserve-f048) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | not tested: `no_code_location` |
| [qoserve-F049](#qoserve-f049) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location` |
| [qoserve-F050](#qoserve-f050) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location` |

## qoserve-F001

**When not (seq.is_paused()): 'Sequence should be in PAUSED state' (sarathi/core/scheduler/deadline_scheduler.py:251)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:251` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `not (seq.is_paused())`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:251`): `assert seq.is_paused()`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at sarathi/core/scheduler/deadline_scheduler.py:251
- contrast run: no exception at sarathi/core/scheduler/deadline_scheduler.py:251
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/qoserve/qoserve-F001/execution_report.json`

## qoserve-F002

**When not (self.block_manager.can_append_slot()): AssertionError (sarathi/core/scheduler/deadline_scheduler.py:253)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:253` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `not (self.block_manager.can_append_slot())`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:253`): `assert self.block_manager.can_append_slot()`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at sarathi/core/scheduler/deadline_scheduler.py:253
- contrast run: no exception at sarathi/core/scheduler/deadline_scheduler.py:253
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/qoserve/qoserve-F002/execution_report.json`

## qoserve-F003

**When NUM_TIERS > 0: Each Sequence's QoS tier (and hence its deadline) is drawn at random from the global `random` module rather than from any caller-supplied SLA. The tier then drives `self.tier_deadline = TIER_DEADLINES[self.tier]` (line 74) and `_get_TBT_deadline`'s choice of `execution_threshold_batched` when `self.tier > 0` (lines 114-115), so the scheduling decision depends on the process-...**

- category `docs_only`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:73` in `sarathi/core/datatypes/sequence.py::Sequence.__init__`
- condition: `NUM_TIERS > 0`
- paper/docs (paper, PDF p.5, text lines 20-30): “3.2 QoS Classes and Deadlines QoServe defines two QoS classes: interactive and non in- teractive. Interactive requests use two SLOs — TTFT (time to first token) and TBT (token-by-token latency), which en- sure immediate responsiveness and consistent pacing. Non- interactive requests have a single T…”
- paper/docs (paper, PDF p.5): “the application owner is free to specify their custom SLO targets within the class”
- code snippet (`sarathi/core/datatypes/sequence.py:73`): `self.tier = random.randint(0, NUM_TIERS - 1)`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## qoserve-F004

**When self.tier > 0: For any non-zero (randomly assigned) tier, the TBT deadline uses execution_threshold_batched instead of execution_threshold, changing the computed deadline. (sarathi/core/datatypes/sequence.py:114)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:114` in `sarathi/core/datatypes/sequence.py::Sequence._get_TBT_deadline`
- condition: `self.tier > 0`
- paper/docs (paper, PDF p.5): “𝐷𝑛 =𝑡𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑇𝑇𝐹𝑇 +(𝑛− 1)· 𝑆𝐿𝑂𝑇𝐵𝑇, (2)”
- code snippet (`sarathi/core/datatypes/sequence.py:114`): `if self.tier > 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at sarathi/core/datatypes/sequence.py:114
- contrast run: branch not taken at sarathi/core/datatypes/sequence.py:114
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/qoserve/qoserve-F004/execution_report.json`

## qoserve-F005

**When memory_budget < 1000: When free KV-cache blocks (free_blocks * block_size // 32) fall below 1000, the prefill token search space is switched from TOKEN_SEARCH_SPACE (up to 2552) to LOW_MEMORY_TOKEN_SEARCH_SPACE (128-512), capping the prefill size the slack-based search can return. (sarathi/core/scheduler/deadline_scheduler.py:120)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:120` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._get_prefill_size_by_slack`
- condition: `memory_budget < 1000`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:120`): `if memory_budget < 1000:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at sarathi/core/scheduler/deadline_scheduler.py:120
- contrast run: branch not taken at sarathi/core/scheduler/deadline_scheduler.py:120
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/qoserve/qoserve-F005/execution_report.json`

## qoserve-F006

**When min_slack <= 0: When the caller-supplied slack is non-positive, the binary search is skipped entirely and the function returns the smallest search-space entry (128) minus decode tokens, i.e. a fixed minimal prefill rather than a slack-derived size. (sarathi/core/scheduler/deadline_scheduler.py:130)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:130` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._get_prefill_size_by_slack`
- condition: `min_slack <= 0`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:130`): `if min_slack <= 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at sarathi/core/scheduler/deadline_scheduler.py:130
- contrast run: branch not taken at sarathi/core/scheduler/deadline_scheduler.py:130
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/qoserve/qoserve-F006/execution_report.json`

## qoserve-F007

**When seq.tier >= 1: For tier>=1 sequences the ttft_deadline is recomputed by subtracting predicted decode time (output_len_pred or num_decode_tokens times execution_threshold_batched); tier 0 sequences keep their original deadline. (sarathi/core/scheduler/deadline_scheduler.py:231)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:231` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `seq.tier >= 1`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:231`): `if seq.tier >= 1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at sarathi/core/scheduler/deadline_scheduler.py:231
- contrast run: branch not taken at sarathi/core/scheduler/deadline_scheduler.py:231
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/qoserve/qoserve-F007/execution_report.json`

## qoserve-F008

**When seq.num_decode_tokens == -1: Selects whether the decode-time estimate uses the global output_len_pred or the per-sequence num_decode_tokens when computing ttft_deadline. (sarathi/core/scheduler/deadline_scheduler.py:233)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:233` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `seq.num_decode_tokens == -1`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:233`): `if seq.num_decode_tokens == -1:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at sarathi/core/scheduler/deadline_scheduler.py:233
- contrast run: branch not taken at sarathi/core/scheduler/deadline_scheduler.py:233
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/qoserve/qoserve-F008/execution_report.json`

## qoserve-F009

**When self.scheduler_type == 'deadline': Only when scheduler_type is 'deadline' is the dynamic chunk size computed via _get_prefill_size_by_slack; otherwise prefill_token_limit stays at chunk_size - num_batched_tokens. (sarathi/core/scheduler/deadline_scheduler.py:276)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:276` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `self.scheduler_type == 'deadline'`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:276`): `if self.scheduler_type == 'deadline':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at sarathi/core/scheduler/deadline_scheduler.py:276
- contrast run: branch not taken at sarathi/core/scheduler/deadline_scheduler.py:276
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'scheduler_type' is not an integer (value 'fcfs')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/qoserve/qoserve-F009/execution_report.json`

## qoserve-F010

**When self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking': The eager-relegation deadline check (service_time_required vs ttft_deadline) only runs for these two scheduler types; other types skip the drop logic. (sarathi/core/scheduler/deadline_scheduler.py:300)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:300` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:300`): `if self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L3, uncalibrated.** established: every defeater was measured and ruled out.

- trigger run: branch taken at sarathi/core/scheduler/deadline_scheduler.py:300
- contrast run: branch not taken at sarathi/core/scheduler/deadline_scheduler.py:300
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- evidence: `tests/qoserve/qoserve-F010/execution_report.json`

## qoserve-F011

**实验脚本不自动下载数据集，需先手动 wget**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `README.md:1-129`
- paper/docs (paper, PDF p.16, text lines 2-4): “A.3.4 Data sets. ShareGPT [19] and Azure production traces (Code, Conversation) [15]. Scripts automatically down- load datasets from public Azure blob storage.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F012

**论文要求训练随机森林；脚本导入并训练 LinearRegression，无 RandomForest/ensemble**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `chunk_size_predictor/predictor.py:1-41`
- paper/docs (paper, PDF p.7, text lines 48-54): “3.6.1 Dynamic chunking batch predictor. Given the statistics of the requests in a batch, e.g. number of requests, context lengths, etc., the dynamic chunk size predictor de- termines the optimal chunk size that maximizes throughput while adhering to the latency constraints. For this, we train a lig…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F013

**缺 §4.3/§4.4 执行路径**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8, text lines 74-79): “Setup. We first evaluateQoServe under uniform load condi- tions to identify the impact of our design on goodput (§4.1) as well as on latency and SLO violations (§4.2). Next, we evaluate how QoServe performs under transient spikes in load (§4.3), and finally we perform detailed ablation of our indiv…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F014

**缺 Qwen/70B 与 4 小时控制**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `fig7.sh:76-106`
- condition: `MODEL in ('Qwen', '70B') or True`
- paper/docs (paper, PDF p.9, text lines 83-87): “their deadlines. For these single replica experiments, we com- pare against the Sarathi-FCFS and Sarathi-EDF baselines. Figure 7 shows the goodput while serving requests over a 4- hour period across three different datasets and models listed in Table 1. As shown, QoServe achieves 1.5x to 2.4x higher”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F015

**Q1 的 TBT 违规未被度量**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `paper_plot_scripts/fig7_cap.py:13-47`
- condition: `tier == 0`
- paper/docs (paper, PDF p.8): “Q1 33.33% 6 50 -”
- paper/docs (paper, PDF p.8): “Q2 33.33% - - 600”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F016

**图输出目录与论文声明的 paper_plots/ 不一致**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `paper_plot_scripts/fig_10_11.py:1-20`
- paper/docs (paper, PDF p.16): “Results are saved to benchmark_output/ (raw logs) and paper_plots/ (plots and graphs).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F017

**固定阈值替代数据 p90**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `paper_plot_scripts/fig_10_11.py:19-37`
- paper/docs (paper, PDF p.11, text lines 43-45): “length (combined across all QoS buckets). We classify re- quests as long if their prompt token count is greater than or equal to the 90th percentile, and short otherwise. Our”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F018

**脚本层同样无按请求提交 QoS 字段的配置。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/config/config.py:284-311`
- paper/docs (paper, PDF p.7, text lines 26-29): “anisms. We extended the vLLM API to associate each in- ference request with its corresponding QoS requirements (TTFT, TBT, and/or TTLT) and priority level during request submission. The hybrid prioritization policy is implemented”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F019

**脚本层无每请求优先级配置。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/config/config.py:284-311`
- paper/docs (paper, PDF p.7, text lines 26-29): “anisms. We extended the vLLM API to associate each in- ference request with its corresponding QoS requirements (TTFT, TBT, and/or TTLT) and priority level during request submission. The hybrid prioritization policy is implemented”
- paper/docs (paper, PDF p.7): “we add a priority field to each request that enables relegation decisions based on application hints such as free-tier versus premium users”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F020

**实验路径同样没有独立的 D_total 完成截止。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:70-80`
- condition: `seq.tier >= 1`
- paper/docs (paper, PDF p.5): “𝐷𝑡𝑜𝑡𝑎𝑙 =𝑡𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑇𝑇𝐿𝑇 (3)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F021

**论文要求 α 同时乘 (Prefill_rem+Decode_rem)；代码把 decode 估计以固定系数 execution_threshold_batched 从期限中扣除，而非以 α 加权加入剩余工作项，且 α 不作用于 decode 项（artifact 范围：α·Decode_rem 项缺失，decode 以 execution_threshold_batched 线性扣减期限）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:88-109`
- condition: `self.scheduler_type != 'fcfs' and self.scheduler_type != 'edf' and self.scheduler_type != 'srpf' and self.drop == other.drop and seq.tier >= 1`
- paper/docs (paper, PDF p.5): “𝑃𝑖 =𝑡𝑖𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑖𝑇𝑇𝐿𝑇+𝛼∗(𝑃𝑟𝑒𝑓𝑖𝑙𝑙 𝑖𝑟𝑒𝑚+𝐷𝑒𝑐𝑜𝑑𝑒𝑖𝑟𝑒𝑚)”
- paper/docs (paper, PDF p.6, text lines 14-15): “where𝐷𝑒𝑐𝑜𝑑𝑒𝑟𝑒𝑚 indicates the time to compute all the de- code tokens. Since decode length is unknown in LLM in-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F022

**论文要求检查“已违反 或 将违反”TTFT/TTLT；代码仅做 TTFT 前瞻（now+service_time>deadline），且仅对 drop==0 且未分配内存的请求生效，无 TTLT 维度。（artifact 范围：仅 TTFT 前瞻，缺 TTLT 与显式“已违反”判定。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- paper/docs (paper, PDF p.4): “The violation checker module validates that the chosen request has not already violated (or will not violate) its QoS targets in the current iteration”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F023

**论文要求移入独立 relegated 队列；代码仅设 drop 标志并放回原 prefill 队列，无 relegated 队列结构，且 drop 请求仍可被再次选中调度。（artifact 范围：。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- paper/docs (paper, PDF p.6): “if a request has already violated its TTFT / TTLT deadline, or is about to violate it in the current iteration, then QoServe de-prioritizes this request into a relegated queue”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F024

**When self.scheduler_type == 'fcfs': `Sequence.__lt__` dispatches on this per-object attribute: 'fcfs' orders by arrival_time, 'edf' by ttft_deadline+arrival_time, 'srpf' by remaining prompt tokens, and anything else falls through to the hybrid-prioritization deadline. The attribute is hard-coded to 'fcfs' in the constructor, so unless some other code overwrites it after construction, the priori...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:80` in `sarathi/core/datatypes/sequence.py::Sequence.__init__`
- condition: `self.scheduler_type == 'fcfs'`
- code snippet (`sarathi/core/datatypes/sequence.py:80`): `self.scheduler_type = 'fcfs'`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## qoserve-F025

**When batch_num_tokens <= 512: The execution-time predictor switches between two hard-coded stratified linear models at a 512-token boundary, so the prefill size chosen by slack depends on which hard-coded coefficient set applies. (sarathi/core/scheduler/deadline_scheduler.py:92)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:92` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._predict_batch_time`
- condition: `batch_num_tokens <= 512`
- paper/docs (docstring, sarathi/core/scheduler/deadline_scheduler.py:60 (_predict_batch_time)): “Predict execution time using two stratified linear models: - tokens_0_512: 0 < total_tokens <= 512 - tokens_513_plus: total_tokens > 512”
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:92`): `model = tokens_0_512 if batch_num_tokens <= 512 else tokens_513_plus`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## qoserve-F026

**When not self._check_request_prompt_length(seq): Requests whose prompt length fails the check are added to ignored_seq_ids and skipped (the RuntimeError is not raised, so the loop continues). (sarathi/core/scheduler/deadline_scheduler.py:211)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:211` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `not self._check_request_prompt_length(seq)`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:211`): `if not self._check_request_prompt_length(seq):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## qoserve-F027

**When (seq.drop == 0) and (seq.mem_allocated == False) and ((now + service_time_required) > (seq.arrival_time + seq.ttft_deadline)): A not-yet-dropped, unallocated sequence whose estimated prefill service time would miss its ttft_deadline is dropped (drop incremented) and re-pushed to the prefill queue, skipping it this iteration. (sarathi/core/scheduler/deadline_scheduler.py:305)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:305` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `(seq.drop == 0) and (seq.mem_allocated == False) and ((now + service_time_required) > (seq.arrival_time + seq.ttft_deadline))`
- paper/docs (code_comment, sarathi/core/scheduler/deadline_scheduler.py:304): “Eager Relegation: If we cannot finish the request within its deadline, we drop it and re-add to the prefill queue”
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:305`): `if seq.drop == 0 and seq.mem_allocated == False and (now + service_time_required > seq.arrival_time + seq.ttft_deadline):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## qoserve-F028

**论文要求用 Vidur 暴露的 harness 采集剖面；pinned 仓库中不存在该采集实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `chunk_size_predictor/predictor.py:1-41`
- paper/docs (paper, PDF p.7, text lines 56-59): “chunk sizes, batch sizes as well as context lengths. To collect this data, we use a lightweight harness exposed by an infer- ence simulator Vidur [3], and collect profiles for each model, hardware, and parallelism configuration of interest.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F029

**偏斜工作负载未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig10_11.sh:103-129`
- paper/docs (paper, PDF p.12, text lines 64-66): “Workload mix. We evaluate QoServe under skewed work- load distributions: 70-15-15 (interactive dominant) and 15-15- 70 (batch-dominant) at 4.5 QPS. Table 6 presents p99 laten-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F030

**未实现按 QoS 桶独立集群的 silo 部署**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “Sarathi-Silo (SOTA), the State-of-the-art siloed deployment where each QoS bucket is assigned an independent GPU cluster with each replica running a Sarathi scheduler”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F031

**silo 基线整体缺失，无按桶 chunk 配置**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “The strictest QoS bucket with 50ms TBT deadline uses a chunk size of 256, while the other two QoS classes use a large chunk size of 2K to maximize throughput in the siloed baselines.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F032

**集群规模实验缺失**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “The silo baseline allocates dedicated replicas based on capacity estimation from per-replica throughput for each QoS tier: 7 replicas for Q1 and 3 each for Q2 and Q3, totaling 13 GPUs.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F033

**瞬态过载工作负载未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.11): “Load in the system varies dynamically between low (QPS:2.0) and high (QPS:5) points every 15 minutes over a total of 4 hours as shown in Figure 12(a).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F034

**无峰谷比构造**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.11): “This pattern incorporates a 2.5× peak-to-trough ratio consistent with request rate variability documented in LLM production traces [9].”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F035

**集群规模实验缺失**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8, text lines 94-97): “line violations with 23% fewer GPUs. To validate QoServe’s resource efficiency, we reduce the silo allocation to match QoServe’s GPU count (6,2,2 replicas), which causes viola- tions to surge to 60.4%. An alternate 4,3,3 allocation faces”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F036

**替代分配实验缺失**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “An alternate 4,3,3 allocation faces approximately 95% Q1 violations with p99 latency of 385.36s.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F037

**论文要求固定 QPS 下离线扫描 α 0–10；artifact 脚本对 α 只给单一常量 0.016，未遍历 0–10 的 α 网格。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.7, text lines 35-37): “decode length.𝛼 is a configurable hyperparameter. For fixed- QPS runs, we perform an offline sweep of𝛼 values from 0 to 10 and select the value that minimizes SLO violations. An𝛼”
- paper/docs (paper, PDF p.7): “select the value that minimizes SLO violations”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F038

**论文称固定 QPS 采用 8 ms/token；artifact 固定 QPS 运行脚本使用 16 ms/token，与论文所选值不符。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- condition: `hybrid_prioritization_param == 0.016`
- paper/docs (paper, PDF p.7, text lines 35-39): “decode length.𝛼 is a configurable hyperparameter. For fixed- QPS runs, we perform an offline sweep of𝛼 values from 0 to 10 and select the value that minimizes SLO violations. An𝛼 of 8 ms/token provided the best trade-off, reducing violations without affecting tail latency. For variable-QPS, we empl…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F039

**论文要求低负载 α=1 ms/token；artifact 无该取值或负载分段。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.7, text lines 39-40): “without affecting tail latency. For variable-QPS, we employ load-adaptive tuning. At low loads, we set𝛼 = 1 ms/token”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F040

**组件消融未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.12): “we tag all requests as important and evaluate three design elements—dynamic chunking, hybrid prioritization, and eager relegation—starting with the Sarathi-EDF baseline.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F041

**消融表汇总未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.12): “Config Optimal Load High load (QPS=6)QPS % gain % viol % impr.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F042

**alpha 敏感性实验未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.12, text lines 51-54): “To further illustrate the impact of hybrid prioritization, Figure 14 plots the median latency and percentage of dead- line violations as we vary system load across three different values of 𝛼, our hybrid prioritization parameter. As 𝛼 in-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F043

**优先级标注未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `paper_plot_scripts/fig_10_11.py:19-37`
- paper/docs (paper, PDF p.11): “we mark a random set of 20% of requests in each QoS bucket as low priority, based on application hints. The remaining 80% of requests in each bucket are marked as high priority or Important.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F044

**未实现多副本 round-robin 分发**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `run_exp.sh:1-27`
- paper/docs (paper, PDF p.8): “Both deployments use round-robin load balancing across replicas.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F045

**脚本层同样无按应用解码历史。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/config/config.py:284-311`
- paper/docs (paper, PDF p.7, text lines 32-35): “factor𝛼 configurable as a deployment parameter. For non- interactive requests, we maintain a running history of token generation patterns per application to estimate the expected decode length.𝛼 is a configurable hyperparameter. For fixed-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F046

**论文要求优先级驱动的抢占；对齐 artifact 调度路径不执行抢占。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:184-354`
- condition: `len(self.running) > 0 and len(self.waiting) > 0 and self.waiting[0].arrival_time <= now and self._sorting_key(self.waiting[0], now) < self._sorting_key(self.running[0], now)`
- paper/docs (paper, PDF p.6): “we preempt a request to accommodate another with a higher priority only if”
- paper/docs (paper, PDF p.6): “preempting that request for an iteration does not lead to deadline violation”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F047

**缺少 prefill 队列抢占资格判定。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:184-354`
- condition: `seq.mem_allocated == True`
- paper/docs (paper, PDF p.6): “(1) the in-flight request is in the prefill queue”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F048

**论文所述避免队头阻塞的抢占手段在 DeadlineScheduler 中不存在。（artifact 范围：。）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:184-354`
- condition: `len(self.running) > 0 and len(self._prefill_queue) > 0`
- paper/docs (paper, PDF p.6): “is a desirable capability as it avoids head-of-line blocking of small interactive requests behind long batch requests”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F049

**论文要求按优先级抢占已部分 prefill 的在途请求；代码无任何抢占触发或调用，仅通过堆排序选择未开始的请求**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- paper/docs (paper, PDF p.6): “Note that our hybrid prioritization scheduling can preempt an in-flight request for which a few prefill chunks have already been processed to instead service a new request with strict QoS target (see eq 4).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## qoserve-F050

**论文要求按优先级分层、低优先级耗尽后才降级高优先级；代码对所有请求一视同仁按截止时间降级，无分层门控。（artifact 范围：。）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- paper/docs (paper, PDF p.6): “Only when there are no more low-priority requests, QoServe proactively relegates high-priority requests that have violated their deadlines to prevent cascading deadline violations.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

