# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；sparta）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/sparta/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **106 条 limitation**（代码侧 + 论文侧），去重后是 **82 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/sparta/limitations_for_tests.json`。

## 1. 两侧的 limitation 有什么不同

| | 代码侧（Wanting，步骤 2 + 3b） | 论文侧（Zhaopeng，步骤 1 + 3a） |
|---|---|---|
| 从哪来 | 从入口函数静态分析 + LLM 找出的检查、分支、回退 | 逐条读论文的机制描述，再去代码里找对应实现 |
| 说的是什么 | “输入满足条件 X 时，代码会抛异常 / 换路径 / 改变状态” | “论文说要做 A，代码做的是 B（或没做）” |
| 条件 | 有，是代码里的 Python 表达式（`condition.expr` + `path_prefix`） | 原始记录没有；步骤 4 由 LLM 写出，用代码核对过 |
| 后果（effect_type） | reject / path_change / state / other …… | 几乎全是 other：只做了静态判断，后果未证实 |
| 证据 | 代码位置（单行）+ 3b 在论文 / README / docstring 里找到的原文 | 论文原文 + 代码位置（常是一段行范围） |
| ID 形式 | `CL-X###`（路线 A 静态）、`CL-B###`（路线 B 加 LLM） | `<论文>-gap-<机制>-<行为>`，如 `infinigen-gap-M01-B03` |
| 类别 | undisclosed / contradicts_docs / stated_differently / docs_only / paper_stated | impl_deviates / not_implemented |
| 典型 witness | solved：z3 给出边界两侧两个具体点 | always：每次走到引用代码都会出现 |
| 适合的测试 | 异常断言、路径打桩，比较好写 | 和论文公式做 differential / metamorphic 对比，比较难写 |

两侧说同一件事、经 LLM 判断合并后的 Finding，`limitations` 里两侧的记录都有。

## 2. 数量

| 论文 | 代码侧 | 论文侧 | 两侧合并 | 合计 |
|---|---|---|---|---|
| sparta | 2 | 79 | 1 | 82 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 47 | 32 | 79 |
| 两侧合并 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 |

| 类别 | 意思 |
|---|---|
| `undisclosed` | 代码有这个限制，用户能读到的地方都没写（核心发现） |
| `contradicts_docs` | 文档写的和代码行为相反 |
| `stated_differently` | 文档写了，但边界不同或说得更弱（如“只测过 bf16”vs 代码强制 bf16） |
| `docs_only` | README / 公开 docstring 写了，论文没写 |
| `paper_stated` | 论文写了，边界和代码一致 |
| `impl_deviates` | 论文描述了，代码实现得不一样 |
| `not_implemented` | 论文描述了，代码里没有 |

按 priority（1 = 先测）：

| 来源 | p1 | p2 | p3 | 合计 |
|---|---|---|---|---|
| 代码侧 | 0 | 1 | 1 | 2 |
| 论文侧 | 0 | 47 | 32 | 79 |
| 两侧合并 | 0 | 1 | 0 | 1 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 2 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 79 | 79 |
| 两侧合并 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 论文侧 | 15 | 0 | 2 | 57 | 0 | 0 | 0 | 5 | 79 |
| 两侧合并 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 1 | 1 | 0 | 0 | 2 |
| 论文侧 | 0 | 0 | 0 | 79 | 79 |
| 两侧合并 | 1 | 0 | 0 | 0 | 1 |

## 3. 一条记录里有什么

`limitations_for_tests.json` 的结构是 `{schema_version, witness_format, rules, note, findings: [...]}`。`findings` 里每条记录的字段如下：

| 字段 | 内容 | 测试时怎么用 |
|---|---|---|
| `finding_id` | `<论文>-F###`，在一篇论文内按 priority 排序 | TestCase.finding_id 填它 |
| `category` | 7 类之一，见上表 | 决定这条测的是“没写”还是“和论文不同” |
| `priority` | 1 / 2 / 3 | 先测 1 |
| `effect_type` | reject / path_change / state / … | 决定 oracle，见第 5 节 |
| `summary` | 一句话：什么条件下会怎样，附位置 | 给人看 |
| `witness_hint` | 触发点、对照点和各名字的含义，见第 4 节 | 构造测试输入 |
| `scope_status` | 是否在论文声明的范围内；目前几乎都是 unknown（论文侧参数映射很少） | out_of_scope 的不计入主结果 |
| `review` / `review_note` | worth_testing / real_but_minor / wrong / unreviewed，以及是谁审的、理由 | wrong 的可以跳过 |
| `rationale` | 分类依据、合并了谁、priority 的理由，以及判为“相关但不同”的其他 Finding | 查原因 |
| `limitation_ids` / `limitations` | 背后的完整 Limitation 记录（两侧都可能有） | 看原始条件、论文原文和代码位置 |
| `verification_ids` / `verifications` | 代码侧的 3b 结果：在哪里找到了说明、原文 | 判断“文档到底怎么写的” |
| `confidence` | 目前全部是 llm_assisted | — |

