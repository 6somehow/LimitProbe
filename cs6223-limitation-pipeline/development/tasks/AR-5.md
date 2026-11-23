task_id: AR-5
serves: course artifact: relevant experimental data and scripts, self-contained and reproducible offline
dag_node: AR
executor: codex
model_profile: medium
limits: {attempts: 2, gpu: none, network: 0}
branch: agent/AR-5/results-bundle
worktree: /home/somehow6/lesson/cs6223-wt/AR-5
reason: data bundling + reproduction script; deliver in <=30 min
allowed_paths: [results/limitset_final/, scripts/limitset/make_results.py, scripts/limitset/reproduce_tables.py, scripts/limitset/bundle_results.py, data/limitset/labels_en.jsonl, data/limitset/labels_en.manifest.json, tests/test_limitset_bundle.py, results/limitset_final/README.md]
non_goals: [docs/13 (controller), code behavior changes, copying PDFs or run input dirs]

## Facts (source run outputs live in the MAIN checkout /home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/out/, not in your worktree; read them by absolute path, read-only)
limitset2 systems -> prediction file, score dir, extra:
- b1: out/limitset2/b1/predictions.jsonl, out/limitset2/g_b1; run dir out/limitset2/b1 (run_manifest.json, cost.jsonl)
- b1x2: out/limitset2/b1x2.jsonl (+ .origins.json, .summary.json), out/limitset2/g_b1x2 (inputs: b1 and out/limitset2/b1b)
- v3c_xtest2: out/limitset2/a1c_full.jsonl (merged: first run out/limitset2/a1c plus retries out/limitset2/a1c_retry2_LS2-05/09/11), score out/limitset2/g_a1c; per-case runs/*/r1/mechanism_evidence.json and evaluation_critiques.json
- union_xtest2: out/limitset2/union.jsonl (+ origins, summary), score out/limitset2/g_union (may still be pending: skip and report if score.json is missing)
- b1_sonnet: out/limitset2/b1_sonnet/predictions.jsonl, score out/limitset2/g_b1_sonnet
- v3c_sonnet: out/limitset2/a1c_sonnet/predictions.jsonl, score out/limitset2/g_a1c_sonnet (+ mechanism_evidence.json per case)
- union_sonnet: out/limitset2/union_sonnet.jsonl (+ origins, summary), score out/limitset2/g_union_sonnet
validation (4 development cases, judge gpt-6.1-terra): out/limitset/g_val4 (predictions out/limitset/val4/predictions.jsonl), g_valsw (out/limitset/valsw), g_val_mech (out/limitset/val_mech/predictions_fixed.jsonl), out/limitset_baselines/g_b1_val (b1_val), g_b2_val (b2_val).
Also copy the scorer-only English labels data/limitset/labels_en.jsonl and labels_en.manifest.json from the main checkout (derived data, translation of the dataset labels; document that it is scorer-only).
## Goal
1. scripts/limitset/bundle_results.py (documented, deterministic) that copies the above into results/limitset_final/<dataset>/<system>/ : predictions.jsonl, score.json, run_manifest.json, cost.jsonl when present, mechanism_evidence.json per case when present (under cases/<case>/). NEVER copy input/ directories, PDFs, logs that may contain keys; scan every copied file for the strings 'sk-', 'Bearer ', 'api_key', 'SOCLAAS' and the raw dataset PDFs; fail if found. Run it.
2. scripts/limitset/reproduce_tables.py: rebuilds the tables of docs/13 offline from results/limitset_final/ (reuse/generalize scripts/limitset/make_results.py: add --root so it reads the bundle layout; keep the old behavior for out/ paths), writes a markdown file and prints it. No network, no model, deterministic. Add a test that runs it on a tiny synthetic bundle and one that checks the real bundle reproduces the same numbers as the committed score.json files.
3. results/limitset_final/README.md (English): layout, what each file is, which system is which (names as in docs/13: B1, B1 x2, v3c, v3c + B1 for x-test-2 and Claude Sonnet 5.5; validation arms), judge settings, known caveats (relay aliases; failed runs counted as misses; retries), sizes; how to re-score for real (command lines with environment variable names only).
4. Report in your return block the total size of results/limitset_final and any system skipped.
Rules: CLAUDE.md (Chinese; read it) and AGENTS.md. Never read or print anything under /home/somehow6/LLM_API_KEY/. No secrets, no PDFs, no paper text in anything you write. Do not edit paperside/ (a teammate's code), third_party/, out/, docs/13_limitset_results.md (the controller finishes it). Do not run git add/commit. All documents you write are ENGLISH. Keep meaning exactly when translating; do not invent results. Do not change runtime behavior of code (comments, docstrings and docs only unless the package says otherwise).
## Checks
- conda run -n findlimit python scripts/limitset/reproduce_tables.py --root results/limitset_final --out /tmp/codex-AR-5-1/tables.md -> exit 0, tables match the committed score.json numbers
- /home/somehow6/miniconda3/envs/findlimit/bin/python -m pytest -q tests/test_limitset_bundle.py -> pass
