# check_limits 开发计划（Shanghao，步骤 5–6）

分支：`somehow6/check_limits`（已检出，无 upstream，基于 `b8fa2eb`）。
状态：计划 v3，2026-11-11。工期是估计，不是承诺。
配套：`SCORECARD.md`（测试设计要求、评分表、判定规则）、`scoring_prototype.py`（评分参考实现）、`KICKOFF_PROMPT.md`（启动开发的 prompt）。

## 1. 目标

输入一条 `Finding`（加关联的 `Limitation`、`Region`、固定 commit 的仓库），code agent 在 **CPU** 上：

1. 按测试设计要求（`SCORECARD.md` §2，T1 到 T9）设计并完成测试：搭环境、选执行方式、构造输入、写 oracle。
2. 按评分表（`SCORECARD.md` §6）填写测试过程指标。

harness 审计表单、补充测量（变异、重复、重放、覆盖率、mock 访问），输出：

- 判定 `yes / no / inconclusive`（对应 `confirmed / refuted / test_error 或 not_run`），规则见 `SCORECARD.md` §3.5。
- 各维度分数、门槛结果、最终分和置信档位。

原则：**LLM 负责理解和构造，判定与分数由确定性 harness 计算。**

## 2. 已核实的事实（2026-11-11 本机验证）

| 项 | 结果 |
|---|---|
| 项目环境 | conda `findlimit`（`<conda-env>`），Python 3.14.10，只有 pip |
| CPU 依赖 | `pip index versions` 能列出 torch CPU 2.9.0 到 2.15.0 和 triton 3.9.0（有 3.14 的 wheel）。FlexPrefill 所需版本未验证 |
| SoCLaaS 网络 | 默认路由 `eth1` 直连失败；绑定 `eth0` 后成功。README 中的代理和 `demo.py` 的 `eth2` 已过时 |
| x-test-2 | 实际模型 `deepseek-v4.1-flash-1017`，推理模型。最小 chat 约 1.6 秒。**tool calling 可用**：非流式返回正确的 `tool_calls`（`finish_reason=tool_calls`），流式请求也正常结束 |
| opencode | 本机未安装。文档支持自定义 OpenAI 兼容 provider（`baseURL`、`env`、`headers`、`models`），以及 agents、skills、MCP、permissions；默认 5 分钟响应头超时，超时重试 3 次 |
| dsh | Node/TypeScript，developer preview，会有破坏性变更，未经安全审计。有 headless 模式和本地沙箱；文档提到默认开启的会话日志和 OTel 反馈上传 |
| 其他 | 有 `node`、`pnpm`、`npm`；没有 uv |

## 3. pilot 对象（F01 到 F07 → Region）

| Finding | Region | 结局 | 位置（`flex_prefill_attention.py`） | 所在函数 | 链长 | 预期 oracle | 预期难度 |
|---|---|---|---|---|---|---|---|
| F07 | R01 | reject | 1824 | `flex_prefill_attention` | 1 | exception O4 | 低，最先做 |
| F01 | R03 | reject | 1836 | `flex_prefill_attention` | 1 | exception O4 | 低 |
| F04 | R04 | reject | 1837 | `flex_prefill_attention` | 1 | exception O4 | 低 |
| F05 | R08 | reject | 1218 | `triton_block_wise_prefill_attention` | 3 | exception O4 | 中：triton 替身可能在路径上 |
| F06 | R09 | reject | 1222 | `triton_block_wise_prefill_attention` | 3 | exception O4 | 中；`out_of_scope`，只记录 |
| F03 | R13 | state_dependent | 1694 | `get_active_blocks` | 2 | 序列对比 O3/O4 | 中：条件是自然语言，要写谓词；跨设备部分 `not_run` |
| F02 | R12 | suspicious（accuracy） | 1708 | `get_active_blocks` | 2 | differential | 高：CPU 上多半 `inconclusive` |

## 4. 检查 v2 后发现的问题与修正

