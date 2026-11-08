# 代码侧任务清单（Wanting）

状态：`[x]` 已完成（本次前置准备），`[ ]` 待做。每个里程碑都写了验收标准。
执行顺序建议：M1 → M2a 与 M2b 并行 → M3 与 M4 并行 → M5 → M6。

步骤 2 有两条技术路线，都要做并对比：**A 静态分析（不用 LLM）** 和 **B LLM 抽取**，见 `docs/06_two_routes.md`。

## M0 前置准备（已完成）

- [x] 选定 pilot：FlexPrefill（官方仓库，commit 已固定）——`docs/04_pilot_flexprefill.md`
- [x] 代码侧相关工作与工具选型——`docs/01_related_work_codeside.md`
- [x] 共享 schema v0.1.0（pydantic + JSON Schema）——`schema/`、`docs/02_schema.md`
- [x] pilot 手工 gold：16 条区域、13 条代码侧 limitation、13 条 3b 草稿、7 条 finding 草稿——`data/pilot_flexprefill/`
- [x] 抽取器 v0（Python ast）+ 评估脚本 + CLI + 测试；pilot recall 16/16，10 条多余预测已分类
- [x] 3b 与步骤 4 的规格、prompt 模板——`docs/03_codeside_spec.md`、`docs/prompts/`
- [x] 开发数据集：SparTA、MInference、InfiniGen、NNSmith 的 artifact.json（固定 commit）+ `scripts/fetch_dataset.sh`——`docs/05_dataset.md`
- [x] 抽取器支持类方法、`self.method()` 调用、一层嵌套函数、`--package-root`；在四篇上完成首次运行
- [x] 纯 LLM 对照组（`codeside/llm_extractor.py`）：上下文构建、prompt、输出校验、可插拔客户端；`extract-llm` 和 `compare` 命令
- [x] 路线 B（`codeside/hybrid_extractor.py`）：A 出候选，LLM 只补调用边和漏报、不删除 A 的结果，结论由代码校验；`extract-hybrid`、`stability`、`scripts/run_routes.py`

## M1 和团队对齐（第 1 周，需要开会）

- [ ] 三人评审 schema，回答 `docs/02_schema.md` 里的 5 个待定问题，定为 v0.2.0
- [ ] 和 Zhaopeng 约定：步骤 1 对 FlexPrefill 的输出替换 `paper_side_stub.json`（字段与 stub 相同）
- [ ] 和 Shanghao 约定：Finding.witness_hint 的格式；把 F01–F07 交给他做第一次 CPU 执行确认
- [ ] 一起评审 `draft_verifications_3b.json` 和 `draft_findings.json`，评审后另存为 gold（不要覆盖草稿）

验收：schema v0.2.0 合入；三人都能用 `python -m codeside.cli validate` 校验自己的输出。

## M2a 路线 A：静态抽取器 v1（降噪 + 接入配置）

- [ ] **路径可行性剪枝**：调用被调函数时，把形参绑定到实参表达式；把被调函数的条件改写成调用方的名字；用 z3 判断"路径前缀 ∧ 条件"是否可满足，不可满足则丢弃（目标：去掉 6 条 decode 噪声）
- [ ] **冗余判断**：前缀蕴含该 assert 条件时标记 subsumed，不输出为 limitation（目标：去掉 `triton_bnhd_pool` 的 2 条）
- [ ] **内部不变量过滤**：条件只依赖内部计算值、与入口参数无数据依赖时降级（目标：去掉 `block_idx` 的 2 条）
- [ ] **配置接入**：从 Binding 读取配置键（如 `flex_prefill_min_budget`），在区域条件里标注配置依赖
- [ ] **调用解析**：包级导入、`self.method` 调用；动态分发走 LLM（`docs/prompts/dispatch_resolution.md`），候选边必须指向真实存在的定义
- [ ] **不早返回的模式切换**：分支体调用了机制相关函数（如 InfiniGen `if warmup: skew(...)`）时也产出区域
- [ ] **双分支分发 / 切换到另一种实现**：两个分支 return 不同实现（NNSmith GradSearch / SamplingSearch，MInference dilated / streaming）；需要 schema 增加 outcome（建议 `alternative`，见 `docs/02_schema.md` 问题 6）
- [ ] **`ClassName.method(self, ...)` 调用**与**继承**（子类没重写时到父类找）
- [ ] **构造函数属性**：条件依赖 `self.x` 时，分析 `__init__` 里 `self.x` 的赋值条件（如 NNSmith 的 `self.differentiable`）
- [ ] 每条规则都在 `tests/fixtures/` 加最小用例

验收：pilot 上 recall 保持 1.00，多余预测 ≤ 2；`pytest` 全部通过；四篇的首次运行结果（`docs/05_dataset.md`）里列出的缺口都被覆盖。

## M2b 路线 B：LLM 抽取

