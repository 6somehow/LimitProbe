# Full dataset evaluation: S s7 vs A vs B

12 papers, three workflows, coverage of diagnosed limitations as the primary metric.

* **S s7** — depth+breadth swarm: phase 1 deep chain + one gap worker; phase 2 appends
  three candidates from distinct stages (admission/representation/sharing/evaluation).
* **A** — one API call with the frozen paper + source packet.
* **B** — one agent session with read-only tools and the same packet, up to 8 replies.

Splits: Dev (NNSmith, MInference, InfiniGen, SparTA), Test-with-source (Prompt Cache,
SpinQuant, KVQuant, DX100), Test paper-only (OneSidedMW, CXLfork, Juneberry,
Twilight/T-LITE). Paper-only cells have no repository; empty code evidence is legitimate.

Grading: a separate blind agent saw only the frozen final and the reference row, with
neutral file names and no condition labels. The stricter holistic LLM grader is reported
as a sensitivity analysis.

## Per-paper matrix (blind grader)

| split | paper | S s7 | A | B |
|---|---|---|---|---|
| dev | NNSmith | core | miss | core |
| dev | MInference | partial | partial | partial |
| dev | InfiniGen | miss | miss | miss |
| dev | SparTA | miss | miss | miss |
| test-source | Prompt Cache | core | core | partial |
| test-source | SpinQuant | partial | core | miss |
| test-source | KVQuant | partial | miss | partial |
| test-source | DX100 | partial | partial | miss |
| paper-only | OneSidedMW | core | core | core |
| paper-only | CXLfork | partial | core | partial |
| paper-only | Juneberry | partial | core | core |
| paper-only | Twilight / T-LITE | miss | core | miss |

## Coverage by split (blind)

| split | S s7 | A | B |
|---|---|---|---|
| Dev | 2/4 | 1/4 | 2/4 |
| Test with source | **4/4** | 3/4 | 2/4 |
| Test paper-only | 3/4 | **4/4** | 3/4 |
| **All 12** | **9/12** | 8/12 | 7/12 |

Core / partial / weighted (core=2, partial=1), blind:

| split | S | A | B |
|---|---|---|---|
| Dev | 1/1/3 | 0/1/1 | 1/1/3 |
| Test with source | 1/3/5 | 2/1/5 | 0/2/2 |
| Paper-only | 1/2/4 | 4/0/8 | 2/1/5 |

## Sensitivity: the holistic grader

The holistic LLM grader is strict about consequences and gives a different ranking:

| split | S s7 | A | B |
|---|---|---|---|
| Dev | 2/4 | 0/4 | 0/4 |
| Test with source | 2/4 | 3/4 | 0/4 |
| Paper-only | 1/4 | 4/4 | 1/4 |
| **All 12** | 5/12 | **7/12** | 1/12 |

So the ranking flips with the grader: blind coverage gives S 9 > A 8 > B 7; the strict
holistic grader gives A 7 > S 5 > B 1. This is the central methodological caveat.

## What the matrix says

* **Source-backed papers favor S.** On Dev + test-with-source (8 papers) blind coverage
  is S 6/8, A 4/8, B 4/8. The deep chain and the witness/consumer probes find mechanisms
  that need code-level tracing (NNSmith single witness; KVQuant protection budget).
* **Paper-only papers favor A.** Without code, A's open-ended single pass produces broad
  paper-level diagnoses and covers all four (4/4 blind), while S's chain-oriented
  workflow covers 3/4 and misses Twilight's net-energy trade-off.
* **B is middle.** It ties S on Dev (NNSmith core) and paper-only (3/4) but trails on
  test-with-source (2/4); one of its finals (SpinQuant) was truncated to 449 bytes with no
  candidates, and several finals needed JSON repair.
* **The overall blind lead is one paper.** 9 vs 8 is descriptive, not a significance
  test. The strict grader reverses it.

## Caveats

* Test papers were inspected during earlier prompt development; these runs are post-hoc,
  not clean held-out estimates.
* One sample per workflow per paper. Coverage differences of one paper are within noise.
* The blind grader is one agent; a third grader or human adjudication is needed before
  the overall ranking is treated as final.
* B's SpinQuant final is truncated; that is a real failure mode of the single-session
  workflow under the output budget, but it also means B's coverage could be higher with
  a retry.
* Paper-only finals have no code evidence by construction; the blind grader was told so.

## Files

* `results/` — blind grades, finals, `matrix.md`, `manifest.json` (sha256 per final)
* `results-holistic/` — the same export with the holistic grader
* `out/grades-blind-*`, `out/grades-*` — raw grade sets
* `runs/*` — wire requests, responses, tool calls, ledgers (not in git)
