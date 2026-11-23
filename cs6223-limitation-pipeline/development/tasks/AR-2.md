task_id: AR-2
serves: course artifact: all documents in English (part 1)
dag_node: AR
executor: codex
model_profile: medium
limits: {attempts: 2, gpu: none, network: 0}
branch: agent/AR-2/translate-a
worktree: /home/somehow6/lesson/cs6223-wt/AR-2
reason: translation; deliver in <=30 min
allowed_paths: [docs/00_project_overview.md, docs/01_related_work_codeside.md, docs/02_schema.md, docs/03_codeside_spec.md, docs/04_pilot_flexprefill.md, docs/05_dataset.md, docs/prompts/, TASKS.md, results/README.md, data/README.md]
non_goals: [other docs, code, README.md]

## Goal
Translate to clear, accurate ENGLISH, in place (same file names): docs/00_project_overview.md, 01_related_work_codeside.md, 02_schema.md, 03_codeside_spec.md, 04_pilot_flexprefill.md, 05_dataset.md, everything under docs/prompts/, TASKS.md, results/README.md (and data/README.md if it exists and has Chinese). Keep tables, code blocks, commands, file paths, identifiers, schema field names and quotes exactly. Prompt templates under docs/prompts/ are DOCUMENTATION of what was sent to models: translate the explanation, and keep the prompt text itself in its original language but add an English translation block under it labelled 'English translation (documentation only)'. Where a sentence is in doubt, translate literally and add '[translator note: ...]'. Verify no CJK remains outside quoted original-language prompt text and dataset quotes: grep -nP '[\x{4e00}-\x{9fff}]'.
Rules: CLAUDE.md (Chinese; read it) and AGENTS.md. Never read or print anything under /home/somehow6/LLM_API_KEY/. No secrets, no PDFs, no paper text in anything you write. Do not edit paperside/ (a teammate's code), third_party/, out/, docs/13_limitset_results.md (the controller finishes it). Do not run git add/commit. All documents you write are ENGLISH. Keep meaning exactly when translating; do not invent results. Do not change runtime behavior of code (comments, docstrings and docs only unless the package says otherwise).
## Checks
- grep -rlP '[\x{4e00}-\x{9fff}]' on the allowed files lists only prompt originals / dataset quotes

STATUS: PARTIAL
COMMITS: pending controller commit
EXECUTOR: codex; requested medium -> actual model id unavailable; effort unavailable
SUMMARY: Translated the project overview and results README; the remaining requested documents and prompt explanations still need translation.
CHECKS: grep -rlP '[\x{4e00}-\x{9fff}]' on existing allowed files; FAIL: Chinese remains in docs/01–05, docs/prompts, TASKS.md, and preserved path placeholders in results/README.md. git diff --check; PASS. git status; PASS: overview and results README modified before this return block.
GPU: none
SELF-REVIEW: Scope checked with git status; only allowed documents and this required return block were written. Original paths and identifiers retained. Full translation and CJK requirement remain unmet; no code or runtime behavior changed.
RISKS: Partial translation requires completion and review for accuracy; results/README.md retains Chinese path placeholders to preserve paths exactly. data/README.md does not exist.
