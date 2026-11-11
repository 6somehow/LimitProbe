# 共享 schema v0.2.0（Wanting 负责，需三人评审）

定义在 `schema/models.py`（pydantic v2，`extra="forbid"`）。不用 Python 的模块可以用
`schema/json/*.schema.json` 校验（`python -m schema.export_json_schema` 生成）。

## 记录类型与生产者

| 记录 | 由谁产生 | 关键字段 |
|---|---|---|
| Artifact | 三人共同 | repo_url、commit、entry_points、execution_env |
| Claim | Zhaopeng（步骤 1） | mechanism、statement、kind、evidence |
| ScopeItem | Zhaopeng | param、kind(interval/set/…)、lower/upper/values、explicit |
| EvalPoint | Zhaopeng | config（论文参数 → 值） |
| Binding | Zhaopeng | paper_term → code_symbol、certain |
| Region | **Wanting**（步骤 2） | condition(expr, params, path_prefix)、outcome、location、call_chain |
| Limitation | 双方 | origin、level、condition_text、effect_type、证据、region_ids |
| Verification | 3a Zhaopeng / 3b **Wanting** | direction、result、documented_in、scope_status、evaluated_in_paper |
| Finding | **Wanting**（步骤 4） | category、level、scope_status、witness_hint、confidence、priority、review |
| TestCase | Shanghao（步骤 5–6） | witness_type、inputs、oracle_type、executable_on、result |

## 关键约定

- **ID**：每个 artifact 内唯一。建议前缀：`C` claim、`S` scope、`E` eval、`B` binding、`R`/`X` region（gold / 抽取）、`PL`/`CL` 论文侧 / 代码侧 limitation、`V` verification、`F` finding、`T` test。
- **TextEvidence.quote 必须逐字出现在来源里**（gate rule，后续自动检查）。
- **CodeLocation.file 是相对仓库根目录的路径**，行号对应 `Artifact.commit`。
- **Region.condition.expr 用代码层的名字**；从论文参数到代码名字的映射只放在 Binding 里。
- **provenance** 区分 ast / llm / manual；**confidence** 区分 mechanical / llm_assisted / llm_only。
- **Outcome**：mechanism、mechanism_variant、fallback、reject、env_dependent、state_dependent、suspicious。
- **FindingCategory（v0.2.0）**，7 类：
  | 类别 | 来源 | 意思 |
  |---|---|---|
  | `undisclosed` | 代码侧 | 代码有这个限制，用户能读到的地方都没写（核心发现） |
  | `contradicts_docs` | 代码侧 | 文档写的和代码行为相反 |
  | `stated_differently` | 代码侧 | 文档写了，但边界不同或说得更弱（"只测过 bf16" vs 代码强制 bf16） |
  | `docs_only` | 代码侧 | README / 公开函数的 docstring 写了，论文没写 |
  | `paper_stated` | 代码侧 | 论文写了，边界与代码一致 |
  | `impl_deviates` | 论文侧 | 论文描述了，代码实现得不一样 |
  | `not_implemented` | 论文侧 | 论文描述了，代码里没有 |
- **"算不算写了"的统一规则**：只算用户会读到的地方——论文（含附录）、README、其他用户文档、公开函数的 docstring。
  代码注释（包括 TODO/FIXME）、私有函数（`_` 开头）的 docstring、只写版本号的说明都不算。
- **Finding.review**：`unreviewed` / `worth_testing` / `real_but_minor` / `wrong`；`review_note` 写明谁审的
  （`human:<名字>` 或 LLM）和理由。

## 版本记录

- **v0.2.0**（Wanting 草稿，待三人确认）：FindingCategory 从 5 类改为上面的 7 类
  （`undocumented`→`undisclosed`，`documented_elsewhere`→`docs_only`，`confirmed`→`paper_stated`，
  `paper_only`→`not_implemented`；原 `boundary_mismatch` 拆成代码侧 `stated_differently` 和论文侧 `impl_deviates`；
  3b `contradicted` 单独成 `contradicts_docs`）；新增 `Finding.review`、`Finding.review_note`。
  `data/pilot_flexprefill/draft_findings.json` 已按新名字迁移。witness_hint 格式见 `docs/09_step4_findings.md`（witness-v2）。
- v0.1.0：初版。

## 需要团队决定的问题

1. ~~README / docstring 里写了、论文没写的，算"已说明"还是"未说明"？~~ v0.2.0：单独成 `docs_only`；注释不算。
2. ~~`weaker` 单独成类还是并入 found？~~ v0.2.0：并入 `stated_differently`。
3. ScopeItem 只来自论文明示，还是也允许"由评测覆盖推断"（`explicit=False`）？pilot 的 context_length 就是推断的。
4. L2 的 level 在步骤 4 由 Wanting 统一设置，L1/L3 由论文侧设置——是否同意？
5. TestCase 是否需要记录执行环境细节（Python / torch 版本、是否 mock 了哪些函数）？建议 Shanghao 补字段。
6. 是否给 Outcome 增加 `alternative`（切换到另一种实现，如 NNSmith 的 GradSearch → SamplingSearch、MInference 的 dilated / streaming）？
7. v0.2.0 的 7 类和 review 字段是否同意？

## 变更规则

改字段必须：提升 `SCHEMA_VERSION`，更新本文件，重新导出 JSON Schema，跑 `pytest`。