注意：论文侧原始记录的 `effect_text` 有一部分写的是“同上……”，指的是 3a 同一条记录的 local_entry 描述。Finding 的 `summary` 已经展开，`limitations` 里保留原样。

## 4. witness_hint 怎么读

- `trigger`：满足条件的点，会走限制分支；`contrast`：离 trigger 最近、但不走限制分支的点。两者都满足 `path_prefix`。
- `atoms` 说明每个名字该怎么造：`input` 直接给值；`local` 是局部变量，按 `aliases` 里的表达式造（如 `q_len` = `q.shape[1]`）；`derived` 要构造出这个值（如造一个第 1 维为 2 的张量）；`predicate` 是真假值，要 mock 或选输入（如 `is_flash_attn_2_available()`）；`category` 是字符串或枚举，`{"not_in": [...]}` 表示“列出的值以外的任意一个”。
- `kind: event_sequence`（effect=state）：先通过前几次调用把状态弄成 trigger，再做检查。
- 状态：

| status | 意思 | 怎么测 |
|---|---|---|
| solved | 两个点都有 | 直接用 trigger / contrast |
| solved_contrast_outside_scope | contrast 只能取在论文 scope 外 | 同上，注意 contrast 不在论文范围内 |
| trigger_only | 条件在路径上总是成立，没有对照点 | 只用 trigger |
| always | 论文侧：每次走到引用代码都会出现 | 任意走到 `code_locations` 的输入 |
| infeasible | 条件和路径前缀矛盾，从入口很可能走不到 | 已降为 p3；可能是误报 |
| no_condition | 论文侧：没有可用条件 | 读 `note` 和 summary，人工判断 |
| untranslatable / unknown | 条件翻译不了 / 求解超时 | 读 condition 原文 |

已知不足：
- `path_prefix` 混着调用链上各层函数的条件。同一个名字在调用者和被调用者里可能不是同一个东西（例如两层里的 `q`）。所以别名只在单层时参与求解，其余只列在 `aliases_not_applied` 里。
- 论文侧条件由 LLM 写出，只核对过“名字都出现在引用的代码里”，**语义不一定对**，要当提示用。
- 所有值都没有实际执行验证过。

## 5. 按 effect 选 oracle（建议）

| effect_type | 意思 | 建议的 oracle |
|---|---|---|
| reject | 抛异常 / 断言失败 | trigger 上断言抛出指定异常，contrast 上不抛 |
| path_change | 换了一条执行路径（回退、换 kernel、换策略） | path hook：在两条路径的入口打桩，trigger 走限制分支、contrast 不走 |
| accuracy | 结果精度变差 | differential：和参考实现比，trigger 上误差超过阈值 |
| state | 依赖前几次调用留下的状态 | event_sequence：先按顺序调用把状态弄成 trigger，再检查 |
| resource / performance | 内存 / 时间 | resource：测量，对比 contrast |
| other（论文侧几乎全是） | 实现和论文描述不同，没有确定的运行时后果 | witness 为 always 时：走到引用代码的任一输入，和论文公式 / 描述做 differential 或 metamorphic 对比；3a 只做了静态判断，后果未证实 |

## 6. 典型例子

每个例子是一条 Finding 的精简版，长字段已截断；完整内容在 json 里。例子是按规则自动挑的第一条，不是挑好看的。“论文侧 · LLM 写出条件”那条正好说明了它的局限：条件在形式上能解，但不一定抓住了论文差异的本质，所以论文侧条件只当提示用。

### 两侧合并：`sparta-F002`

