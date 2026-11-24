# Confidence specification (proposal v0, pending confirmation)

Status: **Confirmed and implemented** (Shanghao approved the four items in §10 on 2026-11-11). This replaces the "weighted geometric mean" in `SCORECARD.md` §3 to §5. See §11 for differences between the implementation and proposal.

This arose from Shanghao's three requirements: (1) The main project is an agent, not a case for one paper. (2) Confidence needs strict, clear rules based on existing software testing concepts and methods, without reinventing them. (3) With the rules fixed, use better agent skills, harnesses, and workflows to obtain higher confidence.

## 1. Problems with the existing scorecard

| Problem | Details |
|---|---|
| Numbers have no meaning | The weights 0.15/0.20, floor 0.05, mock penalties 0.4/0.05, and thresholds 0.7/0.8 are initial values. The final score is neither a probability nor associated with a measurement scale |
| Treating "not done" as "measured as 0.05" | Mutation and replay were not run, yet contribute 0.05 to the geometric mean. Not assessed and measurement failure are different |
| Compensatory aggregation | The geometric mean still allows a high score on one item to offset a low score on another, concealing what is missing |
| Two questions combined | "How well was the test done?" and "Is the verdict correct?" are combined into one score |
| Case-specific heuristics | Adjacent points use "a difference of 1 or a factor of 2", which only makes sense for F01 and F07 |
| Cannot be calibrated | Without ground-truth samples, we cannot say "how likely is a verdict at the high level to be correct?" |

## 2. Principles

1. **Confidence answers one question: how confident are we that the verdict is correct?** It measures neither the importance of a limitation nor the quality of the test's presentation.
2. **Organize evidence by defeaters (reasons that could overturn the verdict), not a weighted sum.** The method comes from Assurance 2.0 and eliminative argumentation (Bloomfield, Rushby; arXiv 2004.10474, 2205.04522, 2405.15800 verified): list all reasons the verdict might be wrong, then eliminate them one by one with evidence; record those that cannot be eliminated as residual doubts.
3. **Each defeater corresponds to an existing testing concept and a deterministic check.** The harness performs the checks; the agent cannot self-report them.
4. **Distinguish four states instead of collapsing them into one number.** `eliminated` (eliminated by measurement), `residual` (argument only, no measurement), `open` (not assessed), `refuted` (check failed).
5. **A rule table determines the level; its parameters are in a profile file, each marked with its source or as a "policy value".** The same evidence and profile yield the same level.
6. **Calibrate the meaning of levels against a ground-truth benchmark**: use fault injection to create samples where "limitation exists/does not exist" is known, and calculate the verdict accuracy and confidence interval at each level. Before calibration, levels are ordinal only, and reports must say "uncalibrated".

## 3. Claim under test

`C`: under condition `cond`, the code exhibits effect `eff` at location `loc` (corresponding to `Finding` + `Region`). A `yes` verdict means "C holds", `no` means "C does not hold", and `inconclusive` means "insufficient evidence to decide".

## 4. Defeater table

The RIPR chain comes from Ammann & Offutt; the first three steps of PIE come from Voas 1992 (the RIPR source has been verified; the details of Voas 1992 are recalled from memory and have not been checked individually).

