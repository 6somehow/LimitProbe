# Two technical routes for step 2 and the comparison protocol

Step 2 (finding limitations on the code side) implements both routes and compares them against the same gold set.

| Route | Method | Code | Status |
|---|---|---|---|
| **A: static analysis (no LLM)** | Python `ast` reads the code and extracts conditions and outcomes using rules | `codeside/extractor.py` | v0 available; M2a improves it |
| **B: static + LLM (redefined on 2026-11-05)** | A produces candidates; the LLM only finds what A misses: additional call edges and missed findings; **it deletes none of A's results**; code validates every LLM conclusion | `codeside/hybrid_extractor.py` | Run on the pilot and four papers |
| B-agent: free exploration | Retains all A results; the LLM explores the entire repo using read-only tools (list directories, grep, read files); code validates reported results | `codeside/agent_extractor.py` | Run 3 times each on the pilot and four papers (`agent-v2`) |
| B-sweep: chunked read-through + review | Retains all A results; code selects files by import relationships (the entry file, two levels of its imports, and one level of files importing it), splits them into chunks and asks the LLM once per chunk; code validates results, then relevance review retains only “limitations of the paper's mechanism” | `codeside/sweep_extractor.py`, `codeside/relevance_filter.py` | Run 3 times each on the pilot and four papers (`sweep-v2` + `relevance-v1`) |
| Control: pure LLM | Give the LLM the source of the entry and reachable functions (with `file:line`) in one call | `codeside/llm_extractor.py` | Control only, not a candidate approach |

## Route B design

```
Route A candidates ─> 1. Add call edges ─> rerun A ─> 2. Add missed findings ─> region table
```

| Stage | What the LLM does | How code validates it | Basis |
|---|---|---|---|
| 1. Add call edges (at most 2 rounds) | Select targets for calls A cannot resolve (`Class.method(self)`, inheritance, `obj.method()`) | Code lists candidates from repository definitions; selection is restricted to these; external library calls are not sent to the LLM | SEA (static candidates + LLM selection); Python call graph research shows that LLMs should not produce edges alone |
| 2. Add missed findings (per function) | Find behavior switches missed by A's rules | Code quotation must appear on that line, the condition must parse and all names must occur in the function; an existing region on the same line counts as a duplicate | RepoAudit (per function + validator) |

Failure handling: parsing failures or API errors are retried 3 times. If they still fail, A's results are retained and the failure is recorded in `failed_calls`; it is not treated as an empty result.

Known limitations: A's extra predictions (such as unreachable paths) are retained unchanged and handled by M2a's deterministic rules. The `alternative` outcome is not yet in the schema, so switches to another implementation are temporarily marked mechanism_variant.

Prompt versions: `hybrid-v1` ran once on the pilot and produced considerable noise in missed findings; `hybrid-v2` narrowed their scope (excluding performance tuning, defaults, compatibility branches, etc.). This change was made after seeing pilot results, so the pilot numbers are not untuned results. `hybrid-v3` removed the step that let the LLM delete A results (v2 mistakenly deleted a real limitation on the development set, and deletion cannot be validated by code); its missed-finding prompt is the same as v2. All current results use v3.

## Comparison of three B approaches (2026-11-06)

A Claude subagent blindly reviewed new results against the source code (without being told their origin), classifying them as useful / true but not useful / wrong. There was one reviewer and the sample was small, so the proportions show only rough trends.

| Approach | New results per paper per run | Consistency across 3 runs (Jaccard) | Tokens per run | Blind review: useful | Wrong |
|---|---|---|---|---|---|
| Route B (hybrid-v3) | 0–40 | — | about 20,000/entry | 4/48 (8%) | 4 |
| B-agent (agent-v2) | 0–39 | 0.07–0.33 | 350,000–840,000 | 21/54 (39%) | 11 |
| B-sweep without review (sweep-v2) | 1–130 | 0.64–0.82 | 110,000–180,000 | 4/49 (8%) | 4 |
| B-sweep + review | 1–38 | 0.55–0.76 | about 100,000 more | **10/46 (22%)**, new sample | 2 |
| B-agent + review | 0–29 | 0.11–0.33 | about 30,000 more | 20/36 (56%) on the first-round sample | — |

On the 144 results already reviewed in the first round, relevance review (`relevance-v1`) retained 25 of the 26 useful results and removed 79 of the other 118. Review and the reviewer used the same criteria, so this agreement is optimistic; the 22% comes from a second-run sample not previously evaluated and is more credible.

Conclusions:
- **Chunked read-through has the most stable coverage**, but many results concern baseline methods (StreamingLLM, vertical-slash, FlexGen top-k, dilated), data movement/scheduling details, and duplicate checks across kernels. Review removes more than half; the remainder mainly consists of the latter two categories.
- **Free exploration has the highest precision**, and can reach places outside the import graph (all 7 useful SparTA results came from it), but is unstable and expensive.
- The results overlap little and are suitable for merging: chunked read-through covers the area near the entry, and free exploration covers distant areas.
- All approaches have FlexPrefill recall of 16/16, inherited from A, so this cannot distinguish B approaches.

### Final B: chunked read-through + free exploration, merged and deduplicated after review

```
A ─┬─ sweep ─ review ─┐
   └─ agent ─ review ─┴─ merge ─ deduplicate (codeside/dedup.py, no LLM) ─ A + new B results
```

Deduplication applies only to new B results; none of A's results are deleted:
1. **Already checked upstream**: if every caller of a function (in a call graph built by name; names with more than 3 definitions are excluded) has already checked the same condition, remove the inner result.
2. **Same switch in the same file**: among new B results with the same condition and outcome, retain the first and put the other locations in notes; if the condition matches A but is in another function (such as HF and vLLM versions), retain and annotate it.

