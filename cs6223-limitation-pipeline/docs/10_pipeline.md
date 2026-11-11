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
```

结果：

| 文件 | 内容 |
|---|---|
| `results/step4/<id>/limitations_for_tests.json` | 这篇论文两侧的全部 limitation（去重、分类、priority、witness_hint 之后） |
| `results/step4/<id>/HANDOFF.md` | 给测试侧的说明 |
| `results/step4/limitations_for_tests.json`、`HANDOFF.md` | 所有论文合在一起（每次自动刷新） |

也可以在 Python 里调：`from pipeline.run import run`。

## 每一步做什么

| 步骤 | 做什么 | 谁的代码 | 输出 | 调模型 |
|---|---|---|---|---|
| fetch | 按 commit 克隆仓库，放好 PDF | — | `third_party/<Repo>`、`third_party/papers/<id>.pdf` | 否 |
| code | 步骤 2 最终路线 B：B-sweep 和 B-agent（都从路线 A 出发）→ 复核 → 合并 → Limitation | Wanting `codeside/` | `out/routes_*/<id>/`、`out/pipeline_ps/<id>/limitations.json` | 是 |
| paper | 步骤 1 + 3a：`run_complete_corpus.py`（独立找机制 → 拆行为 → 每个机制一个 Pi 代理查源码 → 接口）然后 `finalize_handoff.py` | Zhaopeng `paperside/` | `paperside/handoffs/paper-side-v1/<id>/` | 是（最贵） |
| verify3b | 步骤 3b：代码侧每条在论文 / README / docstring 里有没有写 | Wanting | `out/pipeline_ps/<id>/3b.json` | 是 |
| step4 | 去重、分类、priority、witness_hint | Wanting | `results/step4/<id>/` | 是（有缓存） |
| doc | 生成说明 | Wanting | `HANDOFF.md` | 否 |

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
