# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；nnsmith）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/nnsmith/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **42 条 limitation**（代码侧 + 论文侧），去重后是 **38 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/nnsmith/limitations_for_tests.json`。

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
| nnsmith | 33 | 3 | 2 | 38 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 30 | 1 | 1 | 0 | 1 | 0 | 0 | 33 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| 两侧合并 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

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
| 代码侧 | 3 | 14 | 16 | 33 |
| 论文侧 | 0 | 3 | 0 | 3 |
| 两侧合并 | 0 | 2 | 0 | 2 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 3 | 19 | 0 | 0 | 0 | 0 | 11 | 33 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 3 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 |
| 论文侧 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 3 |
| 两侧合并 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 6 | 5 | 8 | 14 | 33 |
| 论文侧 | 0 | 0 | 0 | 3 | 3 |
| 两侧合并 | 1 | 0 | 0 | 1 | 2 |

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

### 代码侧 · stated_differently（文档说得比代码弱）：`nnsmith-F019`

```json
{
 "finding_id": "nnsmith-F019",
 "category": "stated_differently",
 "priority": 2,
 "effect_type": "path_change",
 "scope_status": "unknown",
 "review": "real_but_minor",
 "summary": "When random.uniform(0, 1) < self.forward_prob: A caller-configured forward_prob attribute decides whether the node is inserted by forward insertion (try_forward_insert) or backward insertion (try_backward_insert), selecting between two different graph-construction algorithms. (nnsmith/graph_gen.py:556)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "random.uniform(0, 1) < self.forward_prob",
  "path_prefix": [],
  "trigger": {
   "random.uniform(0, 1)": 1,
   "self.forward_prob": 2
  },
  "contrast": {
   "random.uniform(0, 1)": 1,
   "self.forward_prob": 1
  },
  "atoms": {
   "random.uniform(0, 1)": {
    "kind": "derived",
    "sort": "int"
   },
   "self.forward_prob": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "call_chain_status": "resolved",
  "call_chain": [
   "nnsmith/graph_gen.py::random_model_gen",
   "nnsmith/graph_gen.py::SimpleGenerator.abstract_gen",
   "nnsmith/graph_gen.py::SimpleGenerator.try_insert_node_type"
  ],
  "location": "nnsmith/graph_gen.py:556"
 },
 "limitations": [
  {
   "limitation_id": "CL-B017",
   "origin": "code",
   "condition_text": "random.uniform(0, 1) < self.forward_prob",
   "effect_text": "A caller-configured forward_prob attribute decides whether the node is inserted by forward insertion (try_forward_insert) or backward insertion (try_backward_i…",
   "code_evidence": [
    "nnsmith/graph_gen.py:556-556"
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
   "quote": "When evaluating NNSmith, for Algorithm 1 we choose between forward and backward at every insertion randomly with equal …"
  }
 ],
 "rationale": "3b: boundary_mismatch in paper; 3b boundary_mismatch; priority 2: stated_differently"
}
```

### 两侧合并：`nnsmith-F006`