| # | 问题 | 修正 |
|---|---|---|
| 1 | agent 的 shell 会运行仓库代码；如果 agent 进程持有 `SOCLAAS_API_KEY`，被测代码就能读到它 | **中继注入密钥**：中继从 `soclaas.env` 读 key，加到出站请求头；agent 运行时只拿一个假 key 和 `http://127.0.0.1:<port>/v1`。agent、被测代码都看不到真 key |
| 2 | 判定规则没写清楚（正反例都出现效果怎么办） | `SCORECARD.md` §3.5 加了判定表 |
| 3 | R07 的 `otherwise`、R13 的自然语言条件无法求值，`infect` 恒为 0，测试必然 low | agent 写可执行谓词并事先登记；`infect` 乘 0.6，最高 medium |
| 4 | `on_path` 由 agent 声明，不客观 | mock 由 harness 提供记录型替身，按"目标行之前是否被访问"计算 |
| 5 | 变异要改代码，与 T5"不改仓库"冲突 | 变异只在临时副本上做，只针对目标判定 |
| 6 | "干净环境重放"没定义 | `SCORECARD.md` §3.6 |
| 7 | agent 搭环境时往 `findlimit` 装包，会污染共享环境，也难重放 | `findlimit` 只装 harness 和共用依赖（torch CPU 等，P0 由人或 harness 装好）。artifact 特有依赖由 agent 用 `pip install --target checklimits/.deps/<artifact>` 安装，运行时加入 `PYTHONPATH`，命令记入 manifest |
| 8 | `shanghao_exec_report_draft.py` 的 `Confidence` 结构（因子列表）与评分表不一致 | `models.py` 以 `SCORECARD.md` 为准：`Scorecard{dims, gates, total, form_integrity, final, level}`；草稿只保留 `Fidelity`、`Checks`、`Env` 等结构 |
| 9 | 没有预算上限 | 每条 finding：最多 40 个 agent 步、30 万 token、30 分钟；超出记 `inconclusive`，原因为 budget |
| 10 | 没说哪些文件进 git | 进 git：代码、`PLAN/SCORECARD`、测试、`results/` 下的报告 JSON。不进：`.deps/`、`scratch/`、`runs/` 原始日志、`third_party/` |

## 5. 决定

| # | 事项 | 决定 |
|---|---|---|
| D1 | 项目环境 | conda `findlimit`；artifact 特有依赖进 `.deps/<artifact>`（见 §4 第 7 项） |
| D2 | agent 运行时 | **opencode 为首选**（自定义 provider 有文档支持）；dsh 作为备选。P0 实验后定稿 |
| D3 | 我们的组件 | 与运行时无关：agent 指令文件（T1 到 T9 + 填表说明）+ 命令行 `python -m checklimits {task, mock, run, submit}`。agent 通过 shell 工具调用。以后可再包装成 MCP server |
| D4 | 模型 | `x-test-2`，temperature 0，记录响应中的真实模型名 |
| D5 | 网络与密钥 | 本地中继：监听 `127.0.0.1`，出站绑定 `eth0` 当前地址（运行时读取），注入 key（§4 第 1 项）。只依赖标准库 |
| D6 | 分工 | agent 产出 attempt 包（测试文件、谓词、mock 声明、填好的表）；harness 负责运行、trace、diff、变异、重放、判定、评分 |
| D7 | 代码位置 | `cs6223-limitation-pipeline/checklimits/`，自带 `pyproject.toml`。不改 `codeside/`、`schema/`、`paperside/`、根 `pyproject.toml` |
| D8 | 记录格式 | sidecar `ExecutionReport`（含 `Scorecard`）+ 标准 `TestCase`（能通过 `python -m codeside.cli validate`） |
| D9 | 判定与评分 | 按 `SCORECARD.md` |
| D10 | 范围 | F01 到 F07；`accuracy`、`performance`、`resource` 类默认 `inconclusive` |
| D11 | 校准 | 故障注入得到已知答案的样本，调权重和阈值 |
| D12 | 提交 | 小步提交，只加 `checklimits/` 下的文件，不用 `git add -A`。推送前先问 |

## 6. P0 要用实验确定的事项

| # | 问题 | 实验 | 不通过时 |
|---|---|---|---|
| U1 | opencode 能否通过中继使用 `x-test-2`，并完成一次 shell 工具调用 | 写 `opencode.jsonc` 的自定义 provider；用非交互模式跑一个"列出目录"的任务 | 换 dsh |
| U2 | 运行时是否外发数据（opencode 的分享或遥测；dsh 的会话日志、OTel） | 查配置并关闭；看中继日志，确认只有发往中继的请求，另用 `ss -tnp` 查进程的外连 | 不用该运行时 |
| U3 | 运行时的权限设置能否把写入限制在 scratch 目录 | 让 agent 试着写目录外的文件 | 以 harness 的子进程隔离为准；agent 只在 scratch 目录里工作 |
| U4 | `findlimit` 里 torch(CPU) 能否装上；FlexPrefill 能否 import | 安装并 import | 缺失依赖用记录型替身并登记；仍不行再提议另建 3.11 环境（需同意） |
| U5 | 替换 triton 后 F07、F01 能否到达第 1824、1836 行 | 手写调用 | 调整策略级别 |
| U6 | 运行时版本 | 记下版本并锁定 | 控制破坏性变更 |

