# Limitations report: Tessera: A Holistic Pipeline Parallelism Framework for Trillion-Parameter Heterogeneous MoE Training

- artifact: `tessera` (OSDI 2026), repository none (no public code)
- input: `paper text of osdi26-hu-weifang.pdf` (sha256 `458eff602d4a`), 10 Findings
- generated: 2026-11-18T11:32:49+08:00 by `checklimits test` (contract `checklimits-test-report/1`)

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* A Finding that was not tested may carry an **analysis** (tier A0 to A2): a reading of the paper and code evidence, with text probes run by the harness. It is a weaker kind of evidence than a test, has its own uncalibrated tiers, and never says yes or no.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 10 |
| tested | 0 |
| not tested | 10 |
| analysis only (not tests) | A1 10 |
| not tested, by reason | `no_code_location` 10 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [tessera-P001](#tessera-p001) | paper_only:missing_comparison | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P002](#tessera-p002) | paper_only:evaluation_scope | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P003](#tessera-p003) | paper_only:missing_comparison | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P004](#tessera-p004) | paper_only:assumption | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P005](#tessera-p005) | paper_only:assumption | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P006](#tessera-p006) | paper_only:evaluation_scope | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P007](#tessera-p007) | paper_only:unsupported_claim | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P008](#tessera-p008) | paper_only:evaluation_scope | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P009](#tessera-p009) | paper_only:assumption | other |  | not tested: `no_code_location`, analysis A1/supports |
| [tessera-P010](#tessera-p010) | paper_only:unsupported_claim | other |  | not tested: `no_code_location`, analysis A1/supports |

## tessera-P001

**Tessera improves throughput by 20%–33% over the production baseline across five workloads at 4,096–12,288 GPUs.**

- category `paper_only:missing_comparison`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.1–6.2): “we compare against Alibaba’s internal Megatron-LM fork, the production training stack used for the same Qwen3-family workloads before enabling Tessera.”
- paper/docs (paper, §6.1–6.2): “we benchmark against the Internal Optimized Baseline defined in §6.1”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. The headline production comparison is against Alibaba’s proprietary Megatron-LM fork, not a public baseline; the public Megatron-Core comparison is only at 256 GPUs, so the large-scale gain cannot be independently checked.
- what would settle it: Release the internal baseline configuration or run the same five production workloads against public Megatron-Core at 4,096–12,288 GPUs.

## tessera-P002

**Tessera is a holistic framework for trillion-parameter heterogeneous MoE training.**

- category `paper_only:evaluation_scope`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.1): “Our production evaluation focuses on pre-training the Qwen3 and Qwen3-Next model families.”
- paper/docs (paper, §6.1): “comprising NVIDIA Hopper GPU servers (each equipped with 8 GPUs) interconnected via a high-performance RoCE network.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. Production evidence covers only Qwen3/Qwen3-Next on Hopper/RoCE with proprietary data; non-Qwen models are tested only at 256 GPUs, so generality to other architectures, hardware, and datasets is unproven.
- what would settle it: Run production-scale training on non-Qwen MoE models and non-Hopper interconnects with public data.

## tessera-P003

**Tessera’s profile-driven co-optimization systematically outperforms manual heuristics.**

- category `paper_only:missing_comparison`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.3, §8): “we compare Tessera against Megatron-Core MoE [36] on a 256-GPU cluster.”
- paper/docs (paper, §6.3, §8): “Tessera demonstrates that a unified, profile-driven co-optimization approach systematically outperforms manual heuristics”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. The only empirical comparisons are an internal Megatron fork and Megatron-Core MoE; no head-to-head results are given for Comet, DualPipe, Zero Bubble, Alpa, or other overlap/partitioning systems discussed in related work.
- what would settle it: Benchmark Tessera against those systems on the same models and hardware.

## tessera-P004

**Tessera profiles post-overlap cost on a reference device group and reuses the plan across matching ranks.**

- category `paper_only:assumption`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §3.1.2, §6.7): “Tessera executes the synthesized schedule on a reference device group, a dedicated device set configured with the same TP/EP topology as the target rank, to measure ground-truth post-overlap cost.”
- paper/docs (paper, §3.1.2, §6.7): “Results are cached by device-mesh class and chunk specification for reuse across ranks and replicas with matching GPU type and interconnect pattern.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. Plan quality depends on the reference group matching the target’s GPU type, topology, and interconnect; profiling is offline and can take up to 3,050 s, and drift or heterogeneity would invalidate cached costs.
- what would settle it: Compare plans profiled on the reference group against plans profiled on the actual target ranks under hardware/interconnect variation.

