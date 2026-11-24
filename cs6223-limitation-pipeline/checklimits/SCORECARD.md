# Test Process Scorecard and Confidence Score (check_limits)

Status: design draft, 2026-11-11. **The scoring column in §3 and §4, §5, and §7 have been superseded by `CONFIDENCE_SPEC.md`** (there is no longer a final score or weighted geometric mean); the test design requirements T1 through T9 in §2, the decision table in §3.5, the replay definition in §3.6, and the form in §6 remain valid. Weights and thresholds are initial values without a basis in the literature and must be calibrated using fault injection (see §8).
Reference implementation: `scoring_prototype.py` (standard library only; it has been run, but the examples are constructed, not measured).

## 1. Principles

1. **The code agent fills in the form; the harness audits and calculates.** Each item the agent fills in is either a "claim" that the harness can recompute from run artifacts or a "classification" with fixed options and decision criteria. There is no "self-rating from 1 to 10".
2. **Some metrics are measured only by the harness and are not filled in by the agent** (mutation checks, repeated runs, replay, probe impact, and coverage). The agent cannot falsely report them.
3. **When a claim disagrees with the harness recomputation, the harness result takes precedence.** The disagreement counts against the "form consistency rate" and lowers the final score.
4. The total confidence score is a deterministic function of these metrics; it is not supplied by an LLM.

## 2. Test design requirements (the agent must comply)

| ID | Requirement | Corresponding test concept |
|---|---|---|
| T1 | Write down the oracle and expected results (positive and negative cases) before running; the harness records their hash. Changes to the oracle after the run are counted | Test-first design; prevent fitting the oracle after the fact |
| T2 | The positive and negative cases differ by only one factor, and the negative case uses an adjacent point on the other side of the boundary | Boundary value analysis; minimal pair (ceteris paribus) |
| T3 | Take inputs from `witness_hint`; disclose and justify each parameter chosen by the agent (such as the number of heads) | Input provenance; disclosure of free parameters |
| T4 | Prefer the official entry point; call a deeper function only if the reason is recorded | Integration level (unit vs system test) |
| T5 | Do not modify repository code; use only external mocks for environment substitutions and register them | Fidelity to the system under test |
| T6 | Offline, fixed random seed, fixed commit, CPU only | Reproducibility; hermeticity |
| T7 | The oracle comes from runtime signals (exceptions, trace events, numerical differences) and points to `Region.location` | Decidability of the test oracle |
| T8 | Record all commands so the harness can replay them in a clean environment | Replayability; protection against environment drift |
| T9 | Inputs fall within the paper's scope; an `out_of_scope` finding is recorded only and excluded from the main results | Scope gate |

## 3. Metric definitions

The framework is the **RIPR model** (reachability, infection, propagation, revealability): a test that demonstrates a finding must in sequence execute the target location, satisfy the condition, produce the effect, and make the effect visible to the oracle.

| Dimension | Weight | What it measures | Source | Score (0 to 1) |
|---|---|---|---|---|
| **reach** reachability and decision coverage | 0.15 | The target statement executes; both outcomes (true and false) of the target decision are covered | harness trace | `0.5×[target line executed] + 0.5×(number of decision outcomes seen/2)` |
| **infect** condition verified | 0.15 | Evaluate `Region.condition.expr` on runtime variables: true for the positive case and false for the negative case | Harness captures variables at the target line and evaluates; agent claims, harness recomputes | `0.5×[positive case is true] + 0.5×[negative case is false]`; if it cannot be evaluated (e.g. `otherwise`), score 0 and annotate |
| **oracle** oracle strength | 0.20 | Oracle type and whether it was registered in advance | Agent classifies, harness checks | Tier score × `max(0, 1 − 0.25×number of changes after the run)`; tiers below |
| **control** control quality | 0.15 | Positive and negative cases behave differently, with few differing factors and adjacent points | Harness compares both inputs and behaviors | Score only if behaviors differ; 1 differing factor: 1.0, 2: 0.7, 3 or more: 0.4; multiply by the adjacent-point factor (adjacent: 1.0, non-adjacent or unknown: 0.8) |
| **mutation** mutation sensitivity | 0.10 | Mutate the target decision; the test result should flip | Harness only | `(number killed/number generated) × min(1, number generated/3)`; score 0 if not run |
| **fidelity** fidelity | 0.15 | See below; product of four factors | Harness measurement | `s_mod × s_mock × s_entry × s_probe` |
| **reliability** stability and replay | 0.10 | Repeated runs agree; the harness can replay the same verdict in a clean environment | Harness only | `[replay agrees] × (number of consistent runs/number of runs) × min(1, number of runs/3)` |

