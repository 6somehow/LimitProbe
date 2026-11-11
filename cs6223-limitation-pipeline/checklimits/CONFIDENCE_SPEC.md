# 置信度细则（提案 v0，待确认）

状态：提案，2026-11-11。取代 `SCORECARD.md` §3 到 §5 的"加权几何平均"。未获确认前，代码仍按 `SCORECARD.md` 运行。
起因：Shanghao 的三点要求。(1) 主项目是 agent，不是某个 paper 的 case。(2) 置信度要有严格明确的细则，参考软件测试已有的概念和方法，不重复造轮子。(3) 在细则固定的前提下，用更好的 agent skill、harness、workflow 去拿到更高的置信度。

## 1. 现有评分表的问题

| 问题 | 具体表现 |
|---|---|
| 数字没有含义 | 权重 0.15/0.20、地板 0.05、mock 惩罚 0.4/0.05、阈值 0.7/0.8 都是初始值。最终分既不是概率，也不对应任何测量尺度 |
| 把"没做"当成"测出来是 0.05" | 变异和重放没运行，却以 0.05 参与几何平均。未评估和测量失败是两回事 |
| 补偿式汇总 | 几何平均仍会让一项高分抵消另一项低分，看不出具体缺了什么 |
| 混了两个问题 | "测试做得好不好"和"判定对不对"被合成一个分数 |
| 带有个案启发式 | 相邻点用"差 1 或 2 倍"，只在 F01、F07 上说得通 |
| 不可校准 | 没有带真值的样本，无法说"档位 high 的判定有多大概率是对的" |

## 2. 原则

1. **置信度回答一个问题：这个判定有多大把握是对的。** 它不衡量 limitation 的重要性，也不衡量测试写得漂亮。
2. **用 defeater（可能推翻判定的理由）组织证据，不用加权求和。** 方法来自 Assurance 2.0 和 eliminative argumentation（Bloomfield、Rushby；已核实 arXiv 2004.10474、2205.04522、2405.15800）：先列出判定可能错的所有理由，再逐条用证据消除；消除不了的，登记为残余疑点。
3. **每个 defeater 对应测试领域已有的概念和一个确定性的检查。** 检查由 harness 执行，agent 不能自报。
4. **区分四种状态，不压成一个数。** `eliminated`（已用测量消除）、`residual`（只有论证，没有测量）、`open`（没评估）、`refuted`（检查失败）。
5. **档位由规则表决定，规则表的参数写在一个 profile 文件里，逐项标明出处或"策略值"。** 同一份证据加同一份 profile，得到同一档位。
6. **档位的含义靠带真值的基准校准**：用故障注入造出"limitation 存在/不存在"已知的样本，统计每个档位下判定的正确率和置信区间。校准之前，档位只是序数，报告里必须写"未校准"。

## 3. 被验证的命题

`C`：在条件 `cond` 下，代码在位置 `loc` 出现效果 `eff`（对应 `Finding` + `Region`）。判定 `yes` 是"C 成立"，`no` 是"C 不成立"，`inconclusive` 是"证据不足以判断"。

## 4. defeater 表

RIPR 链来自 Ammann & Offutt，PIE 的前三步来自 Voas 1992（已核实 RIPR 的来源；Voas 1992 的细节来自记忆，未逐条核对）。

