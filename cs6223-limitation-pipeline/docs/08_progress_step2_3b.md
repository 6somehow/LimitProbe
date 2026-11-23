# Code-side progress: steps 2 and 3b (as of 2026-11-08)

Owner: Wanting. This document explains in simple terms what was done, how to run it, the results, and what remains.
For details see `06_two_routes.md` (step 2), `06_3b_eval.md` (3b evaluation), and `07_pipeline_b_3b.md` (end-to-end run).

## In one sentence

Given a paper PDF and its code repository, produce a list of candidate limitations present in the code but not described in the paper. Step 2 finds limitations in the code; 3b checks whether they are described in the paper and documentation. The two steps are connected and have run on all five papers.

## Flow: inputs to outputs

```
Paper PDF + code repository
   │
   ▼  Step 2: find limitations in the code
   │   Route A: scan code with rules (assert / raise / if branches)
   │   Route B: LLM fills gaps (chunked read-through + free exploration), review, merge and deduplicate; retain every A result
   │   → out/pipeline/<paper>/limitations.json
   ▼  Step 3b: answer three questions for each limitation
   │   1. Is it documented? Search paper/README/comments → LLM judgment → verify quotes verbatim → majority of 3 runs
   │   2. Is it within the paper's scope? Use z3 to compare the scope claimed by the paper
   │   3. Did the paper test it? Use z3 to compare the paper's evaluation configurations
   ▼
   3b.json (conclusions, passed to step 4), 3b.detail.json (quotes, votes in each run, whether human review is needed)
   candidates.json (summary of all five papers)
```

3b has five possible judgments: not documented (not_found), documented (found), documented more weakly (weaker), boundary mismatch (boundary_mismatch), and documented as the opposite (contradicted).

## How to run

```bash
uv venv && uv pip install -e ".[dev,llm,verify]"
scripts/fetch_dataset.sh && scripts/fetch_papers.sh       # Put code repositories and paper PDFs in third_party/ (not in git)
echo 'SOCLAAS_API_KEY=...' > .env; echo 'SOCLAAS_BASE_URL=...' >> .env   # Not in git
python -m pytest -q                                       # 111 tests
python scripts/run_pipeline.py --model x-test-2 --repeats 3 --parallel 1 --workers 3
python scripts/summarize_pipeline.py
```

Model: `x-test-2` (actually deepseek-v4.1-flash-1017), temperature 0. Do not set concurrency too high or requests will be rate-limited.

## Work completed

| Part | Description | Code |
|---|---|---|
| Step 2 route A | Static analysis, no LLM | `codeside/extractor.py` |
| Step 2 route B | Chunked read-through + free exploration + relevance review + deduplication | `sweep_extractor.py`, `agent_extractor.py`, `relevance_filter.py`, `dedup.py` |
| 3b document index | Split PDF, README and comments into passages, BM25 retrieval, verbatim quote verification | `codeside/doc_index.py` |
| 3b scope judgment | Use z3 to determine scope and test coverage; return unknown when translation is not possible | `codeside/scope_check.py` |
| 3b core | Four lookup methods (retrieval / full text / passage-by-passage scan / retrieval + adversarial review); the last is the default | `codeside/verify3b.py` |
| End-to-end | Step 2 → 3b, run on all five papers | `scripts/run_pipeline.py`, `scripts/summarize_pipeline.py` |
| Tests | Unit tests + known-answer test set | `tests/`, `scripts/eval_3b.py` |

### 3b known-answer tests

There is no ground truth for whether real papers document a limitation, so we created three types of cases (`tests/fixtures/eval_3b_cases.json`):

| Case type | Correct answer | Default method result |
|---|---|---|
| 27 limitation sentences planted in a copy of the paper | Found | 25/27 |
| 8 traps with similar wording but not documented in the paper | Not documented | 0/8 false positives |
| 7 limitations actually documented in other papers | Found | 7/7 |

These self-created cases are easier than real cases, so the results are optimistic. Indirect wording such as “we did not evaluate X” is easy to miss.

## Results (`results/`)

155 limitations across five papers:

| Paper | Source | Limitations | Not documented anywhere | Documented somewhere | Needs human review |
|---|---|---|---|---|---|
| FlexPrefill | A | 29 | 22 | 7 | 2 |
| FlexPrefill | B | 17 | 11 | 6 | 1 |
| InfiniGen | A | 4 | 4 | 0 | 0 |
| InfiniGen | B | 16 | 15 | 1 | 0 |
| MInference | A | 11 | 11 | 0 | 0 |
| MInference | B | 39 | 39 | 0 | 2 |
| NNSmith | B | 36 | 30 | 6 | 2 |
| SparTA | B | 3 | 2 | 1 | 0 |

Total: 134 not documented, 12 documented, 5 documented more weakly, 3 boundary mismatches, and 1 documented as the opposite.

Main findings:
1. **Papers rarely describe limitations in the code.** None of the 13 items in the FlexPrefill draft were documented in the paper (all three runs agreed); three were documented in the README or comments.
2. **There are 24 strongest candidates**: marked “useful” in blind review and judged “not documented” by 3b.
3. **The basis for candidate F02 is wrong**: the stub says `block_size` is only 128, but appendix F.2 of the paper also tested 64, so it is within the paper's scope. The results for 64 and 128 are close, so the impact may be small; an actual test is needed to confirm.

## Outstanding work / decisions

1. **“Not documented” does not mean “worth reporting.”** Of the items judged not documented, 35 are “true but useless” and 12 are “wrong.” 3b only answers whether they are documented.
2. **Scope judgments lack data.** Only FlexPrefill has a temporary paper-side stub; scope is unknown for the other four papers, pending paper-side data from Zhaopeng.
3. **README/comment judgments are not stable enough**; items with inconsistent results across runs are marked `needs_review`.
4. **Judgment rules remain to be decided**: does a FIXME comment count as “documented”? Does a version number without a description of the consequences count? (Suggested answer: treat both as “not documented.”)
5. **Blind-review labels** cover only some items, with one reviewer per item.

## Next steps

- Manually review the 24 items and select the strongest to hand to the test side (Shanghao) for testing.
- Rerun 3b when paper-side data arrives to complete the scope judgments.
- The three team members should agree on the rules in item 4 above.
