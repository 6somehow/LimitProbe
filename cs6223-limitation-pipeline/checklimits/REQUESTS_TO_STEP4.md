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
