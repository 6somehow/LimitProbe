# AgentSwarm — gap-receipt swarm for paper method-limitation testing

An independent development track for the CS6223 project "paper-guided testing of
research-method limitations", built beside the existing pipeline. It asks one question:
**can a two-role agent swarm deliver the human reference diagnosis (the method's rule,
its trigger and its downstream consequence) where a single API call and a single agent
do not?**

Short answer on the Dev split: **yes, on NNSmith** (core reproduces across samples,
each core blind-graded) and, with the latest s3 role contracts, also on **InfiniGen**
(a first for this study). Worker candidate yield rose from 5 of 13 handoffs (s1) to
9 of 9 handoffs with explicit verdicts (s2+s3). The pre-s2 (s1) prompt also reached a core on the
held-out SpinQuant. Prompt iterations and their measured effects are in
[docs/prompt-iterations.md](docs/prompt-iterations.md).

## Current evidence

Dev papers: NNSmith, MInference, InfiniGen, SparTA. Scores are `core / partial / miss`
against the archived Shanghao reference, used for scoring only. A/B/C/D are the frozen
v9 study conditions with their official grades; S is this track.

| paper | A api_once | B single_agent (v9) | C plain_swarm | D evidence_gap_swarm | S s3 (dev-v12) |
|---|---|---|---|---|---|
| NNSmith | miss | miss | miss | miss | **core** |
| MInference | miss | partial | miss | miss | miss |
| InfiniGen | miss | miss | miss | miss | partial (blind: core) |
| SparTA | miss | miss | miss | miss | miss |
| core/partial | 0/0 | 0/1 | 0/0 | 0/0 | **1/2** |

* A and a **stronger 8-reply single agent** (same packet, tools, historical direct
  prompt) were re-run inside this harness: 0 cores and 0 partials on all four papers.
* NNSmith samples: dev-v6 core, dev-v8 miss, dev-v9 core (stored-witness probe),
  dev-v10 core, dev-v11 core and dev-v12 core (role contracts). Every core was
  blind-confirmed; the miss is retained, not filtered.
* s3 adds the first InfiniGen candidate naming the GQA shared key representation and
  the per-head column/basis conflict (H4); the blind grader calls it core, the holistic
  grader partial. Both readings are kept.
* Test split with the s7 depth+breadth method (same harness, A re-run as a one-call
  baseline): conservative/holistic S is 0 core / 2 partial vs A 1 core / 2 partial; the
  blind agent gives S 1 core / 3 partial / 0 miss vs A 2 core / 1 partial / 1 miss;
  paired blind is 1-1 and A keeps more cores, so **S does not beat A under the study's
  paired/core rule**. Under a coverage metric (at least partial per paper) blind S is
  4/4 vs A 3/4, which is the only reading where S wins; weighted core=2/partial=1 ties
  5-5. Coverage is a post-hoc choice, not the pre-registered rule. The dev advantage did
  not transfer. See [docs/test-results.md](docs/test-results.md)
  for per-paper reasons and the breadth-vs-depth explanation. Test papers were inspected
  during prompt fixes, so these numbers are post-hoc, not clean held-out.
* Every core listed above was also blind-graded by a separate agent that saw only the
  frozen final and the rubric.

Details: [docs/results.md](docs/results.md) · [docs/report.md](docs/report.md) ·
[out/board.html](out/board.html).

## The method (S): two roles, one chain, measured handoffs

```
paper + pinned repository (read-only tools)
        |
        v
  LEAD: stage ledger  ->  complete one chain (produce -> save -> consume -> metric)
        |                                  |
        |  delegate_gap(question,           |  reopen the worker's cited spans
        |    chain_summary, expected_signal) |  (receipts recorded)
        v                                  v
  WORKER: verdict + counts + candidate(s)  ->  LEAD final JSON with origin_ids
```

**Lead role contract** (`swarmlab/prompts.py`, `PROMPT_VERSION = "s2/2026-11-23"`):

1. keep a stage ledger for every acceptance, selection, stopping, allocation or
   shared-state decision: artifact, rule/budget, consumer;
2. count `candidates_considered`, `candidates_kept`, `replay_count` for each artifact;
3. complete one chain end to end with source spans for producer and consumer;
4. delegate exactly once with a causal question and an expected support/refute signal,
   then reopen and adjudicate the returned evidence;
5. final report is graded on its single best record, so one complete chain outranks
   several partial ones; incomplete records go to `known_boundaries`/`rejected`;
6. if a stage produces a test input, cached state, stored witness or propagation
   artifact, at least one retained candidate must follow that stage to its consumer.

**Worker role contract**: restate the gap and artifact/consumer pair; read and quote
pinned source; report `candidates_considered / candidates_kept / replay_count /
consumer_count`; return a verdict (`supports`/`narrows`/`refutes`); if supports or
narrows, return one or two testable candidates with the full chain and comparison; an
empty list is allowed only with a verdict and what evidence would settle the question.

