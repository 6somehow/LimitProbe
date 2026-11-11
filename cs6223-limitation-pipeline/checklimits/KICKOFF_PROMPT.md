# 启动开发 prompt（P0 + P1）

把下面 `---` 之间的内容整段发给 code agent（Kiro、Claude Code 或 opencode 都可以）。
它只覆盖 P0 和 P1，不接 LLM 跑测试；P2 以后另发 prompt。

---

你在 `<workspace>` 仓库的 `somehow6/check_limits` 分支上工作，帮 Shanghao 开发 check_limits：一个在 CPU 上验证 limitation finding 的 agent 系统。本次任务是 **P0（探路）和 P1（确定性核心，不接 LLM）**。

## 先读这些文件，读完再动手

1. `cs6223-limitation-pipeline/checklimits/PLAN.md`：计划，重点是 §3 pilot 对象、§4 修正、§5 决定、§6 未知项、§7 目录、§8 验收。
2. `cs6223-limitation-pipeline/checklimits/SCORECARD.md`：测试设计要求 T1 到 T9、评分维度、门槛、判定规则 §3.5、重放定义 §3.6、表单格式 §6。
3. `cs6223-limitation-pipeline/checklimits/scoring_prototype.py`：评分参考实现，`scoring.py` 要与它的结果一致。
4. `cs6223-limitation-pipeline/schema/models.py`：共享 schema，只读。`TestCase` 在这里。
5. `cs6223-limitation-pipeline/data/pilot_flexprefill/` 下的 `draft_findings.json`、`gold_code_limitations.json`、`gold_regions.json`、`artifact.json`。
6. `cs6223-limitation-pipeline/docs/04_pilot_flexprefill.md` 的"CPU 执行时要提醒 Shanghao 的点"。
7. `<workspace>/shanghao_exec_report_draft.py`：报告结构草稿，`Confidence` 部分已被 SCORECARD 取代。

如果这些文件之间有矛盾，以 `SCORECARD.md` 为准，并把矛盾写进最后的报告。

## 环境与约束

