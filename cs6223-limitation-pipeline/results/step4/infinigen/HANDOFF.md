# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；infinigen）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/infinigen/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **32 条 limitation**（代码侧 + 论文侧），去重后是 **31 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/infinigen/limitations_for_tests.json`。

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
| infinigen | 20 | 11 | 0 | 31 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 19 | 0 | 1 | 0 | 0 | 0 | 0 | 20 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 9 | 2 | 11 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

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
| 代码侧 | 8 | 9 | 3 | 20 |
| 论文侧 | 0 | 9 | 2 | 11 |
| 两侧合并 | 0 | 0 | 0 | 0 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 8 | 11 | 1 | 0 | 0 | 0 | 0 | 20 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 11 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 19 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 20 |
| 论文侧 | 6 | 0 | 1 | 4 | 0 | 0 | 0 | 0 | 11 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 2 | 10 | 2 | 6 | 20 |
| 论文侧 | 0 | 0 | 0 | 11 | 11 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 |

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
| infeasible | 条件和路径前缀矛盾，从入口走不到。`infeasible_because: call_chain` 表示是把被调函数的名字换成入口函数的名字之后才矛盾的（见下面“调用链”） | 已降为 p3，不用花预算 |
| no_condition | 论文侧：没有可用条件 | 读 `note` 和 summary，人工判断 |
| untranslatable / unknown | 条件翻译不了 / 求解超时 | 读 condition 原文 |

调用链（`call_chain_status`）：

| 值 | 意思 |
|---|---|
| resolved | `call_chain` 是从入口函数到目标所在函数的真实调用链（入口在前）。`call_sites` 逐层给出调用所在行、解析方式（`resolved_by`）和参数对应 `args`（被调函数的形参 -> 调用者里的表达式） |
| entry_is_target | 目标就在入口函数里 |
| module_level | 目标是模块级语句，import 时执行，没有调用链 |
| not_found | 静态分析找不到从入口到目标的调用链（动态分发、回调，或目标不在入口的路径上）。有 `calls_entry` 时表示这个函数是调用入口的一方（如框架集成），要直接驱动它 |

- `uncertain_steps` 列出靠猜解析的调用（方法名在仓库里唯一、子类覆盖、嵌套函数被传出去）。
- `other_chains` 是其它调用链（例如同一个函数有两个调用点）。
- `entry_terms`：条件和路径前缀换成入口函数名字后的写法，以及每个名字对应的入口表达式（如 `d` -> `k.shape[3]`）。有它时 `aliases` 也是用入口函数的名字写的。

已知不足：
- 没有调用链（not_found）时，`path_prefix` 仍混着各层函数的条件，同一个名字在调用者和被调用者里可能不是同一个东西。这时别名只在单层时参与求解，其余只列在 `aliases_not_applied` 里。
- 多行语句的 `snippet` 是 `ast.unparse` 后的第一行：并成一行、去掉 assert 消息、去掉多余括号，最多 200 字符。请按解析后的条件比较，不要逐字比较。
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

### 代码侧 · stated_differently（文档说得比代码弱）：`infinigen-F009`

