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

### limitset2 (11 papers, 22 human-reviewed labels, judge gpt-6.1-terra, 1 repeat)

| System | Labels hit [Wilson 95%] | Papers with >=1 hit | Findings/paper | Verified-quote rate | Labels with conditions / defeaters covered | Cost |
|---|---|---|---|---|---|---|
| B1 (x-test-2) | 3/22 [0.05, 0.33] | 3/11 [0.10, 0.57] | 12.1 (2 failed) | n/a (not checked) | 3/22 / 1/22 | 11 calls, 211k+89k tok, 130s/case |
| B1 x2 (x-test-2, two runs merged) | 5/22 [0.10, 0.43] | 4/11 [0.15, 0.65] | 21.0 (0 failed) | n/a (not checked) | 5/22 / 3/22 | n/a |
| v3c (x-test-2) | 7/22 [0.16, 0.53] | 6/11 [0.28, 0.79] | 17.2 (0 failed) | 110/189 | 6/22 / 4/22 | 134 calls, tokens n/a, 1038s/case |
| v3c + B1 (x-test-2) | 8/22 [0.20, 0.57] | 6/11 [0.28, 0.79] | 27.1 (0 failed) | 110/189 | 7/22 / 5/22 | n/a |
| B1 (Claude Sonnet 5.5) | 5/22 [0.10, 0.43] | 4/11 [0.15, 0.65] | 7.4 (1 failed) | n/a (not checked) | 5/22 / 0/22 | 11 calls, 402k+33k tok, 38s/case |
| v3c (Claude Sonnet 5.5) | 12/22 [0.35, 0.73] | 9/11 [0.52, 0.95] | 15.3 (0 failed) | 19/168 | 11/22 / 2/22 | 115 calls, tokens n/a, 274s/case |
| v3c + B1 (Claude Sonnet 5.5) | 15/22 [0.47, 0.84] | 10/11 [0.62, 0.98] | 22.0 (0 failed) | 19/168 | 13/22 / 2/22 | n/a |

### Validation (4 development cases CS6223-01..04, judge gpt-6.1-terra, 2 repeats where run)

| System | Cases found [Wilson 95%] and which | Repeats found |
|---|---|---|
| Pipeline v1 (paper-only + enrichment) | 0/4 [0.00, 0.49] [] | 0/8 |
| Pipeline + swarm | 0/4 [0.00, 0.49] [] | 0/8 |
| Mechanism v1 | 0/4 [0.00, 0.49] [] | 0/8 |
| B1 | 0/4 [0.00, 0.49] [] | 0/8 |
| B2 (opencode) | 1/4 [0.05, 0.70] ['CS6223-04'] | 1/8 |

### Reading the tables (descriptive, not a significance claim)

- **Claude Sonnet 5.5 as generator (limitset2):** v3c covers 12 of 22 labels (9 of 11 papers) against 5 of 22 (4 of 11) for B1 with the same model. The 95% intervals ([0.35, 0.73] and [0.10, 0.43]) only just overlap, so this is the clearest difference in the study, but it is one run on 11 papers with Claude-drafted labels (threat 3).
- **x-test-2 as generator (limitset2):** v3c 7 of 22 (6 of 11 papers), B1 3 of 22, B1 x2 5 of 22. The intervals overlap heavily; the ordering is suggestive only.
- **Union (v3c + B1):** adds 1 label (x-test-2: 8 of 22) and 3 labels (Sonnet: 15 of 22) over v3c alone. Against the matched control B1 x2 (21.0 findings per paper, 5 of 22) the x-test-2 union (27.1 findings per paper, 8 of 22) is higher, which is in line with the diverse-generators idea, but 3 labels on 22 is within noise.
- **Findings per paper and verification:** v3c produces 15 to 17 findings per paper with a category, conditions and defeaters; B1 produces 7 to 12. The quotes of v3c findings verify (letters and digits, normalized) for 110 of 189 findings with x-test-2 but only 19 of 168 with Claude Sonnet 5.5. A covered label therefore does not imply verified evidence: most Sonnet findings are hypotheses argued from the model's reading.
- **Failed papers are counted as misses.** B1 on x-test-2 failed on 2 papers and B1 on Sonnet on 1 paper (service errors); those labels are in the denominator as not covered, which slightly lowers B1 and B1 x2 relative to a complete run.
- **Development cases (validation table):** no system covers more than 1 of 4 cases (only B2 on CS6223-04, 1 of 8 repeats); the 4-case numbers do not separate the systems, and they were used during development.
- **Cost:** v3c makes 104 to 134 model calls for 11 papers (about 10 per paper) against 11 for B1; wall time per paper is dominated by the shared model service (x-test-2 about 1000 s per paper for v3c under load, Sonnet about 270 s). Token counts for v3c are not recorded by the relay path; B1 tokens come from the API usage field.
- **No evidence tier or confidence band is available for any row** (capability difference; see status of goal (c)). Confidence for these findings would have to come from running the test lane on each finding, which was not done.


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
