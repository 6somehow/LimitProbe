# 一条命令跑完整条 pipeline（2026-11-11）

论文侧（Zhaopeng，步骤 1 + 3a）、代码侧（Wanting，步骤 2 + 3b）和整合（步骤 4）合在一个入口里：
`python -m pipeline`（代码在 `pipeline/run.py`）。输入一篇论文和它的仓库，输出这篇论文**两侧的全部 limitation**，
格式和现在交给 Shanghao 的一样（`limitations_for_tests.json` + `HANDOFF.md`）。

已有的五篇（FlexPrefill、SparTA、MInference、InfiniGen、NNSmith）不用重跑：每一步发现输出已经存在就跳过，直接复用。

## 新论文怎么跑

```bash
# 0. 一次性：装论文侧依赖（Python 包 paperprobe + Pi 代理的 node_modules）
python -m pipeline setup-paperside

# 1. 登记论文：写 data/<id>/artifact.json（commit 要写完整哈希；entry 是实现论文机制的函数，可多个）
python -m pipeline init --id mypaper --title "..." --paper-url https://arxiv.org/abs/... \
  --repo-url https://github.com/org/repo --commit <40 位哈希> --domain sparse_attention \
  --entry pkg/module.py::main_function --entry pkg/other.py::Class.method \
  [--package-root src]             # 仓库里 import 的根目录不是仓库根时才需要

# 2. 看还缺什么
python -m pipeline status mypaper

# 3. 跑（会调模型、花钱；论文侧最贵，要显式加 --run-paper-side）
python -m pipeline run mypaper --pdf /path/to/paper.pdf --run-paper-side

# 4. 测试侧（Shanghao 的 checklimits）：每条 Finding 一份 report.json，汇总成 LIMITATIONS.md
python -m pipeline test mypaper [--run-agent] [--strict]
```

结果：

| 文件 | 内容 |
|---|---|
| `results/step4/<id>/limitations_for_tests.json` | 这篇论文两侧的全部 limitation（去重、分类、priority、witness_hint 之后） |
| `results/step4/<id>/HANDOFF.md` | 给测试侧的说明 |
| `results/step4/limitations_for_tests.json`、`HANDOFF.md` | 所有论文合在一起（每次自动刷新） |
| `results/tests/<id>/<finding_id>/report.json` | `pipeline test`：每条 Finding 的测试记录（测了的有判定和档位，没测的有原因代码） |
| `results/tests/<id>/index.json`、`ENV.json`、`pipeline_test.log` | 汇总和 1:1 检查、环境预检、测试侧的完整输出 |
| `results/report/<id>/LIMITATIONS.md` | 汇总报告，档位标明未校准 |

也可以在 Python 里调：`from pipeline.run import run`。

## 一个入口：`doctor` 和 `e2e`（2026-11-17）

配置只来自环境变量（或根目录的 `.env`，环境变量优先；模板见 `.env.example`）：

| 变量 | 含义 |
|---|---|
| `SOCLAAS_API_KEY` | 真 key。只有中继进程拿到；其余进程只拿到占位值 |
| `SOCLAAS_BASE_URL` | 模型服务的上游地址，如 `https://host/v1` |
| `SOCLAAS_IFACE` | 中继出站绑定的网卡，默认 `eth0`；设为空则走普通路由 |
| `PIPELINE_MODEL` | 记录和缓存用的模型名，默认 `x-test-2`（研究用的模型；改了就不会命中缓存）。**不读 `SOCLAAS_MODEL`** |

```bash
# 0. 一次性：python -m pipeline setup-paperside；pip install -e ".[llm,verify,dev]"
# 1. 登记论文：python -m pipeline init --id X ...
# 2. 运行前检查（不调模型；--live 会通过中继调一次 GET /models，验证 key、地址、网卡）
python -m pipeline doctor X --paper-side --agent --live --pdf paper.pdf
# 3. 一条命令：检查 -> 起中继 -> 步骤 1 到 4 -> 测试（带 --provision）-> 关中继
python -m pipeline e2e X --pdf paper.pdf --run-paper-side --run-agent
```

`e2e` 先做 `doctor` 的全部静态检查和一次真实调用，任何一项 FAIL 就在花钱和克隆之前停下（退出码 1，消息 `stopped: ...`）。
中继固定在 `127.0.0.1:8787`（代码 agent 的沙箱配置写死了这个端口）；已有中继在监听时直接复用，不会再起、也不会关。
所有阶段有输出就跳过，所以中途失败后重跑同一条命令即可续上；`--run-paper-side` 的论文侧不会续跑一个不完整的请求，
见 `checklimits/HANDOFF.md` §0。`pipeline test` 也有了 `--provision`。

## 每一步做什么

