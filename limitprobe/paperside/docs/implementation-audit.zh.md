# 实施验收记录

更新时间：2026-10-01。本文区分源码存在、真实运行通过、以及尚无证据三种状态；`unknown` 不是失败，也不是已通过。集成负责人应在产生可回查日志后更新状态，不得用源代码或 mocked 测试代替真实模型运行。

## 需求与证据

| 需求 | 证明文件或记录 | 验收状态 |
| --- | --- | --- |
| 10 篇候选论文，5 个选入官方仓库 | `data/catalog/papers.json`、`data/papers/*/paper.pdf`、`data/repos/*`、`docs/paper-selection.zh.md` | **PASS**：10/5、唯一 ID、来源 URL、PDF hash/页数、5 个 HEAD 和 shallow 属性均真实检查通过 |
| 固定版本、采集可重复 | `scripts/acquire_papers.py`；catalog 的 `pdf_sha256`、`repository_commit`、版本说明 | **PASS**：`--verify-only` 已通过；ALEX 的原 PDF 403 与采用公开 arXiv v2 已记录，不宣称该扩展报告是会议 PDF |
| 模块 1：Paper Profiling | `src/paperprobe/papers.py`；`data/processed/index.json`、各案例 `pages.json/profile.json/paper.txt` | **PASS**：10 篇、202 页实际提取完成；原文证据可回查，scope 保持 pending |
| 模块 2：Paper–Code Alignment | `scanner.py`、`alignment.py`；5 个 `scan.json`、运行 `contexts/` | **抽取 PASS；语义待审**：组件范围扫描 730 条条件、0 个 errors；1,220 个邻近源码附件 quote/hash exact-match。关联、适用 contract 与可触达仍未证明 |
| 模块 3：Candidate Generation | `generation.py`、`pipeline.py`、`batching.py`、`providers.py`；`runs/codex-main/results.json` | **PASS（真实生成）**：3 个成功共享调用、15 个完成任务、43 个原始候选；Full 13、Code-only 15、Direct 15。不能以原始数量判断质量或方法胜负 |
| 模块 4：Feasibility Checks | `checks.py`；主候选 `checks` 与 `tests/test_checks.py` | **机械检查 PASS；语义待审**：43 个候选 static_status=passed、execution_status=not_run；执行、scope 语义与 Oracle 语义不从 gate 推断 |
| 三种方法共享代码池与候选 cap | `configs/default.json`、`pipeline.py`、`providers.py`、`batching.py`；`contexts/`、各方法 `prompt.txt` | **PASS**：当前 cap=3；16k 字符/论文 Full-first freeze；Full/Direct DATA 对象相同，Code-only 代码相同、论文证据为空；三份实际保存 prompt 均 exact-match 重建值 |
| 组件范围冻结与限定发现 | `configs/discovery-scopes.json`、`docs/scan-audit.zh.md`、prepared `scan.json.component_scope` | **PASS**：真实 prepared scope 与人工清单一致；须报告选择成本和条件抽取盲区，不能声称 whole-repo 自动发现 |
| 真实模型响应和成本记录 | `providers.py`；`runs/model-budget.json`、`runs/codex-main/model/batches/*/attempt-1/` 的事件、响应与 provenance | **PASS**：主 call_id 5/6/7 均为 fixed gpt-5.6-sol、统一 instruction hash、工具事件为空；主运行已知 usage 99,276 token，前期失败与 smoke 分开记账 |
| 真实 raw、prompt、公平性与成本审计 | `src/paperprobe/auditing.py`、`runs/codex-main/experiment-audit.json/.md`；CLI `audit --run` | **PASS**：原始 batch、候选 cap/数量、材料、model/instruction/CLI 与调用成本记录均一致；pass 不是语义质量结论 |
| 缓存恢复和无新调用重放 | `pipeline.py`、`tests/test_pipeline.py`；`runs/replay/replay-verification.json`、`runs/codex-main/budget-after-main-and-replay.json` | **PASS**：15 任务、43 候选、0 失败，候选及检查逐项完全一致；protocol 一致、new_model_invocations=0；真实同目录 resume 也全部 Cached、ledger 仍 7。失败默认缓存不自动 retry；replay 不算独立实验重复 |
| 盲审包、双人独立评分、汇总 | `review_ui.py`、`evaluation.py`、`reporting.py`、`docs/review-guide.zh.md`；`runs/codex-main/review/` 与 `evaluation/`、`runs/validation/ui-qa.json` | **数据流与视觉 QA PASS；人评 not_started**：实际浏览器页面 43 候选、258 评分控件、0 非空评分；公共 scope 不暴露 code_only 标签，raw SHA 未改；review_row_count=0、human_conclusions_available=false |
| CLI 与安装环境 | `src/paperprobe/cli.py`、`scripts/bootstrap.sh`、`.venv`；doctor/prepare/run/review/serve | **PASS**：Python 3.12.14、pypdf 6.19.0、Git/Codex 存在且 CLI 已认证；真实主运行与 serve 页面已验收 |
| 本地只读审查服务的 HTTP 边界 | `src/paperprobe/webapp.py`、`tests/test_webapp.py`、`runs/validation/ui-qa.json` | **PASS**：10 项真实 loopback HTTP 边界测试通过；主页面 PDF/引用源码 endpoint 均 HTTP 200、Content-Type 正确、bytes/hash 与本地源相同；private、遍历、未引用文件、symlink 越界/别名、外部绑定和写入被拒绝 |
| 全量测试 | `tests/test_*.py`、`runs/validation/unit-tests.log` | **PASS**：UI 与匿名数据处理更新后，负责人最终 suite 实际 131 项、3.429 秒、无 skip；独立复核也是 131 项通过 |
| 实际目标代码运行 | 独立 harness 与 runtime 日志 | **not_run**：不是本次静态核心的 mandatory 验收；候选执行性、触达、bug 与已验证 Oracle 均尚无证据 |
| Final paper 与研究结论 | 团队后续独立撰写的报告、人工记录、实验结果 | **pending**：此交付是工具与实验支撑，未代写 final paper |

