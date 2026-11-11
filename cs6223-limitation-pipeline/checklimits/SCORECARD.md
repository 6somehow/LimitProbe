# 测试过程评分表与置信分数（check_limits）

状态：设计草稿，2026-11-11。**§3 的评分列、§4、§5、§7 已被 `CONFIDENCE_SPEC.md` 取代**（不再有最终分和加权几何平均）；§2 的测试设计要求 T1 到 T9、§3.5 判定表、§3.6 重放定义、§6 表单仍然有效。权重和阈值是初始值，没有文献依据，要用故障注入校准（见 §8）。
参考实现：`scoring_prototype.py`（纯标准库，已运行，样例是构造的，不是实测）。

## 1. 原则

1. **code agent 填表，harness 审计并计算。** agent 要填的每一项，要么是 harness 能从运行产物重算的"声明项"，要么是有封闭选项和判定准则的"分类项"。没有"自评 1 到 10 分"。
2. **有些指标只由 harness 测量，agent 不填**（变异检查、重复运行、重放、探针影响、覆盖率）。agent 无法虚报。
3. **声明项与 harness 重算不一致时以 harness 为准**，并计入"表单一致率"，降低最终分数。
4. 总置信分数是这些指标的确定性函数，不由 LLM 给出。

## 2. 测试设计要求（agent 必须遵守）

| 编号 | 要求 | 对应的测试概念 |
|---|---|---|
| T1 | 运行前先写下 oracle 和预期结果（正例、反例），harness 记录其哈希；运行后改 oracle 要计数 | 测试先行；防止事后拟合 oracle |
| T2 | 正例与反例只差一个因素，且反例取边界另一侧的相邻点 | 边界值分析；最小对（ceteris paribus） |
| T3 | 输入取自 `witness_hint`；agent 自选的参数（如头数）逐项披露并说明理由 | 输入溯源；自由参数披露 |
| T4 | 优先调用官方入口；只有记录了原因才调用更深的函数 | 集成层级（单元 vs 系统测试） |
| T5 | 不改仓库代码；环境替代只用外部 mock，并登记 | 被测对象保真 |
| T6 | 离线、固定随机种子、固定 commit、只用 CPU | 可重复性；密封性 |
| T7 | oracle 来自运行时信号（异常、trace 事件、数值差），并指向 `Region.location` | 测试 oracle 的可判定性 |
| T8 | 记录全部命令，使 harness 能在干净环境里重放 | 可重放；防环境漂移 |
| T9 | 输入落在论文范围内；`out_of_scope` 的 finding 只记录，不计入主结果 | 范围 gate |

## 3. 指标定义

骨架是 **RIPR 模型**（reachability、infection、propagation、revealability）：一个能说明 finding 成立的测试，要依次做到"执行到目标位置、条件为真、效果出现、oracle 看得见"。

| 维度 | 权重 | 测什么 | 来源 | 评分（0 到 1） |
|---|---|---|---|---|
| **reach** 可达与判定覆盖 | 0.15 | 目标语句被执行；目标判定两个结果（真、假）都被覆盖 | harness trace | `0.5×[目标行被执行] + 0.5×(出现过的判定结果数/2)` |
| **infect** 条件被验证 | 0.15 | 在运行时变量上求值 `Region.condition.expr`：正例为真，反例为假 | harness 在目标行抓取变量后求值；agent 声明，harness 重算 | `0.5×[正例为真] + 0.5×[反例为假]`；无法求值（如 `otherwise`）记 0 并标注 |
| **oracle** oracle 强度 | 0.20 | oracle 的类型和是否事先登记 | agent 分类，harness 核对 | 档位分 × `max(0, 1 − 0.25×事后修改次数)`，档位见下 |
| **control** 对照质量 | 0.15 | 正反例行为不同，且差异因素数少、取相邻点 | harness 比较两组输入与行为 | 行为不同才计分；差 1 个因素 1.0，2 个 0.7，3 个及以上 0.4；再乘相邻点系数（相邻 1.0，不相邻或未知 0.8） |
| **mutation** 变异敏感度 | 0.10 | 对目标判定做变异，测试结果应翻转 | 只由 harness 执行 | `(杀死数/生成数) × min(1, 生成数/3)`；未运行记 0 |
| **fidelity** 保真度 | 0.15 | 见下，四项相乘 | harness 测量 | `s_mod × s_mock × s_entry × s_probe` |
| **reliability** 稳定与重放 | 0.10 | 重复运行一致；harness 能在干净环境重放出相同判定 | 只由 harness 执行 | `[重放一致] × (一致次数/运行次数) × min(1, 运行次数/3)` |

