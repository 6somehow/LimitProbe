# Limitations report: SparTA: Deep-Learning Model Sparsity via Tensor-with-Sparsity-Attribute

- artifact: `sparta` (OSDI 2022), repository https://github.com/microsoft/SparTA at `1f61a363b1`
- input: `results/step4/sparta/limitations_for_tests.json` (sha256 `31a983c91d42`), 82 Findings
- generated: 2026-11-23T11:22:10+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
- environment: **ok**

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
| Findings | 82 |
| tested | 2 |
| not tested | 80 |
| verdicts | yes 2 |
| levels | L1 1, L2 1 |
| analysis only (not tests) | A0 11, A1 20, A2 49 |
| not tested, by reason | `no_code_location` 79, `outcome_unsupported` 1 |

Code side's predicted ceiling vs measured level (both uncalibrated; 2 tested Findings have both): equal 2, measured below ceiling 0, measured above ceiling 0.

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [sparta-F001](#sparta-f001) | undisclosed | path_change | `sparta/transformation/weighted_block_cover.py:77` | **yes** / L2 (uncalibrated) |
| [sparta-F002](#sparta-f002) | docs_only | reject | `sparta/transformation/weighted_block_cover.py:123` | **yes** / L1 (uncalibrated) |
| [sparta-F003](#sparta-f003) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F004](#sparta-f004) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F005](#sparta-f005) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F006](#sparta-f006) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F007](#sparta-f007) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F008](#sparta-f008) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F009](#sparta-f009) | impl_deviates | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F010](#sparta-f010) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:169-178` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F011](#sparta-f011) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:301-335` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F012](#sparta-f012) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:496-538` | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F013](#sparta-f013) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:496-538` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F014](#sparta-f014) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:571-664` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F015](#sparta-f015) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:571-664` | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F016](#sparta-f016) | impl_deviates | other | `script/figure16/a100/sparta.cu:118-140` | not tested: `no_code_location`, analysis A0/contradicts |
| [sparta-F017](#sparta-f017) | impl_deviates | other | `script/figure16/a100/sparta.cu:266-311` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F018](#sparta-f018) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F019](#sparta-f019) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F020](#sparta-f020) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F021](#sparta-f021) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F022](#sparta-f022) | impl_deviates | other | `script/init_checkpoints.sh:1-34` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F023](#sparta-f023) | impl_deviates | other | `script/run_all_2080ti.sh:1-57` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F024](#sparta-f024) | impl_deviates | other | `sparta/artifact_specialization/generate_code.py:58-82` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F025](#sparta-f025) | impl_deviates | other | `sparta/artifact_specialization/generate_code.py:58-82` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F026](#sparta-f026) | impl_deviates | other | `sparta/propagation/talgebra.py:4-17` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F027](#sparta-f027) | impl_deviates | other | `sparta/propagation/talgebra.py:4-17` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F028](#sparta-f028) | impl_deviates | other | `sparta/propagation/talgebra.py:20-34` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F029](#sparta-f029) | impl_deviates | other | `sparta/propagation/talgebra.py:50-62` | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F030](#sparta-f030) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F031](#sparta-f031) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F032](#sparta-f032) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F033](#sparta-f033) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:44-77` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F034](#sparta-f034) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:44-77` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F035](#sparta-f035) | impl_deviates | other | `sparta/transformation/optimize_model.py:29-54` | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F036](#sparta-f036) | impl_deviates | other | `sparta/transformation/transform_policy.py:56-81` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F037](#sparta-f037) | impl_deviates | other | `sparta/transformation/transform_policy.py:56-81` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F038](#sparta-f038) | impl_deviates | other | `sparta/transformation/transform_policy.py:56-81` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F039](#sparta-f039) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-156` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F040](#sparta-f040) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-156` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F041](#sparta-f041) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-156` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F042](#sparta-f042) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F043](#sparta-f043) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F044](#sparta-f044) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F045](#sparta-f045) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F046](#sparta-f046) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F047](#sparta-f047) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F048](#sparta-f048) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F049](#sparta-f049) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F050](#sparta-f050) | undisclosed | other | `sparta/common/sparsity.py:57` | not tested: `outcome_unsupported`, analysis A1/unclear |
| [sparta-F051](#sparta-f051) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/supports |
| [sparta-F052](#sparta-f052) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F053](#sparta-f053) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F054](#sparta-f054) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F055](#sparta-f055) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F056](#sparta-f056) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F057](#sparta-f057) | not_implemented | other |  | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F058](#sparta-f058) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:260-299` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F059](#sparta-f059) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:260-299` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F060](#sparta-f060) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:260-299` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F061](#sparta-f061) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:301-335` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F062](#sparta-f062) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:301-335` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F063](#sparta-f063) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F064](#sparta-f064) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F065](#sparta-f065) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F066](#sparta-f066) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F067](#sparta-f067) | not_implemented | other | `sparta/core/sparta.py:16-24` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F068](#sparta-f068) | not_implemented | other | `sparta/propagation/talgebra.py:4-17` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F069](#sparta-f069) | not_implemented | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F070](#sparta-f070) | not_implemented | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F071](#sparta-f071) | not_implemented | other | `sparta/specialization/specialize_kernel.py:44-77` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F072](#sparta-f072) | not_implemented | other | `sparta/transformation/optimize_model.py:29-54` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F073](#sparta-f073) | not_implemented | other | `sparta/transformation/optimize_model.py:29-54` | not tested: `no_code_location`, analysis A1/unclear |
| [sparta-F074](#sparta-f074) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F075](#sparta-f075) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F076](#sparta-f076) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A2/supports |
| [sparta-F077](#sparta-f077) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F078](#sparta-f078) | not_implemented | other | `sparta/transformation/transform_policy.py:172-191` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F079](#sparta-f079) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:7-24` | not tested: `no_code_location`, analysis A0/contradicts |
| [sparta-F080](#sparta-f080) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:7-24` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F081](#sparta-f081) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:7-24` | not tested: `no_code_location`, analysis A0/supports |
| [sparta-F082](#sparta-f082) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:47-102` | not tested: `no_code_location`, analysis A2/supports |

## sparta-F001

**When cover_sizes[(1, 1)] < ordered_pricing[0][0]: The choice of covering algorithm is driven by the caller's sparsity pattern: if the cheapest block price exceeds the (1,1) element price, the whole weighted-set-cover is skipped and the function returns `None, {(1,1)}` — i.e. the tensor is treated as fully element-wise (no block covering), which then flows into wbc_matmul setting w_tesa.block_si...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:77` in `sparta/transformation/weighted_block_cover.py::weighted_block_cover`
- condition: `cover_sizes[(1, 1)] < ordered_pricing[0][0]`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: When even the cheapest block price is worse than the element-wise price, the block cover is skipped and the whole weight becomes fine-grained (1,1), a variant switch driven by the sparsity pattern; ordered_pricing[0] on an empty list also raises…
- code snippet (`sparta/transformation/weighted_block_cover.py:77`): `if cover_sizes[1, 1] < ordered_pricing[0][0]:`

**Verdict `yes`**: with the trigger the branch at the location is taken and with the contrast it is not; what the claim says happens after the branch was not checked.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L2 (measured: L2).

**Level L2, uncalibrated.** supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual.

- trigger run: branch taken at sparta/transformation/weighted_block_cover.py:77
- contrast run: branch not taken at sparta/transformation/weighted_block_cover.py:77
- open doubts:
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. deeper entry (index 1); reason recorded: The step-4 call chain is not_found: propagate_sparsity is a '# mocked' stub in this pinned branch and has no path to weighted_block_cover, so the official entry cannot reach the …
- what would raise the level: D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/sparta/sparta-F001/execution_report.json`

## sparta-F002

**When len(unique_block_sizes) != 1: wbc_matmul only supports a single block size for the weight tesa. If the weighted block cover (driven by the caller's sparsity pattern / TeSA values) selects more than one block size, decompose_blocked_tesas is a no-op stub (`...`) and then a bare `raise` aborts the whole transformation. So a sparsity pattern that mixes block sizes is rejected rather than hand...**

- category `docs_only`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:123` in `sparta/transformation/weighted_block_cover.py::wbc_matmul`
- condition: `len(unique_block_sizes) != 1`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: wbc_matmul hits a bare raise whenever the weighted block cover picks more than one block size (including a block size plus the (1,1) leftover), so mixed-granularity sparsity patterns from the user's TeSA are rejected.
- paper/docs (paper, PDF p.7): “T 1 i , . . . ,T j i = self.WeightedBlockCover(Ti);”
- paper/docs (paper, PDF p.7): “Ttrans f ormed.Extend(T 1 i , . . . ,T j i );”
- code snippet (`sparta/transformation/weighted_block_cover.py:123`): `raise`

**Verdict `yes`**: with the trigger the exception is raised at the location and with the contrast it is not.
  effect on positive input, none on negative input

Code side predicted ceiling before the test: L1 (measured: L1).

**Level L1, uncalibrated.** indicative: the fatal checks passed; some important checks are residual or open.

- trigger run: RuntimeError at sparta/transformation/weighted_block_cover.py:123
- contrast run: no exception at sparta/transformation/weighted_block_cover.py:123
- open doubts:
  - D3 oracle can see the effect: *residual*. only 1 mutants (< n_min=4); killed 1
  - D13 inputs inside the paper's scope: *residual*. scope_status=unknown
  - D14 official entry point was called: *residual*. the official entry started first but the target line did not run inside it; reason recorded: The pinned propagate_sparsity is a no-op stub (it extracts ModelSparsityInfo and returns pre_sparsity) and step-4 reports call…
- what would raise the level: D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location; D14 (residual): call the official entry, or record why a deeper function is called (execution.entry_reason)
- evidence: `tests/sparta/sparta-F002/execution_report.json`

## sparta-F003

**论文要求 S 初始为全部节点；代码初始队列只含源/汇节点，其余节点由度数递减触发入队**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “S = Set(AllNodesOf(G));”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper quote supports that S should be all nodes, but the finding's code claim has no recorded code evidence. Without seeing the queue initialization, I cannot verify that only source/sink nodes are enqueued or that degree-decreasing triggers the rest. The Step 4 note asserts this, but it is not evidence from the artifact.
- what would settle it: Inspect the implementation where the propagation queue is initialized and compare its initial contents with all graph nodes.

## sparta-F004

**论文要求把全部邻居（除 N）插入 S；代码只在度数归零时入队，非全部邻居**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “S.Insert(B.Remove(N));”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The only evidence is a paper snippet, S.Insert(B.Remove(N)); no code evidence is recorded. The finding asserts a specific code behavior (enqueue only when degree reaches zero) but provides no file, function, or line to verify it. The note also says the cited code lacks the name B, so the paper-to-code mapping is not established. Thus the evidence neither supports nor contradicts the claimed implementation deviation.
- what would settle it: Inspect the implementation of the neighbor-processing loop and show whether every neighbor except N is inserted into S or only zero-degree nodes are enqueued.

## sparta-F005

**论文要求直到无 TeSA 需更新；代码固定两遍、每节点一次，不检测掩码是否仍变化**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “The propagation repeats until no TeSA requires further update.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper quote supports the stated requirement, but no code evidence is recorded. The Step 4 note asserts a fixed two-pass implementation, yet the supplied evidence contains no file, snippet, or search result showing that loop. Without code evidence, the claimed deviation cannot be verified from what is shown.
- what would settle it: Inspect the TeSA propagation loop in the implementation to see whether it repeats until masks stop changing or performs exactly two fixed passes.

## sparta-F006

**论文要求随算子类型 AND 属性类型变化；代码仅覆盖剪枝一种属性种类（量化比特未实现，见 M02-B07-R02），属性维度分派缺失**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5, text lines 46-48): “Intra-operator propagation. The propagation behavior of PropOneNode varies across different type of operators and at- tributes. In Figure 4(b), the pruned element [0,0] in tensor W3”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The finding cites only the paper text; no code evidence is recorded. Without seeing the propagation implementation, I cannot verify whether operator/attribute-type dispatch is missing or whether only pruning attributes are handled. The Step 4 note asserts a gap but does not provide inspectable code.
- what would settle it: Inspect the propagation implementation for dispatch on operator and attribute type and verify whether quantization-bit attributes are handled.

## sparta-F007

**论文要求重复运行多次（经验 256 个随机张量）；代码单次前向，以批内方差近似重复采样，重复次数由 confidence/batch 维决定而非 256 次独立运行**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “By repeating this process enough times (see §5.2)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The only evidence shown is a paper sentence saying the process is repeated enough times, with no code evidence recorded. It does not establish the claimed 256 independent randomized runs, nor that the code uses a single forward pass with batch/confidence variance. Without the cited code or §5.2 details, the deviation cannot be judged.
- what would settle it: Inspect the cited code path and §5.2 to count independent randomized forward passes versus batch/confidence-based approximation.

## sparta-F008

**论文返回 Iupdated∪Oupdated 的输入与输出 TeSA 更新集；代码只返回每层 weight_mask，缺输入/输出更新集**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.6): “return Iupdated , Oupdated ;”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper quote supports that the method returns Iupdated and Oupdated, but the finding provides no code evidence: it explicitly says no code evidence was recorded. The Step 4 note asserts infer_modules_masks returns only weight masks, but without a file path or snippet this cannot be verified. Thus the claimed paper-code deviation is not established from the shown evidence.
- what would settle it: Inspect the infer_modules_masks implementation and its callers to verify whether Iupdated/Oupdated are computed and returned or only per-layer weight masks are returned.

## sparta-F009

**artifact 路径无通用纳入机制。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.8): “SparTA’s specialization framework is general to incorporate any sparsity-aware techniques, including the off-the-shelf sparse kernel and even its dense version.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper claims the framework is general enough to incorporate arbitrary sparsity-aware techniques, but the finding asserts the artifact lacks such a generic mechanism. No code evidence is recorded, so the artifact's actual specialization path cannot be verified from the shown evidence. The Step 4 note is an assertion, not inspectable code. Thus the evidence is insufficient to support or contradict the finding.
- what would settle it: Inspect the specialization dispatch/registration code to see whether arbitrary sparsity-aware kernels can be registered, or whether only built-in SparTA kernels are hardcoded.

## sparta-F010

**论文要求用真实数据集推理得到的算子输入输出张量；逐模块传播路径用随机张量代替真实激活**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:169-178`
- paper/docs (paper, PDF p.6, text lines 84-87): “operator’s input and output tensors, we ﬁrst perform inference on the corresponding DNN model using train/test dataset, and collect the resulting input and output tensors of that operator to construct calibration data (line 20). Next, we gradually”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says calibration data should come from real dataset inference. The code does call calibration with train_dataloader, but the per-module propagation function train_bit_propagate builds its training and validation inputs with torch.rand(dummy_input_shape), not real activations. Thus the cited propagation path uses random tensors, matching the finding.
- cited code found at the pinned commit: yes (4 location(s))
- probe `torch\.rand\(dummy_input_shape\)` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (8 hit(s)). Shows random tensors are generated for per-module propagation.
- probe `data_train_list\.append\(dummy_per_image\)` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (3 hit(s)). Confirms random dummy images populate propagation training data.
- probe `calibration\(model, device, train_dataloader\)` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (1 hit(s)). Shows real loader used only for calibration, not propagation.
- probe `def train_bit_propagate` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (1 hit(s)). Locates the propagation function where random data is used.
- what would settle it: Instrument train_bit_propagate to log whether its inputs come from real dataset activations or torch.rand, or replace random tensors with collected real tensors and compare results.

## sparta-F011

**论文要求对算子所有张量（输入/权重/输出）逐一评估；代码只对 weight 张量做位宽搜索，input/output 未评估**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:301-335`
- paper/docs (paper, PDF p.6): “The process repeats for other tensors in the operator, until all tensors are evaluated.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code fixes input_bit and output_bit from bit_setting, then loops only over weight bits (`for i in range(...)` and `for weight_bits in range(...)`). The QAT config includes input/weight/output, but only weight_bits is varied; input_bits and output_bits remain fixed. This matches the claim that input/output tensors are not searched/evaluated individually.
- cited code found at the pinned commit: yes (2 location(s))
- probe `for weight_bits in range` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (2 hit(s)). Shows the bit search loop varies weight bits.
- probe `for (input_bits|output_bits) in range` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No analogous input/output bit search loop exists.
- probe `train_bit_propagate\(original_module, choose_module, choose_name, all_shapes, input_bit, i, output_bit` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (1 hit(s)). Shows only the middle weight argument is varied.
- what would settle it: Inspect or run the search and verify whether input_bits/output_bits are ever varied independently; the code shows they are fixed.

## sparta-F012

**论文要求精度下降小于预定义阈值（1%）才接受；代码用 best_acc<original_acc 即任何下降都拒绝，无 1% 阈值**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:496-538`
- paper/docs (paper, PDF p.6, text lines 94-97): “operator after lowering the precision. If the drop of model ac- curacy is smaller than a predeﬁned threshold (e.g., 1% in our experiment), the new quantization attribute of that operator is accepted (line 22). The process repeats for other tensors in”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper states a 1% accuracy-drop acceptance threshold, but the shown code only initializes best_acc and runs finetuning; it does not show the acceptance comparison or any original_acc/threshold. Thus the alleged best_acc<original_acc rule is not evidenced in the cited lines.
- cited code found at the pinned commit: yes (2 location(s))
- probe `0\.01|1\s*%|threshold` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No explicit 1% threshold constant in this file; control confirms search location.
- probe `original_acc|best_acc\s*<` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (2 hit(s)). Presence would show the alleged acceptance comparison; absence leaves claim unverified.
- probe `best_acc\s*=` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (14 hit(s)). Confirms best_acc variable exists, but not how it is compared.
- what would settle it: Inspect the full finetuning/acceptance block after line 650 to see whether acceptance uses a 1% drop threshold or a best_acc<original_acc comparison.

## sparta-F013

**论文要求拓扑序并缓存激活；代码按模块注册顺序遍历且无激活缓存**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:496-538`
- paper/docs (paper, PDF p.6): “SparTA works through all the operators in a DNN model in a topological order and caches the activations computed in earlier quantization propagations.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code iterates modules via named_modules() in registration order (lines 514-521) and quantizes each Conv2d independently using random dummy inputs (lines 599-607). It shows no topological sort and no activation cache/reuse across quantization propagations, so the paper's stated propagation precondition is not implemented in this path.
- cited code found at the pinned commit: yes (2 location(s))
- probe `named_modules\(\)` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (12 hit(s)). Confirms module traversal uses PyTorch registration order, not explicit topological order.
- probe `topological|topo_sort|topological_sort` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). Shows no topological-sort symbol in the cited file.
- probe `activation.*cache|cache.*activation|activation_cache|act_cache` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). Shows no activation-cache mechanism in the cited file.
- what would settle it: Instrument the cited function to log module visitation order and whether activations are reused across quantized convolutions.

## sparta-F014

**论文要求同时更新 S 与 Supdated；代码只更新全局位设置，无 Supdated 累积**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:571-664`
- condition: `weight_bits in range(weight_upbound_bits-1, downbound_bit-1, -1)`
- paper/docs (paper, PDF p.6, text lines 16-18): “23 if Tupdated != T then 24 S.Update(Tupdated ); 25 Supdated .Update(Tupdated );”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code updates the module's layer_quant_setting.weight.bits and a temporary bit-setting copy, but contains no Supdated accumulation corresponding to the paper's Supdated.Update(Tupdated). This matches the claimed deviation.
- cited code found at the pinned commit: yes (1 location(s))
- probe `Supdated` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No Supdated accumulation appears in the implementation file.
- probe `S\.Update` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No paper-style S.Update call is present.
- what would settle it: Search the full implementation for any Supdated or S.Update accumulation and compare it with the paper's update step.

## sparta-F015

**论文以 Tupdated==T 跳过；代码以精度下降 break，语义不同**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:571-664`
- paper/docs (paper, PDF p.6): “if Tupdated != T then”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The excerpt shows a descending weight-bit loop with finetuning and a best_acc variable, but it does not show the claimed break on accuracy degradation, nor the paper's Tupdated condition. The cited range extends beyond the shown lines, so the key semantic difference is not established by the evidence provided.
- cited code found at the pinned commit: yes (1 location(s))
- probe `\bbreak\b` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (7 hit(s)). Confirms whether the cited loop contains any break statement.
- probe `Tupdated` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). Shows the paper's Tupdated check is absent from the code.
- probe `if\s+[^\n]*(acc|loss)[^\n]*:[\s\S]{0,80}?break` in `script/figure14/search_finetune_fit_qat.py` expected present: **refuted** (0 hit(s)). Finds an accuracy/loss-conditioned break in the loop.
- what would settle it: Inspect lines 648-664 for a break conditioned on accuracy/loss and confirm no Tupdated check; if so it supports, if no such break or Tupdated is present it contradicts.

## sparta-F016

**论文报告第二 sub-Matmul 的具体残余稀疏度；实验路径无该测量/输出，且底层分派规则与数值趋势不符。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure16/a100/sparta.cu:118-140`
- paper/docs (paper, PDF p.13): “The other sub-Matmul has 12.5%, 8%, 4.5%, 2.0%, 0.5% sparsity ratio respectively.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The transform puts the first nonzero of each 2-element group in A1 and the rest in A2. For input density d, A2 density is d^2/2, giving 12.5%, 8%, 4.5%, 2%, 0.5% for d=0.5..0.1—exactly the paper's numbers. The run/draw scripts only log runtime, but the residual values are analytically derivable, so the claimed mismatch is not supported.
- cited code found at the pinned commit: yes (3 location(s))
- probe `A2\[j\]\s*=\s*A\[j\]` in `script/figure16/a100/sparta.cu` expected present: **confirmed** (1 hit(s)). A2 receives extra nonzeros per pair, matching paper's residual-density trend.
- probe `printf|std::cout|residual|sparsity` in `script/figure16/a100/sparta.cu` expected absent: **refuted** (19 hit(s)). No residual-sparsity print in split code; control confirms file searched.
- probe `Time=` in `script/figure16/a100/draw.py` expected present: **confirmed** (1 hit(s)). Plot script parses only runtime, not residual sparsity.
- probe `residual` in `script/figure16/a100/run.sh` expected absent: **confirmed** (0 hit(s)). Run script loops input sparsity but never measures residual sparsity.
- what would settle it: Compute A2 nonzero density from the transform for input sparsities 0.5–0.9 and compare with 12.5/8/4.5/2/0.5%, while checking whether the paper defines these as density.

## sparta-F017

**实验路径的第二部分内核依赖为 Sputnik，而非 SparTA 专用稀疏内核。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure16/a100/sparta.cu:266-311`
- paper/docs (paper, PDF p.13, text lines 83-85): “tains the elements not included in the ﬁrst one. The ﬁrst one uses Sparse Tensor Cores, while the other uses our specialized sparse kernel. To evaluate the transformation, we randomly”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says the second tensor uses a specialized sparse kernel. The code instead calls CudaSpmm in the second path, and run.sh links -lspmm from the Sputnik build while including Sputnik headers. The Dockerfile also installs Sputnik. This supports that the second kernel dependency is Sputnik, not a SparTA-specific sparse kernel.
- cited code found at the pinned commit: yes (3 location(s))
- probe `-lspmm` in `script/figure16/a100/run.sh` expected present: **confirmed** (2 hit(s)). Links the Sputnik spmm library into the experiment binary.
- probe `CudaSpmm\(` in `script/figure16/a100/sparta.cu` expected present: **confirmed** (1 hit(s)). Second-path kernel call is CudaSpmm, not a SparTA kernel.
- probe `git clone[^\n]*sputnik` in `image/Dockerfile.a100` expected present: **confirmed** (1 hit(s)). Environment installs Sputnik as a dependency.
- what would settle it: Inspect the linked CudaSpmm implementation or build link map to verify it resolves to Sputnik's libspmm rather than a SparTA kernel.

## sparta-F018

**artifact 脚本无反馈驱动的稀疏属性更新步骤。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4): “Given the feedback, model designers may further update the sparsity attributes in some tensors”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited run.sh only calls iterative_SA.py with fixed --sparsity_per_iter and no feedback input; the argparse block exposes no feedback or update-sparsity option. This matches the claim that the artifact path lacks a feedback-driven sparsity-attribute update step, though the shown excerpt is limited.
- cited code found at the pinned commit: yes (2 location(s))
- probe `feedback` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No feedback term in the driver script; control confirms the file was searched.
- probe `feedback` in `script/figure19/iterative_SA.py` expected absent: **confirmed** (0 hit(s)). No feedback term in the script; control confirms the relevant file was searched.
- probe `update.*sparsity|sparsity.*update` in `script/figure19/iterative_SA.py` expected absent: **confirmed** (0 hit(s)). No sparsity-attribute update logic named in the script; control confirms search location.
- what would settle it: Inspect the full iterative_SA.py execution path for any use of feedback to modify sparsity attributes; a text search and call trace would settle it.

## sparta-F019

**artifact 无编译-测量迭代回路。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4): “repeat this process iteratively to ﬁnd the best tradeoff”
- paper/docs (paper, PDF p.4): “Thus SparTA enables a feedback loop, facilitating the innovation in model sparsity.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited run.sh only runs iterative_SA.py twice with --speed-up False/True and then draw.py; it contains no compile/measure/feedback loop or iterative search over tradeoffs. This matches the finding that the artifact lacks the paper's iterative compile-measure loop. Because iterative_SA.py is not shown, the evidence is limited to the cited entry point.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)spartamodel|compile|measure|feedback|tradeoff` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No compile/measure/feedback invocation in cited script; control confirms file searched.
- probe `(?i)\b(for|while)\b|\bdo\b|\bdone\b` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No shell iteration loop; only two fixed runs and draw.
- what would settle it: Inspect iterative_SA.py and model code for a compile-measure loop, or run the artifact and observe whether repeated compile/measure iterations occur.

## sparta-F020

**加速来自 NNI ModelSpeedup 而非 SparTA 稀疏 kernel。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14): “With SparTA, model ﬁne-tuning can be accelerated.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. run.sh compares --speed-up False/True, and draw.py labels the True arm 'With SparTA'. The Step 4 note states the True arm always uses NNI ModelSpeedup rather than SparTA sparse kernels. Thus the plotted 'SparTA' acceleration is actually NNI ModelSpeedup, matching the finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `ModelSpeedup` in `script/figure19/iterative_SA.py` expected present: **not_run** (0 hit(s)). Speed-up branch invokes NNI ModelSpeedup.
- probe `SparTA.*(kernel|sparse)|sparse.*kernel` in `script/figure19/iterative_SA.py` expected absent: **not_run** (0 hit(s)). No SparTA sparse-kernel call in speed-up path.
- probe `--speed-up True` in `script/figure19/run.sh` expected present: **confirmed** (1 hit(s)). Script runs the speed-up arm.
- probe `With SparTA` in `script/figure19/draw.py` expected present: **confirmed** (1 hit(s)). Plot labels speed-up arm as SparTA.
- what would settle it: Inspect the --speed-up True branch in iterative_SA.py and profile both arms to see whether NNI ModelSpeedup or SparTA sparse kernels supplies the speedup.

## sparta-F021

**artifact 无目标稀疏度终止条件。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14, text lines 71-74): “sity pattern iteratively [58, 86]. In each iteration, the algo- rithm “sparsiﬁes” a proportion of the model (e.g., 30%) and ﬁne-tunes it. It repeats the iteration until achieving the tar- geted sparsity (e.g., 90%). In this process, model ﬁne-tuning”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper describes iterative pruning that repeats until a targeted sparsity is reached. The cited artifact code exposes a fixed --n_iter defaulting to 3 and run.sh does not override it; the shown arguments include no target-sparsity stopping criterion. This supports the claim that the artifact uses fixed iterations rather than target-sparsity termination.
- cited code found at the pinned commit: yes (2 location(s))
- probe `range\(args\.n_iter\)` in `script/figure19/iterative_SA.py` expected present: **confirmed** (2 hit(s)). Shows the pruning loop is driven by fixed n_iter, not target sparsity.
- probe `while.*sparsity|sparsity.*while|break.*sparsity|sparsity.*break` in `script/figure19/iterative_SA.py` expected absent: **confirmed** (0 hit(s)). Miss plus control hit indicates no target-sparsity termination condition.
- probe `sparsity_per_iter` in `script/figure19/iterative_SA.py` expected present: **confirmed** (4 hit(s)). Confirms a sparsity argument exists, but not necessarily as a stopping condition.
- what would settle it: Inspect the iterative_SA.py pruning loop to verify it only iterates range(args.n_iter) and never breaks on a target sparsity.

