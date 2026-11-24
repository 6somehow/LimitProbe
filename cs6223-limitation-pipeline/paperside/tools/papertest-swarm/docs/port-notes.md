# Port notes for the main pipeline

The main study already has a handoff audit (commit `4b7bca9`). This track adds three
pieces that can be ported independently, in this order.

## 1. Tolerant candidate parsing (fixes the MInference handoff loss)

`swarmlab/contract.py`

* `parse_json`: bare JSON, fenced JSON with preamble, first balanced object, bare
  candidate list, and a repair that closes a truncated object at the last complete
  record.
* `candidate_groups`: searches `candidates`, `findings`, `results`, `records`,
  `limitations`, `hypotheses`, `items`, plus one nested wrapper (`answer`, `report`,
  `result`, `output`).
* `normalize_record`: field aliases for id, title, rule/claim/causal_argument,
  conditions/trigger, consequence/downstream, `paper_quotes`/`page_number`,
  `source_spans`/`file`/`line`/`end_line`, `minimal_test`/`comparison`.
* It returns `raw_candidate_count` before normalisation and records every repair, so a
  list is never dropped silently.

In the study's packet builder, replace `unpack()` + `candidates` with
`parse_finding_report()` and store `raw_candidate_count`, `parsed_groups`, `repairs`.

## 2. Five-stage handoff ledger

`swarmlab/cell.py::build_ledger`

For every worker: `worker_found` (raw count from the tolerant parse),
`parse_retained` (normalised ids), `delivered_to_lead` (the exact tool payload appears
in a later archived lead request), `verified_span` (the lead read a source span the
worker cited after the handoff), `cited_in_final` (origin id or title match, tolerant
to `workerN:` prefixes).

In the study, `gap_trace` has three of these; adding `verified_span` and checking
delivery against archived request files is enough to reproduce the ledger.

## 3. Discovery probes (what produced the dev core)

`swarmlab/prompts.py` — general text, no paper-specific answers:

* stage ledger: every selection/stopping decision names its artifact and consumer;
* keep-one-of-many: how many candidates survive and whether discarded ones can still
  be exercised by the reported evaluation;
* stored witness: what is stored per test case, how many times it is replayed, whether
  it can be replaced or re-sampled;
* premise → transformation → broken premise → consequence;
* unit mismatch (what the mechanism diversifies vs what the metric aggregates) and
  sharing (one representation consumed by several heads/layers/components).

The NNSmith core was produced by the keep-one-of-many + stored-witness probes. Without
the stored-witness probe (dev-v6) the record was paper-level; with it (dev-v9) the
record cited `input_gen.py` and `cli/fuzz.py` spans as well.

## 4. Transport

`swarmlab/llm.py` streams responses with `include_usage`, enforces a total deadline
(not just a per-read timeout), archives raw SSE plus the reconstructed response, and
disables thinking on the finalisation turn so a long final JSON is not truncated by
reasoning tokens. The non-streaming transport stalled for more than 15 minutes on one
NNSmith finalisation in v3.