## 已完成的真实数据验收

运行环境：bundled Python `/Users/pp/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`，标准库 `unittest` 与 `pypdf`。

```text
python3 -m unittest discover -s tests -p test_catalog.py -v
test_all_ten_pdfs_exist_match_hash_and_parse ... ok
test_catalog_counts_ids_and_metadata ... ok
test_five_repositories_exist_and_match_pinned_commits ... ok
Ran 3 tests in 0.745s
OK
```

实际检查了 10 份 PDF、202 页、5 个 shallow 仓库；没有 skip。数据均来自公开论文页面和官方代码仓库，没有读取 issue 标签作为候选发现线索。原论文、代码快照、当前版本 API 可能存在差异；来源固定只支持复查，并不证明快照就是论文原实验提交。详见论文选择文档。

测试的离线行为：完全缺失 catalog、全部 PDF 或全部仓库会显示明确 skip 信息；部分缺失、内容改变或 commit 不匹配会失败。交付验收必须出现上面的真实 PASS，不能用 skipped suite 代替。

## 真实准备与全量测试

`data/processed/index.json` 已记录 10 篇 PDF、202 页。五个选入案例的 `(files, conditions, errors)` 分别为 MInference `(6,51,0)`、SparTA `(22,132,0)`、InfiniGen `(5,179,0)`、ALEX `(6,196,0)`、FlashAttention-2 `(16,172,0)`；条件合计 730。prepared scope 与 `configs/discovery-scopes.json` 逐项一致；1,220 个邻近源码附件的行范围、原文与 UTF-8 SHA256 逐项核对通过。附件的 `applicability_status=unverified_neighborhood` 保留，来源匹配不升级为合法输入契约。

```text
.venv/bin/python -m unittest discover -s tests
Ran 131 tests in 3.429s
OK
```

测试包含来源篡改与 protocol 不一致拒绝、缓存/失败状态、batch schema、匿名人审数据契约、机械检查和真实 loopback HTTP 边界。mocked provider 测试验证协议实现；它们不替代真实模型 provenance。

初始 12k 字符预算的预检记录在 `runs/preflight-context-budget/preflight-note.json`：`aborted_before_generation`、`model_invocations=0`。随后提升为 16k 字符/论文并保存 Full-first 冻结上下文，不将预检计成失败模型调用。

主实验 `runs/codex-main` 使用 cap=3，5×3=15 个任务均完成，产生 43 个原始候选、0 个失败任务。三个真实共享 invocation 的记录如下。batch 中 paper 输出非独立重复，当前只支持描述性开发 pilot。每个 batch 的 wall time 与 token 只在 `metadata.batches` 计一次，不把 paper task duration 相加；reasoning output 作为 CLI 单列字段保留，不再次加到 input+output 总量。

| 方法 | call_id | 任务 / 原始候选 | 输入 token | 输出 token | 输入+输出 | batch wall 秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full | 5 | 5 / 13 | 27,665 | 6,488 | 34,153 | 319.111 |
| Code-only | 6 | 5 / 15 | 24,137 | 5,608 | 29,745 | 275.631 |
| Direct | 7 | 5 / 15 | 29,339 | 6,039 | 35,378 | 297.567 |
| 主运行合计 | 3 invocations | 15 / 43 | 81,141 | 18,135 | 99,276 | 892.309 |