## sparta-F022

**论文要求传播为 Rammer 内专用编译 pass；实验路径在编译前以 Python 脚本离线传播，编译器 pass 列表无传播 pass。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/init_checkpoints.sh:1-34`
- paper/docs (paper, PDF p.9): “We implemented sparsity attribute propagation as a dedicated compilation pass over Rammer.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The script invokes bert/mobilenet propagate Python scripts before ONNX export, matching offline propagation rather than a Rammer compilation pass. It does not show the compiler pass list, so the 'no pass registered' detail remains unverified, but the observed experimental path supports the deviation.
- cited code found at the pinned commit: yes (1 location(s))
- probe `python .*propagate` in `script/init_checkpoints.sh` expected present: **confirmed** (4 hit(s)). Offline propagation scripts are explicitly run before ONNX export.
- probe `onnx` in `script/init_checkpoints.sh` expected present: **confirmed** (8 hit(s)). ONNX export steps follow the propagation scripts in the same workflow.
- probe `rammer|compiler|pass` in `script/init_checkpoints.sh` expected absent: **confirmed** (0 hit(s)). This script invokes no compiler pass; only Python scripts.
- what would settle it: Inspect Rammer's compiler pass registration/list at the pinned commit and trace whether propagation occurs during compilation or only in the Python scripts.

## sparta-F023

**论文要求复现 Figure 8-11、14-18、20；实际覆盖 8-11、13-15、17、19 与 table3，缺 figure18、figure20，且 2080Ti 路径无 figure16。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/run_all_2080ti.sh:1-57`
- paper/docs (paper, PDF p.21, text lines 27-30): “In this artifact, we will reproduce the Figure 8-11, 14-18, 20 on NVIDIA 2080Ti and A100. Each ﬁgure has a shell script to reproduce and visualize the experimental results automati- cally. In addition, there are many baselines compared in our”
- paper/docs (paper, PDF p.21, text lines 50-56): “Environment setup To set up the environment, please ﬁrst clone the code and build the docker image based the Docker- ﬁle we provided. Second, please start a docker instance and install the SparTA in the python environment. Finally, please run the init_env.sh to initialize the environment variables …”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper claims Figures 8-11, 14-18, and 20 are reproduced on 2080Ti and A100. The pinned run_all_2080ti.sh instead runs figures 8-11, 13-15, 17, 19, and table3, with no figure16, 18, or 20. run_all_a100.sh only runs figure16/a100. This directly supports the stated implementation deviation.
- cited code found at the pinned commit: yes (6 location(s))
- probe `figure18` in `script/run_all_2080ti.sh` expected absent: **confirmed** (0 hit(s)). No figure18 in 2080Ti runner; control confirms file searched
- probe `figure20` in `script/run_all_2080ti.sh` expected absent: **confirmed** (0 hit(s)). No figure20 in 2080Ti runner; control confirms file searched
- probe `figure16` in `script/run_all_2080ti.sh` expected absent: **confirmed** (0 hit(s)). No figure16 in 2080Ti runner; control confirms file searched
- probe `figure13` in `script/run_all_2080ti.sh` expected present: **confirmed** (2 hit(s)). Figure13 is run despite not being in paper's claimed list
- what would settle it: Inspect the pinned scripts to verify which figure directories are invoked on each hardware path.