U4、U5 已排除网络和 agent，可以和 P1 同时做。

## 7. 目录结构

```
cs6223-limitation-pipeline/checklimits/
  PLAN.md  SCORECARD.md  KICKOFF_PROMPT.md  scoring_prototype.py
  pyproject.toml  .gitignore            # 忽略 .deps/ scratch/ runs/
  checklimits/
    __init__.py  __main__.py  cli.py
    models.py        # AttemptManifest、AgentForm、ExecutionReport、Scorecard
    adapter.py       # Finding/Limitation/Region -> 任务描述；witness_hint -> inputs
    relay.py         # 中继（D5）
    fakes.py         # 记录型替身
    runner.py        # 子进程运行、超时、异常与 traceback、环境变量清理
    tracer.py        # sys.settrace / sys.monitoring：目标行、判定结果、变量抓取、call_chain 覆盖率
    audit.py         # 重算声明项，表单一致率
    fidelity.py      # AST diff、mock 的 on_path、探针影响
    mutate.py        # 目标判定变异（先用 ast，必要时换 LibCST）
    replay.py        # 干净环境重放
    verdict.py  scoring.py   # scoring.py 由 scoring_prototype.py 演化
  agent/
    INSTRUCTIONS.md  # 给 code agent 的指令（T1 到 T9、命令行用法、填表）
    opencode.jsonc   # provider 指向中继
  tests/
  results/flexprefill/
```

## 8. 阶段

| 阶段 | 内容 | 验收 |
|---|---|---|
| **P0 探路** | 中继；U1 到 U6；拉取 FlexPrefill（`scripts/fetch_pilot.sh`，固定 `a24b27b`） | 经中继的 x-test-2 调用成功，且中继日志里没有明文 key；FlexPrefill 在 `findlimit` 里能 import；选定运行时，结论写入本文件 |
| **P1 确定性核心（不接 LLM）** | models、adapter、fakes、runner、tracer、audit、fidelity、verdict、scoring；**手写** F07 和 F01 的 attempt 包 | 两条都得到 `yes`；反例对照成立；`pytest` 通过；`codeside.cli validate` 通过 |
| **P1b 变异与重放** | mutate、replay、探针影响 | F07、F01 有实测的杀死率、重放一致性和档位 |
| **P2 agent 层** | `INSTRUCTIONS.md`、命令行、预算 | F07、F01、F04 由 agent 自主完成，判定与手写版一致，表单一致率有数字 |
| **P3 全量 pilot 与校准** | F05、F06、F03、F02；故障注入校准集 | 每条都有报告；校准集上的判定准确率 |
| **P4 推广** | NNSmith；对接 Wanting 步骤 4；M6 动态 trace 对照 | 第二个 artifact 跑通 |
| **P5 评估** | RQ2、RQ3、成本 | 表格与 case study |

## 9. 风险

| 风险 | 缓解 |
|---|---|
| 运行时接口变化或不可用 | 固定版本；agent 与 harness 只通过命令行和 manifest 通信 |
| 运行时外发数据 | U2 验证；未确认前不用 |
| 密钥泄露 | 中继注入 key；子进程环境清理 `SOCLAAS_*`；不打印凭据文件 |
| agent 虚报表单 | harness 重算；变异、重放、重复、mock 访问由 harness 独占 |
| agent 事后改 oracle | 首次运行前登记哈希，事后修改计数扣分 |
| 评分权重没有依据 | 明说是初始值，用故障注入校准 |
| 执行仓库代码有风险 | scratch 目录、超时、环境变量清理 |
| Python 3.14 对 torch、triton 支持不确定 | U4 先验证；记录型替身兜底 |
| `witness_hint` 格式未定 | adapter 单独成层，只实现两种已知形状 |

## 10. 需要你确认

1. 允许在 `findlimit` 里 pip 安装依赖（torch CPU、pydantic、pytest、coverage 等），并用 npm 把 opencode 装到用户目录吗？
2. artifact 特有依赖用 `pip install --target .deps/<artifact>`（§4 第 7 项）可以吗？
3. 中继注入密钥的方案（§4 第 1 项）可以吗？
4. 允许移动 `shanghao_exec_report_draft.py` 进 `checklimits/` 吗？


## 11. 决定记录（2026-11-11 晚，Shanghao 对 P0/P1 报告的回复）

