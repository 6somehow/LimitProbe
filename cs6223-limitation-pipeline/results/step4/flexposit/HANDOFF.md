# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；flexposit）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/flexposit/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **48 条 limitation**（代码侧 + 论文侧），去重后是 **41 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/flexposit/limitations_for_tests.json`。

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
| flexposit | 21 | 19 | 1 | 41 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 16 | 0 | 0 | 5 | 0 | 0 | 0 | 21 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 15 | 4 | 19 |
| 两侧合并 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

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
| 代码侧 | 6 | 2 | 13 | 21 |
| 论文侧 | 0 | 15 | 4 | 19 |
| 两侧合并 | 1 | 0 | 0 | 1 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 8 | 3 | 0 | 0 | 0 | 0 | 10 | 21 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 19 |
| 两侧合并 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 21 |
| 论文侧 | 5 | 0 | 0 | 7 | 0 | 0 | 0 | 7 | 19 |
| 两侧合并 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 0 | 0 | 0 | 21 | 21 |
| 论文侧 | 0 | 0 | 0 | 19 | 19 |
| 两侧合并 | 0 | 0 | 0 | 1 | 1 |

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

### 代码侧 · undisclosed · p1 · 有别名：`flexposit-F001`

```json
{
 "finding_id": "flexposit-F001",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When True: raise FileNotFoundError(f'No sensitivity CSV {str(name_or_path)!r}: not a file, and not one of the shipped models {shipp (src/flexposit/api.py:120)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "not (shipped.is_file())",
  "path_prefix": [
   "config.bits > config.base_nsize",
   "not (os.path.isfile(name_or_path))"
  ],
  "aliases": {
   "shipped.is_file()": "(resources.files('flexposit') / 'data' / 'sensitivity' / f'{sensitivity}.csv').is_file()",
   "os.path.isfile(name_or_path)": "os.path.isfile(sensitivity)"
  },
  "entry_terms": {
   "condition": "not (resources.files('flexposit') / 'data' / 'sensitivity' / f'{sensitivity}.csv').is_file()",
   "path_prefix": {
    "not os.path.isfile(name_or_path)": "not os.path.isfile(sensitivity)"
   },
   "names": {
    "shipped.is_file()": "(resources.files('flexposit') / 'data' / 'sensitivity' / f'{sensitivity}.csv').is_file()",
    "os.path.isfile(name_or_path)": "os.path.isfile(sensitivity)"
   }
  },
  "trigger": {
   "shipped.is_file()": false,
   "config.bits": 2,
   "config.base_nsize": 1,
   "os.path.isfile(name_or_path)": false,
   "(resources.files('flexposit') / 'data' / 'sensitivity' / f'{sensitivity}.csv').is_file()": false,
   "os.path.isfile(sensitivity)": false
  },
  "contrast": {
   "shipped.is_file()": true,
   "config.bits": 2,
   "config.base_nsize": 1,
   "os.path.isfile(name_or_path)": false,
   "(resources.files('flexposit') / 'data' / 'sensitivity' / f'{sensitivity}.csv').is_file()": true,
   "os.path.isfile(sensitivity)": false
  },
  "atoms": {
   "(resources.files('flexposit') / 'data' / 'sensitivity' / f'{sensitivity}.csv').is_file()": {
    "kind": "predicate",
    "sort": "bool"
   },
   "config.base_nsize": {
    "kind": "derived",
    "sort": "int"
   },
   "config.bits": {
    "kind": "derived",
    "sort": "int"
   },
   "os.path.isfile(name_or_path)": {
    "kind": "predicate",
    "sort": "bool"
   },
   "os.path.isfile(sensitivity)": {
    "kind": "predicate",
    "sort": "bool"
   },
   "shipped.is_file()": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "call_chain_status": "resolved",
  "call_chain": [
   "src/flexposit/api.py::quantize",
   "src/flexposit/api.py::read_sensitivity",
   "src/flexposit/api.py::sensitivity_csv"
  ],
  "location": "src/flexposit/api.py:120-121"
 },
 "limitations": [
  {
   "limitation_id": "CL-X002",
   "origin": "code",
   "condition_text": "True",
   "effect_text": "raise FileNotFoundError(f'No sensitivity CSV {str(name_or_path)!r}: not a file, and not one of the shipped models {shipp",
   "code_evidence": [
    "src/flexposit/api.py:120-121"
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
 "rationale": "3b: not_found; priority 1: undisclosed, reject effect, witness reaches it"
}
```

