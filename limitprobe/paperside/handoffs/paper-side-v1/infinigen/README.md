# InfiniGen：论文侧交接包

70 条行为，artifact 路径已判断 59 条、待办 11 条。共享接口已完成来源修订与实际消费者检查；未运行目标系统，人工语义验收待完成。

先读三个文件：

- `paper_side.json`：传给 Wanting 的 `codeside.verify3b --paper-side`。
- `conformance.json`：逐条论文行为、源码判断及证据索引。
- `limitations.json`：有论文依据的不符/未实现候选，供后续整合；不是已确认 bug。

接入命令见 [RUN_WITH_WANTING.md](RUN_WITH_WANTING.md)，模块说明见 [主 README](../../../README.md)。源码片段位于 `source_reads.json`，引用位置和版本见 `code_evidence_registry.json`。冻结清单见 `frozen-behaviors.json` 与 `mechanisms.json`。

`review-notes.json` 描述修订前的审阅；`review-adjustments.json` 保留具体修订，应用后的状态与数量见 `validation.json`。基线或背景观测如有，单独放在 `reported_observations.json`，不进入本系统评估接口。

未闭合的论文引文留在 `pending_records.json`；代码核验未完成项在 `conformance.json` 中用 pending/null 表示。两种待办分别保留，不强行认定未实现。入口导航不是参数映射，也不是实现支持证明。

完整本地包保留 PDF、调用记录与 HTML；轻量发布省略这些大文件，详见发布包的 `source-distribution.json`。原始绝对路径仅描述运行位置，其他机器须使用自己的资产路径。
