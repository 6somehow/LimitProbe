task_id: LS-22c
serves: finish the multi-label scorer (fix the gaps listed in the LS-22b return block in development/tasks/LS-22b.md)
dag_node: LS
executor: codex
model_profile: medium
limits: {attempts: 2, gpu: none, network: 0}
branch: agent/LS-22/limitset2
worktree: /home/somehow6/lesson/cs6223-wt/LS-22
reason: fix listed gaps; deliver in <=20 min
allowed_paths: [scorer_limitset/, scripts/limitset/compare.py, tests/test_limitset_scorer.py, tests/test_limitset_dataset2.py, tests/test_limitset_compare.py, docs/12_limitset2.md]
non_goals: [reading data/limitset2/labels.jsonl or REVIEW.md (FORBIDDEN), runner changes, model calls]

## Fix exactly
1. The judge prompt for a multi-label case returns, per prediction index, `matched` AND a `confidence` in [0,1]; greedy one-to-one assignment (one prediction at most one label, one label at most one prediction) orders matches by confidence then by index; deterministic.
2. Category: each label uses ITS OWN category_code (not the case's first category); aggregate by category over labels.
3. Judge unavailable for one label: that label is excluded from the denominator and counted, others still scored; a case with all labels unavailable is excluded from the case denominator.
4. Per-case-repeat batching: chunk predictions by 30 as before but never produce a prediction matched twice across chunks (resolve by confidence at assignment).
5. CLI works end to end for limitset2 shape: `--dataset limitset2 --labels PATH` where labels have `label_id`, `case_id`, `category_code`, fields like the limitset English labels (invent a fixture; do NOT open the real data/limitset2/labels.jsonl).
6. Strong tests: confidence ordering, mixed-category case, unavailable label, shared prediction assigned once, regression: single-label limitset scores identical to before.
Rules: CLAUDE.md; never read /home/somehow6/LLM_API_KEY/.
## Checks
- /home/somehow6/miniconda3/envs/findlimit/bin/python -m pytest -q -> all pass