**oracle 档位**（封闭选项，agent 选，harness 核对证据）：

| 档位 | 定义 | 分值 |
|---|---|---|
| O4 | 机器可检查，且指向具体效果和具体位置：异常类型加抛出位置等于 `Region.location`；或 hook 事件命名了该位置；或精确值/序列相等 | 1.0 |
| O3 | 机器可检查，指向效果类别但不含位置：仅异常类型、退出码、形状/dtype 差异、超过声明容差的数值差 | 0.7 |
| O2 | 对文本日志做子串或正则匹配 | 0.35 |
| O1 | 由 LLM 或人读输出后判断 | 0.1 |

**fidelity 的四项**（衡量对原代码的保真，借用软件测试里的修改量、被测对象真实性、探针影响）：

| 项 | 定义 | 公式 |
|---|---|---|
| `s_mod` 修改量 | 语义改动语句数 ÷ `call_chain` 内函数的语句总数（AST 计，纯日志探针不算） | `max(0, 1 − Δ/0.05)` |
| `s_mock` 外部替代 | 被 mock 的符号数。**路径上**指运行中在目标行之前被调用，或属于 `call_chain` | `max(0, 1 − 0.4×路径上 − 0.05×路径外)` |
| `s_entry` 入口深度 | 测试直接调用的函数在 `call_chain` 里的位置。片段抽取（不在仓库模块内运行）取 0.25 | `1 − 位置/(链长−1)`，链长为 1 时为 1 |
| `s_probe` 探针影响 | 加 hook 后与不加 hook 时可观测结果是否相同 | 相同或无 hook 为 1，否则 0 |

**补充规则（v2 检查后加入）：**

- **条件无法直接求值时**（如 R07 的 `otherwise`、R13 的自然语言条件）：agent 要写一个可执行谓词 `condition.py`（对目标行抓到的变量求值），首次运行前登记。harness 执行它。此时 `infect` 乘以 0.6，因为"翻译是否忠实"没有被验证；0.6 低于 high 档要求的 0.7，所以这类测试最高为 medium。不写谓词则 `infect = 0`。
- **mock 必须可观测。** agent 声明要 mock 的符号，由 harness 提供记录型替身（记录每次属性访问和调用的时间点），或由 harness 包装 agent 写的替身。`on_path` 由 harness 根据"是否在目标行之前被访问"计算，不由 agent 声明。
- **事件序列类**（`witness_type = event_sequence`，如 F03）：正例和反例都是调用序列。"只差一个因素"指两条序列只在一次调用的一个参数上不同。
- **变异在临时副本上进行**，不改 `third_party/` 里的仓库，所以不违反 T5。只对 `Region.location` 处的判定做变异。可能出现等价变异体，因此杀死率不要求 1.0。

## 3.5 判定规则（harness 根据观测结果决定，不由 agent 决定）

"效果"指 `Region.outcome` 对应的可观测事件：`reject` → 目标位置抛异常；`fallback`、`mechanism_variant` → 目标分支被执行（path hook 事件）；`state_dependent` → 第二次调用的结果与单独调用不同。

| 正例出现效果 | 反例出现效果 | 判定 | 说明 |
|---|---|---|---|
| 是 | 否 | `yes` | |
| 否 | 否 | `no` | 还须通过 G5 |
| 是 | 是 | `inconclusive` | oracle 不够具体，或边界选错 |
| 否 | 是 | `inconclusive` | 边界方向反了 |
| 在别处崩溃、超时、import 失败 | — | `inconclusive`（`test_error`） | |
| 没有运行（环境无法满足） | — | `inconclusive`（`not_run`） | |

## 3.6 "干净环境重放"的定义（G2）

新的临时目录；从固定 commit 重新检出仓库；同一 conda 环境 `findlimit` 加该 artifact 的依赖目录；新进程；清空环境变量里的 `SOCLAAS_*` 和代理设置；只执行 agent 在 `replay_commands` 里登记的命令。

## 4. 硬门槛（任一不满足，判定强制为 `inconclusive`，置信度为 low）

| 门槛 | 内容 |
|---|---|
| G1 | 目标语句被执行（片段抽取要先经逐字比对，证明与仓库对应行一致） |
| G2 | harness 在干净环境重放，得到相同判定 |
| G3 | 没有对目标语句或其判定表达式做语义修改 |
| G4 | oracle 至少 O3，且在首次运行前已登记 |
| G5（仅 `no`） | 正例条件已验证为真；路径上 mock 为 0；变异杀死率不低于 0.5（证明 oracle 在效果存在时能看见它） |