## sparta-F024

**论文要求 2 字节位域属性；artifact 路径以文本配置+按位宽分支替代，未实现 7/4/5 位布局**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/artifact_specialization/generate_code.py:58-82`
- condition: `bit == 32 or bit == 8`
- paper/docs (paper, PDF p.9): “Each TeSA element has a two-byte attribute: 7 bits record the bit width of the element, 4 bits specify the element’s data format”
- paper/docs (paper, PDF p.9, text lines 7-9): “TeSA element has a two-byte attribute: 7 bits record the bit width of the element, 4 bits specify the element’s data format (e.g., unsigned int, ﬂoat32, bﬂoat16), and the rest 5 bits are”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown artifact code branches only on bit==32 and bit==8, writes binary row/col/val files, and returns a text config dict. It contains no packing of a two-byte TeSA attribute with 7-bit width, 4-bit format, and 5 remaining bits. Thus the evidence supports the claimed deviation, though only for this code path.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(<<|>>|bit_width|data_format|bitfield)` in `sparta/artifact_specialization/generate_code.py` expected absent: **confirmed** (0 hit(s)). No bitfield packing or width/format fields in this file.
- what would settle it: Inspect the full artifact for any TeSA attribute serialization, or run a test checking the emitted two-byte header fields.

## sparta-F025

**论文要求 4/8 表示 uint4/uint8；artifact 仅实现 int8 路径，无符号量化未体现**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/artifact_specialization/generate_code.py:58-82`
- condition: `bit == 4 or bit == 8`
- paper/docs (paper, PDF p.4, text lines 114-116): “Figure 3: An example of TeSA. Sparsity Attribute denotes the sparsity pattern, including quantization (4 meansuint4, 8 means uint8) and pruning (0 means the element is pruned).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper states that sparsity attribute 4 means uint4 and 8 means uint8. The shown generator only branches on bit==32 and bit==8, and the 8-bit path calls convert_to_block_csr_int8. There is no 4-bit branch or uint4/uint8 handling in the evidence, so the artifact appears to implement only an int8 path, not unsigned quantization as described.
- cited code found at the pinned commit: yes (1 location(s))
- probe `uint4|uint8` in `sparta/artifact_specialization/generate_code.py` expected absent: **confirmed** (0 hit(s)). No unsigned quantization types in generator; control confirms file searched.
- probe `bit\s*==\s*4` in `sparta/artifact_specialization/generate_code.py` expected absent: **confirmed** (0 hit(s)). No 4-bit branch; control shows bit dispatch exists.
- what would settle it: Inspect the full generator and conversion utilities for any uint4/uint8 or bit==4 path, or run quantization with 4/8 and check emitted types.

## sparta-F026

**论文要求 ×、÷、x^y 三类算子均满足任一 φ 即 φ；代码只提供 × 的 and 规则，÷ 与 x^y 无任何规则**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:4-17`
- paper/docs (paper, PDF p.5): “((x = φ)∨ (y = φ))→ (z = φ)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown Algebra class defines only __add__ (OR) and __mul__ (AND), and algebra_matmul uses only these. No division or exponentiation rule is present in the cited code, while the finding says the paper requires rules for ×, ÷, and x^y. Thus the evidence supports the claimed implementation gap.
- cited code found at the pinned commit: yes (2 location(s))
- probe `__truediv__|__div__|__pow__|def\s+\w*(div|pow)\w*` in `sparta/propagation/talgebra.py` expected absent: **confirmed** (0 hit(s)). Miss shows no division/power rule; control confirms file searched.
- what would settle it: Inspect the full talgebra.py and run propagation with division and exponentiation operators to verify no corresponding rule exists.

## sparta-F027