**Oracle tiers** (fixed options selected by the agent; the harness checks the evidence):

| Tier | Definition | Score |
|---|---|---|
| O4 | Machine-checkable and points to a specific effect and location: exception type plus throw location equals `Region.location`; or a hook event names the location; or exact value/sequence equality | 1.0 |
| O3 | Machine-checkable and points to an effect category but lacks a location: exception type only, exit code, shape/dtype difference, or numerical difference exceeding the declared tolerance | 0.7 |
| O2 | Substring or regular expression matching on text logs | 0.35 |
| O1 | An LLM or person reads the output and judges it | 0.1 |

**Four fidelity factors** (measure fidelity to the original code, drawing on modification amount, authenticity of the system under test, and probe impact in software testing):

| Factor | Definition | Formula |
|---|---|---|
| `s_mod` modification amount | Number of semantically modified statements ÷ total statements in functions in `call_chain` (counted by AST; pure logging probes do not count) | `max(0, 1 − Δ/0.05)` |
| `s_mock` external substitutions | Number of mocked symbols. **On path** means called during the run before the target line, or belonging to `call_chain` | `max(0, 1 − 0.4×on path − 0.05×off path)` |
| `s_entry` entry depth | Position in `call_chain` of the function called directly by the test. Use 0.25 for extracted snippets (not run in a repository module) | `1 − position/(chain length−1)`, or 1 when the chain length is 1 |
| `s_probe` probe impact | Whether observable results are the same with and without hooks | 1 if the same or if there is no hook; otherwise 0 |

**Additional rules (added after the v2 check):**

- **When the condition cannot be evaluated directly** (e.g. R07's `otherwise` or R13's natural-language condition): the agent must write an executable predicate `condition.py` (evaluated on variables captured at the target line) and register it before the first run. The harness executes it. In this case, `infect` is multiplied by 0.6 because the fidelity of the translation has not been verified; 0.6 is below the 0.7 required for the high tier, so such tests can reach at most medium. If no predicate is written, `infect = 0`.
- **Mocks must be observable.** The agent declares the symbols to mock; the harness supplies recording substitutes (recording the time of each attribute access and call), or wraps substitutes written by the agent. The harness computes `on_path` based on whether the symbol was accessed before the target line; the agent does not declare it.
- **Event sequence cases** (`witness_type = event_sequence`, e.g. F03): both positive and negative cases are call sequences. "Differ by only one factor" means the two sequences differ in one argument of one call only.
- **Mutation takes place on a temporary copy**, without modifying repositories in `third_party/`, so it does not violate T5. Only the decision at `Region.location` is mutated. Equivalent mutants may occur, so a kill rate of 1.0 is not required.

## 3.5 Decision rules (the harness decides from observations, not the agent)

"Effect" means the observable event corresponding to `Region.outcome`: `reject` → an exception is raised at the target location; `fallback`, `mechanism_variant` → the target branch executes (path hook event); `state_dependent` → the result of the second call differs from a call made alone.

| Effect in positive case | Effect in negative case | Verdict | Explanation |
|---|---|---|---|
| Yes | No | `yes` | |
| No | No | `no` | Must also pass G5 |
| Yes | Yes | `inconclusive` | Oracle is not specific enough, or the wrong boundary was chosen |
| No | Yes | `inconclusive` | Boundary direction is reversed |
| Crash elsewhere, timeout, or import failure | — | `inconclusive` (`test_error`) | |
| Not run (environment requirements cannot be met) | — | `inconclusive` (`not_run`) | |

## 3.6 Definition of "clean environment replay" (G2)

A new temporary directory; a fresh checkout of the repository from the fixed commit; the same conda environment `findlimit` plus the artifact's dependency directory; a new process; `SOCLAAS_*` and proxy settings cleared from environment variables; and only the commands registered by the agent in `replay_commands` executed.

## 4. Hard gates (if any is unmet, the verdict is forced to `inconclusive` and confidence is low)

| Gate | Requirement |
|---|---|
| G1 | The target statement executes (an extracted snippet must first be compared verbatim to prove it matches the corresponding repository lines) |
| G2 | The harness replays in a clean environment and obtains the same verdict |
| G3 | No semantic modification to the target statement or its decision expression |
| G4 | Oracle is at least O3 and was registered before the first run |
| G5 (only for `no`) | The positive case condition has been verified true; zero on-path mocks; mutation kill rate at least 0.5 (demonstrating that the oracle can see the effect when it exists) |

## 5. Aggregation

