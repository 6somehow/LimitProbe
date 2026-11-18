# 批量运行：step 4 里 harness 能判断的 33 条 FlexPrefill Finding（2026-11-12）

选取规则（`python -m checklimits batch --list`）：代码侧 Finding、Region 的效果类型 harness 能判断（`reject`，或目标是 `if` / `while` 的 `fallback` / `state_dependent`）、step 4 求解器给出了可用的 witness。65 条中选了 33 条；其余 32 条的原因：19 条没有代码位置（论文侧），7 条 witness 为 infeasible，4 条效果类型是 suspicious，1 条 witness 只有 trigger，1 条目标不是分支。

每条一个 agent 会话（`x-test-2`，bwrap 沙箱，白盒：agent 能读 harness 源码），harness 在沙箱外重算全部判定和档位。**没有真值，下面的数字是分布，不是准确率；档位未校准。**

## Verdicts and levels

| | count |
|---|---|
| inconclusive / invalid | 1 |
| inconclusive / n/a | 2 |
| yes / L1 | 15 |
| yes / L2 | 8 |
| yes / L3 | 7 |

## Per finding

| finding | outcome | review | verdict | level | integrity | calls | tokens (M) | s | not eliminated |
|---|---|---|---|---|---|---|---|---|---|
| F001 | reject | worth_testing | yes | L1 | 1.0 | 41 | 1.55 | 345 | D3=res, D5=res, D14=res |
| F002 | reject | unreviewed | yes | L1 | 1.0 | 36 | 1.95 | 454 | D3=res, D14=res |
| F003 | reject | real_but_minor | yes | L3 | 1.0 | 40 | 1.56 | 231 |  |
| F005 | reject | unreviewed | yes | L1 | 1.0 | 42 | 2.39 | 393 | D3=res, D14=res |
| F006 | reject | unreviewed | yes | L1 | 1.0 | 66 | 4.01 | 677 | D5=ref, D14=res |
| F007 | reject | unreviewed | yes | L2 | 1.0 | 60 | 3.78 | 725 | D14=res |
| F008 | reject | unreviewed | yes | L2 | 1.0 | 37 | 1.79 | 399 | D14=res |
| F009 | reject | unreviewed | yes | L2 | 1.0 | 41 | 2.37 | 523 | D14=res |
| F010 | reject | unreviewed | inconclusive | n/a | 0.333 | 69 | 4.01 | 762 | D1=ref, D2=ref, D3=ope, D4=ref, D5=ope, D9=ref, D14=ref |
| F011 | reject | unreviewed | yes | L2 | 1.0 | 35 | 1.46 | 369 | D14=res |
| F012 | state | unreviewed | yes | L1 | 1.0 | 35 | 1.69 | 427 | D3=res, D5=res, D6=res |
| F013 | reject | unreviewed | yes | L3 | 1.0 | 38 | 1.03 | 212 |  |
| F014 | reject | unreviewed | yes | L3 | 1.0 | 42 | 1.84 | 243 |  |
| F015 | reject | real_but_minor | yes | L1 | 1.0 | 86 | 3.49 | 726 | D3=res, D14=res |
| F016 | reject | real_but_minor | yes | L2 | 1.0 | 46 | 2.16 | 488 | D14=res |
| F017 | path_change | real_but_minor | yes | L1 | 1.0 | 49 | 2.08 | 279 | D3=res, D5=res, D14=res |
| F018 | path_change | worth_testing | yes | L1 | 1.0 | 45 | 1.53 | 291 | D3=res, D5=res, D14=res |
| F019 | reject | worth_testing | inconclusive | invalid | 1.0 | 62 | 1.98 | 470 | D2=ref, D3=res, D5=res, D14=res |
| F020 | path_change | worth_testing | yes | L2 | 1.0 | 40 | 2.35 | 646 | D6=res, D14=res |
| F021 | path_change | real_but_minor | yes | L1 | 1.0 | 56 | 3.25 | 594 | D3=res, D6=ref, D14=res |
| F022 | reject | worth_testing | yes | L1 | 1.0 | 31 | 1.05 | 243 | D3=res, D5=res |
| F023 | reject | unreviewed | yes | L1 | 1.0 | 48 | 2.23 | 413 | D3=res, D5=res, D14=res |
| F024 | reject | unreviewed | yes | L1 | 1.0 | 54 | 2.99 | 565 | D5=ope, D6=res |
| F026 | path_change | unreviewed | yes | L3 | 1.0 | 54 | 3.25 | 638 |  |
| F027 | reject | real_but_minor | yes | L1 | 1.0 | 78 | 3.24 | 586 | D3=res, D5=res, D6=res, D14=res |
| F028 | path_change | real_but_minor | yes | L1 | 1.0 | 70 | 3.32 | 753 | D3=res, D6=res, D14=res |
| F029 | path_change | real_but_minor | yes | L2 | 1.0 | 62 | 4.09 | 570 | D6=res, D14=res |
| F039 | path_change | real_but_minor | yes | L1 | 1.0 | 36 | 1.38 | 294 | D3=res, D5=res, D14=res |
| F047 | reject | wrong | inconclusive | n/a | 0.333 | 75 | 4.01 | 722 | D1=ref, D2=ref, D3=ope, D4=ref, D5=ope, D9=ref, D14=ref |
| F052 | reject | unreviewed | yes | L3 | 1.0 | 23 | 0.42 | 149 |  |
| F053 | path_change | unreviewed | yes | L3 | 1.0 | 41 | 1.89 | 275 |  |
| F054 | reject | unreviewed | yes | L3 | 1.0 | 33 | 1.12 | 245 |  |
| F055 | reject | real_but_minor | yes | L2 | 1.0 | 79 | 3.47 | 724 | D6=res, D14=res |

