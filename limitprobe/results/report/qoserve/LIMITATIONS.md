# Limitations report: QoServe: Breaking the Silos of LLM Inference Serving (Niyama)

- artifact: `qoserve` (ASPLOS 2026), repository https://github.com/microsoft/sarathi-serve at `72339db5b1`
- input: `results/step4/qoserve/limitations_for_tests.json` (sha256 `bcd4fb7a75d0`), 50 Findings
- generated: 2026-11-23T11:22:10+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
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
| Findings | 50 |
| tested | 9 |
| not tested | 41 |
| verdicts | yes 9 |
| levels | L1 4, L3 5 |
| analysis only (not tests) | A0 6, A1 3, A2 32 |
| not tested, by reason | `no_code_location` 36, `outcome_unsupported` 5 |

Code side's predicted ceiling vs measured level (both uncalibrated; 9 tested Findings have both): equal 9, measured below ceiling 0, measured above ceiling 0.

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [qoserve-F001](#qoserve-f001) | undisclosed | reject | `sarathi/core/scheduler/deadline_scheduler.py:251` | **yes** / L1 (uncalibrated) |
| [qoserve-F002](#qoserve-f002) | undisclosed | reject | `sarathi/core/scheduler/deadline_scheduler.py:253` | **yes** / L1 (uncalibrated) |
| [qoserve-F003](#qoserve-f003) | docs_only | other | `sarathi/core/datatypes/sequence.py:73` | not tested: `outcome_unsupported`, analysis A2/supports |
| [qoserve-F004](#qoserve-f004) | undisclosed | path_change | `sarathi/core/datatypes/sequence.py:114` | **yes** / L3 (uncalibrated) |
| [qoserve-F005](#qoserve-f005) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:120` | **yes** / L3 (uncalibrated) |
| [qoserve-F006](#qoserve-f006) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:130` | **yes** / L3 (uncalibrated) |
| [qoserve-F007](#qoserve-f007) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:231` | **yes** / L3 (uncalibrated) |
| [qoserve-F008](#qoserve-f008) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:233` | **yes** / L1 (uncalibrated) |
| [qoserve-F009](#qoserve-f009) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:276` | **yes** / L1 (uncalibrated) |
| [qoserve-F010](#qoserve-f010) | undisclosed | path_change | `sarathi/core/scheduler/deadline_scheduler.py:300` | **yes** / L3 (uncalibrated) |
| [qoserve-F011](#qoserve-f011) | impl_deviates | other | `README.md:1-129` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F012](#qoserve-f012) | impl_deviates | other | `chunk_size_predictor/predictor.py:1-41` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F013](#qoserve-f013) | impl_deviates | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F014](#qoserve-f014) | impl_deviates | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F015](#qoserve-f015) | impl_deviates | other | `paper_plot_scripts/fig7_cap.py:13-47` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F016](#qoserve-f016) | impl_deviates | other | `paper_plot_scripts/fig_10_11.py:1-20` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F017](#qoserve-f017) | impl_deviates | other | `paper_plot_scripts/fig_10_11.py:19-37` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F018](#qoserve-f018) | impl_deviates | other | `sarathi/config/config.py:284-311` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F019](#qoserve-f019) | impl_deviates | other | `sarathi/config/config.py:284-311` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F020](#qoserve-f020) | impl_deviates | other | `sarathi/core/datatypes/sequence.py:70-80` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F021](#qoserve-f021) | impl_deviates | other | `sarathi/core/datatypes/sequence.py:88-109` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F022](#qoserve-f022) | impl_deviates | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location`, analysis A0/supports |
| [qoserve-F023](#qoserve-f023) | impl_deviates | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F024](#qoserve-f024) | undisclosed | other | `sarathi/core/datatypes/sequence.py:80` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [qoserve-F025](#qoserve-f025) | undisclosed | other | `sarathi/core/scheduler/deadline_scheduler.py:92` | not tested: `outcome_unsupported`, analysis A0/contradicts |
| [qoserve-F026](#qoserve-f026) | undisclosed | other | `sarathi/core/scheduler/deadline_scheduler.py:211` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [qoserve-F027](#qoserve-f027) | undisclosed | other | `sarathi/core/scheduler/deadline_scheduler.py:305` | not tested: `outcome_unsupported`, analysis A0/contradicts |
| [qoserve-F028](#qoserve-f028) | not_implemented | other | `chunk_size_predictor/predictor.py:1-41` | not tested: `no_code_location`, analysis A1/unclear |
| [qoserve-F029](#qoserve-f029) | not_implemented | other | `fig10_11.sh:103-129` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F030](#qoserve-f030) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F031](#qoserve-f031) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F032](#qoserve-f032) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F033](#qoserve-f033) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F034](#qoserve-f034) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F035](#qoserve-f035) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F036](#qoserve-f036) | not_implemented | other | `fig7.sh:76-106` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F037](#qoserve-f037) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F038](#qoserve-f038) | impl_deviates | other | `fig8.sh:37-69` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F039](#qoserve-f039) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F040](#qoserve-f040) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location`, analysis A0/contradicts |
| [qoserve-F041](#qoserve-f041) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F042](#qoserve-f042) | not_implemented | other | `fig8.sh:37-69` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F043](#qoserve-f043) | not_implemented | other | `paper_plot_scripts/fig_10_11.py:19-37` | not tested: `no_code_location`, analysis A0/supports |
| [qoserve-F044](#qoserve-f044) | not_implemented | other | `run_exp.sh:1-27` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F045](#qoserve-f045) | not_implemented | other | `sarathi/config/config.py:284-311` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F046](#qoserve-f046) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F047](#qoserve-f047) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F048](#qoserve-f048) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F049](#qoserve-f049) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location`, analysis A2/supports |
| [qoserve-F050](#qoserve-f050) | not_implemented | other | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | not tested: `no_code_location`, analysis A0/supports |

## qoserve-F001

**When not (seq.is_paused()): 'Sequence should be in PAUSED state' (sarathi/core/scheduler/deadline_scheduler.py:251)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:251` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `not (seq.is_paused())`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:251`): `assert seq.is_paused()`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

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

Code side predicted ceiling before the test: L1 (measured: L1).

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

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says application owners can specify custom SLO targets and mentions free/paid hints, while the shown code assigns each Sequence a random tier and derives its deadline from TIER_DEADLINES. The finding's core claim that QoS tier/deadline is randomized rather than caller-supplied is directly supported by the code evidence.
- cited code found at the pinned commit: yes (6 location(s))
- probe `self\.tier\s*=\s*random\.randint\(0,\s*NUM_TIERS\s*-\s*1\)` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Confirms tier is randomly assigned, not supplied by caller.
- probe `self\.tier_deadline\s*=\s*TIER_DEADLINES\[self\.tier\]` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Confirms deadline is derived from the random tier.
- probe `execution_threshold_batched` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (2 hit(s)). Shows TBT deadline logic references tier-dependent execution threshold.
- probe `if\s+self\.tier\s*>\s*0` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Shows scheduling threshold selection depends on tier value.
- what would settle it: Run a small unit test constructing Sequences with NUM_TIERS>0 and verify tier/deadline vary randomly and ignore any caller SLA input.

## qoserve-F004

**When self.tier > 0: For any non-zero (randomly assigned) tier, the TBT deadline uses execution_threshold_batched instead of execution_threshold, changing the computed deadline. (sarathi/core/datatypes/sequence.py:114)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:114` in `sarathi/core/datatypes/sequence.py::Sequence._get_TBT_deadline`
- condition: `self.tier > 0`
- paper/docs (paper, PDF p.5): “𝐷𝑛 =𝑡𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑇𝑇𝐹𝑇 +(𝑛− 1)· 𝑆𝐿𝑂𝑇𝐵𝑇, (2)”
- code snippet (`sarathi/core/datatypes/sequence.py:114`): `if self.tier > 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L3 (measured: L3).

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

Code side predicted ceiling before the test: L3 (measured: L3).

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

Code side predicted ceiling before the test: L3 (measured: L3).

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

Code side predicted ceiling before the test: L3 (measured: L3).

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

Code side predicted ceiling before the test: L1 (measured: L1).

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

Code side predicted ceiling before the test: L1 (measured: L1).

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

Code side predicted ceiling before the test: L3 (measured: L3).

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

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says scripts automatically download Azure datasets, but the repository README explicitly instructs users to create data/processed_traces and manually wget the Code and Conversation traces before benchmarking. The shown benchmark script invokes the benchmark runner without any visible download step. This supports the claim that dataset preparation is manual rather than automatic.
- cited code found at the pinned commit: yes (2 location(s))
- probe `wget -O data/processed_traces/AzureLLMInferenceTrace_(code|conv)_1week.csv` in `README.md` expected present: **confirmed** (2 hit(s)). README requires manual wget for Azure trace datasets.
- probe `wget|curl|download` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). Benchmark script lacks auto-download command; manual prep needed.
- what would settle it: Run the benchmark from a clean checkout and check whether data/processed_traces is populated without manual wget.

## qoserve-F012

**论文要求训练随机森林；脚本导入并训练 LinearRegression，无 RandomForest/ensemble**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `chunk_size_predictor/predictor.py:1-41`
- paper/docs (paper, PDF p.7, text lines 48-54): “3.6.1 Dynamic chunking batch predictor. Given the statistics of the requests in a batch, e.g. number of requests, context lengths, etc., the dynamic chunk size predictor de- termines the optimal chunk size that maximizes throughput while adhering to the latency constraints. For this, we train a lig…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper explicitly says the dynamic chunk size predictor uses a lightweight random forest trained on latency data. The cited code imports sklearn.linear_model.LinearRegression and instantiates LinearRegression in train_stratified_models. No random-forest import or estimator appears in the shown code. Thus the implementation deviates from the paper's stated model choice on every training call.
- cited code found at the pinned commit: yes (3 location(s))
- probe `RandomForest|RandomForestRegressor|sklearn\.ensemble` in `chunk_size_predictor/predictor.py` expected absent: **confirmed** (0 hit(s)). Absence shows no random-forest model is imported or used in this file.
- probe `model\s*=\s*LinearRegression\s*\(` in `chunk_size_predictor/predictor.py` expected present: **confirmed** (1 hit(s)). Presence shows the script instantiates a linear regression model for training.
- what would settle it: Inspect the full predictor training path and confirm no random-forest estimator is imported, instantiated, or fitted anywhere.

## qoserve-F013

**缺 §4.3/§4.4 执行路径**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8, text lines 74-79): “Setup. We first evaluateQoServe under uniform load condi- tions to identify the impact of our design on goodput (§4.1) as well as on latency and SLO violations (§4.2). Next, we evaluate how QoServe performs under transient spikes in load (§4.3), and finally we perform detailed ablation of our indiv…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited scripts run Poisson/QPS sweeps and scheduler comparisons; neither contains transient-spike or ablation logic. The paper explicitly assigns those evaluations to §4.3/§4.4. Within the shown code, the claimed execution paths are absent, so the finding is supported, though a full-repo search would strengthen it.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)transient|spike|ablation` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). Absence shows this script lacks §4.3/§4.4 experiment logic.
- probe `(?i)transient|spike|ablation` in `fig10_11.sh` expected absent: **confirmed** (0 hit(s)). Absence shows this sweep script lacks §4.3/§4.4 experiment logic.
- what would settle it: Search the full repository for any script or flag implementing transient-spike and ablation experiments; if none exists, the finding is confirmed.

## qoserve-F014

**缺 Qwen/70B 与 4 小时控制**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `fig7.sh:76-106`
- condition: `MODEL in ('Qwen', '70B') or True`
- paper/docs (paper, PDF p.9, text lines 83-87): “their deadlines. For these single replica experiments, we com- pare against the Sarathi-FCFS and Sarathi-EDF baselines. Figure 7 shows the goodput while serving requests over a 4- hour period across three different datasets and models listed in Table 1. As shown, QoServe achieves 1.5x to 2.4x higher”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The Fig.7 script names three traces but no Qwen/70B model; it uses $MODEL. Its time_limit is 33000000000, not an explicit 4-hour value (if microseconds, ~9.2h). Thus the shown artifact lacks the paper's stated Qwen/70B and 4-hour setup. The model could be external, but the script itself does not show it.
- cited code found at the pinned commit: yes (2 location(s))
- probe `Qwen|70B|Qwen2|Llama-?70` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No Qwen/70B model named in Fig.7 script.
- probe `time_limit\s+14400(000000)?|4\s*hour|4h` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No explicit 4-hour time limit; script sets 33000000000.
- probe `time_limit\s+33000000000` in `fig7.sh` expected present: **confirmed** (1 hit(s)). Fig.7 uses 33e9 time limit, not 4h.
- what would settle it: Check fig7.sh and any sourced environment for MODEL and time_limit to see if Qwen/70B is run and whether the cap equals 4 hours.

## qoserve-F015

**Q1 的 TBT 违规未被度量**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `paper_plot_scripts/fig7_cap.py:13-47`
- condition: `tier == 0`
- paper/docs (paper, PDF p.8): “Q1 33.33% 6 50 -”
- paper/docs (paper, PDF p.8): “Q2 33.33% - - 600”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The violation calculation only uses prefill_e2e_time for tier 0 and request_e2e_time for tiers 1/2. There is no TBT or inter-token latency metric in the shown code, so Q1 TBT violations are not measured by this script.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)tbt|time_between|inter_token|token_latency` in `paper_plot_scripts/fig7_cap.py` expected absent: **confirmed** (0 hit(s)). No TBT metric appears; control confirms the file was searched.
- probe `metric_col = 'prefill_e2e_time' if tier == 0` in `paper_plot_scripts/fig7_cap.py` expected present: **confirmed** (1 hit(s)). Tier 0 violations are computed from prefill time, not TBT.
- what would settle it: Inspect sequence_metrics.csv columns and recompute Q1 violations using a TBT/inter-token column; absence or non-use would confirm.

## qoserve-F016

**图输出目录与论文声明的 paper_plots/ 不一致**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `paper_plot_scripts/fig_10_11.py:1-20`
- paper/docs (paper, PDF p.16): “Results are saved to benchmark_output/ (raw logs) and paper_plots/ (plots and graphs).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states plots are saved to paper_plots/, while the cited script hardcodes OUTPUT_DIR = "plots_fig_10_11". This is a direct implementation deviation in the output path, independent of runtime inputs.
- cited code found at the pinned commit: yes (1 location(s))
- probe `OUTPUT_DIR\s*=\s*"plots_fig_10_11"` in `paper_plot_scripts/fig_10_11.py` expected present: **confirmed** (1 hit(s)). Confirms the script hardcodes a different output directory than paper_plots/.
- what would settle it: Run the script and verify plots are written under plots_fig_10_11/ rather than paper_plots/.

## qoserve-F017

**固定阈值替代数据 p90**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `paper_plot_scripts/fig_10_11.py:19-37`
- paper/docs (paper, PDF p.11, text lines 43-45): “length (combined across all QoS buckets). We classify re- quests as long if their prompt token count is greater than or equal to the 90th percentile, and short otherwise. Our”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper defines long requests using the 90th percentile of prompt token counts. The cited code instead sets a fixed LONG_REQUEST_THRESH = 6200, so short/long classification does not depend on the input distribution. This directly matches the claimed implementation deviation.
- cited code found at the pinned commit: yes (1 location(s))
- probe `LONG_REQUEST_THRESH\s*=\s*6200` in `paper_plot_scripts/fig_10_11.py` expected present: **confirmed** (1 hit(s)). Shows the long-request cutoff is hardcoded to 6200, not computed as p90.
- what would settle it: Inspect or run the classification code on datasets with different prompt-length distributions to verify the cutoff remains fixed at 6200.

## qoserve-F018

**脚本层同样无按请求提交 QoS 字段的配置。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/config/config.py:284-311`
- paper/docs (paper, PDF p.7, text lines 26-29): “anisms. We extended the vLLM API to associate each in- ference request with its corresponding QoS requirements (TTFT, TBT, and/or TTLT) and priority level during request submission. The hybrid prioritization policy is implemented”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited config dataclass exposes only global scheduler knobs (execution_threshold, output_len_pred, hybrid_prioritization_param) and no per-request QoS/priority fields. That is consistent with the finding that request submission lacks per-request QoS configuration, though the shown snippet is config rather than a submission script.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)(per[_-]?request|request[_-]?(qos|priority|ttft|tbt|ttlt)|qos[_-]?(ttft|tbt|ttlt|priority))` in `sarathi/config/config.py` expected absent: **confirmed** (0 hit(s)). Miss shows no per-request QoS fields in this config dataclass.
- probe `(?i)\bqos\b` in `sarathi/config/config.py` expected absent: **confirmed** (0 hit(s)). Miss shows QoS not configured here; control confirms file searched.
- what would settle it: Inspect the request-submission scripts/API for any per-request TTFT/TBT/TTLT/priority fields; if none, the finding holds.

## qoserve-F019

**脚本层无每请求优先级配置。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/config/config.py:284-311`
- paper/docs (paper, PDF p.7, text lines 26-29): “anisms. We extended the vLLM API to associate each in- ference request with its corresponding QoS requirements (TTFT, TBT, and/or TTLT) and priority level during request submission. The hybrid prioritization policy is implemented”
- paper/docs (paper, PDF p.7): “we add a priority field to each request that enables relegation decisions based on application hints such as free-tier versus premium users”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited config exposes only global scheduler parameters (execution_threshold, output_len_pred, hybrid_prioritization_param) and no per-request priority or QoS fields. That matches the finding that the script/config layer lacks per-request priority configuration, despite the paper claiming a request-level priority API. The evidence is limited to config.py, but the shown dataclass is the cited layer.
- cited code found at the pinned commit: yes (1 location(s))
- probe `\bpriority\s*:\s*(int|str|float|Optional\[)` in `sarathi/config/config.py` expected absent: **confirmed** (0 hit(s)). No per-request priority field; control confirms file searched.
- probe `\b(ttft|tbt|ttlt)\s*:\s*(float|int|Optional\[)` in `sarathi/config/config.py` expected absent: **confirmed** (0 hit(s)). No per-request QoS fields; control confirms dataclass fields present.
- what would settle it: Inspect the request submission/API schema and scheduler call path for any per-request priority or QoS field.

## qoserve-F020

**实验路径同样没有独立的 D_total 完成截止。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:70-80`
- condition: `seq.tier >= 1`
- paper/docs (paper, PDF p.5): “𝐷𝑡𝑜𝑡𝑎𝑙 =𝑡𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑇𝑇𝐿𝑇 (3)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper defines D_total, but the shown code only assigns tier_deadline and derives ttft_deadline; no independent D_total completion deadline field or check appears in sequence.py or deadline_scheduler.py. This matches the claim that the experimental path lacks such a deadline.
- cited code found at the pinned commit: yes (3 location(s))
- probe `D_total|total_deadline|deadline_total` in `sarathi/core/datatypes/sequence.py` expected absent: **confirmed** (0 hit(s)). No D_total field; control confirms the file was searched.
- probe `D_total|total_deadline|deadline_total` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). Scheduler uses ttft_deadline, not an independent D_total deadline.
- what would settle it: A text search of the pinned code for any D_total completion-deadline field or comparison would settle whether it exists.

## qoserve-F021

**论文要求 α 同时乘 (Prefill_rem+Decode_rem)；代码把 decode 估计以固定系数 execution_threshold_batched 从期限中扣除，而非以 α 加权加入剩余工作项，且 α 不作用于 decode 项（artifact 范围：α·Decode_rem 项缺失，decode 以 execution_threshold_batched 线性扣减期限）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:88-109`
- condition: `self.scheduler_type != 'fcfs' and self.scheduler_type != 'edf' and self.scheduler_type != 'srpf' and self.drop == other.drop and seq.tier >= 1`
- paper/docs (paper, PDF p.5): “𝑃𝑖 =𝑡𝑖𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑖𝑇𝑇𝐿𝑇+𝛼∗(𝑃𝑟𝑒𝑓𝑖𝑙𝑙 𝑖𝑟𝑒𝑚+𝐷𝑒𝑐𝑜𝑑𝑒𝑖𝑟𝑒𝑚)”
- paper/docs (paper, PDF p.6, text lines 14-15): “where𝐷𝑒𝑐𝑜𝑑𝑒𝑟𝑒𝑚 indicates the time to compute all the de- code tokens. Since decode length is unknown in LLM in-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper formula adds α·(Prefill_rem+Decode_rem) to arrival+TTLT. The comparator applies hybrid_prioritization_param only to remaining prompt tokens, with no decode term. The scheduler instead subtracts a decode estimate from tier_deadline using fixed execution_threshold_batched, not α. Thus the artifact lacks the α·Decode_rem term and uses a linear fixed-coefficient deadline deduction.
- cited code found at the pinned commit: yes (3 location(s))
- probe `hybrid_prioritization_param \* self_remaining_tokens` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Shows α is applied only to remaining prompt tokens.
- probe `execution_threshold_batched` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (5 hit(s)). Shows decode estimate is deducted using a fixed coefficient.
- probe `(?i)decode.*hybrid_prioritization_param|hybrid_prioritization_param.*decode` in `sarathi/core/datatypes/sequence.py` expected absent: **confirmed** (0 hit(s)). No α-weighted decode term appears in the comparator.
- what would settle it: Inspect or run the scheduler with known prefill/decode remaining tokens and α to verify whether priority uses α·Decode_rem or only a fixed execution_threshold_batched deduction.

## qoserve-F022

**论文要求检查“已违反 或 将违反”TTFT/TTLT；代码仅做 TTFT 前瞻（now+service_time>deadline），且仅对 drop==0 且未分配内存的请求生效，无 TTLT 维度。（artifact 范围：仅 TTFT 前瞻，缺 TTLT 与显式“已违反”判定。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- paper/docs (paper, PDF p.4): “The violation checker module validates that the chosen request has not already violated (or will not violate) its QoS targets in the current iteration”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown scheduler code checks only TTFT via now + service_time_required > arrival_time + ttft_deadline, and only when drop == 0 and mem_allocated == False. No TTLT deadline or explicit already-violated check appears. The sequence fields include ttft_deadline but no TTLT field. This matches the finding that the artifact implements only TTFT lookahead and lacks TTLT and explicit already-violated validation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)ttlt|ttl_deadline|ttl_target` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **refuted** (1 hit(s)). No TTLT check in scheduler; TTFT deadline is present.
- probe `(?i)ttlt|ttl_deadline|ttl_target` in `sarathi/core/datatypes/sequence.py` expected absent: **refuted** (1 hit(s)). Sequence has TTFT deadline but no TTLT field.
- probe `already.*violat|violat.*already|has_violated|is_violated` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No explicit already-violated check in scheduler.
- what would settle it: A unit test constructing a request with a TTLT deadline and checking whether the scheduler validates or drops it would settle whether TTLT is enforced.

## qoserve-F023

**论文要求移入独立 relegated 队列；代码仅设 drop 标志并放回原 prefill 队列，无 relegated 队列结构，且 drop 请求仍可被再次选中调度。（artifact 范围：。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- paper/docs (paper, PDF p.6): “if a request has already violated its TTFT / TTLT deadline, or is about to violate it in the current iteration, then QoServe de-prioritizes this request into a relegated queue”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The code confirms the finding: when a request is about to miss its TTFT deadline, it increments seq.drop and pushes the same sequence back into self._prefill_queue. There is no separate relegated queue. The __lt__ method only orders dropped requests after non-dropped ones, so dropped requests remain in the prefill heap and can still be selected later.
- cited code found at the pinned commit: yes (2 location(s))
- probe `relegated` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No relegated queue name appears in scheduler code.
- probe `seq\.drop \+= 1` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (1 hit(s)). Drop flag is set instead of moving request.
- probe `heappush\(self\._prefill_queue, seq\)` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (2 hit(s)). Dropped request is reinserted into original prefill queue.
- probe `if self\.drop != other\.drop` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Drop flag only affects ordering, not queue membership.
- what would settle it: A code inspection or test showing whether dropped requests are placed in a distinct queue and excluded from normal prefill scheduling would settle it.

## qoserve-F024

**When self.scheduler_type == 'fcfs': `Sequence.__lt__` dispatches on this per-object attribute: 'fcfs' orders by arrival_time, 'edf' by ttft_deadline+arrival_time, 'srpf' by remaining prompt tokens, and anything else falls through to the hybrid-prioritization deadline. The attribute is hard-coded to 'fcfs' in the constructor, so unless some other code overwrites it after construction, the priori...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/datatypes/sequence.py:80` in `sarathi/core/datatypes/sequence.py::Sequence.__init__`
- condition: `self.scheduler_type == 'fcfs'`
- code snippet (`sarathi/core/datatypes/sequence.py:80`): `self.scheduler_type = 'fcfs'`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown line confirms only that scheduler_type is initialized to 'fcfs' in the constructor. It does not show Sequence.__lt__, the dispatch branches for 'edf'/'srpf', or whether any later code overwrites scheduler_type. Thus the finding's behavioral claim is not established by the displayed evidence alone.
- cited code found at the pinned commit: yes (1 location(s))
- probe `def\s+__lt__\s*\(` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Shows whether Sequence defines the comparison method central to the claim.
- probe `scheduler_type\s*==\s*['"]fcfs['"]` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Shows whether __lt__ actually branches on the fcfs scheduler type.
- probe `scheduler_type\s*==\s*['"](?:edf|srpf)['"]|ttft_deadline|remaining_prompt_tokens` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (8 hit(s)). Shows whether edf/srpf dispatch branches or related fields exist.
- probe `self\.scheduler_type\s*=\s*['"](?!fcfs)` in `sarathi/core/datatypes/sequence.py` expected absent: **confirmed** (0 hit(s)). Checks whether any non-fcfs assignment overwrites the constructor default.
- what would settle it: Inspect Sequence.__lt__ and every assignment to scheduler_type to verify the dispatch branches and whether any code overwrites the constructor default.

## qoserve-F025

**When batch_num_tokens <= 512: The execution-time predictor switches between two hard-coded stratified linear models at a 512-token boundary, so the prefill size chosen by slack depends on which hard-coded coefficient set applies. (sarathi/core/scheduler/deadline_scheduler.py:92)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:92` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._predict_batch_time`
- condition: `batch_num_tokens <= 512`
- paper/docs (docstring, sarathi/core/scheduler/deadline_scheduler.py:60 (_predict_batch_time)): “Predict execution time using two stratified linear models: - tokens_0_512: 0 < total_tokens <= 512 - tokens_513_plus: total_tokens > 512”
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:92`): `model = tokens_0_512 if batch_num_tokens <= 512 else tokens_513_plus`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The paper explicitly discloses two stratified linear execution-time models split at 512 tokens, and the pinned code line implements exactly that same boundary. Thus the claimed switch is not an undisclosed artifact difference. The extra claim that slack's prefill choice depends on the coefficient set is not directly evidenced, but the 'undisclosed' finding is contradicted.
- cited code found at the pinned commit: yes (1 location(s))
- probe `model\s*=\s*tokens_0_512\s+if\s+\(batch_num_tokens\s*<=\s*512\)\s+else\s+tokens_513_plus` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (1 hit(s)). Code implements the paper-disclosed 512-token stratified model switch.
- what would settle it: Compare the paper's stated 512-token stratified model description with the scheduler code to confirm the boundary and model selection are disclosed.

## qoserve-F026

**When not self._check_request_prompt_length(seq): Requests whose prompt length fails the check are added to ignored_seq_ids and skipped (the RuntimeError is not raised, so the loop continues). (sarathi/core/scheduler/deadline_scheduler.py:211)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:211` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `not self._check_request_prompt_length(seq)`
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:211`): `if not self._check_request_prompt_length(seq):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown evidence is only the condition at line 211. It does not show the branch body, so it cannot establish that failing requests are appended to ignored_seq_ids, skipped, or that no RuntimeError is raised. Paper evidence is also absent.
- cited code found at the pinned commit: yes (1 location(s))
- probe `ignored_seq_ids` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (3 hit(s)). Confirms the variable exists in this file, not branch behavior.
- probe `if not self\._check_request_prompt_length\(seq\):\s*\n\s*[^\n]*ignored_seq_ids` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **refuted** (0 hit(s)). Shows the failing-length branch immediately references ignored_seq_ids.
- probe `ignored_seq_ids\.(append|add)` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (1 hit(s)). Shows requests are added to ignored_seq_ids somewhere in the file.
- what would settle it: Inspect the lines immediately after 211 to see whether the branch appends to ignored_seq_ids and continues without raising RuntimeError.

## qoserve-F027

**When (seq.drop == 0) and (seq.mem_allocated == False) and ((now + service_time_required) > (seq.arrival_time + seq.ttft_deadline)): A not-yet-dropped, unallocated sequence whose estimated prefill service time would miss its ttft_deadline is dropped (drop incremented) and re-pushed to the prefill queue, skipping it this iteration. (sarathi/core/scheduler/deadline_scheduler.py:305)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:305` in `sarathi/core/scheduler/deadline_scheduler.py::DeadlineScheduler._schedule`
- condition: `(seq.drop == 0) and (seq.mem_allocated == False) and ((now + service_time_required) > (seq.arrival_time + seq.ttft_deadline))`
- paper/docs (code_comment, sarathi/core/scheduler/deadline_scheduler.py:304): “Eager Relegation: If we cannot finish the request within its deadline, we drop it and re-add to the prefill queue”
- code snippet (`sarathi/core/scheduler/deadline_scheduler.py:305`): `if seq.drop == 0 and seq.mem_allocated == False and (now + service_time_required > seq.arrival_time + seq.ttft_deadline):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The paper at line 304 explicitly describes eager relegation: dropping and re-adding a request that cannot meet its deadline. The code condition at line 305 matches that deadline-miss test. Therefore the behavior is disclosed, not undisclosed; the finding's category is contradicted, even though the code condition is consistent.
- cited code found at the pinned commit: yes (1 location(s))
- probe `now \+ service_time_required\) > \(seq\.arrival_time \+ seq\.ttft_deadline\)` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (1 hit(s)). Confirms the deadline-miss condition at line 305.
- what would settle it: A diff of the paper's eager-relegation paragraph against the if-body at line 305 would settle whether the behavior is disclosed and implemented as claimed.

## qoserve-F028

**论文要求用 Vidur 暴露的 harness 采集剖面；pinned 仓库中不存在该采集实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `chunk_size_predictor/predictor.py:1-41`
- paper/docs (paper, PDF p.7, text lines 56-59): “chunk sizes, batch sizes as well as context lengths. To collect this data, we use a lightweight harness exposed by an infer- ence simulator Vidur [3], and collect profiles for each model, hardware, and parallelism configuration of interest.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown predictor.py consumes a prebuilt master CSV and does not itself collect profiles, which is consistent with the claim. But the evidence only covers one file; it does not establish that the pinned repository as a whole lacks a Vidur-based harness. The finding overreaches beyond the shown code.
- cited code found at the pinned commit: yes (2 location(s))
- probe `Vidur|harness|collect|profil` in `chunk_size_predictor/predictor.py` expected absent: **confirmed** (0 hit(s)). Predictor file lacks Vidur/harness/collection references; control confirms search location.
- probe `make_master_csv|does not scan raw benchmark` in `chunk_size_predictor/predictor.py` expected present: **confirmed** (1 hit(s)). Shows predictor expects externally produced CSV rather than raw profiling.
- what would settle it: Search the full pinned repository tree for any Vidur harness or profiling/collection code and inspect make_master_csv.py.

## qoserve-F029

**偏斜工作负载未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig10_11.sh:103-129`
- paper/docs (paper, PDF p.12, text lines 64-66): “Workload mix. We evaluate QoServe under skewed work- load distributions: 70-15-15 (interactive dominant) and 15-15- 70 (batch-dominant) at 4.5 QPS. Table 6 presents p99 laten-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited sweep only iterates QPS values and scheduler types, passing scheduler and QPS to wrapper_exp.sh. It never passes or references the paper's 70-15-15 or 15-15-70 workload mixes. Thus the shown code does not implement the skewed workload evaluation described in the paper.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(70[-_ ]?15[-_ ]?15|15[-_ ]?15[-_ ]?70|skew|workload[ _-]?mix)` in `fig10_11.sh` expected absent: **confirmed** (0 hit(s)). Miss shows no skewed workload mix in the sweep; control confirms the file was searched.
- probe `wrapper_exp\.sh \$sched_type \$qps` in `fig10_11.sh` expected present: **confirmed** (1 hit(s)). Hit shows only scheduler type and QPS are passed to the experiment wrapper.
- what would settle it: Inspect wrapper_exp.sh and the workload generator for any workload-mix parameter, or run the sweep with a mix argument and verify it changes request composition.

## qoserve-F030

**未实现按 QoS 桶独立集群的 silo 部署**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “Sarathi-Silo (SOTA), the State-of-the-art siloed deployment where each QoS bucket is assigned an independent GPU cluster with each replica running a Sarathi scheduler”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited scripts launch a single Sarathi/DEADLINE benchmark process per run and assign one scheduler type per GPU. They contain no orchestration for independent per-QoS-bucket GPU clusters, so the paper's Sarathi-Silo baseline is not implemented in the shown code.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)(silo|qos|bucket|cluster)` in `fig10_11.sh` expected absent: **confirmed** (0 hit(s)). No silo/QoS cluster orchestration; only per-GPU scheduler sweeps.
- probe `run_gpu_sweep [0-9]+ "(fcfs|srpf|edf|deadline)"` in `fig10_11.sh` expected present: **confirmed** (4 hit(s)). Each GPU runs one scheduler type, not independent QoS-bucket clusters.
- probe `python -m sarathi\.benchmark\.main` in `fig7.sh` expected present: **confirmed** (1 hit(s)). Only a single Sarathi benchmark process is launched per run.
- what would settle it: A repository-wide search for a launcher starting separate Sarathi replicas on distinct GPU clusters per QoS bucket; finding none confirms the gap.

## qoserve-F031

**silo 基线整体缺失，无按桶 chunk 配置**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “The strictest QoS bucket with 50ms TBT deadline uses a chunk size of 256, while the other two QoS classes use a large chunk size of 2K to maximize throughput in the siloed baselines.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited fig7.sh sets one DEADLINE chunk size of 256 and a SARATHI chunk size of 384, with no per-QoS bucket 2K setting. fig10_11.sh only sweeps scheduler types. Neither script instantiates a siloed baseline with bucket-specific chunk sizes, so the shown evidence supports the claimed missing silo baseline configuration.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)silo` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No silo baseline reference; control confirms scheduler config text is present.
- probe `chunk_size\s+(2048|2K|2000)` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No 2K chunk setting; control shows chunk-size flags are searchable.
- probe `(?i)silo` in `fig10_11.sh` expected absent: **confirmed** (0 hit(s)). Sweep script lacks silo baseline; control confirms file content searched.
- probe `deadline_scheduler_config_chunk_size\s+256` in `fig7.sh` expected present: **confirmed** (1 hit(s)). Only strict-bucket chunk 256 appears, not per-bucket mapping.
- what would settle it: Search all benchmark scripts/configs for a siloed baseline path assigning chunk size 256 to the 50ms TBT bucket and 2048 to the other QoS buckets.

## qoserve-F032

**集群规模实验缺失**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “The silo baseline allocates dedicated replicas based on capacity estimation from per-replica throughput for each QoS tier: 7 replicas for Q1 and 3 each for Q2 and Q3, totaling 13 GPUs.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown scripts implement single-GPU runs (fig7.sh uses tensor/pipeline parallel size 1) and a four-GPU sweep over schedulers (fig10_11.sh uses GPU IDs 0-3). Neither contains a 13-GPU cluster-scale Az-Code 35 QPS experiment matching the paper's silo baseline. Thus the evidence supports the claim that the cluster-scale experiment is missing from the artifact.
- cited code found at the pinned commit: yes (2 location(s))
- probe `run_gpu_sweep\s+(?:[4-9]|1[0-2])\b` in `fig10_11.sh` expected absent: **confirmed** (0 hit(s)). No sweep on GPUs 4-12; only four GPUs are used.
- probe `parallel_config_(?:tensor|pipeline)_parallel_size\s+[2-9]` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). fig7 uses single-GPU parallelism, not a multi-GPU cluster configuration.
- what would settle it: Search the full repository for any 13-GPU/Az-Code cluster launch script or config; finding none would confirm the missing experiment.

## qoserve-F033

**瞬态过载工作负载未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.11): “Load in the system varies dynamically between low (QPS:2.0) and high (QPS:5) points every 15 minutes over a total of 4 hours as shown in Figure 12(a).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited scripts launch POISSON synthetic runs at a single QPS per invocation and a fixed QPS sweep; no code alternates QPS 2.0/5 every 15 minutes. Thus the paper's transient-overload workload is not implemented in the shown artifact.
- cited code found at the pinned commit: yes (2 location(s))
- probe `sleep\s+900|15\s*min|switch.*qps|qps.*switch|low.*high.*qps` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No 15-minute QPS switching in cited run script; control confirms QPS config present.
- probe `QPS_VALUES=\([^)]*\)` in `fig10_11.sh` expected present: **confirmed** (1 hit(s)). Fixed QPS sweep array exists, not dynamic low/high switching.
- what would settle it: A script or config that alternates QPS between 2.0 and 5 every 15 minutes for 4 hours would confirm implementation; its absence confirms the gap.

## qoserve-F034

**无峰谷比构造**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.11): “This pattern incorporates a 2.5× peak-to-trough ratio consistent with request rate variability documented in LLM production traces [9].”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited benchmark invocation uses a POISSON interval generator with a fixed QPS value and no time-varying rate schedule. The TRACE option only supplies request lengths. Thus the code does not construct the paper's 2.5x peak-to-trough request-rate pattern; the finding is supported.
- cited code found at the pinned commit: yes (1 location(s))
- probe `peak.?to.?trough|2\.5\s*[x×]` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No peak-to-trough ratio construction appears in the script.
- probe `interval_generator_config_type\s+'POISSON'` in `fig7.sh` expected present: **confirmed** (1 hit(s)). The request interval generator is constant-rate Poisson.
- probe `poisson_request_interval_generator_config_qps\s+\$QPS` in `fig7.sh` expected present: **confirmed** (1 hit(s)). Poisson rate is a single fixed QPS parameter.
- what would settle it: Inspect the interval generator implementation or run the benchmark with logging to verify no 2.5x time-varying rate modulation occurs.

## qoserve-F035

**集群规模实验缺失**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8, text lines 94-97): “line violations with 23% fewer GPUs. To validate QoServe’s resource efficiency, we reduce the silo allocation to match QoServe’s GPU count (6,2,2 replicas), which causes viola- tions to surge to 60.4%. An alternate 4,3,3 allocation faces”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown fig7.sh invocation sets pipeline/tensor parallel sizes to 1 and contains no silo, replica, or GPU-count allocation. The paper's 6,2,2/4,3,3 cluster-scale comparison is therefore not represented in this script. This supports the claim that the cluster-scale experiment is missing, though the full repository is not shown.
- cited code found at the pinned commit: yes (1 location(s))
- probe `silo|replica|6,2,2|4,3,3|num_gpus|gpu_count` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No cluster allocation terms; only benchmark command present.
- the claim concerns behaviour that needs a GPU, an accelerator or a real run
- what would settle it: Inspect the full artifact or run fig7.sh for any 6,2,2/4,3,3 silo allocation and compare violation rates.

## qoserve-F036

**替代分配实验缺失**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig7.sh:76-106`
- paper/docs (paper, PDF p.8): “An alternate 4,3,3 allocation faces approximately 95% Q1 violations with p99 latency of 385.36s.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown fig7.sh invocation runs a single DEADLINE benchmark with chunk sizes 256/384 and threshold parameters; it contains no alternate 4,3,3 allocation experiment. Since the paper reports a distinct 4,3,3 result, the absence in the benchmark script supports the claim that this experiment is not implemented there.
- cited code found at the pinned commit: yes (1 location(s))
- probe `4,3,3` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No 4,3,3 allocation string; control confirms the script was searched.
- probe `alternate.*allocation|allocation.*alternate` in `fig7.sh` expected absent: **confirmed** (0 hit(s)). No alternate-allocation wording; control confirms benchmark command exists.
- what would settle it: Search the full fig7.sh for any 4,3,3 or alternate-allocation invocation and run it if found.

## qoserve-F037

**论文要求固定 QPS 下离线扫描 α 0–10；artifact 脚本对 α 只给单一常量 0.016，未遍历 0–10 的 α 网格。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.7, text lines 35-37): “decode length.𝛼 is a configurable hyperparameter. For fixed- QPS runs, we perform an offline sweep of𝛼 values from 0 to 10 and select the value that minimizes SLO violations. An𝛼”
- paper/docs (paper, PDF p.7): “select the value that minimizes SLO violations”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited fig8.sh hardcodes deadline_scheduler_hybrid_prioritization_param to 0.016, and the shown sweep scripts iterate over QPS/scheduler combinations, not alpha. No evidence shows an offline alpha sweep from 0 to 10. This matches the claimed gap.
- cited code found at the pinned commit: yes (4 location(s))
- probe `deadline_scheduler_hybrid_prioritization_param\s+0\.016` in `fig8.sh` expected present: **confirmed** (1 hit(s)). Confirms alpha/hybrid parameter is fixed to 0.016 in the run command.
- probe `(?i)for\s+\w+\s+in\s+.*alpha|alpha_values|alpha\s*=` in `fig8.sh` expected absent: **confirmed** (0 hit(s)). Shows no alpha loop in fig8.sh despite loops being present.
- probe `(?i)alpha|hybrid_prioritization_param` in `run_all.sh` expected absent: **confirmed** (0 hit(s)). Shows run_all.sh sweeps QPS, not alpha.
- what would settle it: Search all artifact scripts for any alpha or hybrid_prioritization_param sweep over 0–10; finding only 0.016 would confirm the claim.

## qoserve-F038

**论文称固定 QPS 采用 8 ms/token；artifact 固定 QPS 运行脚本使用 16 ms/token，与论文所选值不符。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- condition: `hybrid_prioritization_param == 0.016`
- paper/docs (paper, PDF p.7, text lines 35-39): “decode length.𝛼 is a configurable hyperparameter. For fixed- QPS runs, we perform an offline sweep of𝛼 values from 0 to 10 and select the value that minimizes SLO violations. An𝛼 of 8 ms/token provided the best trade-off, reducing violations without affecting tail latency. For variable-QPS, we empl…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states fixed-QPS runs selected alpha = 8 ms/token. The pinned fig8.sh fixed-QPS script passes --deadline_scheduler_hybrid_prioritization_param 0.016, i.e. 16 ms/token if the parameter is in seconds, while config.py defaults to 0.008. Thus the artifact's fixed-QPS value differs from the paper's stated 8 ms/token.
- cited code found at the pinned commit: yes (2 location(s))
- probe `hybrid_prioritization_param\s+0\.016` in `fig8.sh` expected present: **confirmed** (1 hit(s)). Shows fixed-QPS script sets the parameter to 0.016, not 0.008.
- probe `default\s*=\s*0\.008` in `sarathi/config/config.py` expected present: **confirmed** (1 hit(s)). Shows the code default is 0.008, matching 8 ms/token.
- what would settle it: Inspect the scheduler's unit conversion for hybrid_prioritization_param and verify whether 0.016 seconds equals 16 ms/token.

## qoserve-F039

**论文要求低负载 α=1 ms/token；artifact 无该取值或负载分段。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.7, text lines 39-40): “without affecting tail latency. For variable-QPS, we employ load-adaptive tuning. At low loads, we set𝛼 = 1 ms/token”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited fig8.sh sets a fixed hybrid_prioritization_param of 0.016 and shows no alpha=1 ms/token or low-load segmentation. The paper's load-adaptive low-load setting is therefore not implemented in the shown artifact code. The evidence directly supports the claimed gap.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)alpha|𝛼|load.?adaptive|adaptive` in `fig8.sh` expected absent: **confirmed** (0 hit(s)). No alpha/load-adaptive setting in script; control confirms file searched.
- probe `hybrid_prioritization_param\s+0\.016` in `fig8.sh` expected present: **confirmed** (1 hit(s)). Fixed hybrid prioritization parameter 0.016, not load-dependent alpha.
- what would settle it: Search the full artifact for any alpha or load-adaptive branch and verify whether fig8.sh ever varies the parameter by QPS.

## qoserve-F040

**组件消融未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.12): “we tag all requests as important and evaluate three design elements—dynamic chunking, hybrid prioritization, and eager relegation—starting with the Sarathi-EDF baseline.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The cited fig8.sh explicitly includes a scheduler type 'deadline_no_dynamic_chunking' in its queue arrays, so at least the dynamic-chunking component ablation is implemented. The blanket claim that component ablation is not implemented is therefore not supported by the shown code. The shown lines do not establish whether hybrid-prioritization and eager-relegation ablations exist, but they refute total absence.
- cited code found at the pinned commit: yes (2 location(s))
- probe `deadline_no_dynamic_chunking` in `fig8.sh` expected present: **confirmed** (4 hit(s)). A no-dynamic-chunking ablation is present in the script.
- what would settle it: Inspect the scheduler code and script for toggles disabling each of the three design elements and run those configurations.

## qoserve-F041

**消融表汇总未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.12): “Config Optimal Load High load (QPS=6)QPS % gain % viol % impr.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown fig8.sh range only invokes sarathi.benchmark.main for a single configuration and redirects output to a log. It contains no visible step that reads per-run metrics or aggregates QPS/gain/violation/improvement across configurations, so the paper's ablation summary table is not produced by this code.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)(groupby|pivot_table|DataFrame|to_csv|aggregate|summary_table|latex|markdown)` in `fig8.sh` expected absent: **confirmed** (0 hit(s)). No aggregation logic in script; only benchmark launch.
- what would settle it: Run the script and check whether any generated file contains the paper's aggregated QPS/gain/violation/improvement table, or grep the full script for aggregation code.

## qoserve-F042

**alpha 敏感性实验未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `fig8.sh:37-69`
- paper/docs (paper, PDF p.12, text lines 51-54): “To further illustrate the impact of hybrid prioritization, Figure 14 plots the median latency and percentage of dead- line violations as we vary system load across three different values of 𝛼, our hybrid prioritization parameter. As 𝛼 in-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper describes varying alpha across three values for Figure 14, but the cited benchmark script passes a single hardcoded hybrid_prioritization_param value (0.016). No loop or variable sweep over alpha is shown, so the alpha sensitivity experiment is not implemented in this code.
- cited code found at the pinned commit: yes (1 location(s))
- probe `hybrid_prioritization_param\s+0\.016` in `fig8.sh` expected present: **confirmed** (1 hit(s)). Shows alpha is hardcoded to one value, not swept.
- probe `hybrid_prioritization_param[^\n]*\$` in `fig8.sh` expected absent: **confirmed** (0 hit(s)). Shows no variable alpha parameter is passed.
- what would settle it: Search all benchmark scripts for a loop or multiple hybrid_prioritization_param values, or run the experiment with three alpha values.

## qoserve-F043

**优先级标注未实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `paper_plot_scripts/fig_10_11.py:19-37`
- paper/docs (paper, PDF p.11): “we mark a random set of 20% of requests in each QoS bucket as low priority, based on application hints. The remaining 80% of requests in each bucket are marked as high priority or Important.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited code only defines SLO thresholds, scheme mappings, and QPS sweep launches. It contains no per-request priority assignment or read, so the paper's 20%/80% low/high priority marking is not implemented in the shown path. The Step 4 note confirms benchmark/plot scripts never assign or read priority labels.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)(priority|low_priority|high_priority|important)` in `paper_plot_scripts/fig_10_11.py` expected absent: **refuted** (1 hit(s)). No priority labels in plot script; control confirms searched file.
- probe `(?i)(priority|low_priority|high_priority|important)` in `fig10_11.sh` expected absent: **confirmed** (0 hit(s)). No priority setup in sweep script; control confirms searched file.
- what would settle it: Search the full scheduler and request-generation code for any assignment or reading of per-request low/high priority labels and verify whether 20/80 random marking exists.

## qoserve-F044

**未实现多副本 round-robin 分发**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `run_exp.sh:1-27`
- paper/docs (paper, PDF p.8): “Both deployments use round-robin load balancing across replicas.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited launch script configures pipeline_parallel_size=1 and tensor_parallel_size=1, and the only replica_resource_mapping line is commented out. It contains no round-robin or load-balancing logic. This supports that the cited artifact run does not implement multi-replica round-robin distribution, though it does not exhaustively prove absence elsewhere in the repository.
- cited code found at the pinned commit: yes (1 location(s))
- probe `^[^#\n]*replica_resource_mapping` in `run_exp.sh` expected absent: **confirmed** (0 hit(s)). Active replica mapping is absent; only a commented line exists.
- probe `parallel_config_(pipeline|tensor)_parallel_size\s+1` in `run_exp.sh` expected present: **confirmed** (2 hit(s)). Pipeline and tensor parallel sizes are set to one replica.
- probe `round.?robin|load.?balanc` in `run_exp.sh` expected absent: **confirmed** (0 hit(s)). No round-robin or load-balancing logic appears in the launch script.
- what would settle it: Inspect the benchmark entrypoint and scheduler for replica selection/round-robin code, or run with multiple replicas and observe request distribution.

## qoserve-F045

**脚本层同样无按应用解码历史。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/config/config.py:284-311`
- paper/docs (paper, PDF p.7, text lines 32-35): “factor𝛼 configurable as a deployment parameter. For non- interactive requests, we maintain a running history of token generation patterns per application to estimate the expected decode length.𝛼 is a configurable hyperparameter. For fixed-”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited config exposes only a fixed output_len_pred default (15) and no per-application decode-history field or tracking. This matches the finding that the script/config layer lacks per-application decode-history estimation, leaving the paper's running-history mechanism unimplemented in the shown code.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)history|per[_-]?application|application.*(decode|output)|decode.*application` in `sarathi/config/config.py` expected absent: **confirmed** (0 hit(s)). No per-application decode-history tracking appears in this config file.
- probe `output_len_pred` in `sarathi/config/config.py` expected present: **confirmed** (1 hit(s)). Only a fixed predicted output length is configured.
- what would settle it: Search the scheduler and request-handling code for any per-application decode-length history and verify whether output_len_pred is ever updated from it.

## qoserve-F046

**论文要求优先级驱动的抢占；对齐 artifact 调度路径不执行抢占。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:184-354`
- condition: `len(self.running) > 0 and len(self.waiting) > 0 and self.waiting[0].arrival_time <= now and self._sorting_key(self.waiting[0], now) < self._sorting_key(self.running[0], now)`
- paper/docs (paper, PDF p.6): “we preempt a request to accommodate another with a higher priority only if”
- paper/docs (paper, PDF p.6): “preempting that request for an iteration does not lead to deadline violation”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The deadline scheduler's _schedule path explicitly comments 'No pre-emption support' and uses can_append_slot assertions rather than calling _preempt. Preemption code exists in base_scheduler and sarathi_scheduler, but the shown deadline scheduling path does not execute it, matching the finding.
- cited code found at the pinned commit: yes (5 location(s))
- probe `self\._preempt\(` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No preemption call in deadline scheduler; control confirms file searched.
- probe `No pre-emption support` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (1 hit(s)). Explicit comment states deadline path lacks preemption support.
- probe `can_append_slot` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (2 hit(s)). Deadline path checks slot append instead of preempting victims.
- what would settle it: Run the deadline scheduler with KV-cache pressure and a higher-priority arrival, then verify whether any running request is preempted.

## qoserve-F047

**缺少 prefill 队列抢占资格判定。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:184-354`
- condition: `seq.mem_allocated == True`
- paper/docs (paper, PDF p.6): “(1) the in-flight request is in the prefill queue”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown scheduler has no preemption eligibility check tied to the prefill queue. It even comments 'No pre-emption support', and preempted_seq_ids is initialized but never appended to. The prefill loop only handles deadline dropping and scheduling, not checking whether an in-flight request is in the prefill queue before preemption.
- cited code found at the pinned commit: yes (3 location(s))
- probe `preempted_seq_ids\.append` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No preemption is recorded; variable only initialized.
- probe `preempt[^\n]*prefill|prefill[^\n]*preempt` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No line links preemption with the prefill queue.
- probe `prefill_queue[^\n]*(preempt|evict)|(preempt|evict)[^\n]*prefill_queue` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No preemption/eviction check on prefill queue.
- what would settle it: A unit test that triggers memory pressure with a prefill-queued request and checks whether it is preempted would settle it.

## qoserve-F048

**论文所述避免队头阻塞的抢占手段在 DeadlineScheduler 中不存在。（artifact 范围：。）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:184-354`
- condition: `len(self.running) > 0 and len(self._prefill_queue) > 0`
- paper/docs (paper, PDF p.6): “is a desirable capability as it avoids head-of-line blocking of small interactive requests behind long batch requests”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown DeadlineScheduler code explicitly comments “No pre-emption support” at line 252. Its scheduling logic sorts/runs decodes and prefills, and uses eager relegation to drop/re-add prefills, but shows no mechanism to preempt a running long batch to avoid head-of-line blocking. This supports the finding that the paper-described preemption capability is absent.
- cited code found at the pinned commit: yes (4 location(s))
- probe `No pre-emption support` in `sarathi/core/scheduler/deadline_scheduler.py` expected present: **confirmed** (1 hit(s)). Explicit comment states the scheduler lacks preemption support.
- probe `def _preempt|preempted_seq_ids\.append|_preempt\(` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No preemption routine or append; control confirms file searched.
- what would settle it: A code search for any preemption routine/call in DeadlineScheduler, plus a mixed long/short scheduling trace, would settle whether short requests can preempt long ones.

## qoserve-F049

**论文要求按优先级抢占已部分 prefill 的在途请求；代码无任何抢占触发或调用，仅通过堆排序选择未开始的请求**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- paper/docs (paper, PDF p.6): “Note that our hybrid prioritization scheduling can preempt an in-flight request for which a few prefill chunks have already been processed to instead service a new request with strict QoS target (see eq 4).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown deadline scheduler loop only pops from the prefill heap, chunks/drops requests, allocates memory, and appends to running. It contains no call to _preempt and no logic that frees or moves an in-flight partially prefilled request. The base scheduler defines _preempt, but the evidence does not show it being triggered. This matches the finding that preemption is not implemented in the scheduling path.
- cited code found at the pinned commit: yes (3 location(s))
- probe `self\._preempt\s*\(` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No preemption call in deadline scheduler; control confirms schedule method present.
- probe `preempted_seq_ids\s*\.append` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No preempted sequence recorded; control confirms variable declared.
- probe `self\._preempt\s*\(` in `sarathi/core/scheduler/base_scheduler.py` expected absent: **confirmed** (0 hit(s)). Preempt helper defined but not invoked in base scheduler; control confirms definition.
- what would settle it: Search the whole repository for calls to _preempt and run a scheduling trace where a strict-QoS request arrives during partial prefill to see whether the in-flight request is preempted.

## qoserve-F050

**论文要求按优先级分层、低优先级耗尽后才降级高优先级；代码对所有请求一视同仁按截止时间降级，无分层门控。（artifact 范围：。）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sarathi/core/scheduler/deadline_scheduler.py:296-333`
- condition: `self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking'`
- paper/docs (paper, PDF p.6): “Only when there are no more low-priority requests, QoServe proactively relegates high-priority requests that have violated their deadlines to prevent cascading deadline violations.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown scheduler loop applies eager relegation based solely on deadline slack and drop count; it never checks seq.priority or seq.tier before relegating. Sequence initializes priority to a constant 1 and assigns tiers randomly, but the scheduler snippet has no low-priority-exhaustion gate. Thus the evidence supports the claim that this path treats requests uniformly by deadline.
- cited code found at the pinned commit: yes (2 location(s))
- probe `seq\.priority` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). Scheduler never reads request priority; control shows drop logic present.
- probe `seq\.tier` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **refuted** (3 hit(s)). Scheduler never consults tier; control shows deadline field used.
- probe `TIER_DEADLINES` in `sarathi/core/scheduler/deadline_scheduler.py` expected absent: **confirmed** (0 hit(s)). No tier-deadline gating in scheduler; control shows throughput logic present.
- probe `self\.priority\s*=\s*1` in `sarathi/core/datatypes/sequence.py` expected present: **confirmed** (1 hit(s)). Priority is initialized to a constant, not differentiated per request.
- what would settle it: A unit test with mixed tiers and an exhausted low-priority queue would show whether high-priority requests are relegated only after low-priority exhaustion.

