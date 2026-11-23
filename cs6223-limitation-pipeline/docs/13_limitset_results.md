# Limitation testset results (2026-11-23)

Read this first. These are small-sample, descriptive numbers with several known biases (section "Threats to validity"). They are **coverage of reference limits**, never accuracy, precision or a false-positive rate: every reference has one or two reference limits per paper and there are no negative examples.

Status of the claims in the project goals:

- (a) Find as many limits as possible: measured as findings per paper (table below). More findings come with more unverified ones.
- (b) Reach the level of the reference labels: measured as coverage of the reference limit by an LLM judge (mechanism, conditions, evidence location, category, disclosure, defeaters per label).
- (c) Scientific confidence per limit in software-testing terms: **not demonstrated in this evaluation.** The confidence model and report exist (`confidence_limitset/`, `docs/12_testing_course_mapping.md`) but the runs below produce predictions (claim, mechanism, conditions, quotes), not tested Findings. No run here has an L/A evidence tier or a confidence band, and the baselines have none by construction. No calibration was attempted.
- Full use of the new paper-side swarm: **next round.** The swarm lane exists (`paperside/tools/papertest-swarm`, `docs/12_limitset_swarm_lane.md`) and was run on the 4 development cases only (0/4 coverage), not on limitset2.

## Datasets

- **Development cases (validation, 4 cases)**: CS6223-01..04 of the 17-case Limitation Testset, one reference limit each. Used for prompt, parser and runner development, so these numbers are in-sample for everything built after seeing them.
- **limitset2 (held-out for prompt v3, 11 papers, 22 labels)**: papers not in the 17-case set (FlexPrefill, FlexPosit, QoServe, Tessera, DistServe, Sarathi-Serve, StreamingLLM, H2O, Quest, AWQ, vAttention), two labels per paper. Labels were drafted by Claude Opus 5.5 (blind to the pipeline and to the prompt plan) and then **reviewed by the dataset owner** (3 keep, 19 edit, 0 drop; edited text synced into `data/limitset2/labels.jsonl`; reasoning-chain, mechanism-insight, caveat and do-not-infer fields are still the original draft text).
- The remaining 13 cases of the 17-case set (the planned test split): the first test run (pipeline v1, B1) never completed under the model-service rate limit and is **not reported**. They were used as design input for prompt v3 (below).

## Systems

| Name | What it is |
|---|---|
| B1 | One model request per paper: full paper text, prompt "Find the limitations of this method", JSON output. No tools, no verification, no enrichment. |
| B1 x2 | Two independent B1 runs merged per paper (only identical claims merged): a control with a similar number of findings as the union systems. |
| v3c | Our mechanism generator, prompt `paper-only-mech-v3c`: (1) one call that inventories the paper's mechanisms and applies seven generic lenses (proxy vs target, objective/stopping mismatch, unit mismatch, unnecessary coupling, origin of the exploited structure, cost moved, regime change); (2) one call per mechanism that writes up to 3 candidates (headline, paper fact, premise, inference, consequence, critical link, necessary conditions, defeaters, disclosure, category); (3) in code: separate evaluation-style critiques, rank, dedupe, keep the top 20. |
| v3c + B1 | Union of v3c and B1 findings per paper (diverse generators / N-version idea: independent generators with different failure modes), identical claims merged, each finding tagged with its origin. |
| Pipeline v1 / mechanism v1 / swarm / B2 | Earlier development arms, validation cases only. |

Generator models: `x-test-2` (alias of the SoCLaaS relay; user-confirmed backend DeepSeek V4.1 flash 1017; the relay response does not report the backend) and Claude Sonnet 5.5 (`claude-sonnet-5-5`, separate relay). Judge: OpenAI `gpt-6.1-terra` for **all** tables (one judge); the judge accepts only the default temperature, so the judge is not deterministic (`temperature: default(1)`). Judge prompt `judge-v3-en-gpt61terra`, one call per (paper, label) over all findings of that paper, matching requires the same mechanism, conditions and consequence; one finding can match at most one label.

## Results

<!--TABLES-->

