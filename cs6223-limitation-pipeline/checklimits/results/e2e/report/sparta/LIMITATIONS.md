# Limitations report: SparTA: Deep-Learning Model Sparsity via Tensor-with-Sparsity-Attribute

- artifact: `sparta` (OSDI 2022), repository https://github.com/microsoft/SparTA at `1f61a363b1`
- input: `results/step4/sparta/limitations_for_tests.json` (sha256 `af8cad7c4e91`), 82 Findings
- generated: 2026-11-16T16:09:59+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
- environment: **not_ok** (repository third_party/SparTA is not checked out)

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 82 |
| tested | 0 |
| not tested | 82 |
| not tested, by reason | `env_unavailable` 3, `no_code_location` 79 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [sparta-F001](#sparta-f001) | undisclosed | path_change | `sparta/transformation/weighted_block_cover.py:77` | not tested: `env_unavailable` |
| [sparta-F002](#sparta-f002) | docs_only | reject | `sparta/transformation/weighted_block_cover.py:123` | not tested: `env_unavailable` |
| [sparta-F003](#sparta-f003) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F004](#sparta-f004) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F005](#sparta-f005) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F006](#sparta-f006) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F007](#sparta-f007) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F008](#sparta-f008) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F009](#sparta-f009) | impl_deviates | other |  | not tested: `no_code_location` |
| [sparta-F010](#sparta-f010) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:169-178` | not tested: `no_code_location` |
| [sparta-F011](#sparta-f011) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:301-335` | not tested: `no_code_location` |
| [sparta-F012](#sparta-f012) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:496-538` | not tested: `no_code_location` |
| [sparta-F013](#sparta-f013) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:496-538` | not tested: `no_code_location` |
| [sparta-F014](#sparta-f014) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:571-664` | not tested: `no_code_location` |
| [sparta-F015](#sparta-f015) | impl_deviates | other | `script/figure14/search_finetune_fit_qat.py:571-664` | not tested: `no_code_location` |
| [sparta-F016](#sparta-f016) | impl_deviates | other | `script/figure16/a100/sparta.cu:118-140` | not tested: `no_code_location` |
| [sparta-F017](#sparta-f017) | impl_deviates | other | `script/figure16/a100/sparta.cu:266-311` | not tested: `no_code_location` |
| [sparta-F018](#sparta-f018) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F019](#sparta-f019) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F020](#sparta-f020) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F021](#sparta-f021) | impl_deviates | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F022](#sparta-f022) | impl_deviates | other | `script/init_checkpoints.sh:1-34` | not tested: `no_code_location` |
| [sparta-F023](#sparta-f023) | impl_deviates | other | `script/run_all_2080ti.sh:1-57` | not tested: `no_code_location` |
| [sparta-F024](#sparta-f024) | impl_deviates | other | `sparta/artifact_specialization/generate_code.py:58-82` | not tested: `no_code_location` |
| [sparta-F025](#sparta-f025) | impl_deviates | other | `sparta/artifact_specialization/generate_code.py:58-82` | not tested: `no_code_location` |
| [sparta-F026](#sparta-f026) | impl_deviates | other | `sparta/propagation/talgebra.py:4-17` | not tested: `no_code_location` |
| [sparta-F027](#sparta-f027) | impl_deviates | other | `sparta/propagation/talgebra.py:4-17` | not tested: `no_code_location` |
| [sparta-F028](#sparta-f028) | impl_deviates | other | `sparta/propagation/talgebra.py:20-34` | not tested: `no_code_location` |
| [sparta-F029](#sparta-f029) | impl_deviates | other | `sparta/propagation/talgebra.py:50-62` | not tested: `no_code_location` |
| [sparta-F030](#sparta-f030) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location` |
| [sparta-F031](#sparta-f031) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location` |
| [sparta-F032](#sparta-f032) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location` |
| [sparta-F033](#sparta-f033) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:44-77` | not tested: `no_code_location` |
| [sparta-F034](#sparta-f034) | impl_deviates | other | `sparta/specialization/specialize_kernel.py:44-77` | not tested: `no_code_location` |
| [sparta-F035](#sparta-f035) | impl_deviates | other | `sparta/transformation/optimize_model.py:29-54` | not tested: `no_code_location` |
| [sparta-F036](#sparta-f036) | impl_deviates | other | `sparta/transformation/transform_policy.py:56-81` | not tested: `no_code_location` |
| [sparta-F037](#sparta-f037) | impl_deviates | other | `sparta/transformation/transform_policy.py:56-81` | not tested: `no_code_location` |
| [sparta-F038](#sparta-f038) | impl_deviates | other | `sparta/transformation/transform_policy.py:56-81` | not tested: `no_code_location` |
| [sparta-F039](#sparta-f039) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-156` | not tested: `no_code_location` |
| [sparta-F040](#sparta-f040) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-156` | not tested: `no_code_location` |
| [sparta-F041](#sparta-f041) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-156` | not tested: `no_code_location` |
| [sparta-F042](#sparta-f042) | impl_deviates | other | `sparta/transformation/transform_policy.py:137-191` | not tested: `no_code_location` |
| [sparta-F043](#sparta-f043) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F044](#sparta-f044) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F045](#sparta-f045) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F046](#sparta-f046) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F047](#sparta-f047) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F048](#sparta-f048) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F049](#sparta-f049) | impl_deviates | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F050](#sparta-f050) | undisclosed | other | `sparta/common/sparsity.py:57` | not tested: `env_unavailable` |
| [sparta-F051](#sparta-f051) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F052](#sparta-f052) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F053](#sparta-f053) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F054](#sparta-f054) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F055](#sparta-f055) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F056](#sparta-f056) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F057](#sparta-f057) | not_implemented | other |  | not tested: `no_code_location` |
| [sparta-F058](#sparta-f058) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:260-299` | not tested: `no_code_location` |
| [sparta-F059](#sparta-f059) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:260-299` | not tested: `no_code_location` |
| [sparta-F060](#sparta-f060) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:260-299` | not tested: `no_code_location` |
| [sparta-F061](#sparta-f061) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:301-335` | not tested: `no_code_location` |
| [sparta-F062](#sparta-f062) | not_implemented | other | `script/figure14/search_finetune_fit_qat.py:301-335` | not tested: `no_code_location` |
| [sparta-F063](#sparta-f063) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F064](#sparta-f064) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F065](#sparta-f065) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F066](#sparta-f066) | not_implemented | other | `script/figure19/run.sh:1-7` | not tested: `no_code_location` |
| [sparta-F067](#sparta-f067) | not_implemented | other | `sparta/core/sparta.py:16-24` | not tested: `no_code_location` |
| [sparta-F068](#sparta-f068) | not_implemented | other | `sparta/propagation/talgebra.py:4-17` | not tested: `no_code_location` |
| [sparta-F069](#sparta-f069) | not_implemented | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location` |
| [sparta-F070](#sparta-f070) | not_implemented | other | `sparta/specialization/specialize_kernel.py:18-42` | not tested: `no_code_location` |
| [sparta-F071](#sparta-f071) | not_implemented | other | `sparta/specialization/specialize_kernel.py:44-77` | not tested: `no_code_location` |
| [sparta-F072](#sparta-f072) | not_implemented | other | `sparta/transformation/optimize_model.py:29-54` | not tested: `no_code_location` |
| [sparta-F073](#sparta-f073) | not_implemented | other | `sparta/transformation/optimize_model.py:29-54` | not tested: `no_code_location` |
| [sparta-F074](#sparta-f074) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F075](#sparta-f075) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F076](#sparta-f076) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F077](#sparta-f077) | not_implemented | other | `sparta/transformation/transform_policy.py:158-191` | not tested: `no_code_location` |
| [sparta-F078](#sparta-f078) | not_implemented | other | `sparta/transformation/transform_policy.py:172-191` | not tested: `no_code_location` |
| [sparta-F079](#sparta-f079) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:7-24` | not tested: `no_code_location` |
| [sparta-F080](#sparta-f080) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:7-24` | not tested: `no_code_location` |
| [sparta-F081](#sparta-f081) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:7-24` | not tested: `no_code_location` |
| [sparta-F082](#sparta-f082) | not_implemented | other | `sparta/transformation/weighted_block_cover.py:47-102` | not tested: `no_code_location` |

## sparta-F001

**When cover_sizes[(1, 1)] < ordered_pricing[0][0]: The choice of covering algorithm is driven by the caller's sparsity pattern: if the cheapest block price exceeds the (1,1) element price, the whole weighted-set-cover is skipped and the function returns `None, {(1,1)}` — i.e. the tensor is treated as fully element-wise (no block covering), which then flows into wbc_matmul setting w_tesa.block_si...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:77` in `sparta/transformation/weighted_block_cover.py::weighted_block_cover`
- condition: `cover_sizes[(1, 1)] < ordered_pricing[0][0]`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: When even the cheapest block price is worse than the element-wise price, the block cover is skipped and the whole weight becomes fine-grained (1,1), a variant switch driven by the sparsity pattern; ordered_pricing[0] on an empty list also raises…
- code snippet (`sparta/transformation/weighted_block_cover.py:77`): `if cover_sizes[1, 1] < ordered_pricing[0][0]:`

**Not tested** (`env_unavailable`): repository third_party/SparTA is not checked out

## sparta-F002

**When len(unique_block_sizes) != 1: wbc_matmul only supports a single block size for the weight tesa. If the weighted block cover (driven by the caller's sparsity pattern / TeSA values) selects more than one block size, decompose_blocked_tesas is a no-op stub (`...`) and then a bare `raise` aborts the whole transformation. So a sparsity pattern that mixes block sizes is rejected rather than hand...**

- category `docs_only`, effect `reject`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:123` in `sparta/transformation/weighted_block_cover.py::wbc_matmul`
- condition: `len(unique_block_sizes) != 1`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: wbc_matmul hits a bare raise whenever the weighted block cover picks more than one block size (including a block size plus the (1,1) leftover), so mixed-granularity sparsity patterns from the user's TeSA are rejected.
- paper/docs (paper, PDF p.7): “T 1 i , . . . ,T j i = self.WeightedBlockCover(Ti);”
- paper/docs (paper, PDF p.7): “Ttrans f ormed.Extend(T 1 i , . . . ,T j i );”
- code snippet (`sparta/transformation/weighted_block_cover.py:123`): `raise`

**Not tested** (`env_unavailable`): repository third_party/SparTA is not checked out

## sparta-F003

**论文要求 S 初始为全部节点；代码初始队列只含源/汇节点，其余节点由度数递减触发入队**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “S = Set(AllNodesOf(G));”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F004

**论文要求把全部邻居（除 N）插入 S；代码只在度数归零时入队，非全部邻居**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “S.Insert(B.Remove(N));”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F005

**论文要求直到无 TeSA 需更新；代码固定两遍、每节点一次，不检测掩码是否仍变化**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “The propagation repeats until no TeSA requires further update.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F006

**论文要求随算子类型 AND 属性类型变化；代码仅覆盖剪枝一种属性种类（量化比特未实现，见 M02-B07-R02），属性维度分派缺失**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5, text lines 46-48): “Intra-operator propagation. The propagation behavior of PropOneNode varies across different type of operators and at- tributes. In Figure 4(b), the pruned element [0,0] in tensor W3”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F007

**论文要求重复运行多次（经验 256 个随机张量）；代码单次前向，以批内方差近似重复采样，重复次数由 confidence/batch 维决定而非 256 次独立运行**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.5): “By repeating this process enough times (see §5.2)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F008

**论文返回 Iupdated∪Oupdated 的输入与输出 TeSA 更新集；代码只返回每层 weight_mask，缺输入/输出更新集**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.6): “return Iupdated , Oupdated ;”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F009

**artifact 路径无通用纳入机制。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- paper/docs (paper, PDF p.8): “SparTA’s specialization framework is general to incorporate any sparsity-aware techniques, including the off-the-shelf sparse kernel and even its dense version.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F010

**论文要求用真实数据集推理得到的算子输入输出张量；逐模块传播路径用随机张量代替真实激活**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:169-178`
- paper/docs (paper, PDF p.6, text lines 84-87): “operator’s input and output tensors, we ﬁrst perform inference on the corresponding DNN model using train/test dataset, and collect the resulting input and output tensors of that operator to construct calibration data (line 20). Next, we gradually”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F011

**论文要求对算子所有张量（输入/权重/输出）逐一评估；代码只对 weight 张量做位宽搜索，input/output 未评估**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:301-335`
- paper/docs (paper, PDF p.6): “The process repeats for other tensors in the operator, until all tensors are evaluated.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F012

**论文要求精度下降小于预定义阈值（1%）才接受；代码用 best_acc<original_acc 即任何下降都拒绝，无 1% 阈值**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:496-538`
- paper/docs (paper, PDF p.6, text lines 94-97): “operator after lowering the precision. If the drop of model ac- curacy is smaller than a predeﬁned threshold (e.g., 1% in our experiment), the new quantization attribute of that operator is accepted (line 22). The process repeats for other tensors in”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F013

**论文要求拓扑序并缓存激活；代码按模块注册顺序遍历且无激活缓存**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:496-538`
- paper/docs (paper, PDF p.6): “SparTA works through all the operators in a DNN model in a topological order and caches the activations computed in earlier quantization propagations.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F014

**论文要求同时更新 S 与 Supdated；代码只更新全局位设置，无 Supdated 累积**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:571-664`
- condition: `weight_bits in range(weight_upbound_bits-1, downbound_bit-1, -1)`
- paper/docs (paper, PDF p.6, text lines 16-18): “23 if Tupdated != T then 24 S.Update(Tupdated ); 25 Supdated .Update(Tupdated );”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F015

**论文以 Tupdated==T 跳过；代码以精度下降 break，语义不同**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:571-664`
- paper/docs (paper, PDF p.6): “if Tupdated != T then”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F016

**论文报告第二 sub-Matmul 的具体残余稀疏度；实验路径无该测量/输出，且底层分派规则与数值趋势不符。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure16/a100/sparta.cu:118-140`
- paper/docs (paper, PDF p.13): “The other sub-Matmul has 12.5%, 8%, 4.5%, 2.0%, 0.5% sparsity ratio respectively.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F017

**实验路径的第二部分内核依赖为 Sputnik，而非 SparTA 专用稀疏内核。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure16/a100/sparta.cu:266-311`
- paper/docs (paper, PDF p.13, text lines 83-85): “tains the elements not included in the ﬁrst one. The ﬁrst one uses Sparse Tensor Cores, while the other uses our specialized sparse kernel. To evaluate the transformation, we randomly”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F018

**artifact 脚本无反馈驱动的稀疏属性更新步骤。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4): “Given the feedback, model designers may further update the sparsity attributes in some tensors”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F019

**artifact 无编译-测量迭代回路。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4): “repeat this process iteratively to ﬁnd the best tradeoff”
- paper/docs (paper, PDF p.4): “Thus SparTA enables a feedback loop, facilitating the innovation in model sparsity.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F020

**加速来自 NNI ModelSpeedup 而非 SparTA 稀疏 kernel。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14): “With SparTA, model ﬁne-tuning can be accelerated.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F021

**artifact 无目标稀疏度终止条件。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14, text lines 71-74): “sity pattern iteratively [58, 86]. In each iteration, the algo- rithm “sparsiﬁes” a proportion of the model (e.g., 30%) and ﬁne-tunes it. It repeats the iteration until achieving the tar- geted sparsity (e.g., 90%). In this process, model ﬁne-tuning”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F022

**论文要求传播为 Rammer 内专用编译 pass；实验路径在编译前以 Python 脚本离线传播，编译器 pass 列表无传播 pass。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/init_checkpoints.sh:1-34`
- paper/docs (paper, PDF p.9): “We implemented sparsity attribute propagation as a dedicated compilation pass over Rammer.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F023

**论文要求复现 Figure 8-11、14-18、20；实际覆盖 8-11、13-15、17、19 与 table3，缺 figure18、figure20，且 2080Ti 路径无 figure16。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `script/run_all_2080ti.sh:1-57`
- paper/docs (paper, PDF p.21, text lines 27-30): “In this artifact, we will reproduce the Figure 8-11, 14-18, 20 on NVIDIA 2080Ti and A100. Each ﬁgure has a shell script to reproduce and visualize the experimental results automati- cally. In addition, there are many baselines compared in our”
- paper/docs (paper, PDF p.21, text lines 50-56): “Environment setup To set up the environment, please ﬁrst clone the code and build the docker image based the Docker- ﬁle we provided. Second, please start a docker instance and install the SparTA in the python environment. Finally, please run the init_env.sh to initialize the environment variables …”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F024

**论文要求 2 字节位域属性；artifact 路径以文本配置+按位宽分支替代，未实现 7/4/5 位布局**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/artifact_specialization/generate_code.py:58-82`
- condition: `bit == 32 or bit == 8`
- paper/docs (paper, PDF p.9): “Each TeSA element has a two-byte attribute: 7 bits record the bit width of the element, 4 bits specify the element’s data format”
- paper/docs (paper, PDF p.9, text lines 7-9): “TeSA element has a two-byte attribute: 7 bits record the bit width of the element, 4 bits specify the element’s data format (e.g., unsigned int, ﬂoat32, bﬂoat16), and the rest 5 bits are”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F025

**论文要求 4/8 表示 uint4/uint8；artifact 仅实现 int8 路径，无符号量化未体现**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/artifact_specialization/generate_code.py:58-82`
- condition: `bit == 4 or bit == 8`
- paper/docs (paper, PDF p.4, text lines 114-116): “Figure 3: An example of TeSA. Sparsity Attribute denotes the sparsity pattern, including quantization (4 meansuint4, 8 means uint8) and pruning (0 means the element is pruned).”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F026

**论文要求 ×、÷、x^y 三类算子均满足任一 φ 即 φ；代码只提供 × 的 and 规则，÷ 与 x^y 无任何规则**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:4-17`
- paper/docs (paper, PDF p.5): “((x = φ)∨ (y = φ))→ (z = φ)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F027

**论文要求 ×/÷/x^y 三者均满足 α∧α→α；代码仅实现 ×**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:4-17`
- paper/docs (paper, PDF p.5): “((x = α)∧ (y = α))→ (z = α)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F028

**论文要求对逐元素可表达算子按计算流计算输出 TeSA；代码只对 matmul 实现，一元与 ÷/x^y 算子无对应计算流**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:20-34`
- paper/docs (paper, PDF p.5): “(x = φ)→ (y = φ)”
- paper/docs (paper, PDF p.5): “(x = α)→ (y = α)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F029

**论文要求三条导数公式（含 gB=gY）；代码仅实现两条，偏置项缺失。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/propagation/talgebra.py:50-62`
- paper/docs (paper, PDF p.6): “Similarly, the TeSA of B and X can be inferred from Y using gB = gY and gX = AT× gY, respectively.”
- paper/docs (paper, PDF p.6): “It is obvious from gB = gY that B has the same TeSA as Y .”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F030

**论文允许输入分解；artifact 路径只处理单输入 TeSA**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- condition: `len(in_tesa) > 1 or len(out_t_tesa) > 1`
- paper/docs (paper, PDF p.7): “Ti = P.TransformTeSA(Ii);”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F031

**输出不分解**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- condition: `len(weight_tesa) > 1`
- paper/docs (paper, PDF p.7): “To = P.TransformTeSA(O);”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F032

**论文要求 m+1 维笛卡尔积；代码仅权重维枚举，实际 1 维**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- condition: `len(in_tesa) == 1 and len(out_t_tesa) == 1 and len(weight_tesa) >= 1`
- paper/docs (paper, PDF p.7): “foreach⟨t1, . . . ,tm,to⟩∈ T1×···× Tm× To do”
- paper/docs (paper, PDF p.7, text lines 25-29): “transformed to one or multiple TeSAs using TransformTeSA. Correspondingly, the operator is transformed to|To| ∏m i=1|Ti| sub-operators, which are the Cartesian product of those de- composed TeSAs. The sub-operator usually has the same”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F033

**论文要求位宽提示指导硬件指令选择（DP4A/wmma）；代码按位宽选不同 CUDA 模板，但模板选择处无基于位宽的指令级特化分支，32bit 分支直接走 cublas/稠密模板（artifact 范围：位宽→模板分派存在，位宽→硬件指令（DP4A）选择不存在）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:44-77`
- condition: `n_bits == 32`
- paper/docs (paper, PDF p.8): “the bit-width of an operator suggests whether to leverage a speciﬁc hardware instruction (e.g., DP4A)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F034

**artifact 路径无 dismantle 展开步骤，仅消费预生成 kernel。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:44-77`
- condition: `dismantle != -1`
- paper/docs (paper, PDF p.8): “When dismantle is applied on a loop, this loop and all its outer loops are unrolled and specialized with the given sparsity attribute.”
- paper/docs (paper, PDF p.8): “we introduce a new schedule primitive dismantle that jointly performs loop unrolling and DCE.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F035

**执行计划未被重写**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/optimize_model.py:29-54`
- condition: `not is_fast_pass(post_sparsity)`
- paper/docs (paper, PDF p.6): “Correspondingly, SparTA rewrites the execution plan of the associated operator to accommodate”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F036

**论文要求每次调用产生新选项并初始化空列表；代码桩未实现且原地修改输入**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:56-81`
- paper/docs (paper, PDF p.7): “/* return a new transformation option per run */”
- paper/docs (paper, PDF p.7): “Ttrans f ormed = [];”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F037

**论文要求返回累积分解列表；代码无该累积返回**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:56-81`
- condition: `len(unique_block_sizes) > 1`
- paper/docs (paper, PDF p.7): “return Ttrans f ormed;”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F038

**论文要求对每个 BitRounding 结果 extend 其 WBC 输出；代码 TransformTeSA 未实现该 extend，实际路径仅收集未使用的 transform_options**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:56-81`
- paper/docs (paper, PDF p.7, text lines 86-92): “52 foreach i∈ 1, . . . ,k do 53 T 1 i , . . . ,T j i = self.WeightedBlockCover(Ti); 54 Ttrans f ormed.Extend(T 1 i , . . . ,T j i );”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F039

**论文要求按采样位选项产生 k 个结果；代码无采样且限制最多 2 种位宽**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-156`
- condition: `len(aligned_bits) > 2`
- paper/docs (paper, PDF p.7): “T1, . . . ,Tk = self.BitRounding(T , self.SampleBitOption());”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F040

**论文要求先经 SampleBitOption 采样一个位选项再传给 BitRounding；代码无采样步骤，bit_align 直接使用 hardware_bit_precisions() 全集合（E4）并返回固定候选，位选项非采样所得。（artifact 范围：无 SampleBitOption 采样，位选项由硬件位宽集合直接决定。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-156`
- paper/docs (paper, PDF p.7): “T1, . . . ,Tk = self.BitRounding(T , self.SampleBitOption());”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F041

**论文要求每次运行返回新的（可不同的）变换选项；代码每次返回相同候选集合，无“per run 新选项”机制。（artifact 范围：。）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-156`
- paper/docs (paper, PDF p.7): “/* return a new transformation option per run */”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F042

**论文要求每个操作数 TeSA 各自带块大小；代码仅权重 TeSA 获得 block_size，输入/输出 TeSA 的 block_size 保持 None 且不被消费（artifact 范围：仅权重侧 hints 完整）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:137-191`
- condition: `in_tesa.block_size is not None or out_tesa.block_size is not None`
- paper/docs (paper, PDF p.8): “Specialization hints: T: {Bit: 32, Block: 2x2}, W: {Bit: 32, Block: 2x2}”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F043

**论文要求 RecordPerf 记录每次 profile；artifact 路径计算后未记录**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “P.RecordPerf(G=ComposeToGraph(S), Proﬁle(G));”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F044

**论文要求返回策略选出的最佳变换；代码无选择逻辑，返回 None**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “return P.BestTransformation();”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F045

**论文要求先 SampleBitOption 采样再传 BitRounding；代码以固定硬件位宽集合枚举替代采样（artifact 范围：无 SampleBitOption 采样触发）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- condition: `isinstance(module_sparsity.module_obj, nn.Linear)`
- paper/docs (paper, PDF p.7): “T1, . . . ,Tk = self.BitRounding(T , self.SampleBitOption());”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F046

**论文要求返回变换后 TeSA 列表；代码对应函数为桩，实际入口返回 None kernel 列表，未返回变换 TeSA 列表**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “return Ttrans f ormed;”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F047

**论文要求调用方迭代多个方案并选满足者；代码迭代循环被注释，未执行方案搜索**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “Given a TeSA, TransformTeSA may have multiple transfor- mation plans. The process iterates over each plan to ﬁnd the satisﬁed one (line 38).”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F048

**论文要求每次调用返回一个新选项；代码返回固定单元素列表或一次性全部结果**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “/* return a new transformation option per run */”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F049

**论文声称框架可纳入任意 sparsity-aware 技术；实验路径既未执行 specialization，其可达代码也只有固定模板枚举，无外部内核纳入能力。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8): “SparTA’s specialization framework is general to incorporate any sparsity-aware techniques, including the off-the-shelf sparse kernel and even its dense version.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F050

**When info.module_name in self.modules_info: When a module name is already present, the merge branch is an empty ellipsis body, so the new SparseModuleInfo (and its updated TeSA attributes) is silently discarded and the earlier state is kept. The mechanism therefore depends on earlier update() calls and ignores later sparsity info for the same module. (sparta/common/sparsity.py:57)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/common/sparsity.py:57` in `sparta/common/sparsity.py::ModelSparsityInfo.update`
- condition: `info.module_name in self.modules_info`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: The merge branch is a stub, but the only caller, extract_sparsity, iterates model.named_modules(), whose names are unique, so a duplicate module name never reaches it.
- code snippet (`sparta/common/sparsity.py:57`): `if info.module_name in self.modules_info:`

**Not tested** (`env_unavailable`): repository third_party/SparTA is not checked out

## sparta-F051

**论文要求量化比特收敛规则；代码只处理剪枝掩码，无量化属性种类**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.5): “For quantization, the attribute will be converged to the fewest quantization bits (or 0-bit, i.e., being pruned).”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F052

**论文要求分发前初始化 Iupdated/Oupdated 空集；代码无规则分发，仅建空字典收集结果**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “Iupdated = Oupdated = /0;”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F053

**论文要求 foreach RegisteredPropRule 调用规则；代码为固定两个硬编码推断函数，无注册表迭代**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “foreach RegisteredPropRule do”
- paper/docs (paper, PDF p.6): “Iproped ,Oproped = RegisteredPropRule(N, Is, Os);”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F054

**论文要求把规则返回的 Iproped/Oproped 合并进节点 Is/Os；代码无规则返回值，直接由硬编码推断写 masks**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “Is.Update(Iproped ); Os.Update(Oproped );”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F055

**论文要求累积每条规则更新到 Iupdated/Oupdated；代码为逐层快照收集，无规则更新累积**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.6): “Iupdated .Update(Iproped );”
- paper/docs (paper, PDF p.6): “Oupdated .Update(Oproped );”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F056

**artifact 路径无单块回退到通用稀疏/dense kernel 的分派。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.8, text lines 117-122): “A specialization hint could also specify the block size equal to the tensor’s shape (i.e., one block covers the whole tensor). In this case, SparTA can directly use the existing state-of-the- art general sparse kernel implementation (e.g., cuSPARSE [3], taco [53]) or even use the dense kernel imple…”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F057

**artifact 路径无该搜索步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- paper/docs (paper, PDF p.8): “It searches from the outermost loop until the level (say l) of inner loop body aligns with the block size.”
- paper/docs (paper, PDF p.8): “dismantle is applied on the third loop, thus the top three loops are unrolled, generating eight small Matmuls (i.e., [2,2]x[2,2]).”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F058

**论文要求从最近缓存激活部分推理；代码无缓存也无部分推理**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:260-299`
- paper/docs (paper, PDF p.6): “Collecting an operator’s calibration data only needs partial inference from the nearest cached activations to this operator.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F059

**无注册调用**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:260-299`
- paper/docs (paper, PDF p.6): “RegisterPropRule(QuantizationPropRule);”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F060

**论文要求 La 输出激活部分推理得 Lb 校准数据；代码无此复用**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:260-299`
- paper/docs (paper, PDF p.6): “consider a sequential model with two layers La and Lb. The propagation on La has collected its output activations in its calibration data. When working on Lb, its calibration data can be collected by doing partial inference from the collected output activations of La.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F061

**无 TeSA 集合初始化**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:301-335`
- paper/docs (paper, PDF p.6): “Supdated = /0; S = ( Is∪ Os );”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F062

**无 SplitToIsOs 返回**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure14/search_finetune_fit_qat.py:301-335`
- paper/docs (paper, PDF p.6): “return SplitToIsOs(Supdated );”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F063

**artifact 路径无编译后延迟/内存测量步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4, text lines 67-69): “Finally, with the ﬁnal compiled code, model designers can proﬁle the DNN model to obtain authentic performance met- rics, including memory consumption and inference latency.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F064

**artifact 路径无真实延迟过滤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14, text lines 46-49): “in Figure 19. Our baseline uses FLOPS as the metric to ﬁlter out the disqualiﬁed models: the model whose FLOPS is larger than 70% of the original FLOPS. In contrast, SparTA uses the real latency to ﬁlter models. The result is shown in Figure 19.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F065

**artifact 无编译迭代。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.4): “This process may be iterated for further improvement.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F066

**artifact 无 FLOPs 过滤基线。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `script/figure19/run.sh:1-7`
- paper/docs (paper, PDF p.14): “Our baseline uses FLOPS as the metric to ﬁlter out the disqualiﬁed models: the model whose FLOPS is larger than 70% of the original FLOPS.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F067

**论文要求对每个 (sub)operator 执行量化特化；artifact 链中特化调用被注释、重建为直通，未执行任何循环级特化。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/core/sparta.py:16-24`
- condition: `backend == 'pytorch'`
- paper/docs (paper, PDF p.8, text lines 125-127): “Specializing operators with quantization attributes also works on the multi-level loops, but starting from the inner- most loop. SparTA picks a proper hardware instruction based”
- paper/docs (paper, PDF p.8): “and then replace the rearranged loop body with the instruction”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F068

**论文要求可注册新算子规则；代码无注册机制，新增算子需改源码**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/propagation/talgebra.py:4-17`
- paper/docs (paper, PDF p.5): “Note that Table 2 can be extended to support new operators.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F069

**无 TransformOp 级 S 初始化**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- paper/docs (paper, PDF p.7): “S = [];”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F070

**论文要求组合为图 G；代码无图构造步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:18-42`
- paper/docs (paper, PDF p.7): “P.RecordPerf(G=ComposeToGraph(S), Proﬁle(G));”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F071

**依赖存在但未被该判定消费，属未接线而非实现**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/specialization/specialize_kernel.py:44-77`
- condition: `block_size is not None and block_size != 1`
- paper/docs (paper, PDF p.8): “A specialization hint could also specify the block size equal to the tensor’s shape (i.e., one block covers the whole tensor).”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F072

**论文要求特化 tiling 对齐指令形状；artifact 入口链无 tiling 生成步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/optimize_model.py:29-54`
- condition: `backend == 'pytorch'`
- paper/docs (paper, PDF p.8, text lines 129-131): “for 8bit, wmma for 4bit. The specialized tiling of the innermost loop(s) is then aligned to the computation shape of the in- struction. For example, one supported computation shape of”
- paper/docs (paper, PDF p.8): “one supported computation shape of wmma is the Matmul [16,16]x[16,16]. To specialize for this instruction, the tiling should rearrange the innermost loop body to align with the shape”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F073

**论文要求 DP4A 重排+替换；artifact 入口链无此步骤。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/optimize_model.py:29-54`
- condition: `backend == 'pytorch'`
- paper/docs (paper, PDF p.8): “The tiling for the instruction DP4A with a shape [1,4]x[4,1] can be done similarly.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F074

**论文要求 while 搜索；artifact 路径仅单遍枚举**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.7): “while P.HasBudget() and P.PerfNotSatisﬁed() do”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F075

**论文要求按 TeSA 位宽选指令；artifact 链未调用特化，位宽选择步骤不存在。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8): “SparTA picks a proper hardware instruction based on the bit-width denoted in TeSA, e.g., DP4A [13] or wmma [5] for 8bit, wmma for 4bit.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F076

**实验路径未执行 specialization 内核选择，且无 block==shape→通用稀疏内核的代码路径；依赖存在不等于执行路径存在。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8, text lines 117-121): “A specialization hint could also specify the block size equal to the tensor’s shape (i.e., one block covers the whole tensor). In this case, SparTA can directly use the existing state-of-the- art general sparse kernel implementation (e.g., cuSPARSE [3], taco [53]) or even use the dense kernel imple…”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F077

**实验路径未运行内核选择，且无 block==shape 的稠密回退分支。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:158-191`
- paper/docs (paper, PDF p.8): “or even use the dense kernel implementation if it perform better.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F078

**论文要求从枚举结果选最佳；代码无候选集合，择优逻辑被注释**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/transform_policy.py:172-191`
- paper/docs (paper, PDF p.9): “and pick the best one”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F079

**artifact 路径无 13 块大小评估入口**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:7-24`
- paper/docs (paper, PDF p.9, text lines 19-21): “weight of different block sizes. Speciﬁcally, we implemented a kernel template for block sparsity, and evaluated 13 dif- ferent block sizes on that template. The overhead of each”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F080

**artifact 路径无零稀疏延迟测量入口**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:7-24`
- paper/docs (paper, PDF p.9): “The overhead of each block size is proﬁled by measuring the latency of the kernel with zero sparsity”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F081

**论文要求 latency/块数；代码无该计算，E2 除法语义不同（按覆盖元素数分摊）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:7-24`
- paper/docs (paper, PDF p.9): “dividing the latency with the number of blocks”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## sparta-F082

**论文要求过稀疏时枚举所有块大小组合并选最优；代码无枚举、无最优选择、无触发条件**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `sparta/transformation/weighted_block_cover.py:47-102`
- paper/docs (paper, PDF p.9): “When an operator is too sparse to saturate available cores, the weights may become less accurate. In such cases, we enumerate all the combinations of block sizes to run the weighted block cover algorithm and pick the best one.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