**论文要求 ×/÷/x^y 三者均满足 α∧α→α；代码仅实现 ×**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:4-17`
- paper/docs (paper, PDF p.5): “((x = α)∧ (y = α))→ (z = α)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited Algebra class defines __mul__ (AND) but no division or exponentiation operators. The paper's α∧α→α condition is shown, and the finding says it must hold for ×, ÷, and x^y. Since only multiplication is implemented among those three, the code deviates for ÷ and x^y. The extra __add__ is irrelevant to the claimed operators.
- cited code found at the pinned commit: yes (1 location(s))
- probe `__truediv__|__div__` in `sparta/propagation/talgebra.py` expected absent: **confirmed** (0 hit(s)). No division operator is defined; control confirms the file was searched.
- probe `__pow__` in `sparta/propagation/talgebra.py` expected absent: **confirmed** (0 hit(s)). No exponentiation operator is defined; control confirms the file was searched.
- what would settle it: Inspect the full Algebra class or execute division/exponentiation on Algebra values to verify those operators are missing.

## sparta-F028

**论文要求对逐元素可表达算子按计算流计算输出 TeSA；代码只对 matmul 实现，一元与 ÷/x^y 算子无对应计算流**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:20-34`
- paper/docs (paper, PDF p.5): “(x = φ)→ (y = φ)”
- paper/docs (paper, PDF p.5): “(x = α)→ (y = α)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says TeSA output is computed via TeSA algebra following the operator's computation flow, implying element-wise operators need corresponding flows. The shown code defines only Algebra add/mul and algebra_matmul, and the only test exercises matmul. No unary, division, or power propagation appears in the cited file, so the claimed implementation gap is supported.
- cited code found at the pinned commit: yes (4 location(s))
- probe `(?i)def\s+algebra_(unary|div|divide|pow|exp|log|relu|sigmoid)` in `sparta/propagation/talgebra.py` expected absent: **confirmed** (0 hit(s)). No element-wise algebra function beyond matmul is defined.
- probe `(?i)(torch\.(div|pow)|\bunary\b|\bdivision\b|\bpower\b)` in `sparta/propagation/talgebra.py` expected absent: **confirmed** (0 hit(s)). No division, power, or unary propagation code is present.
- what would settle it: Search the full talgebra.py and propagation modules for any non-matmul operator flow; if none exists, the finding is confirmed.

## sparta-F029

**论文要求三条导数公式（含 gB=gY）；代码仅实现两条，偏置项缺失。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:50-62`
- paper/docs (paper, PDF p.6): “Similarly, the TeSA of B and X can be inferred from Y using gB = gY and gX = AT× gY, respectively.”
- paper/docs (paper, PDF p.6): “It is obvious from gB = gY that B has the same TeSA as Y .”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper lists gA, gB, gX, and the shown propagate_matmul computes only gA and gX. However, the snippet is a pure matmul propagation with no bias input; bias could be handled by a separate add/bias propagation not shown. The evidence does not establish a code-wide omission.
- cited code found at the pinned commit: yes (2 location(s))
- probe `\b(bias|gB|propagate_add)\b` in `sparta/propagation/talgebra.py` expected present: **refuted** (0 hit(s)). Bias/add propagation exists, so gB may be handled elsewhere.
- probe `prop_tesa_in2\s*=\s*algebra_matmul\(transpose\(tesa_in1\),\s*tesa_out\)` in `sparta/propagation/talgebra.py` expected present: **confirmed** (1 hit(s)). Confirms matmul backward computes gX but not gB.
- what would settle it: Inspect the full propagation module and call graph for a bias/add operator that computes gB=gY; if none exists, the finding is confirmed.

## sparta-F030

**论文允许输入分解；artifact 路径只处理单输入 TeSA**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- condition: `len(in_tesa) > 1 or len(out_t_tesa) > 1`
- paper/docs (paper, PDF p.7): “Ti = P.TransformTeSA(Ii);”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The artifact explicitly disables input decomposition: transform_matmul calls bit_align(in_tesa, decompose=False) and comments that only weight is decomposed. specialize_matmul also asserts len(in_tesa) == 1. This matches the finding that the artifact path handles only a single input TeSA, while the paper's TransformTeSA(Ii) does not show that restriction.
- cited code found at the pinned commit: yes (2 location(s))
- probe `bit_align\(in_tesa, decompose=False\)` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows input decomposition explicitly disabled in transform path.
- probe `len\(in_tesa\) == 1` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Shows specialization asserts exactly one input TeSA.
- what would settle it: Run transform_matmul with a decomposed multi-TeSA input and check whether it decomposes or rejects/asserts.

## sparta-F031

**输出不分解**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- condition: `len(weight_tesa) > 1`
- paper/docs (paper, PDF p.7): “To = P.TransformTeSA(O);”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code asserts len(out_t_tesa) == 1, so the output TESA is constrained to a single element rather than decomposed. It also returns only latency, kernels, and aggr_type, with no TransformTeSA call. Although marked mocked, the visible implementation supports the claimed deviation.
- cited code found at the pinned commit: yes (1 location(s))
- probe `len\(out_t_tesa\)\s*==\s*1` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Shows output TESA is constrained to one element, not decomposed.
- probe `TransformTeSA` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). Shows no output transform call appears in this file.
- probe `return latency, kernels, aggr_type` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Shows function returns no transformed output tensor.
- what would settle it: Inspect the full specialization pipeline to verify whether TransformTeSA is applied to O and whether out_t_tesa can ever have length greater than one.

## sparta-F032

**论文要求 m+1 维笛卡尔积；代码仅权重维枚举，实际 1 维**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- condition: `len(in_tesa) == 1 and len(out_t_tesa) == 1 and len(weight_tesa) >= 1`
- paper/docs (paper, PDF p.7): “foreach⟨t1, . . . ,tm,to⟩∈ T1×···× Tm× To do”
- paper/docs (paper, PDF p.7, text lines 25-29): “transformed to one or multiple TeSAs using TransformTeSA. Correspondingly, the operator is transformed to|To| ∏m i=1|Ti| sub-operators, which are the Cartesian product of those de- composed TeSAs. The sub-operator usually has the same”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper specifies a Cartesian product over m input TeSA dimensions plus output, yielding |To|∏|Ti| sub-operators. The code asserts exactly one input and one output TeSA and loops only over weight_tesa; wbc_matmuls likewise takes in_tesas[0] and out_tesas[0]. Thus the implementation enumerates only the weight dimension, matching the claimed 1-D deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `assert\(len\(in_tesa\) == 1 and len\(out_t_tesa\) == 1 and len\(weight_tesa\) >= 1\)` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Confirms specialization requires exactly one input and output TeSA.
- probe `for idx, w_tesa in enumerate\(weight_tesa\):` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Shows only the weight TeSA list is enumerated for sub-operators.
- probe `in_tesa = in_tesas\[0\]` in `sparta/transformation/weighted_block_cover.py` expected present: **confirmed** (1 hit(s)). Confirms transformation selects only the first input TeSA option.
- probe `for w_tesa in w_tesas:` in `sparta/transformation/weighted_block_cover.py` expected present: **confirmed** (1 hit(s)). Shows enumeration is over weight TeSAs, not input Cartesian product.
- what would settle it: A unit test constructing multiple input TeSA options and checking whether all Cartesian-product combinations are specialized would settle it.

## sparta-F033

**论文要求位宽提示指导硬件指令选择（DP4A/wmma）；代码按位宽选不同 CUDA 模板，但模板选择处无基于位宽的指令级特化分支，32bit 分支直接走 cublas/稠密模板（artifact 范围：位宽→模板分派存在，位宽→硬件指令（DP4A）选择不存在）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:44-77`
- condition: `n_bits == 32`
- paper/docs (paper, PDF p.8): “the bit-width of an operator suggests whether to leverage a speciﬁc hardware instruction (e.g., DP4A)”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code dispatches templates by dismantle and passes n_bits, with 8-bit using quantized templates and 32-bit using cublas/block-sparse paths. No DP4A/wmma instruction-level branch appears in the template-selection code. This matches the artifact-scoped finding: bit-width-to-template dispatch exists, but bit-width-to-hardware-instruction selection is absent in the shown selection logic.
- cited code found at the pinned commit: yes (3 location(s))
- probe `(?i)dp4a|wmma` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). No DP4A/wmma selector in template dispatch code.
- probe `n_bits\s*==\s*32` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (4 hit(s)). Bit-width branches exist, but only for template/cublas paths.
- what would settle it: Search the CUDA templates and generated code for DP4A/wmma intrinsics and trace n_bits into template selection; finding a DP4A branch would refute the claim.

## sparta-F034

**artifact 路径无 dismantle 展开步骤，仅消费预生成 kernel。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:44-77`
- condition: `dismantle != -1`
- paper/docs (paper, PDF p.8): “When dismantle is applied on a loop, this loop and all its outer loops are unrolled and specialized with the given sparsity attribute.”
- paper/docs (paper, PDF p.8): “we introduce a new schedule primitive dismantle that jointly performs loop unrolling and DCE.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code only maps dismantle values to pre-existing kernel templates (dense, finegrained, blocksparse). It does not implement loop unrolling, specialization expansion, or DCE; it selects and returns generated kernel code. This matches the finding that the artifact path consumes pre-generated kernels rather than performing dismantle expansion.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)unroll|dead.?code|\bDCE\b` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). No unrolling/DCE logic appears in this specialization file.
- probe `dense_matmul_template|finegrained_matmul_template|blocksparse_matmul_template` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (6 hit(s)). Kernel is selected from pre-generated templates, not expanded.
- what would settle it: Inspect the full specialization pipeline to verify whether any later stage performs dismantle-driven unrolling/DCE rather than only template selection.

## sparta-F035

**执行计划未被重写**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/optimize_model.py:29-54`
- condition: `not is_fast_pass(post_sparsity)`
- paper/docs (paper, PDF p.6): “Correspondingly, SparTA rewrites the execution plan of the associated operator to accommodate”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The shown optimizer calls tpolicy.transform_module and rebuilds modules, but TransformPolicy internals are not shown. specialize_matmul is marked 'mocked for now' yet still returns kernels. This neither proves nor disproves that the execution plan is rewritten; the relevant rewrite logic may be inside transform_module or rebuild functions.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)execution[_ ]?plan` in `sparta/transformation/optimize_model.py` expected absent: **confirmed** (0 hit(s)). No explicit execution-plan text in optimizer; control confirms file searched.
- probe `(?i)rewrite|rewrit` in `sparta/transformation/optimize_model.py` expected absent: **confirmed** (0 hit(s)). No explicit rewrite call in optimizer; transform_module may still rewrite.
- probe `mocked for now` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Kernel specialization is marked mocked, suggesting incomplete implementation.
- probe `return latency, kernels, aggr_type` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Function returns kernel list, which could be an execution plan.
- what would settle it: Inspect TransformPolicy.transform_module and rebuild_sparse_model_* to see whether they construct or rewrite an execution plan, or run a sparse model and dump the generated plan.

## sparta-F036

