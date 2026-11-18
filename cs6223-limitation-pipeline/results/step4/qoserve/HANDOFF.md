# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；qoserve）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/qoserve/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **62 条 limitation**（代码侧 + 论文侧），去重后是 **50 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/qoserve/limitations_for_tests.json`。

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
| qoserve | 12 | 36 | 2 | 50 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 14 | 22 | 36 |
| 两侧合并 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 2 |

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
| 代码侧 | 2 | 6 | 4 | 12 |
| 论文侧 | 0 | 13 | 23 | 36 |
| 两侧合并 | 0 | 2 | 0 | 2 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 2 | 6 | 0 | 0 | 0 | 0 | 4 | 12 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 36 |
| 两侧合并 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 2 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| 论文侧 | 9 | 0 | 1 | 20 | 1 | 0 | 0 | 5 | 36 |
| 两侧合并 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 0 | 0 | 0 | 12 | 12 |
| 论文侧 | 0 | 0 | 0 | 36 | 36 |
| 两侧合并 | 0 | 0 | 0 | 2 | 2 |

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

### 代码侧 · infeasible（多半走不到，p3）：`qoserve-F038`

```json
{
 "finding_id": "qoserve-F038",
 "category": "impl_deviates",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文称固定 QPS 采用 8 ms/token；artifact 固定 QPS 运行脚本使用 16 ms/token，与论文所选值不符。",
 "witness_hint": {
  "kind": "input_value",
  "status": "infeasible",
  "condition": "hybrid_prioritization_param == 0.016",
  "path_prefix": [],
  "note": "no values satisfy path prefix, condition and scope together",
  "code_locations": [
   "fig8.sh:37-69",
   "sarathi/config/config.py:305-308"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "call_chain_status": "not_found",
  "location": "fig8.sh:37-69"
 },
 "limitations": [
  {
   "limitation_id": "qoserve-gap-M10-B02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: primary 仓库实验/构建路径：fig8.sh（生成 fig8_wrapper.sh 并调用 sarathi.benchmark.main，含 --deadline_scheduler_hybrid_prioritization_param 0.01…",
   "effect_text": "论文称固定 QPS 采用 8 ms/token；artifact 固定 QPS 运行脚本使用 16 ms/token，与论文所选值不符。",
   "code_evidence": [
    "fig8.sh:37-69",
    "sarathi/config/config.py:305-308"
   ],
   "paper_quote": "decode length.𝛼 is a configurable hyperparameter. For fixed- QPS runs, we perform an offline sweep of𝛼 values from 0 to 10 and select the v…"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 3: unreachable: condition contradicts its path prefix"
}
```

### 两侧合并：`qoserve-F003`

