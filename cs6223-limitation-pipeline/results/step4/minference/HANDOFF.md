# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；minference）

> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `results/step4/minference/limitations_for_tests.json`。schema 0.2.0，witness 格式 witness-v2。方法细节见 `docs/09_step4_findings.md`。

## 一句话

1 篇论文共 **82 条 limitation**（代码侧 + 论文侧），去重后是 **73 条 Finding**。每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），还附带它背后的全部原始记录。你要用的文件只有一个：`results/step4/minference/limitations_for_tests.json`。

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
| minference | 50 | 23 | 0 | 73 |

按类别：

| 来源 | undisclosed | contradicts_docs | stated_differently | docs_only | paper_stated | impl_deviates | not_implemented | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 15 | 8 | 23 |
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
| 代码侧 | 19 | 22 | 9 | 50 |
| 论文侧 | 0 | 15 | 8 | 23 |
| 两侧合并 | 0 | 0 | 0 | 0 |

按 effect_type：

| 来源 | reject | path_change | state | accuracy | resource | performance | other | 合计 |
|---|---|---|---|---|---|---|---|---|
| 代码侧 | 15 | 23 | 5 | 0 | 0 | 0 | 7 | 50 |
| 论文侧 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 23 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

按 witness 状态：

| 来源 | solved | solved_contrast_outside_scope | trigger_only | always | infeasible | untranslatable | unknown | no_condition | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 代码侧 | 49 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 50 |
| 论文侧 | 7 | 0 | 1 | 12 | 0 | 0 | 0 | 3 | 23 |
| 两侧合并 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：

| 来源 | worth_testing | real_but_minor | wrong | unreviewed | 合计 |
|---|---|---|---|---|---|
| 代码侧 | 13 | 14 | 2 | 21 | 50 |
| 论文侧 | 0 | 0 | 0 | 23 | 23 |
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

### 代码侧 · undisclosed · p1 · 有别名：`minference-F010`