```json
{
 "finding_id": "sparta-F002",
 "category": "docs_only",
 "priority": 2,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "worth_testing",
 "summary": "When len(unique_block_sizes) != 1: wbc_matmul only supports a single block size for the weight tesa. If the weighted block cover (driven by the caller's sparsity pattern / TeSA values) selects more than one block size, decompose_blocked_tesas is a no-op stub (`...`) and then a bare `raise` aborts the whole transformation. So a sparsity pattern that mixes block sizes is rejected rather than hand...",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "len(unique_block_sizes) != 1",
  "path_prefix": [
   "for w_tesa in w_tesas"
  ],
  "trigger": {
   "len(unique_block_sizes)": 2
  },
  "contrast": {
   "len(unique_block_sizes)": 1
  },
  "atoms": {
   "len(unique_block_sizes)": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "note": "local definitions in the checked function, not used by the solver because the path prefix also holds caller conditions",
  "location": "sparta/transformation/weighted_block_cover.py:123"
 },
 "limitations": [
  {
   "limitation_id": "CL-B003",
   "origin": "code",
   "condition_text": "len(unique_block_sizes) != 1",
   "effect_text": "wbc_matmul only supports a single block size for the weight tesa. If the weighted block cover (driven by the caller's sparsity pattern / TeSA values) selects m…",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:123-123"
   ],
   "paper_quote": null
  },
  {
   "limitation_id": "sparta-gap-M08-A03",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary:transform_policy.py + weighted_block_cover.py + sparta/specialization/specialize_kernel.py（specialize_matmul 代码生成与调优计时）…",
   "effect_text": "同上",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:104-144",
    "sparta/transformation/weighted_block_cover.py:47-102"
   ],
   "paper_quote": "T 1 i , . . . ,T j i = self.WeightedBlockCover(Ti);"
  },
  {
   "limitation_id": "sparta-gap-M09-A12",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary 变换路径 + sparta/specialization/specialize_kernel.py matmul_kernel_init/codegen（消费 block_size/n_bits 提示）；nni/nnfusion/tvm …",
   "effect_text": "同上",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:104-144",
    "sparta/specialization/specialize_kernel.py:44-77"
   ],
   "paper_quote": "64 return DecomposedTeSAs(T , Bchosen);"
  },
  {
   "limitation_id": "sparta-gap-M11-B01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 primary 仓编译/实验路径 sparta/core/sparta.py→optimize_and_rebuild→TransformPolicy.transform_module→transform_matmul→wbc_matmuls→we…",
   "effect_text": "同上：多块大小覆盖在 artifact 路径不可完成",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:104-123",
    "sparta/transformation/weighted_block_cover.py:125-144",
    "sparta/transformation/optimize_model.py:29-54"
   ],
   "paper_quote": "For each TeSA returned by BitRounding, function WeightedBlockCover chooses one or multiple proper block sizes to cover the non-pruned eleme…"
  },
  {
   "limitation_id": "sparta-gap-M11-B09",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 primary 仓编译/实验路径 sparta/core/sparta.py→optimize_and_rebuild→TransformPolicy.transform_module→transform_matmul→wbc_matmuls→we…",
   "effect_text": "同上",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:104-123",
    "sparta/transformation/weighted_block_cover.py:125-144",
    "sparta/transformation/optimize_model.py:29-54"
   ],
   "paper_quote": "return DecomposedTeSAs(T , Bchosen);"
  },
  {
   "limitation_id": "sparta-gap-M11-A01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 primary 仓编译/实验路径 sparta/core/sparta.py→optimize_and_rebuild→TransformPolicy.transform_module→transform_matmul→wbc_matmuls→we…",
   "effect_text": "同上",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:104-123",
    "sparta/transformation/optimize_model.py:29-54"
   ],
   "paper_quote": "WeightedBlockCover chooses one or multiple proper block sizes to cover the non-pruned elements"
  },
  {
   "limitation_id": "sparta-gap-M12-B05-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary artifact 路径：script/ 实验脚本（figure10/11 的 kernel cfg 与模板）+ sparta/specialization 模板与 specialize_kernel.py；Dockerfile 声明的 n…",
   "effect_text": "同上",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:107-123",
    "sparta/transformation/weighted_block_cover.py:125-144",
    "sparta/transformation/transform_policy.py:172-191"
   ],
   "paper_quote": "When an operator is too sparse to saturate available cores, the weights may become less accurate. In such cases, we enumerate all the combi…"
  },
  {
   "limitation_id": "sparta-gap-M12-A01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary artifact 路径：script/ 实验脚本（figure10/11 的 kernel cfg 与模板）+ sparta/specialization 模板与 specialize_kernel.py；Dockerfile 声明的 n…",
   "effect_text": "同上",
   "code_evidence": [
    "sparta/transformation/weighted_block_cover.py:7-24",
    "sparta/transformation/weighted_block_cover.py:125-144"
   ],
   "paper_quote": "When an operator is too sparse to saturate available cores, the weights may become less accurate"
  }
 ],
 "verifications": [
  {
   "result": "found",
   "documented_in": [
    "code_comment",
    "docstring"
   ],
   "quote": "TODO: support more than one block size"
  }
 ],
 "rationale": "3b: found in code_comment, docstring; merged (LLM: same issue): sparta-gap-M08-A03, sparta-gap-M09-A12, sparta-gap-M11-B01, sparta-gap-M11-B09, sparta-gap-M11-A01, sparta-gap-M12-B05-R01, sparta-gap-M12-A01; paper side also reports: impl_deviates, not_implemented; priority 2: impl_deviates; related…"
}
```