Columns: *Labels hit* counts reference limits judged as covered (Wilson 95% interval in brackets, n is tiny). *Papers with >=1 hit* counts papers with at least one covered label. *Findings/paper* is the mean over papers with a prediction; papers whose generation failed are counted as misses in the hit counts and listed as failed in that column. *Verified-quote rate* is the share of findings whose cited quote matches the paper text after normalization (letters and digits only, ignoring case, spacing, punctuation and hyphenation); `n/a` means the system does not check quotes at all (B1 asks for quotes but nothing verifies them). *Conditions / defeaters* count labels where the judge found the label's conditions or defeaters covered.

## What the tables do and do not show

- A covered label means the judge found a finding with the same mechanism, conditions and consequence. It does not show that the finding is correct or useful; extra findings that match no label are candidate novel limits for human triage, not errors.
- Capability difference, not a score: our systems record a category, conditions, defeaters and a disclosure status per finding; B1 produces these fields only as free text. Neither system produces an evidence level or confidence band here (see status of goal (c)).
- Cost: v3c uses about 10 times the model calls of B1 per paper (inventory call, one call per mechanism); wall time is dominated by the model service latency, not by the method.

## Threats to validity (all of them apply)

1. **Tiny samples.** 4 development cases and 11 papers / 22 labels; one repeat on limitset2. Intervals are wide and several arms are not separable.
2. **v3 prompt design used the 17-case labels** (patterns of all 17 labels). Everything on the 17-case set is in-sample for v3. limitset2 was not used for the lens design; a leakage test checks that the prompts share no 5-gram with the 17-case labels and with limitset2's labels.
3. **limitset2 labels were drafted by Claude Opus**, the same family as the Sonnet generator; style overlap may favour Sonnet arms. Human review changed 19 of 22 labels but the reviewer saw the model draft. The judge is a third family (OpenAI); generators are DeepSeek and Claude.
4. **Changes after seeing limitset2 outputs.** v3c first dropped every candidate whose quotes did not verify, which produced almost no findings on limitset2; I then kept those candidates flagged `quote_verified=false`. This was a design change made after looking at limitset2 yields, not tuning on labels (the labels were not read by any generator or prompt), but it is a deviation from "run once".
5. **Judge not deterministic and not human.** One LLM judge, default temperature, no second judge, no human spot check of judge decisions.
6. **Low quote verification.** Most v3c findings are argued from the model's reading; their quotes are paraphrases. They are hypotheses to test, not verified evidence. Verified-quote rate is in the table.
7. **Failures and retries.** Generation calls timed out under my own concurrency and the shared model service; failed paper-runs were retried once (v3c on x-test-2: 3 of 11 papers) and the successful retry is reported. Earlier failed attempts are kept in `out/` under names ending `_aborted`, `_400`, `_dropunverified`, `_allornothing`, `_noquotes`, `_badjson`, `_emptyans`.
8. **Model-service dependence.** `x-test-2` is an alias; the backend and temperature behaviour are not recorded by the service.
9. **Process.** B1 and v3c were not run on the 13 remaining cases of the 17-case set; B2 and swarm were not run on limitset2; no repeats beyond one; no confidence bands.

## Reproducibility

- Code: branch `somehow6/e2e`; freeze record `development/limitset/FREEZE.md` (partly superseded; the final state is this document and git history). Runner `python -m pipeline limitset run --dataset limitset2 --split test --generator mechanism --mech-version v3c`; baselines `python -m pipeline limitset baseline --method b1`; scorer `python -m scorer_limitset --dataset limitset2 --labels data/limitset2/labels.jsonl` with `LIMITSET_JUDGE_MODEL=gpt-6.1-terra LIMITSET_JUDGE_RELAY_PORT=8789 LIMITSET_JUDGE_CHUNK=150`; table builder `scripts/limitset/make_results.py`.
- Generator overrides for the Claude arms: `LIMITSET_GEN_MODEL=claude-sonnet-5-5 LIMITSET_GEN_RELAY_PORT=8788` (temperature and response_format omitted, B1 sends max_tokens 16000).
- Data: `data/limitset/` (17 cases, labels, hashes), `data/limitset2/` (11 cases, 22 reviewed labels, manifest). PDFs are not in git.
- Raw run outputs are under `out/` (not committed).