## What keeps findings below L3

| defeater | state | runs |
|---|---|---|
| D1 | refuted | 2 |
| D14 | refuted | 2 |
| D14 | residual | 21 |
| D2 | refuted | 3 |
| D3 | open | 2 |
| D3 | residual | 14 |
| D4 | refuted | 2 |
| D5 | open | 3 |
| D5 | refuted | 1 |
| D5 | residual | 9 |
| D6 | refuted | 1 |
| D6 | residual | 7 |
| D9 | refuted | 2 |

## Runs that did not end in `yes` (read these first)

* **flexprefill-F010**: verdict=inconclusive final=inconclusive level=n/a; NotImplementedError at workspace/attempt/driver.py:11 before the target was reached | NotImplementedError at workspace/attempt/driver.py:11 before the target was reached; 
    - D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix)
    - D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated
    - D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
* **flexprefill-F019**: verdict=yes final=inconclusive level=invalid; ValueError at flex_prefill/modules/patch.py:320 | no exception at flex_prefill/modules/patch.py:320; 
    - D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated
    - D3 (residual): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location
    - D5 (residual): change exactly one factor between positive and negative, and make the negative the point next to the boundary
* **flexprefill-F047**: verdict=inconclusive final=inconclusive level=n/a; NotImplementedError at workspace/attempt/driver.py:11 before the target was reached | NotImplementedError at workspace/attempt/driver.py:11 before the target was reached; 
    - D1 (refuted): choose inputs that reach the target line (check Region.condition.path_prefix)
    - D2 (refuted): pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated
    - D3 (open): run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location

## Cost

tool calls 1650, LLM steps 1444, tokens 78.7M (counts every re-sent context), agent wall time 257 min summed over runs.

## 读法与发现

**1. 分布。** 33 条里 30 条 `yes`：7 条 L3、8 条 L2、15 条 L1；3 条没有结论（1 条 invalid，2 条 n/a）。`yes` 多不说明 Finding 都是对的，原因见下面第 5 点。

**2. 是什么压低了档位。** 不是判定本身，是证据的完整度：
- **D14（入口）residual，21 条。** Region 的调用链只有"入口函数 + 目标所在函数"，而目标往往在更深的函数里（如 `triton_flash_prefill`），没有 GPU 时无法经官方入口走到，agent 直接调用目标函数并写 `entry_reason`。这是 D14 设计的预期结果（residual，最高 L2），根源是 step 4 不提供真实调用链。
- **D3（变异）residual，14 条。** 守卫只有一两个可变异点（`x is None`、单个比较），变异体少于 `n_min=4`。
- **D5（相邻点）residual 9 条。** 状态类（无法探测邻点）、或边界变量不是整数。
- **D6（替身）residual 7 条、refuted 1 条。** 检查之前的路径必须经过替身。

**3. 没有 yes 的三条：**
- **F010**（`triton_bnhd_pool` 里的 `assert d in {16,32,64,128}`）：路径前缀要求入口函数的 `head_dim` 已在集合内，而条件要求 `d`（`head_dim` 传到这里的参数）不在集合内；我从任务描述推断，经官方入口不可达，没有进一步验证。agent 用完 400 万 token 预算，driver 仍是 init 的占位实现，harness 报 `inconclusive`，表单一致率 0.33。
- **F047**：盲审标签是 `wrong`，同样 token 预算用尽、没有写出可运行的 driver。
- **F019**：agent 判 `yes`，但 harness 发现反例根本没走到目标行（D2 refuted），强制改为 `inconclusive`。这是审计在起作用的例子：agent 声称成功，证据不支持。

