# Limitations report: FlexPosit: Tunable Fractional Precision for LLM Inference Accelerators

- artifact: `flexposit` (MICRO 2026), repository https://github.com/hplp/FlexPosit at `e42a2191a7`
- input: `results/step4/flexposit/limitations_for_tests.json` (sha256 `90fcaf23c279`), 41 Findings
- generated: 2026-11-18T11:19:37+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
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
| Findings | 41 |
| tested | 12 |
| not tested | 29 |
| verdicts | inconclusive 4, yes 8 |
| levels | L1 7, L2 1, invalid 4 |
| analysis only (not tests) | A0 7, A1 3, A2 19 |
| not tested, by reason | `no_code_location` 19, `outcome_unsupported` 10 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [flexposit-F001](#flexposit-f001) | undisclosed | reject | `src/flexposit/api.py:120-121` | **inconclusive** / invalid (uncalibrated) |
| [flexposit-F002](#flexposit-f002) | undisclosed | reject | `src/flexposit/api.py:189` | **yes** / L1 (uncalibrated) |
| [flexposit-F003](#flexposit-f003) | undisclosed | reject | `src/flexposit/export.py:40` | **yes** / L1 (uncalibrated) |
| [flexposit-F004](#flexposit-f004) | undisclosed | reject | `src/flexposit/export.py:135` | **yes** / L2 (uncalibrated) |
| [flexposit-F005](#flexposit-f005) | undisclosed | reject | `src/flexposit/formats.py:39` | **yes** / L1 (uncalibrated) |
| [flexposit-F006](#flexposit-f006) | undisclosed | reject | `src/flexposit/formats.py:103` | **inconclusive** / invalid (uncalibrated) |
| [flexposit-F007](#flexposit-f007) | undisclosed | reject | `src/flexposit/formats.py:156` | **inconclusive** / invalid (uncalibrated) |
| [flexposit-F008](#flexposit-f008) | undisclosed | path_change | `src/flexposit/mpq/channel_window.py:283` | **yes** / L1 (uncalibrated) |
| [flexposit-F009](#flexposit-f009) | undisclosed | path_change | `src/flexposit/mpq/channel_window.py:571` | **yes** / L1 (uncalibrated) |
| [flexposit-F010](#flexposit-f010) | impl_deviates | other | `hardware/README.md:3-9` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F011](#flexposit-f011) | impl_deviates | other | `hardware/README.md:3-9` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F012](#flexposit-f012) | impl_deviates | other | `hardware/README.md:3-9` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F013](#flexposit-f013) | impl_deviates | other | `hardware/rtl/fp8_pe_mac_stream.v:395-423` | not tested: `no_code_location`, analysis A0/contradicts |
| [flexposit-F014](#flexposit-f014) | impl_deviates | other | `hardware/rtl/fp8_pe_mac_stream.v:452-490` | not tested: `no_code_location`, analysis A0/supports |
| [flexposit-F015](#flexposit-f015) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:136-183` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F016](#flexposit-f016) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:218-281` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F017](#flexposit-f017) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:218-279` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F018](#flexposit-f018) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:339-384` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F019](#flexposit-f019) | impl_deviates | other | `hardware/rtl/systolic_efficient.v:198-240` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F020](#flexposit-f020) | impl_deviates | other | `hardware/rtl/systolic_efficient.v:242-330` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F021](#flexposit-f021) | impl_deviates | other | `hardware/rtl/systolic_efficient.v:411-512` | not tested: `no_code_location`, analysis A0/supports |
| [flexposit-F022](#flexposit-f022) | impl_deviates | other | `scripts/regen_sensitivity_ppl.sh:8-33` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F023](#flexposit-f023) | impl_deviates | other | `src/flexposit/export.py:105-141` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F024](#flexposit-f024) | impl_deviates | other | `src/flexposit/sensitivity/ppl_probe.py:72-75` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F025](#flexposit-f025) | undisclosed | other | `src/flexposit/api.py:149` | not tested: `outcome_unsupported`, analysis A0/supports |
| [flexposit-F026](#flexposit-f026) | undisclosed | other | `src/flexposit/api.py:153` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexposit-F027](#flexposit-f027) | docs_only | path_change | `src/flexposit/api.py:181` | **yes** / L1 (uncalibrated) |
| [flexposit-F028](#flexposit-f028) | docs_only | reject | `src/flexposit/api.py:183-186` | **inconclusive** / invalid (uncalibrated) |
| [flexposit-F029](#flexposit-f029) | docs_only | other | `src/flexposit/core.py:35` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexposit-F030](#flexposit-f030) | undisclosed | other | `src/flexposit/core.py:37` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexposit-F031](#flexposit-f031) | docs_only | reject | `src/flexposit/export.py:131` | **yes** / L1 (uncalibrated) |
| [flexposit-F032](#flexposit-f032) | docs_only | other | `src/flexposit/formats.py:29` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexposit-F033](#flexposit-f033) | undisclosed | other | `src/flexposit/mpq/channel_window.py:136` | not tested: `outcome_unsupported`, analysis A2/supports |
| [flexposit-F034](#flexposit-f034) | undisclosed | other | `src/flexposit/mpq/channel_window.py:161` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [flexposit-F035](#flexposit-f035) | undisclosed | other | `src/flexposit/mpq/channel_window.py:205` | not tested: `outcome_unsupported`, analysis A0/supports |
| [flexposit-F036](#flexposit-f036) | undisclosed | other | `src/flexposit/mpq/channel_window.py:208` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [flexposit-F037](#flexposit-f037) | undisclosed | other | `src/flexposit/mpq/channel_window.py:256` | not tested: `outcome_unsupported`, analysis A0/supports |
| [flexposit-F038](#flexposit-f038) | not_implemented | other | `hardware/rtl/fp8_pe_mac_stream.v:497-621` | not tested: `no_code_location`, analysis A2/supports |
| [flexposit-F039](#flexposit-f039) | not_implemented | other | `hardware/rtl/systolic_efficient.v:198-240` | not tested: `no_code_location`, analysis A1/unclear |
| [flexposit-F040](#flexposit-f040) | not_implemented | other | `scripts/regen_sensitivity_ppl.sh:8-33` | not tested: `no_code_location`, analysis A0/supports |
| [flexposit-F041](#flexposit-f041) | not_implemented | other | `src/flexposit/sensitivity/ppl_probe.py:72-75` | not tested: `no_code_location`, analysis A2/supports |

## flexposit-F001

**When True: raise FileNotFoundError(f'No sensitivity CSV {str(name_or_path)!r}: not a file, and not one of the shipped models {shipp (src/flexposit/api.py:120)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/api.py:120-121` in `src/flexposit/api.py::sensitivity_csv`
- condition: `not (shipped.is_file())`
- code snippet (`src/flexposit/api.py:120`): `raise FileNotFoundError(f'No sensitivity CSV {str(name_or_path)!r}: not a file, and not one of the shipped models {shipped_sensitivity()}')`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect on positive input, none on negative input

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2

- trigger run: FileNotFoundError at src/flexposit/api.py:120
- contrast run: no exception at src/flexposit/api.py:120
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'sensitivity' is not an integer (value 'gpt2-large')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/flexposit/flexposit-F001/execution_report.json`

## flexposit-F002

**When state.total_windows == 0: Quantize aborts if no sensitivity rows match the model's layer names, so a mismatched sensitivity file cannot be used. (src/flexposit/api.py:189)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/api.py:189` in `src/flexposit/api.py::quantize`
- condition: `state.total_windows == 0`
- code snippet (`src/flexposit/api.py:189`): `if state.total_windows == 0:`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at src/flexposit/api.py:190
- contrast run: no exception at src/flexposit/api.py:189
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. no effect on either side: the negative input is NOT adjacent to the effect region
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (refuted): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/flexposit/flexposit-F002/execution_report.json`

## flexposit-F003

**When not torch.equal(table[pos], mag): posit_encode raises ValueError if the scaled weights are not exact Posit(nsize,es) values, so layer_codes/export_tile fail for any weight that does not land exactly on the Posit value table. (src/flexposit/export.py:40)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/export.py:40` in `src/flexposit/export.py::posit_encode`
- condition: `not torch.equal(table[pos], mag)`
- code snippet (`src/flexposit/export.py:40`): `if not torch.equal(table[pos], mag):`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at src/flexposit/export.py:41
- contrast run: no exception at src/flexposit/export.py:40
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'value' is not an integer (value 2.0)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. the official entry started first but the target line did not run inside it; reason recorded: Step 4 reports call_chain status not_found: quantize() fake-quantizes weights to exact Posit values and never calls export.lay…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexposit/flexposit-F003/execution_report.json`

## flexposit-F004

**When scale.min() < -16 or scale.max() > 15: export_tile raises ValueError when the per-column scale (-log2_scale) does not fit the RTL's signed 5-bit field, rejecting configurations whose log2_scale falls outside [-15, 16]. (src/flexposit/export.py:135)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/export.py:135` in `src/flexposit/export.py::export_tile`
- condition: `scale.min() < -16 or scale.max() > 15`
- paper/docs (paper, PDF p.5): “a compact 4 b index stores the selected per-channel scale with low metadata overhead”
- code snippet (`src/flexposit/export.py:135`): `if scale.min() < -16 or scale.max() > 15:`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: ValueError at src/flexposit/export.py:136
- contrast run: no exception at src/flexposit/export.py:135
- open doubts:
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'scales' is not an integer (value [1, 15])
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The call chain lists api.quantize as the official entry, but the pinned step-4 static analysis found no call chain from it: quantize returns a QuantState and export_tile is a sep…
- what would raise the level: D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexposit/flexposit-F004/execution_report.json`

## flexposit-F005

**When not 2 <= nsize <= 16: posit_quantize (via _check_posit) rejects nsize outside [2,16], so the tunable precision cannot exceed 16 bits. (src/flexposit/formats.py:39)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/formats.py:39` in `src/flexposit/formats.py::_check_posit`
- condition: `not 2 <= nsize <= 16`
- code snippet (`src/flexposit/formats.py:39`): `if not 2 <= nsize <= 16:`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at src/flexposit/formats.py:40
- contrast run: no exception at src/flexposit/formats.py:39
- open doubts:
  - D5 control pair differs in one factor, negative adjacent to the boundary: *refuted*. no effect on either side: the negative input is NOT adjacent to the effect region
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D5 (refuted): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/flexposit/flexposit-F005/execution_report.json`

## flexposit-F006

**When True: raise TypeError(f'posit_quantize expects a float32 tensor, got {x.dtype}') (src/flexposit/formats.py:103)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/formats.py:103` in `src/flexposit/formats.py::_posit_quantize_torch`
- condition: `x.dtype != torch.float32`
- code snippet (`src/flexposit/formats.py:103`): `raise TypeError(f'posit_quantize expects a float32 tensor, got {x.dtype}')`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect on positive input, none on negative input

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2

- trigger run: TypeError at src/flexposit/formats.py:103
- contrast run: no exception at src/flexposit/formats.py:103
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. the agent's predicate and Region.condition disagree: Region.condition itself does not fail on the negative run
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D4 oracle is specified, located, pre-registered: *residual*. oracle changed 1 time(s) after the first run
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'weight_dtype' is not an integer (value 'float32')
  - D9 result reproduces in a clean checkout: *refuted*. fresh checkout gave different canonical traces: positive, negative
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The official entry api.quantize and core.search_channels call .float() on the weights before posit_quantize, so the non-float32 guard at formats.py:103 is unreachable through the…
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D4 (residual): state the oracle as exception type + Region.location and register it before the first run
- evidence: `tests/flexposit/flexposit-F006/execution_report.json`

## flexposit-F007

**When True: raise ValueError(f'invalid rounding mode {rounding!r}') (src/flexposit/formats.py:156)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `src/flexposit/formats.py:156` in `src/flexposit/formats.py::posit_quantize`
- condition: `rounding not in ('nearest', 'stochastic')`
- code snippet (`src/flexposit/formats.py:156`): `raise ValueError(f'invalid rounding mode {rounding!r}')`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect on positive input, none on negative input

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2

- trigger run: ValueError at src/flexposit/formats.py:156
- contrast run: no exception at src/flexposit/formats.py:156
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'rounding' is not an integer (value 'nearest')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The official entry quantize() at api.py::quantize never forwards rounding; its call chain (search_channels -> posit_quantize) always uses the default rounding='nearest', so the i…
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/flexposit/flexposit-F007/execution_report.json`

## flexposit-F008

**When strategy == "random": Random strategy shuffles candidates with the caller-seeded RNG, selecting a different set of windows than the sensitivity ordering. (src/flexposit/mpq/channel_window.py:283)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:283` in `src/flexposit/mpq/channel_window.py::_order_candidates`
- condition: `strategy == "random"`
- code snippet (`src/flexposit/mpq/channel_window.py:283`): `if strategy == 'random':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at src/flexposit/mpq/channel_window.py:283
- contrast run: branch not taken at src/flexposit/mpq/channel_window.py:283 (later ValueError at src/flexposit/mpq/channel_window.py:287)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'strategy' is not an integer (value 'unknown')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The declared official entry src/flexposit/api.py::quantize cannot reach the target: its plan_windows() always sorts by sensitivity and it contains no random/sweep strategy or cal…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexposit/flexposit-F008/execution_report.json`

## flexposit-F009

**When args.downgrade: Caller flag downgrade switches Budget Mode to demote the least-sensitive windows from upgrade_bits to base_bits (reversed sort, apply_nsize from downgrade_nsize) instead of promoting the most-sensitive windows. (src/flexposit/mpq/channel_window.py:571)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:571` in `src/flexposit/mpq/channel_window.py::main`
- condition: `args.downgrade`
- code snippet (`src/flexposit/mpq/channel_window.py:571`): `if args.downgrade:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at src/flexposit/mpq/channel_window.py:571
- contrast run: branch not taken at src/flexposit/mpq/channel_window.py:571
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'downgrade' is not an integer (value False)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: Static analysis reports call_chain_status=not_found: the declared first node flexposit.api.quantize is a separate Python API implementation that never calls flexposit.mpq.channel…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexposit/flexposit-F009/execution_report.json`

## flexposit-F010

**论文要求 4 PE 共享 1 个 FP16 累加器；RTL 为每 PE 独立块浮点累加器（ACC_MANW=12, GRS=3，非 FP16 格式），无时分复用。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/README.md:3-9`
- paper/docs (paper, PDF p.7): “FlexPosit groups four PEs into a 4-way MAC cluster”
- paper/docs (paper, PDF p.7): “the four PEs within a cluster share a single FP16 accumulator time-multiplexed across lanes”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper describes a 4-PE cluster sharing one time-multiplexed FP16 accumulator. The RTL instead instantiates fp8_pe_mac_stream separately for every systolic PE, with ACC_MANW=12 and GRS=3 block-floating-point accumulator ports. The README explicitly says the test chip moves to one accumulator per PE compared with the paper RTL. This directly supports the claimed implementation deviation.
- cited code found at the pinned commit: yes (5 location(s))
- probe `fp8_pe_mac_stream\s*#\s*\(` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (1 hit(s)). Shows each PE gets its own MAC/accumulator instance, not a shared cluster accumulator.
- probe `parameter integer ACC_MANW\s*=\s*12` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Accumulator mantissa is 12-bit block-float, not FP16.
- probe `parameter integer GRS\s*=\s*3` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (2 hit(s)). Confirms block-floating-point guard/round/sticky accumulator format.
- probe `one accumulator per PE` in `hardware/README.md` expected present: **confirmed** (1 hit(s)). README states the test chip uses per-PE accumulators versus the paper RTL.
- what would settle it: Inspect the RTL hierarchy and accumulator ports to verify no shared FP16 accumulator or 4-PE time-multiplexing exists.

## flexposit-F011

**论文要求簇内 4 个 PE 各取一个不同 FP16 激活；RTL 中不同激活分布在不同行（每行一个），且激活为 FP8 而非 FP16。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/README.md:3-9`
- paper/docs (paper, PDF p.7): “while processing four distinct FP16 activations”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The README explicitly says the test chip moves to FP8 activations, and the RTL instantiates fp8_pe_mac_stream. In systolic_efficient.v, each row i receives act_in[i], and the activation propagates east via pe_act_out[i][j-1], so one activation is used per row rather than four distinct FP16 activations per cluster. This matches the claimed implementation deviation.
- cited code found at the pinned commit: yes (3 location(s))
- probe `moves to FP8 activations` in `hardware/README.md` expected present: **confirmed** (1 hit(s)). Confirms the test chip uses FP8 activations, not FP16.
- probe `act_in\[i\]` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (1 hit(s)). Shows each row receives its own activation input.
- probe `pe_act_out\[i\]\[j-1\]` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (1 hit(s)). Shows activation propagates east within a row, one per row.
- probe `module fp8_pe_mac_stream` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Confirms the PE module is an FP8 MAC datapath.
- what would settle it: Inspect the paper's cluster/PE activation mapping and the RTL row/column activation wiring to verify FP8 versus FP16 and one-per-row versus four-distinct-per-cluster.

## flexposit-F012

**论文要求 FP16 激活与全浮点域 MAC；RTL 激活为 FP8 且累加为块浮点整数尾数，非逐项浮点累加。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/README.md:3-9`
- paper/docs (paper, PDF p.7, text lines 151-155): “Processing Element.Each PE, depicted in Fig. 6(b), forms the basic compute unit within the 4-way MAC cluster, op- erating on the decoded weight terms and FP16 activations to perform multiply-accumulate entirely in the floating-point domain. Each MAC cluster contains four PEs sharing one”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper excerpt explicitly requires FP16 activations and multiply-accumulate entirely in the floating-point domain. The RTL instead instantiates an FP8 PE MAC stream with FP8 activation parameters and a pe_bfp_acc block-floating-point accumulator using an integer mantissa. The README also states the test chip moves to FP8 activations. This directly supports the claimed implementation deviation.
- cited code found at the pinned commit: yes (4 location(s))
- probe `FP8 activations` in `hardware/README.md` expected present: **confirmed** (1 hit(s)). README states test chip uses FP8 activations, unlike paper RTL.
- probe `module\s+fp8_pe_mac_stream` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). RTL module is explicitly an FP8 PE MAC stream.
- probe `module\s+pe_bfp_acc` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Accumulator module is block-floating-point, not per-item float.
- probe `ACC_MANW\s*=\s*12` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Accumulator mantissa is an integer-width parameter.
- what would settle it: Inspect the RTL datapath and accumulator implementation to verify FP8 activations and block-floating-point integer accumulation are unconditional.

## flexposit-F013

**同 local_entry：cyc2 用符号位与未右移的 A**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/fp8_pe_mac_stream.v:395-423`
- paper/docs (paper, PDF p.7): “S1 =A+ (b 0 & (A≫1))”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The code contradicts the finding. In cycle2, add_a is act_temp (the A term), while add_b is selected by data_in[DATA_WIDTH-1] and uses shifted_act. shifted_act is loaded with act_temp in cycle0 and right-shifted in cycle1, so by cycle2 it is A>>1. Thus cycle2 implements A + (b0 & (A>>1)), matching the paper, not using un-right-shifted A for the b0 term.
- cited code found at the pinned commit: yes (3 location(s))
- probe `shifted_act\s*<=\s*shifted_act\s*>>>\s*1` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (3 hit(s)). Right shift occurs before cycle2; shifted_act is A>>1.
- probe `add_b\s*=\s*data_in\[DATA_WIDTH-1\]\s*\?\s*\{\{\(ADDW-MUL_MAG_W\)\{1'b0\}\},\s*shifted_act\}` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Cycle2 b0 term selects shifted_act, not act_temp.
- what would settle it: Simulate or inspect cycle2 signals to verify shifted_act equals act_temp>>1 when add_b is selected.

## flexposit-F014

**同 local_entry**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/fp8_pe_mac_stream.v:452-490`
- condition: `cycleLast and (data_in[0] or act_is_zero)`
- paper/docs (paper, PDF p.8): “The fourth weight term, thezero flag, is latched atcyc3and remains valid for the rest of the precision window”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The paper says the zero flag is latched at cyc3 and held for the rest of the precision window. The RTL instead updates out_zero only inside the cycleLast branch, and the decoder comment calls it the final beat. For P>=6, cycleLast is later than cyc3, so the implementation deviates from the paper.
- cited code found at the pinned commit: yes (3 location(s))
- probe `if \(cycleLast\) begin[\s\S]*?out_zero <=` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **refuted** (0 hit(s)). Zero flag is latched only on cycleLast, not fixed cyc3.
- probe `out_zero\s*<=\s*data_in\[0\]\s*\|\s*act_is_zero` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Confirms zero flag source is final beat data_in.
- probe `final beat explicit zero flag` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Decoder comment states zero flag is final beat.
- probe `cycleLast` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (7 hit(s)). Decoder uses cycleLast boundary for final beat.
- what would settle it: Simulate P>=6 and check whether out_zero changes at cyc3 or only at cycleLast.

## flexposit-F015

**同 local_entry：符号 FIFO 写入在 cyc1 而非 cyc0。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:136-183`
- paper/docs (paper, PDF p.8, text lines 113-114): “markers. Atcyc0, it enters theSIGNstate and pushes the sign term into the FIFO. Atcyc1, it transitions to theREGIME”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states the sign term is pushed into the FIFO at cyc0. The RTL instead maps fifo_in0 to sign_pack only when cycle1, and the FIFO write logic stores data_in0 under cycle1&valid. At cycle0 it writes zero_pack/data_in1/data_in2. This directly supports the claimed deviation: sign FIFO write occurs at cyc1, not cyc0.
- cited code found at the pinned commit: yes (3 location(s))
- probe `cycle1\s*\?\s*sign_pack` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows sign_pack is selected for FIFO input on cycle1.
- probe `if\s*\(\s*cycle1\s*&\s*valid\s*\)` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (2 hit(s)). Shows FIFO data_in0 write is gated by cycle1.
- probe `cycle0\s*\?\s*zero_pack` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows cycle0 FIFO input is zero_pack, not sign_pack.
- what would settle it: A cycle-accurate RTL simulation showing FIFO write-enable and data_in0 on cycle0 versus cycle1 would settle the timing.

## flexposit-F016

**论文要求 cyc0 推入符号项；代码在 cyc1 写符号、cyc0 写零标志与 exp/man**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:218-281`
- paper/docs (paper, PDF p.8, text lines 113-114): “markers. Atcyc0, it enters theSIGNstate and pushes the sign term into the FIFO. Atcyc1, it transitions to theREGIME”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says the sign term is pushed into the FIFO at cycle0. The code instead selects sign_pack for FIFO input on cycle1 and zero_pack on cycle0, and the write logic stores data_in0 on cycle1 while cycle0 stores exponent/fraction data. This directly matches the claimed deviation: sign is written at cycle1, not cycle0.
- cited code found at the pinned commit: yes (3 location(s))
- probe `cycle1\s*\?\s*sign_pack` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows FIFO input selects sign on cycle1, not cycle0.
- probe `cycle0\s*\?\s*zero_pack` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows cycle0 FIFO input is zero flag, not sign.
- probe `if\s*\(cycle1\s*&\s*valid\)` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (2 hit(s)). Confirms sign data_in0 is written during cycle1.
- probe `else if\s*\(cycle0\s*&\s*re\)` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (2 hit(s)). Confirms cycle0 writes exponent/fraction, not sign.
- what would settle it: Inspect or simulate the FIFO write-enable/data mapping to verify sign_pack is enqueued on cycle1 and zero_pack on cycle0.

## flexposit-F017

**同 local_entry：以固定位宽上限而非 cycP 终止尾数收集。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:218-279`
- condition: `index >= 0 and len(fraction) >= MAX_POSIT_FRACTION_BITS`
- paper/docs (paper, PDF p.8, text lines 123-124): “MANTISSAstate, each bit is shifted into a register as it arrives untilcycP, producing the mantissa term. A zero flag is tracked”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states mantissa bits are shifted in until cycP. The RTL instead captures while man_count < MAN_WIDTH, and the model collects fraction bits only while len(fraction) < MAX_POSIT_FRACTION_BITS. Both use fixed width caps, not cycP, matching the claimed deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `man_count\s*<\s*MAN_WIDTH` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows mantissa capture stops at fixed MAN_WIDTH, not cycP.
- probe `len\(fraction\)\s*<\s*MAX_POSIT_FRACTION_BITS` in `hardware/model/flexposit_rtl_exact.py` expected present: **confirmed** (1 hit(s)). Shows fraction collection capped by MAX_POSIT_FRACTION_BITS, not cycP.
- what would settle it: Inspect or simulate the decoder to verify mantissa collection terminates on MAN_WIDTH/MAX_POSIT_FRACTION_BITS rather than a cycP signal.

## flexposit-F018

**同 local_entry：RTL 分槽写入而非一起推入。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:339-384`
- condition: `cycle0 and re`
- paper/docs (paper, PDF p.8): “At completion, the decoder pushes the exponent, mantissa, and zero flag into the per-column FIFO together, forming one decoded weight.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says the decoder pushes exponent, mantissa, and zero flag into the per-column FIFO together as one decoded weight. The RTL instead writes data_in1, data_in2, filler slots, and data_in0 in separate branches/cycles, advancing wr_ptr by precision-1. This is a slot-wise write pattern, not a single bundled push, so the finding is supported.
- cited code found at the pinned commit: yes (2 location(s))
- probe `mem\[wr_ptr\]\s*<=\s*data_in1` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows exponent written to its own FIFO slot.
- probe `mem\[\(wr_ptr\+1\) % DEPTH\]\s*<=\s*data_in2` in `hardware/rtl/posit_decode_and_queue.v` expected present: **confirmed** (1 hit(s)). Shows mantissa written separately, not bundled.
- what would settle it: A cycle-level simulation or waveform of the FIFO write port would show whether exponent, mantissa, and zero flag are enqueued in one cycle or separate cycles.

## flexposit-F019

**论文的“轮流完成、无停顿”依赖共享累加器时分复用；RTL 无共享，且存在全局 stall 背压路径。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:198-240`
- paper/docs (paper, PDF p.7): “since each bit-serial multiplication spans multiple cycles, each PE completes its accumulation in turn without stalls”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper claims PEs accumulate in turn without stalls. The RTL explicitly routes a global stall into the cycle generator, freezes cycle shift registers when stalled, and gates FIFO reads with !stall. This shows a global backpressure path, contradicting the no-stall description. The absence of a shared accumulator is not directly proven by these snippets, but the stall deviation is supported.
- cited code found at the pinned commit: yes (2 location(s))
- probe `\.stall\s*\(\s*stall\s*\)` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (3 hit(s)). Cycle generator receives global stall, contradicting no-stall claim.
- probe `rd_en\s*\(\s*active_row\[i\]\s*&&\s*!stall\s*\)` in `hardware/rtl/mm_efficient.v` expected present: **confirmed** (1 hit(s)). Activation FIFO reads are gated by global stall backpressure.
- probe `else if \(!stall\)` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (5 hit(s)). Cycle shift registers stop advancing during stall.
- what would settle it: A cycle-accurate RTL trace showing stall asserted during accumulation and freezing PE/cycle/FIFO progress would settle it.

## flexposit-F020

**论文要求簇内 4 个 PE 同周期共享同一解码权重项；RTL 中同列相邻 PE 收到同一权重项但相差 1 周期，且不存在“簇内 4 PE 同周期”结构。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:242-330`
- paper/docs (paper, PDF p.7): “Within each cluster, all PEs operate on the same decoded weight term each cycle”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The RTL decodes weights per column (`decoder_loop`) and feeds row 0 from `decoder_data_out[j]`; lower rows receive `pe_data_out[i-1][j]`, so the same column's weight moves down one PE per cycle. There is no cluster-level structure making four PEs share a decoded weight in the same cycle. This matches the claimed structural deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `begin:\s*decoder_loop` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (1 hit(s)). Shows weight decoding is instantiated per column, not per four-PE cluster.
- probe `decoder_data_out\[j\]` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (2 hit(s)). Shows column decoder output feeds the first row PE.
- probe `pe_data_out\[i-1\]\[j\]` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (1 hit(s)). Shows weight/data propagates down rows with one-PE delay.
- probe `cluster` in `hardware/rtl/systolic_efficient.v` expected absent: **confirmed** (0 hit(s)). No cluster-level sharing construct appears in this RTL file.
- what would settle it: Trace or simulate `decoder_data_out[j]` and `pe_data_out[i][j]` to verify same-column PEs receive the same weight on consecutive cycles, not simultaneously.

## flexposit-F021

**同 local_entry：写出受 out_ready 背压与一拍填充延迟约束，非无停顿。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:411-512`
- paper/docs (paper, PDF p.7): “and be written out without stalls.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The RTL explicitly gates ship-out advancement on drain_stage_ready, which depends on out_ready, so deasserted out_ready backpressures writeout. The comment also states the stage register adds one cycle of drain fill latency. Thus the implementation is not literally stall-free at the output interface, supporting the finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `drain_stage_ready\s*=\s*!drain_stage_valid\s*\|\|\s*out_ready` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (1 hit(s)). Shows output handshake depends on out_ready, allowing backpressure.
- probe `Adds one cycle of drain fill latency` in `hardware/rtl/systolic_efficient.v` expected present: **refuted** (0 hit(s)). Confirms an extra fill cycle before drain completion.
- probe `if \(drain_stage_ready\)` in `hardware/rtl/systolic_efficient.v` expected present: **confirmed** (2 hit(s)). FSM advances only when stage ready, indicating possible stalls.
- the claim concerns behaviour that needs a GPU, an accelerator or a real run
- what would settle it: Simulate or formally check the ship-out FSM with out_ready deasserted to see whether writeout stalls and incurs fill latency.

## flexposit-F022

**同 local_entry：符号与 Algorithm 2 第6行相反。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `scripts/regen_sensitivity_ppl.sh:8-33`
- paper/docs (paper, PDF p.6, text lines 10-10): “6:∆PPL(w)←P base −PPL(Mw,D)”
- paper/docs (paper, PDF p.5): “a large∆PPLindicates that additional precision provides a significant accuracy gain, whereas a small∆PPLyields only marginal improvement”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code computes delta as ppl_new - baseline_ppl and comments that negative is good, while paper Algorithm 2 defines ∆PPL = P_base - PPL(Mw,D). Thus the sign is reversed on every call; read_sensitivity_windows consumes delta_ppl unchanged. The evidence supports the impl_deviates finding.
- cited code found at the pinned commit: yes (3 location(s))
- probe `delta\s*=\s*ppl_new\s*-\s*baseline_ppl` in `src/flexposit/sensitivity/ppl_probe.py` expected present: **confirmed** (1 hit(s)). Confirms code computes upgraded minus baseline, opposite paper sign.
- probe `baseline_ppl\s*-\s*ppl_new` in `src/flexposit/sensitivity/ppl_probe.py` expected absent: **confirmed** (0 hit(s)). Shows no paper-order subtraction is used in this file.
- what would settle it: Inspect or run ppl_probe.py on any window and compare the sign of delta_ppl to P_base - PPL(Mw,D).

## flexposit-F023

**论文要求激活保持 FP16；硬件导出/仿真路径把激活转成 FP8 E4M3。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `src/flexposit/export.py:105-141`
- paper/docs (paper, PDF p.5): “only the weights are quantized while activations remain in FP16”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states activations remain FP16, but export_tile explicitly quantizes activations with fp8_e4m3_encode and array_tb.v labels act.mem as FP8 E4M3. This is an unconditional conversion in the cited export/hardware path, so the implementation deviates from the paper. The evidence is code-level, not requiring a hardware run.
- cited code found at the pinned commit: yes (2 location(s))
- probe `fp8_e4m3_encode\(` in `src/flexposit/export.py` expected present: **confirmed** (2 hit(s)). Activation encoding to FP8 is present in export path.
- probe `FP8 E4M3 activation codes` in `hardware/tb/array_tb.v` expected present: **confirmed** (1 hit(s)). Testbench documents FP8 activation input, corroborating export.
- what would settle it: Run export_tile on FP16 activations and inspect act.mem/array_tb input width to verify values are FP8 E4M3 rather than FP16.

## flexposit-F024

**论文要求窗口为阵列列数整数倍；脚本默认256（16列整数倍）但模块默认64，且无对齐校验（E4,E5,E6）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `src/flexposit/sensitivity/ppl_probe.py:72-75`
- condition: `channel_window % 16 != 0`
- paper/docs (paper, PDF p.5): “FlexPosit sets the precision granularity to an integer multiple of the number of columns in the systolic array, partitioning each layer into channel windows”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper excerpt requires channel windows to be integer multiples of the systolic-array column count. The code shows ppl_probe defaults channel_window to 64, the script defaults it to 256, and fisher.py uses channel_window directly in range() with no visible modulo, assert, or alignment validation. Thus the lack of alignment checking is supported. Note that 64 is itself a multiple of 16, so the default-64 contrast alone does not prove misalignment.
- cited code found at the pinned commit: yes (3 location(s))
- probe `--channel_window", type=int, default=64` in `src/flexposit/sensitivity/ppl_probe.py` expected present: **confirmed** (1 hit(s)). Shows module-level default channel window is 64.
- probe `CHANNEL_WINDOW=.*256` in `scripts/regen_sensitivity_ppl.sh` expected present: **confirmed** (1 hit(s)). Shows script-level default channel window is 256.
- probe `channel_window` in `src/flexposit/sensitivity/fisher.py` expected present: **confirmed** (13 hit(s)). Shows channel_window is used to build evaluation windows.
- probe `channel_window\s*%|%\s*channel_window|is_multiple|alignment|aligned|divisible` in `src/flexposit/sensitivity/fisher.py` expected absent: **confirmed** (0 hit(s)). No visible alignment/divisibility validation in window generation.
- what would settle it: Run the sensitivity probe with a non-multiple channel_window and check whether it errors or silently proceeds.

## flexposit-F025

**When r[0] not in valid_layers: Sensitivity rows for layers not present in the model are silently dropped, so the upgrade budget is computed only over matching layers. (src/flexposit/api.py:149)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/api.py:149` in `src/flexposit/api.py::plan_windows`
- condition: `r[0] not in valid_layers`
- code snippet (`src/flexposit/api.py:149`): `rows = [r for r in rows if r[0] in valid_layers]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown line explicitly filters rows to those whose first element is in valid_layers, so rows for other layers are removed without any visible warning. If these are the sensitivity rows used for the upgrade budget, the budget is indeed computed only over matching layers. The evidence directly supports the filtering claim; the budget consequence is a plausible inference from the same rows variable.
- cited code found at the pinned commit: yes (1 location(s))
- probe `rows\s*=\s*\[r for r in rows if r\[0\] in valid_layers\]` in `src/flexposit/api.py` expected present: **confirmed** (1 hit(s)). Confirms the exact filtering line exists.
- probe `valid_layers\s*=` in `src/flexposit/api.py` expected present: **refuted** (0 hit(s)). Shows valid_layers is defined in this file.
- what would settle it: Inspect the surrounding function to verify that the filtered rows are the sensitivity rows used to compute the upgrade budget and that no warning is emitted.

## flexposit-F026

**When span == 0: If upgrade_nsize equals base_nsize (span zero), the upgrade fraction silently becomes 0.0 instead of erroring, so no windows are upgraded. (src/flexposit/api.py:153)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/api.py:153` in `src/flexposit/api.py::plan_windows`
- condition: `span == 0`
- code snippet (`src/flexposit/api.py:153`): `frac = (config.bits - config.base_nsize) / span if span else 0.0`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. Line 153 directly implements a silent fallback: when span is zero, frac becomes 0.0 rather than raising. That matches the finding's core claim. The excerpt does not show that span is defined as upgrade_nsize minus base_nsize, nor that frac controls window upgrades, but the zero-span behavior itself is supported.
- cited code found at the pinned commit: yes (1 location(s))
- probe `span\s*=\s*[^\n]*upgrade_nsize[^\n]*base_nsize|span\s*=\s*[^\n]*base_nsize[^\n]*upgrade_nsize` in `src/flexposit/api.py` expected present: **confirmed** (1 hit(s)). Confirms span is computed from upgrade_nsize and base_nsize.
- probe `frac\s*=\s*\(config\.bits\s*-\s*config\.base_nsize\)\s*/\s*span\s+if\s+span\s+else\s+0\.0` in `src/flexposit/api.py` expected present: **confirmed** (1 hit(s)). Confirms zero span silently yields 0.0 fraction.
- probe `if\s+span\s*==\s*0\s*:\s*\n\s*raise` in `src/flexposit/api.py` expected absent: **confirmed** (0 hit(s)). No explicit zero-span raise; control confirms file searched.
- what would settle it: A unit test invoking the upgrade path with upgrade_nsize == base_nsize and checking whether an error is raised or any window upgrades occur would settle it.

## flexposit-F027

**When config.bits > config.base_nsize: When bits exceeds base_nsize the code requires a sensitivity ranking and runs the window-upgrade planning path; otherwise no windows are upgraded and all channels stay at base_nsize. (src/flexposit/api.py:181)**

- category `docs_only`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/api.py:181` in `src/flexposit/api.py::quantize`
- condition: `config.bits > config.base_nsize`
- paper/docs (docstring, src/flexposit/api.py:168 (quantize)): “It is required when ``config.bits`` is above ``config.base_nsize``”
- code snippet (`src/flexposit/api.py:181`): `if config.bits > config.base_nsize:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at src/flexposit/api.py:181
- contrast run: branch not taken at src/flexposit/api.py:181
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/flexposit/flexposit-F027/execution_report.json`

## flexposit-F028

**When True: raise ValueError(f"bits={config.bits} needs a sensitivity ranking to decide which channel windows get Posit{config.upgra (src/flexposit/api.py:183)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/api.py:183-186` in `src/flexposit/api.py::quantize`
- condition: `sensitivity is None`
- paper/docs (docstring, src/flexposit/api.py:168 (quantize)): “It is required when ``config.bits`` is above ``config.base_nsize``; compute one for a new model with ``python -m flexposit.sensitivity.fisher`` (fast) or ``python -m flexposit.sensitivity.ppl_probe`` (the paper's method).”
- code snippet (`src/flexposit/api.py:183`): `raise ValueError(f"bits={config.bits} needs a sensitivity ranking to decide which channel windows get Posit{config.upgrade_nsize}. Pass sensitivity='<model short name>' for a shipped model, or create`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect on positive input, none on negative input

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2, D12

- trigger run: ValueError at src/flexposit/api.py:183
- contrast run: no exception at src/flexposit/api.py:183
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'sensitivity' is not an integer (value [['proj', 0, 4, -0.5]])
  - D12 Region location and snippet match the repository: *refuted*. Region snippet differs from the repository line
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/flexposit/flexposit-F028/execution_report.json`

## flexposit-F029

**When isinstance(es, int): A scalar es disables the per-channel es search (single candidate), while a sequence enables searching es per channel; the caller's type choice changes which algorithm runs. (src/flexposit/core.py:35)**

- category `docs_only`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/core.py:35` in `src/flexposit/core.py::_es_list`
- condition: `isinstance(es, int)`
- paper/docs (docstring, src/flexposit/core.py:43 (search_channels)): “``es`` is an int, or a sequence of candidates to also search es per row.”
- paper/docs (docstring, src/flexposit/core.py:1 (<module>)): “``es`` is fixed (the paper uses es=1); passing several ``es`` values also searches es per channel.”
- code snippet (`src/flexposit/core.py:35`): `cands = [es] if isinstance(es, int) else list(es)`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The pinned code directly branches on isinstance(es, int): an int becomes a single candidate, while any non-int sequence is expanded into multiple candidates. The paper text also says a sequence enables searching es per row. Thus the caller's type choice changes whether additional es candidates are searched, matching the Finding.
- cited code found at the pinned commit: yes (1 location(s))
- probe `cands\s*=\s*\[es\]\s+if\s+isinstance\(es,\s*int\)\s+else\s+list\(es\)` in `src/flexposit/core.py` expected present: **confirmed** (1 hit(s)). Shows int versus sequence branch selecting candidate list.
- probe `sequence of candidates to also search es per row` in `src/flexposit/core.py` expected present: **confirmed** (1 hit(s)). Paper documents sequence enables additional es search.
- what would settle it: Run search_channels with es as an int and as a list, then compare whether per-channel es candidates are evaluated.

## flexposit-F030

**When all(int(e) > max_es for e in cands): If every caller-supplied es candidate exceeds nsize-1, the list is empty and the code silently falls back to es=0 instead of rejecting the configuration, so the requested es search is not performed. (src/flexposit/core.py:37)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/core.py:37` in `src/flexposit/core.py::_es_list`
- condition: `all(int(e) > max_es for e in cands)`
- code snippet (`src/flexposit/core.py:37`): `return [int(e) for e in cands if int(e) <= max_es] or [0]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target statement has no effect check yet

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line uses `or [0]`, so an empty filtered list becomes `[0]`. If every candidate exceeds `max_es`, no error is raised and `es=0` is used. This directly matches the finding's claim of silent fallback and skipped requested search. No paper evidence is recorded, but the code evidence supports the behavior.
- cited code found at the pinned commit: yes (1 location(s))
- probe `return \[int\(e\) for e in cands if int\(e\) <= max_es\] or \[0\]` in `src/flexposit/core.py` expected present: **confirmed** (1 hit(s)). Hit shows silent fallback to [0] when filter is empty.
- what would settle it: Run the function with all candidates greater than max_es and check whether it returns [0] instead of raising.

## flexposit-F031

**When len(sizes) != 1: export_tile raises ValueError when the selected output channels span more than one Posit size (nsize), so a tile cannot mix channel windows; the caller must pick columns inside a single window. (src/flexposit/export.py:131)**

- category `docs_only`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/export.py:131` in `src/flexposit/export.py::export_tile`
- condition: `len(sizes) != 1`
- paper/docs (docstring, src/flexposit/export.py:121 (export_tile)): “All ``n`` channels must share one Posit size (true inside a channel window).”
- code snippet (`src/flexposit/export.py:131`): `if len(sizes) != 1:`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at src/flexposit/export.py:132
- contrast run: no exception at src/flexposit/export.py:131
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'selection' is not an integer (value 'inside')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. the official entry started first but the target line did not run inside it; reason recorded: Step 4 reports call_chain_status=not_found: export_tile is a separate export-API function and quantize never calls it. The dri…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/flexposit/flexposit-F031/execution_report.json`

## flexposit-F032

**When _BACKEND == "qtorch": Module-level env var read at import time selects the posit/float quantizer implementation. posit_quantize (line 157-159) and float_quantize (line 170-172) then delegate to qtorch_plus instead of the pure-PyTorch `_posit_quantize_torch`/`_float_quantize_torch` used by core.search_channels, so the whole FlexPosit numerical core runs a different implementation depending ...**

- category `docs_only`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/formats.py:29` in `src/flexposit/formats.py::<module>`
- condition: `_BACKEND == "qtorch"`
- paper/docs (docstring, src/flexposit/formats.py:1 (<module>)): “Set ``FLEXPOSIT_BACKEND=qtorch`` to route both functions to qtorch_plus.”
- code snippet (`src/flexposit/formats.py:29`): `_BACKEND = os.environ.get('FLEXPOSIT_BACKEND', 'torch').lower()`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper explicitly states FLEXPOSIT_BACKEND=qtorch routes both quantizers to qtorch_plus, and the shown code reads that env var at module level. The finding's central claim—backend selection changes the numerical implementation—is therefore supported. The exact line ranges and core.search_channels usage are not shown, but they are consistent with the quoted paper.
- cited code found at the pinned commit: yes (1 location(s))
- probe `_BACKEND\s*=\s*os\.environ\.get\(\s*["']FLEXPOSIT_BACKEND["']` in `src/flexposit/formats.py` expected present: **confirmed** (1 hit(s)). Confirms module-level env var read selecting backend.
- probe `qtorch_plus` in `src/flexposit/formats.py` expected present: **confirmed** (8 hit(s)). Shows qtorch backend implementation is referenced in this file.
- probe `def\s+(posit_quantize|float_quantize)\b` in `src/flexposit/formats.py` expected present: **confirmed** (2 hit(s)). Confirms the two quantizer functions exist here.
- probe `if\s+_BACKEND\s*==\s*["']qtorch["']` in `src/flexposit/formats.py` expected present: **confirmed** (2 hit(s)). Shows functions branch to qtorch when env var set.
- what would settle it: Inspect formats.py at the pinned commit to verify posit_quantize and float_quantize branch on _BACKEND and call qtorch_plus.

## flexposit-F033

**When all(e > max_es for e in es_cands): If every caller-supplied es candidate exceeds nsize-1, the search silently falls back to es=0 instead of rejecting or reporting; the requested es_cands are ignored and a different (simpler) exponent-size variant is quantized. (src/flexposit/mpq/channel_window.py:136)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:136` in `src/flexposit/mpq/channel_window.py::_best_scale_es_for_vec`
- condition: `all(e > max_es for e in es_cands)`
- code snippet (`src/flexposit/mpq/channel_window.py:136`): `es_list = [e for e in es_cands if e <= max_es] or [0]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown line directly implements `or [0]`, so if the filtered candidate list is empty, es=0 is used. This supports the claimed silent fallback. The line alone does not prove max_es=nsize-1 or downstream quantization, and no paper evidence is recorded, so disclosure is not assessable from the evidence shown.
- cited code found at the pinned commit: yes (1 location(s))
- probe `max_es\s*=\s*[^\n]*nsize\s*-\s*1` in `src/flexposit/mpq/channel_window.py` expected present: **confirmed** (1 hit(s)). Confirms max_es equals nsize-1, the threshold in the finding.
- probe `es_list\s*=\s*\[e for e in es_cands if e <= max_es\] or \[0\]` in `src/flexposit/mpq/channel_window.py` expected present: **confirmed** (1 hit(s)). Directly shows empty filtered candidates fall back to es=0.
- probe `es_list` in `src/flexposit/mpq/channel_window.py` expected present: **confirmed** (2 hit(s)). Shows the fallback list is referenced in this file.
- what would settle it: Call the function with es_cands all greater than nsize-1 and check whether it silently quantizes with es=0 rather than raising or reporting.

## flexposit-F034

**When start >= end: A window whose clamped start is not less than its end returns the weight unchanged, so an out-of-range or empty caller window is silently a no-op. (src/flexposit/mpq/channel_window.py:161)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:161` in `src/flexposit/mpq/channel_window.py::quantize_window_cpu_from_fp32`
- condition: `start >= end`
- code snippet (`src/flexposit/mpq/channel_window.py:161`): `if start >= end:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The cited line only shows a guard `if start >= end:`. It does not show the body, so it cannot establish that the function returns the weight unchanged or that this is a silent no-op. No paper evidence is recorded. The condition is consistent with the claim but insufficient to verify it.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if start >= end:` in `src/flexposit/mpq/channel_window.py` expected present: **confirmed** (1 hit(s)). Confirms the cited guard exists in the file.
- probe `(?s)if start >= end:\s*\n\s*return\s+weight` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Shows the guard body returns the weight unchanged.
- what would settle it: Inspect the lines immediately after the guard to see whether it returns the original weight unchanged for start >= end.

## flexposit-F035

**When not (is_quant_linear(mod) and hasattr(mod, "weight") and mod.weight is not None and mod.weight.dim() == 2): Modules in the window list that are not recognized quantizable 2D linear layers are skipped, so caller-specified windows on other module types are ignored. (src/flexposit/mpq/channel_window.py:205)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:205` in `src/flexposit/mpq/channel_window.py::apply_windows_to_model`
- condition: `not (is_quant_linear(mod) and hasattr(mod, "weight") and mod.weight is not None and mod.weight.dim() == 2)`
- code snippet (`src/flexposit/mpq/channel_window.py:205`): `if not (is_quant_linear(mod) and hasattr(mod, 'weight') and (mod.weight is not None) and (mod.weight.dim() == 2)):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. Line 205 explicitly filters modules to those that are quant-linear, have a non-None weight, and have a 2D weight. Any other module in the window list fails this guard and is skipped, matching the finding. The snippet does not show the body, but the guard is the exclusion mechanism.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if not \(is_quant_linear\(mod\).*dim\(\) == 2\):\s*\n\s*continue` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Confirms the guard immediately skips non-quantizable 2D modules.
- probe `for .* in .*window` in `src/flexposit/mpq/channel_window.py` expected present: **confirmed** (2 hit(s)). Shows the function iterates over a window list of modules.
- what would settle it: Inspect the lines after 205 to verify a continue/skip and trace that the loop iterates caller-specified window modules.

## flexposit-F036

**When key not in ref_sd: A layer named in the sensitivity windows but absent from the FP32 reference state dict is skipped (with a warning), so the requested window quantization is not applied to that layer. (src/flexposit/mpq/channel_window.py:208)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:208` in `src/flexposit/mpq/channel_window.py::apply_windows_to_model`
- condition: `key not in ref_sd`
- code snippet (`src/flexposit/mpq/channel_window.py:208`): `if key not in ref_sd:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only shown evidence is the condition `if key not in ref_sd:` at line 208. It does not show that a warning is emitted or that the code skips/continues before applying window quantization. The finding may be true, but the displayed snippet is insufficient to confirm the warning-and-skip behavior.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if key not in ref_sd:[\s\S]{0,200}(?:warn|warning|print)` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Missing-key branch contains a warning or print statement.
- probe `if key not in ref_sd:[\s\S]{0,300}\bcontinue\b` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Missing-key branch continues, skipping quantization for that layer.
- probe `if key not in ref_sd:[\s\S]{0,300}\breturn\b` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Missing-key branch returns early, skipping quantization for that layer.
- what would settle it: Inspect the full block under line 208 to verify whether it warns and then continues/returns before applying the requested window quantization.

## flexposit-F037

**When dp >= 0.0 and not allow_positive: When allow_positive is False, windows with non-negative delta_ppl are filtered out of the candidate set, so the caller's allow_positive_to_meet_budget setting changes which windows the mechanism considers. (src/flexposit/mpq/channel_window.py:256)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:256` in `src/flexposit/mpq/channel_window.py::_dedup_windows`
- condition: `dp >= 0.0 and not allow_positive`
- code snippet (`src/flexposit/mpq/channel_window.py:256`): `if dp >= 0.0 and (not allow_positive):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited line directly gates non-negative dp on not allow_positive. If the following statement skips the window, as the probe checks, then setting allow_positive false excludes non-negative delta_ppl windows from consideration. The caller-specific name allow_positive_to_meet_budget is not shown, but the mechanism-level behavior described is supported by the code.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if \(dp >= 0\.0\) and \(not allow_positive\):\s*\n\s*continue` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Non-negative dp is skipped when allow_positive is false.
- probe `def [^(]*\([^)]*allow_positive` in `src/flexposit/mpq/channel_window.py` expected present: **refuted** (0 hit(s)). Function signature exposes allow_positive to callers.
- what would settle it: Run the window-selection function with allow_positive true and false on identical delta_ppl values and compare the candidate windows.

## flexposit-F038

**论文要求 4 并行 MAC/权重项；RTL 为单 PE 串行位乘。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `hardware/rtl/fp8_pe_mac_stream.v:497-621`
- paper/docs (paper, PDF p.7): “effectively performing four parallel MACs per weight and recovering the throughput loss to bit-serial execution”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited RTL module fp8_pe_mac_stream contains one pe_fp8_compute instance and takes a bit-serial decoded beat via data_in. The paper quote explicitly requires four parallel MACs per weight. Nothing in the shown code implements four parallel MAC/weight terms, so the claimed gap is supported by the evidence.
- cited code found at the pinned commit: yes (1 location(s))
- probe `pe_fp8_compute\s+#\s*\(` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (2 hit(s)). Shows the module instantiates a single compute/MAC block.
- probe `genvar|generate|for\s*\([^)]*4` in `hardware/rtl/fp8_pe_mac_stream.v` expected absent: **confirmed** (0 hit(s)). No generate/loop structure for four parallel MAC instances.
- what would settle it: Inspect or simulate the full RTL to count how many independent MAC products per weight are produced per cycle; four parallel products would contradict the finding.

## flexposit-F039

**论文的 4/P 依赖 4-PE 簇并行；RTL 每 PE 为 1/P，簇级 4/P 未被实现。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:198-240`
- condition: `precision_reg >= 4 and precision_reg <= 8`
- paper/docs (paper, PDF p.7, text lines 139-142): “to bit-serial execution. As a result, each cluster achieves an effective throughput of4/PMACs per cycle for any supported precision configuration (4≤P≤8), matching the rate of a conventional FP16 MAC at the minimum 4 b precision”
- paper/docs (paper, PDF p.7): “matching the rate of a conventional FP16 MAC at the minimum 4 b precision while retaining the precision-tunable flexibility of bit-serial computation”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown RTL contains a single-PE MAC module and a cycle generator, but no cluster-level instantiation or aggregation logic. That is consistent with the finding, yet the snippets do not prove that a 4-PE cluster or 4/P throughput path is absent. The paper claim and RTL implementation cannot be reconciled from these excerpts alone.
- cited code found at the pinned commit: yes (2 location(s))
- probe `\bcluster\b` in `hardware/rtl/systolic_efficient.v` expected absent: **confirmed** (0 hit(s)). No cluster-level construct in this file; control confirms file searched.
- probe `4\s*/\s*P|4/P|four[ _-]?PE|PE[ _-]?4` in `hardware/rtl/systolic_efficient.v` expected absent: **confirmed** (0 hit(s)). No explicit 4/P or four-PE cluster throughput expression.
- probe `module\s+fp8_pe_mac_stream` in `hardware/rtl/fp8_pe_mac_stream.v` expected present: **confirmed** (1 hit(s)). Confirms shown module is a single PE MAC, not a cluster.
- what would settle it: Inspect the top-level array/cluster RTL for four parallel PE instances or a 4/P aggregate MAC rate; simulation of cluster throughput would settle it.

## flexposit-F040

**剖析实验路径未产出论文要求的降序排序敏感度图。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `scripts/regen_sensitivity_ppl.sh:8-33`
- paper/docs (paper, PDF p.6, text lines 14-14): “10:returnSORTDESC(S,∆PPL)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The paper requires SORTDESC(S,∆PPL). The cited regeneration path invokes ppl_probe, which saves a JSON summary and CSV; the shown reader returns CSV rows in file order. No shown code performs descending sorting or emits the paper's sorted sensitivity map, so the evidence supports the not_implemented finding.
- cited code found at the pinned commit: yes (3 location(s))
- probe `SORTDESC|sort_desc|sortdesc|reverse\s*=\s*True|\bsorted\s*\(` in `src/flexposit/sensitivity/ppl_probe.py` expected absent: **confirmed** (0 hit(s)). No descending-sort implementation in probe; control confirms file searched.
- probe `\bsorted\s*\(|\bsort\s*\(|reverse\s*=\s*True` in `src/flexposit/mpq/channel_window.py` expected absent: **refuted** (5 hit(s)). Reader returns CSV rows without sorting; control confirms function present.
- what would settle it: Run scripts/regen_sensitivity_ppl.sh and inspect its outputs for a descending-sorted sensitivity map, or search the full repository for SORTDESC or reverse=True sorting.

## flexposit-F041

**论文要求 Qwen 1024；脚本与模块均无 Qwen→1024 规则（E4,E5,E6）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/sensitivity/ppl_probe.py:72-75`
- paper/docs (paper, PDF p.9): “(256 channels by default and 1024 channels for the Qwen models), aligned to an integer multiple of the number of columns in the systolic array.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code exposes only generic channel_window/override_nsize parameters: ppl_probe defaults to 64, the regen script defaults to 256, and fisher windows use the supplied channel_window. No cited code contains a model-name check mapping Qwen to 1024. Thus the paper's Qwen-specific 1024-channel rule is absent from the shown scripts/modules.
- cited code found at the pinned commit: yes (3 location(s))
- probe `(?i)qwen` in `src/flexposit/sensitivity/ppl_probe.py` expected absent: **confirmed** (0 hit(s)). Miss shows no Qwen-specific handling; control confirms file searched.
- probe `(?i)qwen` in `scripts/regen_sensitivity_ppl.sh` expected absent: **confirmed** (0 hit(s)). Miss shows script lacks Qwen→1024 rule; control confirms search location.
- probe `(?i)qwen` in `src/flexposit/sensitivity/fisher.py` expected absent: **confirmed** (0 hit(s)). Miss shows fisher windows lack Qwen-specific 1024 rule; control confirms file searched.
- what would settle it: Inspect or run the cited code with a Qwen model and verify whether channel_window becomes 1024 automatically.

