# Test-split evaluation (s3 method vs one-call baseline)

Setup: frozen test-with-source papers (Prompt Cache, SpinQuant, KVQuant, DX100), the
shipped s3 prompt for S, and the study's one-call A condition, both run in this harness
on 2026-11-23 (`runs/test-v4`). Reference rows 05/07/09/14 were used for scoring only.
Budgets: S up to 10 HTTP requests (7 lead + one worker with up to 3 replies); A exactly
one request with the same frozen paper + source packet.

## Conservative adjudication (reference locus)

| paper | S s3 | A one call |
|---|---|---|
| Prompt Cache | partial (H1) | **core** (C1) |
| SpinQuant | partial (H1) | partial (c2) |
| KVQuant | partial (H3) | miss |
| DX100 | miss | partial (C5) |
| **core/partial** | **0/2** | **1/2** |

* **Prompt Cache.** A's C1 states the reference mechanism directly: per-module
  independent KV excludes cross-module attention, so the cached path is not equivalent
  to full prefill under cross-module dependencies. S found a related but intra-module
  mechanism (H1: module-independent encoding plus evaluation on single-module contexts;
  H3: parameter placeholder freezes the suffix KV). The blind grader called S's H3
  core; conservatively it is partial because the reference's locus is cross-module
  conditioning.
* **SpinQuant.** Both workflows find the shared-R1 compromise with the paper's Fig. 7c
  evidence (S: H1; A: c2). Neither checks whether per-layer R2 absorbs the conflict,
  which the reference's qualification asks for. Partial for both; blind grading calls
  both core.
* **KVQuant.** S's H3 shows that the existing protections (1% outlier budget,
  first-token fp16) do not cover multi-key discrimination and that a shared per-layer
  LUT degrades most; A misses this. S partial, A miss.
* **DX100.** A's C5 establishes the exclusion mechanism (non-commutative RMW and
  cross-iteration aliasing make kernels non-offloadable) but never quantifies the
  blocked-kernel time share or the application-level benefit. S misses the mechanism
  entirely (Range Fuser tile capacity). A partial, S miss.

## Grader comparison

| grader | S s3 (core/partial/miss) | A (core/partial/miss) |
|---|---|---|
| conservative (reference locus, blind cross-check) | 0 / 2 / 2 | 1 / 2 / 1 |
| holistic LLM grader (`out/grades-test-v4`) | 0 / 2 / 2 | 1 / 2 / 1 |
| blind agent | 2 / 1 / 1 | 2 / 0 / 2 |

Two of three graders favour A on this split; the blind grader is more generous to S's
intra-module Prompt Cache record and to S's SpinQuant record. No reading supports a
claim that S beats A on these four test papers.

## s7 depth+breadth test run (test-v5)

The s7 method (phase 1 = the s3 deep loop; phase 2 = one breadth-append call producing
three extra candidates from distinct stages; six candidates total) was run once on the
same four test papers.

| metric | S s7 | A one call |
|---|---|---|
| holistic grader (`out/grades-test-v5`) | 0 core / 2 partial / 2 miss | 1 core / 2 partial / 1 miss |
| conservative adjudication | 0 / 2 / 2 | 1 / 2 / 1 |
| blind agent | 1 core / 3 partial / 0 miss | 2 core / 0 partial / 2 miss |

Per paper (blind): Prompt Cache core (H3 cross-module masking; conservative partial),
SpinQuant partial (B3 R1 shared by activation and KV consumers; the global-R1
compromise appears in a different record), KVQuant partial (B1 fixed 1% protection
budget), DX100 partial (H3 cross-iteration dependence, no time-share consequence).

Paired blind comparison: Prompt Cache tie (core/core), SpinQuant A wins (core vs
partial), KVQuant S wins (partial vs miss), DX100 tie (partial/partial) — 1 win, 1 loss,
but A has more cores (2 vs 1). Under the study's rule S does **not** beat A on this
split. Conservative and holistic grading favour A outright.

## Earlier test samples (for completeness)

| run | prompt | result |
|---|---|---|
| test-v1 | s1 | SpinQuant core; Prompt Cache partial; KVQuant partial; DX100 miss |
| test-v2 | s2 | all four miss (s2 demoted the author-disclosed R1 compromise to `known_boundaries`) |
| test-v3-spinquant | s3, post-hoc | SpinQuant retained the R1 record again (blind core / holistic partial) |
| test-v4 | s3 | table above |

The s1 prompt reached one core (SpinQuant) and two partials, comparable to A's blind
profile, but it was not run against A in this harness.

## Interpretation

The dev result (S beats the archived A/B on NNSmith, and under blind grading adds
InfiniGen) **does not transfer to this test split**. The likely reason is breadth: A
sees the full source packet and returns up to six candidates in one reply, so it can
surface the cross-module and legality mechanisms alongside others, while the s3 lead is
pushed to complete one metric-reaching chain and keeps only two to four candidates.
Depth helped on NNSmith; breadth was needed here.

## Caveats

* The test papers were inspected during the s2 -> s3 prompt fix (SpinQuant directly), so
  s3 test results are post-hoc, not a clean held-out estimate. s1/s2 test runs were made
  before that inspection.
* One sample per workflow per paper; grader disagreement is documented above.
* B (single agent) was not re-run on test in this harness; the archived study has no
  test cells for A/B/C/D either.

## Recommended next step

Redesign the lead prompt to keep the deep chain as the first record but also require
breadth: at least three additional candidates from different stages (admission,
representation, sharing, evaluation), six allowed as in A. Then evaluate on a **fresh**
paper set that has not been inspected, with two samples per condition, before making any
test-split claim.
