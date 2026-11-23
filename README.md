# AgentSwarm — gap-receipt swarm for paper method-limitation testing

An independent development track for the CS6223 project "paper-guided testing of
research-method limitations", built beside the existing pipeline. The project's primary
metric is **coverage of diagnosed limitations**: how many papers receive at least a
usable diagnosis (core or partial). The shipped method is s7, a two-phase depth+breadth
swarm (one gap worker plus one breadth pass, six candidates, 9-10 requests).

| split | S s7 | A api_once | B single_agent |
|---|---|---|---|
| Dev (4) | **2 / 4** | 1 / 4 | 2 / 4 |
| Test with source (4) | **4 / 4** | 3 / 4 | 2 / 4 |
| Test paper-only (4) | 3 / 4 | **4 / 4** | 3 / 4 |
| **All 12 (blind coverage)** | **9 / 12** | 8 / 12 | 7 / 12 |

Test-with-source coverage is sample 1 of the s7 runs (sample 2: S 3/4 vs A 2/4; both
samples favour S). On the strict holistic grader the overall ranking flips:
A 7/12 > S 5/12 > B 1/12. The full per-paper matrix, cores and weighted scores are in
[docs/full-matrix.md](docs/full-matrix.md); the coverage approach and sample-level test
details are in [docs/coverage-primary.md](docs/coverage-primary.md) and
[docs/test-results.md](docs/test-results.md).

All rows use the blind grader; B here is the same single-agent workflow with up to 8
replies. Archived official A grades give 0/4 on Dev. C/D (archived) cover 0/4 on Dev.
Two caveats are part of the result: the grader choice
decides the overall ranking (blind coverage favours S by one paper; the strict grader
favours A), and the test papers were inspected during prompt development, so the test
numbers are post-hoc rather than a clean held-out estimate.

Details: [docs/results.md](docs/results.md) · [docs/report.md](docs/report.md) ·
[out/board.html](out/board.html).

## The method (s7): depth first, breadth appended, measured handoffs

```
Phase 1 (depth)                           Phase 2 (breadth)
paper + pinned repo (read-only tools)
        |
        v
  LEAD: stage ledger -> complete one chain (produce -> save -> consume -> metric)
        |                                  |
        |  delegate_gap(question,           |  reopen the worker's cited spans
        |    chain_summary, expected_signal) |  (receipts recorded)
        v                                  v
  WORKER: verdict + counts + candidate(s)  ->  LEAD deep report (first record frozen)
                                                   |
                                                   v
                                     breadth pass (no tools): append 3 new
                                     candidates from distinct stages
                                     (admission/representation/sharing/evaluation)
                                                   |
                                                   v
                                     merged JSON: deep record first, 6 max
```

Phase 1 is the s3 loop that produced the Dev cores. Phase 2 is one extra call that
freezes the deep report and appends three breadth candidates, one per remaining stage;
the deep first record is returned verbatim. Total budget 9-10 requests: up to 6 lead
replies + one gap worker with 2 replies + one breadth pass.

**Lead role contract** (`swarmlab/prompts.py`, `PROMPT_VERSION = "s7/2026-11-23"`):

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
7. phase 2 appends three breadth candidates from distinct stages while the deep first
   record is returned verbatim (the breadth pass cannot rewrite the chain).

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
contracts (v10-v18): 9 of 9 handoffs returned candidates with a verdict (4 supports,
5 narrows), 13 candidate records, all delivered, 16 spans re-read by the lead, but
strict `origin_ids` citation is 0/13 (see the s4 negative result below). The s7 runs
keep one gap worker per paper and add the breadth pass. On NNSmith the
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
