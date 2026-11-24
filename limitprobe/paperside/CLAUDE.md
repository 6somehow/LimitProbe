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
| `scripts/validate_delivery.py` | 当前及历史交接包的离线消费者和快照检查 |
| `scripts/validate_corpus.mjs` | 完整本地运行的 ID、源码及用量验收 |
| `handoffs/paper-side-v1/<paper>/` | 对外的轻量交接结果 |

## 最新Z3交接：2026-11-16

当前分支 `zhaopeng/paper-side-z3`，在原0.2.0适配工作树上开发。先读 `docs/z3-two-paper-cases.md`，再看 `handoffs/z3-v1/{flexprefill,nnsmith}/`。

- Teams的CONTRACT_TEST_REPORT.md、REQUESTS_TO_STEP4.md已实际读取；消费者代码固定为Shanghao `1753dab2dda1c088f0aeb0546a5d3755f8ebf947`。相关文件hash在consumer_contract_check.json。
- 21+6条原负项逐一triage，各展开一例。不是27个独立bug，也不是所有条目已有可执行输入。构造/分类来自经源码核对的模板，不是新模型自动发现。
- FlexPrefill M08-B05给出score_cover_topk精确位置与二进制有理数输入；论文“exceeds”和公式>=冲突、上游Q/K可实现性未解决，不得直接认定运行错误。
- NNSmith M08-B10给出search_one→GradSearch→grad_input_gen的ms/秒映射与零预算配方；不能用外层search(0)替代。实验调用return_list=True与固定search签名不符，是静态路径阻塞，不冒充已观测TypeError。
- 原生0.2.0 Finding/Limitations输入可读，origin仍paper、effect仍other、witness未知。不要为过门槛假改origin=code或给return/数值赋值贴reject/fallback。
- 实际adapter拒绝paper-origin生成Region，所以分类器在已给代码位置时仍返回no_code_location；旁表拟议Region也需要数值/返回协议oracle。两个report.json均not_run、verdict/level=null，1:1保留，不含置信评分。
- 下一步S4契约协调：接受paper位置的Region、消费effect_location与调用/参数上下文、增加自定义oracle。先解决论文解释与可达性再执行；目标环境、模型构造、试验和人工判断均未在本轮完成。
- `build_z3_handoff.py`生成案例；`probe_z3_consumer.py`只调用实际读取/分类/报告函数，不调用test/envcheck/run_agent；`validate_z3_handoff.py`核对来源、ID覆盖与未运行状态。
- 旧v1/v2交接包和原conformance均未覆盖；Z1/Z2的两个witness已知问题仍保留。

下面是上一轮0.2.0适配记录，以本节为当前优先事项。

## 最新接手状态：2026-11-16

当前基于 main `9fce6e01de09cc1940df9ebd190acd7284ddcb96`，开发分支 `zhaopeng/paper-side-schema02`。本次工作树是 `/Users/pp/Desktop/nus/cs6223/paperside-schema02`，另一台机器不可直接使用这些绝对路径。

- FlexPrefill 和 NNSmith 的 v2 包在 `handoffs/paper-side-v2/`，原生记录均为0.2.0；v1包完全保留。分别有1条tau映射、2条Pool2d核大小映射。
- `parameter_mappings.json` 保存正式参数、存储/使用、原文、类型、单位、所属函数；`consumer_cases.json` 是真实下游接口探针，不是新Finding或目标测试。先看 `docs/parameter-mapping-cases.md`。
- 8个探针：6通过，2保留为下游失败。使用 `--strict-consumer` 时退出码4，不把完整性成功冒充消费者全部通过。main witness把十进制float转成Fraction，导致 `tau == 0.1` 被误判无解；另外schema区间序列化成float，导致整数核宽的contrast出现1.999。不能把这些返回直接当成可执行测试。
- 整数正向fixture使用显式有限输入域 `{0,1,2,3}`，这是测试输入约束，不是论文全集或真实调用前缀。完整整数域和函数帧隔离尚未由共享Binding表达。
- 本次映射是源文/源码辅助审阅的规格，不是新自动抽取模型运行；适配器 `scripts/adapt_schema02.py` 核验PDF hash、仓库commit、正式参数、赋值/使用AST后生成包。
- `scripts/validate_delivery.py` 默认优先v2，其余选历史v1。历史schema变化用AST比较共享记录定义（不执行旧schema），不是跳过哈希。旧三篇没有被宣称迁移为0.2.0。
- 下一步先共同确认类型/函数上下文的下游契约，处理两个witness问题，再对真实step4输入联调；不要重跑五篇论文模型。Z3首批可测性提示已补（见上节）；其他条目、新论文P及人工复核仍待进行。
- 未改共享schema或codeside。共享consumer变化需团队确认；不能把整数类型问题藏进浮点域，也不能把gamma开区间改成闭区间。

