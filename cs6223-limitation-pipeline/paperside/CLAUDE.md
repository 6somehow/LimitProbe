# CLAUDE.md — Zhaopeng 论文侧

供接手本模块的 coding agent 使用。先读本文件，再读 [README.md](README.md)；需要命令和接口字段时查 [HANDOFF.md](HANDOFF.md)。不要把根目录代码侧的旧状态当作论文侧最新状态。

## 负责什么

CS6223 小组项目，输入为论文和对应仓库。Zhaopeng 负责步骤 1 论文语义拆解、步骤 3a 论文 → 代码静态核验。Wanting 负责代码侧发现和代码 → 论文核验；Shanghao 负责测试生成和执行。当前模块不运行目标系统。

问题是：论文承诺的机制行为，在指定源码路径和条件下是否实现。不要先读源码，再把论文要求改写成代码已有的行为。

## 固定的方法

1. 只给模型论文文字与原始页面图像，独立发现机制 k=2；两个请求互不看结果。
2. 合并别名、保留职责与父子关系，确定统一机制。
3. 每机制初次拆行为；另一请求不看初次清单，仅从相关原页独立列步骤。
4. 对账、补机制内遗漏、拆复合项、检查前提，冻结行为 ID 与论文证据。
5. 每机制一个 Pi coding-agent 会话，输入机制、原文、冻结行为及固定 commit 的仓库；自主搜索、读代码、追静态调用关系。
6. 模型语义复核，程序核对 ID、字段、来源与已读行范围；分别记录 `local_entry` 和 `artifact` 路径结果。
7. 组织差异候选、源码证据与论文接口，交给 Wanting。图见 README。

完成项仅三类：`supports` 支持、`deviates` 实现不符、`absent` 该路径未实现。`review_state=pending, verdict=null` 是未完成状态，不能强行判 absent，也不进入差异候选。没搜到名字不证明没有实现；需要检查路径、条件及等价实现。

## 目录与代码入口

| 目录或入口 | 用途 |
|---|---|
| `src/paperprobe/independent_discovery.py` | 论文侧两次独立发现与合并 |
| `src/paperprobe/mechanism_continuation.py` | 行为拆分、独立步骤和机制内对账 |
| `src/paperprobe/delivery.py` | 原文片段、接口 prompt、调用留档、消费者定位 |
| `tools/pi-mechanism-agent/prepare_corpus.py` | 固定仓库、符号与源码输入准备 |
| `tools/pi-mechanism-agent/run-adjudication.mjs` | Pi 工具探索与判断 |
| `tools/pi-mechanism-agent/conformance.mjs` | 判断记录的结构校验 |
| `scripts/run_complete_corpus.py` | 多论文编排；会调用模型，使用固定运行目录 |
| `scripts/build_paper_handoff.py`、`scripts/finalize_handoff.py` | 共享接口导出、映射门控与交接打包 |
| `scripts/validate_delivery.py` | 已入库两篇的离线消费者和快照检查 |
| `scripts/validate_corpus.mjs` | 完整本地运行的 ID、源码及用量验收 |
| `handoffs/paper-side-v1/<paper>/` | 对外的轻量交接结果 |

## 下一步

状态核对日期：2026-11-11。SparTA、FlexPrefill 已验收并入库；后三篇实际模型运行和本地初步导出均已结束，不要因旧 README 写着“仍运行”而重跑 API。

| 本地结果 | 机制 / 行为 | artifact 已判断 / 待办 | 接手动作 |
|---|---|---|---|
| MInference | 13 / 141 | 108 / 33 | 本地接口已修订；复查最终包并发布轻量版 |
| InfiniGen | 8 / 70 | 59 / 11 | 审核现有修订建议、应用后最终验收并发布 |
| NNSmith | 13 / 140 | 113 / 27 | 本地导出完成；审阅接口、最终验收并发布 |

当前发布分支 `zhaopeng/paper-side-v1`。本机完整开发工作区：`/Users/pp/Desktop/nus/cs6223/paper-guided-testing`；发布工作树：`/Users/pp/Desktop/nus/cs6223/paperside-publish-v1`。这些是维护者机器路径，另一台机器不可直接使用。

接手顺序：

1. 先确认所在 checkout 与 Git 状态；读取本地 `runs/team-complete-v1/parallel-summary.json`、`code-coverage-verification.json` 和每包 `validation.json`，与 README 对齐。
2. InfiniGen 已有 `runs/team-complete-v1/infinigen/review-adjustments.proposed.json`，尚待最后应用。若记录包含 `reported_observations`，以非激活观察单独保留，不能把基线/动机实验混进本系统评估。
3. NNSmith 的原始 binding proposal 有缺少 `line_end` 的结构错误，已有 `bindings-structure-repair-v1.raw.json` 修正及 `repair_corpus_bindings.py`。先核对本地修正脚本和缓存；直接跑旧 builder 会重读有意保留的原始错误。不要重复付费修正。
4. 在完整工作区做接口来源审阅，保留原输出，用 `review-adjustments.json` 记录修订。最终化、生成报告，再最终化一次，使 ZIP/索引包含报告。先阅读脚本参数与现有状态再执行。
5. 更新全篇验收与分发清单，再复制轻量 JSON、源码证据到发布工作树。发布 README 和 agent 状态同步更新；不得宣称 pending 已完成。
6. 后续再逐条处理 pending，以及人工语义评审和候选去重。没有人工 gold，不能声称模型审阅是人工验收或报告准确率。

本地恢复脚本与后期修正记录不一定已进入轻量分支；先核对差异再同步，不要假设新 clone 含全部原始运行。传输失败的未知 token 用量和远端状态保留在 `transport-uncertainty.json`，不能记作零消耗。

## 开发与验收规则

- 修改范围以 `paperside/` 为主。不改 Wanting 的 README、根 `CLAUDE.md`、`codeside/` 或共享 schema 来迁就论文侧输出；共享字段变更须团队协调。
- 不修改固定的目标仓库，不覆盖 gold、原始请求、返回或失败记录。更改输入、prompt、模型或预算后创建独立实验记录。
- `paper_side.json` 严格保留四数组接口。三类判断留在 `conformance.json`，不机械映射成共享五类 `Verification`。
- `mechanism_entry` 是入口导航，不是支持证明或标量映射。仅作者明确支持的数值域与确定标量映射可激活；实验点不是穷尽支持范围。当前消费者可能将文本域当作无约束，必须保留现有门控。
- 主仓库和依赖分别保留 repo/commit；引用须对应实际读过的代码。代码引用及结构检查不替代语义核验，也不证明运行缺陷。
- 使用 SoCLaaS `x-test-2` 路由，模型身份以返回为准。凭据从本机环境加载；不打印、不提交 key，不把认证 header 放进调用记录。
- 离线检查、安装、付费复跑的命令见 HANDOFF。重跑前判断是否已有缓存，不自动重新支付整篇调用。
- 提交使用用户 Git 身份及 `zhaopeng/` 分支，不使用 `codex/` 名称或 Codex coauthor。

交付完成的条件：共享接口能被实际消费者加载；行为 IDs 与冻结列表对齐；源码证据、修订及 pending 保留；轻量包哈希一致；README 数量与实际发布文件一致。源码支持、不符、未实现均是静态路径判断，目标运行与人工语义评审单独报告。