- Python 一律用 conda 环境 `findlimit`：`<python>`（3.14.10）。不要新建 venv 或 uv 环境。
- 可以在 `findlimit` 里 `pip install`：pydantic、pytest、coverage、torch（CPU 版，`--index-url https://download.pytorch.org/whl/cpu`），以及 FlexPrefill import 所需的包。每装一个包都记进 `checklimits/ENV.md`（包名、版本、原因）。
- FlexPrefill 用 `cs6223-limitation-pipeline/scripts/fetch_pilot.sh` 拉取，固定 commit `a24b27bf117fd6ad4ba34b0db82c598e7786fd59`。**不要修改 `third_party/` 下的任何文件**。
- SoCLaaS：基地址和 key 在 `<key-dir> `set -a; . soclaas.env; set +a` 加载为环境变量。直连会超时，出站必须绑定 `eth0`（用 `ip -4 -o addr show eth0` 在运行时取地址，不要写死）。
- 只在 `cs6223-limitation-pipeline/checklimits/` 下创建或修改文件。不要改 `codeside/`、`schema/`、`paperside/`、根 `pyproject.toml`、`slides/`、仓库根的 `.gitignore`。
- 被测代码运行的子进程必须清除 `SOCLAAS_*`、`*_proxy`、`OPENAI_*` 环境变量，并设超时。

## 必须先停下来问的事

- 需要 sudo、改系统路由或网络配置。
- `findlimit` 装不上 torch 或 FlexPrefill 依赖，打算另建 Python 环境。
- 想修改约束允许范围以外的文件，或删除任何文件。
- `git push`，或任何改写历史的 git 操作。
- 安装 opencode 或 dsh（P0 的 U1 到 U3 本次**不做**，只做中继和 U4、U5）。

## 任务

### P0

1. **中继** `checklimits/checklimits/relay.py`：只用标准库。监听 `127.0.0.1`（端口可配），把 `/v1/*` 转发到 SoCLaaS，出站源地址绑定 `eth0` 当前地址，在出站请求上加 `Authorization: Bearer <key>`（key 只从环境变量读取），忽略并丢弃客户端发来的 `Authorization`。支持流式响应（SSE 逐块转发）。日志只记方法、路径、状态码、耗时、模型名，**不记请求头和请求体**。
   验收：用假 key 通过中继请求 `/v1/models` 得到 200 且列表含 `x-test-2`；用一个带 `tools` 的 `chat/completions` 请求，得到 `finish_reason=tool_calls`；流式请求能收到 `[DONE]`；`grep` 中继日志找不到 `clsk_`。
2. **U4**：在 `findlimit` 里装 torch(CPU)，尝试 import `flex_prefill.ops.flex_prefill_attention`。triton 能装就装；import 时 GPU 相关的东西失败，就记下失败点，不要改仓库。
3. **U5**：写一个最小脚本，替换掉 import 阶段的 GPU 依赖（如 triton、`GPU_NAME`），调用 `flex_prefill_attention`，确认 F07（`batch_size=2`）在第 1824 行、F01（`q_len=4096, k_len=8192`）在第 1836 行抛出 `AssertionError`，并确认反例（`batch_size=1`；`k_len=4096`）不在这两行抛异常。把需要替换的符号和原因写进 `ENV.md`。

### P1（按 `PLAN.md` §7 的结构）

4. `pyproject.toml`、`.gitignore`（忽略 `.deps/`、`scratch/`、`runs/`）、包骨架。
5. `models.py`：`AttemptManifest`、`AgentForm`（`SCORECARD.md` §6）、`Scorecard`、`ExecutionReport`。pydantic v2，`extra="forbid"`。另写一个函数生成标准 `schema.models.TestCase`。
6. `adapter.py`：从 Finding 经 `limitation_ids` → `region_ids` 取到 Region；把 `witness_hint` 转成 inputs（平铺 → `input_value`；`call_1`、`call_2` 等 → `event_sequence`）。
7. `fakes.py`：记录型替身，记录每次属性访问和调用的顺序号，供 `on_path` 判断。
8. `runner.py` + `tracer.py`：在子进程里运行 attempt；记录目标行（`Region.location`）是否执行、执行时的局部变量快照、目标判定的真假结果、`call_chain` 内函数的行覆盖；捕获异常类型和抛出位置（file:line）。用 `sys.monitoring`（3.12+）或 `sys.settrace`，选一个并在代码注释里说明理由。
9. `audit.py`：用运行产物重算 `AgentForm.claims` 中每一项，输出一致率和不一致明细。
10. `fidelity.py`：仓库 AST diff（应为 0）、mock 的 `on_path`（由 fakes 的记录计算）、入口深度、探针影响（有 hook 与无 hook 结果对比）。
11. `verdict.py`：实现 `SCORECARD.md` §3.5 的判定表。
12. `scoring.py`：实现 `SCORECARD.md` §3 到 §5。在 `tests/` 里用 `scoring_prototype.py` 的 9 个样例做回归，数字必须一致（误差 1e-3 以内）。
13. **手写** F07 和 F01 的 attempt 包（放在 `checklimits/attempts/flexprefill/F07/`、`F01/`），按 T1 到 T9 写：先登记 oracle，正反例只差一个因素。
14. `cli.py`：`python -m checklimits run --attempt <dir>` 运行 attempt 并输出 `results/flexprefill/<test_id>.report.json` 和 `<test_id>.testcase.json`。本次变异、重放、重复可以先返回"未运行"，但要让 `scoring.py` 正确处理未运行的情况（会降分，这是预期的）。

## 验收（全部要有你实际跑出来的输出作为证据）

- `findlimit` 下 `python -m pytest -q checklimits/tests` 全部通过。
- F07、F01 的判定都是 `yes`；报告里 `target_reached=true`，异常位置分别是第 1824、1836 行，反例对照成立。
- `cd cs6223-limitation-pipeline && python -m codeside.cli validate checklimits/results/flexprefill/*.testcase.json` 通过。
- `git diff --stat` 只显示 `checklimits/` 下的文件；`third_party/FlexPrefill` 的 `git status` 是干净的。
- 全仓库搜索 `clsk_` 没有命中（`slides/` 除外）。

## 提交

小步提交，每步一个 commit，只 `git add` 具体文件，不用 `git add -A`。提交信息用英文，说明做了什么。不要 push。

## 最后的报告

用中文，写清楚：
1. 每条验收的结果和对应的命令输出。
2. U4、U5 的结论：装了什么、替换了什么、哪些在路径上。
3. F07、F01 报告里的各维度分数、门槛、最终分和档位。
4. 计划或评分表里你发现的矛盾、模糊处或认为不合理的地方。
5. P2 开始前需要 Shanghao 决定的事。

---