**论文要求每次调用产生新选项并初始化空列表；代码桩未实现且原地修改输入**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:56-81`
- paper/docs (paper, PDF p.7): “/* return a new transformation option per run */”
- paper/docs (paper, PDF p.7): “Ttrans f ormed = [];”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code shows transform_tesas returning only [(tesa,)] without generating n_candidates new options or initializing an empty transformed list. bit_align mutates the input via _convert_tesa_bit and returns the same tesa. This matches the finding that the stub is unimplemented and modifies input in place, deviating from the paper's per-run new-option requirement.
- cited code found at the pinned commit: yes (2 location(s))
- probe `return \[\(tesa,\)\]` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (2 hit(s)). Shows transform_tesas returns the input unchanged as a single candidate.
- probe `_convert_tesa_bit\(tesa` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows bit_align mutates the input TeSA in place.
- probe `Ttransformed\s*=\s*\[\]` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). Shows no empty transformed-list initialization in the cited file.
- what would settle it: Run transform_tesas and bit_align on a TeSA and check object identity and returned candidates to confirm no new options and in-place mutation.

## sparta-F037

**论文要求返回累积分解列表；代码无该累积返回**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:56-81`
- condition: `len(unique_block_sizes) > 1`
- paper/docs (paper, PDF p.7): “return Ttrans f ormed;”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown code returns [(tesa,)] from transform_tesas and wbc_matmuls only accumulates wbc_matmul outputs. In the multi-block branch, wbc_matmul calls decompose_blocked_tesas but discards its result and raises. Thus no cumulative decomposition list is returned, matching the finding. The paper snippet alone is terse, but the code behavior is clear.
- cited code found at the pinned commit: yes (2 location(s))
- probe `return \[\(tesa,\)\]` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (2 hit(s)). transform_tesas returns only the original tesa, not a decomposition list.
- probe `return decompose_blocked_tesas` in `sparta/transformation/weighted_block_cover.py` expected absent: **confirmed** (0 hit(s)). The multi-block decomposition result is never returned.
- probe `decompose_blocked_tesas\(w_tesa, chosen_blocks, unique_block_sizes\)\s*\n\s*raise` in `sparta/transformation/weighted_block_cover.py` expected present: **refuted** (0 hit(s)). Multi-block path raises instead of returning decomposed candidates.
- what would settle it: Run transform_tesas/wbc_matmuls on a multi-block TeSA and check whether the returned list contains all decomposed sub-tensors rather than a single tuple or an exception.

## sparta-F038

**论文要求对每个 BitRounding 结果 extend 其 WBC 输出；代码 TransformTeSA 未实现该 extend，实际路径仅收集未使用的 transform_options**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:56-81`
- paper/docs (paper, PDF p.7, text lines 86-92): “52 foreach i∈ 1, . . . ,k do 53 T 1 i , . . . ,T j i = self.WeightedBlockCover(Ti); 54 Ttrans f ormed.Extend(T 1 i , . . . ,T j i );”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code shows transform_tesas returning only [(tesa,)] and transform_matmul collecting transform_options from wbc_matmuls without extending or using them; the specialization loop is commented out. This matches the claimed missing Extend step, though the ellipses hide some implementation details.
- cited code found at the pinned commit: yes (3 location(s))
- probe `\.Extend\(` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No Extend call appears in the transformation policy file.
- probe `transform_options\s*=` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). transform_options is collected in transform_matmul.
- probe `wbc_matmuls\(` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). WBC output is produced via wbc_matmuls.
- what would settle it: Run transform_matmul on a multi-bit TeSA and check whether the returned transformed set includes all WBC outputs rather than only the original TeSA.

## sparta-F039

**论文要求按采样位选项产生 k 个结果；代码无采样且限制最多 2 种位宽**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-156`
- condition: `len(aligned_bits) > 2`
- paper/docs (paper, PDF p.7): “T1, . . . ,Tk = self.BitRounding(T , self.SampleBitOption());”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper describes producing T1...Tk via SampleBitOption, implying k sampled bit-width candidates. The shown bit_align ignores n_candidates, returns a single result when only one aligned bit exists, and otherwise asserts exactly two aligned bits. No sampling call appears in the file. This supports the claimed implementation deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `SampleBitOption|sample_bit|random\.sample|np\.random` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No sampling call in this file; control confirms correct file.
- probe `only handle at most 2 different bits` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Comment explicitly limits handling to at most two bit widths.
- probe `assert len\(aligned_bits\) == 2` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Code enforces exactly two aligned bit widths in decompose path.
- what would settle it: Run bit_align with more than two aligned bit widths or inspect all call sites to verify n_candidates is never used and no sampling occurs.

## sparta-F040

**论文要求先经 SampleBitOption 采样一个位选项再传给 BitRounding；代码无采样步骤，bit_align 直接使用 hardware_bit_precisions() 全集合（E4）并返回固定候选，位选项非采样所得。（artifact 范围：无 SampleBitOption 采样，位选项由硬件位宽集合直接决定。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-156`
- paper/docs (paper, PDF p.7): “T1, . . . ,Tk = self.BitRounding(T , self.SampleBitOption());”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code shows bit_align obtains bit_options directly from hardware_bit_precisions() and proceeds to alignment/decomposition without any SampleBitOption call. transform_matmul calls bit_align directly. This matches the finding that the paper's sampling step is absent and bit options are fixed by the hardware precision set.
- cited code found at the pinned commit: yes (3 location(s))
- probe `SampleBitOption` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No sampling call appears in the transformation policy file.
- probe `bit_options\s*=\s*self\.hardware_bit_precisions\(\)` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Bit options are taken directly from hardware precisions.
- probe `weight_tesas\s*=\s*self\.bit_align\(weight_tesa\)` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Transformation path invokes bit_align directly, without prior sampling.
- what would settle it: Search transform_policy.py for any SampleBitOption invocation or run the transformation and verify bit options equal the full hardware precision set.

## sparta-F041

**论文要求每次运行返回新的（可不同的）变换选项；代码每次返回相同候选集合，无“per run 新选项”机制。（artifact 范围：。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-156`
- paper/docs (paper, PDF p.7): “/* return a new transformation option per run */”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code derives candidates deterministically from TeSA bits and hardware precisions. bit_align returns a fixed list, and transform_matmul iterates weight_tesas without randomness, seeding, or per-run state. No mechanism creates a new transformation option per run, matching the claimed deviation.
- cited code found at the pinned commit: yes (3 location(s))
- probe `\brandom\b|\bseed\b|np\.random|torch\.rand` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No randomness or seeding in policy; candidates are deterministic.
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Returns fixed best variables, not a per-run new option.
- what would settle it: Call transform_matmul twice with identical TeSA inputs and compare the produced candidate options; identical results would confirm the deviation.

## sparta-F042

**论文要求每个操作数 TeSA 各自带块大小；代码仅权重 TeSA 获得 block_size，输入/输出 TeSA 的 block_size 保持 None 且不被消费（artifact 范围：仅权重侧 hints 完整）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-191`
- condition: `in_tesa.block_size is not None or out_tesa.block_size is not None`
- paper/docs (paper, PDF p.8): “Specialization hints: T: {Bit: 32, Block: 2x2}, W: {Bit: 32, Block: 2x2}”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper excerpt specifies block hints for T, W, and likely output, but the code assigns block_size only to w_tesa in wbc_matmul. Input and output TeSAs are passed through without block_size assignment, and kernel initialization reads only w_tesa.block_size. This matches the claimed implementation deviation: only weight-side block hints are complete.
- cited code found at the pinned commit: yes (3 location(s))
- probe `w_tesa\.block_size\s*=` in `sparta/transformation/weighted_block_cover.py` expected present: **confirmed** (1 hit(s)). Weight TeSA receives block size; supports weight-only hint.
- probe `(in_tesa|out_tesa)\.block_size` in `sparta/transformation/weighted_block_cover.py` expected absent: **confirmed** (0 hit(s)). No input/output block-size assignment in same file; supports asymmetry.
- probe `block_size\s*=\s*w_tesa\.block_size` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Kernel init consumes only weight block size.
- probe `(i_tesa|o_tesa)\.block_size` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). Input/output block sizes are not consumed in kernel init.
- what would settle it: A code-path test or static trace showing whether in_tesa.block_size and out_tesa.block_size are ever assigned or read would settle it.

## sparta-F043

**论文要求 RecordPerf 记录每次 profile；artifact 路径计算后未记录**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “P.RecordPerf(G=ComposeToGraph(S), Proﬁle(G));”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited transform_matmul path never calls RecordPerf, and its specialization/profiling loop is commented out, so it returns None without profiling. Even the active specialize_matmul computes latency but does not call RecordPerf. Thus the artifact path does not record each profile as the paper's P.RecordPerf(...) requires.
- cited code found at the pinned commit: yes (2 location(s))
- probe `RecordPerf` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). Miss shows transform_matmul never records profiles; control confirms file location.
- probe `RecordPerf` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). Miss shows specialize_matmul computes latency without recording; control confirms file location.
- what would settle it: Run transform_matmul on any input and check whether a RecordPerf call or profile record is emitted.

## sparta-F044

**论文要求返回策略选出的最佳变换；代码无选择逻辑，返回 None**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “return P.BestTransformation();”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper requires returning the best transformation, but the cited code comments out the loop that calls specialize_matmul and updates best_kernels/best_aggr_type. Those variables remain None, so transform_matmul always returns (None, None). The specialization function is also marked mocked. This directly supports the finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Function returns best variables that are never assigned in active code.
- probe `# skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). The selection loop is explicitly commented out, leaving no selection logic.
- probe `# mocked for now` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Specialization is mocked, consistent with no real best-transformation selection.
- what would settle it: Run transform_matmul on any valid TeSA input and observe that it returns (None, None) because the selection loop is commented out.

## sparta-F045

**论文要求先 SampleBitOption 采样再传 BitRounding；代码以固定硬件位宽集合枚举替代采样（artifact 范围：无 SampleBitOption 采样触发）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- condition: `isinstance(module_sparsity.module_obj, nn.Linear)`
- paper/docs (paper, PDF p.7): “T1, . . . ,Tk = self.BitRounding(T , self.SampleBitOption());”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code defines a fixed hardware bitwidth list [4,8,16,32] and routes matmul transformation through bit_align, with no visible SampleBitOption call. This matches the claim that sampling is replaced by fixed bitwidth enumeration, though the snippet alone cannot prove absence across the whole file.
- cited code found at the pinned commit: yes (3 location(s))
- probe `SampleBitOption` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No sampling method in policy file; fixed precision list present.
- probe `hardware_bit_precisions` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (2 hit(s)). Fixed hardware bitwidth enumeration exists in policy.
- probe `bit_align\(` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (4 hit(s)). Bit alignment path is used in transformation.
- probe `return \[4, 8, 16, 32\]` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Hardcoded bitwidth set confirms fixed enumeration.
- what would settle it: Search the full transform_policy.py for SampleBitOption and inspect all bit_align/hardware_bit_precisions call sites to verify no sampling is invoked.

## sparta-F046

**论文要求返回变换后 TeSA 列表；代码对应函数为桩，实际入口返回 None kernel 列表，未返回变换 TeSA 列表**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “return Ttrans f ormed;”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited code shows transform_matmul initializes best_kernels to None and the only specialization loop that could assign it is commented out, so it returns None kernels. transform_tesas is also a stub returning [(tesa,)]. Thus the implementation does not return a transformed TeSA list as the paper states.
- cited code found at the pinned commit: yes (3 location(s))
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Entry returns kernel/aggr values, not transformed TeSA list.
- probe `best_kernels = None` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Best kernels initialized None and never assigned in active code.
- probe `^\s*#.*specialize_matmul` in `sparta/transformation/transform_policy.py` expected present: **refuted** (0 hit(s)). Specialization call is commented out, so no kernels are produced.
- probe `return \[\(tesa,\)\]` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (2 hit(s)). transform_tesas is a stub returning the original TeSA.
- what would settle it: Call transform_matmul with any TeSA and verify its first return value is None rather than a transformed TeSA list.

## sparta-F047

**论文要求调用方迭代多个方案并选满足者；代码迭代循环被注释，未执行方案搜索**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “Given a TeSA, TransformTeSA may have multiple transfor- mation plans. The process iterates over each plan to ﬁnd the satisﬁed one (line 38).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code generates transform_options but the loop that would iterate plans, specialize kernels, and select by latency is inside a triple-quoted comment. The function then returns best_kernels and best_aggr_type, which remain None. This directly matches the finding that plan search is disabled.
- cited code found at the pinned commit: yes (2 location(s))
- probe `# skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows the plan-iteration block is explicitly disabled by a comment.
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows function returns unset best kernels after no selection.
- probe `transform_options = wbc_matmuls\(in_tesas\[0\], w_tesas, out_tesas\[0\]\)` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows options are generated but not iterated for selection.
- what would settle it: Run transform_matmul on a TeSA with multiple transform_options and check whether any specialize_matmul call or non-None best_kernels is produced.

## sparta-F048

**论文要求每次调用返回一个新选项；代码返回固定单元素列表或一次性全部结果**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “/* return a new transformation option per run */”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code shows transform_tesas always returns the fixed single-element list [(tesa,)], and transform_matmul returns best_kernels/best_aggr_type while the loop over transform_options is commented out. Thus it does not yield a new transformation option per call; it returns a fixed result or all candidates at once, matching the finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `return \[\(tesa,\)\]` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (2 hit(s)). Shows transform_tesas returns a fixed single-element list, not a new option per call.
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows transform_matmul returns a fixed pair rather than yielding per-call options.
- probe `# skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows the candidate-iteration/specialization loop is disabled in the cited code.
- what would settle it: Call transform_tesas and transform_matmul repeatedly on the same input and check whether each call returns a distinct new transformation option.

## sparta-F049

**论文声称框架可纳入任意 sparsity-aware 技术；实验路径既未执行 specialization，其可达代码也只有固定模板枚举，无外部内核纳入能力。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8): “SparTA’s specialization framework is general to incorporate any sparsity-aware techniques, including the off-the-shelf sparse kernel and even its dense version.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited transform_matmul has the specialize_matmul loop inside a triple-quoted block, so specialization is not executed and best_kernels remains None. The reachable codegen only selects dense, fine-grained, or block-sparse templates based on dismantle values. No path accepts an external sparsity-aware kernel, supporting the claimed implementation deviation.
- cited code found at the pinned commit: yes (2 location(s))
- probe `skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows specialization loop is disabled by a comment block.
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Shows disabled path returns unset kernel selection.
- probe `dense_matmul_template|finegrained_matmul_template|blocksparse_matmul_template` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (6 hit(s)). Shows only three fixed kernel templates are enumerated.
- probe `if dismantle == -1:|elif dismantle == 8:|elif dismantle == 2:` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (3 hit(s)). Shows template choice is fixed by dismantle value.
- what would settle it: Run transform_matmul on any TeSA and verify whether specialize_matmul is ever invoked and whether any non-template external kernel can be selected.

## sparta-F050

**When info.module_name in self.modules_info: When a module name is already present, the merge branch is an empty ellipsis body, so the new SparseModuleInfo (and its updated TeSA attributes) is silently discarded and the earlier state is kept. The mechanism therefore depends on earlier update() calls and ignores later sparsity info for the same module. (sparta/common/sparsity.py:57)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/common/sparsity.py:57` in `sparta/common/sparsity.py::ModelSparsityInfo.update`
- condition: `info.module_name in self.modules_info`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: The merge branch is a stub, but the only caller, extract_sparsity, iterates model.named_modules(), whose names are unique, so a duplicate module name never reaches it.
- code snippet (`sparta/common/sparsity.py:57`): `if info.module_name in self.modules_info:`

**Not tested** (`outcome_unsupported`): effect type 'other': the branch has no raise in its body: the program rejects later, in code the target does not point to

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The snippet shows only the condition at line 57; it does not show the branch body or whether existing entries are updated elsewhere. The claimed silent discard is plausible but not established by the displayed evidence.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?s)if info\.module_name in self\.modules_info:\s*\n\s*\.\.\.` in `sparta/common/sparsity.py` expected present: **refuted** (0 hit(s)). Hit shows the existing-module branch is an empty ellipsis body.
- what would settle it: Read the full update method around line 57 to verify the if body is only `...` and no later assignment updates existing modules.

## sparta-F051

**论文要求量化比特收敛规则；代码只处理剪枝掩码，无量化属性种类**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.5): “For quantization, the attribute will be converged to the fewest quantization bits (or 0-bit, i.e., being pruned).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **supports**. The paper quote establishes a quantization-bit convergence requirement. The Step 4 note identifies the relevant propagate_mask/infer_modules_masks path and states it only handles pruning masks, with no quantization-attribute convergence logic. Although no raw code snippet is recorded, the note directly describes the missing implementation, so the finding is supported.
- what would settle it: Inspect propagate_mask/infer_modules_masks and search for any quantization-bit or attribute convergence code; absence would confirm the gap.

## sparta-F052

**论文要求分发前初始化 Iupdated/Oupdated 空集；代码无规则分发，仅建空字典收集结果**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “Iupdated = Oupdated = /0;”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper quote confirms the stated precondition, but no code evidence is recorded. Without seeing the relevant code, I cannot verify that Iupdated/Oupdated are never initialized as empty sets or that only an empty dict is built. The finding's code-level claim is therefore unsupported by the shown evidence.
- what would settle it: Inspect the cited propagation code for initialization of Iupdated and Oupdated as empty sets before distribution.

## sparta-F053

**论文要求 foreach RegisteredPropRule 调用规则；代码为固定两个硬编码推断函数，无注册表迭代**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “foreach RegisteredPropRule do”
- paper/docs (paper, PDF p.6): “Iproped ,Oproped = RegisteredPropRule(N, Is, Os);”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper excerpts show a foreach RegisteredPropRule requirement and registration calls, but no code evidence is recorded. Without the implementation, the claim that the code uses two hardcoded inference functions and never iterates a registry cannot be verified. The paper side is supported, but the alleged code-paper gap is unsubstantiated.
- what would settle it: Inspect the propagation/inference implementation to see whether it iterates over registered rules or directly calls two hardcoded functions.

## sparta-F054

**论文要求把规则返回的 Iproped/Oproped 合并进节点 Is/Os；代码无规则返回值，直接由硬编码推断写 masks**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “Is.Update(Iproped ); Os.Update(Oproped );”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper quote shows the intended merge of Iproped/Oproped into Is/Os, but no code evidence is recorded. The finding's key claim—that the code never reads rule-returned values and instead writes masks via hardcoded inference—cannot be verified from the shown evidence.
- what would settle it: Inspect the code that updates Is/Os and trace whether Iproped/Oproped from the rule are read or whether masks are assigned by hardcoded logic.

## sparta-F055

**论文要求累积每条规则更新到 Iupdated/Oupdated；代码为逐层快照收集，无规则更新累积**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “Iupdated .Update(Iproped );”
- paper/docs (paper, PDF p.6): “Oupdated .Update(Oproped );”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The finding cites only paper lines requiring cumulative Iupdated/Oupdated updates. No code evidence is recorded, so the alleged layer-by-layer snapshot implementation and absence of rule-update accumulation cannot be verified. The cited names also do not appear in the shown code evidence.
- what would settle it: Inspect the implementation that populates Iupdated/Oupdated to see whether updates accumulate across rules or are collected as per-layer snapshots.

## sparta-F056

**artifact 路径无单块回退到通用稀疏/dense kernel 的分派。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.8, text lines 117-122): “A specialization hint could also specify the block size equal to the tensor’s shape (i.e., one block covers the whole tensor). In this case, SparTA can directly use the existing state-of-the- art general sparse kernel implementation (e.g., cuSPARSE [3], taco [53]) or even use the dense kernel imple…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. The paper states that when block size equals the tensor shape, SparTA can fall back to a general sparse or dense kernel. The Finding claims the artifact lacks this dispatch, but no code evidence or repository paths are shown. Without inspecting the dispatch logic, the absence cannot be confirmed or contradicted.
- what would settle it: Inspect the specialization/dispatch code for a branch where block size equals the tensor shape and verify whether it invokes a general sparse or dense kernel.

## sparta-F057

**artifact 路径无该搜索步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.8): “It searches from the outermost loop until the level (say l) of inner loop body aligns with the block size.”
- paper/docs (paper, PDF p.8): “dismantle is applied on the third loop, thus the top three loops are unrolled, generating eight small Matmuls (i.e., [2,2]x[2,2]).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. no code is cited: the reading rests on the paper text alone

- reading: **unclear**. No code evidence is recorded, and the cited paper only describes the intended search. The Step 4 note asserts absence in sparta_kernel_fetch_pass.cpp but does not show the file or a control search. Without seeing the implementation, the claim that no block-size-aligned loop search exists is not verifiable.
- what would settle it: Search sparta_kernel_fetch_pass.cpp for loop traversal and block-size alignment checks before Weight_Dismantled marking, with a control match in the same file.

## sparta-F058

**论文要求从最近缓存激活部分推理；代码无缓存也无部分推理**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:260-299`
- paper/docs (paper, PDF p.6): “Collecting an operator’s calibration data only needs partial inference from the nearest cached activations to this operator.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code builds calibration/training data with torch.rand dummy tensors and finetunes each conv module; it never loads or propagates cached activations. Thus the paper's nearest-cached-activation partial-inference requirement is not implemented in the shown path.
- cited code found at the pinned commit: yes (2 location(s))
- probe `torch\.rand\(` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (12 hit(s)). Random dummy inputs are generated instead of cached activations.
- probe `cached_activations|activation_cache|nearest_cached` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No cache-related identifiers appear in the cited script.
- what would settle it: Search the full script for any activation-cache load/propagation path and run the calibration to see whether cached activations are used.

## sparta-F059

**无注册调用**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:260-299`
- paper/docs (paper, PDF p.6): “RegisterPropRule(QuantizationPropRule);”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited script uses QAT_Quantizer and configure lists but shows no RegisterPropRule(QuantizationPropRule) call. The paper states that registration as a precondition, so the shown code lacks it. The evidence is limited to the cited file, but it supports the finding that the registration call is absent.
- cited code found at the pinned commit: yes (2 location(s))
- probe `RegisterPropRule\s*\(` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No registration call in cited script; supports missing precondition.
- probe `QuantizationPropRule` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). Propagation-rule class is not referenced in this script.
- what would settle it: A repository-wide grep plus execution trace showing RegisterPropRule(QuantizationPropRule) is never invoked before PropOneNode would settle it.

## sparta-F060

**论文要求 La 输出激活部分推理得 Lb 校准数据；代码无此复用**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:260-299`
- paper/docs (paper, PDF p.6): “consider a sequential model with two layers La and Lb. The propagation on La has collected its output activations in its calibration data. When working on Lb, its calibration data can be collected by doing partial inference from the collected output activations of La.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code builds each layer's training/validation data with fresh torch.rand(dummy_input_shape) tensors and never references La's collected output activations. The paper's described partial-inference propagation from La to Lb is therefore not implemented in the shown path.
- cited code found at the pinned commit: yes (2 location(s))
- probe `torch\.rand\(dummy_input_shape\)` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (8 hit(s)). Shows calibration/training inputs are randomly generated, not reused activations.
- probe `output_activations|activation.*calib|calib.*activation` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No textual evidence of reusing La output activations for Lb calibration.
- probe `def train_bit_propagate` in `script/figure14/search_finetune_fit_qat.py` expected present: **confirmed** (1 hit(s)). Confirms the cited propagation-related function exists in this file.
- what would settle it: Trace or instrument train_bit_propagate to verify whether Lb calibration data ever derives from La outputs rather than fresh random tensors.

## sparta-F061

**无 TeSA 集合初始化**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:301-335`
- paper/docs (paper, PDF p.6): “Supdated = /0; S = ( Is∪ Os );”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code performs QAT quantization with input/weight/output bit settings and finetuning, but shows no TeSA set initialization such as Supdated = ∅ or S = (Is ∪ Os). The absence is consistent across the shown calls, so the finding that TeSA set initialization is not implemented is supported.
- cited code found at the pinned commit: yes (2 location(s))
- probe `TeSA|Supdated|S\s*=\s*\(\s*Is|Is\s*∪\s*Os` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). No TeSA set initialization appears; control confirms the file was searched.
- what would settle it: A text search of the pinned file for TeSA/Supdated/Is∪Os initialization, plus inspection of the quantization path, would settle it.

## sparta-F062

**无 SplitToIsOs 返回**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:301-335`
- paper/docs (paper, PDF p.6): “return SplitToIsOs(Supdated );”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code performs QAT_Quantizer.compress(), dummy training, and bit substitution, but never calls SplitToIsOs or evaluates all tensors in Is∪Os. The cited implementation therefore lacks the paper's SplitToIsOs return on the shown path.
- cited code found at the pinned commit: yes (2 location(s))
- probe `SplitToIsOs` in `script/figure14/search_finetune_fit_qat.py` expected absent: **confirmed** (0 hit(s)). Miss shows no SplitToIsOs call; control confirms the file was searched.
- what would settle it: Search the pinned repository for any SplitToIsOs definition or call and inspect whether the paper's return path is implemented.

## sparta-F063

**artifact 路径无编译后延迟/内存测量步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4, text lines 67-69): “Finally, with the ﬁnal compiled code, model designers can proﬁle the DNN model to obtain authentic performance met- rics, including memory consumption and inference latency.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited figure19 path only runs iterative_SA.py with speed-up off/on and draw.py. draw.py parses training-time and total-time log entries and plots training time; it does not invoke a compiled-model profiling path or measure inference latency/memory. This matches the finding that the artifact path lacks compiled latency/memory measurement.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)latency|memory|profil|compile` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No profiling/latency/memory command in the figure19 runner.
- probe `(?i)latency|memory|profil|compile` in `script/figure19/draw.py` expected absent: **confirmed** (0 hit(s)). Plotting script has no latency/memory/profiling references.
- probe `(?i)training_time|total_time` in `script/figure19/draw.py` expected present: **confirmed** (6 hit(s)). Only training and total time are parsed, not latency/memory.
- what would settle it: Inspect all scripts in the artifact path for any call that profiles a compiled model and records inference latency or memory; none should exist if the finding holds.

## sparta-F064

**artifact 路径无真实延迟过滤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14, text lines 46-49): “in Figure 19. Our baseline uses FLOPS as the metric to ﬁlter out the disqualiﬁed models: the model whose FLOPS is larger than 70% of the original FLOPS. In contrast, SparTA uses the real latency to ﬁlter models. The result is shown in Figure 19.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited figure19 script only runs iterative_SA.py with --speed-up True/False and then draw.py. It contains no latency measurement, profiling, compile, or SparTA invocation. Thus the shown artifact path does not implement the paper's real-latency filtering; the baseline/SPARTA distinction is only a speed-up flag.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)latency|profile|compile|sparta` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No real-latency filtering or SparTA profiling call appears in the figure19 script.
- probe `speed-up` in `script/figure19/run.sh` expected present: **confirmed** (2 hit(s)). The script only toggles a speed-up flag, not measured latency filtering.
- what would settle it: Inspect iterative_SA.py and draw.py for any latency measurement/filtering, or run figure19 and verify whether filtering uses measured latency.

## sparta-F065

**artifact 无编译迭代。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4): “This process may be iterated for further improvement.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The paper says the process may be iterated, but the shown artifact does not implement repeated compilation. figure19/run.sh only runs iterative_SA.py twice (baseline and speed-up) and then draws; it has no loop or re-feed of compiled output. sparta/core/sparta.py calls optimize_and_rebuild once inside SpartaModel.__init__, with no iteration around compilation. Thus the cited code supports the claim that iterative compilation is absent.
- cited code found at the pinned commit: yes (2 location(s))
- probe `\b(for|while)\b|range\(` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No loop in figure script; it only invokes the pruner twice.
- probe `for\s+.*optimize|while\s+.*optimize` in `sparta/core/sparta.py` expected absent: **confirmed** (0 hit(s)). No loop around optimize_and_rebuild; SpartaModel compiles once.
- probe `SpartaModel` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). Figure script never instantiates SpartaModel; no compiled-output re-feed.
- what would settle it: Run figure19 and inspect whether iterative_SA.py repeatedly compiles or re-feeds the optimized model, or grep iterative_SA.py for a loop around pruning/compilation.

