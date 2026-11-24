# Mechanism generation

The default `--generator mechanism --mech-version v3` inventories mechanisms, sweeps seven general lenses, drafts candidates, and ranks and filters them. Quotes are verified against the paper or supplied code; candidates with unverifiable quotes are dropped and counted. Evaluation critiques are saved separately. Necessary conditions are lists in predictions.

Use `--mech-version v1` or `v2` for earlier arms. `--mech-no-filter` skips the final ranking and top-20 cut for v3 while retaining tagged evaluation critiques separately. Arm settings are recorded in the run manifest; use a fresh output directory for a different arm.

## Honesty: in-sample

All v3 results are in-sample: the controller studied all 17 labels when deriving the lenses. The prompt is generic and does not contain case-specific terminology or label sentences. A test checks English label word 5-grams and Chinese label character 8-grams against the four prompt templates when scorer label files are available. The generator itself does not read labels.

`--mech-version v3c` combines inventory and the lens sweep, then drafts up to three candidates per mechanism in parallel. `LIMITSET_MECH_THREADS` controls concurrency (default 6). Each chunk has a 300-second timeout and one retry; failed chunks are recorded and skipped unless all fail. Evidence records chunk counts, failures, and timings. The code ranks by non-obviousness and conditionality, deduplicates, and keeps up to 20 method candidates; `--mech-no-filter` retains all verified candidates. The default remains v3.
