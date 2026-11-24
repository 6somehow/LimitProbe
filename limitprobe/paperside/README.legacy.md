# PaperProbe：论文驱动的候选测试规格

**2026-11-04 新工作流：** 根据团队最新分工，Zhaopeng 的论文侧 limitation 提取和论文→代码核验已开始实现，覆盖 proposal 的 SparTA、MInference、InfiniGen，以及 Teams 新增的 NNSmith。入口、九张研究草稿和真实运行记录见 [Zhaopeng 工作目录](workstreams/zhaopeng/README.md)。它使用独立 catalog 和命令，不改变下面的旧生成实验；来源检查与独立人评、真实执行分开记录。

PaperProbe 在人工冻结的组件范围内，将论文 PDF 与固定版本的官方代码转成带页码、代码行号和版本证据的候选测试规格，供 CS6223 团队验证论文机制与实现条件之间的关系。当前核心是静态生成与独立人评：具体输入、前置条件、观察目标和拟议 Oracle 都会保存；实际输入绑定、路径触达和 Oracle 语义仍需验证。它尚未运行目标软件，也没有已确认的 bug 或动态覆盖结果。

已采集 10 篇论文、选入 5 个开发案例：MInference、SparTA、InfiniGen、ALEX、FlashAttention-2。每份 PDF 的 SHA256 与每个选入仓库的 commit 已固定。选择依据、论文与代码版本差异见 [论文选择](docs/paper-selection.zh.md)，机器可读来源见 [catalog](data/catalog/papers.json)。这 5 个案例用于开发和 pilot；不能将它们称为未见过的 held-out 集，也不能据此声称跨领域通用性。

## 安装与数据验收

需要 Python ≥3.10、Git；Python 依赖为 `pypdf`，其余模块使用标准库。GPU、模型权重和目标仓库运行时依赖不属于静态核心的安装要求。

```sh
cd paperside
bash scripts/bootstrap.sh
.venv/bin/python -m paperprobe doctor
.venv/bin/python -m paperprobe catalog
.venv/bin/python scripts/acquire_papers.py --verify-only
.venv/bin/python -m unittest discover -s tests -p test_catalog.py -v
```

若换到其他机器，从项目根目录执行命令即可。本地已下载的 10 篇 PDF 和 5 个仓库验收通过；精确状态见 [实施审计](docs/implementation-audit.zh.md)。离线源码副本若未包含大文件，catalog 集成测试会显示 `skip`；这不等于数据验收通过。需要重新获取时执行：

```sh
.venv/bin/python scripts/acquire_papers.py
```

脚本使用公开论文与官方仓库，不读取 issue 作为发现线索；重跑会检查已固定的文件和 commit，不自动更新目标源码。无法安装环境时，本机可用 bundled Python 运行 `PYTHONPATH=src <python> -m paperprobe`；对应路径为 `python3`。

## 跑通四个模块

```sh
.venv/bin/python -m paperprobe prepare --all
.venv/bin/python -m paperprobe run --backend heuristic --output runs/demo
```

`prepare --all` 提取 10 篇论文全文，并静态扫描 5 个选入仓库。主实验先由人冻结每篇论文对应的组件范围，再在范围内自动提取代码条件、生成候选；这是限定组件的 guided synthesis / bounded component discovery，组件选择本身有人工成本。当前仓库可能含后续算法和辅助代码，不能将全仓库扫描池直接当作原论文机制，或声称已实现 whole-repository 自动发现。

`run` 对选入案例运行三种方法：`full` 使用论文证据与代码条件；`code_only` 使用同一代码条件池；`direct` 使用论文与代码做直接生成。当前冻结配置为每个 paper/method 最多 **3 个候选**，三种方法共享固定 model、instruction 与组件范围。范围见 [组件清单](configs/discovery-scopes.json)，扫描盲区、条件合法域和人工领域先验见 [扫描审计](docs/scan-audit.zh.md)。

代码池先取每个文件一条条件，再补充其他条件，以减少单文件占满上下文；每篇论文先按 Full 的较长 prompt 在 16,000 字符上限内冻结代码和论文证据，再让 Direct 复用同样材料、Code-only 复用同样代码。条件附带邻近源码和未验证适用性的 contract 候选；它们不是已经确认的合法输入域。源码扫描不是完整程序的语义分析，PDF 抽取的公式、表格和 scope 仍需核对原文。