| # | defeater：判定可能错在 | 对应概念 | harness 的检查 | `eliminated` 的条件 | 类别 |
|---|---|---|---|---|---|
| D1 | 目标语句根本没执行 | Reachability | 目标行事件 | 正例执行目标行 | 致命 |
| D2 | 执行了，但条件没按预期成立 | Infection | 在目标行的局部变量上求值 `cond`（或 agent 事先登记的谓词） | 正例求值为真，反例为假 | 致命 |
| D3 | oracle 看不见效果，或看见了不该看见的 | Propagation、Revealability；变异测试衡量 oracle 充分性 | 对目标判定做变异（取反、比较符替换、删除 assert、常量±1），测试结果必须翻转 | 变异数 ≥ `n_min`，且杀死率的 Wilson 下界 ≥ `kill_lb` | 重要 |
| D4 | oracle 本身不可靠 | Test oracle problem；Barr 等把 oracle 分为 specified、derived、implicit、human（已核实 IEEE TSE 41(5), 2015） | 核对 oracle 类型与证据：是否指向 `Region.location`；是否事先登记 | specified 且位置等于 `Region.location`，登记哈希在首次运行前 | 致命（低于 implicit 或未登记） |
| D5 | 正反例的差别不止一个因素，或反例离边界很远 | Ceteris paribus；边界值分析、域测试的 ON/OFF 点（White & Cohen 1980、Jeng & Weyuker 1994）；delta debugging（Zeller & Hildebrandt 2002） | 输入差集；**harness 自己沿边界变量做二分，验证翻转只发生一次，并找到 ON/OFF 点** | 差集大小为 1，且 agent 的反例等于 OFF 点 | 重要 |
| D6 | 观察依赖了不可信的替身 | Test double 分类（Meszaros：dummy、stub、spy、mock、fake；Fowler）；模拟与参考实现 | **因果依赖分析**：某条观察是在哪些替身被访问之后产生的 | 见 §5 | 重要 |
| D7 | 观测手段改变了行为 | Probe effect（Gait 1986） | 有 hook 与无 hook 的可观测结果对比 | 相同 | 致命 |
| D8 | 结果不稳定 | Flaky tests（Luo 等，FSE 2014） | 固定种子、单线程、离线；重复 `n_rep` 次，比较**规范化轨迹哈希** | 全部相同；报告 Rule of three 上界 3/n | 重要 |
| D9 | 换个环境结果不同 | 可复现性；干净环境重放 | `SCORECARD.md` §3.6 的重放 | 重放判定相同 | 重要 |
| D10 | 缩小规模后行为不同 | 外部效度（表征性） | 正例在完整规模重放；harness 对反例按边界二分时也在完整规模探测目标行 | 两个规模下目标判定的真假一致 | 重要 |
| D11 | 被测代码被改过 | 被测对象保真 | AST diff（目标语句、判定表达式、调用链函数） | 目标语句无改动，其余改动语句比例 ≤ `mod_max` | 致命（目标语句被改） |
| D12 | Region、位置或条件本身有误（上游） | 输入有效性 | snippet 逐字比对 | 与仓库对应行一致 | 致命 |
| D13 | 输入超出论文范围 | 范围 gate（T9） | `scope_status` | `in_scope` 或 `scope_edge` | 说明项 |

`Finding.confidence`（mechanical、llm_assisted）仍然单独报告，不并入。

## 5. 替身依赖：用状态代替乘法权重（D6）

不再用 0.9、0.75、0.3 之类的乘数。每条观察记录它的**因果前缀**：在它产生之前，被访问过哪些替身。观察的证据状态：

| 状态 | 条件 |
|---|---|
| `direct` | 因果前缀里没有任何替身（或只有 spy，即只记录、不改变行为） |
| `simulated:reference` | 前缀里只有调用仓库自带参考实现的替身 |
| `simulated:fake` | 含有自己写的、有真实计算的实现（fake） |
| `simulated:stub` | 含有返回固定值的替身（stub、dummy） |

判定只依赖 `direct` 的观察。`simulated:*` 的观察作为**补充信息**列出，明确标注，不进入判定。例如 F07：正例在目标行抛异常是 `direct`；反例"继续运行并返回 `Tensor(1,512,2,128)`"是 `simulated:fake`。

这样做有两个好处：不需要为每类替身编一个数；agent 如果想让更多结论变成 `direct`，只能减少目标行之前的替身，而不是调大权重。

## 6. 档位规则

| 档位 | 条件（全部满足） |
|---|---|
| `invalid` | 任一致命 defeater 为 `refuted`。判定强制为 `inconclusive` |
| `L1 indicative` | 没有 `refuted`；致命项全部 `eliminated`；重要项有 `open` |
| `L2 supported` | 致命项和 D3、D8、D9 全部 `eliminated`；D5、D6、D10 中允许 `residual` |
| `L3 established` | 所有 defeater 为 `eliminated`，或为"允许残余"的项（D13）。判定所依赖的观察全部是 `direct` |

`no` 判定另加一条：D3 必须 `eliminated`，否则最高 `L1`。理由：证明"没有效果"需要证明 oracle 在效果存在时看得见（变异测试的用途）。

profile 参数（初始值，全部标"策略值"，除非另注）：`n_min = 4`、`kill_lb = 0.5`（Wilson 下界；Wilson 1927）、`n_rep = 5`、`mod_max = 0.05`。校准后再调。

## 7. 校准与有效性（怎么证明细则有意义）

