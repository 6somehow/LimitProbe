# Project overview (final version, 2026-11-01)

## In one sentence

Given a systems research paper and its code repository, the paper and code sides each find limitations and cross-verify them; integration produces four types of finding: "confirmed / boundary mismatch / paper only / present in code but not stated in the paper". Finally, a test is generated for each finding and executed on CPU + mock, a simulator, or GPU to confirm it.

The central finding is a limitation **present in the code, not stated in the paper, and within the scope claimed by the paper**.

## Three levels (proposal Table 1)

| Level | Example | Source |
|---|---|---|
| L1 Visible in evaluation | SparTA: poor performance at low sparsity or with unstructured sparsity | Paper evaluation |
| L2 Between paper and code | Thresholds, fallbacks, configuration restrictions, asserts | Paper and code cross-check (mainly produced by code side) |
| L3 Implicit assumptions | InfiniGen: formula derived for MHA, not directly applicable to GQA | Paper assumptions × architecture variant checklist |

## Workflow and responsibilities

| Step | Content | Output (schema records) | Owner |
|---|---|---|---|
| 1 | Paper side finds limitations: claims, scope, evaluation points, stated limitations, L1, L3 | Claim, ScopeItem, EvalPoint, Binding, Limitation(origin=paper) | Zhaopeng |
| 2 | Code side finds limitations: region table; rejection, fallback, thresholds, configuration restrictions | Region, Limitation(origin=code) | **Wanting** |
| 3a | Paper → code verification: whether paper limitations have code counterparts and whether boundaries agree | Verification(paper_to_code) | Zhaopeng |
| 3b | Code → paper verification: whether paper / README mentions code limitations and whether they are in scope | Verification(code_to_paper) | **Wanting** |
| 4 | Integration: deduplicate, assign four categories, output finding list | Finding | **Wanting** |
| 5 | Test generation: witness + oracle | TestCase | Shanghao |
| 6 | Execution confirmation: CPU + mock / simulator / GPU | TestCase.result | Shanghao |
| 7 | Evaluation | Metrics | All three |

In addition, Zhaopeng owns agent orchestration, the LLM baseline, and the paper-removal ablation; **Wanting owns the shared schema**.

## Wanting's scope

- **Inputs**: paper-side Claim / ScopeItem / EvalPoint / Binding (from Zhaopeng), code repository, full paper and README.
- **Outputs**: Region, Limitation(origin=code), Verification(code_to_paper), Finding (with witness_hint, handed to Shanghao).
- **Evaluation**: region table accuracy (comparison with gold and dynamic traces with Shanghao), classification accuracy.

## Development dataset

SparTA, MInference, InfiniGen (the three papers in the proposal), and NNSmith; see `docs/05_dataset.md`. FlexPrefill is the demonstration pilot.

## Principles

1. The LLM only handles "understanding and locating" (reading papers, supplementing dynamic dispatch, semantic matching); decisions should come from deterministic analysis or execution where possible.
2. Each record has provenance (ast / llm / manual) and verifiable evidence (verbatim quote, file:line).
3. The method is primarily static; execution is used only for confirmation.