三份 provenance 的 `model_requested=gpt-5.6-sol`、`instruction_sha256` 与冻结 protocol 一致，`tools_used=[]`；43 个候选的机械检查均通过，实际执行均未运行，人评均未填。`experiment-audit.json/.md` 的 `audit_status=pass` 核对了实际 raw response、prompt、公平性与资源计量。

`runs/replay` 真实完成 15 任务、43 候选、0 失败；与原运行按 paper/method 逐项比较候选及机械检查内容完全一致。`replay-verification.json` 记录 source protocol 一致、新模型调用数 0、main 最后 call_id=7 且 ledger 仍 7。`budget-after-main-and-replay.json` 保留账本汇总；真实同目录 resume 输出全部 Cached，账本同样没有增加。

主运行人审包已导出 43 个匿名候选。`evaluation/evaluation.json` 尚无人类评分，`review_row_count=0`、`human_review_status=not_started`、`human_conclusions_available=false`。最终公共展示将显式 `code_only` scope 提示置为 unknown，raw results SHA256 仍与重放证明中的 source SHA 一致；没有变更原始候选或填入评分。

负责人已在本机 IAB 浏览器实际检查最终主页面：43 个候选卡片、258 个评分控件、0 个非空评分；页面进度为“43候选 / 0完整 / 0已开始”。摘要与三列评分布局可见，完整原始 JSON 和来源上下文保留在默认折叠区域。PDF 与引用源码两个 endpoint 均返回 HTTP 200，分别为 `application/pdf` 与 `text/plain; charset=utf-8`，响应 bytes/hash 与本地源一致。验收记录为 `runs/validation/ui-qa.json`。未审的上下界不是方法效果结论，页面可用也不意味着已有人类审查。

冻结后的 `(代码条件,论文证据)` 数量为 MInference `(3,3)`、SparTA `(3,3)`、InfiniGen `(3,3)`、ALEX `(5,3)`、FlashAttention-2 `(4,3)`。独立重建三种 batch prompt 并比较 DATA：Full 与 Direct 完全相同，Code-only 的代码完全相同且论文 evidence 数组为空；三份实际保存请求逐字符匹配重建值。该验收验证材料公平性，不评价模型输出质量或 paper scope 的语义正确性。

## 集成负责人更新清单

- [x] 安装和 `doctor` 成功，记录 Python/依赖/CLI 可用性；不输出认证文件。
- [x] `prepare --all` 真实完成 10 份提取与 5 个组件扫描，保存各仓库文件数、条件数和错误。
- [x] 冻结组件与选择理由后重新 prepare；文档披露人工范围选择与整仓库扫描混池风险。
- [x] heuristic demo 标为流程示例，不将旧协议 demo 当当前主实验结果。
- [x] 真实主模型有 3 份成功响应、JSONL usage 和 provenance；前期失败调用也留在预算账本。
- [x] 对 5 案例 ×3 方法保存全部 15 个冻结任务记录；主运行全部完成，原始候选 43 个。
- [x] 实际同目录 cache resume 与 replay 完成；候选及检查一致、source protocol 一致、模型调用数未增加。
- [x] 最终主运行页面在真实浏览器视觉 QA 通过；43 候选、258 空白控件，未写人评。主 PDF/代码 endpoint 与本地源一致；独立草稿和 HTTP 边界由测试覆盖。
- [x] 主运行 review-export 与空白汇总完成：43 匿名候选、0 人评记录，状态 not_started；错误记录拒绝由 suite 验证。
- [x] 最终 UI 与匿名数据处理更新后，全量 tests 真实 131 项通过；实际人评仍 not_started。

模型成本口径：CLI invocation 不是 HTTP request。主运行合计 3 次成功调用、已知 99,276 token。整个账本另含前期通路验证：累计 7 次调用，6 次成功、1 次失败；已知 usage 共 130,230 token，失败无 usage、预留 6,541 token，`charged_tokens=136,771` 是两者合计的预算记账量，不是实际总消耗或美元成本。前期 smoke 与失败不计入主任务样本；第一个 12k context 预检未调用模型，也不计入这 7 次。

主运行统一 instruction SHA256 为 `0070a145302d47ece8e1a5e1d43d225c7c078c718e9c257f4b9a5a77e0b23eec`、CLI `codex-cli 0.147.0`。预算预留不能施加服务端硬 token 上限；成功实际量可以超过预留值，失败实际消耗也可能未知。没有计价依据时不推导美元花费。

研究有效性口径：当前 5 案例是开发/pilot 集，其中 4 个为 ML 系统；没有独立 held-out 数据、已完成的人评、动态覆盖或 bug 确认。静态上引用匹配和输入邻域合理，不证明目标语义成立。尚未完成的研究步骤必须在后续报告中保留。
