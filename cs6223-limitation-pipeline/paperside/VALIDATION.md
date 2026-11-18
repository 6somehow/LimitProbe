# Z3首批交接验收（2026-11-16）

实际读取Teams两个契约附件，并在Shanghao `1753dab` 的真实代码上调用loader、分类器、outcome_support和报告库；未运行target、agent、envcheck或harness。

- FlexPrefill21条、NNSmith6条原负项完整triage；每篇1条详解，原三类判断与v1/v2包未改写。
- 2条原生0.2.0契约fixture成功加载，paper来源、真实代码位置、论文引用与固定commit匹配；函数调用与逐层参数由AST核对。
- 实际消费者均生成0个Region，分类no_code_location，因为adapter拒绝paper来源；旁表拟议Region是合法schema但当前效果检查不支持other/suspicious。
- 每例报告status=not_run、verdict/level=null、calibrated=false，报告与输入1:1，不包含虚构观测或置信档位。
- 完整论文侧回归：240项，238通过、2个外部资产相关跳过；其中13项Z3回归检查覆盖候选完整性、错误标签、虚构运行结果、来源片段和重要语义边界。
- 原PDF hash和固定Git源码均验证。新Z3原文片段按当前pypdf提取，旧claim原文保留为archived_claim_evidence；不同提取版本的数学排版不混作新原文。

入口详情见docs/z3-two-paper-cases.md。以下为前序接口/交付历史记录，不代表Z3已执行目标。

# 0.2.0 接口适配验收（2026-11-16）

基于 main `9fce6e01de09cc1940df9ebd190acd7284ddcb96`，在独立工作树和新虚拟环境安装 `paperside[team,vision,dev]`。仅修改论文侧，未更改共享 schema、codeside 或历史 v1 包。

| 检查 | 结果 |
|---|---|
| 原有测试（加入本轮测试前单独运行） | 219项：217通过、2个外部资产相关跳过 |
| 最终论文侧完整测试 | 227项：225通过、2跳过；新增8项覆盖来源/兼容性/类型与严格消费者验收 |
| main共享测试 | 134通过、3跳过（1缺目标checkout、2缺可选openai） |
| Pi校验器 | 23通过 |
| 交接完整性默认检查 | 优先选两篇v2，另三篇按AST确认历史记录结构兼容；全部通过 |
| 实际消费者探针 | 8项中6通过、2项明确失败，不算通过 |
| `--strict-consumer` | 预期退出码4：仍有已知消费者失败；与结构校验成功区分 |

FlexPrefill 的 tau 已核对正式参数、下传调用和使用。NNSmith 的两条新Binding由论文Listing2的kw/kh，对照固定源码Pool2d的kernel_w_size/kernel_h_size、成员赋值及requires()约束得到；不从名字相似推断。PDF hash与源码commit均核对，逐字引文从原PDF提取。

两项消费者失败：

1. `tau == 0.1`：范围检查为in_scope，但main witness返回infeasible。该实现使用Fraction(float)，与其1/1000搜索网格存在十进制等值问题。
2. 不给整数输入域的 `kernel_w_size == 2`：main witness返回solved，但contrast为1.999，不是有效整数参数。旁表明确code_type，不能把此结果当作可执行测试。带显式有限整数输入域的正向fixture通过；这不冒充完整整数域支持。

案例及真实输出见 `docs/parameter-mapping-cases.md`、v2各包`consumer_cases.json`。`conformance.json`与原claim内容逐字保持，未重新调用模型或执行目标。适配映射规格是经来源审阅的fixture，不是新自动发现实验。

以下是历史v1验收记录，数字和源版本属于当时交付。

# 交接验收记录（2026-11-11）

本轮完成 MInference、InfiniGen、NNSmith 最终交接，五篇均已纳入默认离线验收。使用新建环境 `/tmp/cs6223-final-handoff-venv` 安装 `paperside[team,vision,dev]` 成功；本轮未调用模型 API，未执行目标系统。

| 检查 | 结果 |
|---|---|
| `python scripts/validate_delivery.py` | 五篇通过共享 schema、快照哈希、行为/claim/待办关联、证据引用、映射门控与实际 ScopeChecker 检查 |
| `python -m unittest discover -s tests -v` | 219 项：217 通过，2 项缺少外部 PDF/仓库而跳过 |
| `node --test tools/pi-mechanism-agent/*.test.mjs` | 23 通过 |
| 团队根目录 `python -m pytest -q -rs` | 108 通过，3 跳过：1 项缺少 FlexPrefill checkout，2 项缺可选 openai 依赖 |
| 完整本地 `validate_corpus.mjs` | 四篇后续运行共 46 机制、455 行，冻结 ID 与报告一一对应；固定 Git 内容与已读范围通过 |
| 完整本地 `validate_handoff_archive.py` | 后三篇原 PDF 文本、逐字引文、冻结 ID、固定 Git 源码、引用与完整 ZIP 一致性通过 |

后三篇完整资产验收摘要分别保存在各包的 `archive-acceptance.json`。摘要包含当次完整 ZIP SHA256；ZIP 留在维护者本地，没有提交 Git。摘要作为发布时生成的证书加入轻量包，记录在 `source-distribution.json.release_generated_files`，不冒充原 ZIP 内的文件。

| 论文 | 原生接口 claim / scope / eval / binding | 行为：已判断 / 待办 | 标量映射 / 入口导航 |
|---|---|---|---|
| SparTA | 204 / 26 / 29 / 26 | 199 / 7 | 0 / 26 |
| FlexPrefill | 104 / 16 / 23 / 24 | 96 / 8 | 1 tau / 23 |
| MInference | 139 / 23 / 22 / 24 | 108 / 33 | 0 / 24 |
| InfiniGen | 65 / 25 / 11 / 12 | 59 / 11 | 0 / 12 |
| NNSmith | 139 / 22 / 8 / 24 | 113 / 27 | 0 / 24 |

新增 13 项发布/篡改回归测试覆盖：发布白名单、凭证拒绝、哈希篡改、冻结行为漂移、缺失 claim/引用、非法判定、pending 非 null、观测混入 active eval、遗漏负项、路径逃逸。InfiniGen 8 条和 NNSmith 4 条基线/背景观测仅作为旁表，不传入 active eval。未闭合论文 claim 对应的负项不进入 `limitations.json`。

轻量 checkout 的源码检查使用包内片段，不重新获取 Git blobs；只有持有原始资产的完整检查才独立比对论文及固定源码。旧两包未另附冻结行为快照，轻量检查会说明其 manifest/claim ID 检查的限制。缺少资产而跳过不算来源验证通过。

MInference 的两个机制使用保留 Pi 读取的非流式收尾；NNSmith 有一次 binding 结构修正，详情见 HANDOFF 与各包记录。28 条传输异常的未返回用量及远端状态仍未知；摘要中的 token 不是完整账单。

Wanting 的 README、根 CLAUDE.md、codeside、schema 和共享测试均未修改。发布前检查本次文件未包含密钥、原始 API 日志、PDF、ZIP、node_modules 或大型 HTML。

这些检查确认接口与证据可追溯，不构成人工语义真值、运行缺陷确认或准确率评测。
