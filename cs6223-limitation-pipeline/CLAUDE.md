# CLAUDE.md — CS6223 limitation pipeline（代码侧）

## 项目是什么

NUS CS6223 课程项目。给定系统研究论文 + 代码仓库，论文侧和代码侧各自找 limitation，
互相验证，整合成 finding，再生成测试并执行确认。完整说明：`docs/00_project_overview.md`。

本仓库当前由 **Wanting（代码侧）** 开发，负责：
- 步骤 2：代码侧找 limitation（区域表），**两条路线都做并对比**（`docs/06_two_routes.md`）：
  路线 A 静态分析 `codeside/extractor.py`；路线 B 静态 + LLM `codeside/hybrid_extractor.py`；B-agent 自由探索 `codeside/agent_extractor.py`；B-sweep 分块通读 `codeside/sweep_extractor.py` + 复核 `codeside/relevance_filter.py`；对照组纯 LLM `codeside/llm_extractor.py`
- 步骤 3b：代码 → 论文验证——`codeside/verify3b.py`，说明和结果见 `docs/06_3b_eval.md`；B → 3b 端到端见 `docs/07_pipeline_b_3b.md`
- 步骤 4：整合成 Finding——待实现
- 共享 schema——`schema/models.py`

队友：Zhaopeng（论文侧：步骤 1、3a、agent 编排、baseline），Shanghao（步骤 5–6：测试生成与执行）。

## 下一步做什么

看 `TASKS.md`，从第一个未完成的里程碑开始（M1 需要开会；可以直接从 M2 开始写代码）。
方法细节在 `docs/03_codeside_spec.md`，pilot 的背景在 `docs/04_pilot_flexprefill.md`。

**开发数据集是四篇论文**：SparTA、MInference、InfiniGen、NNSmith（`docs/05_dataset.md`，
元数据在 `data/<id>/artifact.json`）。开发和调试时用这四篇测试；FlexPrefill 是已标注好的示范 pilot。
在这四篇上的数字都是开发集数字，泛化结论只能来自最后约定的 held-out artifact。

## 目录

```
schema/            共享 schema（pydantic）与导出的 JSON Schema
codeside/          extractor.py（步骤 2）、evaluate.py、cli.py
data/<artifact>/   artifact.json、gold_*.json（人工）、draft_*.json（草稿）、paper_side_stub.json
docs/              总览、相关工作、schema 说明、方法规格、pilot 分析、prompt 模板
tests/             pytest；fixtures/ 放最小用例
scripts/           fetch_pilot.sh（按固定 commit 克隆 pilot）
third_party/       被分析的仓库（不提交）
out/               生成结果（不提交）
```

## 常用命令

```bash
pip install -e ".[dev]"            # 依赖：pydantic；测试：pytest；可选：z3-solver
scripts/fetch_pilot.sh             # 克隆 FlexPrefill @ a24b27b
scripts/fetch_dataset.sh           # 按 data/*/artifact.json 克隆四篇 + pilot 到固定 commit
python -m pytest -q                # 必须保持全绿
python -m codeside.cli extract --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --out out/flexprefill_regions.json
python -m codeside.cli evaluate --pred out/flexprefill_regions.json \
  --gold data/pilot_flexprefill/gold_regions.json
python -m codeside.cli to-limitations --regions out/flexprefill_regions.json \
  --out out/flexprefill_code_limitations.json
python -m codeside.cli extract --repo third_party/InfiniGen \
  --entry speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen --artifact infinigen \
  --out out/infinigen_mha_gen.json --package-root speedup/infinigen --package-root speedup/flexgen
python -m codeside.cli extract-llm --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/llm_run1.json   # 需要 .[llm] + .env
python -m codeside.cli compare --gold data/pilot_flexprefill/gold_regions.json \
  --pred static=out/flexprefill_regions.json --pred llm1=out/llm_run1.json
scripts/fetch_papers.sh            # 下载五篇论文 PDF 到 third_party/papers/
python -m codeside.verify3b --limitations data/pilot_flexprefill/gold_code_limitations.json \
  --artifact data/pilot_flexprefill/artifact.json --pdf third_party/papers/flexprefill.pdf \
  --repo third_party/FlexPrefill --paper-side data/pilot_flexprefill/paper_side_stub.json \
  --model x-test-2 --repeats 3 --out out/3b/flexprefill.json   # 需要 .[verify] + .env
python scripts/eval_3b.py          # 3b 的已知答案测试
python -m codeside.cli validate data/*/*.json
python -m schema.export_json_schema
```

## 规则

1. **schema 是三人之间的接口。** 改字段要提升 `SCHEMA_VERSION`、更新 `docs/02_schema.md`、重新导出 JSON Schema、跑测试。
2. **gold 文件是人工标注，不要用程序覆盖。** 生成结果写到 `out/`；草稿评审后另存为新的 gold 文件。
3. **判定尽量确定性。** LLM 只用于理解和定位（读论文、补动态分发、语义匹配）；scope 求交、评测覆盖、可行性用代码或 z3。
4. **证据可核对。** 每条记录带 provenance；quote 必须逐字出现在来源里，代码里要有校验；位置用相对仓库根目录的路径，行号对应 Artifact.commit。
5. **每加一条抽取规则，就在 `tests/fixtures/` 加一个最小用例**，并在 pilot 上跑 evaluate，看 recall 和多余预测的变化。
6. **pilot 上的数字不代表泛化。** v0 规则是对着 FlexPrefill 写的；泛化结论只能来自没调过规则的新 artifact（TASKS.md M3）。
7. 不要修改 `third_party/` 里的代码。
8. **两条路线必须公平对比**：同样的入口和上下文、同样的校验、同样的 gold 和匹配规则；LLM 的模型 ID、temperature、prompt 版本都要记录；不要对着 gold 反复调 prompt 或规则。

## 当前状态（交接时）

- schema v0.1.0；21 个测试全部通过。
- 路线 B（静态 + LLM）已在 pilot 和四篇上各入口运行 3 次（`x-test-2`，prompt `hybrid-v3`，只新增、不删除 A 的结果），结果在 `out/routes/`。
- pilot 上路线 A：recall 16/16、extra 10、cond_exact 13/13。
- 抽取器支持类方法（`file::Class.method`）、`self.method()`、一层嵌套函数（`file::outer.inner`）、`--package-root`。
- 四篇开发集已固定版本并完成首次运行，暴露的缺口列在 `docs/05_dataset.md` 和 TASKS.md M2。
- 抽取器 v0 在 pilot 上 recall 16/16，多余预测 10 条（6 条不可达路径、2 条冗余、2 条内部不变量），对应 TASKS.md M2。
- 论文侧数据目前是 stub（`paper_side_stub.json`），等 Zhaopeng 的步骤 1 输出替换。
- 3b 已实现，pilot 论文层 13 条全部 not_found；与未评审草稿 result 一致 8/13，见 `docs/06_3b_eval.md`。
- 论文附录 F.2 比较了 block_size 64 和 128，stub 的 S2 只写 128，会让 F02 的 scope 判断出错，需要 Zhaopeng 处理。
- F02（硬编码 `// 128`）和 F03（模块级 causal_mask 缓存）是候选 finding，尚未执行确认。
