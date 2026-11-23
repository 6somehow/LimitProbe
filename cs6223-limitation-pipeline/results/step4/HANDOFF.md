# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；7 篇）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

7 篇论文共 **439 条 limitation**（Code side + Paper side），去重后是 **380 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/limitations_for_tests.json`。

## 1. 两侧的 limitation 有什么不同

| | Code side（Wanting，步骤 2 + 3b） | Paper side（Zhaopeng，步骤 1 + 3a） |
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

| 论文 | Code side | Paper side | Merged | Total |
|---|---|---|---|---|
| flexposit | 21 | 19 | 1 | 41 |
| flexprefill | 46 | 19 | 0 | 65 |
| infinigen | 20 | 11 | 0 | 31 |
| minference | 50 | 23 | 0 | 73 |
| nnsmith | 33 | 3 | 2 | 38 |
| qoserve | 12 | 36 | 2 | 50 |
| sparta | 2 | 79 | 1 | 82 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | paper_hypothesis | Total |
|---|---|---|---|---|---|---|---|---|---|
| Code side | 163 | 1 | 8 | 11 | 1 | 0 | 0 | 0 | 184 |
| Paper side | 0 | 0 | 0 | 0 | 0 | 112 | 78 | 0 | 190 |
| Merged | 4 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 6 |

| 类别 | 意思 |
|---|---|
| `undisclosed` | The code has this limitation, but no user-facing source documents it (core finding) |
| `contradicts_docs` | The documentation contradicts the code behavior |
| `stated_differently` | The documentation states a different or weaker boundary (e.g. “only tested bf16” vs code requiring bf16) |
| `docs_only` | The README / public docstring states it, but the paper does not |
| `paper_stated` | The paper states it with the same boundary as the code |
| `impl_deviates` | The implementation differs from the paper |
| `not_implemented` | The paper describes it, but the code does not implement it |
| `paper_hypothesis` | A hypothesis proposed by Swarm from paper evidence |

按 priority（1 = 先测）：

| 来源 | p1 | p2 | p3 | Total |
|---|---|---|---|---|
| Code side | 45 | 65 | 74 | 184 |
| Paper side | 0 | 111 | 79 | 190 |
| Merged | 1 | 5 | 0 | 6 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | Total |
|---|---|---|---|---|---|---|---|---|
| Code side | 62 | 71 | 6 | 0 | 0 | 0 | 45 | 184 |
| Paper side | 0 | 0 | 0 | 0 | 0 | 0 | 190 | 190 |
| Merged | 2 | 1 | 0 | 0 | 0 | 0 | 3 | 6 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | Total |
|---|---|---|---|---|---|---|---|---|---|
| Code side | 172 | 0 | 0 | 0 | 12 | 0 | 0 | 0 | 184 |
| Paper side | 51 | 0 | 1 | 116 | 1 | 0 | 0 | 21 | 190 |
| Merged | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分Code side条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | Total |
|---|---|---|---|---|---|
| Code side | 27 | 40 | 13 | 104 | 184 |
| Paper side | 0 | 0 | 0 | 190 | 190 |
| Merged | 2 | 0 | 0 | 4 | 6 |

## 3. 一条记录里有什么

`limitations_for_tests.json` 的结构是 `{schema_version, witness_format, rules, note, findings: [...]}`。`findings` 里每条记录的字段如下：

| 字段 | 内容 | 测试时怎么用 |
|---|---|---|
| `finding_id` | `<论文>-F###`，在一篇论文内按 priority 排序 | TestCase.finding_id 填它 |
| `category` | 见上表 | 区分文档、实现和论文假设 |
| `priority` | 1 / 2 / 3 | 先测 1 |
| `effect_type` | reject / path_change / state / … | 决定 oracle，见第 5 节 |
| `summary` | 一句话：什么条件下会怎样，附位置 | 给人看 |
| `witness_hint` | 触发点、对照点和各名字的含义，见第 4 节 | 构造测试输入 |
| `scope_status` | 是否在论文声明的范围内；目前几乎都是 unknown（Paper side参数映射很少） | out_of_scope 的不计入主结果 |
| `review` / `review_note` | worth_testing / real_but_minor / wrong / unreviewed，以及是谁审的、理由 | wrong 的可以跳过 |
| `rationale` | 分类依据、合并了谁、priority 的理由，以及判为“相关但不同”的其他 Finding | 查原因 |
| `limitation_ids` / `limitations` | 背后的完整 Limitation 记录（两侧都可能有） | 看原始条件、论文原文和代码位置 |
| `verification_ids` / `verifications` | Code side的 3b 结果：在哪里找到了说明、原文 | 判断“文档到底怎么写的” |
| `confidence` | 目前全部是 llm_assisted | — |
| `process_confidence` | Code side的静态证据：8 项检查的状态、重复测量、预测的测试档位上限、重要性数字（没有自己的档位），见第 6 节；纯Paper side的 Finding 为 null | 作为你定档的输入；不是测试结论 |

注意：Paper side原始记录的 `effect_text` 有一部分写的是“同上……”，指的是 3a 同一条记录的 local_entry 描述。Finding 的 `summary` 已经展开，`limitations` 里保留原样。

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
| always | Paper side：每次走到引用代码都会出现 | 任意走到 `code_locations` 的输入 |
| infeasible | 条件和路径前缀矛盾，从入口走不到。`infeasible_because: call_chain` 表示是把被调函数的名字换成入口函数的名字之后才矛盾的（见下面“调用链”） | 已降为 p3，不用花预算 |
| no_condition | Paper side：没有可用条件 | 读 `note` 和 summary，人工判断 |
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
- Paper side条件由 LLM 写出，只核对过“名字都出现在引用的代码里”，**语义不一定对**，要当提示用。
- 所有值都没有实际执行验证过。

## 5. 按 effect 选 oracle（建议）

| effect_type | 意思 | 建议的 oracle |
|---|---|---|
| reject | Raises an exception / fails an assertion | Assert that trigger raises the specified exception and contrast does not |
| path_change | Changes execution path (fallback, kernel, or strategy) | path hook: instrument both path entries; trigger takes the limited branch and contrast does not |
| accuracy | Reduced result accuracy | differential: compare with a reference implementation; trigger error exceeds the threshold |
| state | Depends on state left by previous calls | event_sequence: call in order to establish the trigger state, then check |
| resource / performance | Memory / time | resource: measure and compare with contrast |
| other (almost all paper-side findings) | The implementation differs from the paper, with no established runtime consequence | When witness is always: use any input that reaches the cited code and compare with the paper formula / description using differential or metamorphic tests; 3a made only a static judgment; the consequence is unconfirmed |

## 6. Code side的静态证据（未校准，没有自己的档位）

每条有Code side记录的 Finding 带一个 `process_confidence` 块（格式 `process-confidence-v2`，规则见 `docs/11_process_confidence.md`）。它是对你的档位的补充：**Code side不定档，档位只由你的测试证据决定**。不执行代码、不调模型，同样的输入得到同样的结果。块里有四部分。

**1. `checks`：核对表。** 词汇和你的 defeater 表一样：`eliminated`（工具核对过）、`residual`（只有论证或模型判断）、`open`（没评估）、`refuted`（核对失败）。

| 检查 | 对应的测试概念 | 对应你的 | `eliminated` 的条件 |
|---|---|---|---|
| C1 location | 输入有效性 | D12 | 固定 commit 下该行的语句就是记录的 snippet |
| C2 condition | 语句的判定（decision） | D2 | 条件就是该语句的判定表达式或它的取反 |
| C3 reachability | 可达性（RIPR 的 R） | D1、D14 | 从官方入口到目标有静态调用链，且没有靠猜的步骤 |
| C4 feasibility | 不可行路径 | witness | z3 在完整路径前缀下找到触发点和对照点 |
| C5 extraction | 分析的可重复性 | D8 | 静态路线找到，或 LLM 路线在全部抽取运行里都找到（同一文件同一行） |
| C6 effect_label | oracle 与语句相符 | D4、效果类型 | 标注的效果能在该语句上判定（reject 要能抛异常，path_change 要是 if / while） |
| C7 documentation | 缺失性断言，只作说明 | — | 3b 找到了原文；not_found 无法证明，为 residual；3 次重复不一致也为 residual |
| C8 review | 审查（inspection） | — | 人工审过；LLM 盲审为 residual，没审为 open |

**2. `repeats`：重复测量。** `extraction_runs`：这个位置在几次抽取运行里出现（`found_in` / `of`）；`documentation_check`：3b 重复几次、结果的一致率；`routes`：哪条路线找到的（`ast` 静态、`llm`）。

**3. `testability`：预测你这边能测到哪一档。** 按你的规则推出来的上限，不是预报，实际可以更低。

| 字段 | 含义 |
|---|---|
| `testable: false` + `expect_not_run` | C4 为 refuted 预计 `witness_unusable`；效果是 `other` 预计 `outcome_unsupported` |
| `mutants` / `mutants_needed` | 用你的 `mutate.generate` 在目标行能造出几个变异体；少于 `n_min`（4）时 D3 消不掉 |
| `ceiling` | `L1`：变异体不够；`L2`：没有调用链，D14 最多 residual；`L3`：静态上没有限制 |
| `limited_by` | 卡在哪个 defeater，原因是什么 |
| `condition_has_calls`、`integer_boundary` | 条件里有没有函数调用（影响 D2 能否直接求值）；边界变量是否都是整数（影响 D5 的邻点） |

和已有测试报告对照（7 篇里测过的 130 条）：**没有一条的实际档位超过预测上限**，98 条正好等于上限；预计 `outcome_unsupported` 的 48 条、`witness_unusable` 的 12 条全部对上。这是在同一批数据上看的，不是独立验证。

**4. `importance`：重要性，和把握分开。**

- `path.decision_on`：`main` 每次调用都会求值这个判定；`side` 判定在某个 `if` / `except` / `case` 里面（自己函数里的见 `enclosing_conditions`，调用链上的见 `conditional_call_sites`）；`unknown` 没有调用链，看不到调用者。
- `impact`：判定管住多少语句（分支体，或 assert / raise 之后函数里剩下的语句）、函数共多少语句、从入口来的调用链条数、仓库里解析到这个函数的调用点数。
- `coverage`：目标函数里有多少个判定（if / while / assert）、Code side列出了几个、入口能否静态到达这个函数。这是**分析的覆盖**，不是执行覆盖；执行覆盖在你的 `execution_report.json` 里。

**建议的用法**：测之前按 `ceiling` 分配预算（`测不了` 的不测，`L1` 的少花时间）；测之后把 `limited_by` 放在档位旁边，说明是这句本身测不到更高还是测得不够；没测的 Finding 把 `checks` 和 `repeats` 作为确定性的证据并排列出；`importance` 只用于排序，不进档位。

预测的测试档位上限：

| 论文 | 测不了 | L1 | L2 | L3 | 没测量 | Total |
|---|---|---|---|---|---|---|
| flexposit | 10 | 10 | 1 | 1 | 0 | 22 |
| flexprefill | 17 | 14 | 4 | 11 | 0 | 46 |
| infinigen | 1 | 13 | 6 | 0 | 0 | 20 |
| minference | 13 | 26 | 1 | 10 | 0 | 50 |
| nnsmith | 13 | 20 | 0 | 2 | 0 | 35 |
| qoserve | 5 | 4 | 0 | 5 | 0 | 14 |
| sparta | 1 | 1 | 1 | 0 | 0 | 3 |

判定在主路径还是侧路径：

| 论文 | main | side | unknown | Total |
|---|---|---|---|---|
| flexposit | 7 | 7 | 8 | 22 |
| flexprefill | 10 | 24 | 12 | 46 |
| infinigen | 2 | 15 | 3 | 20 |
| minference | 16 | 21 | 10 | 50 |
| nnsmith | 4 | 19 | 10 | 35 |
| qoserve | 6 | 6 | 2 | 14 |
| sparta | 0 | 1 | 2 | 3 |