已实际完成 10 篇论文、202 页的提取和 5 个组件范围的扫描：730 条代码条件、0 个扫描错误，1,220 份邻近源码附件的引用与 hash 均匹配。这些数字是抽取与来源检查结果，不是算法覆盖、可运行测试或 bug 数。

| 模块 | 输入与产物 | 结果的含义 |
| --- | --- | --- |
| Paper Profiling | PDF → `data/processed/<id>/pages.json`、`profile.json`、`paper.txt` | 可回查原文的机制证据；scope 待人工确认 |
| Paper–Code Alignment | 固定仓库 → `scan.json`；候选附带代码和论文证据 | 自动检索的潜在关联；不证明路径触达 |
| Candidate Generation | 条件、证据 → `runs/<id>/results.json` | 具体输入、策略、拟观察行为与拟议 Oracle |
| Feasibility Checks | 候选 → 各候选 `checks` 字段 | 版本、引文、schema、边界关系等机械检查；不是执行或语义证明 |

每次运行还输出 `contexts/`、`report.md`、`report.html`。失败、弃权和零输出任务保留在任务列表和评价分母中。`static_status=passed` 与 `execution_status=not_run` 可以同时出现：前者只表示记录的机械检查通过。

`heuristic` 使用确定性模板，仅用于流程演示和回归检查；其三种方法不能充当真实 LLM baseline 的比较结果。

## 模型调用、缓存与重放

