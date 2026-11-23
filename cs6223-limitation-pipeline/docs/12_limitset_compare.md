# Comparing limitset systems

Run `conda run -n findlimit python scripts/limitset/compare.py --system pipeline=SCORE_DIR:PRED_DIR --system baseline=SCORE_DIR:PRED_DIR --split test --out comparison.md --json comparison.json`. Repeat `--system` for each system. The prediction directory and JSON output are optional. Each score directory must contain `score.json`; prediction directories may contain `predictions.jsonl`, `cost.jsonl`, and `run_manifest.json`.

Coverage uses cases in the selected split. Cases flagged judge unavailable and cases with unknown outcomes are excluded from the denominator and listed separately. The intervals are Wilson 95% intervals; the sample is tiny. Per-case results rank available found outcomes and list covered fields. Repeat stability excludes unavailable and unknown repeats. Finding counts are averaged over prediction records for each case.

Evidence tiers and confidence bands describe whether values are present in findings, not their quality. Confidence is uncalibrated. Cost records must identify their case to be assigned to the selected split. Manifest totals are used only when its `case_ids` exactly match that split; otherwise missing costs are `n/a`. Wall time is divided by the number of split cases. No accuracy, precision, or false-positive rate is inferred from these positive cases.