### 论文侧 · impl_deviates · always：`sparta-F007`

```json
{
 "finding_id": "sparta-F007",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求重复运行多次（经验 256 个随机张量）；代码单次前向，以批内方差近似重复采样，重复次数由 confidence/batch 维决定而非 256 次独立运行",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The code always performs a single forward pass and approximates repeated sampling via batch/confidence variance…"
 },
 "limitations": [
  {
   "limitation_id": "sparta-gap-M04-B04-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: nni@8c656fb 的 nni/compression/pytorch/speedup/infer_mask.py（AutoMaskInference，ModelSpeedup 掩码推断路径，含 randomize_tensor/apply_mask…",
   "effect_text": "论文要求重复运行多次（经验 256 个随机张量）；代码单次前向，以批内方差近似重复采样，重复次数由 confidence/batch 维决定而非 256 次独立运行",
   "code_evidence": [],
   "paper_quote": "By repeating this process enough times (see §5.2)"
  },
  {
   "limitation_id": "sparta-gap-M04-A01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: nni@8c656fb 的 nni/compression/pytorch/speedup/infer_mask.py（AutoMaskInference，ModelSpeedup 掩码推断路径，含 randomize_tensor/apply_mask…",
   "effect_text": "论文经验值 256 次随机采样；代码以一次批内统计替代，采样数由 confidence 与输入 batch 维决定，未固定为 256",
   "code_evidence": [],
   "paper_quote": "By repeating this process enough times (see §5.2)"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; merged (LLM: same issue): sparta-gap-M04-A01; priority 2: impl_deviates"
}
```

### 论文侧 · LLM 写出条件并求解：`sparta-F024`

```json
{
 "finding_id": "sparta-F024",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求 2 字节位域属性；artifact 路径以文本配置+按位宽分支替代，未实现 7/4/5 位布局",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "bit == 32 or bit == 8",
  "path_prefix": [
   "weight_tesa.block_size is not None"
  ],
  "trigger": {
   "bit": 8,
   "weight_tesa.block_size is None": false
  },
  "contrast": {
   "bit": 9,
   "weight_tesa.block_size is None": false
  },
  "atoms": {
   "bit": {
    "kind": "input",
    "sort": "int"
   },
   "weight_tesa.block_size is None": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "code_locations": [
   "sparta/artifact_specialization/generate_code.py:58-82"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "location": "sparta/artifact_specialization/generate_code.py:58-82"
 },
 "limitations": [
  {
   "limitation_id": "sparta-gap-M01-B02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary:sparta/artifact_specialization/generate_code.py（bcsr_generate 消费 TeSA）+ nnfusion:src/nnfusion/engine/pass/graph/spargen…",
   "effect_text": "论文要求 2 字节位域属性；artifact 路径以文本配置+按位宽分支替代，未实现 7/4/5 位布局",
   "code_evidence": [
    "sparta/artifact_specialization/generate_code.py:58-82"
   ],
   "paper_quote": "Each TeSA element has a two-byte attribute: 7 bits record the bit width of the element, 4 bits specify the element’s data format"
  },
  {
   "limitation_id": "sparta-gap-M01-A04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary:sparta/artifact_specialization/generate_code.py（bcsr_generate 消费 TeSA）+ nnfusion:src/nnfusion/engine/pass/graph/spargen…",
   "effect_text": "论文要求 4 位格式字段；artifact 路径无格式编码",
   "code_evidence": [],
   "paper_quote": "TeSA element has a two-byte attribute: 7 bits record the bit width of the element, 4 bits specify the element’s data format (e.g., unsigned…"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; merged (LLM: same issue): sparta-gap-M01-A04; priority 2: impl_deviates; related (candidate pair, judged different): sparta-F025"
}
```

### 论文侧 · not_implemented：`sparta-F051`