### 代码侧 · docs_only（README / docstring 写了，论文没写）：`flexposit-F027`

```json
{
 "finding_id": "flexposit-F027",
 "category": "docs_only",
 "priority": 3,
 "effect_type": "path_change",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When config.bits > config.base_nsize: When bits exceeds base_nsize the code requires a sensitivity ranking and runs the window-upgrade planning path; otherwise no windows are upgraded and all channels stay at base_nsize. (src/flexposit/api.py:181)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "config.bits > config.base_nsize",
  "path_prefix": [
   "quantize"
  ],
  "trigger": {
   "config.bits": 2,
   "config.base_nsize": 1,
   "quantize": true
  },
  "contrast": {
   "config.bits": 1,
   "config.base_nsize": 1,
   "quantize": true
  },
  "atoms": {
   "config.base_nsize": {
    "kind": "derived",
    "sort": "int"
   },
   "config.bits": {
    "kind": "derived",
    "sort": "int"
   },
   "quantize": {
    "kind": "input",
    "sort": "bool"
   }
  },
  "call_chain_status": "entry_is_target",
  "call_chain": [
   "src/flexposit/api.py::quantize"
  ],
  "location": "src/flexposit/api.py:181"
 },
 "limitations": [
  {
   "limitation_id": "CL-B003",
   "origin": "code",
   "condition_text": "config.bits > config.base_nsize",
   "effect_text": "When bits exceeds base_nsize the code requires a sensitivity ranking and runs the window-upgrade planning path; otherwise no windows are upgraded and all chann…",
   "code_evidence": [
    "src/flexposit/api.py:181-181"
   ],
   "paper_quote": null
  }
 ],
 "verifications": [
  {
   "result": "found",
   "documented_in": [
    "docstring"
   ],
   "quote": "It is required when ``config.bits`` is above ``config.base_nsize``"
  }
 ],
 "rationale": "3b: found in docstring; priority 3: docs_only, path_change effect"
}
```

### 两侧合并：`flexposit-F004`

```json
{
 "finding_id": "flexposit-F004",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When scale.min() < -16 or scale.max() > 15: export_tile raises ValueError when the per-column scale (-log2_scale) does not fit the RTL's signed 5-bit field, rejecting configurations whose log2_scale falls outside [-15, 16]. (src/flexposit/export.py:135)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "scale.min() < -16 or scale.max() > 15",
  "path_prefix": [],
  "trigger": {
   "scale.min()": 1,
   "scale.max()": 16
  },
  "contrast": {
   "scale.min()": 1,
   "scale.max()": 15
  },
  "atoms": {
   "scale.max()": {
    "kind": "derived",
    "sort": "int"
   },
   "scale.min()": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "call_chain_status": "not_found",
  "location": "src/flexposit/export.py:135"
 },
 "limitations": [
  {
   "limitation_id": "CL-B009",
   "origin": "code",
   "condition_text": "scale.min() < -16 or scale.max() > 15",
   "effect_text": "export_tile raises ValueError when the per-column scale (-log2_scale) does not fit the RTL's signed 5-bit field, rejecting configurations whose log2_scale fall…",
   "code_evidence": [
    "src/flexposit/export.py:135-135"
   ],
   "paper_quote": null
  },
  {
   "limitation_id": "flexposit-gap-M01-B08",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 Python 量化路径 + 其声明的导出/硬件路径：src/flexposit/export.py（layer_codes/export_tile、scale.mem 5-bit 有符号指数）与 hardware/rtl/bfp_pow2_resc…",
   "effect_text": "论文 4-bit 索引 vs 硬件 5-bit 有符号 scale 字段。",
   "code_evidence": [
    "src/flexposit/export.py:105-141",
    "hardware/rtl/bfp_pow2_rescale.v:10-54"
   ],
   "paper_quote": "a compact 4 b index stores the selected per-channel scale with low metadata overhead"
  }
 ],
 "verifications": [
  {
   "result": "not_found",
   "documented_in": [],
   "quote": null
  }
 ],
 "rationale": "3b: not_found; merged (LLM: same issue): flexposit-gap-M01-B08; paper side also reports: impl_deviates; priority 1: undisclosed, reject effect, witness reaches it; related (candidate pair, judged different): flexposit-F023, flexposit-F031"
}
```

