# 论文侧交接操作说明

所有命令从 `paperside/` 目录运行。当前结果状态见 [README](README.md)，agent 开发规则见 [CLAUDE.md](CLAUDE.md)。

## 先做离线检查

需要 Python >=3.10、Git；Node.js >=20 用于 Pi 测试和运行。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[team,vision,dev]'
.venv/bin/python scripts/validate_delivery.py
node --test tools/pi-mechanism-agent/*.test.mjs
```

以上检查不调用 API、不运行目标系统。`validate_delivery.py` 默认验收已发布的全部五篇。回归测试命令：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

缺少 PDF 或目标仓库时，部分测试会跳过；跳过不等于验证通过。已有验证环境和结果见 [VALIDATION.md](VALIDATION.md)。默认自动寻找上层团队项目，也可设置 `PAPERPROBE_TEAM_REPO` 指向含 `schema/`、`codeside/` 的共享项目根目录。

## 交给 Wanting

直接使用 `handoffs/paper-side-v1/<paper>/paper_side.json` 替换原先的论文 stub，不需要先重新抽取。

```bash
# 此段在团队项目根目录运行；其余 verify3b 参数沿用 Wanting 的运行配置。
python -m codeside.verify3b --help
```

在 Wanting 的完整命令中指定：

```text
--paper-side paperside/handoffs/paper-side-v1/sparta/paper_side.json
```

实际 `verify3b` 运行会调用模型。完整命令模板见包内 [RUN_WITH_WANTING.md](handoffs/paper-side-v1/sparta/RUN_WITH_WANTING.md)；其中 PDF 和源码路径须换成接手者本机路径，轻量仓库没有打包 PDF。

共享接口是 schema v0.1.0 的四个数组：`claims`、`scope`、`eval_points`、`bindings`。我们的三类源码判断保留在 `conformance.json`，不要改名后塞入共享 `Verification` 枚举。

| 需要追溯什么 | 文件 |
|---|---|
| 全部行为、主入口与 artifact 路径的判断 | `conformance.json` |
| 静态差异及模型归组 | `limitations.json`、`finding_candidates.json` |
| 实际读过的源码与仓库版本 | `source_reads.json`、`code_evidence_registry.json`、`repositories.json` |
| 论文范围的条件与单位解释 | `scope_interpretations.json` |
| 未闭合论文记录及停用映射 | `pending_records.json`、`inactive_bindings.json` |
| 接口修订依据、原始版本 | `review-adjustments.json`、`review-notes.json`、`paper_side.pre-final.json` |
| 消费者检查与分发文件哈希 | `validation.json`、`source-distribution.json` |

入口导航 `mechanism_entry` 只说明函数位置，不证明支持声明，也不是数值参数映射。当前只激活确定的标量映射及作者明确支持的数值域；文本范围、实验专用数值或不确定映射不能用于排除其他输入。SparTA 的已有代码侧条件仍返回 `unknown`；FlexPrefill 只有 `tau` 的标量映射，不能声称范围核对已全部完成。

## 需要重新生成时

通常先读已有结果。只有确实需要新实验时才运行下面步骤；它会下载资产并调用模型，产生 API 消耗。

```bash
npm ci --prefix tools/pi-mechanism-agent --ignore-scripts --no-audit --no-fund
.venv/bin/python scripts/prepare_team_paper_sources.py --team "${PAPERPROBE_TEAM_REPO:-..}"
# 先在本机 shell 安全加载 SOCLAAS_API_KEY；不把密钥写进仓库或日志。
.venv/bin/python scripts/run_complete_corpus.py --papers flexprefill minference infinigen nnsmith
```

SoCLaaS 使用 `x-test-2` 路由，实际模型标识以每次响应记录为准。固定输入见 [team-reviewed.json](workstreams/zhaopeng/team-reviewed.json) 和团队 `data/*/artifact.json`。

原始记录位于 `runs/team-complete-v1/`，导出位于 `handoffs/paper-side-v1/<paper>/`。输入或 prompt 改变时必须使用独立运行目录；当前入口使用固定目录，先修改并核对输出位置，不能直接把新条件混进已有缓存。SparTA 的专用历史脚本依赖本地归档，不是全新 checkout 的独立入口。

完整运行的来源验收由 `scripts/validate_corpus.mjs` 完成，需要原始调用记录、论文和固定源码，不能仅靠轻量仓库复现。源码行与 commit 对应、字段合法、行为 ID 完整，只证明记录可追溯，不证明模型判断正确。

## 本地资产与仓库资产

仓库保存代码、测试、配置、版本清单、PNG 流程图及已发布的轻量交接包。原 PDF、完整目标仓库、原始 API 日志、ZIP、大型 HTML 和 `node_modules` 不入库。密钥不属于交接包。

每包 `source-distribution.json` 列出保留和省略的文件。后三篇另附 `archive-acceptance.json`：记录完整本地包的原论文、固定 Git 源码、冻结 ID 和 ZIP 检查结果；轻量验收只校验这里保留的快照，不能替代原始资产检查。归档绝对路径是原始运行位置，不能当作另一台机器上的有效路径。当前维护者本地工作区和剩余任务见 [CLAUDE.md](CLAUDE.md#下一步)。

## 本轮交付的恢复记录

MInference 的 M05、M09 在流式连接失败后，复用 Pi 实际读过的源码和冻结行为，分别进行一次无新工具的非流式语义收尾；不是重新探索整个仓库。NNSmith 的 binding proposal 经过一次字段结构修正。全部原始失败保留；源码判断未由打包程序机械改写。

InfiniGen 的 8 条背景/基线观测和 NNSmith 的 4 条基线观测单独留在 `reported_observations.json`，不进入本系统的 active eval。各包的 `review-adjustments.json` 记录接口修订。

需要重查完整本地 ZIP 时，在持有原始运行和资产的工作区运行：

```bash
.venv/bin/python scripts/validate_handoff_archive.py \
  handoffs/paper-side-v1/minference handoffs/paper-side-v1/infinigen \
  handoffs/paper-side-v1/nnsmith --out runs/team-complete-v1/final-archive-acceptance.json
```

该命令不调用模型、不执行目标源码；它会读取论文、Git blobs 和 ZIP。验收摘要中的 token 仅为成功收到的用量，失败传输未返回的用量未知，不代表完整账单。
