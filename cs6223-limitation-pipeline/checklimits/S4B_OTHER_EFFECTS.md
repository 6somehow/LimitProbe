# Analysis and decision on `other` effects (S4b, 2026-11-16)

Conclusion: **No new oracle was implemented.** The `other` class contains no subset that is both bounded and non-tautological. This document gives the rationale and explains how reports now describe why these Findings were not tested.

## Current state

Step 4 divides effects into `reject`, `path_change`, `state`, and `other`. The harness judges only the first three. `other` means there is no corresponding check; there are 168 across five artifacts:

| Category (by target statement and notes) | Count | Example |
|---|---:|---|
| Static discrepancy between paper and code ("Static discrepancy hypothesis", no executable assertion) | 121 | FlexPrefill F030: the paper requires the smallest k whose cumulative sum is ≥γ; the code uses >γ |
| No code location | 14 | Paper-side entries for SparTA |
| Branch with no `raise` in its body (the program rejects later elsewhere) | 12 | NNSmith F005, F007: `if ...: continue` |
| Assignment or augmented assignment | 13 | NNSmith F013: `gres_config = os.getenv('NNSMITH_GRES', '4')` |
| Call statement whose effect is not an exception on that line | 3 | NNSmith F027: `ConstraintCheck.true(...)` returns False |
| Warning or log | 1 | FlexPrefill F049: `warnings.warn(...)` |
| Other (function definition, unparseable) | 4 | |

## What each category needs and whether it can be bounded

| Category | Question for the oracle | Can it be bounded? |
|---|---|---|
| Static discrepancy (121) | How much does the code result differ from the paper's formula? | **No.** Differential comparison needs an executable reference implementation of the paper's formula. Its source is an open question (the paper side must provide a formula with semantics, not a quotation). Without it, any "test" merely compares code with code. |
| Assignment (13) | What downstream change does this assignment cause? | **Tautological.** The assigned value must differ at the trigger and control points, because the condition is on that value (NNSmith F013's condition is `gres_config != "4"`, and the assignment is `gres_config = ...`). The actual effect is downstream ("a different reshape grouping was selected"). Comparing downstream outputs requires a differential or metamorphic relation, but there is no source for the metamorphic relation. |
| Branch that rejects later (12) | Did the program eventually reject, and where? | **Possible, but outside the test side.** The effect location is elsewhere (the caller checks the return value and then `raise`s or retries). Step 4's `effect_anchor` can already move an `except` line to a `raise` and move an assignment to an outer `if` with the same condition; it could be extended to follow the return value to a `raise` in the caller. Once the location is corrected, the existing `reject` check can judge it without a new oracle. |
| Call statement (3) | What happens after it returns False? | As above, first find the effect location. |
| Warning (1) | Did the target line issue a warning? | Technically possible (record with `warnings.catch_warnings`), but one case does not justify a separate oracle. |

## Decision

1. **Do not implement a new oracle.** The largest category (121) lacks a reference implementation, not test-side capability. An assignment oracle would yield a tautological `yes` every time, adding false confirmation to a Finding.
2. **Give specific reasons for not testing.** `classify_finding` now gives category-specific reasons for `other` (`describe_other`), for example: "the target is an assignment; the claimed effect is a later change and requires differential output checking; the assignment itself must differ." Static discrepancies without a code location also state that a reference implementation of the paper's formula is needed. Readers can see what is missing from the report.
3. **Requests to the other two team members:**
   * Wanting: extend `effect_anchor`'s target movement to branches that reject later (12 cases). With the location corrected, the existing `reject` check can judge them; some of the 12 are expected to become judgeable.
   * Zhaopeng: for static discrepancies where the paper gives a formula or pseudocode, identify which can be written as an executable reference function (inputs, outputs, numerical tolerance). Only those can enter the design of a differential oracle. None currently has this information.

## What we will not do

* Do not implement a generic differential check that counts any two different outputs as yes. Any comparison that changes the input produces different outputs, making such a `yes` uninformative.