```json
{
 "finding_id": "infinigen-F009",
 "category": "stated_differently",
 "priority": 2,
 "effect_type": "path_change",
 "scope_status": "unknown",
 "review": "worth_testing",
 "summary": "When self.layer_id > 1: partial_weight_ratio is only set for layers with layer_id > 1; layer 0 and 1 get None, so the partial-weight speculation path is disabled for the first two layers. (speedup/flexgen/infinigen/flex_opt.py:287)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "self.layer_id > 1",
  "path_prefix": [],
  "trigger": {
   "self.layer_id": 2
  },
  "contrast": {
   "self.layer_id": 1
  },
  "atoms": {
   "self.layer_id": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "call_chain_status": "not_found",
  "location": "speedup/flexgen/infinigen/flex_opt.py:287"
 },
 "limitations": [
  {
   "limitation_id": "CL-B001",
   "origin": "code",
   "condition_text": "self.layer_id > 1",
   "effect_text": "partial_weight_ratio is only set for layers with layer_id > 1; layer 0 and 1 get None, so the partial-weight speculation path is disabled for the first two lay…",
   "code_evidence": [
    "speedup/flexgen/infinigen/flex_opt.py:287-287"
   ],
   "paper_quote": null
  }
 ],
 "verifications": [
  {
   "result": "boundary_mismatch",
   "documented_in": [
    "paper"
   ],
   "quote": "InfiniGen initiates speculation and prefetching from Layer 1 because the outliers, which are essential for exploiting i…"
  }
 ],
 "rationale": "3b: boundary_mismatch in paper; 3b boundary_mismatch; priority 2: stated_differently"
}
```

### 代码侧 · state（事件序列）：`infinigen-F002`

```json
{
 "finding_id": "infinigen-F002",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "state",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None: Prefetch path 2 requires MIXED device with populated GPU portion; otherwise path 1. (speedup/flexgen/infinigen/flex_opt.py:442)",
 "witness_hint": {
  "kind": "event_sequence",
  "status": "solved",
  "condition": "k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None",
  "path_prefix": [
   "self.policy.cpu_cache_compute"
  ],
  "trigger": {
   "k_home.device.device_type": "DeviceType.MIXED",
   "k_home.data[0][0] is None": false,
   "self.policy.cpu_cache_compute": true
  },
  "contrast": {
   "k_home.device.device_type": {
    "not_in": [
     "DeviceType.MIXED"
    ]
   },
   "k_home.data[0][0] is None": false,
   "self.policy.cpu_cache_compute": true
  },
  "atoms": {
   "k_home.data[0][0] is None": {
    "kind": "predicate",
    "sort": "bool"
   },
   "k_home.device.device_type": {
    "kind": "category",
    "sort": "str"
   },
   "self.policy.cpu_cache_compute": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "call_chain_status": "not_found",
  "location": "speedup/flexgen/infinigen/flex_opt.py:442"
 },
 "limitations": [
  {
   "limitation_id": "CL-B004",
   "origin": "code",
   "condition_text": "k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None",
   "effect_text": "Prefetch path 2 requires MIXED device with populated GPU portion; otherwise path 1.",
   "code_evidence": [
    "speedup/flexgen/infinigen/flex_opt.py:442-442"
   ],
   "paper_quote": null
  }
 ],
 "verifications": [
  {
   "result": "not_found",
   "documented_in": [],
   "quote": null
  }
 ],
 "rationale": "3b: not_found; priority 1: undisclosed, state effect, witness reaches it; related (candidate pair, judged different): infinigen-F022"
}
```

### 代码侧 · infeasible（多半走不到，p3）：`infinigen-F029`

```json
{
 "finding_id": "infinigen-F029",
 "category": "undisclosed",
 "priority": 3,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When not (dst.device.device_type != DeviceType.MIXED): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:837)",
 "witness_hint": {
  "kind": "input_value",
  "status": "infeasible",
  "condition": "not (dst.device.device_type != DeviceType.MIXED)",
  "path_prefix": [
   "isinstance(k_cache, TorchTensor)",
   "not (attn_sparsity >= 1.0)",
   "k.is_cuda",
   "not (dst.device.device_type == DeviceType.MIXED)",
   "src.device.device_type == DeviceType.MIXED"
  ],
  "note": "no values satisfy path prefix, condition and scope together",
  "call_chain_status": "resolved",
  "call_chain": [
   "speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen",
   "speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice._sparse_attention_value",
   "speedup/flexgen/infinigen/pytorch_backend.py::general_copy"
  ],
  "location": "speedup/flexgen/infinigen/pytorch_backend.py:837"
 },
 "limitations": [
  {
   "limitation_id": "CL-X004",
   "origin": "code",
   "condition_text": "not (dst.device.device_type != DeviceType.MIXED)",
   "effect_text": "AssertionError",
   "code_evidence": [
    "speedup/flexgen/infinigen/pytorch_backend.py:837-837"
   ],
   "paper_quote": null
  }
 ],
 "verifications": [
  {
   "result": "not_found",
   "documented_in": [],
   "quote": null
  }
 ],
 "rationale": "3b: not_found; priority 3: unreachable: condition contradicts its path prefix"
}
```