Normalize conditions before comparison (`not (a == b)` equals `a != b`).

| Paper | New results in 3 runs | Consistency across 3 runs | Present in all 3 |
|---|---|---|---|
| FlexPrefill | 17, 18, 19 | 0.64 | 12 |
| InfiniGen | 16, 12, 15 | 0.57 | 9 |
| MInference | 39, 38, 44 | 0.50 | 23 |
| NNSmith | 36, 33, 38 | 0.41 | 16 |
| SparTA | 3, 4, 15 | 0.21 | 1 |

Blind review (38 previously unreviewed results from the third merged run): **12 useful (32%)**, 20 true but not useful, 6 wrong. No “dead code” rule was added: 3 errors were `GuidedGen` in NNSmith, which is never instantiated, but “no one calls it in the repository” does not mean users cannot use it (a library's public interface); automatic deletion would remove valid results.

Result directories: `out/routes_sweep/` (unreviewed), `out/routes_filtered/` (after review, includes sweep and agent), `out/routes_merged/` (final). Symlink: InfiniGen's `flexgen/flexgen/pytorch_backend.py` points to the entry file; scope is deduplicated by real path (the first run's results remain in `out/routes_sweep_v2_symlink_dup/`).

## Why implement both

- Related work includes both approaches: SymPrompt and RepoAudit use program analysis to extract structure; SciCoQA and Dude let an LLM read code directly.
- Which is better can only be established experimentally. The comparison itself is a table in the report and directly answers “is deterministic extraction necessary?”

## Rules for a fair comparison

1. **Same input**: B sees exactly the functions reachable by A from the same entry (`collect_context` reuses A's call resolution). To test “LLM free exploration,” make a separate B-agent variant and report it in a separate row.
2. **Same output format**: both produce `Region` records, with provenance `ast` and `llm`, respectively.
3. **Same validation**: the function must be in context, the line must fall within the function, the condition must parse as a Python expression, and the outcome must be a known category. Invalid entries count as “rejected” rather than being silently discarded.
4. **Same gold and matching rules**: same file, function, and outcome, with line number tolerance ≤ 2.
5. **Fix and record LLM settings**: model ID, temperature = 0, prompt version (`SYSTEM` and `USER_TEMPLATE` in `llm_extractor.py`), context length.
6. **Run the LLM route 3 times per entry**, reporting the mean and variation.

## Comparison metrics

| Metric | Meaning | Source |
|---|---|---|
| recall | How many gold regions were found | `compare` command |
| extra | Number of extra predictions; later reviewed manually as “gold omissions” or “noise” | `compare` + manual review |
| cond_exact | Proportion of matched regions whose condition expression agrees with gold (“boundary accuracy”) | `compare` |
| rejected / hallucination rate | Proportion of LLM outputs that fail validation (nonexistent line numbers, unparseable conditions, etc.) | `.meta.json` |
| stability | Overlap of gold sets matched across 3 runs | script statistics |
| cost | Tokens and elapsed time; almost zero for route A | `.meta.json` + timing |
| downstream usability | Whether conditions can be used directly for 3b scope intersection and witness solving (parseable, names mapped via Binding) | step 3b / 4 statistics |

Report results separately by artifact, outcome type, and development set / held-out.

## Commands

```bash
# Route A
python -m codeside.cli extract --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --out out/static.json

# Route B (requires pip install -e ".[llm]" and SOCLAAS_API_KEY and SOCLAAS_BASE_URL in .env; --provider anthropic uses Anthropic instead)
python -m codeside.cli extract-hybrid --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/hybrid_run1.json

# B-agent: free exploration of the entire repo (--entry may be repeated; at most 60 steps and 800,000 tokens per run)
python -m codeside.cli extract-agent --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/agent_run1.json

# B-sweep: chunked read-through (--entry may be repeated); review can follow any B result and will not delete A results
python -m codeside.cli extract-sweep --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/sweep_run1.json
python -m codeside.cli filter --regions out/sweep_run1.json --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --model x-test-2 --out out/sweep_run1_filtered.json

# Final B: merge reviewed sweep and agent results and deduplicate
python -m codeside.cli merge out/sweep_run1_filtered.json out/agent_run1_filtered.json \
  --repo third_party/FlexPrefill --out out/b_final_run1.json

# Control: pure LLM
python -m codeside.cli extract-llm --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/llm_run1.json
#   Also writes out/llm_run1.meta.json: actual model (resolved_model), rejected entries, hallucination rate, context size

# Compare
python -m codeside.cli compare --gold data/pilot_flexprefill/gold_regions.json \
  --pred static=out/static.json --pred llm1=out/llm_run1.json
```

Current route A results on the pilot:

```
route   pred  recall  extra  cond_exact  rejected  halluc_rate
static  30    16/16   10     13/13       -         -
```

Run all entries in a batch (A once, B and the control 3 times each): `python scripts/run_routes.py --model x-test-2`; B-agent 3 times per paper: `python scripts/run_routes.py --model x-test-2 --mode agent` (results in `out/routes_agent/`), B-sweep: `--mode sweep` (results in `out/routes_sweep/`), summary: `python scripts/summarize_routes.py`, consistency: `python -m codeside.cli stability <runs...>`. For stricter matching, add `--tol 0 --one-to-one` to `compare` / `evaluate`.

## Notes

- **Gold conditions must use the original names and spelling from the code** (for example, `math.ceil` rather than `ceil`), otherwise cond_exact will be incorrect.
- **cond_exact currently only compares text** (it treats `not (a == b)` and `a != b` as equivalent); z3 could be used to check equivalence later.
- **Route A's rules were written against FlexPrefill; do not repeatedly tune route B's prompt against gold.** Otherwise the comparison is unfair. Record every prompt version.
