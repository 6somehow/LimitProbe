# 代码侧的静态证据（2026-11-21，v2 草稿，待三人确认）

来源：2026-11-20 会议。代码侧要把和软件测试有关的证据放进每条候选，跟着 limitation 一直传到后端，作为后端定档的输入。
实现在 `codeside/process_confidence.py`，测试在 `tests/test_process_confidence.py`。

## 它是什么，不是什么

步骤 4 的每条 Finding 说的是：**在条件 `cond` 下，代码在位置 `loc` 出现效果 `eff`**。测试侧
（`checklimits/CONFIDENCE_SPEC.md`）通过执行来判断这句话，给出 L0–L3。

代码侧提供的是**测试之前就能确定的证据**。它和测试侧用同一个框架（列出“这句话可能错在哪”，逐条给状态，不加权求和），
但是：

- **代码侧不定档。** v1 有过 P0–P3 档位，已删除。原因：在已有的 130 条测试结果上，P 档和测试判定没有关系
  （yes 的比例 P1 56/68、P2 30/33、P3 24/29），多一个档位只会和 L 档混淆。
- **最终档位只由测试侧决定。** 代码侧的证据在记录里和它并排，不改它的规则。
- 不执行代码、不调模型。同样的记录、仓库和运行文件，结果永远相同。

## 四部分

### 1. `checks`：核对表

状态：`eliminated`（工具核对过）、`residual`（只有论证或模型判断）、`open`（没评估）、`refuted`（核对失败）。

| # | 这句话可能错在 | 测试概念 | 对应测试侧 | `eliminated` | 其他状态 |
|---|---|---|---|---|---|
| C1 location | 位置或 snippet 不对 | 输入有效性 | D12 | 固定 commit 下该行的语句和 snippet 按规范形式一致 | 文本在该行但那里不是语句开头：`residual`；不一致或文件不存在：`refuted`；没有仓库：`open` |
| C2 condition | 条件不是这条语句的判定 | 判定（decision），判定覆盖的单位 | D2 | 和语句的判定表达式按 AST 相同或互为取反（含分支里的无条件语句、条件表达式、推导式过滤） | 只是判定的一个操作数，或是改写：`residual`；用了函数里没有的名字：`refuted`；不是 Python 表达式：`open` |
| C3 reachability | 从官方入口走不到 | 可达性（RIPR 的 R） | D1、D14 | 目标在入口函数里、是模块级语句，或有逐层都是真实调用点的调用链 | 调用链里有靠猜的步骤：`residual`；没有调用链：`open` |
| C4 feasibility | 条件和路径前缀矛盾 | 不可行路径；符号执行加约束求解 | witness | z3 解出触发点和对照点，全部路径前缀都进了求解器 | 有前缀没进求解器、没有对照点：`residual`；没解出来：`open`；`infeasible`：`refuted` |
| C5 extraction | 换一次运行就没有这条了 | 可重复性（flaky test） | D8 | 静态路线找到；或 LLM 路线在全部抽取运行里都找到（同一文件同一行） | LLM 路线只在部分运行里找到，或这篇没有重复运行：`residual` |
| C6 effect_label | 标的效果在这条语句上判不了 | test oracle 问题 | D4 | `reject` 的语句能抛异常；`path_change`、`state` 的语句是 `if` / `while` | 不相符：`refuted`；效果是 `other`：`open` |
| C7 documentation | “没写”其实写了 | 缺失性断言 | — | 3b 找到了原文（引用逐字核对过） | `not_found`：`residual`；3 次重复结果不一致：`residual`；没有 3b：`open` |
| C8 review | 有人看了觉得不对 | 审查（inspection） | — | 人工审过 | LLM 盲审：`residual`；审为 `wrong`：`refuted`；没审：`open` |

C7 只影响类别（是不是 `undisclosed`），不影响“代码是否这样做”。

### 2. `repeats`：重复测量