### 论文侧 · impl_deviates · always：`flexposit-F010`

```json
{
 "finding_id": "flexposit-F010",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求 4 PE 共享 1 个 FP16 累加器；RTL 为每 PE 独立块浮点累加器（ACC_MANW=12, GRS=3，非 FP16 格式），无时分复用。",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "hardware/README.md:3-9",
   "hardware/rtl/fp8_pe_mac_stream.v:497-621",
   "hardware/rtl/fp8_pe_mac_stream.v:31-80"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The RTL instantiates one block-floating-point accumulator per PE (ACC_MANW=12, GRS=3) rather than a single shar…",
  "call_chain_status": "not_found",
  "location": "hardware/README.md:3-9"
 },
 "limitations": [
  {
   "limitation_id": "flexposit-gap-M09-B01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求每簇 4 个 PE；RTL 为 N×N 阵列，PE 间仅逐行/逐列传递权重、激活与 valid，不存在 4-PE 簇边界。",
   "code_evidence": [
    "hardware/rtl/systolic_efficient.v:242-330",
    "hardware/rtl/fp8_pe_mac_stream.v:497-621"
   ],
   "paper_quote": "FlexPosit groups four PEs into a 4-way MAC cluster"
  },
  {
   "limitation_id": "flexposit-gap-M09-B04-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求 4 PE 共享 1 个 FP16 累加器；RTL 为每 PE 独立块浮点累加器（ACC_MANW=12, GRS=3，非 FP16 格式），无时分复用。",
   "code_evidence": [
    "hardware/README.md:3-9",
    "hardware/rtl/fp8_pe_mac_stream.v:497-621",
    "hardware/rtl/fp8_pe_mac_stream.v:31-80"
   ],
   "paper_quote": "the four PEs within a cluster share a single FP16 accumulator time-multiplexed across lanes"
  },
  {
   "limitation_id": "flexposit-gap-M09-B05-R02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求 4 PE 交错驱动单一累加器；RTL 无交错与共享累加器。",
   "code_evidence": [
    "hardware/rtl/systolic_efficient.v:242-330",
    "hardware/rtl/systolic_efficient.v:198-240",
    "hardware/rtl/fp8_pe_mac_stream.v:497-621"
   ],
   "paper_quote": "By interleaving four PEs in a round-robin manner, the cluster sustains one product per cycle in steady state, keeping the shared accumulato…"
  },
  {
   "limitation_id": "flexposit-gap-M09-A03",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求共享以去除冗余累加逻辑；RTL 明确复制累加器，与前提相反。",
   "code_evidence": [
    "hardware/README.md:3-9",
    "hardware/rtl/fp8_pe_mac_stream.v:497-621",
    "hardware/rtl/fp8_pe_mac_stream.v:31-80"
   ],
   "paper_quote": "This sharing removes redundant accumulation logic, reducing per-PE hardware cost and improving overall energy efficiency."
  },
  {
   "limitation_id": "flexposit-gap-M09-A04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求 4 PE 共享 1 累加器；RTL 为 1 PE : 1 累加器且簇大小非固定 4。",
   "code_evidence": [
    "hardware/rtl/systolic_efficient.v:242-330",
    "hardware/rtl/fp8_pe_mac_stream.v:497-621"
   ],
   "paper_quote": "Each MAC cluster contains four PEs sharing one accumulator, matching the minimum supported precision of 4 b."
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; merged (LLM: same issue): flexposit-gap-M09-B01, flexposit-gap-M09-B05-R02, flexposit-gap-M09-A03, flexposit-gap-M09-A04; priority 2: impl_deviates; related (candidate pair, judged different): flexposit-F011, flexposit-F019, flexposi…"
}
```

### 论文侧 · LLM 写出条件并求解：`flexposit-F018`

