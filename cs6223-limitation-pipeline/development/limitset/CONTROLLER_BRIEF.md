# Controller brief: Limitation Testset E2E (2026-11-23)

You are the controller (Claude Sonnet 5.5, medium). You dispatch, review, integrate. You do not write bulk code yourself. Code agents are **Codex sub agents only** (user order). Rules of the harness: `/home/somehow6/work/paseo-host-setup/templates/` (read `harness-workflow.md`, `harness-models.md`, `dispatch/codex.sh`). Project rules: `CLAUDE.md` in the repo root. Replies to the user: short plain Chinese. Commit messages: English, trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Goal (user)

1. Upgrade code side and test side so they **fully use the new paper side** (swarm: `origin/zhaopeng/agentswarm-team-handoff`, `paperside/tools/agentswarm-study`, `method-limitations`).
2. New-version E2E test on `/home/somehow6/lesson/CS6223/CS6223_Limitation_Testset.zip` (17 cases, one reference limit each, 3 categories: applicability_limitation 7, mechanism_origin_unclear 2, method_shortcoming 8). Normalize the data. Split into **validation** and **test**.
3. Targets: (a) find as many limits as possible; (b) the limits reach the level of the reference labels (coverage of the reference limit: mechanism, conditions, evidence, category); (c) the report gives each limit a scientific confidence score, aligned with the course **Software Testing**: software under test -> computer-systems research project; bug -> limit.

## Hard rules

- Python only: `/home/somehow6/miniconda3/envs/findlimit/bin/python`. `paseo`/`node` need `export PATH=/home/somehow6/miniconda3/bin:$PATH`.
- Never read, print, or commit anything under `/home/somehow6/LLM_API_KEY/`. SoCLaaS env only: `set -a; . /home/somehow6/LLM_API_KEY/SoCLaaS/soclaas.env; set +a; unset SOCLAAS_MODEL`. Model calls go through the local relay (`pipeline/e2e.py` Relay); calls without the relay hang.
- Small commits, specific `git add <paths>`, never `git add -A`. No force push, no history rewrite, **no push** (ask the user). Do not touch the user's untracked files: `.gitignore`, `docs/E2E_PLAN_P0_2026-11-15.md`, `docs/*.pdf`, `shanghao_*`, `slides/`, `CS6223_Limitation_Testset.zip`.
- Ask the user before: deleting files, sudo, networking changes, installing packages in shared envs. Never `pkill -f`.
- **Blindness:** the pipeline never reads `labels/`, `reference_material/`, `evaluator_evidence/`. Only the scorer reads labels. Case 12 (ODRP) must not get R03 (OneSidedMW) as input. Run each case in its own isolated directory.
- Confidence levels stay **uncalibrated and labelled so** until a calibration run on the validation split supports a claim. Never report accuracy/precision/FP-rate (the set has one reference limit per paper and no negatives); report coverage (recall of reference limits), with CI.
- The zip contents are third-party (papers). Extract to `/home/somehow6/lesson/CS6223/limitset-raw/` (outside git). In the repo commit only normalized derived data (`data/limitset/`: cases, labels, splits, manifests with hashes), code, docs, results JSON/MD. No PDFs.
- Do not commit `results/` that contain model output with secrets; scan every to-be-committed diff for key strings before commit.

## Facts you need

- Zip: has `README_zh.md`, `DATASET_CARD_zh.md`, `evaluation/RUBRIC_zh.md`, `schemas/{input,label,prediction}.schema.json`, `scripts/{validate_dataset,prepare_inputs,export_case,score_annotations}.py`, `inputs/test.jsonl` (17 cases), `labels/test_labels.jsonl`. 12 papers bundled; 5 (CS6223-02,05,07,09,17) are downloaded by `prepare_inputs.py` (needs network, SHA-256 checked). Only InfiniGen (CS6223-03) has pinned code (commit 3754f52d). Other 16 cases: **paper-only** mode (max A1, quotes verbatim from PDF). Existing split file marks all 17 as `test`; we re-split.
- Proposed split (freeze before any run, record the rule): **validation = CS6223-01,02,03,04** (the 4 development papers of the project; cover all 3 categories; 03 has code), **test = the other 13**. Controller may adjust for category balance but must freeze `data/limitset/splits.json` first and never tune on test.
- Pipeline: step 4 -> `limitations_for_tests.json` (Findings) -> `checklimits` (L0-L3 / A0-A2, defeaters D1-D14, paper-only max A1). Entry: `python -m pipeline e2e <id>` (`--no-run` for frozen step-4), `paper-only`. Reports: `results/tests/<id>/`, `results/report/<id>/LIMITATIONS.md`. Contract `checklimits/CONTRACT_TEST_REPORT.md` (`checklimits-test-report/1`).
- New paper side is on `origin/zhaopeng/agentswarm-team-handoff` (not merged here). A prior scratch merge ran in a worktree; swarm outputs have **no interface into step 4** and the candidate -> Finding converter does not exist. Evidence of swarm benefit so far is weak: measure it, do not assume it.
- Prior state: 7 papers + Tessera done; `docs/11_workflow_report_draft.md`; commits on `somehow6/e2e` are not pushed.