| # | Defeater: how the verdict could be wrong | Related concept | Harness check | Condition for `eliminated` | Category |
|---|---|---|---|---|---|
| D1 | The target statement never executes | Reachability | Target line event | The positive case executes the target line | Fatal |
| D2 | It executes, but the condition does not hold as expected | Infection | Evaluate `cond` (or a predicate registered in advance by the agent) on the target line's local variables | True for the positive case and false for the negative case | Fatal |
| D3 | The oracle cannot see the effect, or sees something it should not | Propagation, Revealability; mutation testing measures oracle adequacy | Mutate the target verdict (negation, comparison replacement, assert deletion, constant ±1); the test result must flip | Mutant count ≥ `n_min`, and Wilson lower bound on kill rate ≥ `kill_lb` | Important |
| D4 | The oracle itself is unreliable | Test oracle problem; Barr et al. classify oracles as specified, derived, implicit, human (IEEE TSE 41(5), 2015 verified) | Check oracle type and evidence: does it point to `Region.location`; was it registered in advance | Specified and location equals `Region.location`, with registration hash before the first run | Fatal (below implicit or unregistered) |
| D5 | Positive and negative cases differ in more than one factor, or the negative case is far from the boundary | Ceteris paribus; boundary value analysis, ON/OFF points in domain testing (White & Cohen 1980, Jeng & Weyuker 1994); delta debugging (Zeller & Hildebrandt 2002) | Input difference set; **the harness itself bisects along the boundary variable, verifies that the result flips only once, and finds ON/OFF points** | Difference set size is 1, and the agent's negative case equals the OFF point | Important |
| D6 | An observation depends on an untrustworthy test double | Test double classification (Meszaros: dummy, stub, spy, mock, fake; Fowler); simulation and reference implementations | **Causal dependency analysis**: which doubles were accessed before an observation was produced | See §5 | Important |
| D7 | Observation changes behavior | Probe effect (Gait 1986) | Compare observable results with and without hooks | Identical | Fatal |
| D8 | Results are unstable | Flaky tests (Luo et al., FSE 2014) | Fixed seed, single thread, offline; repeat `n_rep` times and compare **normalized trace hashes** | All identical; report Rule of three upper bound 3/n | Important |
| D9 | Results differ in another environment | Reproducibility; clean-environment replay | Replay from `SCORECARD.md` §3.6 | Same verdict on replay | Important |
| D10 | Behavior differs at reduced scale | External validity (representativeness) | Replay the positive case at full scale; the harness also probes the target line at full scale when bisecting the negative case boundary | The target verdict has the same truth value at both scales | Important |
| D11 | The code under test was modified | Fidelity of the system under test | AST diff (target statement, verdict expression, call-chain functions) | Target statement unchanged, proportion of other modified statements ≤ `mod_max` | Fatal (target statement modified) |
| D12 | Region, location, or condition itself is wrong (upstream) | Input validity | Compare snippet verbatim | Matches the corresponding repository lines | Fatal |
| D13 | Input is outside the paper's scope | Scope gate (T9) | `scope_status` | `in_scope` or `scope_edge` | Informational |

`Finding.confidence` (mechanical, llm_assisted) remains separately reported and is not incorporated.

## 5. Test double dependencies: states instead of multiplicative weights (D6)

Multipliers such as 0.9, 0.75, and 0.3 are no longer used. Each observation records its **causal prefix**: which doubles were accessed before it was produced. Evidence states for observations:

| State | Condition |
|---|---|
| `direct` | No doubles in the causal prefix (or only a spy, which records without changing behavior) |
| `simulated:reference` | The prefix contains only doubles that call the repository's reference implementation |
| `simulated:fake` | Contains a custom implementation that performs real computation (fake) |
| `simulated:stub` | Contains a double that returns fixed values (stub, dummy) |

The verdict depends only on `direct` observations. `simulated:*` observations are listed as **supplementary information**, clearly labeled, and excluded from the verdict. For example, in F07, the positive case throwing an exception at the target line is `direct`; the negative case "continues and returns `Tensor(1,512,2,128)`" is `simulated:fake`.

This has two benefits: there is no need to invent a number for each type of double; if the agent wants more conclusions to be `direct`, it must reduce doubles before the target line rather than increase a weight.

## 6. Level rules

| Level | Conditions (all required) |
|---|---|
| `invalid` | Any fatal defeater is `refuted`. The verdict is forced to `inconclusive` |
| `L1 indicative` | None is `refuted`; all fatal items are `eliminated`; important items include `open` |
| `L2 supported` | Fatal items and D3, D8, D9 are all `eliminated`; `residual` is allowed for D5, D6, D10 |
| `L3 established` | All defeaters are `eliminated`, or are items for which residual is allowed (D13). All observations on which the verdict depends are `direct` |

For a `no` verdict, an additional rule applies: D3 must be `eliminated`, otherwise the maximum is `L1`. Proving "no effect" requires showing that the oracle can see the effect when it exists (the purpose of mutation testing).

Profile parameters (initial values, all marked "policy value" unless otherwise noted): `n_min = 4`, `kill_lb = 0.5` (Wilson lower bound; Wilson 1927), `n_rep = 5`, `mod_max = 0.05`. Adjust after calibration.

## 7. Calibration and validity (how to show the rules are meaningful)

1. **A benchmark with ground truth.** Inject faults into each artifact: delete asserts, change thresholds, or negate conditions to create versions where whether the "limitation exists/does not exist" is known. Empirical studies examine whether mutations can substitute for real faults (Andrews et al. ICSE 2005; Just et al. FSE 2014), but their conclusions are not unconditional; reports must state the limitations.
2. **Metrics.** Verdict accuracy and Wilson interval at each level; types of incorrect verdict (false positive, false negative); Brier score and reliability diagram (Brier 1950; Guo et al. ICML 2017 used these for neural network calibration; we borrow their method).
3. **Form honesty.** Report the agreement rate between agent declarations and harness recalculations separately; do not incorporate it into the level.
4. **Ablation.** Disable harness services one at a time (mutation, boundary bisection, scale checks, causal dependency analysis) and observe how the share and accuracy of each level change. This experiment answers "how much confidence does the harness design bring?"