以下为v1交付历史；其中“下一步”描述的是上一轮状态，以本节为当前工作优先级。

## 下一步

状态核对日期：2026-11-11。五篇交接包均已验收、发布到 `zhaopeng/paper-side-v1`。这指接口/证据/归档验收；人工语义评审和目标运行仍未完成。不要因旧文档或原始失败记录而重新跑整篇 API。

| 已入库结果 | 机制 / 行为 | artifact 已判断 / 待办 | 原生接口 claim / scope / eval / binding |
|---|---|---|---|
| SparTA | 20 / 206 | 199 / 7 | 204 / 26 / 29 / 26 |
| FlexPrefill | 12 / 104 | 96 / 8 | 104 / 16 / 23 / 24 |
| MInference | 13 / 141 | 108 / 33 | 139 / 23 / 22 / 24 |
| InfiniGen | 8 / 70 | 59 / 11 | 65 / 25 / 11 / 12 |
| NNSmith | 13 / 140 | 113 / 27 | 139 / 22 / 8 / 24 |

共 661 行、575 已判断、86 待办。后三篇均有 `frozen-behaviors.json` 与 `mechanisms.json`，以及完整本地包的 `archive-acceptance.json`；旧两包的轻量离线检查使用 manifest/claim 关联，明确报告未独立提供冻结清单的限制。

接手顺序：

1. 核对所在分支与 Git 状态，按 HANDOFF 安装并运行 `scripts/validate_delivery.py`，应发现并通过五篇；无需 API。
2. Wanting 整合时读取各包 `paper_side.json`，通过行为 ID/claim_id 联接 `conformance.json`、`limitations.json` 和源码 registry。先做候选审阅及父子/重复机制去重，再交给测试侧。
3. 源码待办在 conformance 的两种 scope 中分别记录；论文引文未闭合的条目在 `pending_records.json`。逐条补证，不把两个列表机械相加或当作缺陷。
4. `limitations.json` 只包含有论文 claim、已完成的不符/未实现项。InfiniGen 的 M08-A06 有代码侧不符判断，但论文 claim 未闭合，故只留 conformance，未导出为可整合 limitation。先处理其论文依据，再决定是否新增候选。
5. 若修改方法或 prompt，另建实验身份/输出目录，不覆盖已有记录。现有编排入口使用固定路径，先修改并核对路径再启动；小范围验证后再扩大。

已完成的修订不要再重做：InfiniGen 的实验值/基线/耗时等没有被当作全局输入域；8 条背景/基线观测另存。NNSmith 的样例 dtype、平台条件、约21h复现时间已修订，4 条基线评估另存，最后保留22scope/8eval。MInference 的上下文标签、默认版本及实验配置拼接问题已按来源修订。原始审阅提案中的 `not_applied` 描述的是审阅当时；应用状态以每包 `validation.json.interface_review` 为准。

恢复历史：MInference M05/M09 复用实际 Pi 源码读取，进行非流式语义收尾（无新工具）；NNSmith 已完成一次 binding 字段结构修正。原始失败仍保留，不代表任务还在运行。不要直接重跑旧 builder 或导入历史 `close_corpus_nonstream.py`：后者是针对当次运行的可执行恢复脚本，导入也可能触发操作。

完整资产在维护者本机 `/Users/pp/Desktop/nus/cs6223/paper-guided-testing`；发布工作树为 `/Users/pp/Desktop/nus/cs6223/paperside-publish-v1`。另一台机器不具备这些路径，须下载固定资产或向维护者取得归档。原始 API 日志和完整 ZIP 不在 Git；每包分发清单记录省略项。28条传输异常的未知用量/远端状态留在 `transport-uncertainty.json`，不能算零消耗。

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
