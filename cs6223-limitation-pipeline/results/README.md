# Result snapshots (updated 2026-11-11)

Copied from `out/` (`out/` itself is not committed). The temporary development notes (hand-off sheets, progress and draft reports) were removed from the artifact.

- `step2_merged/<paper>/merged_runN.json`: final step 2 results (routes A + B, three runs).
- `pipeline/<paper>/limitations.json`: limitations passed to 3b (from merged_run1).
- `pipeline/<paper>/3b.json`: 3b conclusions; `3b.detail.json`: original quotes, votes per round, needs_review.
- `pipeline/candidates.json`: candidate list across five papers.
- `pipeline/` was rerun with Zhaopeng's `paper_side.json` (2026-11-11; see git history for the original stub version); `candidates.json` includes blind review labels.
- `review/blind_review_labels.json`: Claude subagent blind review labels for route B additions (228 items, one reviewer, not human annotations).
- `step4/`: step 4 findings. `limitations_for_tests.json` is the single file for Shanghao (each item includes the full Limitation and 3b); an optional `HANDOFF.md` that explains it is generated on demand by `scripts/make_handoff_doc.py` (not committed). Each paper has `findings.json`, `llm_records.json` (deduplication votes and paper-side conditions), `review_queue.json` (test order), and `summary.md`. See `docs/09_step4_findings.md`. Each paper also has `<id>/limitations_for_tests.json` and `<id>/HANDOFF.md`; generate these for a new paper with `python -m pipeline run <id>` (`docs/10_pipeline.md`).
- `3b_pilot/`: 3b results for the 13 draft FlexPrefill limitations and the known-answer tests (`eval_cases.json`).