```json
{
 "finding_id": "qoserve-F003",
 "category": "docs_only",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When NUM_TIERS > 0: Each Sequence's QoS tier (and hence its deadline) is drawn at random from the global `random` module rather than from any caller-supplied SLA. The tier then drives `self.tier_deadline = TIER_DEADLINES[self.tier]` (line 74) and `_get_TBT_deadline`'s choice of `execution_threshold_batched` when `self.tier > 0` (lines 114-115), so the scheduling decision depends on the process-...",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "NUM_TIERS > 0",
  "path_prefix": [
   "Sequence.__init__"
  ],
  "trigger": {
   "NUM_TIERS": 1,
   "Sequence.__init__": true
  },
  "contrast": {
   "NUM_TIERS": 0,
   "Sequence.__init__": true
  },
  "atoms": {
   "NUM_TIERS": {
    "kind": "input",
    "sort": "int"
   },
   "Sequence.__init__": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "note": "local definitions in the checked function, not used by the solver because the path prefix also holds caller conditions",
  "call_chain_status": "not_found",
  "location": "sarathi/core/datatypes/sequence.py:73"
 },
 "limitations": [
  {
   "limitation_id": "CL-B001",
   "origin": "code",
   "condition_text": "NUM_TIERS > 0",
   "effect_text": "Each Sequence's QoS tier (and hence its deadline) is drawn at random from the global `random` module rather than from any caller-supplied SLA. The tier then dr…",
   "code_evidence": [
    "sarathi/core/datatypes/sequence.py:73-73"
   ],
   "paper_quote": null
  },
  {
   "limitation_id": "qoserve-gap-M01-B01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的 sarathi 调度器 + DeadlineSchedulerConfig（execution_threshold/execution_threshold_batched）+ benchmark 请求生成器；pape…",
   "effect_text": "实验路径同样没有应用指定 QoS 类的入口，类别由随机数决定。",
   "code_evidence": [
    "sarathi/core/datatypes/sequence.py:11-11",
    "sarathi/core/datatypes/sequence.py:70-80",
    "README.md:110-119"
   ],
   "paper_quote": "3.2 QoS Classes and Deadlines QoServe defines two QoS classes: interactive and non in- teractive. Interactive requests use two SLOs — TTFT …"
  },
  {
   "limitation_id": "qoserve-gap-M01-B05",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的 sarathi 调度器 + DeadlineSchedulerConfig（execution_threshold/execution_threshold_batched）+ benchmark 请求生成器；pape…",
   "effect_text": "实验路径同样无应用自定义 SLO 的配置入口。",
   "code_evidence": [
    "sarathi/core/datatypes/sequence.py:11-11",
    "sarathi/core/datatypes/sequence.py:70-80",
    "README.md:110-119"
   ],
   "paper_quote": "the application owner is free to specify their custom SLO targets within the class"
  },
  {
   "limitation_id": "qoserve-gap-M06-B04-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的 deadline 调度执行路径：DeadlineScheduler + Sequence 元数据 + deadline 配置/基准脚本；Fig.5 数值与多租户 tier 提示路径需运行/配置对齐，本快照未完成。. …",
   "effect_text": "同上。",
   "code_evidence": [
    "sarathi/core/datatypes/sequence.py:61-80",
    "README.md:103-120"
   ],
   "paper_quote": "In multi-tenant deployments, we also use application hints such as free vs paid tier to preferentially relegate low-priority requests to en…"
  }
 ],
 "verifications": [
  {
   "result": "found",
   "documented_in": [
    "code_comment",
    "readme"
   ],
   "quote": "randomly assign a tier to the request between 0 and NUM_TIERs - 1"
  }
 ],
 "rationale": "3b: found in code_comment, readme; merged (LLM: same issue): qoserve-gap-M01-B01, qoserve-gap-M01-B05, qoserve-gap-M06-B04-R01; paper side also reports: impl_deviates, not_implemented; priority 2: impl_deviates; related (candidate pair, judged different): qoserve-F020, qoserve-F022, qoserve-F024, q…"
}
```

### 论文侧 · impl_deviates · always：`qoserve-F019`

```json
{
 "finding_id": "qoserve-F019",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "脚本层无每请求优先级配置。",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "sarathi/config/config.py:284-311"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The config dataclass only exposes global output_len_pred and hybrid_prioritization_param fields with no per-req…",
  "call_chain_status": "module_level",
  "call_chain": [
   "sarathi/config/config.py::<module>"
  ],
  "location": "sarathi/config/config.py:284-311"
 },
 "limitations": [
  {
   "limitation_id": "qoserve-gap-M11-B02-R02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的调度器路径 + 实验脚本（fig7_conv.sh/fig7_sharegpt.sh/fig8.sh 等传入 output_len_pred、hybrid_prioritization_param）；vLLM 外部依赖…",
   "effect_text": "脚本层无每请求优先级配置。",
   "code_evidence": [
    "sarathi/config/config.py:284-311"
   ],
   "paper_quote": "anisms. We extended the vLLM API to associate each in- ference request with its corresponding QoS requirements (TTFT, TBT, and/or TTLT) and…"
  },
  {
   "limitation_id": "qoserve-gap-M11-B05",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的调度器路径 + 实验脚本（fig7_conv.sh/fig7_sharegpt.sh/fig8.sh 等传入 output_len_pred、hybrid_prioritization_param）；vLLM 外部依赖…",
   "effect_text": "脚本层无应用提示优先级入口。",
   "code_evidence": [
    "sarathi/config/config.py:284-311"
   ],
   "paper_quote": "we add a priority field to each request that enables relegation decisions based on application hints such as free-tier versus premium users"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; merged (LLM: same issue): qoserve-gap-M11-B05; priority 2: impl_deviates; related (candidate pair, judged different): qoserve-F018, qoserve-F045"
}
```

### 论文侧 · LLM 写出条件并求解：`qoserve-F020`