**4. 批量运行发现并修复的两个 harness 缺陷**（修复后相关 finding 重新运行）：
- 多行 `assert (...)` / `if (...)` 目标：异常抛在语句内部某一行，3.12+ 的 LINE 事件也不落在关键字那一行，旧规则只认首行，F006 被误判。现在按语句跨度判断，片段比较改成比较解析后的条件（step 4 把多行语句并成一行并丢掉 assert 消息）。
- 嵌套函数名：Region 写 `outer.inner`，CPython 的 `co_qualname` 是 `outer.<locals>.inner`，F020 的目标语句被误判为"已被改动"（D11）。修复后 F020 从 invalid 变为 yes / L2。

**5. 这些数字不能解释成什么。**
- `yes` 只表示"agent 找到了一对输入，使 Region 条件所说的效果在目标处出现、在邻点不出现"，且 harness 重算一致。不表示 Finding 对用户有意义，也不表示 step 4 的 Region 和条件没有读错（批量里只有 F019、F010 这类才会暴露）。
- 33 条全是 FlexPrefill，agent 是同一个模型，没有重复运行，没有方差。
- 白盒：agent 读过 harness 源码，知道每个 defeater 怎么算。
- 表单一致率几乎全是 1.0，说明 agent 的声明与重算一致，这是设计上 agent 在运行后根据报告填 claims 的结果，不能当成"诚实度"的强证据。

**6. 对 step 4 数据的反馈：**
- Region 的调用链应是真实的"入口到目标"的链（现在只有两个元素），否则 D14 总是 residual。
- F010 的 witness 看起来没有把子函数参数 `d` 与入口参数 `head_dim` 关联起来（推断，见上），值得核对。
- 盲审标签与结果：`real_but_minor` 10 条全是 yes；`worth_testing` 5 条里 4 条 yes（另一条是 F019）；`wrong` 的 F047 没有测出来；未审的 17 条里 16 条 yes。样本太小，不能说盲审标签预测了可测性。


## 补记（2026-11-12）：变异算子 v2 之后的重新审计

补了 `is` / `in` / `and` / `or` 互换，并去掉单比较守卫里与取反重复的互换（`CONFIDENCE_SPEC.md` §14）。对上面 33 个已归档 attempt 重新跑 harness（`python -m checklimits reaudit`，不重新运行 agent）：32 条不变，**F053 从 L3 降到 L1**（3 个变异体 < 4）。上面表格里 F053 的 L3 是旧算子集下的结果。分布变为 L3 6 条、L2 8 条、L1 16 条、无结论 3 条。


## 补记二（2026-11-12）：第二个 artifact 之后的规则修正

NNSmith 的批量（`NNSMITH_RESULTS.md`）暴露了三处 harness 缺陷，修复后对本页的 33 个 attempt 再次重新审计，结果与"补记"一致（只有 F053 变化）。对本页有一处解释要改：**F047 没测出来不是 agent 的问题**，它的目标语句（`flex_prefill_attention.py:1221` 的 `if`）不能抛异常，`reject` 标签不适用，现在 harness 直接返回 `not_run`。F047 因此不再属于可判断的 Finding，可判断的 FlexPrefill Finding 是 32 条。


## 补记三（2026-11-16）：agent 当时能看到哪些已有的结果

这批运行时，沙箱没有隐藏 `agent_results/`（已归档的 agent 测试包）。事后检查每次运行的事件日志：30 次 FlexPrefill 批量运行里 27 次提到了 `agent_results`，26 次 NNSmith 运行里 24 次提到。也就是说，**agent 大多读过别的 Finding 的已有测试包作为样例**。对 FlexPrefill 这更重要：F013、F014、F052 的目标语句和手写 pilot 的 F01、F04、F07 是同一行（`assert q.shape[1] == k.shape[1]` 等），当时 `agent_results/f01-r1`、`f04-r1`、`f07-r2` 是可读的，这三条的测试包可能直接借用了它们的写法。我没有逐条核对谁借用了。

从 2026-11-16 起，`agent_results/` 和各结果文档在沙箱里不可见（`agent_loop.HIDE_PATHS_DIRS`，有测试）。上面的分布因此应读作"agent 能看到别的 Finding 的样例"的结果；不带样例的运行见 `EXPERIMENTS.md`。


## 补记四（2026-11-17）：规则改动之后的分布

11-16 到 11-17 harness 有三处改动（`CONFIDENCE_SPEC.md` §18、§19）：`no` 只在 D3 已消除时报告；目标是裸 `raise` 时在守卫上求 D2；D14 要求目标在入口里执行。用新规则对 `results/e2e/` 里的测试包重新审计，并补上了 11-16 用调用链重跑的 agent 测试包（`EXPERIMENTS.md`），这个文档上面的分布因此不再是现状。现状：

FlexPrefill：29 条已测，判定 {'yes': 29}，档位 {'L1': 16, 'L3': 6, 'L2': 7}；没测的原因 {'no_code_location': 19, 'outcome_unsupported': 6, 'witness_unusable': 11}。逐条见 `results/e2e/report/flexprefill/LIMITATIONS.md`。
