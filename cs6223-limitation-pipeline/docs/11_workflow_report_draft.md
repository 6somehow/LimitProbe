# CS6223 Limitation Pipeline：工作流与结果简稿（2026-11-18）

> 简稿。所有置信档位（L0–L3、A0–A2）都**未校准**，也**没有人工核对**；它们不是准确率。

## 1. 要解决的问题

给定一篇系统论文和它的代码仓库，自动找出"论文没说清、或代码里实际受限"的 limitation，并尽量用真实代码把它测出来。

## 2. 工作流

```
论文 PDF + 仓库(固定 commit)
   │
   ├─ 代码侧 (Wanting)   步骤2：静态分析 + LLM 通读，得到"代码里的条件分支/限制"区域
   ├─ 论文侧 (Zhaopeng)  步骤1/3a：从论文找机制与声明，再到源码里定位
   ├─ 验证 3b            代码里的每条限制，论文/README/docstring 有没有写
   └─ 步骤 4             去重、分类、priority、witness 提示 → limitations_for_tests.json（Finding）
                                         │
                                         ▼
测试侧 (Shanghao, checklimits)
   ├─ 环境预检（ENV.json）→ 按需 provision（CPU torch、逐个装依赖）
   ├─ code agent 为每条可测 Finding 设计测试（GPU 代码用 CPU 替身，可带 sim_check 自检）
   ├─ harness 确定性复跑，核对 agent 声明的 oracle，给出 verdict + 档位 L0–L3 + 未排除的 defeater
   ├─ 不能测的 Finding：analysis lane（静态证据 → 正则探针 → LLM 读取），档位 A0–A2，不给 yes/no
   ├─ 没有代码的论文：paper-only 模式（引用必须逐字出现在 PDF；算术检查由 harness 计算），最高 A1
   └─ 输出：results/tests/<id>/、results/report/<id>/LIMITATIONS.md（与 Finding 一对一）
```

入口：`python -m pipeline e2e <id>`（先 `doctor` 预检；key、代理网卡、base_url 全走环境变量，经本地中继）。
对已冻结的步骤 4 输出用 `--no-run`；无代码论文用 `paper-only`。

## 3. 结果总览（7 篇有代码 + 1 篇纯论文）

| 论文 | Finding | 测了 | 测试结果 | 没测的：分析档位 |
|---|---|---|---|---|
| FlexPrefill | 65 | 29 | yes 29（L1 16 / L2 7 / L3 6） | A2 15 / A1 18 / A0 3 |
| NNSmith | 38 | 22 | yes 20，inconclusive 2 | A2 5 / A1 8 / A0 3 |
| InfiniGen | 31 | 19 | yes 15，inconclusive 4 | A2 9 / A1 1 / A0 2 |
| MInference | 73 | 37 | yes 27，inconclusive 10 | A2 17 / A1 9 / A0 10 |
| SparTA | 82 | 2 | yes 2（79 条无代码位置） | A2 49 / A1 20 / A0 11 |
| FlexPosit | 41 | 12 | yes 8，其余 inconclusive/invalid | A2 19 / A1 3 / A0 7 |
| QoServe | 50 | 9 | yes 9 | A2 32 / A1 3 / A0 6 |
| Tessera（无代码） | 10 候选 | 0 | — | A1 10（另 2 条因引用对不上被丢弃） |

合计约 390 条 Finding，其中 130 条左右经过真实代码测试。

## 4. 各论文发现的 limitation（摘要）

**分类共性**：绝大多数是"代码里有、论文没写"（`undisclosed`），其次是实现与论文不一致（`impl_deviates`）和未实现（`not_implemented`）。典型类型有四种：输入被拒绝、改变执行路径、状态/随机性影响、硬编码的规模或配置。

**FlexPrefill**（稀疏注意力）
- GQA 要求 q 头数是 kv 头数的整数倍，否则直接断言失败（F003，L3）。
- 要求 q/k 序列长度相同、`head_dim ∈ {16,32,64,128}`、batch 大小为 1（F013/F014/F052，L3）。
- 序列短于约两个 block 时静默退回 flash attention，稀疏机制不起作用（F026，L3）。
- 补丁入口对非 `LlamaForCausalLM` 模型直接断言失败（F001）。

