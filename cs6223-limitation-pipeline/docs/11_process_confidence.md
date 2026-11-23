# Code-side static evidence (2026-11-21, v2 draft, awaiting agreement from all three team members)

Source: meeting on 2026-11-20. The code side must add evidence relevant to software testing to each candidate and pass it with the limitation to the downstream side as input to its tier assignment. Implementation: `codeside/process_confidence.py`; tests: `tests/test_process_confidence.py`.

## What it is and is not

Each step 4 Finding states: **under condition `cond`, the code produces effect `eff` at location `loc`**. The test side (`checklimits/CONFIDENCE_SPEC.md`) judges this statement by execution and assigns L0–L3.

The code side provides **evidence available before testing**. It uses the same framework as the test side (list “ways this statement could be wrong,” give each a status, and do not calculate a weighted sum), but:

- **The code side does not assign a tier.** v1 had P0–P3 tiers, which were removed: in the 130 existing test results, P tiers had no relationship with test judgments (yes rates: P1 56/68, P2 30/33, P3 24/29); another tier would only be confused with the L tier.
- **Only the test side assigns the final tier.** Code-side evidence sits alongside it in the record and does not change its rules.
- No code is executed and no model is called. The same records, repository and run files always produce the same result.

## Four parts

### 1. `checks`: checklist

Statuses: `eliminated` (checked by a tool), `residual` (only an argument or model judgment), `open` (not assessed), `refuted` (check failed).

| # | How the statement could be wrong | Testing concept | Test-side counterpart | `eliminated` | Other statuses |
|---|---|---|---|---|---|
| C1 location | Location or snippet is wrong | Input validity | D12 | The statement on that line at the pinned commit matches the snippet in canonical form | Text is on the line but it is not the start of a statement: `residual`; mismatch or missing file: `refuted`; no repository: `open` |
| C2 condition | Condition is not the decision for this statement | Decision, the unit of decision coverage | D2 | Same AST as the statement's decision expression or its negation (including unconditional statements in branches, conditional expressions and comprehension filters) | Only an operand of the decision, or a rewrite: `residual`; uses names absent from the function: `refuted`; not a Python expression: `open` |
| C3 reachability | Cannot be reached from the official entry point | Reachability (R in RIPR) | D1, D14 | Target is in the entry function, is a module-level statement, or has a call chain with real call sites at every level | Chain includes a guessed step: `residual`; no chain: `open` |
| C4 feasibility | Condition contradicts the path prefix | Infeasible paths; symbolic execution and constraint solving | witness | z3 solves for trigger and control points, with all path prefixes in the solver | A prefix is absent from the solver or no control point: `residual`; no solution found: `open`; `infeasible`: `refuted` |
| C5 extraction | Another run would not find the item | Repeatability (flaky test) | D8 | Found by the static route, or found by the LLM route in all extraction runs (same file and line) | LLM route found it in only some runs, or this paper has no repeated runs: `residual` |
| C6 effect_label | The labeled effect cannot be judged at this statement | Test oracle problem | D4 | A `reject` statement can raise an exception; a `path_change` or `state` statement is `if` / `while` | Mismatch: `refuted`; effect is `other`: `open` |
| C7 documentation | “Not documented” is actually documented | Absence assertion | — | 3b found the original text (quote verified verbatim) | `not_found`: `residual`; three repeated results disagree: `residual`; no 3b: `open` |
| C8 review | A reviewer considers it wrong | Inspection | — | Reviewed by a human | LLM blind review: `residual`; reviewed as `wrong`: `refuted`; not reviewed: `open` |

C7 affects only the category (whether it is `undisclosed`), not whether the code behaves this way.

### 2. `repeats`: repeated measurements

