# 结果快照（2026-11-08）

由 `out/` 复制而来（`out/` 本身不进 git）。说明见 `docs/08_progress_step2_3b.md`。

- `step2_merged/<论文>/merged_runN.json`：步骤 2 最终结果（路线 A + B，3 次运行）。
- `pipeline/<论文>/limitations.json`：交给 3b 的限制列表（来自 merged_run1）。
- `pipeline/<论文>/3b.json`：3b 结论；`3b.detail.json`：引用原文、每轮投票、needs_review。
- `pipeline/candidates.json`：五篇汇总的候选清单。
- `3b_pilot/`：FlexPrefill 草稿 13 条限制的 3b 结果，以及答案已知测试的结果（`eval_cases.json`）。