The method names and references in points 1 to 3 above, Brier 1950, Guo et al. 2017, Just et al. 2014, Andrews et al. 2005, Luo et al. 2014, Gait 1986, White & Cohen 1980, and Zeller & Hildebrandt 2002 come from memory and were not individually verified in this session. Check the original papers before using them in the paper.

## 8. How to obtain higher confidence with fixed rules

Each `open` or `residual` defeater has an assigned party responsible for eliminating it:

| defeater | What the harness can do automatically | Agent obligations (a checklist in the skill) | Repair after failure (workflow loop) |
|---|---|---|---|
| D3 | Generate and run mutants; calculate the kill rate | Write the oracle as an assertion pointing to a specific location; avoid checking only that "an exception occurred" | Low kill rate: show surviving mutants; the agent strengthens the oracle |
| D5 | Bisect along the boundary variable, verify a single flip, and provide ON/OFF points | Identify the boundary variable and free parameters and explain why | Contrast is not the OFF point: provide the OFF point; the agent replaces the contrast |
| D6 | Analyze causal dependencies; provide spy and simulator templates | Declare the type of each double and the reason; prefer placing doubles after the target line | Observation depends on a stub: suggest a fake or reference implementation, or move the double later |
| D8, D9 | Repeat runs, normalize trace hashes, replay in a clean environment | Register all commands; fix the seed | Instability: locate sources of nondeterminism (threads, hash seed, random numbers) |
| D10 | Replay the target line at full scale | Explain why the behavior is invariant under scaling | Different verdict at full scale: undo scaling |
| D2 | Execute the predicate | Write an executable predicate in advance when the condition cannot be evaluated directly | Predicate is not equivalent to the Region condition: refer for human review |

The workflow is therefore: **plan → register (oracle, expectations, double declarations) → execute → harness audit → repair loop**. The audit produces a "defect list": the state of each defeater and what to do next. The agent addresses only uneliminated defeaters within its budget. It stops when the target level is reached, the budget is exhausted, or the remaining defeaters cannot be eliminated by the agent (for example, an upstream Region is wrong).

## 9. Relationship to the existing implementation

Keep: RIPR measurements (trace, condition evaluation, verdict), AST diff, probe effect, spies, form audit, causal prefix (the current `information` is its precursor), and separate reporting of `Finding.confidence`.

Changes:
1. `scoring.py`: remove the weighted geometric mean and final score; replace them with a defeater state table and the rule table in §6. The nine examples in `scoring_prototype.py` are no longer regression tests; replace them with tests of "the defeater states and level for each example".
2. `models.py`: replace `Scorecard` with `DefeaterTable` plus `level`; replace `InfoItem.confidence` with evidence state.
3. Add `bva.py` (boundary bisection), `mutate.py`, and `replay.py` (already planned for P1b).
4. Replace case-specific code (adjacent-point heuristics and effect verdicts that support only `reject`) with pluggable effect checkers.

The seven diagnostic dimensions may remain as "diagnostic readings", but are no longer combined into a final score.

## 10. Decisions for Shanghao

1. Whether to abandon the numerical final score and report only the level and defeater table (see §1 for the reasons; recommend abandoning it).
2. Whether the level definitions and initial profile values in §6 are acceptable.
3. Whether the verdict depends only on `direct` observations (§5). This downgrades the "normal return" of the F07 and F01 contrast cases to supplementary information.
4. The order of the next steps: implement §9 first (change scoring, add bva, mutate, replay), then write the agent skill and workflow; or write the agent part first. The former is recommended because the agent repair loop needs the harness to provide a defect list.

## 11. Differences between implementation and proposal (2026-11-11)

Code: `confidence.py` (rules), `profile.py` (parameters and sources), `stats.py` (Wilson, Rule of three), `mutate.py`, `bva.py`, `harness.py` (service orchestration).