| Field | Meaning | Data | Testing concept |
|---|---|---|---|
| `extraction_runs.found_in` / `of` | Number of extraction runs in which this location appeared | `results/step2_merged/<id>/merged_run{1,2,3}.json` | Repeatability |
| `documentation_check.paper_agreement` | Agreement rate across three repeated 3b runs | `results/pipeline/<id>/3b.detail.json` | Inter-rater agreement |
| `routes` | Which routes found it (`ast` static, `llm`) | `Limitation.provenance` | Corroboration by two independent methods |

Matching requires the same file and line, a strict criterion: if the LLM points to adjacent lines in two runs, it counts as not found. FlexPosit and QoServe have no repeated extraction records and are marked unmeasured.

### 3. `testability`: predicted ceiling for the test-side tier

Derived from the test side's own rules (`CONFIDENCE_SPEC.md`: L2 requires D3 eliminated, L3 requires D14 eliminated). Conceptually this concerns software testability (controllability and observability) and mutation testing.

| Field | Calculation |
|---|---|
| `testable: false` + `expect_not_run` | C4 is `refuted` → expect `witness_unusable`; effect is `other` → expect `outcome_unsupported` |
| `mutants` | Number of mutants generated at the target line using `checklimits/checklimits/mutate.py::generate` on the test side (the same function, not a separate implementation) |
| `ceiling` | Fewer mutants than `n_min` (4): `L1`, because D3 cannot be eliminated; otherwise, no call chain: `L2`, because D14 can be at most residual; otherwise `L3` |
| `limited_by` | Limiting defeater and reason |
| `condition_has_calls` | Condition contains function calls, so D2 cannot be evaluated directly |
| `integer_boundary` | Boundary variables are all integers, so adjacent points for D5 are defined |

**This is a ceiling, not a forecast**: the actual tier can be lower (a weak oracle, unstable results or a missing environment can all lower it).

Comparison with existing test reports (seven papers, 190 items with code-side records and reports):

| Prediction | Actual | Count |
|---|---|---|
| Ceiling L1 | L1 71, invalid 7, n/a (inconclusive) 10 | 88 |
| Ceiling L2 | L2 12, L1 1 | 13 |
| Ceiling L3 | L3 15, L2 7, L1 4, n/a 3 | 29 |
| Expected `outcome_unsupported` | `outcome_unsupported` | 48 |
| Expected `witness_unusable` | `witness_unusable` | 12 |

**None of the 130 tested items exceeded the predicted ceiling**; 98 exactly matched it. The reasons for all 60 untested items matched. The rules were chosen using these data, so this is not independent validation; if `n_min` changes, the ceiling must change too (it is currently hard-coded as 4). `condition_has_calls` and `integer_boundary` only record facts; they do not enter the ceiling and have not been validated.

### 4. `importance`: importance (separate from confidence)

- `path.decision_on`: `main` means the decision is not inside any `if` / `except` / `case`, nor are call sites on the chain, so it is evaluated on every call; `side` means it is in a conditional branch (`enclosing_conditions`, `conditional_call_sites`); `unknown` means there is no call chain and callers are not visible. Loops are counted separately (`enclosing_loops`). This approximates dominance and operational profile using syntactic nesting; preceding early returns appear only in `path_prefix_conditions`.
- `impact`: `guarded_statements` is the number of statements in the branch body, or the remaining statements in the function after assert / raise (impact analysis); `call_sites_of_function` is the number of call sites resolved to this function (fan-in).
- `coverage`: the number of decisions in the target function, how many the code side listed, and whether the entry point can statically reach it. This is **analysis coverage**, not execution coverage; a low listed proportion does not imply missed reports, since the code side lists only decisions related to the paper's mechanism.

## Future use

| When | Part | Use |
|---|---|---|
| Before testing | `checks`, `testability` | Spend no budget on `testable: false`; spend less agent time on a low `ceiling` |
| After testing | `testability.limited_by` | Place beside the L tier to explain whether the statement itself cannot reach a higher tier or testing was insufficient |
| Untested Finding | `checks`, `repeats` | List as deterministic evidence alongside the A-tier analysis |
| Final report | `importance` | Use only for ranking, not tier assignment |