## tessera-P005

**The overlap-aware partitioner selects a partition that minimizes bottleneck post-overlap cost.**

- category `paper_only:assumption`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §3.1.1, §3.1.3): “Tessera therefore uses the maximum selected post-overlap edge cost as a surrogate objective for partition selection.”
- paper/docs (paper, §3.1.1, §3.1.3): “Tessera restricts candidates to a bounded neighborhood around the baseline to keep overlap scheduling and profiling tractable.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. The MILP minimizes a maximum-edge surrogate, not the full pipeline critical path, and searches only a bounded neighborhood around the serial baseline; better partitions outside that space are not considered.
- what would settle it: Compare against exhaustive or full-critical-path optimization on small models and measure end-to-end iteration time.

## tessera-P006

**The Dynamic Bubble Optimizer fills routing-induced idle slots and recovers throughput.**

- category `paper_only:evaluation_scope`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.6, §5): “We evaluate DBO’s speedup, overhead, and memory cost on Qwen3-Next-M (256 GPUs, 4K sequence length).”
- paper/docs (paper, §6.6, §5): “Systematic validation of this extension under controlled jitter conditions remains future work.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. DBO is isolated only on Qwen3-Next-M at 256 GPUs and 4K sequence length; production validation is two jobs, and controlled validation under infrastructure jitter is explicitly future work.
- what would settle it: Run controlled DBO on/off ablations at production scale and under injected network jitter.

## tessera-P007

**Static planning gave a ~13% boost and DBO raised Qwen3-XL MFU to 39.0% in the production trace.**

- category `paper_only:unsupported_claim`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.2, Fig. 9): “The first step-change (April 9) marks the deployment of Tessera’s Static Planner”
- paper/docs (paper, §6.2, Fig. 9): “The second jump (April 16) marks the activation of the Dynamic Bubble Optimizer”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. The two step changes in a two-week production trace are attributed to Static Planner and DBO without a controlled A/B; other cluster, workload, or software changes could explain the jumps.
- what would settle it: Randomize or repeatedly toggle Static Planner and DBO on the same production job and compare.

## tessera-P008

**Tessera’s event-driven overlap scheduler stays within ~1% of ILP on profiled post-overlap cost.**

- category `paper_only:evaluation_scope`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.5): “For Qwen3-Next-M at sequence length 4K, the EP32 and EP8 regimes produce 690 and 536 scheduling instances.”
- paper/docs (paper, §6.5): “many hit the 300-s budget without a proven optimum.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. Scheduler evaluation uses only Qwen3-Next-M at 4K with EP8/EP32; the ILP reference often hits a 300-s budget without a proven optimum, so the comparison is against a truncated solver.
- what would settle it: Evaluate on more models/sequence lengths and compare against exact or longer-budget ILP solutions.

## tessera-P009

**Co-optimizing partitioning and overlap scheduling yields the highest end-to-end throughput.**

- category `paper_only:assumption`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.4): “we employ a mock router that uniformly distributes tokens and disable DBO, isolating static plan efficiency from dynamic runtime variance.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. The co-optimization experiment uses a mock router with uniform token distribution and disables DBO, removing the routing stochasticity that motivates the design; production behavior may differ.
- what would settle it: Repeat the partition comparison with the real router and DBO enabled.

## tessera-P010

**Tessera introduces zero numerical divergence and no observed quality regression.**

- category `paper_only:unsupported_claim`, effect `other`, step 4 level None, priority None, scope `unknown`
- paper/docs (paper, §6.2): “The two runs produce bit-identical loss trajectories.”
- paper/docs (paper, §6.2): “under deterministic mode.”

**Not tested** (`no_code_location`): no public code: the candidate is a reading of the paper text

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. paper-only: the quotes were verified against the PDF text, nothing else could be checked

- reading: **supports**. Bit-identical loss is shown only in one deterministic-mode run; no convergence curves, held-out quality metrics, or seeds are reported, and production runs are not deterministic.
- what would settle it: Release loss traces, seeds, and held-out evaluation results for Tessera and baseline runs.

