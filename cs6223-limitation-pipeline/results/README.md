# 结果快照（2026-11-11 更新）

由 `out/` 复制而来（`out/` 本身不进 git）。说明见 `docs/08_progress_step2_3b.md`。

- `step2_merged/<论文>/merged_runN.json`：步骤 2 最终结果（路线 A + B，3 次运行）。
- `pipeline/<论文>/limitations.json`：交给 3b 的限制列表（来自 merged_run1）。
- `pipeline/<论文>/3b.json`：3b 结论；`3b.detail.json`：引用原文、每轮投票、needs_review。
- `pipeline/candidates.json`：五篇汇总的候选清单。
- `pipeline/` 已用 Zhaopeng 的 `paper_side.json` 重跑（2026-11-11，原 stub 版本见 git 历史）；`candidates.json` 带盲审标签。
- `review/blind_review_labels.json`：Claude 子代理对路线 B 新增结果的盲审标签（228 条，单审稿人，不是人工标注）。
- `step4/`：步骤 4 的 Finding。`limitations_for_tests.json` 是交给 Shanghao 的单文件（每条自带完整 Limitation 和 3b），`HANDOFF.md` 是给他的说明；每篇 `findings.json`、`llm_records.json`（去重投票、论文侧条件）；`review_queue.json`（测试顺序）；`summary.md`。说明见 `docs/09_step4_findings.md`。每篇另有 `<id>/limitations_for_tests.json` 和 `<id>/HANDOFF.md`；新论文用 `python -m pipeline run <id>` 生成（`docs/10_pipeline.md`）。
- `3b_pilot/`：FlexPrefill 草稿 13 条限制的 3b 结果，以及答案已知测试的结果（`eval_cases.json`）。