### 论文侧 · impl_deviates · always：`infinigen-F020`

```json
{
 "finding_id": "infinigen-F020",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "控制平面组件集合不完整（缺Pool Manager）",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "speedup/flexgen/infinigen/flex_opt.py:282-282",
   "speedup/flexgen/infinigen/flex_opt.py:430-430"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The control-plane component set is incomplete (Pool Manager missing) regardless of runtime inputs, so the gap m…",
  "call_chain_status": "not_found",
  "location": "speedup/flexgen/infinigen/flex_opt.py:282"
 },
 "limitations": [
  {
   "limitation_id": "infinigen-gap-M08-B04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: speedup/flexgen/infinigen/flex_opt.py + pytorch_backend.py 的Infinigen执行路径（FlexGen OPT offloading运行时，含prefetch_cache与KV池拷贝），依赖sp…",
   "effect_text": "同上：无CPU内存压力下的池管理控制流",
   "code_evidence": [
    "speedup/flexgen/infinigen/flex_opt.py:430-430",
    "speedup/flexgen/infinigen/pytorch_backend.py:291-300"
   ],
   "paper_quote": "weights. We explain each operation in Section 4.3. The sec- ond component is the Pool Manager. It manages the KV cache pool on CPU memory u…"
  },
  {
   "limitation_id": "infinigen-gap-M08-A01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: speedup/flexgen/infinigen/flex_opt.py + pytorch_backend.py 的Infinigen执行路径（FlexGen OPT offloading运行时，含prefetch_cache与KV池拷贝），依赖sp…",
   "effect_text": "控制平面组件集合不完整（缺Pool Manager）",
   "code_evidence": [
    "speedup/flexgen/infinigen/flex_opt.py:282-282",
    "speedup/flexgen/infinigen/flex_opt.py:430-430"
   ],
   "paper_quote": "GPU Memory CPU Memory"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; merged (LLM: same issue): infinigen-gap-M08-B04; priority 2: impl_deviates"
}
```

### 论文侧 · LLM 写出条件并求解：`infinigen-F018`

```json
{
 "finding_id": "infinigen-F018",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求覆盖受害者槽位；代码保留全部 K/V 只做注意力屏蔽（artifact 范围：无覆盖写步骤）",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "past_key_value is not None",
  "path_prefix": [],
  "trigger": {
   "past_key_value is None": false
  },
  "contrast": {
   "past_key_value is None": true
  },
  "atoms": {
   "past_key_value is None": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "code_locations": [
   "accuracy/perplexity/table2.sh:27-45",
   "accuracy/src/modeling_opt_ours.py:259-269"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "call_chain_status": "not_found",
  "location": "accuracy/perplexity/table2.sh:27-45"
 },
 "limitations": [
  {
   "limitation_id": "infinigen-gap-M07-B03-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: accuracy/perplexity/table2.sh 实验路径（opt.py/llama.py + modeling_*_ours.py，capacity=0.8/1.0，evict∈{fifo,lru,counter}）；speedup/ 路径未…",
   "effect_text": "同上：无覆盖写步骤",
   "code_evidence": [
    "accuracy/perplexity/table2.sh:27-45",
    "accuracy/src/modeling_opt_ours.py:259-269"
   ],
   "paper_quote": "the manager overwrites the selected victim with the newly generated key and value"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; effect_text '同上' expanded from conformance.json local_entry; priority 2: impl_deviates; related (candidate pair, judged different): infinigen-F019"
}
```