```json
{
 "finding_id": "minference-F010",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "reject",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "When not (Lq == Lk and Lk == Lv): AssertionError (minference/ops/block_sparse_flash_attention.py:126)",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "not (Lq == Lk and Lk == Lv)",
  "path_prefix": [],
  "aliases": {
   "Lq": "q.shape[-1]",
   "Lk": "k.shape[-1]",
   "Lv": "v.shape[-1]"
  },
  "trigger": {
   "Lq": 2,
   "Lk": 2,
   "Lv": 1,
   "q.shape[-1]": 2,
   "k.shape[-1]": 2,
   "v.shape[-1]": 1
  },
  "contrast": {
   "Lq": 2,
   "Lk": 2,
   "Lv": 2,
   "q.shape[-1]": 2,
   "k.shape[-1]": 2,
   "v.shape[-1]": 2
  },
  "atoms": {
   "Lk": {
    "kind": "local",
    "sort": "int"
   },
   "Lq": {
    "kind": "local",
    "sort": "int"
   },
   "Lv": {
    "kind": "local",
    "sort": "int"
   },
   "k.shape[-1]": {
    "kind": "derived",
    "sort": "int"
   },
   "q.shape[-1]": {
    "kind": "derived",
    "sort": "int"
   },
   "v.shape[-1]": {
    "kind": "derived",
    "sort": "int"
   }
  },
  "location": "minference/ops/block_sparse_flash_attention.py:126"
 },
 "limitations": [
  {
   "limitation_id": "CL-X003",
   "origin": "code",
   "condition_text": "not (Lq == Lk and Lk == Lv)",
   "effect_text": "AssertionError",
   "code_evidence": [
    "minference/ops/block_sparse_flash_attention.py:126-126"
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

### 代码侧 · state（事件序列）：`minference-F002`

```json
{
 "finding_id": "minference-F002",
 "category": "undisclosed",
 "priority": 1,
 "effect_type": "state",
 "scope_status": "unknown",
 "review": "real_but_minor",
 "summary": "When ROPE_TYPE is not None: `ROPE_TYPE` is a module-level global computed once from the *first* attention module's `rotary_emb.forward` signature and then reused for every model/layer in the process (`if ROPE_TYPE is not None: return`). Loading a second model with a different RoPE signature in the same process keeps the first model's convention, and `get_cos_sin` then calls `self.rotary_emb` wi...",
 "witness_hint": {
  "kind": "event_sequence",
  "status": "solved",
  "condition": "ROPE_TYPE is not None",
  "path_prefix": [],
  "trigger": {
   "ROPE_TYPE is None": false
  },
  "contrast": {
   "ROPE_TYPE is None": true
  },
  "atoms": {
   "ROPE_TYPE is None": {
    "kind": "predicate",
    "sort": "bool"
   }
  },
  "location": "minference/modules/minference_forward.py:30"
 },
 "limitations": [
  {
   "limitation_id": "CL-B003",
   "origin": "code",
   "condition_text": "ROPE_TYPE is not None",
   "effect_text": "`ROPE_TYPE` is a module-level global computed once from the *first* attention module's `rotary_emb.forward` signature and then reused for every model/layer in …",
   "code_evidence": [
    "minference/modules/minference_forward.py:30-30"
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
 "rationale": "3b: not_found; priority 1: undisclosed, state effect, witness reaches it"
}
```

### 论文侧 · impl_deviates · always：`minference-F043`

```json
{
 "finding_id": "minference-F043",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "实验配置未体现{(1024,4096)}，实际候选为(100,800)",
 "witness_hint": {
  "kind": "input_value",
  "status": "always",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "experiments/README.md:13-30",
   "minference/modules/minference_forward.py:99-197"
  ],
  "note": "the gap shows on every call through the cited code; any input reaching it is a witness. The A-shape candidate set is hardcoded in search_pattern (vertical_size/slash_size derived from fixed values li…",
  "location": "experiments/README.md:13-30"
 },
 "limitations": [
  {
   "limitation_id": "minference-gap-M02-A04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一离线搜索路径：experiments/README.md 的 Offline Kernel-Aware Sparse Pattern Search 命令（run_infinitebench.py --is_search --max_seq_lengt…",
   "effect_text": "同上",
   "code_evidence": [
    "minference/modules/minference_forward.py:99-197",
    "experiments/README.md:13-30"
   ],
   "paper_quote": "We set the target FLOPs t to be the same as 1k global tokens and 4k local window tokens in the A-shape pattern."
  },
  {
   "limitation_id": "minference-gap-M03-B03-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一搜索路径的配置/实验层：experiments/README.md 搜索命令(--task kv_retrieval --max_seq_length 30000 --num_eval_examples 20 --topk 1)、experiment…",
   "effect_text": "实验配置未体现{(1024,4096)}，实际候选为(100,800)",
   "code_evidence": [
    "experiments/README.md:13-30",
    "minference/modules/minference_forward.py:99-197"
   ],
   "paper_quote": "A-shape {(1024, 4096)}"
  },
  {
   "limitation_id": "minference-gap-M03-A01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一搜索路径的配置/实验层：experiments/README.md 搜索命令(--task kv_retrieval --max_seq_length 30000 --num_eval_examples 20 --topk 1)、experiment…",
   "effect_text": "配置层未体现{(1024,4096)}",
   "code_evidence": [
    "experiments/README.md:13-30",
    "minference/modules/minference_forward.py:99-197"
   ],
   "paper_quote": "A-shape {(1024, 4096)}"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; merged (LLM: same issue): minference-gap-M02-A04, minference-gap-M03-A01; priority 2: impl_deviates; related (candidate pair, judged different): minference-F003, minference-F022, minference-F044, minference-F045, minference-F050, min…"
}
```

### 论文侧 · LLM 写出条件并求解：`minference-F042`

```json
{
 "finding_id": "minference-F042",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求循环守卫 s_v≤k_s；代码用 while(1)+break，s 仅在 else 分支递增，终止由 s>=NNZ_S 决定",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "s_idx < end_m",
  "path_prefix": [
   "start_m < seqlen"
  ],
  "trigger": {
   "s_idx": 1,
   "end_m": 2,
   "start_m": 3,
   "seqlen": 4
  },
  "contrast": {
   "s_idx": 2,
   "end_m": 2,
   "start_m": 3,
   "seqlen": 4
  },
  "atoms": {
   "end_m": {
    "kind": "input",
    "sort": "int"
   },
   "s_idx": {
    "kind": "input",
    "sort": "int"
   },
   "seqlen": {
    "kind": "input",
    "sort": "int"
   },
   "start_m": {
    "kind": "input",
    "sort": "int"
   }
  },
  "code_locations": [
   "csrc/vertical_slash_index.cu:27-99",
   "csrc/kernels.cpp:7-18"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "location": "csrc/vertical_slash_index.cu:27-99"
 },
 "limitations": [
  {
   "limitation_id": "minference-gap-M08-B06-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一路径的构建/运行链：setup.py 编译 csrc/vertical_slash_index.cu + csrc/kernels.cpp 为 minference.cuda 扩展，由 pit_sparse_flash_attention_v2.py…",
   "effect_text": "同上",
   "code_evidence": [
    "csrc/vertical_slash_index.cu:27-99",
    "csrc/kernels.cpp:7-18"
   ],
   "paper_quote": "# Merge points (vertical indexes) and ranges (slash indexes) whilesv≤ks do"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; effect_text '同上' expanded from conformance.json local_entry; priority 2: impl_deviates"
}
```

### 论文侧 · not_implemented：`minference-F066`

```json
{
 "finding_id": "minference-F066",
 "category": "not_implemented",
 "priority": 3,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "实验入口未暴露或设定步长50",
 "witness_hint": {
  "kind": "input_value",
  "status": "solved",
  "condition": "is_search",
  "path_prefix": [],
  "trigger": {
   "is_search": true
  },
  "contrast": {
   "is_search": false
  },
  "atoms": {
   "is_search": {
    "kind": "input",
    "sort": "bool"
   }
  },
  "code_locations": [
   "experiments/README.md:13-30",
   "experiments/infinite_bench/args.py:60-81"
  ],
  "condition_source": "LLM (x-test-2) from the paper-side text; names checked against the cited code",
  "location": "experiments/README.md:13-30"
 },
 "limitations": [
  {
   "limitation_id": "minference-gap-M03-B02",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一搜索路径的配置/实验层：experiments/README.md 搜索命令(--task kv_retrieval --max_seq_length 30000 --num_eval_examples 20 --topk 1)、experiment…",
   "effect_text": "实验入口未暴露或设定步长50",
   "code_evidence": [
    "experiments/README.md:13-30",
    "experiments/infinite_bench/args.py:60-81"
   ],
   "paper_quote": "The step size of ChangeSpace is set to 50"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): absent; not a confirmed runtime effect; priority 3: not_implemented, other effect; related (candidate pair, judged different): minference-F043, minference-F044, minference-F045"
}
```

### 论文侧 · no_condition：`minference-F051`

```json
{
 "finding_id": "minference-F051",
 "category": "impl_deviates",
 "priority": 2,
 "effect_type": "other",
 "scope_status": "unknown",
 "review": "unreviewed",
 "summary": "论文要求 dense 注意力输出 y（含 V）；代码只算注意力权重矩阵，未形成输出",
 "witness_hint": {
  "kind": "input_value",
  "status": "no_condition",
  "condition": null,
  "path_prefix": [],
  "code_locations": [
   "minference/modules/minference_forward.py:99-197",
   "minference/modules/minference_forward.py:199-246"
  ],
  "note": "LLM gave no usable condition: names not in the cited code: is_search",
  "location": "minference/modules/minference_forward.py:99-197"
 },
 "limitations": [
  {
   "limitation_id": "minference-gap-M02-B04",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一离线搜索路径：experiments/README.md 的 Offline Kernel-Aware Sparse Pattern Search 命令（run_infinitebench.py --is_search --max_seq_lengt…",
   "effect_text": "同上",
   "code_evidence": [
    "minference/modules/minference_forward.py:99-197",
    "minference/modules/minference_forward.py:199-246"
   ],
   "paper_quote": "y← Softmax(QK⊤/ √ d)"
  },
  {
   "limitation_id": "minference-gap-M02-B05-R01",
   "origin": "paper",
   "condition_text": "Pinned inspected artifact path: 同一离线搜索路径：experiments/README.md 的 Offline Kernel-Aware Sparse Pattern Search 命令（run_infinitebench.py --is_search --max_seq_lengt…",
   "effect_text": "同上",
   "code_evidence": [
    "minference/modules/minference_forward.py:99-197",
    "experiments/README.md:13-30"
   ],
   "paper_quote": "fori← 1 to\\|ρ\\| do yi← SparseAttention(QK⊤/ √ d,ρ i)"
  }
 ],
 "verifications": [],
 "rationale": "paper side (3a static): deviates; not a confirmed runtime effect; effect_text '同上' expanded from conformance.json local_entry; merged (LLM: same issue): minference-gap-M02-B05-R01; priority 2: impl_deviates; related (candidate pair, judged different): minference-F003, minference-F022, minference-F0…"
}
```

## 7. 全部 Finding 索引

每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）。

### minference（73 条）

| ID | 侧 | 类别 | P | effect | witness | 审 | 位置 | 内容 |
|---|---|---|---|---|---|---|---|---|
| F001 | 代 | undisclosed | 1 | reject | solved |  | `minference/minference_configuration.py:56` | When config_path is None and model_name not in MODEL2PATH: If no `config_path` is given, the model … |
| F002 | 代 | undisclosed | 1 | state | solved | ~ | `minference/modules/minference_forward.py:30` | When ROPE_TYPE is not None: `ROPE_TYPE` is a module-level global computed once from the *first* att… |
| F003 | 代 | undisclosed | 1 | state | solved |  | `minference/modules/minference_forward.py:165-172` | When SEARCH_MASK is None # first call only: module-level cache initialised on first call and reused |
| F004 | 代 | undisclosed | 1 | state | solved |  | `minference/modules/minference_forward.py:390` | When "vs" in self.__dict__: Static pattern reuses vertical_topk/slash cached in self.vs from an ear… |
| F005 | 代 | undisclosed | 1 | reject | solved |  | `minference/modules/minference_forward.py:441` | When ty not in {"stream_llm", "vertical_and_slash", "block_sparse"}: The implementation is chosen b… |
| F006 | 代 | undisclosed | 1 | reject | trigger_only |  | `minference/modules/minference_forward.py:484-488` | When True: raise ValueError(f'The cache structure has changed since version v4.36. If you are using… |
| F007 | 代 | undisclosed | 1 | reject | solved | ✓ | `minference/modules/minference_forward.py:504` | When self.is_search and os.path.exists(self.config_path) and self.layer_idx < len(config_list): Wit… |
| F008 | 代 | undisclosed | 1 | state | solved |  | `minference/modules/minference_forward.py:681` | When key_states.shape[-2] != kv_seq_len: Whether SnapKV compression runs depends on `self.kv_seq_le… |
| F009 | 代 | undisclosed | 1 | reject | solved |  | `minference/modules/minference_forward.py:754` | When head_id not in self.best_pattern: The vLLM variant indexes `self.best_pattern[head_id]` direct… |
| F010 | 代 | undisclosed | 1 | reject | solved |  | `minference/ops/block_sparse_flash_attention.py:126` | When not (Lq == Lk and Lk == Lv): AssertionError |
| F011 | 代 | undisclosed | 1 | reject | solved |  | `minference/ops/block_sparse_flash_attention.py:127` | When not (Lk in {16, 32, 64, 128}): AssertionError |
| F012 | 代 | undisclosed | 1 | reject | solved |  | `minference/ops/pit_sparse_flash_attention_v2.py:149` | When not (Lq == Lk and Lk == Lv): AssertionError |
| F013 | 代 | undisclosed | 1 | reject | solved |  | `minference/ops/pit_sparse_flash_attention_v2.py:150` | When not (Lk in {16, 32, 64, 128}): AssertionError |
| F014 | 代 | undisclosed | 1 | reject | solved | ✓ | `minference/ops/streaming_kernel.py:414` | When Lk not in {16, 32, 64, 128}: Head dimension (q/k/v last dim) must be one of 16/32/64/128; othe… |
| F015 | 代 | undisclosed | 1 | reject | solved |  | `minference/ops/streaming_kernel.py:605` | When not (q.dim() == 4): AssertionError |
| F016 | 代 | undisclosed | 1 | reject | solved |  | `minference/ops/streaming_kernel.py:606` | When not (q.shape == k.shape == v.shape): AssertionError |
| F017 | 代 | undisclosed | 1 | reject | solved |  | `minference/patch.py:207` | When output_attentions: If the caller requests attention outputs, execution is aborted by the asser… |
| F018 | 代 | undisclosed | 1 | reject | solved |  | `minference/patch.py:1252` | When not isinstance(model, |
| F019 | 代 | undisclosed | 1 | reject | solved | ~ | `minference/patch.py:1253` | When not |
| F020 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/minference_configuration.py:52` | When self.attn_type in self.STASTIC_ATTENTION_TYPES: For any `attn_type` in `STASTIC_ATTENTION_TYPE… |
| F021 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:63` | When not (self.config_path is not None and os.path.exists(self.config_path) and self.layer_idx < le… |
| F022 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:192` | When best_ty == "stream_llm": If streaming wins the search, it is overridden to vertical_and_slash,… |
| F023 | 代 | undisclosed | 2 | path_change | solved |  | `minference/modules/minference_forward.py:418-419` | When q_len == 1: returns via dense |
| F024 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/modules/minference_forward.py:421` | When self.config.to_dict().get("dilated1", False): Config flag switches to the fixed 'dilated1' spa… |
| F025 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/modules/minference_forward.py:423` | When self.config.to_dict().get("dilated2", False): Config flag switches to the fixed 'dilated2' spa… |
| F026 | 代 | undisclosed | 2 | path_change | solved |  | `minference/modules/minference_forward.py:425-426` | When self.config.to_dict().get('dense', False): returns via dense |
| F027 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/modules/minference_forward.py:427` | When self.config.to_dict().get("streaming", False): Config flag switches to streaming_forward with … |
| F028 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:432` | When self.config.to_dict().get("static_pattern", False): Config flag switches to vertical_and_slash… |
| F029 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/modules/minference_forward.py:434` | When self.config.to_dict().get("vs_only", False): Config flag forces the vertical_and_slash_kernel … |
| F030 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:521` | When self.layer_idx >= self.starting_layer and not self.is_search: Layers below starting_layer (or … |
| F031 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:613` | When self.layer_idx >= self.starting_layer: Layers below starting_layer use dense flash_attn_func; … |
| F032 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:756` | When q_len == 1: In gather_last_q_vertical_slash_topk_vllm, a single query token bypasses the spars… |
| F033 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/modules/minference_forward.py:864` | When kv_cache is None or prefill_meta.block_tables.numel() == 0: Only when there is no KV cache or … |
| F034 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/modules/snap_kv.py:321` | When q_len < self.max_capacity_prompt: When the prompt length is below max_capacity_prompt, update_… |
| F035 | 代 | undisclosed | 2 | path_change | solved |  | `minference/modules/snap_kv.py:347` | When self.pooling == "avgpool": The pooling attribute (set from config.pooling in init_snapkv) sele… |
| F036 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/ops/block_sparse_flash_attention.py:130` | When q.dtype != torch.bfloat16: The Triton kernel's compute dtype is chosen from the input dtype: b… |
| F037 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/ops/streaming_kernel.py:609` | When head_dim not in [16, 32, 64, 128, 256, 512]: For head dimensions not in the hard-coded list, q… |
| F038 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/ops/streaming_kernel.py:620` | When k_len > n_local: The streaming (StreamingLLM) variant only keeps the `n_init` sink tokens when… |
| F039 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/ops/streaming_kernel.py:701` | When len_k <= n_local + n_init: The KV cache kept for subsequent decoding is either the full h_k/h_… |
| F040 | 代 | undisclosed | 2 | path_change | solved | ~ | `minference/patch.py:835` | When config.kv_cache_cpu: Caller-supplied config flag switches to the KV-cache-on-CPU variant (minf… |
| F041 | 代 | undisclosed | 2 | path_change | solved | ✓ | `minference/patch.py:840` | When config.use_snapkv: Caller-supplied config flag switches to the SnapKV variant (minference_patc… |
| F042 | 论 | impl_deviates | 2 | other | solved |  | `csrc/vertical_slash_index.cu:27-99` | 论文要求循环守卫 s_v≤k_s；代码用 while(1)+break，s 仅在 else 分支递增，终止由 s>=NNZ_S 决定 |
| F043 | 论 | impl_deviates | 2 | other | always |  | `experiments/README.md:13-30` | 实验配置未体现{(1024,4096)}，实际候选为(100,800) |
| F044 | 论 | impl_deviates | 2 | other | always |  | `experiments/README.md:13-30` | 实验配置未体现论文候选集 |
| F045 | 论 | impl_deviates | 2 | other | always |  | `experiments/README.md:13-30` | 配置层未体现{100} |
| F046 | 论 | impl_deviates | 2 | other | solved |  | `experiments/infinite_bench/args.py:63-78` | 论文Table4/Fig5报告static变体结果；评估入口未暴露static选项，且底层static实现本身只覆盖VS。 |
| F047 | 论 | impl_deviates | 2 | other | solved |  | `experiments/infinite_bench/args.py:63-78` | 评估入口无'only A-shape'变体选择，无法复现Table4的该变体。 |
| F048 | 论 | impl_deviates | 2 | other | solved |  | `experiments/infinite_bench/args.py:63-78` | 无变体入口，无法复现Table4的only block-sparse行。 |
| F049 | 论 | impl_deviates | 2 | other | solved |  | `minference/models_patch.py:66-73` | 论文 1k 全局/4k 局部；代码 128 全局/3968 局部，两参数均不符。 |
| F050 | 论 | impl_deviates | 2 | other | always |  | `minference/modules/minference_forward.py:99-197` | 论文要求遍历调用方给定的初始化搜索空间 σ；代码遍历写死的候选表，σ 输入不存在（artifact 范围：无 σ 输入，候选表硬编码） |
| F051 | 论 | impl_deviates | 2 | other | no_condition |  | `minference/modules/minference_forward.py:99-197` | 论文要求 dense 注意力输出 y（含 V）；代码只算注意力权重矩阵，未形成输出 |
| F052 | 论 | impl_deviates | 2 | other | no_condition |  | `minference/modules/minference_forward.py:99-197` | 论文要求最小化与 dense 输出的偏差；代码最大化权重保留分数，方向与参照对象均不同 |
| F053 | 论 | impl_deviates | 2 | other | always |  | `minference/modules/minference_forward.py:99-197` | 论文要求六类输入；代码签名缺 V、patterns、ρ、t、σ |
| F054 | 论 | impl_deviates | 2 | other | always |  | `minference/modules/minference_forward.py:99-197` | 论文要求空集初始化；代码以数值 0 与空字符串初始化，且该初值使负分候选永不被选 |
| F055 | 论 | impl_deviates | 2 | other | always |  | `minference/modules/minference_forward.py:199-246` | 论文要求最小化 t_sparse(M)+t_overhead(M)；artifact 执行路径未实现该时间目标。 |
| F056 | 论 | impl_deviates | 2 | other | always |  | `minference/ops/block_sparse_flash_attention.py:150-165` | 论文要求块级 logits 先 softmax（并除 √d）得 Â；代码省略 softmax 与缩放，仅用因果掩码后的原始点积排序（artifact 范围：无 softmax/√d 的块级注意力矩阵） |
| F057 | 代 | undisclosed | 3 | other | solved | ~ | `minference/modules/minference_forward.py:34` | When "seq_len" in inspect.signature(self.rotary_emb.forward).parameters: ROPE_TYPE is chosen by int… |
| F058 | 代 | undisclosed | 3 | state | solved | ✗ | `minference/modules/minference_forward.py:74` | When "apply_rotary_pos_emb" not in self.__dict__: `apply_rotary_pos_emb` is rebound as a module-lev… |
| F059 | 代 | undisclosed | 3 | other | solved | ✓ | `minference/modules/minference_forward.py:194` | When best_ty == "block_sparse": If block_sparse wins, it is replaced by hard-coded vertical_and_sla… |
| F060 | 代 | undisclosed | 3 | other | solved | ✓ | `minference/modules/minference_forward.py:430` | When head_id not in self.best_pattern: When the per-layer pattern file |
| F061 | 代 | undisclosed | 3 | other | solved |  | `minference/modules/minference_forward.py:523` | When is_flash_attn_2_available(): When the sparse path is not taken, availability of flash-attn 2 d… |
| F062 | 代 | undisclosed | 3 | other | solved |  | `minference/modules/minference_forward.py:526` | When not (is_flash_attn_2_available()): attn_output = gather_qkv(q, k, v, attention_mask) |
| F063 | 代 | undisclosed | 3 | other | solved | ~ | `minference/ops/block_sparse_flash_attention.py:164` | When top_k > context_size // block_size_N: The requested `top_k` (derived from the searched `slash_… |
| F064 | 代 | undisclosed | 3 | other | solved |  | `minference/ops/pit_sparse_flash_attention.py:150` | When q.dtype != torch.bfloat16: Any query dtype other than bfloat16 (float32, float64, float16 is f… |
| F065 | 代 | undisclosed | 3 | path_change | solved | ✗ | `minference/ops/pit_sparse_flash_attention_v2.py:188` | When head_dim not in [16, 32, 64, 128, 256, 512]: For head dims outside the power-of-two list |
| F066 | 论 | not_implemented | 3 | other | solved |  | `experiments/README.md:13-30` | 实验入口未暴露或设定步长50 |
| F067 | 论 | not_implemented | 3 | other | always |  | `experiments/infinite_bench/args.py:63-78` | 无变体配置，无法复现Table7的only vertical行。 |
| F068 | 论 | not_implemented | 3 | other | solved |  | `experiments/infinite_bench/args.py:63-78` | 无换算配置入口。 |
| F069 | 论 | not_implemented | 3 | other | trigger_only |  | `minference/modules/minference_forward.py:99-197` | 论文要求每候选计算真实 kernel FLOPs；代码不计算任何 FLOPs |
| F070 | 论 | not_implemented | 3 | other | always |  | `minference/modules/minference_forward.py:99-197` | 论文要求以目标 FLOPs 为停止条件的迭代调整；代码无该循环与调整算子 |
| F071 | 论 | not_implemented | 3 | other | always |  | `minference/modules/minference_forward.py:99-197` | 论文要求累积 FLOPs 对齐后的候选到 ρ；代码无该累积步骤 |
| F072 | 论 | not_implemented | 3 | other | no_condition |  | `minference/modules/minference_forward.py:99-197` | 论文要求 FlashAttention 与 V 信息参与选择；代码为稠密权重计算且完全不含 V |
| F073 | 论 | not_implemented | 3 | other | always |  | `minference/modules/minference_forward.py:199-246` | 论文要求分别定义 t_sparse 与 t_overhead；artifact 路径无对应实现。 |