| Item | Proposal | Implementation |
|---|---|---|
| Level | invalid, L1 to L3 | Adds **L0**: no fatal defeater is refuted, but a fatal item remains `open` (e.g. no probe effect check). The level is `n/a` when the verdict is `inconclusive` |
| D14 | None | Adds "whether execution went through the official entry" (T4 integration level). Entry at `call_chain[0]` is `eliminated`; deeper entry with `execution.entry_reason` is `residual`; no reason is `refuted`. Classified as important |
| D2 | Refer to human review if the predicate cannot be evaluated | An agent-written predicate holds for the Region condition: `residual` (faithfulness of the translation is unverified), hence at most L1. Condition cannot be evaluated at all and no predicate exists: `open` |
| D4 | Registration below specified | Verified tier O1/O2 or unregistered: `refuted`; O3 or oracle changed after registration: `residual`; O4, registered before the first run, with 0 modifications: `eliminated`. The registration hash covers only **oracle, expected result, and condition predicate** (the wording of SCORECARD T1), not inputs, doubles, or scale |
| D5 | Harness bisects to find ON/OFF points | Implemented as **adjacent-point probing**: at full witness scale, try ±`probe_step` on the contrast's boundary variable; if at least one side has an effect, the contrast is adjacent to the effect region. Effects on both sides indicate a one-point no-effect region (a `!=` guard). A non-integer boundary variable or more than one differing factor is `residual`. A `no` verdict requires only one differing factor |
| D6 | direct and three simulated states | All verdict-dependent observations direct: `eliminated`; includes reference or fake: `residual` (at most L2); includes stub: `refuted` (at most L1) |
| D8 | Identical trace hashes | Normalized hash covers status, exception type and location, return-value summary, local-variable summaries at target-line hits, call-chain function start order, and executed line set; excludes sequence numbers and elapsed time |
| D9 | Replay agent commands | The harness replays **its own invocation** in a **fresh checkout of the pinned commit** and a **fresh attempt copy**; it does not execute shell strings written by the agent in `replay_commands` (otherwise an attempt could make the harness run arbitrary commands). `replay_commands` is only a record |
| D10 | Full-scale bisection | Probe the positive and contrast cases once each at full scale (stop at the target verdict); both effects must match the scaled run |
| Probe runs | None | D5, D3, and D10 use probes that "stop at the target verdict" (`tracer.StopProbe`). Probes do not enter the verdict or execute code after the target |
| Numerical diagnostic readings | May retain | Not retained. `Scorecard`, `EvidenceRecord`, `scoring.py`, `s_mod`, etc. were all removed; `scoring_prototype.py` remains in place as a historical file |

Profile defaults: `n_min=4`, `kill_lb=0.5`, `n_rep=5`, `mod_max=0.05`, `probe_step=1`. Sources are all recorded in `profile.py`, and reports include the profile used.

### Known limitations

1. **L3 currently means only "all 14 defeaters we could think of have been measured and eliminated"; it does not mean the verdict is necessarily correct.** Until a fault-injection benchmark exists, reports state `calibrated=false`.
2. Effect verdicts implement only `reject` (an exception at the target location). `fallback`, `mechanism_variant`, `state_dependent`, etc. return `not_run`.
3. D3 mutations apply only to assert, raise, if, and while; adjacent-point probing works only for integer boundary variables.
4. For assert targets, the probe stops early. A mutation "kill" is strong mutation at the target: any change from `yes` counts as a kill, including a crash caused by the mutant. Equivalent mutants are not excluded, so the Wilson lower bound is used instead of requiring 100%.
5. Heap corruption, threads, and nondeterministic libraries: D8 can compare only observed traces; it cannot prove nondeterminism absent. Reports provide the Rule of three upper bound (0.6 for 5 runs, very weak evidence). Reducing the bound to 0.1 requires 30 runs, controlled by profile `n_rep`.

## 12. Fault-injection benchmark v0 (`results/bench/`, 2026-11-11)

`python -m checklimits bench` creates 9 variants for each of three FlexPrefill findings (F07, F01, F04), plus 4 variants that degrade attempt quality, for 31 cases. Variants are written to a new commit in the cloned repository, which becomes the system under test. Each case has ground truth `claim_true` (whether "the witness input is rejected at that line and the adjacent input is not rejected" holds in the variant). A `yes`/`no` verdict is a "decision"; `inconclusive` is an "abstention".

| Variant | Ground truth | What it tests |
|---|---|---|
| orig | True | Control |
| delete-stale / relax-stale | False | Region was not updated with the variant; D12 should catch it |
| delete-snip / relax-snip | False | Region snippet was updated, but the condition still describes the original finding (extractor misread the condition). Should return `no` |
| invert-snip | False | Boundary direction reversed; should not return `yes` |
| otherexc-snip | True | Still rejects, but raises `ValueError`. The oracle recognizes only `AssertionError`; known to return `no` (false negative) |
| shifted / collide | True | Location invalid; should abstain |
| att-fake-einops / att-no-location | True | Verdict should remain `yes`, level should fall below L1 |
| att-scale-dependent | True | Behavior changes after scaling; should abstain |
| att-false-claims | True | Form honesty should decrease (`form_integrity`), verdict unaffected |

