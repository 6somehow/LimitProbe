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

STATUS: DONE
COMMITS: pending controller commit
EXECUTOR: codex; requested medium -> actual model id unavailable; effort unavailable
SUMMARY: Translated both specified documents into English while preserving their technical content, links, identifiers, and reported results; no runtime behavior changed.
CHECKS: grep -nP '[\x{4e00}-\x{9fff}]' docs/01_related_work_codeside.md and docs/02_schema.md; PASS (no matches). git diff --check; PASS. git status; PASS (changes limited to the two documents and this return block).
GPU: none
SELF-REVIEW: Scope and translation completeness checked against both source documents and Chinese-character scan; technical identifiers, links, figures, and commands preserved; runtime and child-process checks do not apply to documentation-only changes.
RISKS: Publication claims were translated as supplied and were not independently verified, as required by the task scope.