## sparta-F066

**artifact 无 FLOPs 过滤基线。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14): “Our baseline uses FLOPS as the metric to ﬁlter out the disqualiﬁed models: the model whose FLOPS is larger than 70% of the original FLOPS.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited run.sh only launches iterative_SA with speed-up True/False and draws results; it contains no FLOPs computation, no 70% threshold, and no model-disqualification step. This matches the paper's described baseline filter being absent from the cited artifact entrypoint. Control probes confirm the file was searched.
- cited code found at the pinned commit: yes (1 location(s))
- probe `(?i)flops?|floating.point.operations` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No FLOPs term in run.sh; control confirms the script was searched.
- probe `70\s*%|0\.7|70` in `script/figure19/run.sh` expected absent: **confirmed** (0 hit(s)). No 70% threshold in run.sh; control confirms the script was searched.
- what would settle it: Inspect iterative_SA.py and all baseline scripts for FLOPs computation and a >70%-of-original rejection path.

## sparta-F067

**论文要求对每个 (sub)operator 执行量化特化；artifact 链中特化调用被注释、重建为直通，未执行任何循环级特化。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/core/sparta.py:16-24`
- condition: `backend == 'pytorch'`
- paper/docs (paper, PDF p.8, text lines 125-127): “Specializing operators with quantization attributes also works on the multi-level loops, but starting from the inner- most loop. SparTA picks a proper hardware instruction based”
- paper/docs (paper, PDF p.8): “and then replace the rearranged loop body with the instruction”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown transform_matmul initializes best_kernels/best_aggr_type to None, places the only specialize_matmul loop inside a triple-quoted block, and returns those None values. optimize_and_rebuild then only calls transform_module and rebuilds modules. This directly supports that quantization specialization is not executed in the artifact chain; the paper's loop-level specialization is absent.
- cited code found at the pinned commit: yes (4 location(s))
- probe `# skip, waiting for more official end-to-end[\s\S]*?specialize_matmul` in `sparta/transformation/transform_policy.py` expected present: **refuted** (0 hit(s)). specialize_matmul follows a skip comment inside the commented block
- probe `best_kernels\s*=\s*None` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). specialization result initialized to None and not actively overwritten
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). function returns None kernels/aggr_type after skipped specialization
- what would settle it: Instrument transform_matmul on a quantized TeSA and check whether specialize_matmul is invoked and returns non-None kernels, or parse the AST to confirm the call is inside a string literal.

