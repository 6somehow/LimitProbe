# CLAUDE.md — CS6223 limitation pipeline（代码侧）

## 项目是什么

NUS CS6223 课程项目。给定系统研究论文 + 代码仓库，论文侧和代码侧各自找 limitation，
互相验证，整合成 finding，再生成测试并执行确认。完整说明：`docs/00_project_overview.md`。

本仓库当前由 **Wanting（代码侧）** 开发，负责：
- 步骤 2：代码侧找 limitation（区域表），**两条路线都做并对比**（`docs/06_two_routes.md`）：
  路线 A 静态分析 `codeside/extractor.py`；路线 B 静态 + LLM `codeside/hybrid_extractor.py`；B-agent 自由探索 `codeside/agent_extractor.py`；B-sweep 分块通读 `codeside/sweep_extractor.py` + 复核 `codeside/relevance_filter.py`；对照组纯 LLM `codeside/llm_extractor.py`
- 步骤 3b：代码 → 论文验证——`codeside/verify3b.py`，说明和结果见 `docs/06_3b_eval.md`；B → 3b 端到端见 `docs/07_pipeline_b_3b.md`
- 步骤 4：整合成 Finding（去重、分类、priority、witness_hint）——`codeside/integrate.py` + `codeside/step4_llm.py` + `codeside/witness.py`，说明和结果见 `docs/09_step4_findings.md`
  - 效果标签检查 `codeside/effect_anchor.py`、调用链和参数对应 `codeside/callgraph.py`、被调函数名字换成入口名字 `codeside/chain_bind.py`（2026-11-15，`E2E_PLAN.md` 的 W1–W3）；Finding 编号跨运行不变
  - 过程置信度 `codeside/process_confidence.py`（2026-11-21）：每条有代码侧记录的 Finding 带静态证据（8 项检查、重复测量、预测的测试档位上限、重要性数字；代码侧不定档），随 Finding 传给测试侧，见 `docs/11_process_confidence.md`
- 共享 schema——`schema/models.py`

队友：Zhaopeng（论文侧：步骤 1、3a、agent 编排、baseline；代码在 `paperside/`），Shanghao（步骤 5–6：测试生成与执行）。

**整条 pipeline 的入口**：`python -m pipeline run <id>`（`pipeline/run.py`，说明见 `docs/10_pipeline.md`）。
它依次跑代码侧、论文侧（调用 `paperside/` 的脚本）、3b、步骤 4，输出 `results/step4/<id>/limitations_for_tests.json`；已有输出的步骤会跳过。

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
pipeline/          一条命令跑完整条 pipeline（两侧 + 整合）
paperside/         Zhaopeng 的论文侧（步骤 1、3a），不要改他的代码
data/<artifact>/   artifact.json、gold_*.json（人工）、draft_*.json（草稿）、paper_side_stub.json
docs/              总览、相关工作、schema 说明、方法规格、pilot 分析、prompt 模板
tests/             pytest；fixtures/ 放最小用例
scripts/           fetch_pilot.sh（按固定 commit 克隆 pilot）
third_party/       被分析的仓库（不提交）
out/               生成结果（不提交）
```

## 常用命令

```bash
python -m pipeline status                       # 每篇论文各步骤是否完成
python -m pipeline run <id> --pdf P --run-paper-side   # 新论文：跑完整条 pipeline（先 init，见 docs/10_pipeline.md）
python -m pipeline test <id> [--run-agent]      # 测试侧：每条 Finding 一份 report.json + LIMITATIONS.md
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
python scripts/run_pipeline.py --out-dir out/pipeline_ps --seed-cache out/pipeline   # B → 3b（论文侧用交接包）
python scripts/run_step4.py        # 步骤 4：Finding + witness_hint，写到 results/step4/（调模型，有缓存；--no-llm 不调）
python scripts/run_step4.py --process-only   # 只重算代码侧静态证据（不调模型，其余内容不变），之后跑 make_handoff_doc.py
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

- schema v0.2.0（草稿，待三人确认：Finding 7 类 + review 字段）；165 个测试全部通过（`checklimits/` 另有 239 个）。
- `python -m pipeline test <id>` 调测试侧（`checklimits/CONTRACT_TEST_REPORT.md`），输出 `results/tests/<id>/` 和 `results/report/<id>/LIMITATIONS.md`。
- 路线 B（静态 + LLM）已在 pilot 和四篇上各入口运行 3 次（`x-test-2`，prompt `hybrid-v3`，只新增、不删除 A 的结果），结果在 `out/routes/`。
- pilot 上路线 A：recall 16/16、extra 10、cond_exact 13/13。
- 抽取器支持类方法（`file::Class.method`）、`self.method()`、一层嵌套函数（`file::outer.inner`）、`--package-root`。
- 四篇开发集已固定版本并完成首次运行，暴露的缺口列在 `docs/05_dataset.md` 和 TASKS.md M2。
- 抽取器 v0 在 pilot 上 recall 16/16，多余预测 10 条（6 条不可达路径、2 条冗余、2 条内部不变量），对应 TASKS.md M2。
- 论文侧已交付：`paperside/handoffs/paper-side-v1/<论文>/paper_side.json`；`run_pipeline.py` 默认使用它（只有 FlexPrefill 有一个参数映射 `tau`，其余 scope 全是 unknown）。
- 步骤 4 已实现，五篇 289 条 Finding 在 `results/step4/`；交给 Shanghao 的单文件是 `results/step4/limitations_for_tests.json`，说明是 `results/step4/HANDOFF.md`（`scripts/make_handoff_doc.py` 生成）。
- 3b 已实现，pilot 论文层 13 条全部 not_found；与未评审草稿 result 一致 8/13，见 `docs/06_3b_eval.md`。
- 论文附录 F.2 比较了 block_size 64 和 128，stub 的 S2 只写 128，会让 F02 的 scope 判断出错，需要 Zhaopeng 处理。
- F02（硬编码 `// 128`）和 F03（模块级 causal_mask 缓存）是候选 finding，尚未执行确认。