模型 backend 调用本机已认证的 Codex CLI。官方非交互文档确认 `--json` 提供 JSONL 事件、`--output-schema` 约束最终 JSON、`--ignore-user-config` 忽略用户配置。实现以只读 sandbox 在临时目录中提供冻结上下文，并拒收包含工具调用的响应。[Codex 非交互文档](https://learn.chatgpt.com/docs/non-interactive-mode)

当前主实验 provider 显式请求 `gpt-5.6-sol`，采用所有方法相同的紧凑无工具 instruction。16,000 字符是每篇论文冻结上下文的上限；实际模型调用按方法把 5 篇论文放入同一 batch。因此使用 **3 次共享 CLI invocation** 产生 **15 个 paper/method 记录**，不是 15 次独立生成。相同 batch 的论文输出彼此依赖；本轮只做描述性开发 pilot，不作统计显著性或泛化结论。`provenance.json` 保存 requested model、instruction hash 与 CLI 版本；请求名称不能证明服务端实际部署细节。

```sh
.venv/bin/python -m paperprobe run --backend codex --output runs/codex-main
.venv/bin/python -m paperprobe audit --run runs/codex-main
.venv/bin/python -m paperprobe run --backend replay --replay-from runs/codex-main --output runs/replay
```

**真实主模型运行已完成，人评尚未开始。** `runs/codex-main` 保存了 3 个成功共享调用、15 个完成任务记录、43 个原始候选：Full 13、Code-only 15、Direct 15。所有候选机械检查通过、执行状态均为 `not_run`；数量和来源匹配不能说明方法优劣。主调用已知输入 81,141、输出 18,135，总计 **99,276 token**；三个 batch 的 wall time 合计 892.309 秒。

各次 smoke 与主运行分开保存。初次继承 app 模型配置的调用被服务器拒绝，所有尝试保留在账本；它不是主运行失败任务。后续 smoke 只验证调用通路，不计入三种方法的研究结果。

`audit` 保存 `experiment-audit.json/.md`，核对原始响应、prompt、provenance、候选上限、任务分母和共享资源计量。当前主运行审计为 pass；这表示记录与材料一致，不表示候选语义正确。`runs/replay` 已重放 15 个任务和 43 个候选，候选及检查内容与原运行一致、模型新调用数为 0；原目录的 cache resume 也未新增调用。证据见 `runs/replay/replay-verification.json`；重放不新增生成样本。

主实验请求保存在 `runs/codex-main/model/batches/<method>/attempt-1/`：`prompt.txt`、`model-instructions.txt`、`response-schema.json`、`events.jsonl`、`stderr.log`；成功后保存 `response.json` 与 `provenance.json`。`results.json` 的 `metadata.batches` 记录每次共享调用的 token 与 wall time，**每个方法只计一次**；不要再把 5 个 paper task 的 duration 或 usage 相加。模型调用预算记录在 `runs/model-budget.json`。计数单位是 **Codex CLI invocation**，一次 invocation 内部的 HTTP 请求数不可由此确定。成功事件中有 `usage` 时记录输入、缓存输入与输出 token；失败且缺少 usage 时保留预算预留值，其实际消耗未知。`charged_tokens` 可能混合已知用量与预留值，不能直接称为实际 token 花费或美元成本；预算预留也不是服务端输出 token 硬上限。

相同 output 目录中的完成与失败任务均使用已有记录，**失败默认不自动重试**；未完成的 batch 尝试也会保留。恢复与 `replay` 都检查冻结的 protocol、配置、组件范围、实现与 prepared source hash、PDF hash 和干净的固定仓库 commit，版本不一致会拒绝。`replay` 重放原候选并重新机械校验，不发起模型调用；它不是独立随机重复，也不能作为新增研究样本。改变 source、方法、配置或 backend 应使用新的运行目录，并重新冻结实验设置。

`runs/preflight-context-budget/` 保存了初始 12,000 字符预算不足的预检：在生成前终止，模型调用数为 0；之后上限提升到 16,000 字符。预检不是失败模型调用，也没有研究候选结果。

## 独立人评与本地页面

```sh
.venv/bin/python -m paperprobe review-export --run runs/codex-main --output runs/codex-main/review
.venv/bin/python -m paperprobe serve --review runs/codex-main/review --port 8765
```

人审包包含匿名排序的候选与证据、空白评分表、浏览器页面和单独的来源映射。实验管理员保存 `review/private/blinding-map.json`；两位审查者独立查看匿名页面，填写自己的 reviewer ID，并分别导出 CSV 或 JSON。代码与全文仍需让审查者访问，内容结构可能使方法被推测出来，因此匿名性有局限。

页面先展示候选摘要与评分，完整证据和元数据默认折叠。公共范围状态已屏蔽显式的 `code_only` 方法提示，原始运行结果保持不变；自由文本和证据数量仍可能暗示方法。

最终主页面已在本机浏览器实际检查：43 个候选、258 个评分控件，已填写数量为 0；摘要与三列评分可见，完整原文与来源上下文折叠保留。PDF 与引用源码入口均返回正确内容，byte/hash 与本地来源完全一致；验收记录见 [ui-qa.json](runs/validation/ui-qa.json)。页面验收没有写入人类评分。

`serve` 仅绑定 `127.0.0.1`，访问 `http://127.0.0.1:8765/`。页面的全文和代码链接会改成本机只读资源路由；代码入口只列出匿名候选引用的文本源码文件，不提供目录浏览、private 映射或写入评分接口。评分草稿和导出继续由浏览器本地处理。

```sh
.venv/bin/python -m paperprobe evaluate --run runs/codex-main --reviews runs/codex-main/reviewer-a.csv runs/codex-main/reviewer-b.csv --output runs/codex-main/evaluation
```

六项评分为 scope、代码关联、输入具体性、策略合理性、观察清晰度及 Oracle 设计，值只能是 `yes/no/unknown`；空白表示未审。前五项共同定义候选规格是否合格，Oracle 设计单列。两名独立审查者不足时保持 pending；分歧保留 conflict；未知不会自动变成 no。系统不替人填写。详见 [人评指南](docs/review-guide.zh.md)。

汇总保存 `evaluation.json/.md/.html`，保留零输出任务、失败任务和未决评分，按相同任务计算方法配对差值。未决情况下的上下界不是置信区间；输入 15、16、17 也不是三个独立研究样本。当前主运行的 43 个匿名候选已导出，人评记录数为 0，状态 `not_started`，`human_conclusions_available=false`；尚不能宣布方法优劣。

## 验证与后续研究

```sh
.venv/bin/python -m unittest discover -s tests -v
```

原始生成工作流首次交付时，全量测试已真实通过：131 项、无 skip；包含最终审查页和匿名数据处理的回归检查。新增论文 limitation 模块后，2026-11-04 的全量 146 项也已通过；最新验收见 Zhaopeng 工作目录。旧模型、重放及页面验收的证据见实施审计。

[实施审计](docs/implementation-audit.zh.md) 将需求、证据文件、真实验证与未完成项逐项对应。可选下一阶段是挑选候选、由团队实现最小适配器、记录实际触达与语义结果；这需要单独报告人工适配成本。当前静态核心的产物不能改名为完整 fuzzing campaign 或复现论文性能结果。

课程 final report 的结论与正文由团队根据实验记录独立完成；本仓库不生成 final paper 或伪造人评结果。
