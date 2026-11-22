# AgentSwarm: gap-directed agent swarm for method-limitation testing

An independent development track for the CS6223 project "paper-guided testing of
research-method limitations". It lives beside the existing pipeline and reuses the
same frozen evidence, the same model route, and the same human reference rubric
(evaluation only). The goal of this track is a swarm method that **beats the two
simple baselines** on the development papers:

| Condition | Workflow | Requests / cell (cap) |
|---|---|---|
| **A** `api_once` | one DeepSeek API call with the frozen paper + source packet | 1 |
| **B** `single_agent` | one Pi-style agent loop with read-only paper/repository tools and the same packet | up to 8 |
| **S** `gap_receipt_swarm` | lead self-traces the method chain, delegates exactly one unresolved link to a worker, reopens the cited spans, then finalises with origin IDs | up to 8 lead + 2 worker = 10 |

A and B reproduce the study's baselines under this harness. S is the new method.

## Why this design

The previous round (v9) produced **no core hit** for any swarm variant while the
single-call and single-agent baselines produced one partial hit each on MInference.
Two concrete failures were audited:

1. **Discovery was split across short sessions.** In the earlier successful NNSmith
   run, one tool-using session spent ten model replies walking
   `generate → materialise → save one input → replay that input` and asked whether
   *other legal inputs ever get tested*. The v9 swarm made each worker do a
   compressed discovery pass, so nobody owned that chain.
2. **Handoff losses were invisible.** A worker returned structured candidates with
   different field names; the parser dropped both. Nothing recorded where in the
   pipeline the finding disappeared.

S is built around those two findings:

* **The lead owns the evidence chain** and keeps its own tool history (the r14
  pattern from AgentSwarm-Serve): it maps every stopping/selection decision to the
  artifact it returns and to the downstream consumer of that artifact.
* **Delegation carries one named gap, not the whole investigation.** The lead must
  call `delegate_gap(question, chain_summary)` exactly once; the worker receives the
  paper, the lead's chain summary and the same read-only tools.
* **Verification is a receipt, not a claim.** The lead must reopen the source spans
  it relies on; the harness records whether it did.
* **Every handoff stage is measured**: `worker_found → parse_retained →
  delivered_to_lead → verified_span → cited_in_final`. The parser accepts field
  aliases (`findings`, `candidate_id`, `paper_quotes`, `source_spans`, `file`/`line`,
  bare lists, truncated JSON) and records every repair instead of dropping a list.

The stage-ledger prompt asks, for each artifact, *how many otherwise-valid inputs
share it and what the downstream comparison then exercises*. That is the generic
form of the questions that produced the earlier NNSmith hit, and it applies to
MInference (fixed sparse index vs. changed RoPE mapping), InfiniGen (one shared key
representation for several query heads) and SparTA (zero arrangement vs. real
reduction dependencies).

## Layout

```
swarmlab/
  evidence.py   frozen paper pages + pinned Git blobs, read receipts, no execution
  contract.py   tolerant finding-list extraction, canonicalisation, validation
  llm.py        SoCLaaS chat client, archives every request/response
  prompts.py    frozen prompt texts for A, B, S and the grader
  agents.py     lead/worker loops, budgets, compaction receipts, forced delegation
  cell.py       one experimental cell, delegation tool, handoff ledger
  runner.py     prepare a run, run cells with concurrency 2
  grade.py      blinded packets, semantic grading, paired metrics
inputs/         frozen dev papers + source packets (sha256-indexed)
reference/      human rubric, evaluation only (never in generation inputs)
runs/           archived run cells (inputs, requests, responses, tools, ledger)
out/            grading packets and grades
tests/          offline tests (mock provider, parser, ledger, budget)
```

## Reproduce

```sh
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python scripts/prepare_inputs.py      # copy + hash-check frozen dev inputs
.venv/bin/python -m swarmlab.runner prepare runs/dev-v1 --inputs inputs
.venv/bin/python -m swarmlab.runner run runs/dev-v1 --split dev \
    --conditions gap_receipt_swarm
.venv/bin/python -m swarmlab.grade packet runs/dev-v1 --out out/packets-dev \
    --reference reference/reference-rubric-20261121.md
```

The runner needs `SOCLAAS_API_KEY` / `SOCLAAS_BASE_URL` in
`~/.config/soclaas/soclaas.env`. Every cell archives the exact wire requests,
responses, tool calls, reads and usage. Cells never overwrite an existing archive.

## Protocol

`protocol.json` is frozen per run: model `x-test-2` (backend
`deepseek-v4.1-flash-1017`), thinking enabled with `reasoning_effort=max`, 32,768
output tokens, 10 HTTP requests and 750,000 actual tokens per cell, 420 s per
request, concurrency 2. Compaction is deterministic: older tool payloads are
trimmed (last four kept) with a before/after token estimate in `events.jsonl`, so a
long session can continue without losing its own decisions.

For S the lead gets eight replies; a delegation is forced by the workflow (a user
note from turn 3; from turn 4 `delegate_gap` is the only exposed tool) and must
happen before the final report. Workers get two replies each: one tool round and
one answer.

## Evaluation

* Dev cases: NNSmith, MInference, InfiniGen, SparTA. The reference rubric
  (`reference/reference-rubric-20261121.md`) is never exposed to any generation
  cell; it is used only to build blinded grading packets.
* A report is graded on its single best record: **core** (same mechanism,
  trigger and consequence as the reference), **partial** (one segment, or a clue
  the reference itself calls partial), **miss** (different mechanism).
* Paired rule (from the study): a challenger beats a baseline only if it has more
  paired wins than losses **and** at least as many core hits against each of A and
  B on all four dev cases.
* Archived baseline finals are imported into the same packet format
  (`grade.py import-archived`) so they can be re-graded by one grader as a
  cross-check; the official frozen grades remain the primary baseline scores.

## Status

See `runs/` for the archived cells and `docs/status.md` for the current scoreboard.
