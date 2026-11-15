# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；flexprefill）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/flexprefill/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **67 条 limitation**（代码侧 + 论文侧），去重后是 **65 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/flexprefill/limitations_for_tests.json`。

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
| flexprefill | 46 | 19 | 0 | 65 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 34 | 0 | 6 | 6 | 0 | 0 | 0 | 46 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 9 | 10 | 19 |
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
| 代码侧 | 16 | 13 | 17 | 46 |
| 论文侧 | 0 | 9 | 10 | 19 |
| 两侧合并 | 0 | 0 | 0 | 0 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 31 | 10 | 1 | 0 | 0 | 0 | 4 | 46 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 19 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 38 | 0 | 1 | 0 | 7 | 0 | 0 | 0 | 46 |
| 论文侧 | 3 | 0 | 0 | 15 | 0 | 0 | 0 | 1 | 19 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 5 | 10 | 1 | 30 | 46 |
| 论文侧 | 0 | 0 | 0 | 19 | 19 |
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

### 代码侧 · undisclosed · p1 · 有别名：`flexprefill-F003`

```json
{
 "finding_id": "flexprefill-F003",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "real_but_minor",
 "summary": "When num_q_heads % num_kv_heads != 0: GQA requires the number of query heads to be a multiple of KV heads; otherwise execution stops. (flex_prefill/ops/flex_prefill_attention.py:247)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "num_q_heads % num_kv_heads != 0",
  "path_prefix": [],
  "aliases": {
   "num_q_heads": "q.shape[2]",
   "num_kv_heads": "k.shape[2]"
  },
  "trigger": {
   "num_q_heads": 5,
   "num_kv_heads": 4,
   "q.shape[2]": 5,
   "k.shape[2]": 4
  },
  "contrast": {
   "num_q_heads": 5,
   "num_kv_heads": 5,
   "q.shape[2]": 5,
   "k.shape[2]": 5
  },
  "atoms": {
   "k.shape[2]": {
    "kind": "derived",
    "sort": "int"
   },
   "num_kv_heads": {
    "kind": "local",
    "sort": "int"
   },
   "num_q_heads": {
    "kind": "local",
    "sort": "int"
   },
   "q.shape[2]": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "location": "flex_prefill/ops/flex_prefill_attention.py:247"
 },
 "limitations": [
  {
   "limitation_id": "CL-B009",
   "origin": "code",
   "condition_text": "num_q_heads % num_kv_heads != 0",
   "effect_text": "GQA requires the number of query heads to be a multiple of KV heads; otherwise execution stops.",
   "code_evidence": [
    "flex_prefill/ops/flex_prefill_attention.py:247-247"
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

### 代码侧 · stated_differently（文档说得比代码弱）：`flexprefill-F019`

```json
{
 "finding_id": "flexprefill-F019",
 "category": "stated_differently",
 "priority": 2,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "worth_testing",
 "summary": "When not (\"llama\" in model_name.lower() or \"glm\" in model_name.lower() or \"qwen2\" in model_name.lower()): Any HF model whose class name lacks llama/glm/qwen2 is rejected outright. (flex_prefill/modules/patch.py:320)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "not (\"llama\" in model_name.lower() or \"glm\" in model_name.lower() or \"qwen2\" in model_name.lower())",
  "path_prefix": [],
  "trigger": {
   "'llama' in model_name.lower()": false,
   "'glm' in model_name.lower()": false,
   "'qwen2' in model_name.lower()": false
  },
  "contrast": {
   "'llama' in model_name.lower()": true,
   "'glm' in model_name.lower()": false,
   "'qwen2' in model_name.lower()": false
  },
  "atoms": {
   "'glm' in model_name.lower()": {
    "kind": "predicate",
    "sort": "bool"
   },
   "'llama' in model_name.lower()": {
    "kind": "predicate",
    "sort": "bool"
   },
   "'qwen2' in model_name.lower()": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "location": "flex_prefill/modules/patch.py:320"
 },
 "limitations": [
  {
   "limitation_id": "CL-B006",
   "origin": "code",
   "condition_text": "not (\"llama\" in model_name.lower() or \"glm\" in model_name.lower() or \"qwen2\" in model_name.lower())",
   "effect_text": "Any HF model whose class name lacks llama/glm/qwen2 is rejected outright.",
   "code_evidence": [
    "flex_prefill/modules/patch.py:320-320"
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
   "quote": "Currently, `flex_prefill.patch_model` only supports the following models: - LLaMA: [meta-llama/Meta-Llama-3.1-8B-Instru…"
  }
 ],
 "rationale": "3b: weaker in readme; 3b weaker; priority 2: stated_differently"
}
```

### 代码侧 · docs_only（README / docstring 写了，论文没写）：`flexprefill-F039`

```json
{
 "finding_id": "flexprefill-F039",
 "category": "docs_only",
 "priority": 3,
 "effect_type": "path_change",
 "scope_status": "unknown",
 "review": "real_but_minor",
 "summary": "When pattern == \"default\": For the default pattern, patch_llama_attention returns without patching, leaving the original dense attention implementation in place. (flex_prefill/modules/patch.py:114)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "pattern == \"default\"",
  "path_prefix": [],
  "trigger": {
   "pattern": "default"
  },
  "contrast": {
   "pattern": {
    "not_in": [
     "default"
    ]
   }
  },
  "atoms": {
   "pattern": {
    "kind": "category",
    "sort": "str"
   }
  },
  "location": "flex_prefill/modules/patch.py:114"
 },
 "limitations": [
  {
   "limitation_id": "CL-B002",
   "origin": "code",
   "condition_text": "pattern == \"default\"",
   "effect_text": "For the default pattern, patch_llama_attention returns without patching, leaving the original dense attention implementation in place.",
   "code_evidence": [
    "flex_prefill/modules/patch.py:114-114"
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
   "quote": "- 'default': Default attention mechanism with no additional configuration."
  }
 ],
 "rationale": "3b: found in docstring; priority 3: docs_only, path_change effect"
}
```

### 代码侧 · state（事件序列）：`flexprefill-F012`

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
  "trigger": {
   "causal_mask is None": true,
   "batch_size": 1,
   "q_len": 385,
   "q.shape[1]": 1,
   "k.shape[1]": 1,
   "head_dim": 32,
   "block_size": 128,
   "min_budget": 384
  },
  "contrast": {
   "causal_mask is None": false,
   "batch_size": 1,
   "q_len": 385,
   "q.shape[1]": 1,
   "k.shape[1]": 1,
   "head_dim": 32,
   "block_size": 128,
   "min_budget": 384
  },
  "atoms": "... 8 atoms, see json",
  "note": "local definitions in the checked function, not used by the solver because the path prefix also holds caller conditions",
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
 "rationale": "3b: not_found; priority 1: undisclosed, state effect, witness reaches it; related (candidate pair, judged different): flexprefill-F031, flexprefill-F032, flexprefill-F033, flexprefill-F034"
}
```

### 代码侧 · infeasible（多半走不到，p3）：`flexprefill-F041`

```json
{
 "finding_id": "flexprefill-F041",
 "category": "stated_differently",
 "priority": 3,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When not (q.dtype == torch.bfloat16): AssertionError (flex_prefill/ops/flex_prefill_attention.py:868)",
 "witness_hint": {
  "kind": "input_value",
  "status": "infeasible",
  "condition": "not (q.dtype == torch.bfloat16)",
  "path_prefix": [
   "batch_size == 1",
   "not (q_len == 1)",
   "q.shape[1] == k.shape[1]",
   "head_dim in {16, 32, 64, 128}",
   "block_size in {16, 32, 64, 128}",
   "not (q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size))",
   "not (q.shape[1] > 1)",
   "q_len == 1"
  ],
  "note": "no values satisfy path prefix, condition and scope together",
  "location": "flex_prefill/ops/flex_prefill_attention.py:868"
 },
 "limitations": [
  {
   "limitation_id": "CL-X025",
   "origin": "code",
   "condition_text": "not (q.dtype == torch.bfloat16)",
   "effect_text": "AssertionError",
   "code_evidence": [
    "flex_prefill/ops/flex_prefill_attention.py:868-868"
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
 "rationale": "3b: weaker in readme; 3b weaker; priority 3: unreachable: condition contradicts its path prefix"
}
```

### 论文侧 · impl_deviates · always：`flexprefill-F057`

```json
{
 "finding_id": "flexprefill-F057",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求的上界推导在实验路径无对应实现或检验",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "experiments/scripts/flex_prefill/ruler.sh:21-29"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The paper's upper-bound derivation (single query position, a_k ≤ a_S / a_k ≤ 1−a_S) has no corresponding implem…",
  "location": "experiments/scripts/flex_prefill/ruler.sh:21-29"
 },
 "limitations": [
  {
   "limitation_id": "flexprefill-gap-M11-B01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的 flex_prefill 包 + experiments/scripts/flex_prefill/ruler.sh（flex_prefill_gamma=0.95 配置）构成的实验路径；无独立推导/证明构建产物. …",
   "effect_text": "论文要求的上界推导在实验路径无对应实现或检验",
   "code_evidence": [
    "experiments/scripts/flex_prefill/ruler.sh:21-29"
   ],
   "paper_quote": "= (1−aS) LX j=1 \\|vj\\|"
  },
  {
   "limitation_id": "flexprefill-gap-M11-A04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 pinned commit 的 flex_prefill 包 + experiments/scripts/flex_prefill/ruler.sh（flex_prefill_gamma=0.95 配置）构成的实验路径；无独立推导/证明构建产物. …",
   "effect_text": "同上",
   "code_evidence": [
    "experiments/scripts/flex_prefill/ruler.sh:21-29"
   ],
   "paper_quote": "LetaS =P j∈Saj. Then, ak≤ aS fork∈ S, and ak≤ 1−aS fork̸∈ S."
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; merged (LLM: same issue): flexprefill-gap-M11-A04; priority 3: not_implemented, other effect; related (candidate pair, judged different): flexprefill-F058, flexprefill-F059, flexprefill-F060, flexprefill-F061, flexprefill-F062, flexpre…"
}
```

### 论文侧 · LLM 写出条件并求解：`flexprefill-F032`

```json
{
 "finding_id": "flexprefill-F032",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文取累计和 ≥γ 的最小前缀长度 K；代码保留累计和 ≤γ*num_blocks 的项，边界条件与阈值尺度均不同，且未显式求 K",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "gamma != gamma * num_blocks",
  "path_prefix": [],
  "trigger": {
   "gamma": 2,
   "num_blocks": 2
  },
  "contrast": {
   "gamma": 2,
   "num_blocks": 1
  },
  "atoms": {
   "gamma": {
    "kind": "input",
    "sort": "int"
   },
   "num_blocks": {
    "kind": "input",
    "sort": "int"
   }
  },
  "code_locations": [
   "flex_prefill/ops/flex_prefill_attention.py:1661-1779",
   "flex_prefill/ops/flex_prefill_attention.py:1588-1598"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "location": "flex_prefill/ops/flex_prefill_attention.py:1661-1779"
 },
 "limitations": [
  {
   "limitation_id": "flexprefill-gap-M07-B05",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一 Triton/PyTorch 路径：triton_bnhd_pool、torch_bhn_sumpool、score_cover_idx、transform_veritcal_slash_idx 及 flex_prefill_attention 内…",
   "effect_text": "同上",
   "code_evidence": [
    "flex_prefill/ops/flex_prefill_attention.py:1661-1779",
    "flex_prefill/ops/flex_prefill_attention.py:1588-1598"
   ],
   "paper_quote": "Ia← argsort( ¯A) # Obtain the minimum computational budget making the sum of the scores exceedsγ K← min{k :P i∈Ia[1:k] ¯A[i]≥γ}"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; effect_text '同上' expanded from conformance.json local_entry; priority 2: impl_deviates; related (candidate pair, judged different): flexprefill-F012, flexprefill-F025, flexprefill-F031, flexprefill-F050"
}
```

### 论文侧 · not_implemented：`flexprefill-F056`

```json
{
 "finding_id": "flexprefill-F056",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求单卡 A100 80GB；脚本未固定设备数量或型号，accelerate 可多进程运行",
 "witness_hint": {
  "kind": "input_value",
  "status": "no_condition",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "experiments/scripts/flex_prefill/ruler.sh:16-45",
   "experiments/scripts/flex_prefill/infinitebench.sh:20-65"
  ],
  "note": "not decided by input values: The gap concerns hardware/device configuration (single A100 80GB vs. accelerate multi-process/multi-GPU), which is not determined by any input value in the shown code.",
  "location": "experiments/scripts/flex_prefill/ruler.sh:16-45"
 },
 "limitations": [
  {
   "limitation_id": "flexprefill-gap-M12-A05",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: experiments/scripts/flex_prefill/{ruler.sh,infinitebench.sh} + experiments/benchmark/{run_ruler.py,run_infinitebench.py} 实验路径，含…",
   "effect_text": "论文要求单卡 A100 80GB；脚本未固定设备数量或型号，accelerate 可多进程运行",
   "code_evidence": [
    "experiments/scripts/flex_prefill/ruler.sh:16-45",
    "experiments/scripts/flex_prefill/infinitebench.sh:20-65"
   ],
   "paper_quote": "Our experiments are conducted in a computing environment equipped with a single NVIDIA A100 GPU with 80GB of memory."
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; priority 3: not_implemented, other effect"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### flexprefill（65 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved | ✓ | `flex_prefill/modules/patch.py:123` | When not isinstance(model, LlamaForCausalLM): Patching a non-LlamaForCausalLM model with a non-defa… |
| F002 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/modules/patch.py:241` | When not isinstance(model, Qwen2ForCausalLM): Patching a non-Qwen2ForCausalLM model with a non-defa… |
| F003 | 代 | undisclosed | 1 | reject | solved | ~ | `flex_prefill/ops/flex_prefill_attention.py:247` | When num_q_heads % num_kv_heads != 0: GQA requires the number of query heads to be a multiple of KV… |
| F004 | 代 | undisclosed | 1 | reject | trigger_only |  | `flex_prefill/ops/flex_prefill_attention.py:865` | When not (q_len == 1): AssertionError |
| F005 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1219` | When not (q_len == k_len): AssertionError |
| F006 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1240-1244` | When not (isinstance(block_idx, list) and isinstance(block_idx[0], list) and isinstance(block_idx[0… |
| F007 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1245` | When not (len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads): AssertionError |
| F008 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1256` | When not (num_block <= total_q_blocks * (total_q_blocks + 1) // 2): AssertionError |
| F009 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1258` | When not (num_q_heads % num_kv_heads == 0): AssertionError |
| F010 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1450` | When not (d in {16, 32, 64, 128}): AssertionError |
| F011 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1451` | When not (kernel_size in {16, 32, 64, 128, 256, 512}): AssertionError |
| F012 | 代 | undisclosed | 1 | state | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1695-1698` | When causal_mask is None # first call only: module-level cache initialised on first call and reused |
| F013 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1836` | When not (q.shape[1] == k.shape[1]): AssertionError |
| F014 | 代 | undisclosed | 1 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1837` | When not (head_dim in {16, 32, 64, 128}): AssertionError |
| F015 | 代 | undisclosed | 1 | reject | solved | ~ | `flex_prefill/ops/vertical_slash_attention.py:265` | When q_len != k_len: Rejects inputs where query and key sequence lengths differ, so no cross-length… |
| F016 | 代 | undisclosed | 1 | reject | solved | ~ | `flex_prefill/ops/vertical_slash_attention.py:552` | When head_dim not in {16, 32, 64, 128}: Caller-supplied head_dim outside the fixed set aborts execu… |
| F017 | 代 | undisclosed | 2 | path_change | solved | ~ | `flex_prefill/modules/patch.py:69` | When pattern == "minfer": For minfer, the config is loaded from a hard-coded JSON file chosen by cf… |
| F018 | 代 | undisclosed | 2 | path_change | solved | ✓ | `flex_prefill/modules/patch.py:313` | When "llama" in model_name.lower(): Model class name selects which patch_*_attention implementation… |
| F019 | 代 | stated_differently | 2 | reject | solved | ✓ | `flex_prefill/modules/patch.py:320` | When not ("llama" in model_name.lower() or "glm" in model_name.lower() or "qwen2" in model_name.low… |
| F020 | 代 | undisclosed | 2 | path_change | solved | ✓ | `flex_prefill/modules/patch.py:424` | When kv_cache is None or prefill_meta.block_tables is None or prefill_meta.block_tables.numel() == … |
| F021 | 代 | undisclosed | 2 | path_change | solved | ~ | `flex_prefill/modules/patch.py:501` | When "attention" in type(m).__name__.lower() and hasattr(m, "impl"): Only modules whose class name … |
| F022 | 代 | stated_differently | 2 | reject | solved | ✓ | `flex_prefill/ops/flex_prefill_attention.py:672` | When q.dtype != torch.bfloat16: triton_flash_attention rejects non-bfloat16 queries before dispatch… |
| F023 | 代 | stated_differently | 2 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1218` | When not (q.dtype == torch.bfloat16): AssertionError |
| F024 | 代 | stated_differently | 2 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1222-1226` | When not (block_size in {32, 64, 128}): 'only support block size in {32, 64, 128} if head_dim <= 12… |
| F025 | 代 | undisclosed | 2 | path_change | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1727` | When kl_div < tau: per-element branch stored in block_sparse_mask |
| F026 | 代 | undisclosed | 2 | path_change | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1842-1854` | When q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size): returns via fla… |
| F027 | 代 | stated_differently | 2 | reject | solved | ~ | `flex_prefill/ops/vertical_slash_attention.py:264` | When q.dtype != torch.bfloat16: Rejects any query tensor not in bfloat16, so callers using fp16/fp3… |
| F028 | 代 | undisclosed | 2 | path_change | solved | ~ | `flex_prefill/ops/vertical_slash_attention.py:557` | When seq_len <= min(vertical_size, slash_size) * block_size: For short sequences the sparse vertica… |
| F029 | 代 | undisclosed | 2 | path_change | solved | ~ | `flex_prefill/ops/vertical_slash_attention.py:570` | When seq_len <= 16 * 1024: Sequence length selects between the vertical/slash Triton kernel (<=16k)… |
| F030 | 论 | impl_deviates | 2 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1588-1591` | 论文要求最小 k 使累计≥γ；代码取累计>γ 的最小 k（累计恰等于 γ 时多选一条），且 //128+1 放大、min/max_budget 覆盖，K_v 不再是论文定义的最小前缀（artifac… |
| F031 | 论 | impl_deviates | 2 | other | always |  | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | 论文要求先除以 Σ¯A 再展平；代码未归一化，改以放大阈值补偿 |
| F032 | 论 | impl_deviates | 2 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | 论文取累计和 ≥γ 的最小前缀长度 K；代码保留累计和 ≤γ*num_blocks 的项，边界条件与阈值尺度均不同，且未显式求 K |
| F033 | 论 | impl_deviates | 2 | other | always |  | `flex_prefill/ops/flex_prefill_attention.py:1661-1779` | 论文要求 S 为 Ia 前 K 项；代码把 query-aware 前缀与 vertical/slash 索引取并集，S 不是纯 Ia[1:K] |
| F034 | 论 | impl_deviates | 2 | other | always |  | `flex_prefill/ops/flex_prefill_attention.py:1676-1706` | 论文要求 pool(Q̂)（块池化，保留每块一个向量）与 pool(K) 相乘；代码把 Q̂ 的 block_size 行压成单一均值向量，得到 1×num_blocks 的分布，而非 num_bl… |
| F035 | 论 | impl_deviates | 2 | other | always |  | `flex_prefill/ops/flex_prefill_attention.py:1705-1716` | 池化内核无法表达论文二维 sumpool(softmax 矩阵)，实际 â 为列和向量 |
| F036 | 论 | impl_deviates | 2 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1707-1713` | 实验配置的 1024 预算未转化为每 head 最终激活 token 数下限，Query-Aware 头无下限 |
| F037 | 论 | impl_deviates | 2 | other | always |  | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | ā 角色正确；â 角色由 vertical 承担，但 vertical 非论文 sumpool(softmax(Q̂Kᵀ/√d)) 块和，真实分布操作数被替换（artifact 范围：â 操作数非论… |
| F038 | 论 | impl_deviates | 2 | other | always |  | `flex_prefill/ops/flex_prefill_attention.py:1718-1729` | 论文 Algorithm 2 以 JSD<τ 返回 pattern(query_specific/vertical_slash)；代码不返回模式，而用同一阈值改写预算并继续 vertical/sla… |
| F039 | 代 | docs_only | 3 | path_change | solved | ~ | `flex_prefill/modules/patch.py:114` | When pattern == "default": For the default pattern, patch_llama_attention returns without patching,… |
| F040 | 代 | undisclosed | 3 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:88-96` | When not ('h100' in gpu_name) and not ('a100' in gpu_name) and not ('4090' in gpu_name): if head_la… |
| F041 | 代 | stated_differently | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:868` | When not (q.dtype == torch.bfloat16): AssertionError |
| F042 | 代 | undisclosed | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:869` | When not (head_dim in {16, 32, 64, 128}): 'only support head_dim in {16, 32, 64, 128}' |
| F043 | 代 | docs_only | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:870-875` | When not (block_size in {16, 32, 64, 128}): 'only support block size in {16, 32, 64, 128}' |
| F044 | 代 | undisclosed | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:876` | When not (num_blocks <= triton.cdiv(k_len, block_size)): AssertionError |
| F045 | 代 | undisclosed | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:878` | When not (num_q_heads % num_kv_heads == 0): AssertionError |
| F046 | 代 | undisclosed | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:1220` | When not (head_dim <= 256): 'only support head_dim <= 256' |
| F047 | 代 | undisclosed | 3 | reject | solved | ✗ | `flex_prefill/ops/flex_prefill_attention.py:1221` | When head_dim <= 128: For head_dim <= 128 only block_size in {32,64,128} is allowed; otherwise (128… |
| F048 | 代 | undisclosed | 3 | reject | infeasible |  | `flex_prefill/ops/flex_prefill_attention.py:1228-1231` | When not (block_size in {32, 64}): 'only support block size in {32, 64} if 128 < head_dim <= 256' |
| F049 | 代 | undisclosed | 3 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1270-1272` | When not (int(triton.__version__.split('.')[0]) >= 3): warnings.warn('triton version greater than 3… |
| F050 | 代 | undisclosed | 3 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1708` | When block_size != 128: hard-coded 128 in `score_cover_topk(vertical, gamma) // 128` while paramete… |
| F051 | 代 | undisclosed | 3 | other | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1787` | When not (is_flash_attn_2_available()): flash_attn_func = triton_flash_attention |
| F052 | 代 | docs_only | 3 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1824` | When not (batch_size == 1): 'only support batch size 1 for now' |
| F053 | 代 | docs_only | 3 | path_change | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1825-1835` | When q_len == 1: returns via flash_attn_func, triton_flash_attention |
| F054 | 代 | docs_only | 3 | reject | solved |  | `flex_prefill/ops/flex_prefill_attention.py:1838` | When not (block_size in {16, 32, 64, 128}): AssertionError |
| F055 | 代 | docs_only | 3 | reject | solved | ~ | `flex_prefill/ops/vertical_slash_attention.py:553` | When block_size not in {16, 32, 64, 128}: Caller-supplied block_size outside the fixed set aborts e… |
| F056 | 论 | not_implemented | 3 | other | no_condition |  | `experiments/scripts/flex_prefill/ruler.sh:16-45` | 论文要求单卡 A100 80GB；脚本未固定设备数量或型号，accelerate 可多进程运行 |
| F057 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求的上界推导在实验路径无对应实现或检验 |
| F058 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求显式连续松弛步骤；代码无该步骤 |
| F059 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求构造 Lagrangian；代码无 |
| F060 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求 KKT 条件；代码无 |
| F061 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求该代数表达；代码无 |
| F062 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求陈述该约束问题；代码无对应形式化 |
| F063 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求二值变量重写；代码无 |
| F064 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求平稳性条件；代码无 |
| F065 | 论 | not_implemented | 3 | other | always |  | `experiments/scripts/flex_prefill/ruler.sh:21-29` | 论文要求互补松弛；代码无 |
