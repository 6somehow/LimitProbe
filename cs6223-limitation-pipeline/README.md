# CS6223 limitation pipeline

找出系统研究原型中"代码里存在、论文没有说明、又落在论文声明范围内"的 limitation，
并为每一条生成可执行的测试。

- 项目总览与分工：`docs/00_project_overview.md`
- 代码侧任务清单：`TASKS.md`
- 给 Claude Code 的上下文：`CLAUDE.md`
- 开发数据集（SparTA、MInference、InfiniGen、NNSmith）：`docs/05_dataset.md`
- **步骤 2 + 3b 进度和结果（先看这个）：`docs/08_progress_step2_3b.md`，结果在 `results/`**

## 快速开始

```bash
pip install -e ".[dev]"
scripts/fetch_dataset.sh   # 四篇 + pilot
python -m pytest -q
python -m codeside.cli extract --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --out out/flexprefill_regions.json
python -m codeside.cli evaluate --pred out/flexprefill_regions.json \
  --gold data/pilot_flexprefill/gold_regions.json
```