1. Use a **weighted geometric mean** of dimension scores, with a floor of 0.05 for each dimension. This prevents other strengths from masking a weak link, consistent with the RIPR chain's idea that the weakest link determines evidence strength.
2. `final score = geometric mean × form consistency rate`. Form consistency rate = number of items where the harness recomputation agrees with the agent's claim ÷ total number of claims.
3. If a gate fails, the final score is capped at 0.49.
4. Tiers:
   - **high**: final score at least 0.80; `reach`, `infect`, `oracle`, and `control` each at least 0.7; `mutation` at least 0.5 (must have been evaluated); `fidelity` at least 0.7.
   - **medium**: final score at least 0.55.
   - **low**: all others.
5. Upstream `Finding.confidence` (mechanical, llm_assisted) is **reported separately and not incorporated**, to avoid mixing confidence in the upstream evidence chain with the quality of this test.

## 6. Form filled in by the agent

```json
{
  "test_id": "T01", "finding_id": "F01", "strategy": "S0|S1|S2|S3",
  "design": {
    "witness_source": "witness_hint",
    "free_parameters": [{"name": "num_heads", "value": 8, "why": "witness_hint 未给出"}],
    "positive_input": {"q_len": 4096, "k_len": 8192},
    "negative_input": {"q_len": 4096, "k_len": 4096},
    "boundary_variable": "k_len",
    "condition_predicate_file": null,
    "oracle": {"tier": "O4", "type": "exception",
               "spec": "AssertionError raised at flex_prefill_attention.py:1836",
               "signal_location": "flex_prefill/ops/flex_prefill_attention.py:1836"},
    "expected": {"positive": "AssertionError at :1836", "negative": "no exception at :1836"}
  },
  "execution": {
    "entry_called": "flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention",
    "call_chain_index": 0,
    "repo_files_modified": [],
    "mocks": [{"symbol": "triton", "kind": "fake_module", "reason": "import-time dependency"}],
    "hooks": [],
    "replay_commands": ["..."]
  },
  "claims": {
    "target_reached": true,
    "decision_outcomes_seen": ["true", "false"],
    "condition_true_on_positive": true,
    "condition_false_on_negative": true,
    "positive_observed": "AssertionError at :1836",
    "negative_observed": "no exception at :1836"
  },
  "evidence": {"trace_file": "...", "stdout_file": "...", "diff_file": "..."}
}
```

Original-language example string: `"witness_hint 未给出"` [English: "not provided by witness_hint"].

The harness recomputes and compares every item in `claims`. Mutation checks, repeated runs, replay, coverage, probe impact, and the number of changes after the run are not in the form; the harness measures them.

## 7. Prototype output on constructed examples (not measured results)

| Example | Geometric mean | Final score | Tier | Verdict |
|---|---|---|---|---|
| A Ideal (F01 type, 1 off-path mock) | 0.992 | 0.992 | high | yes |
| B Extracted snippet only | 0.806 | 0.806 | medium | yes |
| C 2 on-path mocks | 0.752 | 0.752 | medium | yes |
| D Oracle judged by LLM, changed 2 times after the run | 0.545 | 0.490 | low | inconclusive (G4) |
| E Ideal, but no mutation run and only 1 run | 0.659 | 0.659 | medium | yes |
| F Ideal, but 3/6 form items disagree with recomputation | 0.992 | 0.496 | low | yes |
| G `no`, mutation killed only 1/4 | 0.864 | 0.490 | low | inconclusive (G5) |
| H Target line not reached | 0.633 | 0.490 | low | inconclusive (G1) |
| I Condition judged by an agent-written predicate (F03 type) | 0.919 | 0.919 | medium | yes |

I first tried a weighted arithmetic mean, but failing examples such as D and H could still score above 0.8, so I switched to a geometric mean with a cap for failed gates.

## 8. Limitations and calibration

- The weights, the `0.05` denominator for modification amount, the `0.4/0.05` mock penalties, and the tier thresholds are all initial values.
- Calibration method: inject faults into the pilot (delete an assert, change a threshold, negate a condition) to obtain samples with known answers for "limitation present/absent"; check whether verdicts and tiers are reasonable, then adjust parameters.
- The mutation operator set is fixed: condition negation, comparison operator replacement (`==`↔`!=`, `<`↔`<=`, `>`↔`>=`), deletion of assert or raise, and adding or subtracting 1 from a constant.
- This scorecard measures only "how well the test was done", not "how important the limitation is".
- An `effect_type` (accuracy, performance, resource) that cannot be evaluated under the CPU restriction defaults to `inconclusive` and is excluded from scoring.