## Work packages (each = one Codex task package `development/tasks/<ID>.md`, own worktree, own branch `agent/<ID>/<name>`)

| ID | Scope | Depends |
|---|---|---|
| LS-00 (you) | Set up harness: `tools/dispatch/codex.sh` adapter (sed PROJECT=cs6223, CONDA_ENV=findlimit, worktrees `/home/somehow6/lesson/cs6223-wt/<ID>`), `development/state.md`, merge `origin/zhaopeng/agentswarm-team-handoff` into the integration branch (`somehow6/e2e`) and fix conflicts; run tests. Freeze split. | - |
| LS-01 | Normalize dataset: extract zip, run its `validate_dataset.py`, `prepare_inputs.py` (network via `NET=1`); write `scripts/limitset/normalize.py` -> `data/limitset/{cases.jsonl,labels.jsonl,splits.json,manifest.json}` (hashes), per-case isolated input dirs, map to pipeline artifact/paper entries; tests. | LS-00 |
| LS-02 | Swarm candidate -> pipeline: converter from swarm/gap-receipt candidates (`agentswarm-study` outputs) to the paper-side schema that step 4 reads and to the checklimits paper-only/analysis lane; code side uses them (3b verification, step 4 integration, `process_confidence`); keep schema compatibility or bump `SCHEMA_VERSION` per CLAUDE.md rule 1. | LS-00 |
| LS-03 | Runner `python -m pipeline limitset run --split validation\|test [--case ID] [--repeats N]`: per case isolated dir, relay, paper-only or with-code E2E, outputs predictions JSONL per `schemas/prediction.schema.json` plus per-run evidence; N repeats for stability. | LS-01, LS-02 |
| LS-04 | Scorer: match predictions to reference labels (deterministic fields + blind LLM judge with `RUBRIC_zh.md`, judge model/prompt recorded, independent from generator run); coverage by category and by label field (mechanism, conditions, defeaters, evidence location, category, disclosure); novelty of extra findings flagged for human review, not counted wrong; Wilson/bootstrap CI; wraps the zip's `score_annotations.py`. | LS-01 |
| LS-05 | Confidence model + report in software-testing terms (see below); `LIMITATIONS.md` and a case-level report; doc `docs/12_testing_course_mapping.md`. Calibration check on validation: reliability table; if n is too small, say so. | LS-02 (schema), parallel with LS-03/04 |
| LS-06 | Run validation (tune on it only), freeze code + prompts + config by commit SHA, run test **once** (3 repeats), score, write `docs/13_limitset_results.md`. | all |

Parallel limit: 3-4 Codex agents. Review each return block yourself (diff, tests, key scan) before you commit. Use a different session than the author for review of LS-02/LS-05 (Claude `claude-opus-5-5` medium via dispatch, or a second Codex review). Report to the user: after LS-00/01 (data + split), after validation run, after test run. Ask the user only for real decisions.

## Confidence scoring (LS-05 content; software-testing mapping)

Map and implement, each with a definition in the doc:
- test oracle problem -> reference label + defeater list as oracle; executed test (L0-L3) vs analysis (A0-A2) as evidence strength; "no oracle" -> not scored as yes/no.
- fault detection effectiveness / test adequacy -> **limit coverage** = reference limits found / total, per category (applicability, mechanism, shortcoming), with CI; extra finds = candidate novel limits (triage queue), not false positives.
- flaky tests / repeatability -> stability across N repeats (fraction of repeats that re-find a limit; matched by claim similarity).
- test independence / N-version -> agreement across sources (paper-side swarm vs code side vs test result); independent judge.
- bug severity/priority -> limit impact/importance (existing `process_confidence` importance) kept separate from confidence.
- confidence = ordinal band from explicit, auditable evidence items (not one opaque number): evidence tier, replication, cross-source agreement, open defeaters, code availability (paper-only caps). Show the items next to the band. State `uncalibrated` until reliability on validation supports a statement; then give observed hit rate per band with CI and the n.
- Report sections: summary, coverage table (by category / split), per-limit table (claim, category, evidence, confidence band + items, defeaters, disclosure status), threats to validity (17 cases, 1 label each, no negatives, LLM judge, paper-only), reproducibility (commit SHAs, model IDs, seeds, hashes).

## Done when

Validation + test results committed (local), `docs/13_limitset_results.md` written with honest limits, all tests green (`/home/somehow6/miniconda3/envs/findlimit/bin/python -m pytest -q` and `checklimits/`), a short Chinese summary sent to the user, push left to the user.
