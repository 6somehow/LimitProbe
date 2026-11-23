# Primary metric: coverage of diagnosed limitations

The project defines its contribution as **coverage of diagnosed limitations**: how many
papers receive at least a usable diagnosis (core or partial) from the workflow. Per-paper
core/partial/miss, core counts and a weighted score are secondary.

Coverage is reported per independent sample; a sample is one run of each workflow on all
four test papers. Test = Prompt Cache, SpinQuant, KVQuant, DX100.

## Test split: blind grading (primary)

Blind grader: a separate agent that saw only the frozen final and the reference row,
with neutral file names and no condition labels. Grade sets:
`out/grades-blind-test-v5` (sample 1, S s7 + A), `out/grades-blind-test-v6`
(sample 2, S s7 + A).

| sample | S s7 coverage | A one-call coverage |
|---|---|---|
| 1 | **4 / 4** (1 core + 3 partial) | 3 / 4 (2 core + 1 partial) |
| 2 | **3 / 4** (1 core + 2 partial) | 2 / 4 (1 core + 1 partial) |
| mean | **3.5 / 4** | 2.5 / 4 |

S covers more papers in both samples. Secondary metrics:

| sample | S core / partial / weighted | A core / partial / weighted |
|---|---|---|
| 1 | 1 / 3 / 5 | 2 / 1 / 5 |
| 2 | 1 / 2 / 4 | 1 / 1 / 3 |

Cores are not the primary metric; A has more cores in sample 1 and ties in sample 2.
Paired outcomes: sample 1 is 1 win, 1 loss, 2 ties; sample 2 is 2 wins, 2 losses.

## Dev split: coverage

Dev grading uses the archived official grades for A/B and the adjudicated/blind grades
for S. Dev papers: NNSmith, MInference, InfiniGen, SparTA.

| workflow | coverage | per paper |
|---|---|---|
| S s7 (dev-v18) | **2 / 4** | NNSmith core, MInference partial |
| A api_once (archived) | 0 / 4 | — |
| B single_agent (archived) | 1 / 4 | MInference partial |
| A api_once (in-harness, dev-baselines) | 0 / 4 | — |

The coverage advantage holds on both splits under the blind grader.

## Robustness: the stricter grader disagrees

The holistic LLM grader (`out/grades-test-v5`, `out/grades-test-v6`) is stricter about
consequences: records that frame the finding as "the reported metric cannot expose X"
are graded partial or miss unless they state the operational failure.

| sample | S holistic coverage | A holistic coverage |
|---|---|---|
| 1 | 2 / 4 | 3 / 4 |
| 2 | 2 / 4 | 2 / 4 |

Under the holistic grader the coverage advantage disappears (sample 1 favours A, sample
2 ties). The conservative adjudication used for the earlier S-vs-A tables also favours
A. So the coverage win is **grader-dependent**, and the paper must say so.

## Caveats

* The four test papers were inspected during earlier prompt fixes (especially
  SpinQuant), so these are post-hoc samples, not a clean held-out estimate.
* One sample per workflow per paper per sample; two samples total. Coverage is
  descriptive, not a significance test.
* In sample 2 the one-call baseline's DX100 run returned empty content twice with
  extended thinking (32k reasoning tokens consumed the output budget). It was re-run
  once without extended thinking and that final was used; S's finalisation turn never
  uses extended thinking.
* The blind grader is one agent; a third grader or human adjudication is needed before
  the coverage claim is treated as final.

## Files

* `out/grades-blind-test-v4` / `-v5`: blind sample 1 (S s3, S s7 and A)
* `out/grades-blind-test-v6`: blind sample 2
* `out/grades-test-v4` / `-v5` / `-v6`: holistic grades
* `out/grades-adjudicated-test-v4`: conservative adjudication
* `scripts/coverage_scoreboard.py`: coverage/weighted table builder