### 论文侧 · not_implemented：`infinigen-F030`

```json
{
 "finding_id": "infinigen-F030",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求饱和时全体减半；代码无该步骤（artifact 范围：无饱和减半）",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "self.eviction_policy == \"counter\"",
  "path_prefix": [],
  "trigger": {
   "self.eviction_policy": "counter"
  },
  "contrast": {
   "self.eviction_policy": {
    "not_in": [
     "counter"
    ]
   }
  },
  "atoms": {
   "self.eviction_policy": {
    "kind": "category",
    "sort": "str"
   }
  },
  "code_locations": [
   "accuracy/perplexity/table2.sh:27-45",
   "accuracy/src/modeling_opt_ours.py:224-228"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "call_chain_status": "not_found",
  "location": "accuracy/perplexity/table2.sh:27-45"
 },
 "limitations": [
  {
   "limitation_id": "infinigen-gap-M07-B07",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: accuracy/perplexity/table2.sh 实验路径（opt.py/llama.py + modeling_*_ours.py，capacity=0.8/1.0，evict∈{fifo,lru,counter}）；speedup/ 路径未…",
   "effect_text": "同上：无饱和减半",
   "code_evidence": [
    "accuracy/perplexity/table2.sh:27-45",
    "accuracy/src/modeling_opt_ours.py:224-228"
   ],
   "paper_quote": "If any counter becomes saturated, all the counter values are reduced by half."
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; effect_text '同上' expanded from conformance.json local_entry; priority 3: not_implemented, other effect"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### infinigen（31 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved | ~ | `speedup/flexgen/infinigen/flex_opt.py:426` | When self.policy.attn_sparsity >= 1.0: Path 2 (split GPU/CPU attention) asserts that sparsity >= 1.… |
| F002 | 代 | undisclosed | 1 | state | solved |  | `speedup/flexgen/infinigen/flex_opt.py:442` | When k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None: Prefetch path… |
| F003 | 代 | undisclosed | 1 | reject | solved | ✓ | `speedup/flexgen/infinigen/flex_opt.py:466` | When path == 1 or path == 2: Prefetching is not implemented for CPU-compute paths 1 and 2; raises V… |
| F004 | 代 | undisclosed | 1 | reject | solved | ~ | `speedup/flexgen/infinigen/flex_opt.py:710` | When not (self.policy.act_gpu_percent == 100 or self.policy.act_cpu_percent == 100 or self.policy.a… |
| F005 | 代 | undisclosed | 1 | reject | solved | ~ | `speedup/flexgen/infinigen/flex_opt.py:1359` | When args.compress_cache and args.attn_sparsity < 1.0: Combining cache compression with attention s… |
| F006 | 代 | undisclosed | 1 | reject | solved |  | `speedup/flexgen/infinigen/pytorch_backend.py:464` | When not (attn_sparsity >= 1.0): AssertionError |
| F007 | 代 | undisclosed | 1 | reject | solved |  | `speedup/flexgen/infinigen/pytorch_backend.py:823` | When not (src.device.device_type != DeviceType.MIXED): AssertionError |
| F008 | 代 | undisclosed | 1 | reject | solved |  | `speedup/flexgen/infinigen/pytorch_backend.py:881` | When not (all((x.step is None for x in indices))): AssertionError |
| F009 | 代 | stated_differently | 2 | path_change | solved | ✓ | `speedup/flexgen/infinigen/flex_opt.py:287` | When self.layer_id > 1: partial_weight_ratio is only set for layers with layer_id > 1; layer 0 and … |
| F010 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/flex_opt.py:389` | When self.policy.attn_sparsity >= 1.0: When sparsity >= 1.0 the full V cache is copied; otherwise V… |
| F011 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/flex_opt.py:528` | When self.enable_prefetching: When prefetching is enabled, mha_gen is called with p_w_q, partial_k_… |
| F012 | 代 | undisclosed | 2 | path_change | solved |  | `speedup/flexgen/infinigen/flex_opt.py:541` | When prev_partial_cache_read_buf is not None and self.layer_id > 1: Partial cache accumulation for … |
| F013 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/flex_opt.py:799` | When j not in self.attn_layer[2:]: Cache loading is skipped for all attention layers except the fir… |
| F014 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/pytorch_backend.py:401` | When p_w_q is None: In TorchDevice.mha_gen, the InfiniGen KV speculation (speculate_attention) only… |
| F015 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/pytorch_backend.py:422` | When attn_sparsity >= 1.0: Caller-supplied attn_sparsity selects dense attention (decompress full k… |
| F016 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/pytorch_backend.py:479` | When comp_config.group_dim == 0: Caller-supplied comp_config.group_dim decides whether k_new/v_new … |
| F017 | 代 | undisclosed | 2 | path_change | solved | ~ | `speedup/flexgen/infinigen/pytorch_backend.py:767` | When policy.cache_disk_percent == 0: When the configured disk cache percent is zero, the KV cache i… |
| F018 | 论 | impl_deviates | 2 | other | solved |  | `accuracy/perplexity/table2.sh:27-45` | 论文要求覆盖受害者槽位；代码保留全部 K/V 只做注意力屏蔽（artifact 范围：无覆盖写步骤） |
| F019 | 论 | impl_deviates | 2 | other | solved |  | `accuracy/perplexity/table2.sh:27-45` | 论文要求淘汰后更新 GPU 部分 key cache；代码无该步骤（artifact 范围：缺更新步骤） |
| F020 | 论 | impl_deviates | 2 | other | always |  | `speedup/flexgen/infinigen/flex_opt.py:282` | 控制平面组件集合不完整（缺Pool Manager） |
| F021 | 论 | impl_deviates | 2 | other | solved |  | `speedup/flexgen/infinigen/flex_opt.py:513-524` | 论文要求A=V；代码A为V列按σq·σk排序重排，A≠V（artifact 范围：A为排序重排后的V，非论文所述A=V） |
| F022 | 论 | impl_deviates | 2 | other | trigger_only |  | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | 预取集合由 top-k(均值) 决定，而非严格 >max−alpha 的令牌集合 |
| F023 | 论 | impl_deviates | 2 | other | solved |  | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | 实验路径以绝对令牌数封顶，未实现 20% 比例上限 |
| F024 | 论 | impl_deviates | 2 | other | solved |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 实验路径缺少K的逐元素绝对值 |
| F025 | 论 | impl_deviates | 2 | other | always |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 求和对象缺少K_abs项 |
| F026 | 论 | impl_deviates | 2 | other | always |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 单次topk未容纳K离群列 |
| F027 | 代 | undisclosed | 3 | path_change | solved | ✗ | `speedup/flexgen/infinigen/flex_opt.py:690` | When (i == 0) or (i == (self.config.num_hidden_layers - 1)): When sep_layer is set, the first and l… |
| F028 | 代 | undisclosed | 3 | path_change | solved | ✗ | `speedup/flexgen/infinigen/pytorch_backend.py:326` | When warmup or partial_weight_ratio is None: In TorchDevice.mha, the partial-weight index (which he… |
| F029 | 代 | undisclosed | 3 | reject | infeasible |  | `speedup/flexgen/infinigen/pytorch_backend.py:837` | When not (dst.device.device_type != DeviceType.MIXED): AssertionError |
| F030 | 论 | not_implemented | 3 | other | solved |  | `accuracy/perplexity/table2.sh:27-45` | 论文要求饱和时全体减半；代码无该步骤（artifact 范围：无饱和减半） |
| F031 | 论 | not_implemented | 3 | other | always |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 实验路径缺少论文指定的相加步骤 |