**NNSmith**（DNN 模糊测试）
- 对每个节点以 `constrain_prob` 随机跳过引导约束，机制是概率性的，论文表述更确定（F035）。
- 内存限制约束加入后，若求解结果不是 sat 就直接断言中止（F004）。
- 乘法位宽达到 `ARITH_MAX_WIDTH` 后不再对齐，会改变求解行为（F010）。
- 环境变量（如 `NNSMITH_GRES`、`NNSMITH_FLOPS_LIM=off`）会悄悄改变生成与接受规则（F001/F011）。

**InfiniGen**（KV cache 预取）
- 预取路径取决于设备类型是否为 MIXED；`compress_cache` 与 `attn_sparsity<1` 组合未实现（F002/F005）。
- 只有 `layer_id > 1` 的层才启用部分权重推测，第 0、1 层及首尾层不走 InfiniGen 路径（F009/F012/F027）。

**MInference**（动态稀疏注意力）
- 多个内核对 `head_dim`、q/k/v 形状有硬断言（`Lk ∈ {16,32,64,128}`、四维、三者同形；F011/F013/F015/F016，L2–L3）。
- 不在列表内的 head_dim 会被补零到 2 的幂再进内核（F037）。

**SparTA**（稀疏张量编译）
- 覆盖算法的选择取决于调用者给的稀疏模式和块价格（F001）。
- `wbc_matmul` 只支持单一块尺寸，多尺寸时失败（F002）。
- 82 条里绝大部分是论文侧描述，没有代码位置，只能给分析意见。

**FlexPosit**（Posit 量化）
- 每列 scale 超出 [-16, 15] 就无法写入 RTL 的 5 位字段（F004）。
- `nsize` 必须在 [2,16]，精度上限被硬性限制（F005）。
- 权重必须恰好是 Posit 值，否则编码报错（F003）。
- 敏感度文件与层名对不上时整个量化中止（F002）。
- 4 条 `invalid` 的 Finding 还没有查原因。

**QoServe**（SLO 调度）
- 非 0 tier 的 TBT 截止时间改用另一个阈值，实际行为随随机分配的 tier 变化（F004，L3）。
- 空闲 KV 块低于 1000 时 prefill 搜索空间被切换（F005，L3）。
- slack ≤ 0 时跳过二分搜索，直接返回最小值 128（F006，L3）。
- tier ≥ 1 的 ttft 截止时间要扣除预测的 decode 时间，依赖输出长度预测（F007，L3）。

**Tessera**（OSDI 2026，无代码，只给论文阅读意见，均为 A1）
- 头条的 20%–33% 提升是对阿里内部 Megatron-LM 分支的比较，公开可比的只有 256 卡的结果（P001）。
- 生产证据只覆盖 Qwen3 系列、Hopper/RoCE、私有数据；其他模型只在 256 卡测过（P002）。
- 分区器优化的是最大边代理目标，不是完整流水线关键路径；搜索范围限于串行基线附近（P005）。
- DBO 的单独验证只有 Qwen3-Next-M、256 卡、4K 序列（P006）。
- 两周生产轨迹里的两次提升归因于 Static Planner / DBO，没有受控 A/B（P007）。
- 共优化实验用均匀 token 分布的 mock router 并关闭 DBO，去掉了设计所针对的路由随机性（P009）。
- "零数值偏差、无质量回退"只有一次确定性模式的位一致 loss，没有收敛曲线和多种子结果（P010）。

## 5. 已知限制（交付时必须说明）

1. 步骤 4 重跑**不可复现**（SparTA 82→100，FlexPosit 也变过），原因未查。对已有结果必须用 `--no-run`。
2. 所有档位未校准，没有人工核对；A2 只表示"找到的文本与读法一致"。
3. GPU 替身的 `sim_check` 只在 FlexPrefill F07 上验证过；没有符号执行引擎。
4. 测试结果偏向"可达的条件分支 + 断言/路径变化"；对性能、精度类 limitation，测试几乎覆盖不到。
5. 大量 Finding（SparTA 79 条等）只有分析意见，没有测试。
6. 评审标签来自盲 LLM 评审，不是人工。

## 6. 建议的下一步

1. 查步骤 4 为什么不可复现。
2. 抽 20 条 A0/A2 做人工核对，得到第一批粗略的校准数据。
3. 查 FlexPosit 的 4 条 `invalid`。
4. 让 agent 在新的 GPU Finding 上写真正的 `sim_check`，验证这条链路。
