# Report: a gap-receipt agent swarm that finds a method limitation the baselines miss

## Question

Can an agent swarm reliably produce a *core* method-boundary diagnosis — the reference
mechanism, its trigger and its downstream consequence — on the CS6223 dev papers,
where the two simple baselines do not?

## Conditions

| id | workflow | budget |
|---|---|---|
| A | one DeepSeek call with the frozen paper + source packet | 1 request |
| B | one agent session with read-only paper/repository tools and the same packet | up to 8 replies |
| S | lead keeps its own evidence chain, must delegate exactly one unresolved artifact-consumer link to a worker, reopens the returned spans, then finalises with origin ids | up to 8 lead + 2 worker replies |

Same model route (`x-test-2`, backend `deepseek-v4.1-flash-1017`), same frozen inputs,
same human reference rubric (evaluation only), same output contract. B in this harness
uses the historical direct-agent system prompt, so it is a *stronger* baseline than the
archived v9 B, which stopped after one reply.

## Result (dev, one sample per condition unless noted)

| paper | A | B | B+ (8-reply, in harness) | S (dev-v6) |
|---|---|---|---|---|
| NNSmith | miss | miss | miss | **core** (H3) |
| MInference | miss | partial | miss | partial (H1) |
| InfiniGen | miss | miss | miss | miss |
| SparTA | miss | miss | miss | miss |

S totals 1 core + 1 partial. It has more paired wins than losses against both A and B
and strictly more core hits, which is the study's dev-selection rule.

A second S sample on NNSmith (dev-v9, same prompt plus a stored-witness probe) also
produced a core record (W2: the search returns the first feasible ⟨X,W⟩ and only that
witness is replayed per graph), so the core is reproducible in 2 of 3 NNSmith samples.
A third sample (dev-v8) missed the core, which is reported as variance rather than
hidden.

## The core record (NNSmith, S)

* **Rule.** The numerical search runs once per generated graph; it returns the first
  feasible ⟨X,W⟩ and differential testing replays only that witness.
* **Trigger.** Compiler behaviour that depends on the actual values (constant folding,
  identity elimination, overflow/precision boundaries) rather than only on graph
  structure and attributes.
* **Consequence.** Coverage and bug counts are attributed to graph and attribute
  diversity; value-dependent branches are exercised at most once per graph and cannot
  be attributed.
* **Comparison (falsifiable).** Same graphs, same compiler, same total budget: k=1
  witness per graph (paper setting) vs k=5 independent valid witnesses; measure unique
  branch increments and the witness-to-boundary distance distribution.

This meets all four reference full-match items (first-valid stopping objective;
validity witness vs numeric-domain coverage; random init/restarts considered; same-graph
same-budget comparison) and avoids the reference's overclaims.

## Handoff audit (the part the previous round was missing)

Every worker handoff is recorded in five stages:
`worker_found → parse_retained → delivered_to_lead → verified_span → cited_in_final`.

Across the four S development samples: 13 delegated gaps, 6 worker candidate sets
returned, all 6 parsed and delivered (the tolerant parser repairs aliases, bare lists
and truncated JSON), 2 cited in a final report. No parse losses were observed.

On the NNSmith core cell the worker returned an empty candidate list; the core came
from the lead's own stage ledger and trace. That is an honest negative result for
delegation: the current worker prompt is good at verifying a named link but weak at
discovering one.

## Why S found it

The successful samples used four generic probes, no reference answers:

1. stage ledger: every selection/stopping decision names its artifact and consumer;
2. keep-one-of-many: how many candidates survive and whether the discarded ones can
   still be exercised by the reported evaluation;
3. premise → transformation → broken premise → consequence;
4. unit mismatch and sharing.

The stored-witness probe added in dev-v9 ("what is stored per test case, how many
times is it replayed, can the witness be replaced") made the core record more explicit
and better evidenced (code spans in `input_gen.py` and `cli/fuzz.py`).

## Threats to validity

* One sample per baseline; S has three NNSmith samples. The comparison uses archived
  official grades for A/B as the primary baseline, plus in-harness reruns.
* The reference itself is a human hypothesis set, not executed ground truth.
* Grading is semantic. We used three graders: a holistic LLM grader, a structured
  four-question rubric grader, and an independent blind agent. They agree on the
  acceptance of the NNSmith core and disagree on weaker partial cases; disagreements
  are documented in `out/grades-*`.
* The probe list names generic transformation categories (context length/extension,
  position scaling, grouping, zero arrangement, input values). These categories overlap
  the reference rubric's categories by construction. The probes never name a paper's
  diagnosis, and the held-out SpinQuant core (shared global R1) comes from a different
  category than the dev core, but this is a design-coupling risk to keep in mind.
* The test split has been run with S once (SpinQuant core, two partials, one miss);
  A/B were not re-run on test.

## Held-out test run

The frozen S method was run once on the four test-with-source papers without tuning:

| paper | S | best record |
|---|---|---|
| Prompt Cache | partial | H2 (placeholder-frozen suffix KV; intra-module locus) |
| SpinQuant | **core** | H1 (one global R1 forces a per-layer compromise; Fig. 7c evidence; per-layer R1 comparison) |
| KVQuant | partial | H2 (outlier budget by magnitude, not sensitivity) |
| DX100 | miss | H1 (tile-capacity truncation) |

A blind independent grader agreed on SpinQuant core and DX100 miss, graded Prompt
Cache core (a more lenient reading) and KVQuant partial. The table keeps the
conservative reading.

## Next steps

1. Make the worker discover rather than only verify: give it the lead's top-two gaps
   and three replies, and measure cited-in-final per worker.
2. Pre-register two samples per condition for the next evaluation round.
3. Try the paper-only test stratum (OneSidedMW, CXLfork, Juneberry, Twilight) with
   paper-only tools.