Results (one full run in addition to 137 unit tests, about 36 seconds per case, 3 in parallel):

| Level | case | Decisions | Correct | Accuracy | Wilson lower bound |
|---|---|---|---|---|---|
| L3 | 3 | 3 | 3 | 1.0 | 0.44 |
| L1 | 12 | 12 | 9 | 0.75 | 0.47 |
| invalid | 10 | 0 | 0 | | |
| n/a | 6 | 0 | 0 | | |

- **0 false positives.** All 16 abstentions fell under `invalid` (D12 or D2 refuted) or `n/a`.
- All three false negatives (`*-otherexc-snip`) were L1 with D3 `refuted` (mutants survived; the oracle could not see the effect). `relax-snip`, also with D3 refuted, was judged correctly.
- The sample is too small (15 decisions), and Wilson intervals are wide. This is a smoke test of the rules, not calibration; `calibrated` remains false.

### Problems found by the benchmark

1. **Harness defect (fixed).** The first run of `att-fake-einops` returned L3: the fake module was accessed only during import, and the child cleared the record at the start of each case, so D6 incorrectly reported `direct`. Import-stage records are now retained. A regression test was added (it fails without the fix).
2. **D3 for set guards.** F04's `head_dim in {16,32,64,128}` uses only one contrast (128), so all mutants changing 16, 32, or 64 to another number survived; D3 was refuted and the level was L1. `next_steps` now lists surviving mutants and suggests "add an input for each member". The agent currently supplies only one contrast; this is an agent-layer design problem.
3. **Decision pending: should a `no` verdict become `inconclusive` when D3 is refuted?** The approved rule is "at most L1". The benchmark has 6 cases with `no` + D3 refuted: 3 correct (relax-snip), 3 wrong (otherexc-snip), equivalent to a coin toss. Mutation testing logic says that an oracle unable to see changes at the target cannot prove "no effect". The original SCORECARD G5 required this. Forcing `inconclusive` would turn all 6 into abstentions. This change was proposed after seeing the benchmark, so it needs your confirmation; otherwise it risks tuning the rule to the benchmark.

## 13. Effect types (evening of 2026-11-11)

D1 to D14 apply to all three effect types; only "what counts as an effect" differs (`runner.outcome_support`, `runner.to_observation`):

| `Region.outcome` | Effect | Requirement |
|---|---|---|
| `reject` | Exception at the target location (type from oracle spec) | Any target statement |
| `fallback`, `mechanism_variant` | Branch decision at the target enters the branch body | Target is `if` or `while` |
| `state_dependent` | As above, but only the last driver call counts; earlier `positive_prelude` / `negative_prelude` calls first change state | Target is `if` or `while` |
| Other | Not judged, `not_run` | |

Known gaps (covered by tests; rules are not relaxed for them): adjacent state points cannot be probed, so D5 is at most residual; guards such as `x is None` have fewer than 4 mutants, so D3 is at most residual; preludes before the checked call must run doubles after the target, so D6 is at most residual. Thus `state_dependent` is at most L1 under current rules. Improvements require more mutation operators (`is` and `is not`, `and` and `or`) or adjacent-point probing for state; these are new design decisions.

## 14. Mutation operator set v2 (2026-11-12, Shanghao approved additional operators)

**Added:** swap comparison operators `is` and `is not`, `in` and `not in`; swap logical connectives `and` and `or` (one mutant per connective). Existing condition negation, `==`/`!=`, `<`/`<=`, `>`/`>=` swaps, deletion of `assert`/`raise`, and integer constant ±1 remain unchanged.

**One count was also tightened:** `not (a == b)` and `a != b` (likewise `is` and `in`) are the same mutant. When the entire condition is one such comparison, the swap is no longer counted, as it would double-count and inflate the mutant count used by D3. Previously 1 of F07's 5 mutants was a duplicate; now there are 4 (negation, `1→2`, `1→0`, deletion), with Wilson lower bound 0.51, just above the 0.5 threshold.

**Impact (re-audit of 33 archived agent attempts, without rerunning the agent):**

| | Count |
|---|---|
| Level unchanged | 32 |
| Level decreased | 1 (F053: `if q_len == 1:`, 3 mutants, fewer than `n_min=4`; D3 changed from eliminated to residual and L3 to L1) |
| Level increased | 0 |