## 7. 典型例子

每个例子是一条 Finding 的精简版，长字段已截断；完整内容在 json 里。例子是按规则自动挑的第一条，不是挑好看的。“Paper side · LLM 写出条件”那条正好说明了它的局限：条件在形式上能解，但不一定抓住了论文差异的本质，所以Paper side条件只当提示用。

### Code side · undisclosed · p1 · 有别名：`flexprefill-F015`

```json
{
 "finding_id": "flexprefill-F015",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "real_but_minor",
 "summary": "When q_len != k_len: Rejects inputs where query and key sequence lengths differ, so no cross-length (e.g. decode-style) attention is supported. (flex_prefill/ops/vertical_slash_attention.py:265)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "q_len != k_len",
  "path_prefix": [],
  "aliases": {
   "q_len": "q.shape[1]",
   "k_len": "k.shape[1]"
  },
  "trigger": {
   "q_len": 1,
   "k_len": 2,
   "q.shape[1]": 1,
   "k.shape[1]": 2
  },
  "contrast": {
   "q_len": 2,
   "k_len": 2,
   "q.shape[1]": 2,
   "k.shape[1]": 2
  },
  "atoms": {
   "k.shape[1]": {
    "kind": "derived",
    "sort": "int"
   },
   "k_len": {
    "kind": "local",
    "sort": "int"
   },
   "q.shape[1]": {
    "kind": "derived",
    "sort": "int"
   },
   "q_len": {
    "kind": "local",
    "sort": "int"
   }
  },
  "call_chain_status": "not_found",
  "location": "flex_prefill/ops/vertical_slash_attention.py:265"
 },
 "limitations": [
  {
   "limitation_id": "CL-B013",
   "origin": "code",
   "condition_text": "q_len != k_len",
   "effect_text": "Rejects inputs where query and key sequence lengths differ, so no cross-length (e.g. decode-style) attention is supported.",
   "code_evidence": [
    "flex_prefill/ops/vertical_slash_attention.py:265-265"
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
 "rationale": "3b: not_found; priority 1: undisclosed, reject effect, witness reaches it",
 "process_confidence": {
  "checks": {
   "C1": "eliminated",
   "C2": "eliminated",
   "C3": "open",
   "C4": "eliminated",
   "C5": "eliminated",
   "C6": "eliminated",
   "C7": "residual",
   "C8": "residual"
  },
  "found_in_runs": 3,
  "ceiling": "L1",
  "limited_by": [
   "D3: 2 mutant(s) of the target line, fewer than n_min=4; it cannot be eliminated",
   "D14: no call chain from an official entry; a test has to call a deeper function, at most residual"
  ],
  "decision_on": "unknown",
  "guarded_statements": 18,
  "note": "... evidence per check and the full numbers are in the json"
 }
}
```

### Code side · stated_differently（文档说得比代码弱）：`flexprefill-F027`

```json
{
 "finding_id": "flexprefill-F027",
 "category": "stated_differently",
 "priority": 2,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "real_but_minor",
 "summary": "When q.dtype != torch.bfloat16: Rejects any query tensor not in bfloat16, so callers using fp16/fp32 cannot run this kernel. (flex_prefill/ops/vertical_slash_attention.py:264)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "q.dtype != torch.bfloat16",
  "path_prefix": [],
  "trigger": {
   "q.dtype": {
    "not_in": [
     "torch.bfloat16"
    ]
   }
  },
  "contrast": {
   "q.dtype": "torch.bfloat16"
  },
  "atoms": {
   "q.dtype": {
    "kind": "category",
    "sort": "str"
   }
  },
  "call_chain_status": "not_found",
  "location": "flex_prefill/ops/vertical_slash_attention.py:264"
 },
 "limitations": [
  {
   "limitation_id": "CL-B012",
   "origin": "code",
   "condition_text": "q.dtype != torch.bfloat16",
   "effect_text": "Rejects any query tensor not in bfloat16, so callers using fp16/fp32 cannot run this kernel.",
   "code_evidence": [
    "flex_prefill/ops/vertical_slash_attention.py:264-264"
   ],
   "paper_quote": null
  }
 ],
 "verifications": [
  {
   "result": "weaker",
   "documented_in": [
    "readme"
   ],
   "quote": "Note: The current version only supports inference with a batch size of 1 and has only been tested with bfloat16 precisi…"
  }
 ],
 "rationale": "3b: weaker in readme; 3b weaker; priority 2: stated_differently",
 "process_confidence": {
  "checks": {
   "C1": "eliminated",
   "C2": "eliminated",
   "C3": "open",
   "C4": "eliminated",
   "C5": "eliminated",
   "C6": "eliminated",
   "C7": "eliminated",
   "C8": "residual"
  },
  "found_in_runs": 3,
  "ceiling": "L1",
  "limited_by": [
   "D3: 2 mutant(s) of the target line, fewer than n_min=4; it cannot be eliminated",
   "D14: no call chain from an official entry; a test has to call a deeper function, at most residual"
  ],
  "decision_on": "unknown",
  "guarded_statements": 19,
  "note": "... evidence per check and the full numbers are in the json"
 }
}
```