```json
{
 "finding_id": "qoserve-F020",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "实验路径同样没有独立的 D_total 完成截止。",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "seq.tier >= 1",
  "path_prefix": [],
  "trigger": {
   "seq.tier": 1
  },
  "contrast": {
   "seq.tier": 0
  },
  "atoms": {
   "seq.tier": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "code_locations": [
   "sarathi/core/datatypes/sequence.py:70-80",
   "sarathi/core/scheduler/deadline_scheduler.py:226-237",
   "README.md:110-119"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "call_chain_status": "not_found",
  "location": "sarathi/core/datatypes/sequence.py:70-80"
 },
 "limitations": [
  {
   "limitation_id": "qoserve-gap-M01-B04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的 sarathi 调度器 + DeadlineSchedulerConfig（execution_threshold/execution_threshold_batched）+ benchmark 请求生成器；pape…",
   "effect_text": "实验路径同样没有独立的 D_total 完成截止。",
   "code_evidence": [
    "sarathi/core/datatypes/sequence.py:70-80",
    "sarathi/core/scheduler/deadline_scheduler.py:226-237",
    "README.md:110-119"
   ],
   "paper_quote": "𝐷𝑡𝑜𝑡𝑎𝑙 =𝑡𝑎𝑟𝑟𝑖𝑣𝑎𝑙+𝑆𝐿𝑂𝑇𝑇𝐿𝑇 (3)"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 2: impl_deviates; related (candidate pair, judged different): qoserve-F003, qoserve-F007, qoserve-F008, qoserve-F024"
}
```

### 论文侧 · not_implemented：`qoserve-F028`

```json
{
 "finding_id": "qoserve-F028",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求用 Vidur 暴露的 harness 采集剖面；pinned 仓库中不存在该采集实现",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "chunk_size_predictor/predictor.py:1-41",
   "chunk_size_predictor/predictor.py:213-254"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The pinned repository lacks the Vidur-based profiling harness entirely, so the paper's data-collection precondi…",
  "call_chain_status": "module_level",
  "call_chain": [
   "chunk_size_predictor/predictor.py::<module>"
  ],
  "location": "chunk_size_predictor/predictor.py:1-41"
 },
 "limitations": [
  {
   "limitation_id": "qoserve-gap-M03-B04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: chunk_size_predictor/predictor.py（训练/评估脚本，依赖未提供的 make_master_csv.py 生成的 master CSV）+ 上述调度器路径；Vidur 采集与 A100 实验路径未提供. Paper prec…",
   "effect_text": "论文要求用 Vidur 暴露的 harness 采集剖面；pinned 仓库中不存在该采集实现",
   "code_evidence": [
    "chunk_size_predictor/predictor.py:1-41",
    "chunk_size_predictor/predictor.py:213-254"
   ],
   "paper_quote": "chunk sizes, batch sizes as well as context lengths. To collect this data, we use a lightweight harness exposed by an infer- ence simulator…"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; priority 3: not_implemented, other effect; related (candidate pair, judged different): qoserve-F012"
}
```

### 论文侧 · no_condition：`qoserve-F011`

```json
{
 "finding_id": "qoserve-F011",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "实验脚本不自动下载数据集，需先手动 wget",
 "witness_hint": {
  "kind": "input_value",
  "status": "no_condition",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "README.md:1-129",
   "fig7.sh:1-182"
  ],
  "note": "not decided by input values: The gap is that the experiment scripts do not auto-download datasets (requiring manual wget), which is a fixed property of the scripts rather than something depending on …",
  "call_chain_status": "not_found",
  "location": "README.md:1-129"
 },
 "limitations": [
  {
   "limitation_id": "qoserve-gap-M14-A04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 脚本实际调用的实验路径 python -m sarathi.benchmark.main（DEADLINE 调度、POISSON 到达、TRACE 长度、FLASHINFER、DUMMY 权重）与绘图路径；CUDA/A100/FlashInfer/HF …",
   "effect_text": "实验脚本不自动下载数据集，需先手动 wget",
   "code_evidence": [
    "README.md:1-129",
    "fig7.sh:1-182"
   ],
   "paper_quote": "A.3.4 Data sets. ShareGPT [19] and Azure production traces (Code, Conversation) [15]. Scripts automatically down- load datasets from public…"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 2: impl_deviates"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### qoserve（50 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:251` | When not (seq.is_paused()): 'Sequence should be in PAUSED state' |