The three new operator types raised no levels: among 15 cases with D3 residual, single-comparison guards (`x is None`, `q_len == 1`) already had only one non-equivalent mutant, negation, and member constants ±1 for `x in {...}` guards were already counted. Only compound conditions gain `and`/`or` mutants, and almost none of these 15 are compound. **Thus D3 residual is mainly due to the small number of logically mutable points in these guards, not an overly narrow operator set.** Raising them to L2 requires a rule change (e.g. adjust `n_min` to the number of mutable points, or accept "all non-equivalent mutants killed"); that is a separate decision.

Distribution: 5 cases with 1 mutant, 8 with 2, 2 with 3, 16 with 4 or more, and 2 with no applicable operator (not run).

### Benchmark rerun (2026-11-12)

Rerun all 31 benchmark cases with operator v2 and the current hand-written attempts: verdict categories unchanged (TP 6, TN 6, FN 3, abstentions 16, **still 0 false positives**). F04-orig and F04-relax-snip rose from L1 to L3 **because `extra_negatives` were added to the hand-written F04 attempt after the first benchmark** (one contrast per set-guard member), not because of the operator change. L3 is now 5/5 correct (Wilson lower bound 0.57), L1 7/10 correct, and the three false negatives (`*-otherexc-snip`) remain L1. This is still a smoke test of 15 decisions, not calibration.

## 15. Rule corrections from a second artifact (2026-11-12)

1. **Applicability of `reject` (`runner.outcome_support`).** Judge only when the target can raise an exception: `assert`, `raise`, or `if` / `while` with a `raise` in the branch body. Other statements return `not_run` with a reason, not `no`. Reason: if "the program eventually rejects" is attached to `continue`, an assignment, or a loop condition, "exception at the target location" can never hold, producing a `no` in the wrong direction.
2. **Normalized hash scope (D8, D9).** Include only verdict, condition value, exception, return-value summary, function start order, executed line set, and local values of **names appearing in the Region condition**. Irrelevant locals such as clocks, random numbers, and object addresses no longer make deterministic behavior look unstable. When there is a `condition.py` predicate, still hash all locals (the predicate can read any name).
3. **Module-level targets.** `function == "<module>"` denotes statements executed at import; AST comparison and coverage handle them accordingly. Names beginning with `__` in the module dictionary are not captured.

## 16. Fault-injection benchmark expanded to 82 cases (2026-11-16)

`bench.py` adds a second class of cases: inject repository faults into test packages agents wrote for step 4 Findings (NNSmith F004, F017, F025, F010; FlexPrefill F003, F054, F026). Rules match the first 31 cases: 5 `reject` variants (original, deletion, negation, different exception type, paired with "stale Region" or "current snippet"), 5 branch variants (original, condition replaced with `False`, negation, replaced with `True`, with the same two Regions), plus "stale location" (insert a comment line or a harmless statement). Acceptable result sets were fixed before the run and written in `bench.py`. There are also two test-package faults for NNSmith F004. The original 31 cases were rerun as well.

| | First 31 cases (11-11) | Now 82 cases |
|---|---|---|
| False positives (claim false but verdict `yes`) | 0 | **0** |
| Verdict `yes` | 6, all correct | 15, all correct (7 L3, 8 L1, Wilson lower bounds 0.65 and 0.68) |
| Verdict `no` | 9, 6 correct | 13, 7 correct |
| Abstentions | 16 | 54 |

By verdict and level:

| Verdict / level | Decisions | Correct | Rate | Wilson 95% interval |
|---|---|---|---|---|
| `yes` / L3 | 7 | 7 | 1.00 | 0.65 to 1.00 |
| `yes` / L1 | 8 | 8 | 1.00 | 0.68 to 1.00 |
| `no` / L3 | 1 | 1 | 1.00 | 0.21 to 1.00 |
| **`no` / L1** | **12** | **6** | **0.50** | **0.25 to 0.75** |

Interpretation:

