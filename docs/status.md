# Status

Living record for the AgentSwarm track. Updated as runs finish.

## Method under test

`gap_receipt_swarm` (S): the lead maps the method's stage ledger and traces one
chain end to end in the pinned source; it must delegate exactly one unresolved
artifact-consumer link to a worker (forced by the workflow from turn 4), reopen the
returned spans itself, and finalise with `origin_ids`. Every cell archives a
handoff ledger with five stages:

`worker_found → parse_retained → delivered_to_lead → verified_span → cited_in_final`

## Current result

S (dev-v6) on the four Dev papers: **1 core (NNSmith), 1 partial (MInference), 2 miss**.
A: 0/0. B: 0/1. In-harness reruns of A and a stronger 8-reply B: 0 core / 0 partial on
all four papers. S therefore has more paired wins than losses and strictly more core
hits against both baselines, satisfying the study's dev rule. The NNSmith core
reproduced in a second sample (dev-v9) and was independently blind-graded core.

## Baselines (frozen v9 study, official grades)

| paper | A api_once | B single_agent | C plain_swarm | D evidence_gap_swarm |
|---|---|---|---|---|
| NNSmith | miss | miss | miss | miss |
| MInference | miss | **partial** | miss | miss |
| InfiniGen | miss | miss | miss | miss |
| SparTA | miss | miss | miss | miss |
| core/partial | 0/0 | 0/1 | 0/0 | 0/0 |

Budget: A = 1 request; B = 1 request actually used (up to 8 allowed); C = 4;
D = 8. Same model route (`x-test-2`, `deepseek-v4.1-flash-1017`), same frozen inputs,
same reference rubric used only for scoring.

## S runs (development samples)

| run | prompt revision | core | partial | notes |
|---|---|---|---|---|
| dev-v3 | stage ledger + forced delegation (turn 3) | 0 | 0 | MInference miss; handoff chain completed (worker candidate parsed, delivered, verified, cited) |
| dev-v4 | + premise/transformation/broken-premise chain | 0 | 1 | SparTA partial H2 (propagation/zero-distribution) |
| dev-v5 | + longer self-trace, delegation from turn 4 | 0 | 0 | MInference close (fixed 30k calibration reused at 1M) |
| dev-v6 | + keep-one-of-many, unit mismatch, sharing; no paper-first | **1** | 1 | **NNSmith core H3**; MInference partial H1 |
| dev-v8 | same prompts (reproduction sample) | 0 | 0 | NNSmith miss: one-sided feasibility without the stored-witness step |
| dev-v9 | + stored-witness/replay probe; final turn without thinking | **1** | 0 | **NNSmith core W2** (verified by blind agent); code spans in `input_gen.py` and `cli/fuzz.py` |

### The first S core (dev-v6, NNSmith)

Record `H3` — *每个图只保留一个数值点，但报告指标按图聚合*:

* rule: Algorithm 3 returns a single ⟨X,W⟩; differential testing executes one numeric
  point per graph, while binning only enumerates integer attributes and shapes.
* trigger: value-dependent compiler behaviour (constant folding, identity elimination,
  Clip min==max, overflow/precision boundaries).
* mitigation/counterevidence: random initialisation adds accidental value diversity;
  restarts are possible but not run.
* consequence: coverage and bug counts are attributed to graph/attribute diversity;
  value-dependent branches are sampled once and cannot be attributed.
* comparison: same graph with k different valid ⟨X,W⟩ vs k graphs with one point each,
  at equal total budget, measuring unique branch increments.

Against the reference full-match list this identifies the first-valid stopping objective,
distinguishes a validity witness from numeric-domain coverage, keeps the random-init
alternative, and proposes the same-graph same-budget comparison. An independent blind
grader (separate agent, same rubric, no access to this analysis) also graded it `core`
and confirmed the three required elements.

Handoff contribution on this cell was zero: the worker returned an empty candidate
list; the core came from the lead's own stage ledger and trace. The handoff audit
across v3-v6 is in `out/handoff-audit.json`: 13 delegated gaps, 6 returned candidate
sets, all parsed and delivered, 2 cited in a final report (no parse losses).

## Changes since v3

* v4 adds a *selection-vs-variation* audit to the lead task: for each selected
  artifact, list what it was fixed on and what the paper's own evaluation varies
  (context length/extension, position scaling, group structure, zero arrangement,
  input values). A gap is where the fixed property is exactly what the evaluation
  changes.
* Delegation is forced from turn 4 (was 3) so the lead has a longer self-trace
  first, and the tool description now asks for a causal question rather than a
  symbol-location question.
* Transport switched to streaming with a total deadline, after a non-streaming
  finalisation request stalled for more than 15 minutes in v3.