| 字段 | 含义 | 数据 | 测试概念 |
|---|---|---|---|
| `extraction_runs.found_in` / `of` | 这个位置在几次抽取运行里出现 | `results/step2_merged/<id>/merged_run{1,2,3}.json` | 可重复性 |
| `documentation_check.paper_agreement` | 3b 重复 3 次，结果的一致率 | `results/pipeline/<id>/3b.detail.json` | 评分者间一致性 |
| `routes` | 哪条路线找到的（`ast` 静态、`llm`） | `Limitation.provenance` | 两种独立方法互相印证 |

匹配按“同一文件同一行”，偏严：LLM 两次指向相邻两行会算作没找到。FlexPosit 和 QoServe 没有重复抽取的记录，记为没测量。

### 3. `testability`：预测测试侧能到哪一档

按测试侧自己的规则推出来（`CONFIDENCE_SPEC.md`：L2 要 D3 消除，L3 要 D14 消除）。概念上是软件可测性
（可控性、可观察性）和变异测试。

| 字段 | 怎么算 |
|---|---|
| `testable: false` + `expect_not_run` | C4 为 `refuted` → 预计 `witness_unusable`；效果是 `other` → 预计 `outcome_unsupported` |
| `mutants` | 用测试侧的 `checklimits/checklimits/mutate.py::generate` 在目标行生成的变异体个数（同一个函数，不是另写一套） |
| `ceiling` | 变异体少于 `n_min`（4）：`L1`，因为 D3 消不掉；否则没有调用链：`L2`，因为 D14 最多 residual；否则 `L3` |
| `limited_by` | 卡在哪个 defeater 和原因 |
| `condition_has_calls` | 条件里有函数调用，D2 不能直接求值 |
| `integer_boundary` | 边界变量都是整数，D5 的相邻点才有定义 |

**这是上限，不是预报**：实际档位可以更低（oracle 弱、结果不稳定、环境缺失都会拉低）。

和已有测试报告对照（7 篇，有代码侧记录且有报告的 190 条）：

| 预测 | 实际 | 条数 |
|---|---|---|
| 上限 L1 | L1 71，invalid 7，n/a（inconclusive）10 | 88 |
| 上限 L2 | L2 12，L1 1 | 13 |
| 上限 L3 | L3 15，L2 7，L1 4，n/a 3 | 29 |
| 预计 `outcome_unsupported` | `outcome_unsupported` | 48 |
| 预计 `witness_unusable` | `witness_unusable` | 12 |

测过的 130 条里**没有一条超过预测上限**，98 条正好等于上限；60 条没测的原因全部对上。
注意：规则是看着这批数据定的，这不是独立验证；`n_min` 改了，上限也要跟着改（现在写死为 4）。
`condition_has_calls` 和 `integer_boundary` 只是记录事实，没有进上限，也没有验证过。

### 4. `importance`：重要性（和把握分开）

- `path.decision_on`：`main` 判定不在任何 `if` / `except` / `case` 里面，调用链上的调用点也不在，每次调用都会求值；
  `side` 在某个条件分支里（`enclosing_conditions`、`conditional_call_sites`）；`unknown` 没有调用链，看不到调用者。
  循环单独计数（`enclosing_loops`）。概念上对应支配关系和 operational profile；这里按语法嵌套近似，
  前面的提前返回只体现在 `path_prefix_conditions` 里。
- `impact`：`guarded_statements` 是分支体的语句数，或 assert / raise 之后函数里剩下的语句数（影响分析）；
  `call_sites_of_function` 是解析到这个函数的调用点数（扇入）。
- `coverage`：目标函数里的判定数、代码侧列出了几个、入口能否静态到达。这是**分析的覆盖**，不是执行覆盖；
  列出的比例低不等于漏报，代码侧只列和论文机制有关的判定。

## 后面怎么用

| 用在哪 | 用哪部分 | 怎么用 |
|---|---|---|
| 测试之前 | `checks`、`testability` | `testable: false` 的不花预算；`ceiling` 低的少花 agent 时间 |
| 测试之后 | `testability.limited_by` | 放在 L 档旁边，说明是这句本身测不到更高，还是测得不够 |
| 没测的 Finding | `checks`、`repeats` | 作为确定性的证据和 A 档分析并排列出 |
| 最终报告 | `importance` | 只用于排序，不进档位 |

