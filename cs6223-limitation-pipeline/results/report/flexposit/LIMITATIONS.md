# Limitations report: FlexPosit: Tunable Fractional Precision for LLM Inference Accelerators

- artifact: `flexposit` (MICRO 2026), repository https://github.com/hplp/FlexPosit at `e42a2191a7`
- input: `results/step4/flexposit/limitations_for_tests.json` (sha256 `90fcaf23c279`), 41 Findings
- generated: 2026-11-17T15:26:22+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
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
| Findings | 41 |
| tested | 12 |
| not tested | 29 |
| verdicts | inconclusive 4, yes 8 |
| levels | L1 7, L2 1, invalid 4 |
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
| [flexposit-F010](#flexposit-f010) | impl_deviates | other | `hardware/README.md:3-9` | not tested: `no_code_location` |
| [flexposit-F011](#flexposit-f011) | impl_deviates | other | `hardware/README.md:3-9` | not tested: `no_code_location` |
| [flexposit-F012](#flexposit-f012) | impl_deviates | other | `hardware/README.md:3-9` | not tested: `no_code_location` |
| [flexposit-F013](#flexposit-f013) | impl_deviates | other | `hardware/rtl/fp8_pe_mac_stream.v:395-423` | not tested: `no_code_location` |
| [flexposit-F014](#flexposit-f014) | impl_deviates | other | `hardware/rtl/fp8_pe_mac_stream.v:452-490` | not tested: `no_code_location` |
| [flexposit-F015](#flexposit-f015) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:136-183` | not tested: `no_code_location` |
| [flexposit-F016](#flexposit-f016) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:218-281` | not tested: `no_code_location` |
| [flexposit-F017](#flexposit-f017) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:218-279` | not tested: `no_code_location` |
| [flexposit-F018](#flexposit-f018) | impl_deviates | other | `hardware/rtl/posit_decode_and_queue.v:339-384` | not tested: `no_code_location` |
| [flexposit-F019](#flexposit-f019) | impl_deviates | other | `hardware/rtl/systolic_efficient.v:198-240` | not tested: `no_code_location` |
| [flexposit-F020](#flexposit-f020) | impl_deviates | other | `hardware/rtl/systolic_efficient.v:242-330` | not tested: `no_code_location` |
| [flexposit-F021](#flexposit-f021) | impl_deviates | other | `hardware/rtl/systolic_efficient.v:411-512` | not tested: `no_code_location` |
| [flexposit-F022](#flexposit-f022) | impl_deviates | other | `scripts/regen_sensitivity_ppl.sh:8-33` | not tested: `no_code_location` |
| [flexposit-F023](#flexposit-f023) | impl_deviates | other | `src/flexposit/export.py:105-141` | not tested: `no_code_location` |
| [flexposit-F024](#flexposit-f024) | impl_deviates | other | `src/flexposit/sensitivity/ppl_probe.py:72-75` | not tested: `no_code_location` |
| [flexposit-F025](#flexposit-f025) | undisclosed | other | `src/flexposit/api.py:149` | not tested: `outcome_unsupported` |
| [flexposit-F026](#flexposit-f026) | undisclosed | other | `src/flexposit/api.py:153` | not tested: `outcome_unsupported` |
| [flexposit-F027](#flexposit-f027) | docs_only | path_change | `src/flexposit/api.py:181` | **yes** / L1 (uncalibrated) |
| [flexposit-F028](#flexposit-f028) | docs_only | reject | `src/flexposit/api.py:183-186` | **inconclusive** / invalid (uncalibrated) |
| [flexposit-F029](#flexposit-f029) | docs_only | other | `src/flexposit/core.py:35` | not tested: `outcome_unsupported` |
| [flexposit-F030](#flexposit-f030) | undisclosed | other | `src/flexposit/core.py:37` | not tested: `outcome_unsupported` |
| [flexposit-F031](#flexposit-f031) | docs_only | reject | `src/flexposit/export.py:131` | **yes** / L1 (uncalibrated) |
| [flexposit-F032](#flexposit-f032) | docs_only | other | `src/flexposit/formats.py:29` | not tested: `outcome_unsupported` |
| [flexposit-F033](#flexposit-f033) | undisclosed | other | `src/flexposit/mpq/channel_window.py:136` | not tested: `outcome_unsupported` |
| [flexposit-F034](#flexposit-f034) | undisclosed | other | `src/flexposit/mpq/channel_window.py:161` | not tested: `outcome_unsupported` |
| [flexposit-F035](#flexposit-f035) | undisclosed | other | `src/flexposit/mpq/channel_window.py:205` | not tested: `outcome_unsupported` |
| [flexposit-F036](#flexposit-f036) | undisclosed | other | `src/flexposit/mpq/channel_window.py:208` | not tested: `outcome_unsupported` |
| [flexposit-F037](#flexposit-f037) | undisclosed | other | `src/flexposit/mpq/channel_window.py:256` | not tested: `outcome_unsupported` |
| [flexposit-F038](#flexposit-f038) | not_implemented | other | `hardware/rtl/fp8_pe_mac_stream.v:497-621` | not tested: `no_code_location` |
| [flexposit-F039](#flexposit-f039) | not_implemented | other | `hardware/rtl/systolic_efficient.v:198-240` | not tested: `no_code_location` |
| [flexposit-F040](#flexposit-f040) | not_implemented | other | `scripts/regen_sensitivity_ppl.sh:8-33` | not tested: `no_code_location` |
| [flexposit-F041](#flexposit-f041) | not_implemented | other | `src/flexposit/sensitivity/ppl_probe.py:72-75` | not tested: `no_code_location` |

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

## flexposit-F011

**论文要求簇内 4 个 PE 各取一个不同 FP16 激活；RTL 中不同激活分布在不同行（每行一个），且激活为 FP8 而非 FP16。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/README.md:3-9`
- paper/docs (paper, PDF p.7): “while processing four distinct FP16 activations”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F012

**论文要求 FP16 激活与全浮点域 MAC；RTL 激活为 FP8 且累加为块浮点整数尾数，非逐项浮点累加。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/README.md:3-9`
- paper/docs (paper, PDF p.7, text lines 151-155): “Processing Element.Each PE, depicted in Fig. 6(b), forms the basic compute unit within the 4-way MAC cluster, op- erating on the decoded weight terms and FP16 activations to perform multiply-accumulate entirely in the floating-point domain. Each MAC cluster contains four PEs sharing one”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F013

**同 local_entry：cyc2 用符号位与未右移的 A**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/fp8_pe_mac_stream.v:395-423`
- paper/docs (paper, PDF p.7): “S1 =A+ (b 0 & (A≫1))”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F014

**同 local_entry**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/fp8_pe_mac_stream.v:452-490`
- condition: `cycleLast and (data_in[0] or act_is_zero)`
- paper/docs (paper, PDF p.8): “The fourth weight term, thezero flag, is latched atcyc3and remains valid for the rest of the precision window”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F015

**同 local_entry：符号 FIFO 写入在 cyc1 而非 cyc0。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:136-183`
- paper/docs (paper, PDF p.8, text lines 113-114): “markers. Atcyc0, it enters theSIGNstate and pushes the sign term into the FIFO. Atcyc1, it transitions to theREGIME”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F016

**论文要求 cyc0 推入符号项；代码在 cyc1 写符号、cyc0 写零标志与 exp/man**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:218-281`
- paper/docs (paper, PDF p.8, text lines 113-114): “markers. Atcyc0, it enters theSIGNstate and pushes the sign term into the FIFO. Atcyc1, it transitions to theREGIME”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F017

**同 local_entry：以固定位宽上限而非 cycP 终止尾数收集。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:218-279`
- condition: `index >= 0 and len(fraction) >= MAX_POSIT_FRACTION_BITS`
- paper/docs (paper, PDF p.8, text lines 123-124): “MANTISSAstate, each bit is shifted into a register as it arrives untilcycP, producing the mantissa term. A zero flag is tracked”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F018

**同 local_entry：RTL 分槽写入而非一起推入。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/posit_decode_and_queue.v:339-384`
- condition: `cycle0 and re`
- paper/docs (paper, PDF p.8): “At completion, the decoder pushes the exponent, mantissa, and zero flag into the per-column FIFO together, forming one decoded weight.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F019

**论文的“轮流完成、无停顿”依赖共享累加器时分复用；RTL 无共享，且存在全局 stall 背压路径。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:198-240`
- paper/docs (paper, PDF p.7): “since each bit-serial multiplication spans multiple cycles, each PE completes its accumulation in turn without stalls”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F020

**论文要求簇内 4 个 PE 同周期共享同一解码权重项；RTL 中同列相邻 PE 收到同一权重项但相差 1 周期，且不存在“簇内 4 PE 同周期”结构。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:242-330`
- paper/docs (paper, PDF p.7): “Within each cluster, all PEs operate on the same decoded weight term each cycle”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F021

**同 local_entry：写出受 out_ready 背压与一拍填充延迟约束，非无停顿。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:411-512`
- paper/docs (paper, PDF p.7): “and be written out without stalls.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F022

**同 local_entry：符号与 Algorithm 2 第6行相反。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `scripts/regen_sensitivity_ppl.sh:8-33`
- paper/docs (paper, PDF p.6, text lines 10-10): “6:∆PPL(w)←P base −PPL(Mw,D)”
- paper/docs (paper, PDF p.5): “a large∆PPLindicates that additional precision provides a significant accuracy gain, whereas a small∆PPLyields only marginal improvement”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F023

**论文要求激活保持 FP16；硬件导出/仿真路径把激活转成 FP8 E4M3。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `src/flexposit/export.py:105-141`
- paper/docs (paper, PDF p.5): “only the weights are quantized while activations remain in FP16”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F024

**论文要求窗口为阵列列数整数倍；脚本默认256（16列整数倍）但模块默认64，且无对齐校验（E4,E5,E6）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `src/flexposit/sensitivity/ppl_probe.py:72-75`
- condition: `channel_window % 16 != 0`
- paper/docs (paper, PDF p.5): “FlexPosit sets the precision granularity to an integer multiple of the number of columns in the systolic array, partitioning each layer into channel windows”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F025

**When r[0] not in valid_layers: Sensitivity rows for layers not present in the model are silently dropped, so the upgrade budget is computed only over matching layers. (src/flexposit/api.py:149)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/api.py:149` in `src/flexposit/api.py::plan_windows`
- condition: `r[0] not in valid_layers`
- code snippet (`src/flexposit/api.py:149`): `rows = [r for r in rows if r[0] in valid_layers]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## flexposit-F026

**When span == 0: If upgrade_nsize equals base_nsize (span zero), the upgrade fraction silently becomes 0.0 instead of erroring, so no windows are upgraded. (src/flexposit/api.py:153)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/api.py:153` in `src/flexposit/api.py::plan_windows`
- condition: `span == 0`
- code snippet (`src/flexposit/api.py:153`): `frac = (config.bits - config.base_nsize) / span if span else 0.0`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

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

## flexposit-F030

**When all(int(e) > max_es for e in cands): If every caller-supplied es candidate exceeds nsize-1, the list is empty and the code silently falls back to es=0 instead of rejecting the configuration, so the requested es search is not performed. (src/flexposit/core.py:37)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/core.py:37` in `src/flexposit/core.py::_es_list`
- condition: `all(int(e) > max_es for e in cands)`
- code snippet (`src/flexposit/core.py:37`): `return [int(e) for e in cands if int(e) <= max_es] or [0]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target statement has no effect check yet

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

## flexposit-F033

**When all(e > max_es for e in es_cands): If every caller-supplied es candidate exceeds nsize-1, the search silently falls back to es=0 instead of rejecting or reporting; the requested es_cands are ignored and a different (simpler) exponent-size variant is quantized. (src/flexposit/mpq/channel_window.py:136)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:136` in `src/flexposit/mpq/channel_window.py::_best_scale_es_for_vec`
- condition: `all(e > max_es for e in es_cands)`
- code snippet (`src/flexposit/mpq/channel_window.py:136`): `es_list = [e for e in es_cands if e <= max_es] or [0]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

## flexposit-F034

**When start >= end: A window whose clamped start is not less than its end returns the weight unchanged, so an out-of-range or empty caller window is silently a no-op. (src/flexposit/mpq/channel_window.py:161)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:161` in `src/flexposit/mpq/channel_window.py::quantize_window_cpu_from_fp32`
- condition: `start >= end`
- code snippet (`src/flexposit/mpq/channel_window.py:161`): `if start >= end:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## flexposit-F035

**When not (is_quant_linear(mod) and hasattr(mod, "weight") and mod.weight is not None and mod.weight.dim() == 2): Modules in the window list that are not recognized quantizable 2D linear layers are skipped, so caller-specified windows on other module types are ignored. (src/flexposit/mpq/channel_window.py:205)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:205` in `src/flexposit/mpq/channel_window.py::apply_windows_to_model`
- condition: `not (is_quant_linear(mod) and hasattr(mod, "weight") and mod.weight is not None and mod.weight.dim() == 2)`
- code snippet (`src/flexposit/mpq/channel_window.py:205`): `if not (is_quant_linear(mod) and hasattr(mod, 'weight') and (mod.weight is not None) and (mod.weight.dim() == 2)):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## flexposit-F036

**When key not in ref_sd: A layer named in the sensitivity windows but absent from the FP32 reference state dict is skipped (with a warning), so the requested window quantization is not applied to that layer. (src/flexposit/mpq/channel_window.py:208)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:208` in `src/flexposit/mpq/channel_window.py::apply_windows_to_model`
- condition: `key not in ref_sd`
- code snippet (`src/flexposit/mpq/channel_window.py:208`): `if key not in ref_sd:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## flexposit-F037

**When dp >= 0.0 and not allow_positive: When allow_positive is False, windows with non-negative delta_ppl are filtered out of the candidate set, so the caller's allow_positive_to_meet_budget setting changes which windows the mechanism considers. (src/flexposit/mpq/channel_window.py:256)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/mpq/channel_window.py:256` in `src/flexposit/mpq/channel_window.py::_dedup_windows`
- condition: `dp >= 0.0 and not allow_positive`
- code snippet (`src/flexposit/mpq/channel_window.py:256`): `if dp >= 0.0 and (not allow_positive):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

## flexposit-F038

**论文要求 4 并行 MAC/权重项；RTL 为单 PE 串行位乘。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `hardware/rtl/fp8_pe_mac_stream.v:497-621`
- paper/docs (paper, PDF p.7): “effectively performing four parallel MACs per weight and recovering the throughput loss to bit-serial execution”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F039

**论文的 4/P 依赖 4-PE 簇并行；RTL 每 PE 为 1/P，簇级 4/P 未被实现。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `hardware/rtl/systolic_efficient.v:198-240`
- condition: `precision_reg >= 4 and precision_reg <= 8`
- paper/docs (paper, PDF p.7, text lines 139-142): “to bit-serial execution. As a result, each cluster achieves an effective throughput of4/PMACs per cycle for any supported precision configuration (4≤P≤8), matching the rate of a conventional FP16 MAC at the minimum 4 b precision”
- paper/docs (paper, PDF p.7): “matching the rate of a conventional FP16 MAC at the minimum 4 b precision while retaining the precision-tunable flexibility of bit-serial computation”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F040

**剖析实验路径未产出论文要求的降序排序敏感度图。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `scripts/regen_sensitivity_ppl.sh:8-33`
- paper/docs (paper, PDF p.6, text lines 14-14): “10:returnSORTDESC(S,∆PPL)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

## flexposit-F041

**论文要求 Qwen 1024；脚本与模块均无 Qwen→1024 规则（E4,E5,E6）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `src/flexposit/sensitivity/ppl_probe.py:72-75`
- paper/docs (paper, PDF p.9): “(256 channels by default and 1024 channels for the Qwen models), aligned to an integer multiple of the number of columns in the systolic array.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