* **No `yes` was wrong.** All 15 `yes` verdicts had true claims. This is the strongest statement the benchmark supports; it is still based on 15 decisions and faults we devised ourselves.
* **L1 `no` is a coin toss.** Of 12 L1 `no` verdicts, 6 were wrong, **all from the same fault**: the claim was true, but the repository replaced `AssertionError` with `ValueError` (`*-otherexc-snip`, now 6 cases versus 3 in the first 31). The oracle recognized only `AssertionError`, so it saw "no expected exception" and returned `no`. D3 (mutation check) was `refuted` for 5 and `residual` for 1. The 11-11 decision was "`no` is at most L1 when D3 is not eliminated; do not force `inconclusive`". These new data are evidence about that decision: half of L1 `no` verdicts in this fault family are wrong. **I did not change the rule** (changing it after seeing the benchmark risks tuning to it); the decision is left to you.
* **More abstentions are not errors.** Three F07, F01, and F04 cases with "guard deleted, Region snippet updated" changed from `no`/L1 to `inconclusive`/n/a: Region says the effect is `reject`, but the target statement is now `pass`. The 11-12 rule "judge `reject` only when the target can raise an exception" (§15) makes them abstain. Their acceptable set is `{no}`, so they are "outside the acceptable set" in the table, but are not incorrect verdicts.
* Results agree across families: 0 false positives in the 31 hand-written pilot cases, 30 NNSmith cases, and 21 FlexPrefill step 4 test-package cases.
* All are small deterministic faults. This remains a smoke test, **not calibration**. The meaning of levels needs an empirical basis from human annotation (`labels` command).

## 17. Agent visibility (2026-11-16, updated 11-17)

* Unreadable in the sandbox: `attempts/`, `results/`, `locks/`, `runs/`, `tests/`, `scripts/`, `scratch/`, `agent_results/`, git history, credentials, `PLAN.md`, `ENV.md`, `KICKOFF_PROMPT.md`, `scoring_prototype.py`, and `AGENT_RESULTS.md`, `BATCH_RESULTS.md`, `NNSMITH_RESULTS.md`, `PREFLIGHT_FLEXPOSIT.md`. `agent_results/` was readable before 11-16 (third addendum to `BATCH_RESULTS.md`).
* White box (default): can read `checklimits/` source, `CONFIDENCE_SPEC.md`, `SCORECARD.md`.
* `--blind` (clean blind test): no harness in the sandbox (the package directory is an empty tmpfs); rules and experiment records are unreadable. `cl` is the client; `task`, `init`, `lint`, `run` are executed by a service outside the sandbox (`agent_service.py`) in the same bwrap sandbox, returning only output. The first 11-16 "blind test" only replaced source with `.pyc`; all five runs read bytecode using `strings`, `marshal`, `dis`, so that version counts only as semi-blind (`EXPERIMENTS.md`).

## 19. D14 requires the target to execute inside the entry (2026-11-17)

Previously D14 checked only whether `call_chain[0]` was the first function started. It now also requires that function still to be running when the target line executes (the tracer records the call stack at each hit, `fidelity.entry_on_stack`). If the entry starts first but the target executes outside it (call the entry once, then call the target function directly): an `entry_reason` gives residual; no reason gives refuted. Module-level targets and hits without a recorded call stack are not checked. See `EXPERIMENTS.md`: "D14 的漏洞" [The D14 loophole] for the discovery and impact on existing results.

Impact on all existing results (re-audited under the new rule): FlexPrefill F008 fell from L3 to L2; NNSmith F035 fell from L3 to L2; other e2e levels were unchanged. The 82 benchmark cases were not rerun (they inject faults and do not involve entry), so the conclusion of 16 decisions and 0 false positives is unaffected, but was not reverified.

## 20. Cross-checking D2 and agent predicates, and the first human baseline (2026-11-17)

The agent can write a `condition.py` predicate in place of Region.condition for D2. The predicate may describe something else. The human baseline (`labels/sheet_shanghao.csv`) found NNSmith F009: Region's condition is `max(left, right) >= W` ("do not add carry at the limit"), while the target statement is `if carry and max(...) < W:`. The agent wrote its predicate to match the statement, reversing trigger and contrast; the harness gave `yes`/L1 with D2 only residual. Now, when a predicate exists, Region.condition is also evaluated (`TargetHit.region_condition_value`): if evaluable and inconsistent with "positive true, contrast false", D2 is refuted; if consistent, D2 is eliminated; if not evaluable, it remains residual. Region.condition is not evaluated when it contains calls (`random.uniform(...)`, `x.size()`), because evaluation would alter the program under test (`tracer._pure_expression`). F009 is now `inconclusive`/`invalid`; F019 and F022 remain residual because their conditions contain calls. Tests cover this.

First baseline numbers (18 of 20 sampled cases received a harness `yes`, after refreshing the key): human judgments that "the assertion holds for the code" were 16/18 (Wilson 0.67 to 0.97), L1 4/6, L2 6/6, L3 6/6. **q2 (test validity) was mostly not assessed:** baseline q2 says `Unverified` because the reviewer did not receive driver source; only F009 was judged `Inconsistent`. `labels/context/` added the full driver for each case. These numbers are not calibration; the sample is 18 and intervals overlap across levels.