现在只做到“带过去”：块在 `limitations_for_tests.json` 的每条记录里，测试侧原样放进 `report.json` 的
`finding.process_confidence`。上表的四种用法都还没有接进测试侧和报告，要团队同意后再做。

## 在记录里的样子

`limitations_for_tests.json` 里每条记录的 `process_confidence`（纯论文侧的 Finding 为 null）。它和 `limitations`
一样是交接记录上的附加键，**不是 `Finding` schema 的字段**，共享 schema 没有改。

```json
{
 "format": "process-confidence-v2", "calibrated": false, "limitation_id": "CL-B013",
 "checks": {"C1": {"name": "location", "status": "eliminated", "evidence": "..."}, "...": {}},
 "open_doubts": ["C3", "C8"],
 "repeats": {"extraction_runs": {"measured": true, "found_in": 3, "of": 3, "match": "same file and line"},
             "documentation_check": {"measured": true, "repeats": 3, "paper_agreement": 1.0, "elsewhere_agreement": 1.0},
             "routes": ["llm"]},
 "testability": {"measured": true, "testable": true, "mutants": 2, "mutants_needed": 4,
                 "mutant_operators": {"...": 1}, "ceiling": "L1",
                 "limited_by": ["D3: 2 mutant(s) of the target line, fewer than n_min=4; it cannot be eliminated", "D14: ..."],
                 "condition_has_calls": false, "integer_boundary": true},
 "importance": {"path": {"decision_on": "unknown", "...": 0}, "impact": {"guarded_statements": 30, "...": 0},
                "coverage": {"function_decisions": 4, "...": 0}}
}
```

一条 Finding 合并了多条代码侧记录时，按 witness 所用的那一条计算。

只重算、不重跑步骤 4（不调模型，其余内容不变）：

```bash
python scripts/run_step4.py --process-only [--only <id> ...]
python scripts/make_handoff_doc.py
```

每篇的汇总在 `findings.report.json` 的 `process_confidence`，全部论文的表在 `results/step4/process_confidence.md`，
`HANDOFF.md` 第 6 节有说明。

## 需要团队决定

1. **四种用法做不做。** 尤其是没测的 Finding（约 270 条）怎么定最终的四档：会议要求每条 claim 都有档位，
   但 L 档只有测过的才有。
2. **测试侧的两行改动要 Shanghao 确认**：`checklimits/checklimits/adapter.py` 在校验 `Finding` 前取出这个键；
   `testreport.py` 把它放进 `report.json`。
3. **测试报告会显示 `stale`。** `limitations_for_tests.json` 改了，`pipeline status` 的 test 一行从 `done` 变成 `stale`。
   已有的判定和档位不受影响，但要在有被测环境的机器上重跑 `pipeline test <id>`（不带 `--run-agent`）。
4. **“主路径”的定义。** 现在按语法嵌套。另一种是“论文评测的配置会不会走到”，需要论文侧的参数映射，目前大多是 unknown。
5. **要不要进共享 schema。** 改 `schema/models.py` 会让论文侧 `schema_contract.py` 的 3 个测试失败（它记录了文件哈希），
   需要 Zhaopeng 同时更新。

## 已知限制

- 上限规则只在开发数据上对过，没有独立验证；`n_min` 写死为 4，没有读测试侧的 profile。
- 变异体个数依赖测试侧的 `mutate.py`，按文件路径加载；那个文件不在时 `testability` 记为没测量。
- C2 只认 AST 相同或取反，等价改写会被记为 `residual`。
- C3、C4 直接读 `witness_hint`，继承它的限制（`checklimits/REQUESTS_TO_STEP4.md` §6 的两条仍未处理）。
- 抽取运行的匹配按行号，偏严。
- 文中的文献概念（RIPR、PIE、ON/OFF 点等）是凭记忆列的，写进报告前要核对原文。
- 没有人工标注对照，这些证据和正确率的关系未知。
