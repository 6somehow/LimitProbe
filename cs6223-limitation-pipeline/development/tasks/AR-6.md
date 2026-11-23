task_id: AR-6
serves: course artifact: all documents in English
dag_node: AR
executor: codex
model_profile: medium
limits: {attempts: 2, gpu: none, network: 0}
branch: agent/AR-6/translate
worktree: /home/somehow6/lesson/cs6223-wt/AR-6
reason: translation of a small file set; deliver in <=25 min
allowed_paths: [docs/01_related_work_codeside.md, docs/02_schema.md]
non_goals: [any other file, runtime code behavior]

## Goal
Translate these files to clear, accurate ENGLISH, in place (same names): docs/01_related_work_codeside.md, docs/02_schema.md . 
Rules: AGENTS.md. Never read or print anything under /home/somehow6/LLM_API_KEY/. Do not edit paperside/, third_party/, out/, docs/13_limitset_results.md. Do not run git add/commit. ENGLISH output. Keep meaning exactly; keep tables, code blocks, commands, paths, identifiers, schema field names and quotes unchanged; do not invent results. Comments/docs only: no runtime behavior changes. Translate EVERY Chinese sentence of every file in your list, not a sample: finish all files before you stop, then verify with: grep -nP "[\x{4e00}-\x{9fff}]" FILE (only quoted original-language prompt text or dataset quotes may remain, each marked with an English translation next to it).
## Checks
- grep -nP '[\x{4e00}-\x{9fff}]' on each listed file shows no unmarked Chinese
