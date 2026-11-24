# Step 2 (final B) → Step 3b: End-to-end run (2026-11-06)

```bash
python scripts/run_pipeline.py --model x-test-2 --repeats 3 --parallel 1 --workers 3   # Results in out/pipeline/<id>/
python scripts/summarize_pipeline.py [--labels <blind-review labels JSON>]                       # Summary + out/pipeline/candidates.json
```

- Input: `out/routes_merged/<id>/merged_run1.json` (A plus reviewed sweep and agent results, deduplicated; see `06_two_routes.md`).
- `to-limitations --include-variants`: also exports B's `mechanism_variant` with `effect_type` set to `path_change` (the schema is unchanged; the default still skips these). A's own `mechanism` regions are not exported.
- 3b: `consensus`, 3 rounds, `3b-v3`, `x-test-2` (actual model `deepseek-v4.1-flash-1017`). Only FlexPrefill has a paper-side stub; scope is unknown for the other four papers.
- Keep concurrency low (`--parallel 1 --workers 3`) to avoid rate limiting (429). A failed 3b call raises an error and exits; it is not treated as “not found”. The cache prevents repeat charges on reruns.

## Fix

When `scope_check.py` encountered a non-Boolean condition, z3 raised an exception and 3b failed for the entire paper. B uses a wider variety of conditions than A, such as `not gqa_interleave` and a single integer name in `path_prefix`. z3 exceptions are now converted to Untranslatable, making scope unknown; a regression test was added.

## Results

| Paper | Source | Limitations | Not stated in paper or docs | Stated somewhere | Needs manual review |
|---|---|---|---|---|---|
| FlexPrefill | A | 29 | 22 | 7 | 2 |
| FlexPrefill | B | 17 | 11 | 6 | 1 |
| InfiniGen | A | 4 | 4 | 0 | 0 |
| InfiniGen | B | 16 | 15 | 1 | 0 |
| MInference | A | 11 | 11 | 0 | 0 |
| MInference | B | 39 | 39 | 0 | 2 |
| NNSmith | B | 36 | 30 | 6 | 2 |
| SparTA | B | 3 | 2 | 1 | 0 |

There are 155 in total: not_found 134, found 12, weaker 5, boundary_mismatch 3, contradicted 1.

Among the 83 labeled additions from B, blind review marked 29 useful, of which 3b marked 24 not found. These are currently the strongest candidates, listed in `out/pipeline/candidates.json` (`label == "useful"` and `result == "not_found"`).

FlexPrefill scope (based on the stub): 2 are in_scope and not found (`kl_div < tau`, `seq_len <= min(vertical_size, slash_size) * block_size`); 3 are scope_edge and not found (`q_len != k_len` twice, `q_len != 1`). Most others are unknown.

## Notes

- **not_found does not mean a finding.** 35 “real but not useful” and 12 “wrong” entries were also marked not found. 3b only answers whether something is stated; it does not decide whether it is worth reporting.
- Blind review labels cover only some entries, each reviewed by one Claude reviewer.
- The four development-set papers have no paper-side data, so their scope is all unknown; whether they fall within the paper's scope cannot yet be determined.