```json
{
 "finding_id": "flexposit-F018",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "同 local_entry：RTL 分槽写入而非一起推入。",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "cycle0 and re",
  "path_prefix": [
   "not stall"
  ],
  "trigger": {
   "cycle0": true,
   "re": true,
   "stall": false
  },
  "contrast": {
   "cycle0": false,
   "re": true,
   "stall": false
  },
  "atoms": {
   "cycle0": {
    "kind": "input",
    "sort": "bool"
   },
   "re": {
    "kind": "input",
    "sort": "bool"
   },
   "stall": {
    "kind": "input",
    "sort": "bool"
   }
  },
  "code_locations": [
   "hardware/rtl/posit_decode_and_queue.v:339-384",
   "hardware/model/flexposit_rtl_exact.py:118-161"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "call_chain_status": "not_found",
  "location": "hardware/rtl/posit_decode_and_queue.v:339-384"
 },
 "limitations": [
  {
   "limitation_id": "flexposit-gap-M08-B08",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 RTL 路径 + hardware/model/flexposit_rtl_exact.py::decode_native_posit 参考模型 + hardware/tb 与 scripts/run_array_test.py 的 iverilo…",
   "effect_text": "同 local_entry：RTL 分槽写入而非一起推入。",
   "code_evidence": [
    "hardware/rtl/posit_decode_and_queue.v:339-384",
    "hardware/model/flexposit_rtl_exact.py:118-161"
   ],
   "paper_quote": "At completion, the decoder pushes the exponent, mantissa, and zero flag into the per-column FIFO together, forming one decoded weight."
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 2: impl_deviates"
}
```

### 论文侧 · not_implemented：`flexposit-F038`

```json
{
 "finding_id": "flexposit-F038",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求 4 并行 MAC/权重项；RTL 为单 PE 串行位乘。",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "hardware/rtl/fp8_pe_mac_stream.v:497-621"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The RTL module implements a single-PE bit-serial MAC unconditionally, so the paper's four-parallel-MAC-per-weig…",
  "call_chain_status": "not_found",
  "location": "hardware/rtl/fp8_pe_mac_stream.v:497-621"
 },
 "limitations": [
  {
   "limitation_id": "flexposit-gap-M09-A01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求 4 并行 MAC/权重项；RTL 为单 PE 串行位乘。",
   "code_evidence": [
    "hardware/rtl/fp8_pe_mac_stream.v:497-621"
   ],
   "paper_quote": "effectively performing four parallel MACs per weight and recovering the throughput loss to bit-serial execution"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; priority 3: not_implemented, other effect; related (candidate pair, judged different): flexposit-F010, flexposit-F011, flexposit-F020, flexposit-F039"
}
```

### 论文侧 · no_condition：`flexposit-F011`

