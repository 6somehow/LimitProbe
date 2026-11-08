# 代码侧方法规格：步骤 2、3b、4

## 步骤 2：代码侧找 limitation（区域表）

> 步骤 2 有两条路线：本节描述路线 A（静态分析）；路线 B（LLM 抽取）和对比协议见 `docs/06_two_routes.md`。两条路线的输出格式和校验规则相同。

**输入**：Artifact（仓库 + commit）、Binding（机制入口、参数映射）。
**输出**：Region 列表；再转换成 Limitation(origin=code)。

### 2.1 抽取信号（v0 已实现，见 `codeside/extractor.py`）

| 信号 | Outcome | 例子（FlexPrefill） |
|---|---|---|
| `assert` / `raise` 涉及参数或其派生变量 | reject | `assert batch_size == 1` |
| 早返回分支，且调用了 baseline（名字命中 hint 列表） | fallback | `if q_len <= max(...): return flash_attn_func(...)` |
| `global X` + `if X is None:` | state_dependent | `causal_mask` 模块级缓存 |
| 依赖版本 / 包是否安装 / GPU 型号的分支（取默认分支） | env_dependent | `triton.__version__ < 3` |
| `mask = <与参数比较>`（张量逐元素分支） | mechanism_variant | `block_sparse_mask = kl_div < tau` |
| 算术中出现的字面量等于入口参数的默认值，且该参数在作用域内 | suspicious | `// 128`，而 `block_size` 可配置 |
| 入口函数的默认路径 | mechanism | 所有 guard 通过后 |

每个 Region 记录：原始条件表达式、所依赖的名字、**路径前缀**（外层分支条件，已取反）、file:line、调用链、provenance。

### 2.2 v0 的已知缺口（TASKS.md M2）

| 缺口 | pilot 上的表现 | 计划 |
|---|---|---|
| 不做路径可行性剪枝 | 在 prefill 前缀下仍分析了 decode kernel，产生 6 条噪声 | 调用时把被调函数参数绑定到调用方表达式，用 z3 检查前缀与条件是否矛盾 |
| 不判断冗余 | `triton_bnhd_pool` 的两个 assert 已被入口 assert 覆盖 | 前缀蕴含该条件时标为 subsumed |
| 不区分内部不变量 | `isinstance(block_idx, list)` 这类断言并非输入限制 | 条件只涉及内部计算值、与入口参数无数据依赖时降级 |
| 调用解析只支持同文件和简单 `from x import f` | — | 补包级导入、方法调用；动态分发交给 LLM（`docs/prompts/dispatch_resolution.md`） |
| 配置键未接入 | `flex_prefill_min_budget` 经 `modules/patch.py` 传入 | 从 Binding 读配置键 → 参数映射 |

### 2.3 Region → Limitation

`python -m codeside.cli to-limitations` 把 reject / fallback / env / state / suspicious 区域转为
Limitation（effect_type：reject→reject，fallback→path_change，state→state，其余→other）。
mechanism 和 mechanism_variant 不是 limitation，但保留在区域表里供 scope 和评测覆盖判断使用。

## 步骤 3b：代码 → 论文验证

> 已实现，实现细节和结果见 `docs/06_3b_eval.md`。

对每条代码侧 Limitation 回答三个**独立**的问题：

| 问题 | 方法 | 结果字段 |
|---|---|---|
| ① 文档里有没有写？ | 检索候选段落（论文正文、附录、README、docstring、注释），关键词 = 条件里的名字 + Binding 对应的论文术语 + 条件里的数值；再交给 LLM 判断（`docs/prompts/3b_code_to_paper.md`）。**quote 必须逐字出现在来源中**，否则作废 | result、documented_in、matching_evidence |
| ② 在不在论文声明的 scope 内？ | 用 Binding 把区域条件里的代码名字换成论文参数，与 ScopeItem 求交（区间 / 集合运算，必要时 z3）。交集非空 → in_scope；只与 `explicit=False` 的范围或论文显式假设相交 → scope_edge；交集为空 → out_of_scope；没有可用的 Binding → unknown | scope_status |
| ③ 有没有被评测过？ | 是否存在某个 EvalPoint 满足区域条件 | evaluated_in_paper |

MatchResult：found（写了，边界一致）、boundary_mismatch、weaker（写了但比代码行为弱，如"只测过"对"必须"）、not_found、contradicted（文档说法与代码相反，如 docstring 说支持 16，kernel 拒绝 16）。

## 步骤 4：整合

### 4.1 去重与合并

- 论文侧 Limitation 经 3a 找到代码对应、代码侧 Limitation 经 3b 找到论文对应、两者 code_evidence 指向同一 Region（或条件等价）→ 合并为一条 Finding。
- 同一函数内条件相同的多条代码侧 Limitation 合并。

### 4.2 分类决策表

| 论文侧 | 代码侧 | 3a | 3b | 类别 |
|---|---|---|---|---|
| 有 | 有 | found | found | confirmed |
| 有 | 有 | boundary_mismatch | 任意 | boundary_mismatch |
| 有 | 无 | not_found | — | paper_only（性能 / 算法类，或论文过时） |
| 无 | 有 | — | not_found | **undocumented** |
| 无 | 有 | — | found / weaker，且只在 README / docstring / 注释 | documented_elsewhere |
| 无 | 有 | — | contradicted | undocumented（rationale 注明"文档与代码矛盾"） |

scope_status = out_of_scope 的 finding 保留在记录里，但不计入主结果。

### 4.3 优先级与置信度

- priority 1：undocumented，scope 为 in_scope / scope_edge，effect ∈ {reject, accuracy, state}
- priority 2：undocumented 的 path_change；documented_elsewhere 且 weaker
- priority 3：其余
- confidence：Region 来自 ast、Binding certain、quote 已逐字校验 → mechanical；任一环节依赖 LLM → llm_assisted

### 4.4 witness_hint

在"scope ∩ 区域条件"里取具体值（区间端点、边界两侧各一个点），用 z3 或手写区间运算求解，
写入 Finding.witness_hint，交给 Shanghao 生成测试。scope 没有约束的维度取论文 EvalPoint 的值。
