# Code-side method specification: steps 2, 3b, and 4

## Step 2: Find code-side limitations (region table)

> Step 2 has two routes: this section describes route A (static analysis); for route B (LLM extraction) and the comparison protocol, see `docs/06_two_routes.md`. Both routes use the same output format and validation rules.

**Input**: Artifact (repository + commit), Binding (mechanism entry point, parameter mapping).
**Output**: A list of Regions, then converted to Limitation(origin=code).

### 2.1 Extraction signals (implemented in v0; see `codeside/extractor.py`)

| Signal | Outcome | Example (FlexPrefill) |
|---|---|---|
| `assert` / `raise` involving a parameter or a variable derived from it | reject | `assert batch_size == 1` |
| Early-return branch that calls a baseline (name matches the hint list) | fallback | `if q_len <= max(...): return flash_attn_func(...)` |
| `global X` + `if X is None:` | state_dependent | `causal_mask` module-level cache |
| Branch depending on dependency version, package installation, or GPU model (take the default branch) | env_dependent | `triton.__version__ < 3` |
| `mask = <comparison with parameter>` (element-wise tensor branch) | mechanism_variant | `block_sparse_mask = kl_div < tau` |
| A literal in arithmetic equals the default value of an entry parameter, and that parameter is in scope | suspicious | `// 128`, while `block_size` is configurable |
| Default path of the entry function | mechanism | After all guards pass |

Each Region records the original condition expression, the names it depends on, the **path prefix** (outer branch conditions, negated where applicable), file:line, call chain, and provenance.

### 2.2 Known v0 gaps (TASKS.md M2)

| Gap | Effect on pilot | Plan |
|---|---|---|
| No path feasibility pruning | The decode kernel is still analyzed under the prefill prefix, producing 6 noisy predictions | Bind callee parameters to caller expressions at calls; use z3 to check whether the prefix and condition conflict |
| No redundancy detection | Two asserts in `triton_bnhd_pool` are already covered by entry asserts | Mark as subsumed when the prefix implies the condition |
| No distinction for internal invariants | Assertions such as `isinstance(block_idx, list)` are not input limitations | Downgrade conditions involving only internally computed values with no data dependency on entry parameters |
| Call resolution only supports the same file and simple `from x import f` | — | Add package-level imports and method calls; leave dynamic dispatch to the LLM (`docs/prompts/dispatch_resolution.md`) |
| Configuration keys are not connected | `flex_prefill_min_budget` is passed through `modules/patch.py` | Read configuration key → parameter mappings from Binding |

### 2.3 Region → Limitation

`python -m codeside.cli to-limitations` converts reject / fallback / env / state / suspicious regions to
Limitations (effect_type: reject→reject, fallback→path_change, state→state, the rest→other).
mechanism and mechanism_variant are not limitations, but remain in the region table for scope and evaluation coverage judgments.

## Step 3b: Code → paper verification

> Implemented; see `docs/06_3b_eval.md` for details and results.

Answer three **independent** questions for each code-side Limitation:

| Question | Method | Result field |
|---|---|---|
| ① Is it documented? | Retrieve candidate passages (paper body, appendix, README, docstrings, comments) using names in the condition, corresponding paper terms from Binding, and numeric values in the condition as keywords; then ask the LLM to judge (`docs/prompts/3b_code_to_paper.md`). **The quote must appear verbatim in the source** or it is invalid | result、documented_in、matching_evidence |
| ② Is it within the scope claimed by the paper? | Use Binding to replace code names in the region condition with paper parameters and intersect with ScopeItem (interval / set operations, z3 if needed). Nonempty intersection → in_scope; intersection only with `explicit=False` ranges or explicit paper assumptions → scope_edge; empty intersection → out_of_scope; no usable Binding → unknown | scope_status |
| ③ Was it evaluated? | Whether an EvalPoint satisfies the region condition | evaluated_in_paper |

MatchResult: found (documented, with matching boundaries), boundary_mismatch, weaker (documented but weaker than code behavior, e.g. “only tested” versus “required”), not_found, contradicted (documentation contradicts the code, e.g. a docstring says 16 is supported but the kernel rejects 16).

## Step 4: Integration

### 4.1 Deduplication and merging

- A paper-side Limitation has a code match through 3a, a code-side Limitation has a paper match through 3b, and both code_evidence entries point to the same Region (or equivalent conditions) → merge into one Finding.
- Merge multiple code-side Limitations with the same condition within the same function.

### 4.2 Classification decision table

| Paper side | Code side | 3a | 3b | Category |
|---|---|---|---|---|
| Present | Present | found | found | confirmed |
| Present | Present | boundary_mismatch | Any | boundary_mismatch |
| Present | Absent | not_found | — | paper_only (performance / algorithm, or outdated paper) |
| Absent | Present | — | not_found | **undocumented** |
| Absent | Present | — | found / weaker, and only in README / docstring / comments | documented_elsewhere |
| Absent | Present | — | contradicted | undocumented (rationale notes “documentation contradicts code”) |

Findings with scope_status = out_of_scope remain in the records but are excluded from the main results.

### 4.3 Priority and confidence

- priority 1: undocumented, scope is in_scope / scope_edge, effect ∈ {reject, accuracy, state}
- priority 2: undocumented path_change; documented_elsewhere and weaker
- priority 3: all others
- confidence: Region from ast, Binding certain, quote verified verbatim → mechanical; any step relies on an LLM → llm_assisted

### 4.4 witness_hint

Select concrete values within “scope ∩ region condition” (interval endpoints and one point on each side of a boundary), using z3 or hand-written interval operations to solve,
write them to Finding.witness_hint, and pass them to Shanghao for test generation. For dimensions unconstrained by scope, use the paper's EvalPoint values.
