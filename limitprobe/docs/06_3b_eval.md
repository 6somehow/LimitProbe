# Step 3b: implementation and evaluation

Given a code-side Limitation, answer separately: is it documented (LLM + verbatim validation), is it within the paper's scope (deterministic), and did the paper evaluate it (deterministic)?

> **All numbers below are development numbers.** The comparison draft has not been reviewed, and the planted tests use synthetic data; conclusions about generalization must wait for held-out artifacts (TASKS M3).

## Related work: no exactly equivalent work

| Work | Similarities | Differences |
|---|---|---|
| [SciCoQA](https://arxiv.org/abs/2601.12910) (ACL 2026) | Paper–code differences, including Paper Omission | Detects differences overall; does not judge scope or evaluation; even the best model finds only 46.7%, and Paper Omission is especially difficult |
| [MPDetector](https://arxiv.org/abs/2411.11410) (ISSTA 2025) | Code constraints versus document constraints; symbolic execution + LLM | Targets API documentation and constraints already stated in documentation |
| [DocPrism](https://arxiv.org/abs/2511.00215) | Document–code inconsistency | Shows that LLMs easily mistake natural gaps between documentation and implementation for inconsistencies (flagging rate 98%→14% in an ablation); 3b's decision rules address this |
| [ZeroFalse](https://arxiv.org/abs/2510.02534), [LLM4PFA](https://arxiv.org/abs/2506.10322), [IRIS](https://arxiv.org/abs/2405.17238) | Deterministic analysis + LLM review | Targets vulnerability alerts; inspired skeptic review |
| Dude (see `01_related_work_codeside.md`) | code→paper direction | Checks descriptions and relies on an LLM for judgment |

3b differs in that it checks **regions with conditions**; answers three questions separately; requires evidence to be verifiable verbatim; and actively verifies cases where something is not stated.

## Implementation

| File | Purpose |
|---|---|
| `scripts/fetch_papers.sh` | Download five PDFs to `third_party/papers/`, with URLs pinned to versions |
| `codeside/doc_index.py` | Split PDFs into sections and paragraphs (handling two columns, headers, and references), index README / docstrings / comments, BM25, verbatim validation |
| `codeside/scope_check.py` | Scope and evaluation coverage, solved with z3; returns `unknown` / `None` when translation fails, without guessing |
| `codeside/verify3b.py` | Four evidence-gathering methods, review, and Verification assembly |
| `scripts/eval_3b.py`, `tests/fixtures/eval_3b_cases.json` | Known-answer test set |
| `scripts/run_3b_dataset.sh` | Four development papers: route A → 3b |

Evidence-gathering methods (skills):

| skill | Method |
|---|---|
| `retrieve` | BM25 + LLM-generated queries in paper wording; judge candidate passages |
| `fullpaper` | One limitation against the entire paper |
| `sweep` | Read through by section, asking about all limitations once per section |
| `consensus` (default) | Run the three methods above; when one finds evidence, a skeptic tries to rebut it |

README / docstrings / comments are judged as a separate layer. Besides retrieval, **comments and docstrings near the location are forced into the candidates**, because authors often explain a limitation nearby using words unrelated to its condition.

Rules to prevent silent failures:

- A non-`not_found` result must have a quote appearing verbatim in the cited passage (at least 12 characters, no ellipsis); otherwise it is downgraded and recorded.
- The stored quote is a slice of the original text, not the model's version.
- Truncated model output, a failed call, or failure to parse JSON in all three attempts raises an error; it never becomes “not mentioned in the paper.”
- `temperature=0` is still nondeterministic. When rounds disagree, use the majority and mark `needs_review`, so the majority does not obscure real evidence.

Output: `<out>.json` is a list of Verifications; `<out>.detail.json` also contains each skill's results per round, separate conclusions for the paper and other documentation layers, validation failures, model settings, and usage.

```bash
scripts/fetch_papers.sh
python -m codeside.verify3b --limitations data/pilot_flexprefill/gold_code_limitations.json \
  --artifact data/pilot_flexprefill/artifact.json --pdf third_party/papers/flexprefill.pdf \
  --repo third_party/FlexPrefill --paper-side data/pilot_flexprefill/paper_side_stub.json \
  --model x-test-2 --repeats 3 --out out/3b/flexprefill.json
python scripts/eval_3b.py            # about 5 minutes
scripts/run_3b_dataset.sh
```

Paper versions: FlexPrefill arXiv v1, MInference arXiv v1 (contemporaneous with the pinned code version), NNSmith arXiv v2, and the official USENIX versions of InfiniGen and SparTA.

## Results

Model `x-test-2` (actual `deepseek-v4.1-flash-1017`), `temperature=0`, prompt `3b-v3`.

### Known-answer tests

| skill | Planted sentences: all labels correct | Planted sentences: found | Similar but absent: false positives | Actually stated in paper: hits |
|---|---|---|---|---|
| retrieve | 23/27 | 25/27 | 0/8 | 7/7 |
| fullpaper | 23/27 | 24/27 | 1/8 | 7/7 |
| sweep | 22/27 | 24/27 | 1/8 | **3/7** |
| consensus | 23/27 | 25/27 | 0/8 | 7/7 |

- **The four differ mostly by 1–2 cases; the sample is too small to claim that one is significantly better.** Only sweep clearly lags on real positives and is not recommended alone.
- Use consensus by default; retrieve is a reasonable alternative to save tokens, with nearly identical results in this run.
- Most errors concern detailed labels (confusing `boundary_mismatch` and `contradicted`); the judgment of whether something is stated is more reliable.
- Known blind spot: weak statements such as “we did not evaluate X” are easily missed; the skeptic risks false rejection (it once rejected a planted sentence because “this sentence looks like it was added later”).
- Planted sentences are more explicit than real papers, so these numbers are **optimistic**.

### Pilot (FlexPrefill, 13 cases, 3 rounds)

**Paper layer: all 13 are `not_found`, identical in all 3 rounds.** Independent keyword checks support this (batch, dtype, GQA, flash_attn, etc. occur 0 times in the paper).

Stability (number identical across all 3 rounds): retrieve, fullpaper, consensus 13/13; sweep 11/13; README / comment layer 11/13.

Compared with the **unreviewed draft**: result agrees on 8/13. Scope agrees on 3 of the 4 cases where it can be judged; the other 9 are `unknown`.

| Item | Draft | 3b | Assessment (pending review) |
|---|---|---|---|
| CL02 decode | found, no evidence | not_found | The docstring only says "flash decoding", not that it is dense. Both readings are plausible; the draft has no quote and cannot pass validation |
| CL05 block_size=16 | contradicted | not_found, correct in 1/3 rounds, `needs_review` | **3b is wrong**: the docstring explicitly says 16 is supported, but the kernel rejects it |
| CL06 short sequence | weaker, no evidence | not_found | The draft infers this from “at least 1024 tokens”; that sentence describes the experimental setup, and 3b is stricter |
| CL09 triton | found (README says `triton==3.0.0`) | not_found | Only a version requirement is stated, not the consequence of an older version |
| CL13 flash_attn | found (README says optional) | not_found | The draft's own reasoning also says "not the consequence" |

Review should clarify: **does a dependency version declaration count as stating the limitation?**

### Development set

| Paper | Limitation source | Result |
|---|---|---|
| MInference | Route A, 11 | All not_found |
| InfiniGen | Route A, 4 | All not_found |
| NNSmith | Route A produced 0, 1 handwritten (non-differentiable degradation) | Paper layer not_found, consistent in 3/3 rounds |
| SparTA | Route A produced 0 | Not verified |

All scopes here are `unknown` because paper-side data is not yet available. Many route A limitations are internal assertions (such as `q.dim() == 4`) that papers would not normally state, so these not_found results are not all valuable findings; the final step must filter them.

For the NNSmith case, the paper only uses Sampling as a comparison baseline and does not say that non-differentiable models fall back to it. A code comment contains a FIXME, and the model's judgment of “does this count as stated?” is unstable.

## Issues for the team

1. **F02's scope basis is wrong.** S2 of the stub says `block_size` is only 128, based on the paper's "uses a block_size = 128 in all experiments". But Appendix F.2 compares 64 and 128 and says "different block sizes can be flexibly selected according to different hardware". With the stub, CL10 is `out_of_scope`; changing S2 to {64, 128} makes it `in_scope`. Zhaopeng's step 1 needs to cover this. **Table 7 also shows similar performance for 64 and 128, which may weaken F02's accuracy concern**; Shanghao's execution must confirm it.
2. **The stub is too small to judge most scopes.** batch_size, head_dim, and dtype have no Binding, so 9/13 are `unknown`. This is an honest result, not a bug; wait for real step 1 output.
3. **Do comments count as “documented”** (question 1 in `02_schema.md`)? A FIXME turns a core candidate like the NNSmith case into `documented_elsewhere`; step 4 needs a rule.
4. **Decision table gap**: when 3b finds something in the paper body but the paper side did not list it, `03_codeside_spec.md` 4.2 has no corresponding category.

## Not done / known limitations

- `Verification.result` has only one value. Separate conclusions for the paper and other documentation layers are in `rationale` and the detail file; structuring them requires a schema change (M1).
- Numbers in tables and figures come from extracted text; text in figures is largely unavailable. Scope judgment depends on structured paper-side data.
- Conditions in `path_prefix` that cannot be translated are discarded and recorded, which may classify `out_of_scope` as in scope.
- There has been no comparison with reviewed gold because it does not yet exist (M1).
- The prompt was revised twice (reasons in `verify3b.py`), both based on pilot errors. v3 did not fix CL02 and made CL05 worse, so tuning stopped.