```json
{
 "finding_id": "nnsmith-F006",
 "category": "undisclosed",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "worth_testing",
 "summary": "When p.grad is not None and torch.any(p.grad != 0): If all parameter gradients are zero, ConstraintCheck.true(nonzero, ...) raises, aborting the backward step ('Gradients are all zero. Cannot make progress.'). (nnsmith/materialize/torch/symbolnet.py:188)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "p.grad is not None and torch.any(p.grad != 0)",
  "path_prefix": [],
  "trigger": {
   "p.grad is None": false,
   "torch.any(p.grad != 0)": true
  },
  "contrast": {
   "p.grad is None": false,
   "torch.any(p.grad != 0)": false
  },
  "atoms": {
   "p.grad is None": {
    "kind": "predicate",
    "sort": "bool"
   },
   "torch.any(p.grad != 0)": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "call_chain_status": "resolved",
  "call_chain": [
   "nnsmith/materialize/torch/input_gen.py::PracticalHybridSearch.search_one",
   "nnsmith/materialize/torch/input_gen.py::GradSearch.search_one",
   "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
   "nnsmith/materialize/torch/symbolnet.py::SymbolNet.backward"
  ],
  "location": "nnsmith/materialize/torch/symbolnet.py:188"
 },
 "limitations": [
  {
   "limitation_id": "CL-B028",
   "origin": "code",
   "condition_text": "p.grad is not None and torch.any(p.grad != 0)",
   "effect_text": "If all parameter gradients are zero, ConstraintCheck.true(nonzero, ...) raises, aborting the backward step ('Gradients are all zero. Cannot make progress.').",
   "code_evidence": [
    "nnsmith/materialize/torch/symbolnet.py:188-188"
   ],
   "paper_quote": null
  },
  {
   "limitation_id": "CL-B029",
   "origin": "code",
   "condition_text": "nonzero is False",
   "effect_text": "If the loss has zero gradient w.r.t. all trainable tensors (e.g. the NaN/Inf came from a non-differentiable path), `backward` raises ConstraintError; `grad_inp…",
   "code_evidence": [
    "nnsmith/materialize/torch/symbolnet.py:191-191"
   ],
   "paper_quote": null
  },
  {
   "limitation_id": "nnsmith-gap-M08-B06",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: experiments/nnsmith_gen_onnx.py::nnsmith_gen_once 与 nnsmith/materialize/torch/__init__.py::TorchModel.refine_weights 经Practical…",
   "effect_text": "零梯度触发搜索终止+外层重试，而非 Line 11 随机重启",
   "code_evidence": [
    "nnsmith/materialize/torch/symbolnet.py:229-293",
    "nnsmith/materialize/torch/symbolnet.py:151-217",
    "nnsmith/materialize/torch/__init__.py:31-41"
   ],
   "paper_quote": "if⟨𝑋,𝑊⟩ not changed then // Zero gradients"
  },
  {
   "limitation_id": "nnsmith-gap-M08-B08",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: experiments/nnsmith_gen_onnx.py::nnsmith_gen_once 与 nnsmith/materialize/torch/__init__.py::TorchModel.refine_weights 经Practical…",
   "effect_text": "零梯度未 continue OUTER，仅外层 max_sample 重试",
   "code_evidence": [
    "nnsmith/materialize/torch/symbolnet.py:229-293",
    "nnsmith/materialize/torch/__init__.py:31-41",
    "experiments/nnsmith_gen_onnx.py:42-48"
   ],
   "paper_quote": "continue OUTER // Go to Line 3"
  }
 ],
 "verifications": [
  {
   "result": "not_found",
   "documented_in": [],
   "quote": null
  },
  {
   "result": "not_found",
   "documented_in": [],
   "quote": null
  }
 ],
 "rationale": "3b: not_found; merged (LLM: same issue): CL-B029, nnsmith-gap-M08-B06, nnsmith-gap-M08-B08; paper side also reports: impl_deviates; priority 2: impl_deviates; related (candidate pair, judged different): nnsmith-F024, nnsmith-F025"
}
```

### 论文侧 · LLM 写出条件并求解：`nnsmith-F028`

```json
{
 "finding_id": "nnsmith-F028",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "artifact 路径不存在 pad 的 0 箱/负箱特化",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "self.extra_attrs[\"type\"] in (\"ConstPad\", \"ReplicatePad\", \"ReflectPad\")",
  "path_prefix": [],
  "trigger": {
   "self.extra_attrs['type']": "ConstPad"
  },
  "contrast": {
   "self.extra_attrs['type']": {
    "not_in": [
     "ConstPad",
     "ReflectPad",
     "ReplicatePad"
    ]
   }
  },
  "atoms": {
   "self.extra_attrs['type']": {
    "kind": "category",
    "sort": "str"
   }
  },
  "code_locations": [
   "nnsmith/abstract/op.py:1053-1080",
   "nnsmith/graph_gen.py:50-70"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "call_chain_status": "module_level",
  "call_chain": [
   "nnsmith/abstract/op.py::<module>"
  ],
  "location": "nnsmith/abstract/op.py:1053-1080"
 },
 "limitations": [
  {
   "limitation_id": "nnsmith-gap-M12-B03",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的规格+图生成路径（op.py + graph_gen.py 的 concretize_op/checked_type_transfer）；无独立实验脚本承载该机制. Paper precondition: Defaul…",
   "effect_text": "artifact 路径不存在 pad 的 0 箱/负箱特化",
   "code_evidence": [
    "nnsmith/abstract/op.py:1053-1080",
    "nnsmith/graph_gen.py:50-70"
   ],
   "paper_quote": "for the “padding” attribute in ConstPad, ReplicatePad, and ReflectPad, we add both the 0-bin and negative bins"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; priority 2: impl_deviates; related (candidate pair, judged different): nnsmith-F029"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### nnsmith（38 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved | ~ | `nnsmith/abstract/op.py:1563` | When gres_config not in ("3", "4", "5"): An unrecognized NNSMITH_GRES environment value causes a Va… |
| F003 | 代 | undisclosed | 1 | reject | solved |  | `nnsmith/cli/fuzz.py:180` | When isinstance(e, InternalError): InternalError from make_testcase is propagated, aborting the fuz… |
| F004 | 代 | contradicts_docs | 1 | reject | solved |  | `nnsmith/graph_gen.py:260` | When self.check_sat() != z3.sat: After adding the memory-limit constraint, an unsatisfiable (or unk… |
| F009 | 代 | undisclosed | 2 | path_change | solved | ~ | `nnsmith/abstract/arith.py:74` | When carry and max(left_size, right_size) >= ARITH_MAX_WIDTH: For addition, the extra carry bit is … |
| F010 | 代 | undisclosed | 2 | path_change | solved | ~ | `nnsmith/abstract/arith.py:79` | When mult and (right.size() + left.size()) >= ARITH_MAX_WIDTH: For multiplication, when the combine… |
| F011 | 代 | undisclosed | 2 | path_change | solved |  | `nnsmith/abstract/op.py:25` | When FLOPS_LIM == "off": Setting NNSMITH_FLOPS_LIM=off sets FLOPS_LIM to None, disabling the FLOPs … |
| F012 | 代 | undisclosed | 2 | path_change | solved | ✓ | `nnsmith/abstract/op.py:910` | When Z3_CONS_FLOPS: A module-level flag decides whether the FLOPS upper-bound constraint is added t… |
| F014 | 代 | undisclosed | 2 | path_change | solved | ✓ | `nnsmith/abstract/op.py:1587` | When os.getenv("NNSMITH_CONS_RESHAPE", "off") != "off": The environment variable NNSMITH_CONS_RESHA… |
| F015 | 代 | undisclosed | 2 | path_change | solved |  | `nnsmith/cli/fuzz.py:60` | When not self.crash_safe and self.test_timeout is not None: Setting fuzz.test_timeout without crash… |
| F016 | 代 | undisclosed | 2 | path_change | solved |  | `nnsmith/cli/model_gen.py:31` | When cfg["backend"]["type"] is not None: A caller-supplied backend type decides whether a BackendFa… |
| F017 | 代 | undisclosed | 2 | path_change | solved | ✓ | `nnsmith/graph_gen.py:256` | When NNSMITH_LIMNF_V == "0": Branches the memory-limit constraint: v0 adds nnsmith_le(self.n_floats… |
| F018 | 代 | undisclosed | 2 | path_change | solved |  | `nnsmith/graph_gen.py:258` | When NNSMITH_LIMNF_V == "1": With NNSMITH_LIMNF_V=1 the per-op float-count constraints accumulated … |
| F019 | 代 | stated_differently | 2 | path_change | solved | ~ | `nnsmith/graph_gen.py:556` | When random.uniform(0, 1) < self.forward_prob: A caller-configured forward_prob attribute decides w… |
| F020 | 代 | undisclosed | 2 | path_change | solved |  | `nnsmith/graph_gen.py:944` | When idx in disable: For each reshape group, one randomly chosen destination dimension is disabled … |
| F021 | 代 | undisclosed | 2 | path_change | solved | ✓ | `nnsmith/materialize/torch/__init__.py:47` | When self.sat_inputs is None: When no satisfying inputs were found (sat_inputs is None), make_oracl… |
| F022 | 代 | undisclosed | 2 | path_change | solved |  | `nnsmith/materialize/torch/input_gen.py:93` | When all([DType.is_float(v.dtype) for _, v in self.net.input_like.items()]): Whether all model inpu… |
| F006 | 合 | undisclosed | 2 | other | solved | ✓ | `nnsmith/materialize/torch/symbolnet.py:188` | When p.grad is not None and torch.any(p.grad != 0): If all parameter gradients are zero, Constraint… |
| F024 | 合 | undisclosed | 2 | other | solved |  | `nnsmith/materialize/torch/symbolnet.py:234` | When max_time is None: The gradient-based input search budget is taken from the environment (NNSMIT… |
| F025 | 代 | undisclosed | 2 | path_change | solved | ✓ | `nnsmith/materialize/torch/symbolnet.py:238` | When tensor.data.dtype.is_floating_point: Only floating-point input tensors are wrapped as trainabl… |
| F028 | 论 | impl_deviates | 2 | other | solved |  | `nnsmith/abstract/op.py:1053-1080` | artifact 路径不存在 pad 的 0 箱/负箱特化 |
| F029 | 论 | impl_deviates | 2 | other | always |  | `nnsmith/abstract/op.py:1332-1360` | artifact 路径不存在 Conv2d padding 的 0 箱特化 |
| F030 | 论 | impl_deviates | 2 | other | solved |  | `nnsmith/graph_gen.py:1029-1058` | 论文要求每轮随机选一半；代码仅首轮随机，后续轮固定丢弃后半段 |
| F013 | 代 | undisclosed | 3 | other | solved |  | `nnsmith/abstract/op.py:1552` | When gres_config != "4": The environment variable NNSMITH_GRES selects the reshape grouping strateg… |
| F002 | 代 | undisclosed | 3 | other | solved |  | `nnsmith/abstract/op.py:2083` | When not check_sat(): If the requested output rank cannot be satisfied by the rank-increment loop (… |
| F031 | 代 | undisclosed | 3 | other | solved | ✗ | `nnsmith/graph_gen.py:190` | When int(os.getenv("NNSMITH_BITS", 30)) != 30: The number of bits used to split the integer-domain … |
| F005 | 代 | undisclosed | 3 | other | solved | ~ | `nnsmith/graph_gen.py:524` | When isinstance(op, Expand) and oshape.ndims < op.expand_last_dim: Placeholder shapes with fewer di… |
| F032 | 代 | undisclosed | 3 | other | solved | ✗ | `nnsmith/graph_gen.py:834` | When os.getenv("NNSMITH_LB", "off") == "off": The upper-bound constraint on slice start/end paramet… |
| F033 | 代 | undisclosed | 3 | other | solved | ✗ | `nnsmith/graph_gen.py:984` | When os.getenv("NNSMITH_G_CONFIG", "1") != "1": The environment variable NNSMITH_G_CONFIG selects w… |
| F034 | 代 | undisclosed | 3 | path_change | solved | ✗ | `nnsmith/graph_gen.py:1016` | When config is None: If the op class has no entry in param_config, extra_constraints returns an emp… |
| F035 | 代 | undisclosed | 3 | path_change | solved | ✗ | `nnsmith/graph_gen.py:1044` | When len(cons) == 0 or random.uniform(0, 1) > self.constrain_prob: Guidance constraints for a node … |
| F036 | 代 | paper_stated | 3 | path_change | solved | ✗ | `nnsmith/graph_gen.py:1052` | When self.check_sat(*cur_cons) != z3.sat: If the collected guidance constraints are unsatisfiable, … |
| F037 | 代 | undisclosed | 3 | path_change | solved | ✗ | `nnsmith/graph_gen.py:1054` | When len(cur_cons) == 0: When all guidance constraints are dropped due to unsat, the loop breaks an… |
| F023 | 代 | undisclosed | 3 | other | solved |  | `nnsmith/materialize/torch/input_gen.py:98` | When self.differentiable is False: The variant is decided by a single probe forward pass on random … |
| F026 | 代 | undisclosed | 3 | other | solved |  | `nnsmith/materialize/torch/symbolnet.py:358` | When output_tensors[i].grad_fn is None: `differentiable` is reset to True at the start of every for… |
| F038 | 代 | undisclosed | 3 | path_change | solved | ✗ | `nnsmith/materialize/torch/symbolnet.py:382` | When self.check_intermediate_numeric or (self.use_gradient and not self.stop_updating_loss): Constr… |
| F007 | 代 | undisclosed | 3 | other | solved | ✓ | `nnsmith/materialize/torch/symbolnet.py:385` | When loss_fn.dispatch(type(op)) is not None: If an op produces NaN/Inf but has no registered loss f… |
| F027 | 代 | undisclosed | 3 | other | solved |  | `nnsmith/materialize/torch/symbolnet.py:403` | When vul_op_loss is None: When an op produces NaN/Inf but has no registered loss function (`loss_fn… |
| F008 | 代 | undisclosed | 3 | other | solved |  | `nnsmith/materialize/torch/symbolnet.py:421` | When self.loss is not None: If two vulnerable ops both produce NaN/Inf in the same forward pass, th… |