- [ ] 和团队确认模型 ID（当前用 `x-test-2`，经 SOCLAAS 的 OpenAI 兼容接口，key 放在 `.env`）
- [ ] 在 pilot 上跑 3 次，用 `compare` 和路线 A 对比；人工检查被拒绝的条目
- [ ] 上下文过长时的处理：按调用深度截断，或分函数多次调用再合并
- [ ] prompt 每改一版就记录版本号和改动原因；**不要对着 gold 反复调 prompt**
- [x] B-agent 变体（`codeside/agent_extractor.py`）：LLM 用只读工具自由探索整个 repo，已在 5 篇上各跑 3 次
- [x] 裁决 B 新增结果的质量（Claude subagent 盲审，见 `docs/06_two_routes.md`“B 的三种做法对比”）
- [x] B-sweep（`codeside/sweep_extractor.py`）+ 相关性复核（`codeside/relevance_filter.py`），5 篇各 3 次
- [x] 调用链去重（`codeside/dedup.py`）+ 合并 sweep 和 agent（`cli merge`），结果在 `out/routes_merged/`；盲审新样本有用 32%
- [ ] repo 里自带的基线方法代码（vertical-slash、FlexGen top-k、dilated、SnapKV）仍是主要噪声：需要论文侧告诉我们哪些是基线
- [ ] 人工标注确认 B 的最终输出（目前只有单个 Claude 审稿人，每轮 38–49 条）
- [ ] `mechanism_variant` 在 to-limitations 里默认被跳过；现在用 `--include-variants` 暂记为 path_change，需要团队决定是否加 `alternative` 结局
- [x] 最终的 B → 3b 端到端跑通五篇（`scripts/run_pipeline.py`，`docs/07_pipeline_b_3b.md`）；修了 scope_check 遇到非布尔条件崩溃的问题
- [ ] （可选）路线 C 混合：A 出候选，LLM 只补 A 做不到的部分

验收：pilot 和四篇上都有 A、B 两行结果（recall、extra、cond_exact、幻觉率、3 次的波动、成本）。

## M3 开发数据集的 gold 与评估（四篇）

- [ ] 和团队确认每篇的入口函数（`data/<id>/artifact.json` 里是候选），必要时补充
- [ ] 每篇由领域负责人 + 另一人独立标注 gold 区域表和代码侧 limitation，算一致性（建议顺序：NNSmith（全 CPU，最快）→ MInference → InfiniGen → SparTA）
- [ ] 跟进 `docs/05_dataset.md` 里的候选观察：SparTA 的传播桩函数交给 Zhaopeng 做 3a；NNSmith 的非可微退化做 3b
- [ ] 若有 NNSmith 对话里的结论，整理进 `data/nnsmith/notes.md`
- [ ] 每次改规则或 prompt 后，在四篇 + pilot 上重跑两条路线的 `compare`，记录变化
- [ ] 约定 1–2 篇 held-out artifact（最后只跑一次、不调规则），用来报告泛化

验收：四篇都有 gold；每篇的 recall 和多余预测写入 `docs/05_dataset.md`；held-out 名单确定。

## M4 步骤 3b 实现

- [x] 文本准备：论文 PDF → 分节文本（改用 PyMuPDF，不需要 sudo，能处理双栏），README、docstring、注释建索引，每段带来源和位置
- [x] 检索：用条件里的名字、Binding 映射的论文术语、条件里的数值召回候选段落
- [x] LLM 判断（`codeside/verify3b.py`，由 `docs/prompts/3b_code_to_paper.md` 演化），**代码里校验 quote 逐字存在**
- [x] scope 判断：Binding 映射 + ScopeItem 区间 / 集合运算（必要时 z3），确定性实现
- [x] 评测覆盖判断：EvalPoint 是否满足区域条件
- [x] 输出 Verification(code_to_paper)
- [ ] 与 M1 评审后的 gold 对比（gold 还不存在；目前只和未评审草稿对比过）

验收：pilot 上与 gold 3b 的 result 一致率、scope_status 一致率，写入 `docs/06_3b_eval.md`。

## M5 步骤 4 整合

- [ ] 读入论文侧 Limitation + 3a、代码侧 Limitation + 3b
- [ ] 去重合并（同一 Region 或等价条件）
- [ ] 按 `docs/03_codeside_spec.md` 的决策表分类，设置 L2、priority、confidence
- [ ] witness_hint：在 scope ∩ 区域条件里求具体值（边界两侧各一个点）
- [ ] 输出 Finding，交给 Shanghao

验收：pilot 上重新生成的 Finding 与评审后的 gold 一致；Shanghao 能直接用 witness_hint 写测试。

## M6 评估（与团队一起）

- [ ] 区域表 precision / recall（对 gold），**路线 A、B（及 C）并列**，按 artifact 和结局类型分开
- [ ] 下游可用性：两条路线产出的条件，有多少能直接用于 3b 的 scope 求交和 witness 求解
- [ ] 与 Shanghao 做动态 trace 对照：随机 + 边界输入在 CPU 上运行，记录实际分支，对比区域表（区域 recall、区域 precision、边界准确率）
- [ ] 步骤 4 分类的混淆矩阵
- [ ] 按 L1 / L2 / L3 分开汇总