| 步骤 | 做什么 | 谁的代码 | 输出 | 调模型 |
|---|---|---|---|---|
| fetch | 按 commit 克隆仓库，放好 PDF | — | `third_party/<Repo>`、`third_party/papers/<id>.pdf` | 否 |
| code | 步骤 2 最终路线 B：B-sweep 和 B-agent（都从路线 A 出发）→ 复核 → 合并 → Limitation | Wanting `codeside/` | `out/routes_*/<id>/`、`out/pipeline_ps/<id>/limitations.json` | 是 |
| paper | 步骤 1 + 3a：`run_complete_corpus.py`（独立找机制 → 拆行为 → 每个机制一个 Pi 代理查源码 → 接口）然后 `finalize_handoff.py` | Zhaopeng `paperside/` | `paperside/handoffs/paper-side-v1/<id>/` | 是（最贵） |
| verify3b | 步骤 3b：代码侧每条在论文 / README / docstring 里有没有写 | Wanting | `out/pipeline_ps/<id>/3b.json` | 是 |
| step4 | 去重、分类、priority、witness_hint | Wanting | `results/step4/<id>/` | 是（有缓存） |
| doc | 生成说明 | Wanting | `HANDOFF.md` | 否 |

**test**（`python -m pipeline test <id>`，2026-11-15）：在 `checklimits/` 目录下调用
`python -m checklimits test <id> --results-root <pipeline 根>/results`，接口见 `checklimits/CONTRACT_TEST_REPORT.md`。
它不是 `run` 的一步：开 `--run-agent` 时每条 Finding 要跑一个 code agent（5 到 15 分钟）。

- 不开 `--run-agent` 时只重新审计 `checklimits/agent_results/` 和 `results/tests/<id>/` 里已有的测试包，
  能判断但没有测试包的记为 `not_run(not_attempted)`。
- 退出码按契约第 6 节：0 报告完整（有 `not_run` 也算）；2 输入错误、3 条目对不上、1 测试侧异常时停下并说明原因；
  4（只在 `--strict` 下）报告已写出，但有环境、agent 或 harness 原因的 `not_run`，也按失败退出。
- `status` 里 test 一行：`done` 报告完整且由当前的步骤 4 文件生成；`stale` 步骤 4 重跑过，要重测；`todo` 还没有报告。
- 被测仓库的环境由测试侧预检（`ENV.json`），不安装任何东西。缺依赖时能判断的 Finding 都记为 `not_run(env_unavailable)`，
  原因写在报告里。

顺序是 code → paper → verify3b：Zhaopeng 的 `finalize_handoff.py` 会读代码侧的 limitation
（`results/pipeline/<id>/limitations.json`，pipeline 自动放好），3b 又要用论文侧的 `paper_side.json`。

- **跳过和重做**：fetch、code、paper、verify3b 看输出是否存在，存在就跳过；要重做就删掉对应输出。step4 和 doc 每次都重跑
  （LLM 答案有缓存，很快）。`--until <步骤>` 跑到某一步为止。
- **论文侧为什么要显式开启**：每个机制开一个 Pi coding agent，调用量远大于其他步骤；而且会写进 `paperside/`
  （运行记录 `paperside/runs/`、交接包 `paperside/handoffs/`）。没有 `--run-paper-side` 时，如果交接包不存在就停下并说明原因。
  也可以把 Zhaopeng 单独跑好的交接包直接放进 `paperside/handoffs/paper-side-v1/<id>/`。
- **论文侧的前置条件**，pipeline 自动处理：在 `paperside/workstreams/zhaopeng/team-reviewed.json` 里登记这篇论文的
  commit 和 PDF 哈希（他的代码要求先登记）；在 `paperside/data/repos/team-<id>` 放一份固定 commit 的仓库。
  这两项都只是数据，不改他的代码。
- **API key** 从环境变量或 `.env` 读，不会打印。
- 日志：代码侧在 `out/pipeline_ps/<id>/pipeline.log`，论文侧在 `out/paperside_logs/<id>.log`。

## 现状和限制

- **新论文的完整流程还没有真正跑过一次**（太贵，也还没有新论文）。已经验证的部分：
  - 五篇论文上，每一步都能识别为已完成并复用，step4 和 doc 能重新生成；
  - 用临时 artifact 测过 init、fetch、status，以及论文侧缺前置条件或没开 `--run-paper-side` 时的报错；
  - 论文侧依赖装好后，Zhaopeng 的 219 个单元测试和 `validate_delivery.py` 在 schema v0.1.0 下全部通过。
- **schema v0.2.0 会触发 Zhaopeng 的哈希检查**：他的 `validate_delivery.py` 和 10 个单元测试会对比 `schema/models.py`
  的哈希，所以在 v0.2.0 下会报 “Shared consumer schema changed”。v0.2.0 只改了 Finding，没改他输出的四个数组和 Limitation。
  团队确认 v0.2.0 后，需要他更新这个哈希。我没有改他的文件。
- 论文侧有些硬编码只对五篇有效（例如 SparTA 的专用脚本）。新论文走的是 `run_complete_corpus.py` 的通用流程，没有人工
  `review-adjustments.json`，所以接口修订少于五篇已交付的包。
- 代码侧只用第 1 次运行（`run1`），和现在五篇的结果一致。