## sparta-F068

**论文要求可注册新算子规则；代码无注册机制，新增算子需改源码**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/propagation/talgebra.py:4-17`
- paper/docs (paper, PDF p.5): “Note that Table 2 can be extended to support new operators.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code hardcodes TeSA algebra via Algebra.__add__/__mul__ and fixed propagate_matmul logic. No registration API, decorator, registry, or operator-rule table appears in the shown file. Adding a new operator would require editing source, matching the finding that the paper's extensibility claim is not implemented.
- cited code found at the pinned commit: yes (4 location(s))
- probe `(?i)register|registry|add_operator|operator_rule|register_operator` in `sparta/propagation/talgebra.py` expected absent: **confirmed** (0 hit(s)). No operator registration mechanism in cited file; control confirms correct file.
- probe `def propagate_matmul` in `sparta/propagation/talgebra.py` expected present: **confirmed** (1 hit(s)). Propagation is a fixed function, not dynamically registered operator rules.
- what would settle it: Search the full repository for any operator registration API and try adding a new operator without modifying source files.

## sparta-F069

**无 TransformOp 级 S 初始化**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- paper/docs (paper, PDF p.7): “S = [];”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited specialize_matmul only builds kernels, accumulates latency, and returns aggr_type; it never initializes a TransformOp-level S list. The paper snippet shows S = [], but the shown code has no corresponding initialization, so the finding is supported for this function.
- cited code found at the pinned commit: yes (1 location(s))
- probe `S\s*=\s*\[\]` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). Miss shows no S=[] initialization; control confirms file was searched.
- what would settle it: Search the full specialization/TransformOp code for any S initialization, or run specialization and check whether S exists.

## sparta-F070

**论文要求组合为图 G；代码无图构造步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- paper/docs (paper, PDF p.7): “P.RecordPerf(G=ComposeToGraph(S), Proﬁle(G));”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited function only initializes/tunes matmul kernels, accumulates per-kernel latency, and returns kernels plus aggr_type. It never constructs a graph G or calls ComposeToGraph/RecordPerf, so the paper's graph-composition step is absent from this path. The evidence directly supports the claimed not_implemented gap.
- cited code found at the pinned commit: yes (1 location(s))
- probe `ComposeToGraph|RecordPerf` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). Absence shows no graph composition or profiling call in this file.
- what would settle it: Search the pinned repository for any ComposeToGraph/RecordPerf implementation or call reachable from specialize_matmul.

## sparta-F071

**依赖存在但未被该判定消费，属未接线而非实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:44-77`
- condition: `block_size is not None and block_size != 1`
- paper/docs (paper, PDF p.8): “A specialization hint could also specify the block size equal to the tensor’s shape (i.e., one block covers the whole tensor).”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The shown code branches only on block_size None, 1, or else; it never compares block_size to the tensor shape. Any other value, including a shape-sized block, is routed to the generic blocksparse template. Thus the paper’s whole-tensor block-size hint is not explicitly wired as a specialization, matching the not_implemented finding.
- cited code found at the pinned commit: yes (2 location(s))
- probe `block_size\s*==\s*(shape|matmul_shape|m|k|n)` in `sparta/specialization/specialize_kernel.py` expected absent: **confirmed** (0 hit(s)). No shape-equality branch; only sentinel 1 branch exists.
- probe `block_size\s*==\s*None` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Block size is used as a None sentinel for dense selection.
- probe `blocksparse_matmul_template\([^\n]*block_size` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (2 hit(s)). Non-sentinel block sizes are passed to generic blocksparse template.
- what would settle it: A static search or unit test that sets block_size to the tensor shape and checks whether a dedicated whole-tensor specialization is selected would settle it.

## sparta-F072

**论文要求特化 tiling 对齐指令形状；artifact 入口链无 tiling 生成步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/optimize_model.py:29-54`
- condition: `backend == 'pytorch'`
- paper/docs (paper, PDF p.8, text lines 129-131): “for 8bit, wmma for 4bit. The specialized tiling of the innermost loop(s) is then aligned to the computation shape of the in- struction. For example, one supported computation shape of”
- paper/docs (paper, PDF p.8): “one supported computation shape of wmma is the Matmul [16,16]x[16,16]. To specialize for this instruction, the tiling should rearrange the innermost loop body to align with the shape”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The shown entry chain calls transform_module, and transform_matmul's specialization loop is commented out, so no specialize_matmul/tiling generation is active. The paper requires tiling aligned to instruction shape, but the artifact path shown returns without generating such tiling. This supports the finding, though the snippets are not exhaustive.
- cited code found at the pinned commit: yes (2 location(s))
- probe `^\s*latency, kernels, aggr_type = specialize_matmul\(` in `sparta/transformation/transform_policy.py` expected absent: **refuted** (1 hit(s)). Active specialization call absent; only commented block remains.
- probe `tiling` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No tiling generation in transform policy file.
- probe `tiling|specialize_matmul` in `sparta/transformation/optimize_model.py` expected absent: **confirmed** (0 hit(s)). Entry chain lacks tiling or specialization call.
- what would settle it: Run optimize_and_rebuild on a sparse matmul and inspect generated kernels or IR for instruction-shaped tiling.

## sparta-F073

**论文要求 DP4A 重排+替换；artifact 入口链无此步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/optimize_model.py:29-54`
- condition: `backend == 'pytorch'`
- paper/docs (paper, PDF p.8): “The tiling for the instruction DP4A with a shape [1,4]x[4,1] can be done similarly.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A1 (uncalibrated; this is not a test verdict).** text-only reading (no runnable code, no probe): the lowest tier. the reading is unclear; probes alone do not decide it

- reading: **unclear**. The paper quote says DP4A tiling 'can be done similarly,' not that it is required. The shown entry functions contain no DP4A, but they do not cover the full transformation chain (e.g., wbc_matmuls, specialize_matmul), so absence in these snippets cannot establish that the artifact lacks DP4A reorder/replacement.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)dp4a` in `sparta/transformation/optimize_model.py` expected absent: **confirmed** (0 hit(s)). Entry file has no DP4A mention; control confirms correct file.
- probe `(?i)dp4a` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). Transform policy lacks DP4A text; control confirms correct file.
- what would settle it: Search the full transformation entry chain, including transform_module, wbc_matmuls, and kernel specialization, for DP4A reorder/replacement and compare it with the paper's actual requirement.

## sparta-F074

**论文要求 while 搜索；artifact 路径仅单遍枚举**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “while P.HasBudget() and P.PerfNotSatisﬁed() do”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited transform_matmul has no while HasBudget/PerfNotSatisfied loop; its inner transform_options specialization loop is commented out, and specialize_matmul is explicitly mocked. Thus the shown path performs only a single enumeration over weight_tesas and cannot implement the paper's budget/performance-driven search.
- cited code found at the pinned commit: yes (2 location(s))
- probe `while\s+P\.HasBudget` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No paper-style budget while loop in transform_matmul
- probe `# skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Inner specialization/enumeration loop is disabled by commenting
- probe `# mocked for now` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Specialization and latency profiling are mocked, not real search
- what would settle it: Run transform_matmul on any input and verify it never iterates under HasBudget/PerfNotSatisfied and never calls a real specialize_matmul.