### Code side · docs_only（README / docstring 写了，论文没写）：`flexposit-F027`

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
 "rationale": "3b: found in docstring; priority 3: docs_only, path_change effect",
 "process_confidence": {
  "checks": {
   "C1": "eliminated",
   "C2": "eliminated",
   "C3": "eliminated",
   "C4": "eliminated",
   "C5": "residual",
   "C6": "eliminated",
   "C7": "eliminated",
   "C8": "open"
  },
  "found_in_runs": null,
  "ceiling": "L1",
  "limited_by": [
   "D3: 2 mutant(s) of the target line, fewer than n_min=4; it cannot be eliminated"
  ],
  "decision_on": "main",
  "guarded_statements": 6,
  "note": "... evidence per check and the full numbers are in the json"
 }
}
```

### Code side · state（事件序列）：`flexprefill-F012`

```json
{
 "finding_id": "flexprefill-F012",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "state",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When causal_mask is None  # first call only: module-level cache initialised on first call and reused (flex_prefill/ops/flex_prefill_attention.py:1695)",
 "witness_hint": {
  "kind": "event_sequence",
  "status": "solved",
  "condition": "causal_mask is None  # first call only",
  "path_prefix": [
   "batch_size == 1",
   "not (q_len == 1)",
   "q.shape[1] == k.shape[1]",
   "head_dim in {16, 32, 64, 128}",
   "block_size in {16, 32, 64, 128}",
   "not (q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size))"
  ],
  "aliases": {
   "q_len": "q.shape[1]"
  },
  "entry_terms": {
   "path_prefix": {
    "batch_size == 1": "k.shape[0] == 1",
    "not q_len == 1": "not q.shape[1] == 1",
    "head_dim in {16, 32, 64, 128}": "k.shape[3] in {16, 32, 64, 128}"
   },
   "names": {
    "q_len": "q.shape[1]"
   }
  },
  "trigger": {
   "causal_mask is None": true,
   "batch_size": 1,
   "q_len": 385,
   "q.shape[1]": 385,
   "k.shape[1]": 385,
   "head_dim": 16,
   "block_size": 128,
   "min_budget": 318,
   "k.shape[0]": 1,
   "k.shape[3]": 64
  },
  "contrast": {
   "causal_mask is None": false,
   "batch_size": 1,
   "q_len": 385,
   "q.shape[1]": 385,
   "k.shape[1]": 385,
   "head_dim": 16,
   "block_size": 128,
   "min_budget": 318,
   "k.shape[0]": 1,
   "k.shape[3]": 64
  },
  "atoms": "... 10 atoms, see json",
  "call_chain_status": "resolved",
  "call_chain": [
   "flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention",
   "flex_prefill/ops/flex_prefill_attention.py::get_active_blocks"
  ],
  "location": "flex_prefill/ops/flex_prefill_attention.py:1695-1698"
 },
 "limitations": [
  {
   "limitation_id": "CL-X008",
   "origin": "code",
   "condition_text": "causal_mask is None # first call only",
   "effect_text": "module-level cache initialised on first call and reused",
   "code_evidence": [
    "flex_prefill/ops/flex_prefill_attention.py:1695-1698"
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
 "rationale": "3b: not_found; priority 1: undisclosed, state effect, witness reaches it; related (candidate pair, judged different): flexprefill-F031, flexprefill-F032, flexprefill-F033, flexprefill-F034",
 "process_confidence": {
  "checks": {
   "C1": "eliminated",
   "C2": "eliminated",
   "C3": "eliminated",
   "C4": "eliminated",
   "C5": "eliminated",
   "C6": "eliminated",
   "C7": "residual",
   "C8": "open"
  },
  "found_in_runs": 3,
  "ceiling": "L1",
  "limited_by": [
   "D3: 1 mutant(s) of the target line, fewer than n_min=4; it cannot be eliminated"
  ],
  "decision_on": "main",
  "guarded_statements": 3,
  "note": "... evidence per check and the full numbers are in the json"
 }
}
```

### Code side · infeasible（多半走不到，p3）：`qoserve-F038`

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

### Merged：`flexposit-F004`

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
 "rationale": "3b: not_found; merged (LLM: same issue): flexposit-gap-M01-B08; paper side also reports: impl_deviates; priority 1: undisclosed, reject effect, witness reaches it; related (candidate pair, judged different): flexposit-F023, flexposit-F031",
 "process_confidence": {
  "checks": {
   "C1": "eliminated",
   "C2": "eliminated",
   "C3": "open",
   "C4": "eliminated",
   "C5": "residual",
   "C6": "eliminated",
   "C7": "residual",
   "C8": "open"
  },
  "found_in_runs": null,
  "ceiling": "L2",
  "limited_by": [
   "D14: no call chain from an official entry; a test has to call a deeper function, at most residual"
  ],
  "decision_on": "unknown",
  "guarded_statements": 1,
  "note": "... evidence per check and the full numbers are in the json"
 }
}
```

### Paper side · impl_deviates · always：`flexposit-F010`

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

### Paper side · LLM 写出条件并求解：`flexposit-F018`

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

### Paper side · not_implemented：`flexposit-F038`

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

### Paper side · no_condition：`flexposit-F011`

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

## 8. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（Code side / Paper side / Merged）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）；过程 = 过程置信度档位和判定所在路径（第 6 节；Paper side为空）。

### flexposit（41 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved |  | L1 side | `src/flexposit/api.py:120-121` | When True: raise FileNotFoundError(f'No sensitivity CSV {str(name_or_path)!r}: not a file, and not … |
| F002 | 代 | undisclosed | 1 | reject | solved |  | L1 side | `src/flexposit/api.py:189` | When state.total_windows == 0: Quantize aborts if no sensitivity rows match the model's layer names… |
| F003 | 代 | undisclosed | 1 | reject | solved |  | L1 unknown | `src/flexposit/export.py:40` | When not torch.equal(table[pos], mag): posit_encode raises ValueError if the scaled weights are not… |
| F004 | 合 | undisclosed | 1 | reject | solved |  | L2 unknown | `src/flexposit/export.py:135` | When scale.min() < -16 or scale.max() > 15: export_tile raises ValueError when the per-column scale… |
| F005 | 代 | undisclosed | 1 | reject | solved |  | L3 main | `src/flexposit/formats.py:39` | When not 2 <= nsize <= 16: posit_quantize (via _check_posit) rejects nsize outside [2,16], so the t… |
| F006 | 代 | undisclosed | 1 | reject | solved |  | L1 main | `src/flexposit/formats.py:103` | When True: raise TypeError(f'posit_quantize expects a float32 tensor, got {x.dtype}') |
| F007 | 代 | undisclosed | 1 | reject | solved |  | L1 main | `src/flexposit/formats.py:156` | When True: raise ValueError(f'invalid rounding mode {rounding!r}') |
| F008 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `src/flexposit/mpq/channel_window.py:283` | When strategy == "random": Random strategy shuffles candidates with the caller-seeded RNG, selectin… |
| F009 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `src/flexposit/mpq/channel_window.py:571` | When args.downgrade: Caller flag downgrade switches Budget Mode to demote the least-sensitive windo… |
| F010 | 论 | impl_deviates | 2 | other | always |  |  | `hardware/README.md:3-9` | 论文要求 4 PE 共享 1 个 FP16 累加器；RTL 为每 PE 独立块浮点累加器（ACC_MANW=12, GRS=3，非 FP16 格式），无时分复用。 |
| F011 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/README.md:3-9` | 论文要求簇内 4 个 PE 各取一个不同 FP16 激活；RTL 中不同激活分布在不同行（每行一个），且激活为 FP8 而非 FP16。 |
| F012 | 论 | impl_deviates | 2 | other | always |  |  | `hardware/README.md:3-9` | 论文要求 FP16 激活与全浮点域 MAC；RTL 激活为 FP8 且累加为块浮点整数尾数，非逐项浮点累加。 |
| F013 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/rtl/fp8_pe_mac_stream.v:395-423` | 同 local_entry：cyc2 用符号位与未右移的 A |
| F014 | 论 | impl_deviates | 2 | other | solved |  |  | `hardware/rtl/fp8_pe_mac_stream.v:452-490` | 同 local_entry |
| F015 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/rtl/posit_decode_and_queue.v:136-183` | 同 local_entry：符号 FIFO 写入在 cyc1 而非 cyc0。 |
| F016 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/rtl/posit_decode_and_queue.v:218-281` | 论文要求 cyc0 推入符号项；代码在 cyc1 写符号、cyc0 写零标志与 exp/man |
| F017 | 论 | impl_deviates | 2 | other | solved |  |  | `hardware/rtl/posit_decode_and_queue.v:218-279` | 同 local_entry：以固定位宽上限而非 cycP 终止尾数收集。 |
| F018 | 论 | impl_deviates | 2 | other | solved |  |  | `hardware/rtl/posit_decode_and_queue.v:339-384` | 同 local_entry：RTL 分槽写入而非一起推入。 |
| F019 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/rtl/systolic_efficient.v:198-240` | 论文的“轮流完成、无停顿”依赖共享累加器时分复用；RTL 无共享，且存在全局 stall 背压路径。 |
| F020 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/rtl/systolic_efficient.v:242-330` | 论文要求簇内 4 个 PE 同周期共享同一解码权重项；RTL 中同列相邻 PE 收到同一权重项但相差 1 周期，且不存在“簇内 4 PE 同周期”结构。 |
| F021 | 论 | impl_deviates | 2 | other | no_condition |  |  | `hardware/rtl/systolic_efficient.v:411-512` | 同 local_entry：写出受 out_ready 背压与一拍填充延迟约束，非无停顿。 |
| F022 | 论 | impl_deviates | 2 | other | always |  |  | `scripts/regen_sensitivity_ppl.sh:8-33` | 同 local_entry：符号与 Algorithm 2 第6行相反。 |
| F023 | 论 | impl_deviates | 2 | other | always |  |  | `src/flexposit/export.py:105-141` | 论文要求激活保持 FP16；硬件导出/仿真路径把激活转成 FP8 E4M3。 |
| F024 | 论 | impl_deviates | 2 | other | solved |  |  | `src/flexposit/sensitivity/ppl_probe.py:72-75` | 论文要求窗口为阵列列数整数倍；脚本默认256（16列整数倍）但模块默认64，且无对齐校验（E4,E5,E6） |
| F025 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `src/flexposit/api.py:149` | When r[0] not in valid_layers: Sensitivity rows for layers not present in the model are silently dr… |
| F026 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `src/flexposit/api.py:153` | When span == 0: If upgrade_nsize equals base_nsize (span zero), the upgrade fraction silently becom… |
| F027 | 代 | docs_only | 3 | path_change | solved |  | L1 main | `src/flexposit/api.py:181` | When config.bits > config.base_nsize: When bits exceeds base_nsize the code requires a sensitivity … |
| F028 | 代 | docs_only | 3 | reject | solved |  | L1 side | `src/flexposit/api.py:183-186` | When True: raise ValueError(f"bits={config.bits} needs a sensitivity ranking to decide which channe… |
| F029 | 代 | docs_only | 3 | other | solved |  | 测不了 main | `src/flexposit/core.py:35` | When isinstance(es, int): A scalar es disables the per-channel es search (single candidate), while … |
| F030 | 代 | undisclosed | 3 | other | solved |  | 测不了 main | `src/flexposit/core.py:37` | When all(int(e) > max_es for e in cands): If every caller-supplied es candidate exceeds nsize-1, th… |
| F031 | 代 | docs_only | 3 | reject | solved |  | L1 unknown | `src/flexposit/export.py:131` | When len(sizes) != 1: export_tile raises ValueError when the selected output channels span more tha… |
| F032 | 代 | docs_only | 3 | other | solved |  | 测不了 main | `src/flexposit/formats.py:29` | When _BACKEND == "qtorch": Module-level env var read at import time selects the posit/float quantiz… |
| F033 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `src/flexposit/mpq/channel_window.py:136` | When all(e > max_es for e in es_cands): If every caller-supplied es candidate exceeds nsize-1, the … |
| F034 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `src/flexposit/mpq/channel_window.py:161` | When start >= end: A window whose clamped start is not less than its end returns the weight unchang… |
| F035 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `src/flexposit/mpq/channel_window.py:205` | When not (is_quant_linear(mod) and hasattr(mod, "weight") and mod.weight is not None and mod.weight… |
| F036 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `src/flexposit/mpq/channel_window.py:208` | When key not in ref_sd: A layer named in the sensitivity windows but absent from the FP32 reference… |
| F037 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `src/flexposit/mpq/channel_window.py:256` | When dp >= 0.0 and not allow_positive: When allow_positive is False, windows with non-negative delt… |
| F038 | 论 | not_implemented | 3 | other | always |  |  | `hardware/rtl/fp8_pe_mac_stream.v:497-621` | 论文要求 4 并行 MAC/权重项；RTL 为单 PE 串行位乘。 |
| F039 | 论 | not_implemented | 3 | other | solved |  |  | `hardware/rtl/systolic_efficient.v:198-240` | 论文的 4/P 依赖 4-PE 簇并行；RTL 每 PE 为 1/P，簇级 4/P 未被实现。 |
| F040 | 论 | not_implemented | 3 | other | always |  |  | `scripts/regen_sensitivity_ppl.sh:8-33` | 剖析实验路径未产出论文要求的降序排序敏感度图。 |
| F041 | 论 | not_implemented | 3 | other | always |  |  | `src/flexposit/sensitivity/ppl_probe.py:72-75` | 论文要求 Qwen 1024；脚本与模块均无 Qwen→1024 规则（E4,E5,E6） |

### flexprefill（65 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved | ✓ | L1 unknown | `flex_prefill/modules/patch.py:123` | When not isinstance(model, LlamaForCausalLM): Patching a non-LlamaForCausalLM model with a non-defa… |
| F002 | 代 | undisclosed | 1 | reject | solved |  | L1 unknown | `flex_prefill/modules/patch.py:241` | When not isinstance(model, Qwen2ForCausalLM): Patching a non-Qwen2ForCausalLM model with a non-defa… |
| F003 | 代 | undisclosed | 1 | reject | solved | ~ | L3 side | `flex_prefill/ops/flex_prefill_attention.py:247` | When num_q_heads % num_kv_heads != 0: GQA requires the number of query heads to be a multiple of KV… |
| F006 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `flex_prefill/ops/flex_prefill_attention.py:1240-1244` | When not (isinstance(block_idx, list) and isinstance(block_idx[0], list) and isinstance(block_idx[0… |
| F007 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `flex_prefill/ops/flex_prefill_attention.py:1245` | When not (len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads): AssertionError |
| F008 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `flex_prefill/ops/flex_prefill_attention.py:1256` | When not (num_block <= total_q_blocks * (total_q_blocks + 1) // 2): AssertionError |
| F009 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `flex_prefill/ops/flex_prefill_attention.py:1258` | When not (num_q_heads % num_kv_heads == 0): AssertionError |
| F012 | 代 | undisclosed | 1 | state | solved |  | L1 main | `flex_prefill/ops/flex_prefill_attention.py:1695-1698` | When causal_mask is None # first call only: module-level cache initialised on first call and reused |
| F013 | 代 | undisclosed | 1 | reject | solved |  | L3 main | `flex_prefill/ops/flex_prefill_attention.py:1836` | When not (q.shape[1] == k.shape[1]): AssertionError |
| F014 | 代 | undisclosed | 1 | reject | solved |  | L3 main | `flex_prefill/ops/flex_prefill_attention.py:1837` | When not (head_dim in {16, 32, 64, 128}): AssertionError |
| F015 | 代 | undisclosed | 1 | reject | solved | ~ | L1 unknown | `flex_prefill/ops/vertical_slash_attention.py:265` | When q_len != k_len: Rejects inputs where query and key sequence lengths differ, so no cross-length… |
| F016 | 代 | undisclosed | 1 | reject | solved | ~ | L2 unknown | `flex_prefill/ops/vertical_slash_attention.py:552` | When head_dim not in {16, 32, 64, 128}: Caller-supplied head_dim outside the fixed set aborts execu… |
| F017 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `flex_prefill/modules/patch.py:69` | When pattern == "minfer": For minfer, the config is loaded from a hard-coded JSON file chosen by cf… |
| F018 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 unknown | `flex_prefill/modules/patch.py:313` | When "llama" in model_name.lower(): Model class name selects which patch_*_attention implementation… |
| F019 | 代 | stated_differently | 2 | reject | solved | ✓ | L1 side | `flex_prefill/modules/patch.py:320` | When not ("llama" in model_name.lower() or "glm" in model_name.lower() or "qwen2" in model_name.low… |
| F020 | 代 | undisclosed | 2 | path_change | solved | ✓ | L2 side | `flex_prefill/modules/patch.py:424` | When kv_cache is None or prefill_meta.block_tables is None or prefill_meta.block_tables.numel() == … |
| F021 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `flex_prefill/modules/patch.py:501` | When "attention" in type(m).__name__.lower() and hasattr(m, "impl"): Only modules whose class name … |
| F022 | 代 | stated_differently | 2 | reject | solved | ✓ | L1 side | `flex_prefill/ops/flex_prefill_attention.py:672` | When q.dtype != torch.bfloat16: triton_flash_attention rejects non-bfloat16 queries before dispatch… |
| F023 | 代 | stated_differently | 2 | reject | solved |  | L1 side | `flex_prefill/ops/flex_prefill_attention.py:1218` | When not (q.dtype == torch.bfloat16): AssertionError |
| F024 | 代 | stated_differently | 2 | reject | solved |  | L3 side | `flex_prefill/ops/flex_prefill_attention.py:1222-1226` | When not (block_size in {32, 64, 128}): 'only support block size in {32, 64, 128} if head_dim <= 12… |
| F026 | 代 | undisclosed | 2 | path_change | solved |  | L3 main | `flex_prefill/ops/flex_prefill_attention.py:1842-1854` | When q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size): returns via fla… |
| F027 | 代 | stated_differently | 2 | reject | solved | ~ | L1 unknown | `flex_prefill/ops/vertical_slash_attention.py:264` | When q.dtype != torch.bfloat16: Rejects any query tensor not in bfloat16, so callers using fp16/fp3… |
| F028 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `flex_prefill/ops/vertical_slash_attention.py:557` | When seq_len <= min(vertical_size, slash_size) * block_size: For short sequences the sparse vertica… |
| F029 | 代 | undisclosed | 2 | path_change | solved | ~ | L2 unknown | `flex_prefill/ops/vertical_slash_attention.py:570` | When seq_len <= 16 * 1024: Sequence length selects between the vertical/slash Triton kernel (<=16k)… |
| F030 | 论 | impl_deviates | 2 | other | solved |  |  | `flex_prefill/ops/flex_prefill_attention.py:1588-1591` | 论文要求最小 k 使累计≥γ；代码取累计>γ 的最小 k（累计恰等于 γ 时多选一条），且 //128+1 放大、min/max_budget 覆盖，K_v 不再是论文定义的最小前缀（artifac… |
| F031 | 论 | impl_deviates | 2 | other | always |  |  | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | 论文要求先除以 Σ¯A 再展平；代码未归一化，改以放大阈值补偿 |
| F032 | 论 | impl_deviates | 2 | other | solved |  |  | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | 论文取累计和 ≥γ 的最小前缀长度 K；代码保留累计和 ≤γ*num_blocks 的项，边界条件与阈值尺度均不同，且未显式求 K |
| F033 | 论 | impl_deviates | 2 | other | always |  |  | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | 论文要求 S 为 Ia 前 K 项；代码把 query-aware 前缀与 vertical/slash 索引取并集，S 不是纯 Ia[1:K] |
| F034 | 论 | impl_deviates | 2 | other | always |  |  | `flex_prefill/ops/flex_prefill_attention.py:1676-1706` | 论文要求 pool(Q̂)（块池化，保留每块一个向量）与 pool(K) 相乘；代码把 Q̂ 的 block_size 行压成单一均值向量，得到 1×num_blocks 的分布，而非 num_bl… |
| F035 | 论 | impl_deviates | 2 | other | always |  |  | `flex_prefill/ops/flex_prefill_attention.py:1705-1716` | 池化内核无法表达论文二维 sumpool(softmax 矩阵)，实际 â 为列和向量 |
| F036 | 论 | impl_deviates | 2 | other | solved |  |  | `flex_prefill/ops/flex_prefill_attention.py:1707-1713` | 实验配置的 1024 预算未转化为每 head 最终激活 token 数下限，Query-Aware 头无下限 |
| F037 | 论 | impl_deviates | 2 | other | always |  |  | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | ā 角色正确；â 角色由 vertical 承担，但 vertical 非论文 sumpool(softmax(Q̂Kᵀ/√d)) 块和，真实分布操作数被替换（artifact 范围：â 操作数非论… |
| F038 | 论 | impl_deviates | 2 | other | always |  |  | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | 论文 Algorithm 2 以 JSD<τ 返回 pattern(query_specific/vertical_slash)；代码不返回模式，而用同一阈值改写预算并继续 vertical/sla… |
| F039 | 代 | docs_only | 3 | path_change | solved | ~ | L1 unknown | `flex_prefill/modules/patch.py:114` | When pattern == "default": For the default pattern, patch_llama_attention returns without patching,… |
| F040 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:88-96` | When not ('h100' in gpu_name) and not ('a100' in gpu_name) and not ('4090' in gpu_name): if head_la… |
| F004 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:865` | When not (q_len == 1): AssertionError |
| F041 | 代 | stated_differently | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:868` | When not (q.dtype == torch.bfloat16): AssertionError |
| F042 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:869` | When not (head_dim in {16, 32, 64, 128}): 'only support head_dim in {16, 32, 64, 128}' |
| F043 | 代 | docs_only | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:870-875` | When not (block_size in {16, 32, 64, 128}): 'only support block size in {16, 32, 64, 128}' |
| F044 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:876` | When not (num_blocks <= triton.cdiv(k_len, block_size)): AssertionError |
| F045 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:878` | When not (num_q_heads % num_kv_heads == 0): AssertionError |
| F005 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1219` | When not (q_len == k_len): AssertionError |
| F046 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1220` | When not (head_dim <= 256): 'only support head_dim <= 256' |
| F047 | 代 | undisclosed | 3 | other | solved | ✗ | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1221` | When head_dim <= 128: For head_dim <= 128 only block_size in {32,64,128} is allowed; otherwise (128… |
| F048 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1228-1231` | When not (block_size in {32, 64}): 'only support block size in {32, 64} if 128 < head_dim <= 256' |
| F049 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1270-1272` | When not (int(triton.__version__.split('.')[0]) >= 3): warnings.warn('triton version greater than 3… |
| F010 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1450` | When not (d in {16, 32, 64, 128}): AssertionError |
| F011 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `flex_prefill/ops/flex_prefill_attention.py:1451` | When not (kernel_size in {16, 32, 64, 128, 256, 512}): AssertionError |
| F050 | 代 | undisclosed | 3 | other | solved |  | 测不了 main | `flex_prefill/ops/flex_prefill_attention.py:1708` | When block_size != 128: hard-coded 128 in `score_cover_topk(vertical, gamma) // 128` while paramete… |
| F025 | 代 | undisclosed | 3 | other | solved |  | 测不了 main | `flex_prefill/ops/flex_prefill_attention.py:1727` | When kl_div < tau: per-element branch stored in block_sparse_mask |
| F051 | 代 | undisclosed | 3 | other | solved |  | 测不了 main | `flex_prefill/ops/flex_prefill_attention.py:1787` | When not (is_flash_attn_2_available()): flash_attn_func = triton_flash_attention |
| F052 | 代 | docs_only | 3 | reject | solved |  | L3 main | `flex_prefill/ops/flex_prefill_attention.py:1824` | When not (batch_size == 1): 'only support batch size 1 for now' |
| F053 | 代 | docs_only | 3 | path_change | solved |  | L1 main | `flex_prefill/ops/flex_prefill_attention.py:1825-1835` | When q_len == 1: returns via flash_attn_func, triton_flash_attention |
| F054 | 代 | docs_only | 3 | reject | solved |  | L3 main | `flex_prefill/ops/flex_prefill_attention.py:1838` | When not (block_size in {16, 32, 64, 128}): AssertionError |
| F055 | 代 | docs_only | 3 | reject | solved | ~ | L2 unknown | `flex_prefill/ops/vertical_slash_attention.py:553` | When block_size not in {16, 32, 64, 128}: Caller-supplied block_size outside the fixed set aborts e… |
| F056 | 论 | not_implemented | 3 | other | no_condition |  |  | `experiments/scripts/flex_prefill/ruler.sh:16-45` | 论文要求单卡 A100 80GB；脚本未固定设备数量或型号，accelerate 可多进程运行 |
| F057 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求的上界推导在实验路径无对应实现或检验 |
| F058 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求显式连续松弛步骤；代码无该步骤 |
| F059 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求构造 Lagrangian；代码无 |
| F060 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求 KKT 条件；代码无 |
| F061 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求该代数表达；代码无 |
| F062 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求陈述该约束问题；代码无对应形式化 |
| F063 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求二值变量重写；代码无 |
| F064 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求平稳性条件；代码无 |
| F065 | 论 | not_implemented | 3 | other | always |  |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求互补松弛；代码无 |

### infinigen（31 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved | ~ | L1 side | `speedup/flexgen/infinigen/flex_opt.py:426` | When self.policy.attn_sparsity >= 1.0: Path 2 (split GPU/CPU attention) asserts that sparsity >= 1.… |
| F002 | 代 | undisclosed | 1 | state | solved |  | L2 side | `speedup/flexgen/infinigen/flex_opt.py:442` | When k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None: Prefetch path… |
| F003 | 代 | undisclosed | 1 | reject | solved | ✓ | L2 side | `speedup/flexgen/infinigen/flex_opt.py:466` | When path == 1 or path == 2: Prefetching is not implemented for CPU-compute paths 1 and 2; raises V… |
| F004 | 代 | undisclosed | 1 | reject | solved | ~ | L1 side | `speedup/flexgen/infinigen/flex_opt.py:710` | When not (self.policy.act_gpu_percent == 100 or self.policy.act_cpu_percent == 100 or self.policy.a… |
| F005 | 代 | undisclosed | 1 | reject | solved | ~ | L2 unknown | `speedup/flexgen/infinigen/flex_opt.py:1359` | When args.compress_cache and args.attn_sparsity < 1.0: Combining cache compression with attention s… |
| F006 | 代 | undisclosed | 1 | reject | solved |  | L1 side | `speedup/flexgen/infinigen/pytorch_backend.py:464` | When not (attn_sparsity >= 1.0): AssertionError |
| F007 | 代 | undisclosed | 1 | reject | solved |  | L1 side | `speedup/flexgen/infinigen/pytorch_backend.py:823` | When not (src.device.device_type != DeviceType.MIXED): AssertionError |
| F008 | 代 | undisclosed | 1 | reject | solved |  | L1 side | `speedup/flexgen/infinigen/pytorch_backend.py:881` | When not (all((x.step is None for x in indices))): AssertionError |
| F009 | 代 | stated_differently | 2 | path_change | solved | ✓ | L2 unknown | `speedup/flexgen/infinigen/flex_opt.py:287` | When self.layer_id > 1: partial_weight_ratio is only set for layers with layer_id > 1; layer 0 and … |
| F010 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `speedup/flexgen/infinigen/flex_opt.py:389` | When self.policy.attn_sparsity >= 1.0: When sparsity >= 1.0 the full V cache is copied; otherwise V… |
| F011 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `speedup/flexgen/infinigen/flex_opt.py:528` | When self.enable_prefetching: When prefetching is enabled, mha_gen is called with p_w_q, partial_k_… |
| F012 | 代 | undisclosed | 2 | path_change | solved |  | L2 side | `speedup/flexgen/infinigen/flex_opt.py:541` | When prev_partial_cache_read_buf is not None and self.layer_id > 1: Partial cache accumulation for … |
| F013 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `speedup/flexgen/infinigen/flex_opt.py:799` | When j not in self.attn_layer[2:]: Cache loading is skipped for all attention layers except the fir… |
| F014 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 main | `speedup/flexgen/infinigen/pytorch_backend.py:401` | When p_w_q is None: In TorchDevice.mha_gen, the InfiniGen KV speculation (speculate_attention) only… |
| F015 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `speedup/flexgen/infinigen/pytorch_backend.py:422` | When attn_sparsity >= 1.0: Caller-supplied attn_sparsity selects dense attention (decompress full k… |
| F016 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `speedup/flexgen/infinigen/pytorch_backend.py:479` | When comp_config.group_dim == 0: Caller-supplied comp_config.group_dim decides whether k_new/v_new … |
| F017 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `speedup/flexgen/infinigen/pytorch_backend.py:767` | When policy.cache_disk_percent == 0: When the configured disk cache percent is zero, the KV cache i… |
| F018 | 论 | impl_deviates | 2 | other | solved |  |  | `accuracy/perplexity/table2.sh:27-45` | 论文要求覆盖受害者槽位；代码保留全部 K/V 只做注意力屏蔽（artifact 范围：无覆盖写步骤） |
| F019 | 论 | impl_deviates | 2 | other | solved |  |  | `accuracy/perplexity/table2.sh:27-45` | 论文要求淘汰后更新 GPU 部分 key cache；代码无该步骤（artifact 范围：缺更新步骤） |
| F020 | 论 | impl_deviates | 2 | other | always |  |  | `speedup/flexgen/infinigen/flex_opt.py:282` | 控制平面组件集合不完整（缺Pool Manager） |
| F021 | 论 | impl_deviates | 2 | other | solved |  |  | `speedup/flexgen/infinigen/flex_opt.py:513-524` | 论文要求A=V；代码A为V列按σq·σk排序重排，A≠V（artifact 范围：A为排序重排后的V，非论文所述A=V） |
| F022 | 论 | impl_deviates | 2 | other | solved |  |  | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | 预取集合由 top-k(均值) 决定，而非严格 >max−alpha 的令牌集合 |
| F023 | 论 | impl_deviates | 2 | other | solved |  |  | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | 实验路径以绝对令牌数封顶，未实现 20% 比例上限 |
| F024 | 论 | impl_deviates | 2 | other | solved |  |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 实验路径缺少K的逐元素绝对值 |
| F025 | 论 | impl_deviates | 2 | other | always |  |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 求和对象缺少K_abs项 |
| F026 | 论 | impl_deviates | 2 | other | always |  |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 单次topk未容纳K离群列 |
| F027 | 代 | undisclosed | 3 | path_change | solved | ✗ | L2 side | `speedup/flexgen/infinigen/flex_opt.py:690` | When (i == 0) or (i == (self.config.num_hidden_layers - 1)): When sep_layer is set, the first and l… |
| F028 | 代 | undisclosed | 3 | path_change | solved | ✗ | L1 main | `speedup/flexgen/infinigen/pytorch_backend.py:326` | When warmup or partial_weight_ratio is None: In TorchDevice.mha, the partial-weight index (which he… |
| F029 | 代 | undisclosed | 3 | reject | infeasible |  | 测不了 side | `speedup/flexgen/infinigen/pytorch_backend.py:837` | When not (dst.device.device_type != DeviceType.MIXED): AssertionError |
| F030 | 论 | not_implemented | 3 | other | solved |  |  | `accuracy/perplexity/table2.sh:27-45` | 论文要求饱和时全体减半；代码无该步骤（artifact 范围：无饱和减半） |
| F031 | 论 | not_implemented | 3 | other | always |  |  | `speedup/infinigen/infinigen/partial_weight_generation_contr…` | 实验路径缺少论文指定的相加步骤 |

### minference（73 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved |  | L1 unknown | `minference/minference_configuration.py:56` | When config_path is None and model_name not in MODEL2PATH: If no `config_path` is given, the model … |
| F003 | 代 | undisclosed | 1 | state | solved |  | L1 side | `minference/modules/minference_forward.py:165-172` | When SEARCH_MASK is None # first call only: module-level cache initialised on first call and reused |
| F004 | 代 | undisclosed | 1 | state | solved |  | L1 side | `minference/modules/minference_forward.py:390` | When "vs" in self.__dict__: Static pattern reuses vertical_topk/slash cached in self.vs from an ear… |
| F006 | 代 | undisclosed | 1 | reject | solved |  | L1 side | `minference/modules/minference_forward.py:484-488` | When True: raise ValueError(f'The cache structure has changed since version v4.36. If you are using… |
| F008 | 代 | undisclosed | 1 | state | solved |  | L1 side | `minference/modules/minference_forward.py:681` | When key_states.shape[-2] != kv_seq_len: Whether SnapKV compression runs depends on `self.kv_seq_le… |
| F010 | 代 | undisclosed | 1 | reject | solved |  | L3 main | `minference/ops/block_sparse_flash_attention.py:126` | When not (Lq == Lk and Lk == Lv): AssertionError |
| F011 | 代 | undisclosed | 1 | reject | solved |  | L3 main | `minference/ops/block_sparse_flash_attention.py:127` | When not (Lk in {16, 32, 64, 128}): AssertionError |
| F012 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `minference/ops/pit_sparse_flash_attention_v2.py:149` | When not (Lq == Lk and Lk == Lv): AssertionError |
| F013 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `minference/ops/pit_sparse_flash_attention_v2.py:150` | When not (Lk in {16, 32, 64, 128}): AssertionError |
| F014 | 代 | undisclosed | 1 | reject | solved | ✓ | L3 side | `minference/ops/streaming_kernel.py:414` | When Lk not in {16, 32, 64, 128}: Head dimension (q/k/v last dim) must be one of 16/32/64/128; othe… |
| F015 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `minference/ops/streaming_kernel.py:605` | When not (q.dim() == 4): AssertionError |
| F016 | 代 | undisclosed | 1 | reject | solved |  | L3 side | `minference/ops/streaming_kernel.py:606` | When not (q.shape == k.shape == v.shape): AssertionError |
| F017 | 代 | undisclosed | 1 | reject | solved |  | L1 unknown | `minference/patch.py:207` | When output_attentions: If the caller requests attention outputs, execution is aborted by the asser… |
| F019 | 代 | undisclosed | 1 | reject | solved | ~ | L1 side | `minference/patch.py:1253` | When not |
| F020 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 unknown | `minference/minference_configuration.py:52` | When self.attn_type in self.STASTIC_ATTENTION_TYPES: For any `attn_type` in `STASTIC_ATTENTION_TYPE… |
| F021 | 代 | undisclosed | 2 | path_change | solved | ✓ | L3 main | `minference/modules/minference_forward.py:63` | When not (self.config_path is not None and os.path.exists(self.config_path) and self.layer_idx < le… |
| F022 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 side | `minference/modules/minference_forward.py:192` | When best_ty == "stream_llm": If streaming wins the search, it is overridden to vertical_and_slash,… |
| F023 | 代 | undisclosed | 2 | path_change | solved |  | L1 main | `minference/modules/minference_forward.py:418-419` | When q_len == 1: returns via dense |
| F024 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 main | `minference/modules/minference_forward.py:421` | When self.config.to_dict().get("dilated1", False): Config flag switches to the fixed 'dilated1' spa… |
| F025 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 main | `minference/modules/minference_forward.py:423` | When self.config.to_dict().get("dilated2", False): Config flag switches to the fixed 'dilated2' spa… |
| F026 | 代 | undisclosed | 2 | path_change | solved |  | L1 main | `minference/modules/minference_forward.py:425-426` | When self.config.to_dict().get('dense', False): returns via dense |
| F027 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 main | `minference/modules/minference_forward.py:427` | When self.config.to_dict().get("streaming", False): Config flag switches to streaming_forward with … |
| F028 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 main | `minference/modules/minference_forward.py:432` | When self.config.to_dict().get("static_pattern", False): Config flag switches to vertical_and_slash… |
| F029 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 main | `minference/modules/minference_forward.py:434` | When self.config.to_dict().get("vs_only", False): Config flag forces the vertical_and_slash_kernel … |
| F030 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 side | `minference/modules/minference_forward.py:521` | When self.layer_idx >= self.starting_layer and not self.is_search: Layers below starting_layer (or … |
| F031 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 unknown | `minference/modules/minference_forward.py:613` | When self.layer_idx >= self.starting_layer: Layers below starting_layer use dense flash_attn_func; … |
| F032 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 unknown | `minference/modules/minference_forward.py:756` | When q_len == 1: In gather_last_q_vertical_slash_topk_vllm, a single query token bypasses the spars… |
| F033 | 代 | undisclosed | 2 | path_change | solved | ✓ | L2 side | `minference/modules/minference_forward.py:864` | When kv_cache is None or prefill_meta.block_tables.numel() == 0: Only when there is no KV cache or … |
| F034 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `minference/modules/snap_kv.py:321` | When q_len < self.max_capacity_prompt: When the prompt length is below max_capacity_prompt, update_… |
| F035 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `minference/modules/snap_kv.py:347` | When self.pooling == "avgpool": The pooling attribute (set from config.pooling in init_snapkv) sele… |
| F037 | 代 | undisclosed | 2 | path_change | solved | ~ | L3 side | `minference/ops/streaming_kernel.py:609` | When head_dim not in [16, 32, 64, 128, 256, 512]: For head dimensions not in the hard-coded list, q… |
| F038 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `minference/ops/streaming_kernel.py:620` | When k_len > n_local: The streaming (StreamingLLM) variant only keeps the `n_init` sink tokens when… |
| F039 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `minference/ops/streaming_kernel.py:701` | When len_k <= n_local + n_init: The KV cache kept for subsequent decoding is either the full h_k/h_… |
| F040 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `minference/patch.py:835` | When config.kv_cache_cpu: Caller-supplied config flag switches to the KV-cache-on-CPU variant (minf… |
| F041 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 unknown | `minference/patch.py:840` | When config.use_snapkv: Caller-supplied config flag switches to the SnapKV variant (minference_patc… |
| F042 | 论 | impl_deviates | 2 | other | solved |  |  | `csrc/vertical_slash_index.cu:27-99` | 论文要求循环守卫 s_v≤k_s；代码用 while(1)+break，s 仅在 else 分支递增，终止由 s>=NNZ_S 决定 |
| F043 | 论 | impl_deviates | 2 | other | always |  |  | `experiments/README.md:13-30` | 实验配置未体现{(1024,4096)}，实际候选为(100,800) |
| F044 | 论 | impl_deviates | 2 | other | always |  |  | `experiments/README.md:13-30` | 实验配置未体现论文候选集 |
| F045 | 论 | impl_deviates | 2 | other | always |  |  | `experiments/README.md:13-30` | 配置层未体现{100} |
| F046 | 论 | impl_deviates | 2 | other | solved |  |  | `experiments/infinite_bench/args.py:63-78` | 论文Table4/Fig5报告static变体结果；评估入口未暴露static选项，且底层static实现本身只覆盖VS。 |
| F047 | 论 | impl_deviates | 2 | other | solved |  |  | `experiments/infinite_bench/args.py:63-78` | 评估入口无'only A-shape'变体选择，无法复现Table4的该变体。 |
| F048 | 论 | impl_deviates | 2 | other | solved |  |  | `experiments/infinite_bench/args.py:63-78` | 无变体入口，无法复现Table4的only block-sparse行。 |
| F049 | 论 | impl_deviates | 2 | other | solved |  |  | `minference/models_patch.py:66-73` | 论文 1k 全局/4k 局部；代码 128 全局/3968 局部，两参数均不符。 |
| F050 | 论 | impl_deviates | 2 | other | always |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求遍历调用方给定的初始化搜索空间 σ；代码遍历写死的候选表，σ 输入不存在（artifact 范围：无 σ 输入，候选表硬编码） |
| F051 | 论 | impl_deviates | 2 | other | no_condition |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求 dense 注意力输出 y（含 V）；代码只算注意力权重矩阵，未形成输出 |
| F052 | 论 | impl_deviates | 2 | other | no_condition |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求最小化与 dense 输出的偏差；代码最大化权重保留分数，方向与参照对象均不同 |
| F053 | 论 | impl_deviates | 2 | other | always |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求六类输入；代码签名缺 V、patterns、ρ、t、σ |
| F054 | 论 | impl_deviates | 2 | other | always |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求空集初始化；代码以数值 0 与空字符串初始化，且该初值使负分候选永不被选 |
| F055 | 论 | impl_deviates | 2 | other | always |  |  | `minference/modules/minference_forward.py:199-246` | 论文要求最小化 t_sparse(M)+t_overhead(M)；artifact 执行路径未实现该时间目标。 |
| F056 | 论 | impl_deviates | 2 | other | always |  |  | `minference/ops/block_sparse_flash_attention.py:150-165` | 论文要求块级 logits 先 softmax（并除 √d）得 Â；代码省略 softmax 与缩放，仅用因果掩码后的原始点积排序（artifact 范围：无 softmax/√d 的块级注意力矩阵） |
| F002 | 代 | undisclosed | 3 | other | solved | ~ | 测不了 | `minference/modules/minference_forward.py:30` | When ROPE_TYPE is not None: `ROPE_TYPE` is a module-level global computed once from the *first* att… |
| F057 | 代 | undisclosed | 3 | other | solved | ~ | 测不了 main | `minference/modules/minference_forward.py:34` | When "seq_len" in inspect.signature(self.rotary_emb.forward).parameters: ROPE_TYPE is chosen by int… |
| F058 | 代 | undisclosed | 3 | state | solved | ✗ | L1 main | `minference/modules/minference_forward.py:74` | When "apply_rotary_pos_emb" not in self.__dict__: `apply_rotary_pos_emb` is rebound as a module-lev… |
| F059 | 代 | undisclosed | 3 | other | solved | ✓ | 测不了 side | `minference/modules/minference_forward.py:194` | When best_ty == "block_sparse": If block_sparse wins, it is replaced by hard-coded vertical_and_sla… |
| F060 | 代 | undisclosed | 3 | other | solved | ✓ | 测不了 main | `minference/modules/minference_forward.py:430` | When head_id not in self.best_pattern: When the per-layer pattern file |
| F005 | 代 | undisclosed | 3 | other | solved |  | 测不了 | `minference/modules/minference_forward.py:441` | When ty not in {"stream_llm", "vertical_and_slash", "block_sparse"}: The implementation is chosen b… |
| F007 | 代 | undisclosed | 3 | other | solved | ✓ | 测不了 main | `minference/modules/minference_forward.py:504` | When self.is_search and os.path.exists(self.config_path) and self.layer_idx < len(config_list): Wit… |
| F061 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `minference/modules/minference_forward.py:523` | When is_flash_attn_2_available(): When the sparse path is not taken, availability of flash-attn 2 d… |
| F062 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `minference/modules/minference_forward.py:526` | When not (is_flash_attn_2_available()): attn_output = gather_qkv(q, k, v, attention_mask) |
| F009 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `minference/modules/minference_forward.py:754` | When head_id not in self.best_pattern: The vLLM variant indexes `self.best_pattern[head_id]` direct… |
| F036 | 代 | undisclosed | 3 | other | solved | ~ | 测不了 main | `minference/ops/block_sparse_flash_attention.py:130` | When q.dtype != torch.bfloat16: The Triton kernel's compute dtype is chosen from the input dtype: b… |
| F063 | 代 | undisclosed | 3 | other | solved | ~ | 测不了 main | `minference/ops/block_sparse_flash_attention.py:164` | When top_k > context_size // block_size_N: The requested `top_k` (derived from the searched `slash_… |
| F064 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `minference/ops/pit_sparse_flash_attention.py:150` | When q.dtype != torch.bfloat16: Any query dtype other than bfloat16 (float32, float64, float16 is f… |
| F065 | 代 | undisclosed | 3 | path_change | solved | ✗ | L3 side | `minference/ops/pit_sparse_flash_attention_v2.py:188` | When head_dim not in [16, 32, 64, 128, 256, 512]: For head dims outside the power-of-two list |
| F018 | 代 | undisclosed | 3 | other | solved |  | 测不了 | `minference/patch.py:1252` | When not isinstance(model, |
| F066 | 论 | not_implemented | 3 | other | solved |  |  | `experiments/README.md:13-30` | 实验入口未暴露或设定步长50 |
| F067 | 论 | not_implemented | 3 | other | always |  |  | `experiments/infinite_bench/args.py:63-78` | 无变体配置，无法复现Table7的only vertical行。 |
| F068 | 论 | not_implemented | 3 | other | solved |  |  | `experiments/infinite_bench/args.py:63-78` | 无换算配置入口。 |
| F069 | 论 | not_implemented | 3 | other | solved |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求每候选计算真实 kernel FLOPs；代码不计算任何 FLOPs |
| F070 | 论 | not_implemented | 3 | other | always |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求以目标 FLOPs 为停止条件的迭代调整；代码无该循环与调整算子 |
| F071 | 论 | not_implemented | 3 | other | always |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求累积 FLOPs 对齐后的候选到 ρ；代码无该累积步骤 |
| F072 | 论 | not_implemented | 3 | other | no_condition |  |  | `minference/modules/minference_forward.py:99-197` | 论文要求 FlashAttention 与 V 信息参与选择；代码为稠密权重计算且完全不含 V |
| F073 | 论 | not_implemented | 3 | other | always |  |  | `minference/modules/minference_forward.py:199-246` | 论文要求分别定义 t_sparse 与 t_overhead；artifact 路径无对应实现。 |

### nnsmith（38 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved | ~ | L1 side | `nnsmith/abstract/op.py:1563` | When gres_config not in ("3", "4", "5"): An unrecognized NNSMITH_GRES environment value causes a Va… |
| F003 | 代 | undisclosed | 1 | reject | solved |  | L1 unknown | `nnsmith/cli/fuzz.py:180` | When isinstance(e, InternalError): InternalError from make_testcase is propagated, aborting the fuz… |
| F004 | 代 | contradicts_docs | 1 | reject | solved |  | L1 side | `nnsmith/graph_gen.py:260` | When self.check_sat() != z3.sat: After adding the memory-limit constraint, an unsatisfiable (or unk… |
| F009 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 unknown | `nnsmith/abstract/arith.py:74` | When carry and max(left_size, right_size) >= ARITH_MAX_WIDTH: For addition, the extra carry bit is … |
| F010 | 代 | undisclosed | 2 | path_change | solved | ~ | L1 side | `nnsmith/abstract/arith.py:79` | When mult and (right.size() + left.size()) >= ARITH_MAX_WIDTH: For multiplication, when the combine… |
| F011 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `nnsmith/abstract/op.py:25` | When FLOPS_LIM == "off": Setting NNSMITH_FLOPS_LIM=off sets FLOPS_LIM to None, disabling the FLOPs … |
| F012 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 side | `nnsmith/abstract/op.py:910` | When Z3_CONS_FLOPS: A module-level flag decides whether the FLOPS upper-bound constraint is added t… |
| F014 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 side | `nnsmith/abstract/op.py:1587` | When os.getenv("NNSMITH_CONS_RESHAPE", "off") != "off": The environment variable NNSMITH_CONS_RESHA… |
| F015 | 代 | undisclosed | 2 | path_change | solved |  | L1 unknown | `nnsmith/cli/fuzz.py:60` | When not self.crash_safe and self.test_timeout is not None: Setting fuzz.test_timeout without crash… |
| F016 | 代 | undisclosed | 2 | path_change | solved |  | L1 unknown | `nnsmith/cli/model_gen.py:31` | When cfg["backend"]["type"] is not None: A caller-supplied backend type decides whether a BackendFa… |
| F017 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 side | `nnsmith/graph_gen.py:256` | When NNSMITH_LIMNF_V == "0": Branches the memory-limit constraint: v0 adds nnsmith_le(self.n_floats… |
| F018 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `nnsmith/graph_gen.py:258` | When NNSMITH_LIMNF_V == "1": With NNSMITH_LIMNF_V=1 the per-op float-count constraints accumulated … |
| F019 | 代 | stated_differently | 2 | path_change | solved | ~ | L3 main | `nnsmith/graph_gen.py:556` | When random.uniform(0, 1) < self.forward_prob: A caller-configured forward_prob attribute decides w… |
| F020 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `nnsmith/graph_gen.py:944` | When idx in disable: For each reshape group, one randomly chosen destination dimension is disabled … |
| F021 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 unknown | `nnsmith/materialize/torch/__init__.py:47` | When self.sat_inputs is None: When no satisfying inputs were found (sat_inputs is None), make_oracl… |
| F022 | 代 | undisclosed | 2 | path_change | solved |  | L1 unknown | `nnsmith/materialize/torch/input_gen.py:93` | When all([DType.is_float(v.dtype) for _, v in self.net.input_like.items()]): Whether all model inpu… |
| F006 | 合 | undisclosed | 2 | other | solved | ✓ | 测不了 side | `nnsmith/materialize/torch/symbolnet.py:188` | When p.grad is not None and torch.any(p.grad != 0): If all parameter gradients are zero, Constraint… |
| F024 | 合 | undisclosed | 2 | other | solved |  | 测不了 side | `nnsmith/materialize/torch/symbolnet.py:234` | When max_time is None: The gradient-based input search budget is taken from the environment (NNSMIT… |
| F025 | 代 | undisclosed | 2 | path_change | solved | ✓ | L1 side | `nnsmith/materialize/torch/symbolnet.py:238` | When tensor.data.dtype.is_floating_point: Only floating-point input tensors are wrapped as trainabl… |
| F028 | 论 | impl_deviates | 2 | other | solved |  |  | `nnsmith/abstract/op.py:1053-1080` | artifact 路径不存在 pad 的 0 箱/负箱特化 |
| F029 | 论 | impl_deviates | 2 | other | always |  |  | `nnsmith/abstract/op.py:1332-1360` | artifact 路径不存在 Conv2d padding 的 0 箱特化 |
| F030 | 论 | impl_deviates | 2 | other | solved |  |  | `nnsmith/graph_gen.py:1029-1058` | 论文要求每轮随机选一半；代码仅首轮随机，后续轮固定丢弃后半段 |
| F013 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `nnsmith/abstract/op.py:1552` | When gres_config != "4": The environment variable NNSMITH_GRES selects the reshape grouping strateg… |
| F002 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `nnsmith/abstract/op.py:2083` | When not check_sat(): If the requested output rank cannot be satisfied by the rank-increment loop (… |
| F031 | 代 | undisclosed | 3 | other | solved | ✗ | 测不了 | `nnsmith/graph_gen.py:190` | When int(os.getenv("NNSMITH_BITS", 30)) != 30: The number of bits used to split the integer-domain … |
| F005 | 代 | undisclosed | 3 | other | solved | ~ | 测不了 side | `nnsmith/graph_gen.py:524` | When isinstance(op, Expand) and oshape.ndims < op.expand_last_dim: Placeholder shapes with fewer di… |
| F032 | 代 | undisclosed | 3 | other | solved | ✗ | 测不了 side | `nnsmith/graph_gen.py:834` | When os.getenv("NNSMITH_LB", "off") == "off": The upper-bound constraint on slice start/end paramet… |
| F033 | 代 | undisclosed | 3 | other | solved | ✗ | 测不了 | `nnsmith/graph_gen.py:984` | When os.getenv("NNSMITH_G_CONFIG", "1") != "1": The environment variable NNSMITH_G_CONFIG selects w… |
| F034 | 代 | undisclosed | 3 | path_change | solved | ✗ | L1 side | `nnsmith/graph_gen.py:1016` | When config is None: If the op class has no entry in param_config, extra_constraints returns an emp… |
| F035 | 代 | undisclosed | 3 | path_change | solved | ✗ | L3 main | `nnsmith/graph_gen.py:1044` | When len(cons) == 0 or random.uniform(0, 1) > self.constrain_prob: Guidance constraints for a node … |
| F036 | 代 | paper_stated | 3 | path_change | solved | ✗ | L1 main | `nnsmith/graph_gen.py:1052` | When self.check_sat(*cur_cons) != z3.sat: If the collected guidance constraints are unsatisfiable, … |
| F037 | 代 | undisclosed | 3 | path_change | solved | ✗ | L1 main | `nnsmith/graph_gen.py:1054` | When len(cur_cons) == 0: When all guidance constraints are dropped due to unsat, the loop breaks an… |
| F023 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `nnsmith/materialize/torch/input_gen.py:98` | When self.differentiable is False: The variant is decided by a single probe forward pass on random … |
| F026 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `nnsmith/materialize/torch/symbolnet.py:358` | When output_tensors[i].grad_fn is None: `differentiable` is reset to True at the start of every for… |
| F038 | 代 | undisclosed | 3 | path_change | solved | ✗ | L1 unknown | `nnsmith/materialize/torch/symbolnet.py:382` | When self.check_intermediate_numeric or (self.use_gradient and not self.stop_updating_loss): Constr… |
| F007 | 代 | undisclosed | 3 | other | solved | ✓ | 测不了 side | `nnsmith/materialize/torch/symbolnet.py:385` | When loss_fn.dispatch(type(op)) is not None: If an op produces NaN/Inf but has no registered loss f… |
| F027 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `nnsmith/materialize/torch/symbolnet.py:403` | When vul_op_loss is None: When an op produces NaN/Inf but has no registered loss function (`loss_fn… |
| F008 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `nnsmith/materialize/torch/symbolnet.py:421` | When self.loss is not None: If two vulnerable ops both produce NaN/Inf in the same forward pass, th… |

### qoserve（50 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved |  | L1 main | `sarathi/core/scheduler/deadline_scheduler.py:251` | When not (seq.is_paused()): 'Sequence should be in PAUSED state' |
| F002 | 代 | undisclosed | 1 | reject | solved |  | L1 main | `sarathi/core/scheduler/deadline_scheduler.py:253` | When not (self.block_manager.can_append_slot()): AssertionError |
| F003 | 合 | docs_only | 2 | other | solved |  | 测不了 unknown | `sarathi/core/datatypes/sequence.py:73` | When NUM_TIERS > 0: Each Sequence's QoS tier (and hence its deadline) is drawn at random from the g… |
| F004 | 合 | undisclosed | 2 | path_change | solved |  | L3 main | `sarathi/core/datatypes/sequence.py:114` | When self.tier > 0: For any non-zero (randomly assigned) tier, the TBT deadline uses execution_thre… |
| F005 | 代 | undisclosed | 2 | path_change | solved |  | L3 side | `sarathi/core/scheduler/deadline_scheduler.py:120` | When memory_budget < 1000: When free KV-cache blocks (free_blocks * block_size // 32) fall below 10… |
| F006 | 代 | undisclosed | 2 | path_change | solved |  | L3 side | `sarathi/core/scheduler/deadline_scheduler.py:130` | When min_slack <= 0: When the caller-supplied slack is non-positive, the binary search is skipped e… |
| F007 | 代 | undisclosed | 2 | path_change | solved |  | L3 main | `sarathi/core/scheduler/deadline_scheduler.py:231` | When seq.tier >= 1: For tier>=1 sequences the ttft_deadline is recomputed by subtracting predicted … |
| F008 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `sarathi/core/scheduler/deadline_scheduler.py:233` | When seq.num_decode_tokens == -1: Selects whether the decode-time estimate uses the global output_l… |
| F009 | 代 | undisclosed | 2 | path_change | solved |  | L1 side | `sarathi/core/scheduler/deadline_scheduler.py:276` | When self.scheduler_type == 'deadline': Only when scheduler_type is 'deadline' is the dynamic chunk… |
| F010 | 代 | undisclosed | 2 | path_change | solved |  | L3 main | `sarathi/core/scheduler/deadline_scheduler.py:300` | When self.scheduler_type == 'deadline' or self.scheduler_type == 'deadline_no_dynamic_chunking': Th… |
| F011 | 论 | impl_deviates | 2 | other | no_condition |  |  | `README.md:1-129` | 实验脚本不自动下载数据集，需先手动 wget |
| F012 | 论 | impl_deviates | 2 | other | always |  |  | `chunk_size_predictor/predictor.py:1-41` | 论文要求训练随机森林；脚本导入并训练 LinearRegression，无 RandomForest/ensemble |
| F013 | 论 | impl_deviates | 2 | other | always |  |  | `fig7.sh:76-106` | 缺 §4.3/§4.4 执行路径 |
| F014 | 论 | impl_deviates | 2 | other | trigger_only |  |  | `fig7.sh:76-106` | 缺 Qwen/70B 与 4 小时控制 |
| F015 | 论 | impl_deviates | 2 | other | solved |  |  | `paper_plot_scripts/fig7_cap.py:13-47` | Q1 的 TBT 违规未被度量 |
| F016 | 论 | impl_deviates | 2 | other | always |  |  | `paper_plot_scripts/fig_10_11.py:1-20` | 图输出目录与论文声明的 paper_plots/ 不一致 |
| F017 | 论 | impl_deviates | 2 | other | always |  |  | `paper_plot_scripts/fig_10_11.py:19-37` | 固定阈值替代数据 p90 |
| F018 | 论 | impl_deviates | 2 | other | always |  |  | `sarathi/config/config.py:284-311` | 脚本层同样无按请求提交 QoS 字段的配置。 |
| F019 | 论 | impl_deviates | 2 | other | always |  |  | `sarathi/config/config.py:284-311` | 脚本层无每请求优先级配置。 |
| F020 | 论 | impl_deviates | 2 | other | solved |  |  | `sarathi/core/datatypes/sequence.py:70-80` | 实验路径同样没有独立的 D_total 完成截止。 |
| F021 | 论 | impl_deviates | 2 | other | solved |  |  | `sarathi/core/datatypes/sequence.py:88-109` | 论文要求 α 同时乘 (Prefill_rem+Decode_rem)；代码把 decode 估计以固定系数 execution_threshold_batched 从期限中扣除，而非以 α 加权加… |
| F022 | 论 | impl_deviates | 2 | other | solved |  |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求检查“已违反 或 将违反”TTFT/TTLT；代码仅做 TTFT 前瞻（now+service_time>deadline），且仅对 drop==0 且未分配内存的请求生效，无 TTLT 维… |
| F023 | 论 | impl_deviates | 2 | other | solved |  |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求移入独立 relegated 队列；代码仅设 drop 标志并放回原 prefill 队列，无 relegated 队列结构，且 drop 请求仍可被再次选中调度。（artifact 范围：… |
| F024 | 代 | undisclosed | 3 | other | solved |  | 测不了 unknown | `sarathi/core/datatypes/sequence.py:80` | When self.scheduler_type == 'fcfs': `Sequence.__lt__` dispatches on this per-object attribute: 'fcf… |
| F025 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `sarathi/core/scheduler/deadline_scheduler.py:92` | When batch_num_tokens <= 512: The execution-time predictor switches between two hard-coded stratifi… |
| F026 | 代 | undisclosed | 3 | other | solved |  | 测不了 main | `sarathi/core/scheduler/deadline_scheduler.py:211` | When not self._check_request_prompt_length(seq): Requests whose prompt length fails the check are a… |
| F027 | 代 | undisclosed | 3 | other | solved |  | 测不了 side | `sarathi/core/scheduler/deadline_scheduler.py:305` | When (seq.drop == 0) and (seq.mem_allocated == False) and ((now + service_time_required) > (seq.arr… |
| F028 | 论 | not_implemented | 3 | other | always |  |  | `chunk_size_predictor/predictor.py:1-41` | 论文要求用 Vidur 暴露的 harness 采集剖面；pinned 仓库中不存在该采集实现 |
| F029 | 论 | not_implemented | 3 | other | always |  |  | `fig10_11.sh:103-129` | 偏斜工作负载未实现 |
| F030 | 论 | not_implemented | 3 | other | always |  |  | `fig7.sh:76-106` | 未实现按 QoS 桶独立集群的 silo 部署 |
| F031 | 论 | not_implemented | 3 | other | always |  |  | `fig7.sh:76-106` | silo 基线整体缺失，无按桶 chunk 配置 |
| F032 | 论 | not_implemented | 3 | other | no_condition |  |  | `fig7.sh:76-106` | 集群规模实验缺失 |
| F033 | 论 | not_implemented | 3 | other | always |  |  | `fig7.sh:76-106` | 瞬态过载工作负载未实现 |
| F034 | 论 | not_implemented | 3 | other | always |  |  | `fig7.sh:76-106` | 无峰谷比构造 |
| F035 | 论 | not_implemented | 3 | other | no_condition |  |  | `fig7.sh:76-106` | 集群规模实验缺失 |
| F036 | 论 | not_implemented | 3 | other | no_condition |  |  | `fig7.sh:76-106` | 替代分配实验缺失 |
| F037 | 论 | not_implemented | 3 | other | always |  |  | `fig8.sh:37-69` | 论文要求固定 QPS 下离线扫描 α 0–10；artifact 脚本对 α 只给单一常量 0.016，未遍历 0–10 的 α 网格。 |
| F038 | 论 | impl_deviates | 3 | other | infeasible |  |  | `fig8.sh:37-69` | 论文称固定 QPS 采用 8 ms/token；artifact 固定 QPS 运行脚本使用 16 ms/token，与论文所选值不符。 |
| F039 | 论 | not_implemented | 3 | other | always |  |  | `fig8.sh:37-69` | 论文要求低负载 α=1 ms/token；artifact 无该取值或负载分段。 |
| F040 | 论 | not_implemented | 3 | other | always |  |  | `fig8.sh:37-69` | 组件消融未实现 |
| F041 | 论 | not_implemented | 3 | other | always |  |  | `fig8.sh:37-69` | 消融表汇总未实现 |
| F042 | 论 | not_implemented | 3 | other | always |  |  | `fig8.sh:37-69` | alpha 敏感性实验未实现 |
| F043 | 论 | not_implemented | 3 | other | always |  |  | `paper_plot_scripts/fig_10_11.py:19-37` | 优先级标注未实现 |
| F044 | 论 | not_implemented | 3 | other | always |  |  | `run_exp.sh:1-27` | 未实现多副本 round-robin 分发 |
| F045 | 论 | not_implemented | 3 | other | always |  |  | `sarathi/config/config.py:284-311` | 脚本层同样无按应用解码历史。 |
| F046 | 论 | not_implemented | 3 | other | solved |  |  | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | 论文要求优先级驱动的抢占；对齐 artifact 调度路径不执行抢占。 |
| F047 | 论 | not_implemented | 3 | other | solved |  |  | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | 缺少 prefill 队列抢占资格判定。 |
| F048 | 论 | not_implemented | 3 | other | solved |  |  | `sarathi/core/scheduler/deadline_scheduler.py:184-354` | 论文所述避免队头阻塞的抢占手段在 DeadlineScheduler 中不存在。（artifact 范围：。） |
| F049 | 论 | not_implemented | 3 | other | no_condition |  |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求按优先级抢占已部分 prefill 的在途请求；代码无任何抢占触发或调用，仅通过堆排序选择未开始的请求 |
| F050 | 论 | not_implemented | 3 | other | solved |  |  | `sarathi/core/scheduler/deadline_scheduler.py:296-333` | 论文要求按优先级分层、低优先级耗尽后才降级高优先级；代码对所有请求一视同仁按截止时间降级，无分层门控。（artifact 范围：。） |

### sparta（82 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 2 | path_change | solved | ✓ | L2 unknown | `sparta/transformation/weighted_block_cover.py:77` | When cover_sizes[(1, 1)] < ordered_pricing[0][0]: The choice of covering algorithm is driven by the… |
| F002 | 合 | docs_only | 2 | reject | solved | ✓ | L1 unknown | `sparta/transformation/weighted_block_cover.py:123` | When len(unique_block_sizes) != 1: wbc_matmul only supports a single block size for the weight tesa… |
| F003 | 论 | impl_deviates | 2 | other | always |  |  | `` | 论文要求 S 初始为全部节点；代码初始队列只含源/汇节点，其余节点由度数递减触发入队 |
| F004 | 论 | impl_deviates | 2 | other | no_condition |  |  | `` | 论文要求把全部邻居（除 N）插入 S；代码只在度数归零时入队，非全部邻居 |
| F005 | 论 | impl_deviates | 2 | other | always |  |  | `` | 论文要求直到无 TeSA 需更新；代码固定两遍、每节点一次，不检测掩码是否仍变化 |
| F006 | 论 | impl_deviates | 2 | other | always |  |  | `` | 论文要求随算子类型 AND 属性类型变化；代码仅覆盖剪枝一种属性种类（量化比特未实现，见 M02-B07-R02），属性维度分派缺失 |
| F007 | 论 | impl_deviates | 2 | other | always |  |  | `` | 论文要求重复运行多次（经验 256 个随机张量）；代码单次前向，以批内方差近似重复采样，重复次数由 confidence/batch 维决定而非 256 次独立运行 |
| F008 | 论 | impl_deviates | 2 | other | always |  |  | `` | 论文返回 Iupdated∪Oupdated 的输入与输出 TeSA 更新集；代码只返回每层 weight_mask，缺输入/输出更新集 |
| F009 | 论 | impl_deviates | 2 | other | always |  |  | `` | artifact 路径无通用纳入机制。 |
| F010 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:169-178` | 论文要求用真实数据集推理得到的算子输入输出张量；逐模块传播路径用随机张量代替真实激活 |
| F011 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:301-335` | 论文要求对算子所有张量（输入/权重/输出）逐一评估；代码只对 weight 张量做位宽搜索，input/output 未评估 |
| F012 | 论 | impl_deviates | 2 | other | no_condition |  |  | `script/figure14/search_finetune_fit_qat.py:496-538` | 论文要求精度下降小于预定义阈值（1%）才接受；代码用 best_acc<original_acc 即任何下降都拒绝，无 1% 阈值 |
| F013 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:496-538` | 论文要求拓扑序并缓存激活；代码按模块注册顺序遍历且无激活缓存 |
| F014 | 论 | impl_deviates | 2 | other | solved |  |  | `script/figure14/search_finetune_fit_qat.py:571-664` | 论文要求同时更新 S 与 Supdated；代码只更新全局位设置，无 Supdated 累积 |
| F015 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:571-664` | 论文以 Tupdated==T 跳过；代码以精度下降 break，语义不同 |
| F016 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure16/a100/sparta.cu:118-140` | 论文报告第二 sub-Matmul 的具体残余稀疏度；实验路径无该测量/输出，且底层分派规则与数值趋势不符。 |
| F017 | 论 | impl_deviates | 2 | other | no_condition |  |  | `script/figure16/a100/sparta.cu:266-311` | 实验路径的第二部分内核依赖为 Sputnik，而非 SparTA 专用稀疏内核。 |
| F018 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 脚本无反馈驱动的稀疏属性更新步骤。 |
| F019 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 无编译-测量迭代回路。 |
| F020 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure19/run.sh:1-7` | 加速来自 NNI ModelSpeedup 而非 SparTA 稀疏 kernel。 |
| F021 | 论 | impl_deviates | 2 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 无目标稀疏度终止条件。 |
| F022 | 论 | impl_deviates | 2 | other | always |  |  | `script/init_checkpoints.sh:1-34` | 论文要求传播为 Rammer 内专用编译 pass；实验路径在编译前以 Python 脚本离线传播，编译器 pass 列表无传播 pass。 |
| F023 | 论 | impl_deviates | 2 | other | always |  |  | `script/run_all_2080ti.sh:1-57` | 论文要求复现 Figure 8-11、14-18、20；实际覆盖 8-11、13-15、17、19 与 table3，缺 figure18、figure20，且 2080Ti 路径无 figure1… |
| F024 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/artifact_specialization/generate_code.py:58-82` | 论文要求 2 字节位域属性；artifact 路径以文本配置+按位宽分支替代，未实现 7/4/5 位布局 |
| F025 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/artifact_specialization/generate_code.py:58-82` | 论文要求 4/8 表示 uint4/uint8；artifact 仅实现 int8 路径，无符号量化未体现 |
| F026 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/propagation/talgebra.py:4-17` | 论文要求 ×、÷、x^y 三类算子均满足任一 φ 即 φ；代码只提供 × 的 and 规则，÷ 与 x^y 无任何规则 |
| F027 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/propagation/talgebra.py:4-17` | 论文要求 ×/÷/x^y 三者均满足 α∧α→α；代码仅实现 × |
| F028 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/propagation/talgebra.py:20-34` | 论文要求对逐元素可表达算子按计算流计算输出 TeSA；代码只对 matmul 实现，一元与 ÷/x^y 算子无对应计算流 |
| F029 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/propagation/talgebra.py:50-62` | 论文要求三条导数公式（含 gB=gY）；代码仅实现两条，偏置项缺失。 |
| F030 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/specialization/specialize_kernel.py:18-42` | 论文允许输入分解；artifact 路径只处理单输入 TeSA |
| F031 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/specialization/specialize_kernel.py:18-42` | 输出不分解 |
| F032 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/specialization/specialize_kernel.py:18-42` | 论文要求 m+1 维笛卡尔积；代码仅权重维枚举，实际 1 维 |
| F033 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/specialization/specialize_kernel.py:44-77` | 论文要求位宽提示指导硬件指令选择（DP4A/wmma）；代码按位宽选不同 CUDA 模板，但模板选择处无基于位宽的指令级特化分支，32bit 分支直接走 cublas/稠密模板（artifact 范… |
| F034 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/specialization/specialize_kernel.py:44-77` | artifact 路径无 dismantle 展开步骤，仅消费预生成 kernel。 |
| F035 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/transformation/optimize_model.py:29-54` | 执行计划未被重写 |
| F036 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:56-81` | 论文要求每次调用产生新选项并初始化空列表；代码桩未实现且原地修改输入 |
| F037 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/transformation/transform_policy.py:56-81` | 论文要求返回累积分解列表；代码无该累积返回 |
| F038 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:56-81` | 论文要求对每个 BitRounding 结果 extend 其 WBC 输出；代码 TransformTeSA 未实现该 extend，实际路径仅收集未使用的 transform_options |
| F039 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/transformation/transform_policy.py:137-156` | 论文要求按采样位选项产生 k 个结果；代码无采样且限制最多 2 种位宽 |
| F040 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:137-156` | 论文要求先经 SampleBitOption 采样一个位选项再传给 BitRounding；代码无采样步骤，bit_align 直接使用 hardware_bit_precisions() 全集合（… |
| F041 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:137-156` | 论文要求每次运行返回新的（可不同的）变换选项；代码每次返回相同候选集合，无“per run 新选项”机制。（artifact 范围：。） |
| F042 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/transformation/transform_policy.py:137-191` | 论文要求每个操作数 TeSA 各自带块大小；代码仅权重 TeSA 获得 block_size，输入/输出 TeSA 的 block_size 保持 None 且不被消费（artifact 范围：仅权… |
| F043 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求 RecordPerf 记录每次 profile；artifact 路径计算后未记录 |
| F044 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求返回策略选出的最佳变换；代码无选择逻辑，返回 None |
| F045 | 论 | impl_deviates | 2 | other | solved |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求先 SampleBitOption 采样再传 BitRounding；代码以固定硬件位宽集合枚举替代采样（artifact 范围：无 SampleBitOption 采样触发） |
| F046 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求返回变换后 TeSA 列表；代码对应函数为桩，实际入口返回 None kernel 列表，未返回变换 TeSA 列表 |
| F047 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求调用方迭代多个方案并选满足者；代码迭代循环被注释，未执行方案搜索 |
| F048 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求每次调用返回一个新选项；代码返回固定单元素列表或一次性全部结果 |
| F049 | 论 | impl_deviates | 2 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文声称框架可纳入任意 sparsity-aware 技术；实验路径既未执行 specialization，其可达代码也只有固定模板枚举，无外部内核纳入能力。 |
| F050 | 代 | undisclosed | 3 | other | solved | ~ | 测不了 side | `sparta/common/sparsity.py:57` | When info.module_name in self.modules_info: When a module name is already present, the merge branch… |
| F051 | 论 | not_implemented | 3 | other | always |  |  | `` | 论文要求量化比特收敛规则；代码只处理剪枝掩码，无量化属性种类 |
| F052 | 论 | not_implemented | 3 | other | always |  |  | `` | 论文要求分发前初始化 Iupdated/Oupdated 空集；代码无规则分发，仅建空字典收集结果 |
| F053 | 论 | not_implemented | 3 | other | always |  |  | `` | 论文要求 foreach RegisteredPropRule 调用规则；代码为固定两个硬编码推断函数，无注册表迭代 |
| F054 | 论 | not_implemented | 3 | other | always |  |  | `` | 论文要求把规则返回的 Iproped/Oproped 合并进节点 Is/Os；代码无规则返回值，直接由硬编码推断写 masks |
| F055 | 论 | not_implemented | 3 | other | no_condition |  |  | `` | 论文要求累积每条规则更新到 Iupdated/Oupdated；代码为逐层快照收集，无规则更新累积 |
| F056 | 论 | not_implemented | 3 | other | no_condition |  |  | `` | artifact 路径无单块回退到通用稀疏/dense kernel 的分派。 |
| F057 | 论 | not_implemented | 3 | other | always |  |  | `` | artifact 路径无该搜索步骤。 |
| F058 | 论 | not_implemented | 3 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:260-299` | 论文要求从最近缓存激活部分推理；代码无缓存也无部分推理 |
| F059 | 论 | not_implemented | 3 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:260-299` | 无注册调用 |
| F060 | 论 | not_implemented | 3 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:260-299` | 论文要求 La 输出激活部分推理得 Lb 校准数据；代码无此复用 |
| F061 | 论 | not_implemented | 3 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:301-335` | 无 TeSA 集合初始化 |
| F062 | 论 | not_implemented | 3 | other | always |  |  | `script/figure14/search_finetune_fit_qat.py:301-335` | 无 SplitToIsOs 返回 |
| F063 | 论 | not_implemented | 3 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 路径无编译后延迟/内存测量步骤。 |
| F064 | 论 | not_implemented | 3 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 路径无真实延迟过滤。 |
| F065 | 论 | not_implemented | 3 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 无编译迭代。 |
| F066 | 论 | not_implemented | 3 | other | always |  |  | `script/figure19/run.sh:1-7` | artifact 无 FLOPs 过滤基线。 |
| F067 | 论 | not_implemented | 3 | other | solved |  |  | `sparta/core/sparta.py:16-24` | 论文要求对每个 (sub)operator 执行量化特化；artifact 链中特化调用被注释、重建为直通，未执行任何循环级特化。 |
| F068 | 论 | not_implemented | 3 | other | always |  |  | `sparta/propagation/talgebra.py:4-17` | 论文要求可注册新算子规则；代码无注册机制，新增算子需改源码 |
| F069 | 论 | not_implemented | 3 | other | always |  |  | `sparta/specialization/specialize_kernel.py:18-42` | 无 TransformOp 级 S 初始化 |
| F070 | 论 | not_implemented | 3 | other | always |  |  | `sparta/specialization/specialize_kernel.py:18-42` | 论文要求组合为图 G；代码无图构造步骤 |
| F071 | 论 | not_implemented | 3 | other | solved |  |  | `sparta/specialization/specialize_kernel.py:44-77` | 依赖存在但未被该判定消费，属未接线而非实现 |
| F072 | 论 | not_implemented | 3 | other | solved |  |  | `sparta/transformation/optimize_model.py:29-54` | 论文要求特化 tiling 对齐指令形状；artifact 入口链无 tiling 生成步骤。 |
| F073 | 论 | not_implemented | 3 | other | solved |  |  | `sparta/transformation/optimize_model.py:29-54` | 论文要求 DP4A 重排+替换；artifact 入口链无此步骤。 |
| F074 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求 while 搜索；artifact 路径仅单遍枚举 |
| F075 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 论文要求按 TeSA 位宽选指令；artifact 链未调用特化，位宽选择步骤不存在。 |
| F076 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 实验路径未执行 specialization 内核选择，且无 block==shape→通用稀疏内核的代码路径；依赖存在不等于执行路径存在。 |
| F077 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/transform_policy.py:158-191` | 实验路径未运行内核选择，且无 block==shape 的稠密回退分支。 |
| F078 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/transform_policy.py:172-191` | 论文要求从枚举结果选最佳；代码无候选集合，择优逻辑被注释 |
| F079 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/weighted_block_cover.py:7-24` | artifact 路径无 13 块大小评估入口 |
| F080 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/weighted_block_cover.py:7-24` | artifact 路径无零稀疏延迟测量入口 |
| F081 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/weighted_block_cover.py:7-24` | 论文要求 latency/块数；代码无该计算，E2 除法语义不同（按覆盖元素数分摊） |
| F082 | 论 | not_implemented | 3 | other | always |  |  | `sparta/transformation/weighted_block_cover.py:47-102` | 论文要求过稀疏时枚举所有块大小组合并选最优；代码无枚举、无最优选择、无触发条件 |
