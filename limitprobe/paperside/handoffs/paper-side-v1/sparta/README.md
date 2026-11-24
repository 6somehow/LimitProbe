# sparta 论文侧交接包

`paper_side.json` 是 Wanting `codeside.verify3b --paper-side` 的原生输入，四个数组保持共享 schema v0.1.0。`validation.json` 已调用实际消费者的加载函数和范围检查器。

`conformance.json` 保留全部 206 条行为、两条作用域及原始三结论；未完成项 verdict=null，不是第四类结论。`finding_candidates.json` 按原模型原因归组，父子机制可能重叠，不能直接当作独立 bug 数。`limitations.json` 是附原文的静态差异候选，未赋予已确认运行效果。共享 Verification 的五类语义与正向 claim 判定不同，因此没有机械改标签；整合时通过 claim_id/behavior_id 读取 conformance。

`source_reads.json` 保留实际代码片段；registry 的 repo 别名必须与原始报告的固定 commit 配合。共享 CodeLocation 不支持多仓库，故依赖库引用留在 registry，不伪装成主仓库路径。

`pending_records.json` 留存引用或语义未闭合的论文条目；`inactive_bindings.json` 中的映射不传给求解器。经验设置不变成支持范围；free_text 不强制数值化；集合/张量/len 条件无法表达时 unknown 是明确的接口限制，不是模型发现缺陷。

本模块没有运行目标；团队独立复核和下游测试仍待进行。复跑需 `x-test-2` 授权环境，所有实际 prompts/返回保存在 manifest 指向的 work 目录。

## Git source distribution

This lightweight checkout omits the full evidence/PDF/API logs, ZIP and HTML views. See source-distribution.json and original-bundle-index.json. Absolute paths in original provenance identify the maintainer archive, not portable links. Offline validation: run `python scripts/validate_delivery.py` from paperside/.