| F002 | 代 | undisclosed | 1 | reject | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:253` | When not (self.block_manager.can_append_slot()): AssertionError |
| F003 | 合 | docs_only | 2 | other | solved |  | `sarathi/core/datatypes/sequence.py:73` | When NUM_TIERS > 0: Each Sequence's QoS tier (and hence its deadline) is drawn at random from the g… |
| F004 | 合 | undisclosed | 2 | path_change | solved |  | `sarathi/core/datatypes/sequence.py:114` | When self.tier > 0: For any non-zero (randomly assigned) tier, the TBT deadline uses execution_thre… |
| F005 | 代 | undisclosed | 2 | path_change | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:120` | When memory_budget < 1000: When free KV-cache blocks (free_blocks * block_size // 32) fall below 10… |
| F006 | 代 | undisclosed | 2 | path_change | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:130` | When min_slack <= 0: When the caller-supplied slack is non-positive, the binary search is skipped e… |
| F007 | 代 | undisclosed | 2 | path_change | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:231` | When seq.tier >= 1: For tier>=1 sequences the ttft_deadline is recomputed by subtracting predicted … |
| F008 | 代 | undisclosed | 2 | path_change | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:233` | When seq.num_decode_tokens == -1: Selects whether the decode-time estimate uses the global output_l… |
| F009 | 代 | undisclosed | 2 | path_change | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:276` | When self.scheduler_type == 'deadline': Only when scheduler_type is 'deadline' is the dynamic chunk… |
| F010 | 代 | undisclosed | 2 | path_change | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:300` | When self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking': Th… |
| F011 | 论 | impl_deviates | 2 | other | no_condition |  | `README.md:1-129` | 实验脚本不自动下载数据集，需先手动 wget |
| F012 | 论 | impl_deviates | 2 | other | always |  | `chunk_size_predictor/predictor.py:1-41` | 论文要求训练随机森林；脚本导入并训练 LinearRegression，无 RandomForest/ensemble |
| F013 | 论 | impl_deviates | 2 | other | always |  | `fig7.sh:76-106` | 缺 §4.3/§4.4 执行路径 |
| F014 | 论 | impl_deviates | 2 | other | trigger_only |  | `fig7.sh:76-106` | 缺 Qwen/70B 与 4 小时控制 |
| F015 | 论 | impl_deviates | 2 | other | solved |  | `paper_plot_scripts/fig7_cap.py:13-47` | Q1 的 TBT 违规未被度量 |
| F016 | 论 | impl_deviates | 2 | other | always |  | `paper_plot_scripts/fig_10_11.py:1-20` | 图输出目录与论文声明的 paper_plots/ 不一致 |
| F017 | 论 | impl_deviates | 2 | other | always |  | `paper_plot_scripts/fig_10_11.py:19-37` | 固定阈值替代数据 p90 |
| F018 | 论 | impl_deviates | 2 | other | always |  | `sarathi/config/config.py:284-311` | 脚本层同样无按请求提交 QoS 字段的配置。 |
| F019 | 论 | impl_deviates | 2 | other | always |  | `sarathi/config/config.py:284-311` | 脚本层无每请求优先级配置。 |
| F020 | 论 | impl_deviates | 2 | other | solved |  | `sarathi/core/datatypes/sequence.py:70-80` | 实验路径同样没有独立的 D_total 完成截止。 |
| F021 | 论 | impl_deviates | 2 | other | solved |  | `sarathi/core/datatypes/sequence.py:88-109` | 论文要求 α 同时乘 (Prefill_rem+Decode_rem)；代码把 decode 估计以固定系数 execution_threshold_batched 从期限中扣除，而非以 α 加权加… |
| F022 | 论 | impl_deviates | 2 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求检查“已违反 或 将违反”TTFT/TTLT；代码仅做 TTFT 前瞻（now+service_time>deadline），且仅对 drop==0 且未分配内存的请求生效，无 TTLT 维… |
| F023 | 论 | impl_deviates | 2 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求移入独立 relegated 队列；代码仅设 drop 标志并放回原 prefill 队列，无 relegated 队列结构，且 drop 请求仍可被再次选中调度。（artifact 范围：… |
| F024 | 代 | undisclosed | 3 | other | solved |  | `sarathi/core/datatypes/sequence.py:80` | When self.scheduler_type == 'fcfs': `Sequence.__lt__` dispatches on this per-object attribute: 'fcf… |
| F025 | 代 | undisclosed | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:92` | When batch_num_tokens <= 512: The execution-time predictor switches between two hard-coded stratifi… |
| F026 | 代 | undisclosed | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:211` | When not self._check_request_prompt_length(seq): Requests whose prompt length fails the check are a… |
| F027 | 代 | undisclosed | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:305` | When (seq.drop == 0) and (seq.mem_allocated == False) and ((now + service_time_required) > (seq.arr… |
| F028 | 论 | not_implemented | 3 | other | always |  | `chunk_size_predictor/predictor.py:1-41` | 论文要求用 Vidur 暴露的 harness 采集剖面；pinned 仓库中不存在该采集实现 |
| F029 | 论 | not_implemented | 3 | other | always |  | `fig10_11.sh:103-129` | 偏斜工作负载未实现 |
| F030 | 论 | not_implemented | 3 | other | always |  | `fig7.sh:76-106` | 未实现按 QoS 桶独立集群的 silo 部署 |
| F031 | 论 | not_implemented | 3 | other | always |  | `fig7.sh:76-106` | silo 基线整体缺失，无按桶 chunk 配置 |
| F032 | 论 | not_implemented | 3 | other | no_condition |  | `fig7.sh:76-106` | 集群规模实验缺失 |
| F033 | 论 | not_implemented | 3 | other | always |  | `fig7.sh:76-106` | 瞬态过载工作负载未实现 |
| F034 | 论 | not_implemented | 3 | other | always |  | `fig7.sh:76-106` | 无峰谷比构造 |
| F035 | 论 | not_implemented | 3 | other | no_condition |  | `fig7.sh:76-106` | 集群规模实验缺失 |
| F036 | 论 | not_implemented | 3 | other | no_condition |  | `fig7.sh:76-106` | 替代分配实验缺失 |
| F037 | 论 | not_implemented | 3 | other | always |  | `fig8.sh:37-69` | 论文要求固定 QPS 下离线扫描 α 0–10；artifact 脚本对 α 只给单一常量 0.016，未遍历 0–10 的 α 网格。 |
| F038 | 论 | impl_deviates | 3 | other | infeasible |  | `fig8.sh:37-69` | 论文称固定 QPS 采用 8 ms/token；artifact 固定 QPS 运行脚本使用 16 ms/token，与论文所选值不符。 |
| F039 | 论 | not_implemented | 3 | other | always |  | `fig8.sh:37-69` | 论文要求低负载 α=1 ms/token；artifact 无该取值或负载分段。 |
| F040 | 论 | not_implemented | 3 | other | always |  | `fig8.sh:37-69` | 组件消融未实现 |
| F041 | 论 | not_implemented | 3 | other | always |  | `fig8.sh:37-69` | 消融表汇总未实现 |
| F042 | 论 | not_implemented | 3 | other | always |  | `fig8.sh:37-69` | alpha 敏感性实验未实现 |
| F043 | 论 | not_implemented | 3 | other | always |  | `paper_plot_scripts/fig_10_11.py:19-37` | 优先级标注未实现 |
| F044 | 论 | not_implemented | 3 | other | always |  | `run_exp.sh:1-27` | 未实现多副本 round-robin 分发 |
| F045 | 论 | not_implemented | 3 | other | always |  | `sarathi/config/config.py:284-311` | 脚本层同样无按应用解码历史。 |
| F046 | 论 | not_implemented | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | 论文要求优先级驱动的抢占；对齐 artifact 调度路径不执行抢占。 |
| F047 | 论 | not_implemented | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | 缺少 prefill 队列抢占资格判定。 |
| F048 | 论 | not_implemented | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | 论文所述避免队头阻塞的抢占手段在 DeadlineScheduler 中不存在。（artifact 范围：。） |
| F049 | 论 | not_implemented | 3 | other | no_condition |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求按优先级抢占已部分 prefill 的在途请求；代码无任何抢占触发或调用，仅通过堆排序选择未开始的请求 |
| F050 | 论 | not_implemented | 3 | other | solved |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求按优先级分层、低优先级耗尽后才降级高优先级；代码对所有请求一视同仁按截止时间降级，无分层门控。（artifact 范围：。） |