## sparta-F075

**论文要求按 TeSA 位宽选指令；artifact 链未调用特化，位宽选择步骤不存在。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8): “SparTA picks a proper hardware instruction based on the bit-width denoted in TeSA, e.g., DP4A [13] or wmma [5] for 8bit, wmma for 4bit.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited transform_matmul computes bit-aligned TeSA options but the only specialize_matmul call is inside a triple-quoted skipped block. It then returns best_kernels and best_aggr_type, which remain None. The hardware_bit_precisions helper exists but is not called in this file. Thus the bit-width-based instruction selection step is absent from the artifact chain.
- cited code found at the pinned commit: yes (2 location(s))
- probe `# skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Specialization block is explicitly marked skipped.
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Function returns unset best values after loop.
- probe `self\.hardware_bit_precisions\(` in `sparta/transformation/transform_policy.py` expected absent: **refuted** (1 hit(s)). Bit-precision helper is defined but not called here.
- what would settle it: Run transform_matmul on any TeSA and check whether specialize_matmul is invoked and returns non-None kernels/aggr_type.

## sparta-F076

**实验路径未执行 specialization 内核选择，且无 block==shape→通用稀疏内核的代码路径；依赖存在不等于执行路径存在。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8, text lines 117-121): “A specialization hint could also specify the block size equal to the tensor’s shape (i.e., one block covers the whole tensor). In this case, SparTA can directly use the existing state-of-the- art general sparse kernel implementation (e.g., cuSPARSE [3], taco [53]) or even use the dense kernel imple…”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited transform_matmul comments out the entire specialize_matmul loop and returns best_kernels/best_aggr_type that are never assigned in active code. The Dockerfile only installs taco, showing dependency presence, not an execution path. Thus the block==shape→general sparse kernel selection is not executed and no active code path implements it.
- cited code found at the pinned commit: yes (2 location(s))
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Returns selection variables never assigned in active code.
- probe `# then specialize kernels for this transformation option` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Kernel-selection call sits inside a commented block.
- probe `latency, kernels, aggr_type = specialize_matmul` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Specialization call text exists only in disabled loop context.
- probe `git clone https://github.com/QuanluZhang/taco.git` in `image/Dockerfile` expected present: **confirmed** (1 hit(s)). Taco dependency installed, not evidence of runtime execution.
- what would settle it: Run transform_matmul and check whether specialize_matmul is invoked and best_kernels becomes non-None, especially for block==shape inputs.

## sparta-F077

**实验路径未运行内核选择，且无 block==shape 的稠密回退分支。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8): “or even use the dense kernel implementation if it perform better.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited transform_matmul calls wbc_matmuls but the only specialize_matmul/kernel-selection loop is inside a triple-quoted comment, so it never executes. best_kernels and best_aggr_type remain None. No block==shape dense fallback appears in the shown code, matching the claim that the experimental path skips kernel selection and dense fallback.
- cited code found at the pinned commit: yes (1 location(s))
- probe `^\s*latency, kernels, aggr_type = specialize_matmul\(` in `sparta/transformation/transform_policy.py` expected absent: **refuted** (1 hit(s)). No active kernel-selection call; only commented code.
- probe `block\s*==\s*shape` in `sparta/transformation/transform_policy.py` expected absent: **confirmed** (0 hit(s)). No block==shape dense fallback branch in this file.
- what would settle it: Run transform_matmul on any valid TeSA input and verify it returns None kernels without invoking specialize_matmul or a dense fallback.

## sparta-F078

**论文要求从枚举结果选最佳；代码无候选集合，择优逻辑被注释**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:172-191`
- paper/docs (paper, PDF p.9): “and pick the best one”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited code computes transform_options but the loop that would specialize each option and update best_latency/best_kernels is inside a triple-quoted comment. The function then returns best_kernels and best_aggr_type without executing any best-selection logic, matching the finding that the paper's 'pick the best one' step is not implemented.
- cited code found at the pinned commit: yes (1 location(s))
- probe `for \(in_ts, w_ts, out_ts\) in transform_options:` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Candidate loop text exists in the cited region.
- probe `if latency < best_latency:` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Best-latency comparison exists in the cited region.
- probe `'''\s*# skip, waiting for more official end-to-end` in `sparta/transformation/transform_policy.py` expected present: **refuted** (0 hit(s)). Triple-quoted comment starts before the candidate loop, disabling it.
- probe `return best_kernels, best_aggr_type` in `sparta/transformation/transform_policy.py` expected present: **confirmed** (1 hit(s)). Function returns stored best values without executing the commented selection loop.
- what would settle it: Run the function with multiple transform_options and verify specialize_matmul is never called and best_latency is never updated.

## sparta-F079

**artifact 路径无 13 块大小评估入口**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:7-24`
- paper/docs (paper, PDF p.9, text lines 19-21): “weight of different block sizes. Speciﬁcally, we implemented a kernel template for block sparsity, and evaluated 13 dif- ferent block sizes on that template. The overhead of each”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **contradicts**. The cited specialize_kernel.py exposes blocksparse_matmul_template(..., block_size, ...), which accepts block_size_k/n and generates the block-sparse kernel; it is not limited to the seven cover sizes. available_covering_size is a cost table for weighted cover, not the evaluation entry. Thus the claim that no block-size evaluation entry exists is contradicted by the shown code, though an explicit 13-size benchmark is not shown.
- cited code found at the pinned commit: yes (3 location(s))
- probe `def blocksparse_matmul_template\(shape, n_bits, block_size, bias\)` in `sparta/specialization/specialize_kernel.py` expected present: **confirmed** (1 hit(s)). Confirms callable entry point accepts block size parameter.
- probe `\(128, 128\)` in `sparta/transformation/weighted_block_cover.py` expected absent: **confirmed** (0 hit(s)). Shows cover table has only seven sizes, not evaluation loop.
- what would settle it: Search the artifact for a benchmark script that loops over 13 block sizes or run blocksparse_matmul_template with 13 sizes.

## sparta-F080

**artifact 路径无零稀疏延迟测量入口**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:7-24`
- paper/docs (paper, PDF p.9): “The overhead of each block size is proﬁled by measuring the latency of the kernel with zero sparsity”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited code only returns hardcoded profiled block costs and generates kernel templates. Neither file contains a zero-sparsity latency measurement entry, benchmark loop, timing call, or profiling harness. The docstring even says the numbers are pre-profiled costs. This supports the claim that the artifact lacks a measurement path for zero-sparsity latency per block size, though the shown evidence is limited to these files.
- cited code found at the pinned commit: yes (2 location(s))
- probe `(?i)(zero[_-]?sparsity|latency|measure|profil(e|ing)|benchmark|timeit|cudaEvent)` in `sparta/transformation/weighted_block_cover.py` expected absent: **refuted** (1 hit(s)). No timing or zero-sparsity measurement entry in cost table file.
- probe `(?i)(zero[_-]?sparsity|latency|measure|profil(e|ing)|benchmark|cudaEvent)` in `sparta/specialization/specialize_kernel.py` expected absent: **refuted** (17 hit(s)). Kernel template generator has no latency measurement code.
- what would settle it: Search the full repository for any zero-sparsity latency profiling harness or run such a harness to see whether it exists.

## sparta-F081

**论文要求 latency/块数；代码无该计算，E2 除法语义不同（按覆盖元素数分摊）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:7-24`
- paper/docs (paper, PDF p.9): “dividing the latency with the number of blocks”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A0 (uncalibrated; this is not a test verdict).** evidence could not be grounded, or the reading and the probes disagree. the reading and the probes disagree

- reading: **supports**. The cited function only returns a hardcoded cover-size cost table; it contains no latency value and no division by block count. This supports the core not_implemented claim. The additional E2 semantic-difference detail is not independently evidenced by this snippet, but the absence of the paper's latency-per-block computation is supported.
- cited code found at the pinned commit: yes (1 location(s))
- probe `\blatency\b` in `sparta/transformation/weighted_block_cover.py` expected absent: **confirmed** (0 hit(s)). No latency variable in cited file; control confirms file searched.
- probe `(?i)block(s)?\s*(count|number)|num_blocks|n_blocks` in `sparta/transformation/weighted_block_cover.py` expected absent: **refuted** (7 hit(s)). No block-count variable in cited file; control confirms search location.
- probe `/` in `sparta/transformation/weighted_block_cover.py` expected absent: **refuted** (5 hit(s)). No division operator in file; control confirms correct file.
- what would settle it: Search the full repository for any latency divided by block count; the finding is confirmed if only hardcoded cover-size costs exist.

## sparta-F082

**论文要求过稀疏时枚举所有块大小组合并选最优；代码无枚举、无最优选择、无触发条件**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:47-102`
- paper/docs (paper, PDF p.9): “When an operator is too sparse to saturate available cores, the weights may become less accurate. In such cases, we enumerate all the combinations of block sizes to run the weighted block cover algorithm and pick the best one.”

**Not tested** (`no_code_location`): no code location: a static discrepancy between the paper and the code (no executable claim): judging it needs a reference implementation of the paper's formula to compare against (differential oracle)

**Analysis only, tier A2 (uncalibrated; this is not a test verdict).** code found at the pinned commit and a deterministic probe agrees with the reading. the probes confirm what the Finding says

- reading: **supports**. The cited code returns a single weighted block cover and wbc_matmuls explicitly says it returns only one covering option. There is no enumeration of block-size combinations, no comparison/selection of a best covering, and optimize_model has no too-sparse trigger. This matches the finding that the paper-described behavior is absent.
- cited code found at the pinned commit: yes (3 location(s))
- probe `itertools\.combinations|combinations\(` in `sparta/transformation/weighted_block_cover.py` expected absent: **confirmed** (0 hit(s)). No block-size combination enumeration in cover algorithm.
- probe `enumerate all|pick the best|optimal` in `sparta/transformation/weighted_block_cover.py` expected absent: **confirmed** (0 hit(s)). No best-option selection or enumeration in file.
- probe `only return one covering option` in `sparta/transformation/weighted_block_cover.py` expected present: **confirmed** (1 hit(s)). Docstring confirms single covering option returned.
- probe `too sparse|saturate|enumerate|combinations|best` in `sparta/transformation/optimize_model.py` expected absent: **confirmed** (0 hit(s)). No sparsity trigger or enumeration in optimization entry.
- what would settle it: Run a sparse operator through TransformPolicy and inspect whether multiple block-size coverings are generated and compared; the code shows only one.

