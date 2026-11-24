# Limitations report: NNSmith: Generating Diverse and Valid Test Cases for Deep Learning Compilers

- artifact: `nnsmith` (ASPLOS 2023), repository https://github.com/ise-uiuc/nnsmith at `a8307f2b80`
- input: `results/step4/nnsmith/limitations_for_tests.json` (sha256 `36d40c452598`), 38 Findings
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
| Findings | 38 |
| tested | 22 |
| not tested | 16 |
| verdicts | inconclusive 2, yes 20 |
| levels | L1 19, L2 1, invalid 2 |
| analysis only (not tests) | A0 3, A1 8, A2 5 |
| not tested, by reason | `no_code_location` 3, `outcome_unsupported` 13 |

Code side's predicted ceiling vs measured level (both uncalibrated; 20 tested Findings have both): equal 18, measured below ceiling 2, measured above ceiling 0.

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [nnsmith-F001](#nnsmith-f001) | undisclosed | reject | `nnsmith/abstract/op.py:1563` | **yes** / L1 (uncalibrated) |
| [nnsmith-F003](#nnsmith-f003) | undisclosed | reject | `nnsmith/cli/fuzz.py:180` | **inconclusive** / invalid (uncalibrated) |
| [nnsmith-F004](#nnsmith-f004) | contradicts_docs | reject | `nnsmith/graph_gen.py:260` | **yes** / L1 (uncalibrated) |
| [nnsmith-F009](#nnsmith-f009) | undisclosed | path_change | `nnsmith/abstract/arith.py:74` | **inconclusive** / invalid (uncalibrated) |
| [nnsmith-F010](#nnsmith-f010) | undisclosed | path_change | `nnsmith/abstract/arith.py:79` | **yes** / L1 (uncalibrated) |
| [nnsmith-F011](#nnsmith-f011) | undisclosed | path_change | `nnsmith/abstract/op.py:25` | **yes** / L1 (uncalibrated) |
| [nnsmith-F012](#nnsmith-f012) | undisclosed | path_change | `nnsmith/abstract/op.py:910` | **yes** / L1 (uncalibrated) |
| [nnsmith-F014](#nnsmith-f014) | undisclosed | path_change | `nnsmith/abstract/op.py:1587` | **yes** / L1 (uncalibrated) |
| [nnsmith-F015](#nnsmith-f015) | undisclosed | path_change | `nnsmith/cli/fuzz.py:60` | **yes** / L1 (uncalibrated) |
| [nnsmith-F016](#nnsmith-f016) | undisclosed | path_change | `nnsmith/cli/model_gen.py:31` | **yes** / L1 (uncalibrated) |
| [nnsmith-F017](#nnsmith-f017) | undisclosed | path_change | `nnsmith/graph_gen.py:256` | **yes** / L1 (uncalibrated) |
| [nnsmith-F018](#nnsmith-f018) | undisclosed | path_change | `nnsmith/graph_gen.py:258` | **yes** / L1 (uncalibrated) |
| [nnsmith-F019](#nnsmith-f019) | stated_differently | path_change | `nnsmith/graph_gen.py:556` | **yes** / L1 (uncalibrated) |
| [nnsmith-F020](#nnsmith-f020) | undisclosed | path_change | `nnsmith/graph_gen.py:944` | **yes** / L1 (uncalibrated) |
| [nnsmith-F021](#nnsmith-f021) | undisclosed | path_change | `nnsmith/materialize/torch/__init__.py:47` | **yes** / L1 (uncalibrated) |
| [nnsmith-F022](#nnsmith-f022) | undisclosed | path_change | `nnsmith/materialize/torch/input_gen.py:93` | **yes** / L1 (uncalibrated) |
| [nnsmith-F006](#nnsmith-f006) | undisclosed | other | `nnsmith/materialize/torch/symbolnet.py:188` | not tested: `outcome_unsupported`, analysis A2/supports |
| [nnsmith-F024](#nnsmith-f024) | undisclosed | other | `nnsmith/materialize/torch/symbolnet.py:234` | not tested: `outcome_unsupported`, analysis A2/supports |
| [nnsmith-F025](#nnsmith-f025) | undisclosed | path_change | `nnsmith/materialize/torch/symbolnet.py:238` | **yes** / L1 (uncalibrated) |
| [nnsmith-F028](#nnsmith-f028) | impl_deviates | other | `nnsmith/abstract/op.py:1053-1080` | not tested: `no_code_location`, analysis A0/contradicts |
| [nnsmith-F029](#nnsmith-f029) | impl_deviates | other | `nnsmith/abstract/op.py:1332-1360` | not tested: `no_code_location`, analysis A0/supports |
| [nnsmith-F030](#nnsmith-f030) | impl_deviates | other | `nnsmith/graph_gen.py:1029-1058` | not tested: `no_code_location`, analysis A2/supports |
| [nnsmith-F013](#nnsmith-f013) | undisclosed | other | `nnsmith/abstract/op.py:1552` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F002](#nnsmith-f002) | undisclosed | other | `nnsmith/abstract/op.py:2083` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F031](#nnsmith-f031) | undisclosed | other | `nnsmith/graph_gen.py:190` | not tested: `outcome_unsupported`, analysis A0/supports |
| [nnsmith-F005](#nnsmith-f005) | undisclosed | other | `nnsmith/graph_gen.py:524` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F032](#nnsmith-f032) | undisclosed | other | `nnsmith/graph_gen.py:834` | not tested: `outcome_unsupported`, analysis A2/supports |
| [nnsmith-F033](#nnsmith-f033) | undisclosed | other | `nnsmith/graph_gen.py:984` | not tested: `outcome_unsupported`, analysis A2/supports |
| [nnsmith-F034](#nnsmith-f034) | undisclosed | path_change | `nnsmith/graph_gen.py:1016` | **yes** / L1 (uncalibrated) |
| [nnsmith-F035](#nnsmith-f035) | undisclosed | path_change | `nnsmith/graph_gen.py:1044` | **yes** / L2 (uncalibrated) |
| [nnsmith-F036](#nnsmith-f036) | paper_stated | path_change | `nnsmith/graph_gen.py:1052` | **yes** / L1 (uncalibrated) |
| [nnsmith-F037](#nnsmith-f037) | undisclosed | path_change | `nnsmith/graph_gen.py:1054` | **yes** / L1 (uncalibrated) |
| [nnsmith-F023](#nnsmith-f023) | undisclosed | other | `nnsmith/materialize/torch/input_gen.py:98` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F026](#nnsmith-f026) | undisclosed | other | `nnsmith/materialize/torch/symbolnet.py:358` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F038](#nnsmith-f038) | undisclosed | path_change | `nnsmith/materialize/torch/symbolnet.py:382` | **yes** / L1 (uncalibrated) |
| [nnsmith-F007](#nnsmith-f007) | undisclosed | other | `nnsmith/materialize/torch/symbolnet.py:385` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F027](#nnsmith-f027) | undisclosed | other | `nnsmith/materialize/torch/symbolnet.py:403` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [nnsmith-F008](#nnsmith-f008) | undisclosed | other | `nnsmith/materialize/torch/symbolnet.py:421` | not tested: `outcome_unsupported`, analysis A1/unclear |

## nnsmith-F001

**When gres_config not in ("3", "4", "5"): An unrecognized NNSMITH_GRES environment value causes a ValueError, rejecting the input. (nnsmith/abstract/op.py:1563)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `nnsmith/abstract/op.py:1563` in `nnsmith/abstract/op.py::Reshape.requires`
- condition: `gres_config not in ("3", "4", "5")`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Rejecting an invalid value of an internal env knob is config validation, not a limit of what the mechanism supports.
- code snippet (`nnsmith/abstract/op.py:1563`): `raise ValueError(f'NNSMITH_GRES={gres_config} is not recognized')`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: ValueError at nnsmith/abstract/op.py:1563
- contrast run: no exception at nnsmith/abstract/op.py:1563
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/nnsmith/nnsmith-F001/execution_report.json`

## nnsmith-F003

**When isinstance(e, InternalError): InternalError from make_testcase is propagated, aborting the fuzzing loop, while other exceptions are swallowed and the loop continues. (nnsmith/cli/fuzz.py:180)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `nnsmith/cli/fuzz.py:180` in `nnsmith/cli/fuzz.py::FuzzingLoop.run`
- condition: `isinstance(e, InternalError)`
- paper/docs (code_comment, nnsmith/cli/fuzz.py:180): “propagate internal errors”
- code snippet (`nnsmith/cli/fuzz.py:180`): `raise e`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  no effect on either input

Code side predicted ceiling before the test: L1 (measured: invalid).

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2

- trigger run: no exception at nnsmith/cli/fuzz.py:180 (later InternalError at nnsmith/error.py:73)
- contrast run: no exception at nnsmith/cli/fuzz.py:180
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. condition does not hold on the positive or does not fail on the negative
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 0
  - D6 verdict-bearing observations do not depend on stand-ins: *refuted*. verdict-bearing observations: positive simulated:stub, negative simulated:stub
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The advertised call_chain[0] PracticalHybridSearch.search_one has no static path to FuzzingLoop.run (step 4 reports call_chain_status=not_found); FuzzingLoop.run is the target's …
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): 1 mutant(s) survived because no input separates them from the original: delete_statement (`pass # propagate internal errors`). Add inputs that d…; D6 (refuted): move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation
- evidence: `tests/nnsmith/nnsmith-F003/execution_report.json`

## nnsmith-F004

**When self.check_sat() != z3.sat: After adding the memory-limit constraint, an unsatisfiable (or unknown) solver result aborts generation via assertion. (nnsmith/graph_gen.py:260)**

- category `contradicts_docs`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `nnsmith/graph_gen.py:260` in `nnsmith/graph_gen.py::SimpleGenerator.abstract_gen`
- condition: `self.check_sat() != z3.sat`
- paper/docs (paper, 3.2 Model Generation, p.6): “if the solver fails to find a satisfiable assignment after adding 𝐶𝑏to the graph’s constraints, we randomly drop half of the constraints and retry, until it succeeds (Line 18).”
- paper/docs (paper, 3.2 Model Generation, p.6): “17 while ¬𝑀.solver.try_add_constraints(𝐶𝑏) do 18 𝐶𝑏←randomly select |𝐶𝑏| 2 constraints in 𝐶𝑏”
- code snippet (`nnsmith/graph_gen.py:260`): `assert self.check_sat() == z3.sat`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: AssertionError at nnsmith/graph_gen.py:260
- contrast run: no exception at nnsmith/graph_gen.py:260
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/nnsmith/nnsmith-F004/execution_report.json`

## nnsmith-F009

**When carry and max(left_size, right_size) >= ARITH_MAX_WIDTH: For addition, the extra carry bit is only prepended when the wider operand is strictly below ARITH_MAX_WIDTH; at the maximum width nnsmith_add silently omits the carry extension. (nnsmith/abstract/arith.py:74)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/arith.py:74` in `nnsmith/abstract/arith.py::align_bvs`
- condition: `carry and max(left_size, right_size) >= ARITH_MAX_WIDTH`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Internal carry-bit extension in the z3 helper.
- code snippet (`nnsmith/abstract/arith.py:74`): `if carry and max(left_size, right_size) < ARITH_MAX_WIDTH:`

**Verdict `inconclusive`**: no verdict: the test was invalid or could not separate the cases.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: invalid).

**Level invalid, uncalibrated.** a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn. refuted fatal defeaters: D2

- trigger run: branch taken at nnsmith/abstract/arith.py:74
- contrast run: branch not taken at nnsmith/abstract/arith.py:74
- open doubts:
  - D2 condition holds on positive, fails on negative: *refuted*. the agent's predicate and Region.condition disagree: Region.condition itself does not hold on the positive run and does not fail on the negative run
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D5 control pair differs in one factor, negative adjacent to the boundary: *open*. a neighbour probe failed before the target was decided
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 Region call chain [PracticalHybridSearch.search_one, align_bvs] is synthetic: no real call graph was handed over, and search_one only reaches align_bvs through a full …
- what would raise the level: D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (open): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/nnsmith/nnsmith-F009/execution_report.json`

## nnsmith-F010

**When mult and (right.size() + left.size()) >= ARITH_MAX_WIDTH: For multiplication, when the combined width already reaches ARITH_MAX_WIDTH, align_bvs returns the operands without zero-extension, so nnsmith_mul silently skips the widening that it performs for narrower operands. (nnsmith/abstract/arith.py:79)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/arith.py:79` in `nnsmith/abstract/arith.py::align_bvs`
- condition: `mult and (right.size() + left.size()) >= ARITH_MAX_WIDTH`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Internal bit-width cap in the z3 multiplication helper.
- code snippet (`nnsmith/abstract/arith.py:79`): `if max_val >= ARITH_MAX_WIDTH:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/abstract/arith.py:79
- contrast run: branch not taken at nnsmith/abstract/arith.py:79
- open doubts:
  - D3 oracle can see the effect: *residual*. only 2 mutants (< n_min=4); killed 2
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. the official entry started first but the target line did not run inside it and no reason is recorded
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (refuted): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F010/execution_report.json`

## nnsmith-F011

**When FLOPS_LIM == "off": Setting NNSMITH_FLOPS_LIM=off sets FLOPS_LIM to None, disabling the FLOPs constraint entirely, which changes the search/acceptance behavior of the generator. (nnsmith/abstract/op.py:25)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/op.py:25` in `nnsmith/abstract/op.py::<module>`
- condition: `FLOPS_LIM == "off"`
- code snippet (`nnsmith/abstract/op.py:25`): `if FLOPS_LIM == 'off':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/abstract/op.py:25
- contrast run: branch not taken at nnsmith/abstract/op.py:25
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'FLOPS_LIM' is not an integer (value '123')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/nnsmith/nnsmith-F011/execution_report.json`

## nnsmith-F012

**When Z3_CONS_FLOPS: A module-level flag decides whether the FLOPS upper-bound constraint is added to the Pool2d requirements; when enabled, the solver rejects parameter/shape combinations exceeding FLOPS_LIM, changing which models are generated. (nnsmith/abstract/op.py:910)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/op.py:910` in `nnsmith/abstract/op.py::Pool2d.requires`
- condition: `Z3_CONS_FLOPS`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: NNSMITH_Z3_CONS_FLOPS=off removes the FLOPS bound from the solver constraints (and other values fail an assert at import), an env-driven switch in how FLOPS are limited.
- code snippet (`nnsmith/abstract/op.py:910`): `if Z3_CONS_FLOPS:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/abstract/op.py:910
- contrast run: branch not taken at nnsmith/abstract/op.py:910
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'Z3_CONS_FLOPS' is not an integer (value False)
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/nnsmith/nnsmith-F012/execution_report.json`

## nnsmith-F014

**When os.getenv("NNSMITH_CONS_RESHAPE", "off") != "off": The environment variable NNSMITH_CONS_RESHAPE toggles whether additional dimension-limit constraints (__DIM_LIMIT__=4096, halving per dim) are added to the Reshape constraints, changing the generated constraint set. (nnsmith/abstract/op.py:1587)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/op.py:1587` in `nnsmith/abstract/op.py::Reshape.requires`
- condition: `os.getenv("NNSMITH_CONS_RESHAPE", "off") != "off"`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: The NNSMITH_CONS_RESHAPE env var adds per-dimension upper bounds to Reshape target shapes, changing which shapes the generator can produce.
- code snippet (`nnsmith/abstract/op.py:1587`): `if os.getenv('NNSMITH_CONS_RESHAPE', 'off') != 'off':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/abstract/op.py:1587
- contrast run: branch not taken at nnsmith/abstract/op.py:1587
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 5); reason recorded: The step-4 call chain is synthetic (the adapter notes the real call graph is not part of the hand-off): PracticalHybridSearch.search_one never invokes Reshape.requires in the pin…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F014/execution_report.json`

## nnsmith-F015

**When not self.crash_safe and self.test_timeout is not None: Setting fuzz.test_timeout without crash_safe silently changes execution to the crash-safe path (warning only), altering how testcases are validated. (nnsmith/cli/fuzz.py:60)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/cli/fuzz.py:60` in `nnsmith/cli/fuzz.py::FuzzingLoop.__init__`
- condition: `not self.crash_safe and self.test_timeout is not None`
- code snippet (`nnsmith/cli/fuzz.py:60`): `if not self.crash_safe and self.test_timeout is not None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/cli/fuzz.py:60 (later ValueError at nnsmith/cli/fuzz.py:90)
- contrast run: branch not taken at nnsmith/cli/fuzz.py:60 (later ValueError at nnsmith/cli/fuzz.py:90)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The upstream call chain is inconsistent for this finding: call_chain[0] is PracticalHybridSearch.search_one, which has no call edge to FuzzingLoop.__init__ (FuzzingLoop.run would…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F015/execution_report.json`

## nnsmith-F016

**When cfg["backend"]["type"] is not None: A caller-supplied backend type decides whether a BackendFactory is constructed; the factory is then passed to auto_opset, changing which operators are considered available for model generation. (nnsmith/cli/model_gen.py:31)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/cli/model_gen.py:31` in `nnsmith/cli/model_gen.py::main`
- condition: `cfg["backend"]["type"] is not None`
- code snippet (`nnsmith/cli/model_gen.py:31`): `if cfg['backend']['type'] is not None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/cli/model_gen.py:31 (later ValueError at nnsmith/materialize/__init__.py:221)
- contrast run: branch not taken at nnsmith/cli/model_gen.py:31 (later ValueError at nnsmith/materialize/__init__.py:221)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The target statement lives in main. The hand-off lists PracticalHybridSearch.search_one as call_chain[0] because it is the artifact's global entry point, but that function is cal…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F016/execution_report.json`

## nnsmith-F017

**When NNSMITH_LIMNF_V == "0": Branches the memory-limit constraint: v0 adds nnsmith_le(self.n_floats, self.limit_float); v1 adds the accumulated self.n_floats_cons instead. (nnsmith/graph_gen.py:256)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/graph_gen.py:256` in `nnsmith/graph_gen.py::SimpleGenerator.abstract_gen`
- condition: `NNSMITH_LIMNF_V == "0"`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: The NNSMITH_LIMNF_V env var switches between one total float-count limit and per-node limits on tensor size.
- code snippet (`nnsmith/graph_gen.py:256`): `if NNSMITH_LIMNF_V == '0':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:256
- contrast run: branch not taken at nnsmith/graph_gen.py:256
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'NNSMITH_LIMNF_V' is not an integer (value '1')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/nnsmith/nnsmith-F017/execution_report.json`

## nnsmith-F018

**When NNSMITH_LIMNF_V == "1": With NNSMITH_LIMNF_V=1 the per-op float-count constraints accumulated in `self.n_floats_cons` are added to the solver instead of the single aggregate constraint, so the same seed yields different accepted graphs depending on the environment variable. (nnsmith/graph_gen.py:258)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/graph_gen.py:258` in `nnsmith/graph_gen.py::SimpleGenerator.abstract_gen`
- condition: `NNSMITH_LIMNF_V == "1"`
- code snippet (`nnsmith/graph_gen.py:258`): `if NNSMITH_LIMNF_V == '1':`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:258
- contrast run: branch not taken at nnsmith/graph_gen.py:258
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D5 control pair differs in one factor, negative adjacent to the boundary: *residual*. one factor differs; adjacency not measurable: boundary variable 'NNSMITH_LIMNF_V' is not an integer (value '2')
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
- evidence: `tests/nnsmith/nnsmith-F018/execution_report.json`

## nnsmith-F019

**When random.uniform(0, 1) < self.forward_prob: A caller-configured forward_prob attribute decides whether the node is inserted by forward insertion (try_forward_insert) or backward insertion (try_backward_insert), selecting between two different graph-construction algorithms. (nnsmith/graph_gen.py:556)**

- category `stated_differently`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/graph_gen.py:556` in `nnsmith/graph_gen.py::SimpleGenerator.try_insert_node_type`
- condition: `random.uniform(0, 1) < self.forward_prob`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: forward_prob is just the probability of mixing forward and backward insertion, both part of the normal mechanism; it is a tuning knob.
- paper/docs (paper, 5 EVALUATION 5.1 Experimental Setup, p.8): “When evaluating NNSmith, for Algorithm 1 we choose between forward and backward at every insertion randomly with equal probability.”
- paper/docs (paper, 3.2 Model Generation, p.4): “extending it by either (a) adding a new node whose input edges are connected to the output of an existing node (we refer to this as a forward insertion) or (b) replacing an existing placeholder node with an operator node whose input edges are connected to one or more placeholder nodes (we refer to …”
- code snippet (`nnsmith/graph_gen.py:556`): `if random.uniform(0, 1) < self.forward_prob:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L3 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:556
- contrast run: branch not taken at nnsmith/graph_gen.py:556
- open doubts:
  - D2 condition holds on positive, fails on negative: *residual*. agent-written predicate holds on positive and fails on negative; its fidelity to the Region condition is not verified
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D2 (residual): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated
- evidence: `tests/nnsmith/nnsmith-F019/execution_report.json`

## nnsmith-F020

**When idx in disable: For each reshape group, one randomly chosen destination dimension is disabled from binning, so that dimension is left unconstrained by the guidance. (nnsmith/graph_gen.py:944)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/graph_gen.py:944` in `nnsmith/graph_gen.py::__GROUP_RESHAPE`
- condition: `idx in disable`
- code snippet (`nnsmith/graph_gen.py:944`): `if idx in disable:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:944
- contrast run: branch not taken at nnsmith/graph_gen.py:944 (later IndexError at nnsmith/graph_gen.py:946)
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: random_model_gen constructs PureSymbolGen, whose extra_constraints returns [] and whose extra_constraints call sites are commented out, so the guided PARAM_CONFIG1 Reshape callab…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F020/execution_report.json`

## nnsmith-F021

**When self.sat_inputs is None: When no satisfying inputs were found (sat_inputs is None), make_oracle silently uses random inputs via get_random_inps() rather than the search result, changing which inputs the oracle is built from. (nnsmith/materialize/torch/__init__.py:47)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/materialize/torch/__init__.py:47` in `nnsmith/materialize/torch/__init__.py::TorchModel.make_oracle`
- condition: `self.sat_inputs is None`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: When the value search finds no satisfying inputs, the oracle silently uses random inputs that may produce NaN/Inf.
- paper/docs (code_comment, nnsmith/materialize/torch/__init__.py:46): “fall back to random inputs if no solution is found.”
- code snippet (`nnsmith/materialize/torch/__init__.py:47`): `if self.sat_inputs is None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/materialize/torch/__init__.py:47
- contrast run: branch not taken at nnsmith/materialize/torch/__init__.py:47
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *refuted*. the official entry started first but the target line did not run inside it and no reason is recorded
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (refuted): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F021/execution_report.json`

## nnsmith-F022

**When all([DType.is_float(v.dtype) for _, v in self.net.input_like.items()]): Whether all model inputs are float dtypes decides if a differentiability probe is run; otherwise self.differentiable is forced False, which later routes search_one to SamplingSearch instead of GradSearch. (nnsmith/materialize/torch/input_gen.py:93)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/materialize/torch/input_gen.py:93` in `nnsmith/materialize/torch/input_gen.py::PracticalHybridSearch.__init__`
- condition: `all([DType.is_float(v.dtype) for _, v in self.net.input_like.items()])`
- paper/docs (code_comment, nnsmith/materialize/torch/input_gen.py:103): “if this model is purely differentiable -> GradSearch otherwise -> SamplingSearch FIXME: Estimate gradient (e.g., proxy gradient) for non-differentiable inputs.”
- code snippet (`nnsmith/materialize/torch/input_gen.py:93`): `if all([DType.is_float(v.dtype) for _, v in self.net.input_like.items()]):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/materialize/torch/input_gen.py:93
- contrast run: branch not taken at nnsmith/materialize/torch/input_gen.py:93
- open doubts:
  - D2 condition holds on positive, fails on negative: *residual*. agent-written predicate holds on positive and fails on negative; its fidelity to the Region condition is not verified
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The Region target is PracticalHybridSearch.__init__; the instance must be constructed (running the target) before the official entry search_one can be invoked, so __init__ starts…
- what would raise the level: D2 (residual): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated; D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F022/execution_report.json`

## nnsmith-F006

**When p.grad is not None and torch.any(p.grad != 0): If all parameter gradients are zero, ConstraintCheck.true(nonzero, ...) raises, aborting the backward step ('Gradients are all zero. Cannot make progress.'). (nnsmith/materialize/torch/symbolnet.py:188)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:188` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.backward`
- condition: `p.grad is not None and torch.any(p.grad != 0)`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: Zero gradients raise ConstraintError, grad_input_gen breaks and returns None, so for such models the gradient search gives up and make_oracle ends up using random inputs.
- paper/docs (paper, PDF p.7): “if⟨𝑋,𝑊⟩ not changed then // Zero gradients”
- paper/docs (paper, PDF p.7): “⟨𝑋,𝑊⟩← randomly initialized values”
- code snippet (`nnsmith/materialize/torch/symbolnet.py:188`): `if p.grad is not None and torch.any(p.grad != 0):`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code gates a nonzero-gradient flag on `p.grad is not None and torch.any(p.grad != 0)`, then calls `ConstraintCheck.true(...)` with the zero-gradient error message. Thus all-zero gradients make the check fail and raise, matching the finding. The paper instead says to reinitialize and continue OUTER, so the abort behavior is an undisclosed discrepancy.
- cited code found at the pinned commit: yes (6 location(s))
- probe `if p\.grad is not None and torch\.any\(p\.grad != 0\):` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Shows the code only treats gradients as nonzero when any element differs from zero.
- probe `Gradients are all zero\. Cannot make progress\.` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Confirms the zero-gradient failure message exists in the file.
- probe `nonzero\s*=\s*True` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Shows a nonzero flag is set only under the nonzero-gradient condition.
- what would settle it: Run backward on a network with all parameter gradients zero and observe whether it raises the zero-gradient ConstraintError instead of reinitializing and continuing.

## nnsmith-F024

**When max_time is None: The gradient-based input search budget is taken from the environment (NNSMITH_GRAD_TIME, default 0.5 s). The `while time.time() - st < max_time` loop at line 257 can therefore exit before any satisfying input is found, in which case `grad_input_gen` returns None (line 293) and the caller falls back to random sampling. (nnsmith/materialize/torch/symbolnet.py:234)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:234` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen`
- condition: `max_time is None`
- paper/docs (paper, PDF p.7): “raise failed to find viable⟨𝑋,𝑊⟩”
- code snippet (`nnsmith/materialize/torch/symbolnet.py:234`): `max_time = float(os.getenv('NNSMITH_GRAD_TIME', 0.5))`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code reads NNSMITH_GRAD_TIME with default 0.5, loops only while under max_time, and returns sat_inputs (None) without raising. That directly contradicts the paper's 'raise failed to find viable'. The random-sampling fallback is not in the snippet, but the timeout/None discrepancy is supported.
- cited code found at the pinned commit: yes (3 location(s))
- probe `NNSMITH_GRAD_TIME` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). env budget default is read
- probe `while time\.time\(\) - st < max_time` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). loop can exit on timeout
- probe `return sat_inputs` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). timeout returns None, not raise
- what would settle it: Trace PracticalHybridSearch.search to see whether a None from grad_input_gen triggers random sampling.

## nnsmith-F025

**When tensor.data.dtype.is_floating_point: Only floating-point input tensors are wrapped as trainable Parameters; integer tensors are passed through untrained, so gradient-based input search only optimizes float inputs. (nnsmith/materialize/torch/symbolnet.py:238)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:238` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen`
- condition: `tensor.data.dtype.is_floating_point`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: Gradient-guided value search optimizes only floating-point inputs; integer inputs are never searched.
- code snippet (`nnsmith/materialize/torch/symbolnet.py:238`): `if tensor.data.dtype.is_floating_point:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/materialize/torch/symbolnet.py:238
- contrast run: branch not taken at nnsmith/materialize/torch/symbolnet.py:238
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
- evidence: `tests/nnsmith/nnsmith-F025/execution_report.json`

## nnsmith-F028

**artifact 路径不存在 pad 的 0 箱/负箱特化**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/op.py:1053-1080`
- condition: `self.extra_attrs["type"] in ("ConstPad", "ReplicatePad", "ReflectPad")`
- paper/docs (paper, PDF p.8): “for the “padding” attribute in ConstPad, ReplicatePad, and ReflectPad, we add both the 0-bin and negative bins”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The shown Pad.requires code explicitly adds constraints for negative padding, including the comment and nnsmith_gt(nnsmith_add(pad[...], isv[j]), 0) checks. That contradicts the claim that no negative-bin specialization path exists. The snippet does not show an explicit 0-bin token, but the broad finding that the specialization is absent is not supported.
- cited code found at the pinned commit: yes (2 location(s))
- probe `When using negative padding` in `nnsmith/abstract/op.py` expected present: **confirmed** (1 hit(s)). Shows negative-padding handling exists in Pad.requires.
- probe `nnsmith_gt\(nnsmith_add\(pad\[i \* 2\]` in `nnsmith/abstract/op.py` expected present: **confirmed** (1 hit(s)). Shows explicit negative-padding constraints are implemented.
- probe `0[-_ ]?bin|zero[-_ ]?bin` in `nnsmith/abstract/op.py` expected absent: **confirmed** (0 hit(s)). No explicit 0-bin token appears in this file.
- what would settle it: A unit test instantiating Pad with zero and negative padding and inspecting generated z3 constraints would settle whether both bins are specialized.

## nnsmith-F029

**artifact 路径不存在 Conv2d padding 的 0 箱特化**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/abstract/op.py:1332-1360`
- paper/docs (paper, PDF p.8): “we add one extra bin that contains only one integer “0” for the “padding” attribute in Conv2d”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown NCHWConv2d stores padding generically and concretize_graph only evaluates the z3 model; no code creates a Conv2d padding bin restricted to 0. The paper's claimed zero-only padding bin is therefore absent from the cited path, matching the finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `padding\s*==\s*0|padding\s*=\s*0|\b0\b[^\n]{0,40}padding|padding[^\n]{0,40}\b0\b` in `nnsmith/abstract/op.py` expected absent: **refuted** (12 hit(s)). No zero-only padding bin appears in op.py
- probe `padding` in `nnsmith/graph_gen.py` expected absent: **refuted** (2 hit(s)). graph_gen.py has no padding-specific bin logic
- what would settle it: Search the full pinned op.py and graph_gen.py for any Conv2d padding bin restricted to integer 0; finding none confirms the claim.

## nnsmith-F030

**论文要求每轮随机选一半；代码仅首轮随机，后续轮固定丢弃后半段**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/graph_gen.py:1029-1058`
- condition: `len(cur_cons) > 0 and self.check_sat(*cur_cons) != z3.sat`
- paper/docs (paper, PDF p.6, text lines 48-49): “18 𝐶𝑏← randomly select |𝐶𝑏| 2 constraints in𝐶𝑏”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The code shuffles all constraints once, then in the unsat backoff loop repeatedly truncates the current list to its first half. It does not reshuffle before each halving, so later rounds deterministically discard the latter half of the current ordering, matching the finding.
- cited code found at the pinned commit: yes (1 location(s))
- probe `random\.shuffle\(shuffled\)` in `nnsmith/graph_gen.py` expected present: **confirmed** (1 hit(s)). Shows constraints are shuffled once before the backoff loop.
- probe `while self\.check_sat\(\*cur_cons\) != z3\.sat:` in `nnsmith/graph_gen.py` expected present: **confirmed** (1 hit(s)). Shows the repeated backoff loop where halving occurs.
- probe `cur_cons = cur_cons\[: len\(cur_cons\) // 2\]` in `nnsmith/graph_gen.py` expected present: **confirmed** (1 hit(s)). Shows each failed round keeps only the first half, not a fresh random half.
- what would settle it: Instrument post_process to log cur_cons across backoff iterations and verify no reshuffle occurs after the initial shuffle.

## nnsmith-F013

**When gres_config != "4": The environment variable NNSMITH_GRES selects the reshape grouping strategy: "5" = one group (flatten), "3" = min(src_len, dst_len) groups, "4" (default) = random number of groups weighted by 2**i. Any other value raises ValueError, rejecting the model. The chosen grouping changes the generated reshape constraints and hence the accepted graphs. (nnsmith/abstract/op.py:1...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/abstract/op.py:1552` in `nnsmith/abstract/op.py::Reshape.requires`
- condition: `gres_config != "4"`
- code snippet (`nnsmith/abstract/op.py:1552`): `gres_config = os.getenv('NNSMITH_GRES', '4')`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown line only confirms that NNSMITH_GRES is read with default "4". It does not show the claimed mappings for "5" and "3", the weighted random grouping for "4", the ValueError for other values, or that grouping changes accepted graphs. With no paper evidence, the full finding is not established by the single line.
- cited code found at the pinned commit: yes (1 location(s))
- probe `NNSMITH_GRES` in `nnsmith/abstract/op.py` expected present: **confirmed** (2 hit(s)). Confirms the environment variable is read in this file.
- probe `gres_config\s*==\s*["']5["']` in `nnsmith/abstract/op.py` expected present: **confirmed** (1 hit(s)). Would show a branch for the claimed flatten grouping value.
- probe `gres_config\s*==\s*["']3["']` in `nnsmith/abstract/op.py` expected present: **confirmed** (1 hit(s)). Would show a branch for the claimed min-length grouping value.
- probe `2\s*\*\*\s*i` in `nnsmith/abstract/op.py` expected present: **confirmed** (1 hit(s)). Would support the claimed 2**i weighted random grouping.
- what would settle it: Inspect the full function around line 1552 and trace the branches for NNSMITH_GRES values "5", "3", "4", and invalid values.

## nnsmith-F002

**When not check_sat(): If the requested output rank cannot be satisfied by the rank-increment loop (e.g. out_abs_tensor ndims inconsistent with the max reachable rank), the loop never terminates, effectively rejecting/hanging on that output shape. (nnsmith/abstract/op.py:2083)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/abstract/op.py:2083` in `nnsmith/abstract/op.py::MatMul.deduct_inp_ranks_and_dtype`
- condition: `not check_sat()`
- code snippet (`nnsmith/abstract/op.py:2083`): `while not check_sat():`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only evidence is a while not check_sat() line. It shows a loop gated by satisfiability, but not the rank-increment logic, max reachable rank, or whether check_sat can become true for inconsistent out_abs_tensor ndims. Nontermination/hanging is plausible but not established by the shown line; no paper evidence is recorded.
- cited code found at the pinned commit: yes (1 location(s))
- probe `while not check_sat\(\):` in `nnsmith/abstract/op.py` expected present: **confirmed** (1 hit(s)). Confirms the cited satisfiability-gated loop exists.
- probe `out_abs_tensor` in `nnsmith/abstract/op.py` expected present: **confirmed** (53 hit(s)). Shows the output tensor variable is present in this file.
- probe `rank` in `nnsmith/abstract/op.py` expected present: **confirmed** (107 hit(s)). Shows rank-related logic exists, but not its termination behavior.
- probe `check_sat` in `nnsmith/abstract/op.py` expected present: **confirmed** (2 hit(s)). Shows the satisfiability check is used, but not whether it can fail forever.
- what would settle it: Inspect the loop body and rank-increment bounds to see whether check_sat can ever become true for an unsatisfiable requested output rank.

## nnsmith-F031

**When int(os.getenv("NNSMITH_BITS", 30)) != 30: The number of bits used to split the integer-domain symbols into groups is read from NNSMITH_BITS (default 30). A smaller value makes `random_group` produce more, smaller groups, i.e. a different (coarser) integer encoding of the same abstract graph, changing which graphs the solver accepts. (nnsmith/graph_gen.py:190)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:190` in `nnsmith/graph_gen.py::SimpleGenerator.new_syms`
- condition: `int(os.getenv("NNSMITH_BITS", 30)) != 30`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: NNSMITH_BITS is only read when use_bitvec is True, which is hard-coded False, so this code is dead.
- code snippet (`nnsmith/graph_gen.py:190`): `map(len, random_group(int(os.getenv("NNSMITH_BITS", 30)), len(names)))`

**Not tested** (`outcome_unsupported`): effect type 'other': the target is a call whose effect is not an exception at that line (for example a check that returns False)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown line directly reads NNSMITH_BITS with default 30 and passes it to random_group, matching the finding's core. It does not itself prove the downstream grouping or solver-acceptance effect, but the code evidence supports the undisclosed env-var behavior.
- cited code found at the pinned commit: yes (1 location(s))
- probe `NNSMITH_BITS` in `nnsmith/graph_gen.py` expected present: **confirmed** (1 hit(s)). Confirms env var is read in graph_gen.py.
- probe `def random_group` in `nnsmith/graph_gen.py` expected present: **refuted** (0 hit(s)). Confirms random_group is defined in same file for behavior check.
- probe `random_group` in `nnsmith/graph_gen.py` expected present: **confirmed** (2 hit(s)). Confirms random_group is called in this file.
- what would settle it: Run the solver with NNSMITH_BITS=30 and a smaller value and compare accepted graph sets, after inspecting random_group.

## nnsmith-F005

**When isinstance(op, Expand) and oshape.ndims < op.expand_last_dim: Placeholder shapes with fewer dims than the Expand op's expand_last_dim are skipped as backward-insertion candidates, excluding them from consideration. (nnsmith/graph_gen.py:524)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:524` in `nnsmith/graph_gen.py::SimpleGenerator.try_backward_insert`
- condition: `isinstance(op, Expand) and oshape.ndims < op.expand_last_dim`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Skipping placeholders whose rank is too low for Expand is an operator-specific shape-validity invariant, not a user-facing limitation.
- code snippet (`nnsmith/graph_gen.py:524`): `if isinstance(op, Expand) and oshape.ndims < op.expand_last_dim:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Line 524 shows the exact guard condition, but the shown evidence does not include the loop context or the body that would prove candidates are skipped. A following `continue` would support the finding; without it, the effect is not established.
- cited code found at the pinned commit: yes (1 location(s))
- probe `if isinstance\(op, Expand\) and oshape\.ndims < op\.expand_last_dim:` in `nnsmith/graph_gen.py` expected present: **confirmed** (1 hit(s)). Confirms the cited guard exists in the file.
- probe `(?s)if isinstance\(op, Expand\) and oshape\.ndims < op\.expand_last_dim:\s*\n\s*continue` in `nnsmith/graph_gen.py` expected present: **refuted** (0 hit(s)). Shows the guard immediately skips the candidate via continue.
- what would settle it: A text search showing a `continue` immediately under the line 524 guard would confirm the skip.

## nnsmith-F032

**When os.getenv("NNSMITH_LB", "off") == "off": The upper-bound constraint on slice start/end parameters is only added when the NNSMITH_LB environment variable is unset or 'off'; setting NNSMITH_LB to any other value silently drops the upper bound, changing the generated slice parameter ranges. (nnsmith/graph_gen.py:834)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:834` in `nnsmith/graph_gen.py::range_constrain`
- condition: `os.getenv("NNSMITH_LB", "off") == "off"`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: range_constrain is only called from GuidedGen, which is never instantiated, so the NNSMITH_LB switch has no effect in practice.
- code snippet (`nnsmith/graph_gen.py:834`): `if ub is not None and os.getenv('NNSMITH_LB', 'off') == 'off':`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. Line 834 explicitly gates the `ub is not None` branch on `NNSMITH_LB` being unset or `off`. That matches the claimed condition: any other value skips the branch, so the upper-bound handling is not applied. The shown line does not itself name slice start/end, but the environment-variable gating behavior is directly evidenced.
- cited code found at the pinned commit: yes (1 location(s))
- probe `os\.getenv\("NNSMITH_LB", "off"\) == "off"` in `nnsmith/graph_gen.py` expected present: **confirmed** (1 hit(s)). Shows the upper-bound branch is gated on NNSMITH_LB being off/unset.
- what would settle it: Inspect the block guarded by line 834 to verify it adds the slice start/end upper bound and that no alternate path adds it when NNSMITH_LB is set.

## nnsmith-F033

**When os.getenv("NNSMITH_G_CONFIG", "1") != "1": The environment variable NNSMITH_G_CONFIG selects which parameter-guidance table GuidedGen uses: "0" = PARAM_CONFIG0 (no parameter guidance at all, only input-shape guidance), "1" = PARAM_CONFIG1, "2" = PARAM_CONFIG2 (pads get symmetric bins). This changes the constraints added in `extra_constraints`/`post_process`, i.e. which models are generated...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:984` in `nnsmith/graph_gen.py::GuidedGen.__init__`
- condition: `os.getenv("NNSMITH_G_CONFIG", "1") != "1"`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: GuidedGen is never instantiated, so the NNSMITH_G_CONFIG selection is dead code.
- code snippet (`nnsmith/graph_gen.py:984`): `}[os.getenv("NNSMITH_G_CONFIG", "1")]`

**Not tested** (`outcome_unsupported`): effect type 'other': the target statement has no effect check yet

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. Line 984 directly uses os.getenv("NNSMITH_G_CONFIG", "1") as a dict key, so the environment variable selects a configuration table. The snippet does not itself show the table names or that they alter extra_constraints/post_process, but the selection mechanism is confirmed; probes can verify the named tables and constraint hooks.
- cited code found at the pinned commit: yes (1 location(s))
- probe `PARAM_CONFIG0` in `nnsmith/graph_gen.py` expected present: **confirmed** (2 hit(s)). Shows config 0 table exists in the same file.
- probe `PARAM_CONFIG1` in `nnsmith/graph_gen.py` expected present: **confirmed** (12 hit(s)). Shows config 1 table exists in the same file.
- probe `PARAM_CONFIG2` in `nnsmith/graph_gen.py` expected present: **confirmed** (5 hit(s)). Shows config 2 table exists in the same file.
- probe `extra_constraints|post_process` in `nnsmith/graph_gen.py` expected present: **confirmed** (8 hit(s)). Shows config can feed constraint or post-processing logic.
- what would settle it: Inspect the dict at graph_gen.py:984 and trace PARAM_CONFIG0/1/2 into extra_constraints/post_process to verify the mapping and generated-model effects.

## nnsmith-F034

**When config is None: If the op class has no entry in param_config, extra_constraints returns an empty list, so no guidance is applied for that op (silently unguided). (nnsmith/graph_gen.py:1016)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:1016` in `nnsmith/graph_gen.py::GuidedGen.extra_constraints`
- condition: `config is None`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: GuidedGen is never instantiated anywhere in the repo, so this branch is dead.
- code snippet (`nnsmith/graph_gen.py:1016`): `if config is None:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:1016
- contrast run: branch not taken at nnsmith/graph_gen.py:1016
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 3); reason recorded: The official entry random_model_gen (graph_gen.py:1061) constructs a PureSymbolGen, whose post_process is SimpleGenerator.post_process (a no-op, line 180) and whose extra_constra…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F034/execution_report.json`

## nnsmith-F035

**When len(cons) == 0 or random.uniform(0, 1) > self.constrain_prob: Guidance constraints for a node are randomly skipped based on constrain_prob, so the mechanism probabilistically falls back to unguided generation for that node. (nnsmith/graph_gen.py:1044)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:1044` in `nnsmith/graph_gen.py::GuidedGen.post_process`
- condition: `len(cons) == 0 or random.uniform(0, 1) > self.constrain_prob`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: GuidedGen.post_process is never reached because GuidedGen is never instantiated.
- code snippet (`nnsmith/graph_gen.py:1044`): `if len(cons) == 0 or random.uniform(0, 1) > self.constrain_prob:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L3 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at nnsmith/graph_gen.py:1044
- contrast run: branch not taken at nnsmith/graph_gen.py:1044
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. the official entry started first but the target line did not run inside it; reason recorded: The official entry random_model_gen is called. It hardcodes PureSymbolGen, which inherits the no-op SimpleGenerator.post_proce…
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F035/execution_report.json`

## nnsmith-F036

**When self.check_sat(*cur_cons) != z3.sat: If the collected guidance constraints are unsatisfiable, the code halves the constraint list repeatedly (line 1053) and finally adds whatever remains (possibly empty), silently dropping guidance rather than rejecting the input. (nnsmith/graph_gen.py:1052)**

- category `paper_stated`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:1052` in `nnsmith/graph_gen.py::GuidedGen.post_process`
- condition: `self.check_sat(*cur_cons) != z3.sat`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: GuidedGen is never instantiated anywhere (random_model_gen uses PureSymbolGen), so this post_process back-off is dead code.
- paper/docs (paper, 3.2 Model Generation, p.6): “if the solver fails to find a satisfiable assignment after adding 𝐶𝑏to the graph’s constraints, we randomly drop half of the constraints and retry, until it succeeds (Line 18).”
- paper/docs (paper, 3.2 Model Generation, p.6): “17 while ¬𝑀.solver.try_add_constraints(𝐶𝑏) do 18 𝐶𝑏←randomly select |𝐶𝑏| 2 constraints in 𝐶𝑏”
- code snippet (`nnsmith/graph_gen.py:1052`): `while self.check_sat(*cur_cons) != z3.sat:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:1052
- contrast run: branch not taken at nnsmith/graph_gen.py:1052
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: random_model_gen (call_chain[0]) constructs PureSymbolGen, whose post_process is the inherited no-op SimpleGenerator.post_process; the target GuidedGen.post_process is never reac…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F036/execution_report.json`

## nnsmith-F037

**When len(cur_cons) == 0: When all guidance constraints are dropped due to unsat, the loop breaks and self.solver.add(cur_cons) adds an empty list, so generation proceeds with no guidance applied. (nnsmith/graph_gen.py:1054)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/graph_gen.py:1054` in `nnsmith/graph_gen.py::GuidedGen.post_process`
- condition: `len(cur_cons) == 0`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: GuidedGen.post_process is never reached because GuidedGen is never instantiated.
- code snippet (`nnsmith/graph_gen.py:1054`): `if len(cur_cons) == 0:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/graph_gen.py:1054
- contrast run: branch not taken at nnsmith/graph_gen.py:1054
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 2); reason recorded: The step-4 call chain is synthetic: it pairs the same-file artifact entry random_model_gen with the target function. In the pinned commit random_model_gen constructs PureSymbolGe…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F037/execution_report.json`

## nnsmith-F023

**When self.differentiable is False: The variant is decided by a single probe forward pass on random inputs: `self.net.differentiable` is set by SymbolNet.forward (it becomes False as soon as any op is non-differentiable or a numeric check fails). If that one random probe happens to hit a non-differentiable path, `search_one` (line 107) silently falls back to `SamplingSearch.search_one` for all s...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/materialize/torch/input_gen.py:98` in `nnsmith/materialize/torch/input_gen.py::PracticalHybridSearch.__init__`
- condition: `self.differentiable is False`
- code snippet (`nnsmith/materialize/torch/input_gen.py:98`): `self.differentiable = self.net.differentiable`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only shown evidence is an assignment copying net.differentiable. It does not show a random probe forward pass, that any non-differentiable op flips the flag, or that search_one falls back to SamplingSearch. The fallback and probe behavior are central, so the finding is not established by the snippet.
- cited code found at the pinned commit: yes (1 location(s))
- probe `SamplingSearch\.search_one` in `nnsmith/materialize/torch/input_gen.py` expected present: **confirmed** (1 hit(s)). Fallback call exists in this file, supporting the silent fallback claim.
- probe `def search_one` in `nnsmith/materialize/torch/input_gen.py` expected present: **confirmed** (4 hit(s)). search_one is defined here; its line 107 context can be inspected.
- probe `self\.differentiable\s*=\s*self\.net\.differentiable` in `nnsmith/materialize/torch/input_gen.py` expected present: **confirmed** (1 hit(s)). Assignment shown; differentiable mirrors net, but not probe behavior.
- what would settle it: Inspect search_one and SymbolNet.forward to verify whether a single random probe sets net.differentiable and triggers SamplingSearch fallback.

## nnsmith-F026

**When output_tensors[i].grad_fn is None: `differentiable` is reset to True at the start of every forward (line 313) and AND-ed with each op output's grad_fn. PracticalHybridSearch.__init__ reads this flag after one probe forward, so a single non-differentiable op (or a non-float input) permanently disables the gradient search for the whole model. (nnsmith/materialize/torch/symbolnet.py:358)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:358` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.forward`
- condition: `output_tensors[i].grad_fn is None`
- code snippet (`nnsmith/materialize/torch/symbolnet.py:358`): `self.differentiable &= output_tensors[i].grad_fn is not None`

**Not tested** (`outcome_unsupported`): effect type 'other': the target assigns a value; the claimed effect is what that value changes later, which needs a differential check of outputs (the assignment itself would differ trivially)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Line 358 confirms the AND with grad_fn, so a None grad_fn clears the flag. But the evidence does not show the reset at line 313 or that PracticalHybridSearch.__init__ reads the flag after one probe. Without those, the claimed permanent disabling is not established; it is only plausible.
- cited code found at the pinned commit: yes (1 location(s))
- probe `self\.differentiable\s*=\s*True` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Shows flag reset to True, supporting the per-forward reset claim.
- probe `self\.differentiable\s*&=` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Confirms the AND assignment with grad_fn, matching the cited line.
- probe `(?s)class\s+PracticalHybridSearch.*?self\.differentiable` in `nnsmith/materialize/torch/symbolnet.py` expected present: **refuted** (0 hit(s)). Shows PracticalHybridSearch references the flag, but not the read timing.
- what would settle it: Inspect the forward reset and PracticalHybridSearch.__init__ to see whether the flag is read once after a probe and never recomputed.

## nnsmith-F038

**When self.check_intermediate_numeric or (self.use_gradient and not self.stop_updating_loss): Constructor/config attributes check_intermediate_numeric, use_gradient and stop_updating_loss decide whether the numeric-validity check and loss-based input search run at all; when false, the whole NaN/Inf detection and loss-update mechanism is skipped. (nnsmith/materialize/torch/symbolnet.py:382)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:382` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.forward`
- condition: `self.check_intermediate_numeric or (self.use_gradient and not self.stop_updating_loss)`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: The real condition is check_intermediate_numeric or (use_gradient and not stop_updating_loss), and invalid_found_last is reset to False at the start of every forward, so the claimed dependence on earlier state does not exist.
- code snippet (`nnsmith/materialize/torch/symbolnet.py:382`): `if self.check_intermediate_numeric or (self.use_gradient and (not self.stop_updating_loss)):`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: branch taken at nnsmith/materialize/torch/symbolnet.py:382
- contrast run: branch not taken at nnsmith/materialize/torch/symbolnet.py:382
- open doubts:
  - D3 oracle can see the effect: *residual*. only 3 mutants (< n_min=4); killed 3
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: PracticalHybridSearch.__init__ calls the real SymbolNet.forward to test differentiability before search_one starts; that forward evaluates the target guard with the constructed a…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/nnsmith/nnsmith-F038/execution_report.json`

## nnsmith-F007

**When loss_fn.dispatch(type(op)) is not None: If an op produces NaN/Inf but has no registered loss function, ConstraintCheck.true at line 403 fails with 'op=... has no torch_loss but produces NaN or INF!', aborting the search. (nnsmith/materialize/torch/symbolnet.py:385)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:385` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.forward`
- condition: `loss_fn.dispatch(type(op)) is not None`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: When gradient search is running and an op with no registered loss function produces NaN/Inf, a ConstraintError ends the gradient search, so such ops cannot be repaired.
- code snippet (`nnsmith/materialize/torch/symbolnet.py:385`): `if loss_fn.dispatch(type(op)) is not None:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Only line 385 is shown; it tests `loss_fn.dispatch(type(op)) is not None`, which is the opposite of 'no registered loss function'. The claimed line 403 ConstraintCheck.true and abort message are not in the evidence, so the failure behavior cannot be confirmed.
- cited code found at the pinned commit: yes (1 location(s))
- probe `has no torch_loss but produces NaN or INF` in `nnsmith/materialize/torch/symbolnet.py` expected present: **refuted** (0 hit(s)). A hit shows the claimed abort message exists in the file.
- probe `ConstraintCheck\.true\([\s\S]{0,200}has no torch_loss` in `nnsmith/materialize/torch/symbolnet.py` expected present: **refuted** (0 hit(s)). A hit shows the message is used in a ConstraintCheck.true call.
- probe `if loss_fn\.dispatch\(type\(op\)\) is not None:` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Confirms the cited condition is present as shown.
- what would settle it: A text search for the exact abort message and the ConstraintCheck.true call near line 403 would settle whether the claimed failure exists.

## nnsmith-F027

**When vul_op_loss is None: When an op produces NaN/Inf but has no registered loss function (`loss_fn.dispatch(type(op)) is None`), the constraint check raises ConstraintError, which `grad_input_gen` catches at line 268 and turns into `break` (line 286) — the gradient search aborts and returns None, so the caller silently falls back to random sampling for that model. (nnsmith/materialize/torch/sy...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:403` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.forward`
- condition: `vul_op_loss is None`
- code snippet (`nnsmith/materialize/torch/symbolnet.py:403`): `ConstraintCheck.true(vul_op_loss is not None, f'op={op} has no `torch_loss` but produces NaN or INF!')`

**Not tested** (`outcome_unsupported`): effect type 'other': the target is a call whose effect is not an exception at that line (for example a check that returns False)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The only shown code is a single ConstraintCheck.true call at line 403. It does not show the vul_op_loss None branch, the ConstraintError catch, the break at line 286, a None return, or any caller fallback to random sampling. No paper evidence is recorded. The claim may be true, but the displayed evidence is insufficient to establish it.
- cited code found at the pinned commit: yes (1 location(s))
- probe `vul_op_loss\s+is\s+None` in `nnsmith/materialize/torch/symbolnet.py` expected present: **refuted** (0 hit(s)). Shows whether the claimed None branch exists in this file.
- probe `except\s+ConstraintError[\s\S]{0,300}?break` in `nnsmith/materialize/torch/symbolnet.py` expected present: **refuted** (0 hit(s)). Shows whether ConstraintError is caught and followed nearby by break.
- probe `grad_input_gen` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Confirms the named function exists, but not its full control flow.
- probe `return\s+None` in `nnsmith/materialize/torch/symbolnet.py` expected present: **refuted** (0 hit(s)). Shows a None return exists, but not that it follows this path.
- what would settle it: Trace grad_input_gen and its callers in symbolnet.py to verify the ConstraintError path, break, None return, and random-sampling fallback.

## nnsmith-F008

**When self.loss is not None: If two vulnerable ops both produce NaN/Inf in the same forward pass, the second one trips this check and raises ConstraintError, which aborts the gradient search (caught in grad_input_gen, line 268 -> break) instead of optimising for either loss. (nnsmith/materialize/torch/symbolnet.py:421)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:421` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.forward`
- condition: `self.loss is not None`
- code snippet (`nnsmith/materialize/torch/symbolnet.py:421`): `ConstraintCheck.true(self.loss is None, 'Multiple loss detected!')`

**Not tested** (`outcome_unsupported`): effect type 'other': the target is a call whose effect is not an exception at that line (for example a check that returns False)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. Line 421 confirms a guard that raises when self.loss is already set, but the shown evidence does not establish that NaN/Inf sets self.loss, that two vulnerable ops trigger it, or that grad_input_gen catches ConstraintError and breaks. The full causal claim is therefore not verifiable from the single line.
- cited code found at the pinned commit: yes (1 location(s))
- probe `ConstraintCheck\.true\(self\.loss is None, "Multiple loss detected!"\)` in `nnsmith/materialize/torch/symbolnet.py` expected present: **confirmed** (1 hit(s)). Confirms the multiple-loss guard exists at line 421.
- what would settle it: Inject NaN/Inf into two vulnerable ops and trace whether self.loss is set twice and whether grad_input_gen catches ConstraintError and breaks.

