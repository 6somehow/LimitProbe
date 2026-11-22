# Results (dev split)

All runs use frozen inputs, model `x-test-2` / `deepseek-v4.1-flash-1017`, and the human
reference rubric for scoring only. A/B/C/D are the frozen v9 conditions with their
official grades. S is the gap-receipt swarm implemented in this workspace.

## Per-paper dev grades

| paper | A api_once | B single_agent (v9) | C plain_swarm | D evidence_gap_swarm | S dev-v6 |
|---|---|---|---|---|---|
| NNSmith | miss | miss | miss | miss | **core** (H3) |
| MInference | miss | partial | miss | miss | partial (H1) |
| InfiniGen | miss | miss | miss | miss | miss |
| SparTA | miss | miss | miss | miss | miss |
| core/partial | 0/0 | 0/1 | 0/0 | 0/0 | **1/1** |

S satisfies the study's dev rule: more paired wins than losses and strictly more core
hits against each of A and B.

## S sample variance on NNSmith

| sample | prompt | NNSmith | evidence |
|---|---|---|---|
| dev-v6 | probes v1 (stage ledger, keep-one-of-many, unit mismatch, sharing) | **core** H3 | paper Algorithm 3 line 15 + comparison |
| dev-v8 | same prompts | miss | best record framed the search as one-sided feasibility without the stored-witness step |
| dev-v9 | + stored-witness / replay probe; final turn without thinking | **core** W2 | code spans `input_gen.py` 31-74, 102-110 and `cli/fuzz.py` 134-156 |

The core reproduces in 2 of 3 samples; the miss is kept in the record rather than
filtered out.

## Role-contract prompts (s2, dev-v10)

Prompt version `s2/2026-11-23` adds a role contract for both roles: the lead must count
`candidates_considered / candidates_kept / replay_count` per artifact, complete one
chain with producer and consumer spans, rank the record that reaches the reported
metric first, and keep at least one candidate from the input/witness stage when one
exists; the worker must return a verdict (`supports`/`narrows`/`refutes`), the four
counts from source, and one or two fully chained candidates, with an empty list allowed
only with a verdict and a missing-evidence statement. Delegation now requires an
`expected_signal`; the worker gets three replies.

| paper | S s2 (dev-v10) | blind check |
|---|---|---|
| NNSmith | **core** (H1) | core, all three nnsmith_check items yes |
| MInference | partial (H1) | partial, still missing the RoPE step |
| InfiniGen | miss | — |
| SparTA | miss | — |

A second s2 sample on NNSmith (dev-v11) also produced a core (H1: the search keeps the
first feasible witness and `make_oracle` uses only that one), blind-confirmed. So the
s2 prompts reached the core in 2 of 2 samples, 4 of 5 NNSmith samples overall.

Worker delivery changed from 6/13 handoffs returning candidates (v3-v6, no verdict
asked) to **5/5 handoffs returning candidates with a verdict** (v10-v11: 2 supports,
3 narrows). On NNSmith the worker itself returned
`nnsmith-single-witness-consumption` with counts `considered=2, kept=1, replay=1,
consumer=1`, and the lead verified 2 of its spans.

## In-harness baseline reruns

The archived v9 B stopped after one reply. To test whether S also beats a *stronger*
single agent, B was re-run in this harness with the historical direct-agent system
prompt, the full packet, tools, and up to 8 replies.

| paper | A (in harness) | B+ single agent, 8 replies | S dev-v6 |
|---|---|---|---|
| NNSmith | miss | miss | **core** |
| MInference | miss | miss | partial |
| InfiniGen | miss | miss | miss |
| SparTA | miss | miss | miss |

The in-harness baselines are all 0 core / 0 partial under the same holistic grader
(`out/grades-baselines`), so S wins against both the archived and the strengthened
baselines.

## Handoff audit

`out/handoff-audit.json` records every worker handoff across the four S samples:

* 13 delegated gaps
* 6 worker candidate sets returned
* 6 parsed and retained (tolerant parser: aliases, bare lists, truncated JSON)
* 6 delivered to the lead
* 2 cited in a final report

No candidate list was lost between worker output and the lead's context. The NNSmith
core itself came from the lead's own chain: the worker on that cell returned an empty
list. Delegation currently verifies more reliably than it discovers.

## Grading provenance

Three independent graders are archived:

* `out/grades-*` — holistic LLM grader (`swarmlab.grade`), strict prompt;
* `out/grades-rubric-*` — structured four-question rubric grader (`swarmlab.rubric`);
  this grader is the most lenient on partial/clue cases and is not used for the claim;
* `out/grades-adjudicated-*` — the reference `full_match` checklist applied to the best
  record, cross-checked by a separate blind agent with the same rubric. The NNSmith
  core was confirmed by the blind agent in both samples.

Disagreements are documented per cell (holistic vs structured vs blind), rather than
resolved silently.


## Held-out test split (S only, frozen method)

The S method (dev-v9 prompt: stage ledger, keep-one-of-many, premise/transformation,
unit mismatch, sharing, stored-witness) was run once on the four test-with-source
papers. No tuning was done on these papers; the reference rows 05/07/09/14 were used
only for scoring.

| paper | S | best record | note |
|---|---|---|---|
| Prompt Cache | partial | H2 | parameter placeholder freezes the suffix KV (same family as the reference's missing conditioning, but intra-module) |
| SpinQuant | **core** | H1 | shared global R1 forces a per-layer compromise; the paper's own Fig. 7c shows one layer's SNR worsens; per-layer R2 absorption is discussed; per-layer R1 comparison proposed |
| KVQuant | partial | H2 | outlier budget allocated by magnitude rather than sensitivity; the first-token position proxy is not addressed |
| DX100 | miss | H1 | tile-capacity truncation, not cross-iteration dependence blocking offload |

A blind independent grader agreed on the SpinQuant core, graded Prompt Cache core (a
more lenient reading of the same conditioning family), KVQuant partial and DX100 miss.
The conservative adjudication above keeps Prompt Cache at partial because the
reference's locus is cross-module conditioning. Test outcome under the conservative
reading: **1 core, 2 partial, 1 miss** with the method frozen before the run.