## 21. D5 adjacent-point probe retries on timeout (2026-11-17)

NNSmith's `random_model_gen` uses `max_gen_millisec` as a time limit. Under heavy load, adjacent-point probes (`neg+`, `neg-`) can time out before reaching a target verdict, leaving D5 `open` and lowering the level (F035 chain-3 fell from L3 to L1 with 3 parallel workers). Now `harness._run_bva` separately retries probes without a target verdict up to `BVA_RETRIES = 2` times. Only undecided probes are rerun: decided results are not overwritten; retries can only turn `open` into a measured result, not reverse a level's judgment. Probes still undecided remain `open`. No thresholds or rules changed, so the benchmark and `results/e2e/` were not rerun. Two tests cover this (`test_mutate_bva.py`). This does not "prove" the load issue is gone: parallel re-audit on the real machine has not been repeated; `--workers 1` or 2 is still recommended when it is.

## 22. Analysis channel: analyze untestable Findings at separate levels (2026-11-18)

A `not_run` Finding (`no_code_location`, `outcome_unsupported`, paper-only) no longer has only a one-line reason. `checklimits analyze` / `pipeline analyze` / `pipeline e2e` (default) adds an `analysis` block to each (`report.json` optional field, no contract version bump). This **is not a test**: it never has `yes`/`no` or an L level.

Three steps, in decreasing order of credibility:
1. **Static evidence check (deterministic):** the file cited by the Finding exists at the pinned commit, the line number is in range, and the cited snippet is there.
2. **Probes (run by the harness):** the language model can propose regex probes ("the script has no `wget`"). Probes can inspect only files cited by the Finding; an `absent` probe must include a `control` regex that matches in the same file, otherwise it is `unanchored` and does not count ("not found" is too easy to satisfy).
3. **Language model interpretation:** `supports` / `contradicts` / `unclear`, with reasons; answers are cached.

Levels (uncalibrated, on a different scale from L levels):

| Level | Condition |
|---|---|
| A2 | Cited code found, at least one probe ran and agrees with the interpretation |
| A1 | Text interpretation only: paper-only, no repository, or no probe can be written |
| A0 | Evidence cannot be grounded (cited file or line absent), interpretation contradicts a probe, or model gave no usable answer |

**Paper-only** (`checklimits paper-only` / `pipeline paper-only`, e.g. Tessera with no public code): the model reads the full PDF and lists limitations readers can establish from the text (assumptions, evaluation scope, missing comparisons, numerical inconsistencies). The harness checks that each quotation **appears verbatim in the PDF**; otherwise it discards and counts the entire item. A candidate may include an arithmetic check, with every number appearing in the quotation, evaluated by the harness. Maximum level A1. Records are numbered `<id>-P001…`, with `not_run.code = no_code_location` and `finding.category = paper_only:<kind>`; they do not use the step 4 schema.

Limitations: probes are text searches, not semantic analysis; model-proposed probes may choose the wrong file or regex; A2 says only "the text found agrees with the interpretation". No human verification or calibration.

## 23. Accelerator code doubles must demonstrate fidelity (2026-11-18)

Lack of a GPU is not a reason to abandon a Finding. The agent can use a CPU double (`sim.py`) for a CUDA/Triton kernel or hardware block, and declare how to show that the double computes what the kernel computes with `MockDecl.sim_check = "check.py::fn"`: `fn(sim)` returns `{"ok","detail","kind"}`. This can compare numerical results with a CPU reference implementation on small random inputs, check invariants (softmax rows sum to 1, mask applies, shape), or use sympy / z3 for a symbolic proof of the formula.

The agent writes the check, so the harness does not trust it directly: `simcheck.py` first runs it on the double in a child process (must be ok), then on each "broken double" (output scaled up, negated, zeroed). A check that still passes after damage cannot see errors and is marked `vacuous`. States: `agrees` / `disagrees` / `vacuous` / `error`. **Only `disagrees` changes the level** (D6 refuted); `agrees` is recorded only as D6 evidence, while the double's evidence state remains determined by `sim_class` (`simulated:*`, level cap unchanged).

Validation: after adding `sim_check` to the FlexPrefill F07 `bnhd_pool` double, it was `agrees` in the real harness (`tests/test_simcheck.py` also has 5 unit tests: agrees, disagrees, vacuous, error, undeclared). An agent has not yet written and run `sim_check` itself for a new Finding that truly needs a GPU.
