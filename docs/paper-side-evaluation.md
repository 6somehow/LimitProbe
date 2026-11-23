# Paper-side diagnosis on eight source-backed papers

A (one model request) and B (one tool-using agent, up to eight replies) receive the paper and the source packet. PaperTest Swarm maps decisions in the paper, follows an evidence chain in the pinned repository, and delegates a question about one link. It then appends candidates from other stages to the deep report. PaperTest Swarm has a ten-request cap. All three use DeepSeek V4.1 Flash through SoCLaaS. The human reference diagnoses are held back for grading.

Coverage counts papers with at least one core or partial match. The blinded grader sees the final and the reference diagnosis with the workflow identity hidden. The strict grader puts more weight on the operational consequence. Both grade the same 24 final reports.

| Split | PaperTest Swarm | A | B |
|---|---:|---:|---:|
| Development (4) | **2/4** | 1/4 | 2/4 |
| Test with source (4) | **4/4** | 3/4 | 2/4 |

![Blinded diagnosis coverage by workflow on the development and source-backed test sets](figures/paper-side-coverage.svg)

| Split | Paper | PaperTest Swarm | A | B |
|---|---|---|---|---|
| Development | NNSmith | core | miss | core |
| Development | MInference | partial | partial | partial |
| Development | InfiniGen | miss | miss | miss |
| Development | SparTA | miss | miss | miss |
| Evaluation | Prompt Cache | core | core | partial |
| Evaluation | SpinQuant | partial | core | miss |
| Evaluation | KVQuant | partial | miss | partial |
| Evaluation | DX100 | partial | partial | miss |

On the evaluation split, the blinded grader gives PaperTest Swarm partial credit for KVQuant's fixed protection budget and part of DX100's dependence across iterations. A receives a core grade on SpinQuant, where PaperTest Swarm receives partial credit.

| Split | PaperTest Swarm core / weighted | A core / weighted | B core / weighted |
|---|---:|---:|---:|
| Development (4) | 1 / 3 | 0 / 1 | 1 / 3 |
| Test with source (4) | 1 / 5 | 2 / 5 | 0 / 2 |

The weighted score gives two points for core, one for partial, and zero for miss. The discovery task ends with a proposed experiment. For NNSmith, for example, hold the graph, compiler and differential oracle fixed, vary the number of valid inputs per graph, and count graphs that expose a discrepancy. Runtime test effectiveness would require executing that comparison.

## Sensitivity to the grader

| Split | PaperTest Swarm | A | B |
|---|---:|---:|---:|
| Development (4) | 2/4 | 0/4 | 0/4 |
| Test with source (4) | 2/4 | 3/4 | 0/4 |

The strict grader puts A ahead on the four evaluation papers. The evaluation papers also informed some prompt revisions. We report one output per workflow and paper in this matrix, and chose the coverage metric after seeing preliminary results. The runs estimate semantic matches to reference hypotheses and leave runtime validation to the test stage. B's SpinQuant final was truncated and contained no candidate, so it counts as a miss in this run. The systems use different call budgets, and the comparison does not estimate the effect of delegation in isolation.

The [blinded archive](../results/matrix.md) and [strict archive](../results-holistic/matrix.md) contain the per-paper grades and final reports.

To regenerate the figure with Matplotlib installed:

```sh
python3 scripts/plot_paper_side.py --output docs/figures/paper-side-coverage.svg
```
