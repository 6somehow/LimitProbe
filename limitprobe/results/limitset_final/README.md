# Limitset results bundle

This bundle contains saved predictions and scores. It supports offline table reproduction; re-scoring calls a judge and is a separate operation. The scorer-only English translations are in `data/limitset/labels_en.jsonl` and `labels_en.manifest.json` at the repository root. They are evaluation data, not pipeline input.

Each `<dataset>/<system>/` directory contains `predictions.jsonl` and `score.json`. Where available, `run_manifest.json` records the run settings and `cost.jsonl` records calls and costs. `cases/<case>/mechanism_evidence.json` holds mechanism-run evidence; evaluation critiques are also included where available. Union and B1 x2 directories include origin and summary files when present. Inputs, PDFs and logs are excluded.

For limitset2, `b1` is B1, `b1x2` merges two B1 runs, `v3c_xtest2` is v3c, and `union_xtest2` is v3c + B1, all using x-test-2. The corresponding Claude Sonnet 5.5 arms are `b1_sonnet`, `v3c_sonnet`, and `union_sonnet`. Validation contains `val4` (pipeline v1, paper-only plus enrichment), `valsw` (pipeline plus swarm), `val_mech` (mechanism v1), `b1_val` (B1), and `b2_val` (B2, opencode).

The limitset2 scores use judge gpt-6.1-terra with one repeat across 11 papers and 22 labels. Validation uses four development cases and two judge repeats where run. Model names are relay aliases; they do not independently establish the underlying model identity. Failed prediction runs count as misses. The x-test-2 v3c predictions merge the initial run with retries for LS2-05, LS2-09, and LS2-11; evidence for a retried case comes from the later run. The cost summary based on evidence is an estimate and does not include token totals.

The bundle occupies approximately 8.0 MiB on disk (excluding the scorer-only labels). All listed systems are present. Rebuild the tables without network access:

```sh
conda run -n findlimit python scripts/limitset/reproduce_tables.py --root results/limitset_final --out /tmp/tables.md
```

Real re-scoring requires the scorer, its dataset inputs, a configured judge endpoint and credentials, and incurs model calls. This bundle alone does not contain the inputs or credentials needed for that operation; the saved scores suffice for the offline tables.

## Re-scoring for real (needs a model service)

The tables in this bundle are rebuilt offline (`python scripts/limitset/reproduce_tables.py --root results/limitset_final --out tables.md`). Re-scoring the predictions needs a judge model behind a local OpenAI-compatible relay (the relay holds the key; the scorer only sees a placeholder). Set the environment variable names below; never write key values into files.

```bash
# judge: OpenAI gpt-6.1-terra through a relay on port 8789 (variables read by scorer_limitset)
export LIMITSET_JUDGE_MODEL=gpt-6.1-terra LIMITSET_JUDGE_RELAY_PORT=8789 LIMITSET_JUDGE_CHUNK=150

# limitset2 (22 human-reviewed labels): needs the Limitation Testset root for its schemas
python -m scorer_limitset --pred results/limitset_final/limitset2/b1/predictions.jsonl \
  --root <path-to-CS6223_Limitation_Testset> --dataset limitset2 --labels data/limitset2/labels.jsonl \
  --out /tmp/rescore_b1 --judge relay --workers 8

# development cases (4 cases; Chinese labels translated to English, scorer-only)
python -m scorer_limitset --pred results/limitset_final/validation/b1_val/predictions.jsonl \
  --root <path-to-CS6223_Limitation_Testset> --splits data/limitset/splits.json \
  --out /tmp/rescore_val_b1 --judge relay --labels-en data/limitset/labels_en.jsonl --workers 4
```

The judge accepts only its default temperature, so a re-score is not bit-for-bit identical to the committed `score.json` files; expect small differences in the per-label decisions.
