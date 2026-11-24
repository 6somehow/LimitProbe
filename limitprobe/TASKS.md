# Code-side task list (Wanting)

Status: `[x]` completed (preparation for this work), `[ ]` pending. Each milestone has acceptance criteria. Suggested order: M1 → M2a and M2b in parallel → M3 and M4 in parallel → M5 → M6.

Step 2 has two technical routes, both to be implemented and compared: **A static analysis (no LLM)** and **B LLM extraction**, see `docs/06_two_routes.md`.

## M0 Preparation (completed)

- [x] Select pilot: FlexPrefill (official repository, pinned commit) — `docs/04_pilot_flexprefill.md`
- [x] Code-side related work and tool selection — `docs/01_related_work_codeside.md`
- [x] Shared schema v0.1.0 (pydantic + JSON Schema) — `schema/`, `docs/02_schema.md`
- [x] Manual pilot gold: 16 regions, 13 code-side limitations, 13 draft 3b verifications, 7 draft findings — `data/pilot_flexprefill/`
- [x] Extractor v0 (Python ast) + evaluation script + CLI + tests; pilot recall 16/16, 10 extra predictions classified
- [x] Specifications and prompt templates for 3b and step 4 — `docs/03_codeside_spec.md`, `docs/prompts/`
- [x] Development dataset: artifact.json for SparTA, MInference, InfiniGen, NNSmith (pinned commits) + `scripts/fetch_dataset.sh` — `docs/05_dataset.md`
- [x] Extractor supports class methods, `self.method()` calls, one level of nested functions, and `--package-root`; first run completed on the four papers
- [x] Pure LLM control (`codeside/llm_extractor.py`): context construction, prompt, output validation, pluggable client; `extract-llm` and `compare` commands
- [x] Route B (`codeside/hybrid_extractor.py`): A produces candidates, LLM only adds call edges and missed findings without deleting A results, conclusions validated by code; `extract-hybrid`, `stability`, `scripts/run_routes.py`

## M1 Align with the team (week 1, meeting required)

- [ ] All three review the schema, answer the 5 open questions in `docs/02_schema.md`, and finalize v0.2.0
- [ ] Agree with Zhaopeng: step 1 output for FlexPrefill replaces `paper_side_stub.json` (same fields as the stub)
- [ ] Agree with Shanghao on the Finding.witness_hint format; hand F01–F07 to him for initial CPU execution confirmation
- [ ] Review `draft_verifications_3b.json` and `draft_findings.json` together; save reviewed versions separately as gold (do not overwrite drafts)

Acceptance: schema v0.2.0 merged; all three can validate their output with `python -m codeside.cli validate`.

## M2a Route A: static extractor v1 (noise reduction + configuration integration)

