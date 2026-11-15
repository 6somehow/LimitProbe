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