1. **带真值的基准。** 对每个 artifact 做故障注入：删 assert、改阈值、把条件取反，造出"limitation 存在/不存在"已知的版本。变异能否替代真实故障，有实证研究（Andrews 等 ICSE 2005；Just 等 FSE 2014），但结论不是无条件的，报告里要写限制。
2. **指标。** 每个档位的判定正确率及 Wilson 区间；错误判定的类型（假阳性、假阴性）；Brier 分数和可靠性图（Brier 1950；Guo 等 ICML 2017 用于神经网络校准，借其方法）。
3. **表单诚实度。** agent 声明与 harness 重算的一致率，单独报告，不并入档位。
4. **消融。** 逐个关掉 harness 服务（变异、边界二分、规模检查、因果依赖分析），看各档位的占比和正确率怎么变。这是回答"harness 设计带来多少置信度"的实验。

上面第 1 到 3 点里的方法名和出处，Brier 1950、Guo 等 2017、Just 等 2014、Andrews 等 2005、Luo 等 2014、Gait 1986、White & Cohen 1980、Zeller & Hildebrandt 2002 来自记忆，未在本次会话里逐条核对，进入论文前要查原文。

## 8. 怎样在细则固定的前提下拿到更高的置信度

每个 `open` 或 `residual` 的 defeater 都对应一个由谁来消除：

| defeater | harness 能自动做的 | agent 的义务（skill 里写成清单） | 失败后的修复动作（workflow 回环） |
|---|---|---|---|
| D3 | 自动生成并执行变异，算杀死率 | 把 oracle 写成指向具体位置的断言，避免只检查"有异常" | 杀死率低：提示存活变异体，agent 加强 oracle |
| D5 | 沿边界变量二分，验证单次翻转，给出 ON/OFF 点 | 说明哪个变量是边界变量，哪些参数是自由参数及理由 | 反例不是 OFF 点：给出 OFF 点，agent 换反例 |
| D6 | 因果依赖分析；提供记录型替身（spy）和模拟器模板 | 声明每个替身的类别和理由；优先把替身放到目标行之后 | 观察依赖 stub：提示换成 fake 或参考实现，或把替身后移 |
| D8、D9 | 重复运行、规范化轨迹哈希、干净环境重放 | 登记全部命令；固定种子 | 不稳定：定位非确定性来源（线程、哈希种子、随机数） |
| D10 | 在完整规模重放目标行 | 给出规模缩放的不变性论证 | 完整规模下判定不同：撤销缩放 |
| D2 | 执行谓词 | 条件无法直接求值时，事先写可执行谓词 | 谓词与 Region 条件不等价：交给人复核 |

workflow 因此分为：**计划 → 登记（oracle、预期、替身声明）→ 执行 → harness 审计 → 修复回环**。审计输出一份"缺陷清单"：每个 defeater 的状态，以及下一步该做什么。agent 在预算内只处理未消除的 defeater。停止条件：达到目标档位、预算耗尽，或剩下的 defeater 无法由 agent 消除（例如上游 Region 有误）。

## 9. 与现有实现的关系

保留：RIPR 的测量（trace、条件求值、判定结果）、AST diff、探针影响、记录型替身、表单审计、因果前缀（现在的 `information` 是它的雏形）、`Finding.confidence` 单独报告。

要改：
1. `scoring.py`：去掉加权几何平均和最终分，改为 defeater 状态表加 §6 的规则表。`scoring_prototype.py` 的九个样例不再回归；改为"每个样例对应的 defeater 状态和档位"的新测试。
2. `models.py`：`Scorecard` 改成 `DefeaterTable` 加 `level`；`InfoItem.confidence` 改成证据状态。
3. 新增 `bva.py`（边界二分）、`mutate.py`、`replay.py`（P1b 本来就要做）。
4. 个案代码（相邻点启发式、只支持 `reject` 的效果判定）换成可插拔的效果检查器。

诊断用的七个维度可以保留为"诊断读数"，不再合成最终分。

## 10. 需要 Shanghao 决定

1. 是否放弃数值化的最终分，只报告档位加 defeater 表（原因见 §1，建议放弃）。
2. §6 的档位定义和 profile 初始值是否可接受。
3. 判定只依赖 `direct` 的观察（§5）。这会让 F07、F01 的反例"正常返回"降为补充信息。
4. 下一步的顺序：先实现 §9（改 scoring、加 bva、mutate、replay），再写 agent skill 和 workflow；还是先写 agent 部分。建议前者，因为 agent 的修复回环需要 harness 给出缺陷清单。
