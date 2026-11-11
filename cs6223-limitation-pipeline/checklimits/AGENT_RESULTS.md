# 自主 agent 运行结果（P2，2026-11-11）

运行时 opencode 1.19.5（npm 装在 `scratch/opencode/`，用户目录，可删），模型 `x-test-2`（经中继，temperature 由服务端默认），沙箱 bwrap。命令：`python -m checklimits agent <finding> --run-id <id>`。每次运行的 attempt 包、报告和成本在 `agent_results/<run-id>/`。

## 结果

| run | finding | 输入来源 | 判定 | 档位 | 表单一致率 | 工具调用 | LLM 步数 | token（含重复上下文） | 用时 |
|---|---|---|---|---|---|---|---|---|---|
| f07-r2 | F07 | 试点数据 | yes | L3 | 1.0 | 37 | 36 | 1.52M | 255 s |
| f01-r1 | F01 | 试点数据 | yes | L3 | 1.0 | 24 | 25 | 0.83M | 175 s |
| f04-r1 | F04 | 试点数据 | yes | L3 | 1.0 | 39 | 29 | 1.29M | 256 s |
| s4-f014-r1 | flexprefill-F014 | step 4 hand-off（witness-v2） | yes | L3（D13 residual） | 1.0 | 42 | 38 | 1.84M | 244 s |

手写版的判定与档位：F07、F01、F04 都是 yes / L3。**三条的判定与手写版一致**，档位相同。每次运行都没有触发 oracle 锁篡改检测（`lock_tampered=false`）。

### 第二批：新的效果类型（fallback、state_dependent）

harness 现在能判断三类效果：`reject`（目标位置抛异常）、`fallback` / `mechanism_variant`（目标处的 `if` / `while` 判定被执行，即走进分支）、`state_dependent`（同样的分支判定，但检查的是最后一次调用，之前由 prelude 调用改变状态）。目标不是 `if` / `while` 时返回 `not_run` 并给出原因。

| run | finding | 效果类型 | 判定 | 档位 | 表单一致率 | 工具调用 | 用时 | 未消除的 defeater |
|---|---|---|---|---|---|---|---|---|
| s4-f053-r1 | flexprefill-F053 `if q_len == 1:` (1825) | fallback | yes | L3 | 1.0 | 41 | 275 s | 无 |
| s4-f026-r1 | flexprefill-F026 `if q_len <= max(2*block_size, ...)` (1842) | fallback | yes | L3 | 1.0 | 54 | 639 s | 无 |
| s4-f012-r1 | flexprefill-F012 `if causal_mask is None:` (1695，`global` 缓存) | state_dependent | yes | **L1** | 1.0 | 35（两个 session） | 428 s | D3、D5、D6 为 residual |

F012 停在 L1，有三个结构性原因，agent 在最终总结里都说对了：

- **D3（变异）**：`x is None` 守卫只有一个变异体（取反），少于 `n_min=4`，所以 D3 无法消除，L2、L3 都到不了。
- **D5（相邻点）**：边界因素是程序状态（prelude），harness 无法探测状态的邻点。
- **D6（替身）**：检查调用之前的 prelude 调用必然跑过目标之后的 CPU 替身，所以反例观察是 `simulated:fake`（因果前缀分析给出的结果，规则按预期工作）。

这是第一次真实地走到"反馈回环第二个 session"：agent 收到 `next_steps` 后重跑，确认三项都不是它能修的，没有改报告，并说明了原因。

两点实现说明：
1. `state_dependent` 的"效果"按 SCORECARD §3.5 应是"第二次调用的结果与单独调用不同"。实现的是更窄的版本：**目标处分支判定在最后一次调用里与单独调用不同**。目标不是分支的状态类 finding 目前是 `not_run`。
2. Region 条件现在在局部变量之外也在模块全局里求值，F012 的 `causal_mask` 是 `global` 变量，否则条件无法求值，D2 会一直是 open。

## 设计与手写版对比

| | 手写 | agent |
|---|---|---|
| F07 | 缩到 q_len=512，2 个 CPU 替身（GPU kernel 启动器），S1 | 保持 witness 规模 4096，同样 2 个替身（同一对符号，同样的 sim 类别），S1 |
| F01 | 缩到 512/1024，2 个替身，S1 | 完整规模 4096/8192，**没有替身**，S0；反例在目标行之后因没有 GPU 崩溃（不影响判定，D6 只看判定依赖的观察） |
| F04 | 缩到 512，2 个替身，3 个 extra_negatives | 完整规模，**没有替身**，S0，4 个 extra_negatives |
| flexprefill-F014 | | trigger/contrast 为 head_dim 127/128，3 个 extra_negatives，1 个 sim（`flash_attn_func`） |