- [ ] **Path feasibility pruning**: when calling a callee, bind formal parameters to argument expressions; rewrite callee conditions using caller names; use z3 to check whether “path prefix ∧ condition” is satisfiable, discarding it if not (target: remove 6 decode noise predictions)
- [ ] **Redundancy detection**: when the prefix implies an assert condition, mark it subsumed and do not output it as a limitation (target: remove 2 for `triton_bnhd_pool`)
- [ ] **Internal invariant filtering**: downgrade conditions that depend only on internally computed values and have no data dependency on entry parameters (target: remove 2 for `block_idx`)
- [ ] **Configuration integration**: read configuration keys (such as `flex_prefill_min_budget`) from Binding and annotate configuration dependencies in region conditions
- [ ] **Call resolution**: package-level imports and `self.method` calls; use LLM for dynamic dispatch (`docs/prompts/dispatch_resolution.md`); candidate edges must point to existing definitions
- [ ] **Mode switches without early return**: also produce a region when a branch calls a mechanism-related function (such as InfiniGen `if warmup: skew(...)`)
- [ ] **Two-branch dispatch / switch to another implementation**: two branches return different implementations (NNSmith GradSearch / SamplingSearch, MInference dilated / streaming); schema needs another outcome (proposed `alternative`, see question 6 in `docs/02_schema.md`)
- [ ] **`ClassName.method(self, ...)` calls** and **inheritance** (look in the parent class when the subclass does not override)
- [ ] **Constructor attributes**: when a condition depends on `self.x`, analyze the assignment condition for `self.x` in `__init__` (such as NNSmith's `self.differentiable`)
- [ ] Add a minimal case in `tests/fixtures/` for every rule

Acceptance: pilot recall remains 1.00, extra predictions ≤ 2; all `pytest` tests pass; all gaps listed in the first-run results for the four papers (`docs/05_dataset.md`) are covered.

## M2b Route B: LLM extraction

- [ ] Confirm model ID with the team (currently `x-test-2`, via SOCLAAS's OpenAI-compatible interface, key in `.env`)
- [ ] Run 3 times on the pilot, compare with route A using `compare`, and manually inspect rejected entries
- [ ] Handle overly long context: truncate by call depth, or call per function and merge
- [ ] Record a version number and reason for every prompt change; **do not repeatedly tune the prompt against gold**
- [x] B-agent variant (`codeside/agent_extractor.py`): LLM freely explores the whole repo with read-only tools; run 3 times each on 5 papers
- [x] Assess the quality of new B results (Claude subagent blind review, see “Comparison of three B approaches” in `docs/06_two_routes.md`)
- [x] B-sweep (`codeside/sweep_extractor.py`) + relevance review (`codeside/relevance_filter.py`), 3 runs each on 5 papers
- [x] Call-chain deduplication (`codeside/dedup.py`) + merge sweep and agent (`cli merge`), results in `out/routes_merged/`; blind review of a new sample found 32% useful
- [ ] Baseline method code bundled in the repo (vertical-slash, FlexGen top-k, dilated, SnapKV) remains the main noise: the paper side needs to tell us which are baselines
- [ ] Manually annotate and confirm B's final output (currently only one Claude reviewer, 38–49 results per round)
- [ ] `mechanism_variant` is skipped by default in to-limitations; `--include-variants` currently marks it temporarily as path_change; the team must decide whether to add the `alternative` outcome
- [x] Final B → 3b ran end to end on all five papers (`scripts/run_pipeline.py`, `docs/07_pipeline_b_3b.md`); fixed scope_check crashing on non-boolean conditions
- [ ] (Optional) Route C hybrid: A produces candidates, LLM only adds what A cannot

Acceptance: pilot and four papers each have rows for A and B (recall, extra, cond_exact, hallucination rate, variation across 3 runs, cost).

## M3 Gold and evaluation for the development dataset (four papers)

- [ ] Confirm entry functions for each paper with the team (`data/<id>/artifact.json` contains candidates), adding more if necessary
- [ ] For each paper, the domain lead and another person independently annotate the gold region table and code-side limitations, and calculate agreement (suggested order: NNSmith (all CPU, fastest) → MInference → InfiniGen → SparTA)
- [ ] Follow up candidate observations in `docs/05_dataset.md`: give SparTA propagation stub functions to Zhaopeng for 3a; run 3b on NNSmith's non-differentiable degradation
- [ ] If there are conclusions from the NNSmith conversation, put them in `data/nnsmith/notes.md`
- [ ] After every rule or prompt change, rerun `compare` for both routes on the four papers + pilot and record changes
- [ ] Agree on 1–2 held-out artifacts (run only once at the end, without tuning rules) to report generalization

Acceptance: all four papers have gold; recall and extra predictions for each are recorded in `docs/05_dataset.md`; held-out list is fixed.

## M4 Implement step 3b

- [x] Text preparation: paper PDF → sectioned text (switched to PyMuPDF, no sudo required, handles two columns); index README, docstrings, comments, with source and location for each passage
- [x] Retrieval: retrieve candidate passages using names in conditions, paper terms mapped by Binding, and values in conditions
- [x] LLM judgment (`codeside/verify3b.py`, evolved from `docs/prompts/3b_code_to_paper.md`), **code validates that quotes exist verbatim**
- [x] Scope judgment: Binding mapping + ScopeItem interval / set operations (z3 if needed), deterministic implementation
- [x] Evaluation coverage judgment: whether EvalPoint satisfies the region condition
- [x] Output Verification(code_to_paper)
- [ ] Compare with gold reviewed in M1 (gold does not yet exist; currently compared only with the unreviewed draft)

Acceptance: record pilot agreement with gold 3b on result and scope_status in `docs/06_3b_eval.md`.

## M5 Step 4 integration

- [x] Read paper-side Limitation + 3a (Zhaopeng's handoff package), code-side Limitation + 3b (`codeside/integrate.py`)
- [x] Deduplicate and merge: mechanically merge equivalent conditions in the same code-side function; select candidate pairs by rules within the paper side and across sides, then merge after LLM judges whether they describe the same thing (`codeside/step4_llm.py`)
- [x] Change classification to the 7 categories of schema v0.2.0, consistently count as documented only what users will read; change priority to “consequence × triggerability”; initially fill review fields using blind review
- [x] witness_hint: solve for concrete values in scope ∩ region condition (one point on each side of the boundary, `codeside/witness.py`, format `witness-v2`: add aliases; LLM writes paper-side conditions and code checks them)
- [x] Output Finding (`results/step4/`), single file for Shanghao `results/step4/limitations_for_tests.json`
- [ ] Team confirms schema v0.2.0 (7 categories, review fields), the documentation rule, and priority rule; Shanghao confirms witness-v2 format
- [ ] Manually screen `results/step4/review_queue.json` and select Findings to hand to testing
- [ ] Path prefixes do not distinguish functions at different levels of the call chain; aliases only work at a single level (record the containing function in step 2's path_prefix)

Acceptance: regenerated pilot Findings agree with reviewed gold; Shanghao can write tests directly from witness_hint.

## M6 Evaluation (with the team)

- [ ] Region table precision / recall (against gold), **routes A and B (and C) side by side**, separated by artifact and outcome type
- [ ] Downstream usability: how many conditions from both routes can be used directly for 3b scope intersection and witness solving
- [ ] Compare with dynamic traces with Shanghao: run random + boundary inputs on CPU, record actual branches, compare with the region table (region recall, region precision, boundary accuracy)
- [ ] Confusion matrix for step 4 classification
- [ ] Summarize separately by L1 / L2 / L3