Currently the block is only passed through: it is in every record in `limitations_for_tests.json`, and the test side copies it unchanged into `finding.process_confidence` in `report.json`. None of the four uses above is connected to the test side or report yet; team agreement is required first.

## Example in a record

`process_confidence` in each record of `limitations_for_tests.json` (null for a purely paper-side Finding). Like `limitations`, it is an extra key on the handoff record, **not a field in the `Finding` schema**; the shared schema has not changed.

```json
{
 "format": "process-confidence-v2", "calibrated": false, "limitation_id": "CL-B013",
 "checks": {"C1": {"name": "location", "status": "eliminated", "evidence": "..."}, "...": {}},
 "open_doubts": ["C3", "C8"],
 "repeats": {"extraction_runs": {"measured": true, "found_in": 3, "of": 3, "match": "same file and line"},
             "documentation_check": {"measured": true, "repeats": 3, "paper_agreement": 1.0, "elsewhere_agreement": 1.0},
             "routes": ["llm"]},
 "testability": {"measured": true, "testable": true, "mutants": 2, "mutants_needed": 4,
                 "mutant_operators": {"...": 1}, "ceiling": "L1",
                 "limited_by": ["D3: 2 mutant(s) of the target line, fewer than n_min=4; it cannot be eliminated", "D14: ..."],
                 "condition_has_calls": false, "integer_boundary": true},
 "importance": {"path": {"decision_on": "unknown", "...": 0}, "impact": {"guarded_statements": 30, "...": 0},
                "coverage": {"function_decisions": 4, "...": 0}}
}
```

When one Finding merges multiple code-side records, the calculation uses the record used by the witness.

Recompute only, without rerunning step 4 (no model call; all other content unchanged):

```bash
python scripts/run_step4.py --process-only [--only <id> ...]
python scripts/make_handoff_doc.py
```

Each paper's summary is in `process_confidence` in `findings.report.json`; the table for all papers is in `results/step4/process_confidence.md`. Section 6 of `HANDOFF.md` explains it.

## Team decisions needed

1. **Whether to implement the four uses.** In particular, how to assign the final four tiers to untested Findings (about 270): the meeting required a tier for every claim, but L tiers exist only for tested items.
2. **Shanghao must confirm the two test-side changes**: `checklimits/checklimits/adapter.py` removes this key before validating the `Finding`; `testreport.py` puts it into `report.json`.
3. **Test reports will show `stale`.** Because `limitations_for_tests.json` changed, the test line in `pipeline status` changes from `done` to `stale`. Existing judgments and tiers are unaffected, but `pipeline test <id>` must be rerun on a machine with the tested environment (without `--run-agent`).
4. **Definition of “main path.”** It currently uses syntactic nesting. An alternative is whether the paper's evaluated configurations reach it, which requires paper-side parameter mappings; most are currently unknown.
5. **Whether to add it to the shared schema.** Changing `schema/models.py` will cause three tests in paper-side `schema_contract.py` to fail (it records the file hash); Zhaopeng must update it at the same time.

## Known limitations

- The ceiling rules have only been compared against development data, with no independent validation; `n_min` is hard-coded as 4 and does not read the test-side profile.
- The mutant count depends on the test side's `mutate.py`, loaded by file path; when that file is absent, `testability` is marked unmeasured.
- C2 recognizes only identical or negated ASTs; equivalent rewrites are marked `residual`.
- C3 and C4 read `witness_hint` directly and inherit its limitations (the two items in `checklimits/REQUESTS_TO_STEP4.md` §6 remain unaddressed).
- Extraction runs are matched by line number, a strict criterion.
- The literature concepts in this document (RIPR, PIE, ON/OFF points, etc.) were listed from memory and need checking against the original sources before inclusion in a report.
- There is no human-annotated comparison, so the relationship between this evidence and accuracy is unknown.