**Handoff ledger** for every worker: `worker_found → parse_retained →
delivered_to_lead → verified_span → cited_in_final` (`ledger.json`). The parser accepts
field aliases, bare candidate lists, truncated JSON and a root object that closes early
before `"candidates"`; it records every repair, so a structured candidate list is never
dropped silently. Across v3–v6: 13 delegated gaps, 6 candidate
sets returned, 6 parsed and delivered, 2 cited in a final report. With the s2/s3 role
contracts (v10-v12): 9 of 9 handoffs returned candidates with a verdict (4 supports,
5 narrows), 13 candidate records, all delivered, 16 spans re-read by the lead, but
strict `origin_ids` citation is 0/13 (see the s4 negative result below). On NNSmith the
worker returned `nnsmith-single-witness-consumption` and
`nnsmith-single-witness-first-feasible` with counts considered=2, kept=1, replay=1,
consumer=1.

## Repository layout

```
swarmlab/
  evidence.py   frozen paper pages + pinned Git blobs, read receipts, no execution
  contract.py   tolerant finding-list parsing, canonicalisation, validation
  llm.py        streaming SoCLaaS client with total deadline; archives every request
  prompts.py    role contracts and prompt texts (A, B, S, grader)
  agents.py     lead/worker loops, budgets, compaction, forced delegation
  cell.py       one cell: delegation tool, handoff ledger, archive
  runner.py     prepare/run cells (concurrency 2)
  grade.py      blinded packets, holistic grading, paired metrics
  rubric.py     structured four-question grading (secondary opinion)
inputs/         frozen dev + test papers and source packets (sha256-indexed)
reference/      human rubric — evaluation only, never in generation inputs
runs/           archived cells: requests, SSE, responses, tools, reads, ledger
out/            packets, grades, handoff audit, board.html
tests/          offline tests (mock provider, parser, ledger, budget)
docs/           method, results, report, status, port notes
```

## Reproduce

```sh
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python scripts/prepare_inputs.py
.venv/bin/python -m swarmlab.runner prepare runs/dev-v1 --inputs inputs
.venv/bin/python -m swarmlab.runner run runs/dev-v1 --split dev \
    --conditions gap_receipt_swarm            # S; add api_once single_agent for baselines
.venv/bin/python -m swarmlab.grade packet runs/dev-v1 --out out/packets-dev \
    --reference reference/reference-rubric-20261121.md
.venv/bin/python -m swarmlab.grade grade out/packets-dev --out out/grades-dev
.venv/bin/python scripts/build_board.py --help
.venv/bin/python -m pytest -q
```

The runner reads `SOCLAAS_API_KEY` / `SOCLAAS_BASE_URL` from
`~/.config/soclaas/soclaas.env`. Every cell archives the exact wire requests, raw SSE,
responses, tool calls, read spans and usage; a cell never overwrites an existing
archive. `runs/` and `out/` are git-ignored; code, prompts, inputs and docs are tracked.

## Protocol

Model `x-test-2` (backend `deepseek-v4.1-flash-1017`), thinking enabled with
`reasoning_effort=max` during exploration, 32,768 output tokens, 10 HTTP requests and
750,000 actual tokens per cell, 600 s per request, concurrency 2. The finalisation turn
runs without thinking so a long final JSON is not truncated by reasoning tokens.
Compaction is deterministic: older tool payloads are trimmed (last four kept) with a
before/after estimate in `events.jsonl`.

S budget split (s2 prompts): 7 lead replies + one worker with up to 3 replies, inside
the same 10-request cell cap.

## Grading provenance and caveats

* Grading is semantic against the archived reference rubric. Three graders are
  archived: holistic (`grade.py`), structured four-question (`rubric.py`, more lenient;
  not used for the claim), and independent blind agents.
* The reference is a human hypothesis set, not executed ground truth.
* Probe categories (length/extension, position scaling, grouping, arrangement, input
  values) overlap the reference rubric's categories by construction; the probes never
  name a paper's diagnosis, but this is a design-coupling risk to review.
* The Test split has S only; A/B/C/D were not re-run there.
* Delegation currently verifies better than it discovers: the NNSmith core came from
  the lead's own chain, with the worker returning an empty list on that cell.

## Related docs

* [docs/method.md](docs/method.md) — the S workflow and why it differs from C/D
* [docs/results.md](docs/results.md) — per-paper grades, variance, in-harness baselines
* [docs/report.md](docs/report.md) — full report with threats to validity
* [docs/test-results.md](docs/test-results.md) — test-split S vs A, grader comparison
* [docs/prompt-iterations.md](docs/prompt-iterations.md) — s1→s2→s3 changes and
  measured role delivery
* [docs/port-notes.md](docs/port-notes.md) — what to port into the main pipeline
* [docs/status.md](docs/status.md) — run log