```json
{
 "finding_id": "flexposit-F011",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求簇内 4 个 PE 各取一个不同 FP16 激活；RTL 中不同激活分布在不同行（每行一个），且激活为 FP8 而非 FP16。",
 "witness_hint": {
  "kind": "input_value",
  "status": "no_condition",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "hardware/README.md:3-9",
   "hardware/rtl/systolic_efficient.v:242-330",
   "hardware/rtl/fp8_pe_mac_stream.v:497-621"
  ],
  "note": "not decided by input values: The mismatch (FP8 vs FP16 activations, one activation per row vs four distinct per cluster) is a fixed RTL/design difference, not determined by any input value in the sho…",
  "call_chain_status": "not_found",
  "location": "hardware/README.md:3-9"
 },
 "limitations": [
  {
   "limitation_id": "flexposit-gap-M09-B02-R02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: hardware/ 测试芯片 RTL 路径：hardware/rtl/systolic_efficient.v（N×N PE 阵列、cycle_gen 精度窗口、行延迟）、hardware/rtl/fp8_pe_mac_stream.v（PE 计算 + …",
   "effect_text": "论文要求簇内 4 个 PE 各取一个不同 FP16 激活；RTL 中不同激活分布在不同行（每行一个），且激活为 FP8 而非 FP16。",
   "code_evidence": [
    "hardware/README.md:3-9",
    "hardware/rtl/systolic_efficient.v:242-330",
    "hardware/rtl/fp8_pe_mac_stream.v:497-621"
   ],
   "paper_quote": "while processing four distinct FP16 activations"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 2: impl_deviates; related (candidate pair, judged different): flexposit-F010, flexposit-F012, flexposit-F020, flexposit-F038, flexposit-F039"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### flexposit（41 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved |  | `src/flexposit/api.py:120-121` | When True: raise FileNotFoundError(f'No sensitivity CSV {str(name_or_path)!r}: not a file, and not … |
| F002 | 代 | undisclosed | 1 | reject | solved |  | `src/flexposit/api.py:189` | When state.total_windows == 0: Quantize aborts if no sensitivity rows match the model's layer names… |
| F003 | 代 | undisclosed | 1 | reject | solved |  | `src/flexposit/export.py:40` | When not torch.equal(table[pos], mag): posit_encode raises ValueError if the scaled weights are not… |
| F004 | 合 | undisclosed | 1 | reject | solved |  | `src/flexposit/export.py:135` | When scale.min() < -16 or scale.max() > 15: export_tile raises ValueError when the per-column scale… |
| F005 | 代 | undisclosed | 1 | reject | solved |  | `src/flexposit/formats.py:39` | When not 2 <= nsize <= 16: posit_quantize (via _check_posit) rejects nsize outside [2,16], so the t… |
| F006 | 代 | undisclosed | 1 | reject | solved |  | `src/flexposit/formats.py:103` | When True: raise TypeError(f'posit_quantize expects a float32 tensor, got {x.dtype}') |
| F007 | 代 | undisclosed | 1 | reject | solved |  | `src/flexposit/formats.py:156` | When True: raise ValueError(f'invalid rounding mode {rounding!r}') |
| F008 | 代 | undisclosed | 2 | path_change | solved |  | `src/flexposit/mpq/channel_window.py:283` | When strategy == "random": Random strategy shuffles candidates with the caller-seeded RNG, selectin… |
| F009 | 代 | undisclosed | 2 | path_change | solved |  | `src/flexposit/mpq/channel_window.py:571` | When args.downgrade: Caller flag downgrade switches Budget Mode to demote the least-sensitive windo… |
| F010 | 论 | impl_deviates | 2 | other | always |  | `hardware/README.md:3-9` | 论文要求 4 PE 共享 1 个 FP16 累加器；RTL 为每 PE 独立块浮点累加器（ACC_MANW=12, GRS=3，非 FP16 格式），无时分复用。 |
| F011 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/README.md:3-9` | 论文要求簇内 4 个 PE 各取一个不同 FP16 激活；RTL 中不同激活分布在不同行（每行一个），且激活为 FP8 而非 FP16。 |
| F012 | 论 | impl_deviates | 2 | other | always |  | `hardware/README.md:3-9` | 论文要求 FP16 激活与全浮点域 MAC；RTL 激活为 FP8 且累加为块浮点整数尾数，非逐项浮点累加。 |
| F013 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/rtl/fp8_pe_mac_stream.v:395-423` | 同 local_entry：cyc2 用符号位与未右移的 A |
| F014 | 论 | impl_deviates | 2 | other | solved |  | `hardware/rtl/fp8_pe_mac_stream.v:452-490` | 同 local_entry |
| F015 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/rtl/posit_decode_and_queue.v:136-183` | 同 local_entry：符号 FIFO 写入在 cyc1 而非 cyc0。 |
| F016 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/rtl/posit_decode_and_queue.v:218-281` | 论文要求 cyc0 推入符号项；代码在 cyc1 写符号、cyc0 写零标志与 exp/man |
| F017 | 论 | impl_deviates | 2 | other | solved |  | `hardware/rtl/posit_decode_and_queue.v:218-279` | 同 local_entry：以固定位宽上限而非 cycP 终止尾数收集。 |
| F018 | 论 | impl_deviates | 2 | other | solved |  | `hardware/rtl/posit_decode_and_queue.v:339-384` | 同 local_entry：RTL 分槽写入而非一起推入。 |
| F019 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/rtl/systolic_efficient.v:198-240` | 论文的“轮流完成、无停顿”依赖共享累加器时分复用；RTL 无共享，且存在全局 stall 背压路径。 |
| F020 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/rtl/systolic_efficient.v:242-330` | 论文要求簇内 4 个 PE 同周期共享同一解码权重项；RTL 中同列相邻 PE 收到同一权重项但相差 1 周期，且不存在“簇内 4 PE 同周期”结构。 |
| F021 | 论 | impl_deviates | 2 | other | no_condition |  | `hardware/rtl/systolic_efficient.v:411-512` | 同 local_entry：写出受 out_ready 背压与一拍填充延迟约束，非无停顿。 |
| F022 | 论 | impl_deviates | 2 | other | always |  | `scripts/regen_sensitivity_ppl.sh:8-33` | 同 local_entry：符号与 Algorithm 2 第6行相反。 |
| F023 | 论 | impl_deviates | 2 | other | always |  | `src/flexposit/export.py:105-141` | 论文要求激活保持 FP16；硬件导出/仿真路径把激活转成 FP8 E4M3。 |
| F024 | 论 | impl_deviates | 2 | other | solved |  | `src/flexposit/sensitivity/ppl_probe.py:72-75` | 论文要求窗口为阵列列数整数倍；脚本默认256（16列整数倍）但模块默认64，且无对齐校验（E4,E5,E6） |
| F025 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/api.py:149` | When r[0] not in valid_layers: Sensitivity rows for layers not present in the model are silently dr… |
| F026 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/api.py:153` | When span == 0: If upgrade_nsize equals base_nsize (span zero), the upgrade fraction silently becom… |
| F027 | 代 | docs_only | 3 | path_change | solved |  | `src/flexposit/api.py:181` | When config.bits > config.base_nsize: When bits exceeds base_nsize the code requires a sensitivity … |
| F028 | 代 | docs_only | 3 | reject | solved |  | `src/flexposit/api.py:183-186` | When True: raise ValueError(f"bits={config.bits} needs a sensitivity ranking to decide which channe… |
| F029 | 代 | docs_only | 3 | other | solved |  | `src/flexposit/core.py:35` | When isinstance(es, int): A scalar es disables the per-channel es search (single candidate), while … |
| F030 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/core.py:37` | When all(int(e) > max_es for e in cands): If every caller-supplied es candidate exceeds nsize-1, th… |
| F031 | 代 | docs_only | 3 | reject | solved |  | `src/flexposit/export.py:131` | When len(sizes) != 1: export_tile raises ValueError when the selected output channels span more tha… |
| F032 | 代 | docs_only | 3 | other | solved |  | `src/flexposit/formats.py:29` | When _BACKEND == "qtorch": Module-level env var read at import time selects the posit/float quantiz… |
| F033 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/mpq/channel_window.py:136` | When all(e > max_es for e in es_cands): If every caller-supplied es candidate exceeds nsize-1, the … |
| F034 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/mpq/channel_window.py:161` | When start >= end: A window whose clamped start is not less than its end returns the weight unchang… |
| F035 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/mpq/channel_window.py:205` | When not (is_quant_linear(mod) and hasattr(mod, "weight") and mod.weight is not None and mod.weight… |
| F036 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/mpq/channel_window.py:208` | When key not in ref_sd: A layer named in the sensitivity windows but absent from the FP32 reference… |
| F037 | 代 | undisclosed | 3 | other | solved |  | `src/flexposit/mpq/channel_window.py:256` | When dp >= 0.0 and not allow_positive: When allow_positive is False, windows with non-negative delt… |
| F038 | 论 | not_implemented | 3 | other | always |  | `hardware/rtl/fp8_pe_mac_stream.v:497-621` | 论文要求 4 并行 MAC/权重项；RTL 为单 PE 串行位乘。 |
| F039 | 论 | not_implemented | 3 | other | solved |  | `hardware/rtl/systolic_efficient.v:198-240` | 论文的 4/P 依赖 4-PE 簇并行；RTL 每 PE 为 1/P，簇级 4/P 未被实现。 |
| F040 | 论 | not_implemented | 3 | other | always |  | `scripts/regen_sensitivity_ppl.sh:8-33` | 剖析实验路径未产出论文要求的降序排序敏感度图。 |
| F041 | 论 | not_implemented | 3 | other | always |  | `src/flexposit/sensitivity/ppl_probe.py:72-75` | 论文要求 Qwen 1024；脚本与模块均无 Qwen→1024 规则（E4,E5,E6） |