## 5. 汇总

1. 维度分数用**加权几何平均**，每个维度下限取 0.05。这样一个弱环节不会被其他强项掩盖，符合 RIPR 链"最弱一环决定证据强度"的想法。
2. `最终分 = 几何平均 × 表单一致率`。表单一致率 = harness 重算与 agent 声明一致的项数 ÷ 声明项总数。
3. 门槛未过时，最终分封顶 0.49。
4. 档位：
   - **high**：最终分不低于 0.80；`reach`、`infect`、`oracle`、`control` 都不低于 0.7；`mutation` 不低于 0.5（必须已评估）；`fidelity` 不低于 0.7。
   - **medium**：最终分不低于 0.55。
   - **low**：其余。
5. 上游 `Finding.confidence`（mechanical、llm_assisted）**单独报告，不并入**，避免把"证据链上游的可信度"和"本次测试做得好不好"混在一起。

## 6. agent 填写的表

```json
{
  "test_id": "T01", "finding_id": "F01", "strategy": "S0|S1|S2|S3",
  "design": {
    "witness_source": "witness_hint",
    "free_parameters": [{"name": "num_heads", "value": 8, "why": "witness_hint 未给出"}],
    "positive_input": {"q_len": 4096, "k_len": 8192},
    "negative_input": {"q_len": 4096, "k_len": 4096},
    "boundary_variable": "k_len",
    "condition_predicate_file": null,
    "oracle": {"tier": "O4", "type": "exception",
               "spec": "AssertionError raised at flex_prefill_attention.py:1836",
               "signal_location": "flex_prefill/ops/flex_prefill_attention.py:1836"},
    "expected": {"positive": "AssertionError at :1836", "negative": "no exception at :1836"}
  },
  "execution": {
    "entry_called": "flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention",
    "call_chain_index": 0,
    "repo_files_modified": [],
    "mocks": [{"symbol": "triton", "kind": "fake_module", "reason": "import-time dependency"}],
    "hooks": [],
    "replay_commands": ["..."]
  },
  "claims": {
    "target_reached": true,
    "decision_outcomes_seen": ["true", "false"],
    "condition_true_on_positive": true,
    "condition_false_on_negative": true,
    "positive_observed": "AssertionError at :1836",
    "negative_observed": "no exception at :1836"
  },
  "evidence": {"trace_file": "...", "stdout_file": "...", "diff_file": "..."}
}
```

`claims` 里每一项都由 harness 重算并比对。变异检查、重复运行、重放、覆盖率、探针影响、事后修改次数不在表里，由 harness 测量。

## 7. 原型在构造样例上的输出（不是实测）

| 样例 | 几何平均 | 最终分 | 档位 | 判定 |
|---|---|---|---|---|
| A 理想（F01 型，1 个路径外 mock） | 0.992 | 0.992 | high | yes |
| B 只有片段抽取 | 0.806 | 0.806 | medium | yes |
| C 2 个路径上的 mock | 0.752 | 0.752 | medium | yes |
| D oracle 由 LLM 判断，事后改 2 次 | 0.545 | 0.490 | low | inconclusive（G4） |
| E 理想，但没跑变异，只跑 1 次 | 0.659 | 0.659 | medium | yes |
| F 理想，但表单 3/6 项与重算不符 | 0.992 | 0.496 | low | yes |
| G `no`，变异只杀死 1/4 | 0.864 | 0.490 | low | inconclusive（G5） |
| H 目标行未到达 | 0.633 | 0.490 | low | inconclusive（G1） |
| I 条件由 agent 写的谓词判断（F03 型） | 0.919 | 0.919 | medium | yes |

我先试过加权算术平均，D 和 H 这类失败样例也能拿到 0.8 以上，所以改用几何平均加门槛封顶。

## 8. 局限与校准

- 权重、`0.05` 的修改量分母、`0.4/0.05` 的 mock 惩罚、各档阈值都是初始值。
- 校准方法：对 pilot 做故障注入（删 assert、改阈值、把条件取反），得到已知答案的"有/无 limitation"样本，看判定和档位是否合理，再调整参数。
- 变异算子集固定为：条件取反、比较符替换（`==`↔`!=`、`<`↔`<=`、`>`↔`>=`）、删除 assert 或 raise、常量加减 1。
- 本表只衡量"测试做得好不好"，不衡量"limitation 重不重要"。
- CPU 限制下无法评估的 `effect_type`（accuracy、performance、resource）默认 `inconclusive`，不进入评分。
