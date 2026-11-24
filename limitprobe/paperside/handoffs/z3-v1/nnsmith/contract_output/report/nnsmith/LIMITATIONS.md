> Offline contract-format demonstration only. No target, agent, environment probe or tests ran.

# Limitations report: NNSmith: Generating Diverse and Valid Test Cases for Deep Learning Compilers

- artifact: `nnsmith` (ASPLOS 2023), repository https://github.com/ise-uiuc/nnsmith at `a8307f2b80`
- input: `limitations_for_tests.json` (sha256 `d80931d38bc4`), 1 Findings
- generated: 2026-11-16T15:33:49+08:00 by `checklimits test` (contract `checklimits-test-report/1`)

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 1 |
| tested | 0 |
| not tested | 1 |
| not tested, by reason | `no_code_location` 1 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [nnsmith-Z3-M08-B10](#nnsmith-z3-m08-b10) | impl_deviates | other | `nnsmith/materialize/torch/symbolnet.py:293` | not tested: `no_code_location` |

## nnsmith-Z3-M08-B10

**预算耗尽则抛出失败异常**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `nnsmith/materialize/torch/symbolnet.py:293` in `nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen`
- paper/docs (paper, PDF p.7): “raise failed to find viable⟨𝑋,𝑊⟩”
- paper/docs (paper, PDF p.7, text lines 43-53): “Search process. The overall input search algorithm (Algorithm 3) proceeds as follows: Given a model𝑀 and time budget𝑇 , we first randomly initialize inputs and weights⟨𝑋,𝑊⟩ (Line 2) used by the first iteration of the search algorithm (Line 3). In each iteration, we find the first operator (in topol…”
- code snippet (`nnsmith/materialize/torch/symbolnet.py:293`): `return sat_inputs`

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence); Source locations exist, but adapter.region_from_limitation refuses origin=paper. This proposed effect also needs a custom oracle: outcome 'suspicious' has no effect check yet