```json
{
 "finding_id": "sparta-F051",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求量化比特收敛规则；代码只处理剪枝掩码，无量化属性种类",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The propagate_mask/infer_modules_masks path only handles pruning masks and has no quantization-attribute conver…"
 },
 "limitations": [
  {
   "limitation_id": "sparta-gap-M02-B07-R02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary@1f61a36 实验脚本（script/figure13/finegrained_propagate.py、script/checkpoints/bert/bert_propagate.py）调用 nni@8c656fb 的 ModelS…",
   "effect_text": "论文要求量化比特收敛规则；代码只处理剪枝掩码，无量化属性种类",
   "code_evidence": [],
   "paper_quote": "For quantization, the attribute will be converged to the fewest quantization bits (or 0-bit, i.e., being pruned)."
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; priority 3: not_implemented, other effect; related (candidate pair, judged different): sparta-F003, sparta-F004, sparta-F005, sparta-F006"
}
```

### 论文侧 · no_condition：`sparta-F004`

```json
{
 "finding_id": "sparta-F004",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求把全部邻居（除 N）插入 S；代码只在度数归零时入队，非全部邻居",
 "witness_hint": {
  "kind": "input_value",
  "status": "no_condition",
  "condition": null,
  "path_prefix": [],
  "code_locations": [],
  "note": "LLM gave no usable condition: names not in the cited code: B"
 },
 "limitations": [
  {
   "limitation_id": "sparta-gap-M02-B05-R02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary@1f61a36 实验脚本（script/figure13/finegrained_propagate.py、script/checkpoints/bert/bert_propagate.py）调用 nni@8c656fb 的 ModelS…",
   "effect_text": "论文要求把全部邻居（除 N）插入 S；代码只在度数归零时入队，非全部邻居",
   "code_evidence": [],
   "paper_quote": "S.Insert(B.Remove(N));"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 2: impl_deviates; related (candidate pair, judged different): sparta-F003, sparta-F005, sparta-F006, sparta-F051"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### sparta（82 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 2 | path_change | solved | ✓ | `sparta/transformation/weighted_block_cover.py:77` | When cover_sizes[(1, 1)] < ordered_pricing[0][0]: The choice of covering algorithm is driven by the… |
| F002 | 合 | docs_only | 2 | reject | solved | ✓ | `sparta/transformation/weighted_block_cover.py:123` | When len(unique_block_sizes) != 1: wbc_matmul only supports a single block size for the weight tesa… |
| F003 | 论 | impl_deviates | 2 | other | always |  | `` | 论文要求 S 初始为全部节点；代码初始队列只含源/汇节点，其余节点由度数递减触发入队 |
| F004 | 论 | impl_deviates | 2 | other | no_condition |  | `` | 论文要求把全部邻居（除 N）插入 S；代码只在度数归零时入队，非全部邻居 |
| F005 | 论 | impl_deviates | 2 | other | always |  | `` | 论文要求直到无 TeSA 需更新；代码固定两遍、每节点一次，不检测掩码是否仍变化 |
| F006 | 论 | impl_deviates | 2 | other | always |  | `` | 论文要求随算子类型 AND 属性类型变化；代码仅覆盖剪枝一种属性种类（量化比特未实现，见 M02-B07-R02），属性维度分派缺失 |
| F007 | 论 | impl_deviates | 2 | other | always |  | `` | 论文要求重复运行多次（经验 256 个随机张量）；代码单次前向，以批内方差近似重复采样，重复次数由 confidence/batch 维决定而非 256 次独立运行 |
| F008 | 论 | impl_deviates | 2 | other | always |  | `` | 论文返回 Iupdated∪Oupdated 的输入与输出 TeSA 更新集；代码只返回每层 weight_mask，缺输入/输出更新集 |
| F009 | 论 | impl_deviates | 2 | other | always |  | `` | artifact 路径无通用纳入机制。 |
| F010 | 论 | impl_deviates | 2 | other | always |  | `script/figure14/search_finetune_fit_qat.py:169-178` | 论文要求用真实数据集推理得到的算子输入输出张量；逐模块传播路径用随机张量代替真实激活 |
| F011 | 论 | impl_deviates | 2 | other | always |  | `script/figure14/search_finetune_fit_qat.py:301-335` | 论文要求对算子所有张量（输入/权重/输出）逐一评估；代码只对 weight 张量做位宽搜索，input/output 未评估 |
| F012 | 论 | impl_deviates | 2 | other | no_condition |  | `script/figure14/search_finetune_fit_qat.py:496-538` | 论文要求精度下降小于预定义阈值（1%）才接受；代码用 best_acc<original_acc 即任何下降都拒绝，无 1% 阈值 |
| F013 | 论 | impl_deviates | 2 | other | always |  | `script/figure14/search_finetune_fit_qat.py:496-538` | 论文要求拓扑序并缓存激活；代码按模块注册顺序遍历且无激活缓存 |
| F014 | 论 | impl_deviates | 2 | other | trigger_only |  | `script/figure14/search_finetune_fit_qat.py:571-664` | 论文要求同时更新 S 与 Supdated；代码只更新全局位设置，无 Supdated 累积 |
| F015 | 论 | impl_deviates | 2 | other | always |  | `script/figure14/search_finetune_fit_qat.py:571-664` | 论文以 Tupdated==T 跳过；代码以精度下降 break，语义不同 |
| F016 | 论 | impl_deviates | 2 | other | always |  | `script/figure16/a100/sparta.cu:118-140` | 论文报告第二 sub-Matmul 的具体残余稀疏度；实验路径无该测量/输出，且底层分派规则与数值趋势不符。 |
| F017 | 论 | impl_deviates | 2 | other | no_condition |  | `script/figure16/a100/sparta.cu:266-311` | 实验路径的第二部分内核依赖为 Sputnik，而非 SparTA 专用稀疏内核。 |
| F018 | 论 | impl_deviates | 2 | other | always |  | `script/figure19/run.sh:1-7` | artifact 脚本无反馈驱动的稀疏属性更新步骤。 |
| F019 | 论 | impl_deviates | 2 | other | always |  | `script/figure19/run.sh:1-7` | artifact 无编译-测量迭代回路。 |
| F020 | 论 | impl_deviates | 2 | other | always |  | `script/figure19/run.sh:1-7` | 加速来自 NNI ModelSpeedup 而非 SparTA 稀疏 kernel。 |
| F021 | 论 | impl_deviates | 2 | other | always |  | `script/figure19/run.sh:1-7` | artifact 无目标稀疏度终止条件。 |
| F022 | 论 | impl_deviates | 2 | other | always |  | `script/init_checkpoints.sh:1-34` | 论文要求传播为 Rammer 内专用编译 pass；实验路径在编译前以 Python 脚本离线传播，编译器 pass 列表无传播 pass。 |
| F023 | 论 | impl_deviates | 2 | other | always |  | `script/run_all_2080ti.sh:1-57` | 论文要求复现 Figure 8-11、14-18、20；实际覆盖 8-11、13-15、17、19 与 table3，缺 figure18、figure20，且 2080Ti 路径无 figure1… |
| F024 | 论 | impl_deviates | 2 | other | solved |  | `sparta/artifact_specialization/generate_code.py:58-82` | 论文要求 2 字节位域属性；artifact 路径以文本配置+按位宽分支替代，未实现 7/4/5 位布局 |
| F025 | 论 | impl_deviates | 2 | other | solved |  | `sparta/artifact_specialization/generate_code.py:58-82` | 论文要求 4/8 表示 uint4/uint8；artifact 仅实现 int8 路径，无符号量化未体现 |
| F026 | 论 | impl_deviates | 2 | other | always |  | `sparta/propagation/talgebra.py:4-17` | 论文要求 ×、÷、x^y 三类算子均满足任一 φ 即 φ；代码只提供 × 的 and 规则，÷ 与 x^y 无任何规则 |
| F027 | 论 | impl_deviates | 2 | other | always |  | `sparta/propagation/talgebra.py:4-17` | 论文要求 ×/÷/x^y 三者均满足 α∧α→α；代码仅实现 × |
| F028 | 论 | impl_deviates | 2 | other | always |  | `sparta/propagation/talgebra.py:20-34` | 论文要求对逐元素可表达算子按计算流计算输出 TeSA；代码只对 matmul 实现，一元与 ÷/x^y 算子无对应计算流 |
| F029 | 论 | impl_deviates | 2 | other | always |  | `sparta/propagation/talgebra.py:50-62` | 论文要求三条导数公式（含 gB=gY）；代码仅实现两条，偏置项缺失。 |
| F030 | 论 | impl_deviates | 2 | other | solved |  | `sparta/specialization/specialize_kernel.py:18-42` | 论文允许输入分解；artifact 路径只处理单输入 TeSA |
| F031 | 论 | impl_deviates | 2 | other | solved |  | `sparta/specialization/specialize_kernel.py:18-42` | 输出不分解 |
| F032 | 论 | impl_deviates | 2 | other | solved |  | `sparta/specialization/specialize_kernel.py:18-42` | 论文要求 m+1 维笛卡尔积；代码仅权重维枚举，实际 1 维 |
| F033 | 论 | impl_deviates | 2 | other | solved |  | `sparta/specialization/specialize_kernel.py:44-77` | 论文要求位宽提示指导硬件指令选择（DP4A/wmma）；代码按位宽选不同 CUDA 模板，但模板选择处无基于位宽的指令级特化分支，32bit 分支直接走 cublas/稠密模板（artifact 范… |
| F034 | 论 | impl_deviates | 2 | other | solved |  | `sparta/specialization/specialize_kernel.py:44-77` | artifact 路径无 dismantle 展开步骤，仅消费预生成 kernel。 |
| F035 | 论 | impl_deviates | 2 | other | solved |  | `sparta/transformation/optimize_model.py:29-54` | 执行计划未被重写 |
| F036 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:56-81` | 论文要求每次调用产生新选项并初始化空列表；代码桩未实现且原地修改输入 |
| F037 | 论 | impl_deviates | 2 | other | solved |  | `sparta/transformation/transform_policy.py:56-81` | 论文要求返回累积分解列表；代码无该累积返回 |
| F038 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:56-81` | 论文要求对每个 BitRounding 结果 extend 其 WBC 输出；代码 TransformTeSA 未实现该 extend，实际路径仅收集未使用的 transform_options |
| F039 | 论 | impl_deviates | 2 | other | solved |  | `sparta/transformation/transform_policy.py:137-156` | 论文要求按采样位选项产生 k 个结果；代码无采样且限制最多 2 种位宽 |
| F040 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:137-156` | 论文要求先经 SampleBitOption 采样一个位选项再传给 BitRounding；代码无采样步骤，bit_align 直接使用 hardware_bit_precisions() 全集合（… |
| F041 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:137-156` | 论文要求每次运行返回新的（可不同的）变换选项；代码每次返回相同候选集合，无“per run 新选项”机制。（artifact 范围：。） |
| F042 | 论 | impl_deviates | 2 | other | solved |  | `sparta/transformation/transform_policy.py:137-191` | 论文要求每个操作数 TeSA 各自带块大小；代码仅权重 TeSA 获得 block_size，输入/输出 TeSA 的 block_size 保持 None 且不被消费（artifact 范围：仅权… |
| F043 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求 RecordPerf 记录每次 profile；artifact 路径计算后未记录 |
| F044 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求返回策略选出的最佳变换；代码无选择逻辑，返回 None |
| F045 | 论 | impl_deviates | 2 | other | solved |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求先 SampleBitOption 采样再传 BitRounding；代码以固定硬件位宽集合枚举替代采样（artifact 范围：无 SampleBitOption 采样触发） |
| F046 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求返回变换后 TeSA 列表；代码对应函数为桩，实际入口返回 None kernel 列表，未返回变换 TeSA 列表 |
| F047 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求调用方迭代多个方案并选满足者；代码迭代循环被注释，未执行方案搜索 |
| F048 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求每次调用返回一个新选项；代码返回固定单元素列表或一次性全部结果 |
| F049 | 论 | impl_deviates | 2 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文声称框架可纳入任意 sparsity-aware 技术；实验路径既未执行 specialization，其可达代码也只有固定模板枚举，无外部内核纳入能力。 |
| F050 | 代 | undisclosed | 3 | other | solved | ~ | `sparta/common/sparsity.py:57` | When info.module_name in self.modules_info: When a module name is already present, the merge branch… |
| F051 | 论 | not_implemented | 3 | other | always |  | `` | 论文要求量化比特收敛规则；代码只处理剪枝掩码，无量化属性种类 |
| F052 | 论 | not_implemented | 3 | other | always |  | `` | 论文要求分发前初始化 Iupdated/Oupdated 空集；代码无规则分发，仅建空字典收集结果 |
| F053 | 论 | not_implemented | 3 | other | always |  | `` | 论文要求 foreach RegisteredPropRule 调用规则；代码为固定两个硬编码推断函数，无注册表迭代 |
| F054 | 论 | not_implemented | 3 | other | always |  | `` | 论文要求把规则返回的 Iproped/Oproped 合并进节点 Is/Os；代码无规则返回值，直接由硬编码推断写 masks |
| F055 | 论 | not_implemented | 3 | other | no_condition |  | `` | 论文要求累积每条规则更新到 Iupdated/Oupdated；代码为逐层快照收集，无规则更新累积 |
| F056 | 论 | not_implemented | 3 | other | no_condition |  | `` | artifact 路径无单块回退到通用稀疏/dense kernel 的分派。 |
| F057 | 论 | not_implemented | 3 | other | always |  | `` | artifact 路径无该搜索步骤。 |
| F058 | 论 | not_implemented | 3 | other | always |  | `script/figure14/search_finetune_fit_qat.py:260-299` | 论文要求从最近缓存激活部分推理；代码无缓存也无部分推理 |
| F059 | 论 | not_implemented | 3 | other | always |  | `script/figure14/search_finetune_fit_qat.py:260-299` | 无注册调用 |
| F060 | 论 | not_implemented | 3 | other | always |  | `script/figure14/search_finetune_fit_qat.py:260-299` | 论文要求 La 输出激活部分推理得 Lb 校准数据；代码无此复用 |
| F061 | 论 | not_implemented | 3 | other | always |  | `script/figure14/search_finetune_fit_qat.py:301-335` | 无 TeSA 集合初始化 |
| F062 | 论 | not_implemented | 3 | other | always |  | `script/figure14/search_finetune_fit_qat.py:301-335` | 无 SplitToIsOs 返回 |
| F063 | 论 | not_implemented | 3 | other | always |  | `script/figure19/run.sh:1-7` | artifact 路径无编译后延迟/内存测量步骤。 |
| F064 | 论 | not_implemented | 3 | other | always |  | `script/figure19/run.sh:1-7` | artifact 路径无真实延迟过滤。 |
| F065 | 论 | not_implemented | 3 | other | always |  | `script/figure19/run.sh:1-7` | artifact 无编译迭代。 |
| F066 | 论 | not_implemented | 3 | other | always |  | `script/figure19/run.sh:1-7` | artifact 无 FLOPs 过滤基线。 |
| F067 | 论 | not_implemented | 3 | other | trigger_only |  | `sparta/core/sparta.py:16-24` | 论文要求对每个 (sub)operator 执行量化特化；artifact 链中特化调用被注释、重建为直通，未执行任何循环级特化。 |
| F068 | 论 | not_implemented | 3 | other | always |  | `sparta/propagation/talgebra.py:4-17` | 论文要求可注册新算子规则；代码无注册机制，新增算子需改源码 |
| F069 | 论 | not_implemented | 3 | other | always |  | `sparta/specialization/specialize_kernel.py:18-42` | 无 TransformOp 级 S 初始化 |
| F070 | 论 | not_implemented | 3 | other | always |  | `sparta/specialization/specialize_kernel.py:18-42` | 论文要求组合为图 G；代码无图构造步骤 |
| F071 | 论 | not_implemented | 3 | other | solved |  | `sparta/specialization/specialize_kernel.py:44-77` | 依赖存在但未被该判定消费，属未接线而非实现 |
| F072 | 论 | not_implemented | 3 | other | solved |  | `sparta/transformation/optimize_model.py:29-54` | 论文要求特化 tiling 对齐指令形状；artifact 入口链无 tiling 生成步骤。 |
| F073 | 论 | not_implemented | 3 | other | solved |  | `sparta/transformation/optimize_model.py:29-54` | 论文要求 DP4A 重排+替换；artifact 入口链无此步骤。 |
| F074 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求 while 搜索；artifact 路径仅单遍枚举 |
| F075 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求按 TeSA 位宽选指令；artifact 链未调用特化，位宽选择步骤不存在。 |
| F076 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 实验路径未执行 specialization 内核选择，且无 block==shape→通用稀疏内核的代码路径；依赖存在不等于执行路径存在。 |
| F077 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/transform_policy.py:158-191` | 实验路径未运行内核选择，且无 block==shape 的稠密回退分支。 |
| F078 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/transform_policy.py:172-191` | 论文要求从枚举结果选最佳；代码无候选集合，择优逻辑被注释 |
| F079 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/weighted_block_cover.py:7-24` | artifact 路径无 13 块大小评估入口 |
| F080 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/weighted_block_cover.py:7-24` | artifact 路径无零稀疏延迟测量入口 |
| F081 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/weighted_block_cover.py:7-24` | 论文要求 latency/块数；代码无该计算，E2 除法语义不同（按覆盖元素数分摊） |
| F082 | 论 | not_implemented | 3 | other | always |  | `sparta/transformation/weighted_block_cover.py:47-102` | 论文要求过稀疏时枚举所有块大小组合并选最优；代码无枚举、无最优选择、无触发条件 |
