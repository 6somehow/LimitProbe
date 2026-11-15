# 测试侧对 step 4 输出的请求（给 Wanting，2026-11-12）

来自对 `results/step4/flexprefill/limitations_for_tests.json` 的 33 条批量运行（`BATCH_RESULTS.md`）。每条都有证据位置；优先级按对测试置信度的影响排。

## 1. Region 里的真实调用链（影响最大）

**现状：** step 4 不产出 Region。测试侧从 Limitation 构造一个，`call_chain = [入口函数, 目标所在函数]`，中间的调用层不知道。

**后果：** 目标常在更深的函数里（例如 `triton_flash_prefill`、`patch_vllm_model.flex_prefill_forward`）。没有 GPU 时官方入口走不到，agent 只能直接调用目标函数并写 `entry_reason`。测试侧的"是否经过官方入口"检查（D14）因此对 33 条里的 21 条只能是 residual，这些 finding 最高 L2。

**请求：** 在 Limitation 或 Finding 里给出从入口函数到目标函数的调用链（函数名列表，入口在前），以及每一层调用时参数名的对应（例如入口的 `head_dim` 在子函数里叫 `d`）。步骤 2 的路线 A 已经分析了入口到目标的路径前缀，调用链应该是同一份分析的副产品。

## 2. 子函数里的 witness：参数名要和入口参数关联（F010）

`flexprefill-F010` 的目标是 `triton_bnhd_pool` 里的 `assert d in {16,32,64,128}`，条件是 `d` 不在集合内，路径前缀却要求入口函数的 `head_dim` 已在同一集合内。`d` 就是 `head_dim` 传下来的值（我推断，没有逐行核对），这两个约束合起来无解，经官方入口不可达。但 witness 状态是 `solved`。

**请求：** 求解器把调用链上"形参 = 实参"的绑定也带入约束；绑定后无解的标 `infeasible`（这样 priority 会降到 3，测试侧也不会花预算）。需要请求 1 的参数对应作为输入。

## 3. 多行语句的 snippet 约定

`flexprefill-F006`（`assert (` 跨 5 行）、F020、F024 的 `snippet` 是并成一行、去掉 assert 消息的形式。测试侧现在按解析后的条件比较，不再要求逐字相同，所以不需要改。只请在文档里写明这个约定（并行、去消息、去多余括号），以免以后改成别的形式而不通知。

## 4. 已知不影响测试侧、但值得知道的

* `Region.location.function` 对嵌套函数写成 `outer.inner`（没有 `<locals>`）。测试侧已按这个约定匹配，请保持。
* 19 条没有代码位置的论文侧 Finding 目前无法由测试侧处理（需要 differential / metamorphic 型 oracle，不在当前 harness 里）。如果论文侧能给出"论文公式对应的代码位置"，其中一部分可以按分支或异常效果测。

## 5. 效果标签的约定（P0-3 / W2，2026-11-15）

测试侧把每条 Finding 的 `effect_type` 当作"怎么判定"的指令。NNSmith 的 38 条里，15 条因为标签和目标语句对不上而没有测（`outcome_unsupported`），FlexPrefill 65 条里有 6 条。**这些不是测不了的 Finding，是标签用得不一致。**

| `effect_type` | 测试侧怎么判 | 因此目标语句必须是 |
|---|---|---|
| `reject` | 目标位置抛出异常 | `assert`、`raise`，或分支体里有 `raise` 的 `if` / `while` |
| `path_change`（测试侧叫 fallback） | 目标处的 `if` / `while` 条件为真，分支被执行 | `if` / `while` 语句本身（条件语句），不是赋值或函数调用 |
| `state` | 前置调用之后，同一分支的判定变化 | 同上，且 witness 里有前置调用序列 |
| `other` | 不判定 | 无要求 |

NNSmith 里的反例：`while not check_sat():`（F002）和 `if ...: continue`（F005、F007）被标成 `reject`，它们不抛异常；`path_change` 被标在赋值语句上的有 7 条。这些如果能改标成 `other` 或者给出真正抛异常的位置，测试侧就能区分"测不了"和"没有标准确"。

**请求：** step 4 在写 `effect_type` 前检查目标语句的类型，不满足上表的改标 `other`，或在 `witness_hint` 里另给出 `effect_location`（真正产生效果的语句）。测试侧会按这个字段重新选取。
