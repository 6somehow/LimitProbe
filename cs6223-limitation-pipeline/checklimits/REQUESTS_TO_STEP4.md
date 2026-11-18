> **已作废（2026-11-18）：** 这份请求不再转给 Wanting。她的部分由 Shanghao 一侧自己做。下面的内容保留作记录；§6 的两个问题（`override` 指向从未实例化的类；`infeasible` 只覆盖入口参数的线性约束）仍然存在，要做时见本文。

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

## 回复（Wanting，2026-11-15）

都已在 `somehow6/check_limits` 上实现，步骤 4 结果已重跑（五篇 289 条，finding_id 全部不变）。说明在 `docs/09_step4_findings.md` 的“2026-11-15 新增”一节。

| 请求 | 处理 |
|---|---|
| 1 调用链 | `witness_hint.call_chain`（入口在前，到目标所在函数为止）和 `call_sites`（每层调用所在行、解析方式、参数对应 `args`：被调函数形参 -> 调用者里的表达式），状态在 `call_chain_status`。静态找不到的标 `not_found`，不猜；靠猜解析的步骤列在 `uncertain_steps`。`adapter.py` 有 `call_chain` 时用它构造 Region（`tests/test_adapter_chain.py`），没有时保持原来的两层 |
| 2 F010 | 求解时把被调函数的名字换成入口函数的名字（`entry_terms`）。F010 现在是 `infeasible`、`infeasible_because: call_chain`，priority 3。同样被证明走不到的还有 F004、F005、F011 |
| 3 snippet | 步骤 4 现在把所有代码侧 snippet 统一写成一种形式：`assert <条件>`（去消息）、`if <条件>:` / `while <条件>:`（只有头部）、其它语句取 `ast.unparse` 的第一行；一行、去多余括号、最多 200 字符。约定写在 `docs/09_step4_findings.md` 和 HANDOFF。之前路线 B 的多行语句会只剩 `if (`（如 F020），现在不会了；你的 D12 比较两种都接受 |
| 4 | `outer.inner` 保持不变（调用链也用这个写法） |
| 5 效果标签 | 按上表检查（`codeside/effect_anchor.py`）。不满足的改 `other`，原因写在 Limitation 的 `notes` 和 `findings.report.json` 的 `effect_checks`。能找到真正产生效果的语句时（`except` 行 -> 处理块里的 `raise`；赋值 -> 条件相同的外层 `if`），目标移过去，`witness_hint` 里给 `effect_location` 和原来的 `labelled_location`；`code_evidence[0]` 也已经是新位置，所以现在的选取不用改就能用 |

另外：

* finding_id 跨运行不变了（由同一组 Limitation 组成的 Finding 沿用上一次的编号），已归档的 attempt 不会对错条目。
* 契约里 `witness_unusable` 归我的部分：原来的 6 条 `trigger_only` 都有了 contrast（nnsmith-F001 的条件被抄进了自己的路径前缀；minference-F006 是分支里无条件的 `raise`，现在用最内层的分支条件作判定）。剩下的 `witness_unusable` 都是 `infeasible`（FlexPrefill 11 条、InfiniGen 1 条），是有意的：从入口走不到，不用花预算。

效果（按你的 `classify_finding` 规则）：

| | FlexPrefill | NNSmith |
|---|---|---|
| `outcome_unsupported`（标签和语句不符） | 2 -> 0 | 13 -> 0 |
| 改成 `other` | 2 | 12 |
| 能判断 | 32 -> 29 | 19 -> 22 |

`pipeline test`（W6）已接上，按 `CONTRACT_TEST_REPORT.md` 调用和解释退出码，`pipeline status` 显示 test 阶段（done / stale / todo）。在我这台机器上 NNSmith 预检是 `not_ok`（缺 `multipledispatch`），所以没有产出可比的判定，归档的报告样例需要你在有环境的机器上重新生成。

## 6. 调用链用起来之后看到的三件事（Shanghao，2026-11-16）

用新调用链重跑 agent（`EXPERIMENTS.md`）：NNSmith F035 和 F012、FlexPrefill F008 的 D14 从 residual 变成 eliminated，所以调用链有用。同时有三处值得 Wanting 看：

1. **`override` 步骤指向没有被实例化的类（nnsmith-F034、F036）。** 调用链 `random_model_gen -> SimpleGenerator.abstract_gen -> GuidedGen.post_process` 里最后一步是 `override`（你已经列在 `uncertain_steps`）。agent 读源码发现 `GuidedGen` 在整个仓库里只有定义，没有实例化（`grep GuidedGen` 只有 `class GuidedGen` 和它自己的 `super().__init__`）；官方入口构造的是 `PureSymbolGen`，它的 `post_process` 是空操作。所以这两条的目标代码从官方入口走不到。建议：`override` 步骤的子类若在仓库里从未被构造，就把这一步标成不可达，witness 状态记 `infeasible`（`infeasible_because: unreachable_class`）。
2. **条件涉及列表长度时求解器不知道不可行（flexprefill-F007）。** 目标守卫是 `len(block_idx) == batch_size and len(block_idx[0]) == num_q_heads`（1245 行附近）。agent 读到官方入口调用 `get_active_blocks`，里面的 `transform_veritcal_slash_idx` 总是构造 `batch_size` 个、每个 `num_heads` 个元素的列表，所以守卫从官方入口不可能为假。step 4 现在记为 `solved`，因为这个构造不在入口参数的线性约束里。这类大概没法自动发现，请在 `HANDOFF.md` 里写明"`infeasible` 只覆盖入口参数可以线性表达的约束"。
3. **目标是裸 `raise` 时测试侧会判 `invalid`（nnsmith-F001、F003，flexprefill-F019，另有 infinigen-F004、minference-F006、F019 同类，共 6 条）。** 守卫成立时才会执行到 `raise`，对照点执行不到目标行，所以 D2（"条件在对照点为假"）无法在目标行上求值。这是测试侧的缺口，不是 step 4 的错，**还没有修**：要让 harness 在 `raise` 的外层 `if` 头上求值条件，需要改追踪器（两个后端）、运行器和审计，还没排。在那之前这 6 条的测试只能是 `invalid`。不需要你改什么；只请保持这几条的 `code_evidence[0]` 指向 `raise` 语句，我按这个约定改。

**更新（2026-11-17）：** §6 第 3 条已在测试侧修好（裸 `raise` 的 D2 现在在守卫上求值，`CONFIDENCE_SPEC.md` §18）；Wanting 只需继续保持 `code_evidence[0]` 指向 `raise` 语句。第 1、2 条仍待 Wanting 处理，测试侧不依赖它们。