| # | 事项 | 决定 | 落实 |
|---|---|---|---|
| 1 | 没有 GPU 时下游怎么办 | 尽量用过程模拟（torch 原生函数、triton-cpu 一类），**必须缩小规模**；目的是模拟行为来判断 limitation 是否存在，不要求与 GPU 逐位一致 | 已做：F07/F01 反例改为跑完整稀疏路径（真实 `get_active_blocks` + 两个 CPU 替身），规模缩到 1/8，见 `ENV.md` |
| 2 | 反例在目标行之后崩溃 | 把下游 mock 掉，让反例正常返回。原则：尽量用 mock 和 simulator 获取更多信息和结论，并对"经过替身得到的信息"按过程分析打置信度 | 已做：`ExecutionReport.information` 里每条信息记录依赖的替身、规模权重和置信度（`fidelity.SIM_WEIGHT`，初始值待校准） |
| 3 | 相邻点的判定 | 由 agent 视情况决定 | P2 的 agent 指令里写明；harness 现有的启发式只作兜底 |
| 4 | 另建 Python 3.11 环境 | 允许，用 pip venv，放在项目临时存储目录，后续可删 | `checklimits/scratch/venv311/`，`scripts/make_venv311.sh` |
| 5 | opencode 安装与 U1 到 U3 | 同意 | 未开始，等 P2 的启动 prompt |
| 6 | 预算上限 | 可以放得更宽 | 未定具体数值，P2 再定 |
| 7 | `TestCase.inputs` 格式（`role` 键）与 `result_notes` | 确认 | 保持现状 |

| 8 | 置信度方案（2026-11-11 晚第二轮） | 四项均批准：放弃数值最终分；档位定义和 profile 初始值；判定只依赖 direct 的观察；先改 harness，再写 agent skill 与 workflow | 已实现，见 `CONFIDENCE_SPEC.md` §11。下一步：agent skill、workflow 与缺陷清单回环；故障注入基准与校准 |
| 9 | 合并 `wanting/step4-findings`（2026-11-11 晚） | 用户要求检查、合并并继续开发 | 已合并（无冲突）；适配 schema 0.2.0（类别改名）和 witness-v2（trigger/contrast）；`adapter.py` 可直接读 `results/step4/<artifact>/limitations_for_tests.json`，并从 Limitation 构造 Region（step 4 不产出 Region，调用链只有"入口函数 + 所在函数"）。65 条 FlexPrefill Finding 全部能加载，其中 23 条是当前 harness 能测的（代码侧、`reject`、witness 为 solved 的输入对）。agent 层已完成，见 `AGENT_RESULTS.md` |
| 10 | 规则决定与下一步（用户回复） | `no` 判定在 D3 被推翻时不强制 `inconclusive`（保持最高 L1）；下一步 (a) 扩展效果判定，再 (b) 批量跑可测的 Finding；批准推送当前分支 | 已推送 `origin/somehow6/check_limits`；(a) 已做并有 agent 运行，见 `AGENT_RESULTS.md` 和 `CONFIDENCE_SPEC.md` §13 |
| 11 | 下一步方向（用户选 b） | 第二个 artifact | NNSmith 已做完：`NNSMITH_RESULTS.md`。三处 harness 缺陷已修；`CONFIDENCE_SPEC.md` §15 |
| 12 | 端到端关键路径（2026-11-15，依据 `docs/E2E_PLAN_P0_2026-11-15.md`） | 先完成 Shanghao 的 S1、S2、S3 | 已实现：`python -m checklimits test / report / envcheck`；契约见 `CONTRACT_TEST_REPORT.md`；报告样例在 `results/e2e/`。`pipeline test` 的接线（W6）在 `pipeline/run.py`，不在本目录，未改 |
| 13 | 阶段 A、B、C、D 的可做部分（2026-11-16，用户批准，P 选 FlexPosit，备选 QoServe/Niyama） | A1 `pipeline test` 实跑；A2/A4 用调用链重跑 agent；B1 FlexPosit 预检；C 的 S4b 分析；D 的 S5a/S5b/S5c、C1a | 见 `EXPERIMENTS.md`（25 次运行）、`PREFLIGHT_FLEXPOSIT.md`（60 个仓库测试通过，无人工步骤）、`S4B_OTHER_EFFECTS.md`（不实现新 oracle，依据）、`CONFIDENCE_SPEC.md` §16 §17（82 个 case，假阳性 0，L1 的 `no` 一半错）；`labels/` 是待三人标注的 20 条。FlexPosit 的完整 pipeline 运行（W4、Z4）在别人那里，未做 |