agent 在 F01、F04 上比手写版保真度更高：不缩放、不用替身。F04 里它自己加了 extra_negatives，按指令里的说明把集合守卫的每个成员各配一个输入，变异杀死率因此够用。

## 有效性说明（必读）

1. **第一次运行作废。** `scratch/agent_runs/INVALID-f07-r1-*`：agent 读到并复制了手写的 F07 driver。之后沙箱用 tmpfs 隐藏了 `attempts/`、`results/`、`locks/`、`tests/`、`scripts/`、`scratch/`（只重新暴露 venv 和 opencode）、`ENV.md`、`PLAN.md`、`KICKOFF_PROMPT.md`、`scoring_prototype.py` 和 git 历史。表里四次运行都在这之后，命令日志里没有访问这些路径的记录。
2. **agent 能读 harness 源码。** 它在 F07 运行里读了 `models.py`、`audit.py`、`confidence.py`、`mutate.py`、`bva.py` 等。这是白盒设定：规则公开，agent 知道每个 defeater 怎么算。结果衡量的是"知道规则的 agent 能否做出满足规则的测试"，不是"盲测"。要做盲测需要把 harness 源码也藏起来，那样 `cl` 就无法运行，要改成 harness 在沙箱外以服务形式运行。
3. **样本是 4 次运行、3 个 finding，全是 `reject` 型的 assert 守卫。** L3 在这里是容易达到的档位，不能推广到别的效果类型。`calibrated` 仍为 false。
4. **token 数含每一步重复发送的上下文**（opencode 的 `step_finish.tokens.total`），不是新增输入。f07-r2 因超过当时的 150 万 token 预算被中止，但它的 attempt 包在中止前已经写完，之后的认证运行正常；预算现已提到 400 万。
5. 同一个 agent、同一个提示，没有重复运行，所以看不到运行间方差。

## 沙箱与运行时验证（U1 到 U3，U6）

| 项 | 结论 | 证据 |
|---|---|---|
| U1 经中继使用 x-test-2 并完成 shell 工具调用 | 通过 | opencode `run --format json` 完成 `ls` / `echo` 工具调用并输出 DONE；中继日志只有 `POST /v1/chat/completions 200 ... model=x-test-2` |
| U2 运行时不外发数据 | 通过（有一处前提） | 沙箱内用 `ss -tnp` 每 0.2 秒采样，名为 opencode 的进程只连 `127.0.0.1:8787`。前提：HOME 预热（provider 包 `@ai-sdk/openai-compatible` 已在 npm 缓存里）并设 `npm_config_offline=true`；首次运行会连 npm registry 下载这个包。另设了 `share: disabled`、`autoupdate: false`、`OPENCODE_DISABLE_MODELS_FETCH=1` 等 |
| U3 把写入限制在 scratch | opencode 自带权限不可靠，用 bwrap 实现 | opencode 的 `permission` 只管它自己的工具，shell 里的 python 可以绕过；bwrap 以只读方式挂载整个文件系统，仅运行目录可写：写 `third_party/` 得到 `Read-only file system`，凭据目录在沙箱里是空的（`ls -A | wc -l` 为 0），写运行目录成功 |
| U6 版本 | opencode 1.19.5 | `scratch/opencode/node_modules/.bin/opencode --version`；该版本用 V1 配置语法（`provider`、`permission`），网上"latest"文档是 V2（`providers`、`permissions`），不能混用 |

## 未做或未验证

- 网络没有被封（没有 root，无法配防火墙）。agent 没有任何可泄露的凭据，但它理论上可以访问外网。
- 预算没有触发"所有 session 用完仍未达到目标"的路径，因此修复回环里"把 `next_steps` 反馈给 agent 再来一轮"这条路径在真实运行里没有被走到。回环代码有单元测试（预算、反馈文本），但没有端到端验证。
- 没有测量 agent 对规则的"过拟合"：它是否会在不理解的情况下照着 INSTRUCTIONS 模板套。需要用规则之外的 finding 测（例如 `fallback` 或 `state_dependent` 型），那需要先扩展 harness 的效果判定。
