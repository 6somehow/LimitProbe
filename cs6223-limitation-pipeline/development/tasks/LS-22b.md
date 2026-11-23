task_id: LS-22b
serves: limitset2 multi-label scorer (continues LS-22: runner --dataset part is already DONE in this worktree; read the LS-22 return block in development/tasks/LS-22.md)
dag_node: LS
executor: codex
model_profile: medium
limits: {attempts: 2, gpu: none, network: 0}
branch: agent/LS-22/limitset2
worktree: /home/somehow6/lesson/cs6223-wt/LS-22
reason: scorer part; deliver in <=25 min
allowed_paths: [scorer_limitset/, scripts/limitset/compare.py, tests/test_limitset_scorer.py, tests/test_limitset_dataset2.py, tests/test_limitset_compare.py, docs/12_limitset2.md]
non_goals: [reading data/limitset2/labels.jsonl or any REVIEW.md (FORBIDDEN), editing the runner, running models]

## Goal (the remaining items of LS-22 spec in development/tasks/LS-22.md, items 2 and 3)
Scorer `python -m scorer_limitset`: `--dataset limitset|limitset2`, `--labels PATH` (limitset2 labels are English: no --labels-en needed); several labels per case (key `label_id`): judge every label against the case's predictions (batched per case-repeat as now; one judge call per (case, repeat, label)); one prediction can match at most one label (deterministic greedy assignment by judge confidence/order); per label found/not found + field coverage; aggregate coverage over LABELS (found/total) and over CASES (>=1 label found), each with Wilson CI, by category; judge_unavailable excluded and counted; stability across repeats; score.json keeps the `cases` list compatible with scripts/limitset/compare.py and the report (add a `labels` list per case); extend compare.py to print both denominators. The single-label limitset must score exactly as before (regression test with a fixture). Leakage test: prompt texts of all mechanism versions and the B1 prompt share no lowercase word 5-gram with data/limitset2/labels.jsonl; read the file only at test run time via Path, skip if missing; YOU must not open it. Tests with invented fixtures. docs/12_limitset2.md short.
Rules: CLAUDE.md; never read /home/somehow6/LLM_API_KEY/.
## Checks
- /home/somehow6/miniconda3/envs/findlimit/bin/python -m pytest -q -> all pass

STATUS: PARTIAL
COMMITS: pending controller commit
EXECUTOR: codex; requested medium -> actual model id unavailable; effort unavailable
SUMMARY: Added dataset selection, multi-label scoring with greedy assignment, label and case coverage, comparison output, synthetic assignment coverage, documentation, and a held-out prompt leakage test. Legacy scorer path remains unchanged. The multi-label implementation is incomplete: relay prompts do not request confidence, category comparison uses the case's first category, and per-case-repeat judging retains legacy chunking and fallback calls.
CHECKS: conda run -n findlimit python -m pytest -q --basetemp=/tmp/codex-LS-22b-1/final; PASS (261 passed, 3 skipped; leakage skipped because labels absent). Initial full run INVALID_RUN: scratch parent missing. git status --short PASS; git diff --check PASS.
GPU: none
SELF-REVIEW: Synthetic fixture checks a shared prediction is assigned once and both denominators; existing suite checks legacy scoring and comparison. Leakage check is present but skipped. Confidence ordering, mixed-category cases, unavailable behavior, and CLI multi-label schema need stronger tests and fixes; no independent review requested.
RISKS: Do not integrate as complete until the listed multi-label gaps are fixed. Existing changes to runner and LS-22 package predate this task. Actual model and effort identifiers were not exposed.
