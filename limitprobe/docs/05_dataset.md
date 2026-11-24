# Development dataset: four papers

Development and debugging use the three papers in the proposal plus NNSmith. FlexPrefill remains a completed example pilot (`data/pilot_flexprefill/`)
and is not counted in the dataset. Metadata for each artifact is in `data/<id>/artifact.json`; `scripts/fetch_dataset.sh` clones them at fixed commits.

| ID | Paper | Conference | Pinned version | Domain | Proposal level | Execution environment |
|---|---|---|---|---|---|---|
| sparta | [SparTA](https://www.usenix.org/conference/osdi22/presentation/zheng-ningxin) | OSDI 2022 | Branch `sparta_artifact` @ 1f61a36 (2022-04-30) | Sparse compilation | L1 visible in evaluation | Requires GPU; CPU can only mock |
| minference | [MInference 1.0](https://arxiv.org/abs/2407.02490) | NeurIPS 2024 | tag `v0.1.4` @ 427b1dd (2024-07-05) | Sparse attention | L2 paper–code gap | CPU + mock; index conversion depends on a CUDA extension |
| infinigen | [InfiniGen](https://www.usenix.org/conference/osdi24/presentation/lee) | OSDI 2024 | 3754f52 (2024-07-09) | KV cache | L3 implicit assumption (MHA vs GQA) | CPU (shape and GPU memory cases) + mock |
| nnsmith | [NNSmith](https://arxiv.org/abs/2207.13066) | ASPLOS 2023 | tag `v0.0.1` @ a8307f2 (2022-09-25) | DL compiler fuzzing | — | **All CPU** |

### Why pin these versions

Paper–code alignment needs **the code at the time of publication**; otherwise, “features or fixes added after the paper” would be treated as differences:

- SparTA's main branch has evolved; the OSDI'22 artifact is on the `sparta_artifact` branch;
- MInference's HEAD (2026) has added many other methods; `v0.1.4` is the first release after the arXiv paper (2024-07);
- NNSmith's `v0.0.1` is closest to the ASPLOS artifact ([Zenodo 7222132](https://zenodo.org/records/7222132), 2022-10).

### About NNSmith

The shared conversation link's body cannot be read; only its title ("分析NNsmith搜索缺陷"; English: “Analyze NNSmith search defects”) identifies it as NNSmith.
If the conversation contains specific conclusions (such as search defects found), please organize them in `data/nnsmith/notes.md`; they can be used directly as gold candidates.

## First extractor v0 run on the four papers (rules were not tuned to them)

```bash
python -m codeside.cli extract --repo third_party/<repo> --entry "<entry>" --artifact <id> \
  --out out/<id>.json [--package-root <dir> ...]
```

| Entry | Region count | Outcome distribution |
|---|---|---|
| sparta `propagate_sparsity` | 1 | mechanism 1 |
| minference `gather_last_q_vertical_slash_topk_v4` | 9 | reject 6、fallback 2、mechanism 1 |
| minference `minference_forward.forward` | 4 | reject 1、state 1、env 1、mechanism 1 |
| infinigen `TorchDevice.mha` | 1 | mechanism 1 |
| infinigen `TorchDevice.mha_gen` | 5 | reject 4、mechanism 1 |
| nnsmith `PracticalHybridSearch.search_one` | 1 | mechanism 1 |
| nnsmith `random_model_gen` | 1 | mechanism 1 |

There is no gold yet, so only coverage is considered here; recall is not calculated.

## Issues exposed by the first run (observations requiring manual confirmation + extractor gaps)

**Observations worth following up (candidates, unverified):**

- **SparTA**: `sparta/propagation/propagate.py::propagate_sparsity` is a stub in the artifact branch (comment `# mocked`, returns the input sparsity directly); `talgebra.py` has propagation rules only for matmul. Sparsity propagation is one of the paper's core mechanisms. Confirm whether the artifact reproduces the paper's results through another path (such as precomputed results under `script/`)—a typical 3a (paper → code) candidate for Zhaopeng.
- **NNSmith**: `search_one` uses gradient search (`GradSearch`) only when the model is “differentiable”; otherwise it falls back to random sampling (`SamplingSearch`). Differentiability requires all inputs to be floating point. The code has a FIXME: "Estimate gradient (e.g., proxy gradient) for non-differentiable inputs". The paper emphasizes gradient-guided search; 3b needs to check whether it discusses non-differentiable cases.
- **MInference**: `q_len == 1` uses dense (decode); configuration options `dense` / `dilated1` / `dilated2` / `streaming` bypass vertical-slash; the Triton kernel requires head_dim ∈ {16, 32, 64, 128}; `search_pattern` has a module-level cache `SEARCH_MASK`.
- **InfiniGen**: In `mha`, skew runs only during `warmup`, and partial weight is enabled only outside warmup and when a ratio is set; `mha_gen` has 4 asserts.

**Extractor gaps (added to TASKS.md M2):**

1. **Mode switches without an early return are not recognized**: branches such as InfiniGen's `if warmup: skew(...)` change the mechanism executed but have no return, so v0 produces no region.
2. **Two-branch dispatch**: NNSmith's `if self.differentiable: return GradSearch.search_one(...) else: return SamplingSearch.search_one(...)` and MInference's `dilated` / `streaming` both “switch to another implementation”, but v0 does not report them because the callee names are not in the fallback hint list. Suggest adding an outcome to the schema (e.g. `alternative`).
3. **Calls of the form `ClassName.method(self, ...)`** are not resolved.
4. **Conditions depend on attributes set in `__init__`** (such as `self.differentiable`): analyze the constructor and carry in the conditions determining the attribute's origin.
5. **Inheritance**: find methods not overridden by a subclass in the parent class.

## Development set and generalization

All four papers are used for development and debugging, so numbers obtained on them are **development-set numbers** and cannot directly support generalization claims.
Agree before M3 to choose 1–2 unseen artifacts as held-out at the end, run them only once without tuning rules, and use them to report generalization results.
