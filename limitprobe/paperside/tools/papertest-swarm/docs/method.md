# The gap-receipt swarm (S) in one page

## Why a new track exists

v9 measured four conditions on the four dev papers. The two simple baselines were:

* **A `api_once`** — one DeepSeek call with the frozen paper + full source packet.
* **B `single_agent`** — one agent loop with paper/repository tools and the same packet.

A scored 0 core / 0 partial; B scored 0 core / 1 partial (MInference). The two swarm
variants (C plain swarm, D evidence-gap swarm) scored 0 core / 0 partial. Two concrete
defects were found in the swarm variants:

1. **Nobody owned the evidence chain.** Discovery was split across short worker
   sessions, so no session walked a full `produce → save → consume → metric` path.
   The one historical NNSmith hit came from a single tool-using session that spent ten
   replies tracing exactly such a path.
2. **Handoffs silently lost findings.** A worker returned structured candidates under
   different field names; the strict parser dropped them and no stage recorded the loss.

## The workflow

```
        paper + pinned repo (read-only evidence tools)
                          |
              +-----------+-----------+
              |                       |
      (1) paper-first map      (forced once, turn 4+)
      stages / artifacts /          |
      consumers / gaps              v
              |            (2) delegate_gap(question, chain)
              |                       |
              |            worker: same tools, 2 replies
              |            returns candidate JSON
              |                       |
              v                       v
      (3) lead traces the    (4) lead reopens the worker's
          chain in source          spans (receipts recorded)
              \                       /
               +---------+-----------+
                         |
              (5) final JSON with origin_ids
```

The lead keeps its own tool history; the worker only fills one named gap. A worker
report never replaces the lead's reading.

## What the harness records

* every wire request/response (`request-NN.json`, `response-NN.json`, raw `*.sse`)
* every tool call and read span (`tools.json`, `reads.json`)
* the paper-first map, delegation question and chain summary (`events.jsonl`, `handoff.json`)
* `ledger.json` with five stages per worker candidate:

  `worker_found → parse_retained → delivered_to_lead → verified_span → cited_in_final`

* validation receipts: exact paper quote match, source spans actually read, comparison
  completeness (`validation.json`)

## Discovery prompts (generic, no reference answers)

The method ships four generic probes that mirror the reference rubric's structure
without naming any paper's diagnosis:

1. **Stage ledger** — every acceptance/selection/stopping decision names the artifact
   it returns and the downstream consumer of that artifact.
2. **Keep-one-of-many** — when a stage selects among candidates, how many survive in
   the artifact, and can the discarded candidates still be exercised by the reported
   evaluation?
3. **Premise → transformation → broken premise → consequence** — why the artifact is
   adequate under the calibration condition, what the paper's own evaluation changes,
   which quantity changes, and how the reported metric is affected.
4. **Sharing** — one representation/budget/decision consumed by several heads, layers
   or components with possibly conflicting needs; and **unit mismatch** between what
   the mechanism diversifies and what the metric aggregates.

The paper-first pass forces the model to produce this map before reading code, because
code-first exploration in v3-v5 drifted into implementation details (tolerance,
binning fallback, block-size cost tables).

## Budgets and fairness

* A: 1 request, full packet, no tools.
* B: same packet and system as the archived baseline, tools on, up to 8 replies.
* S: up to 10 requests per cell (8 lead + one 2-reply worker), same model route,
  same frozen inputs, same reference rubric (evaluation only).

A and B are re-run inside this harness so that the comparison does not depend on a
different agent runtime, and the archived v9 finals are re-graded as a cross-check.
