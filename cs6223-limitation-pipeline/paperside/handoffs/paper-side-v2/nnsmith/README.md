# nnsmith · schema 0.2.0 交接样例

直接输入：`paper_side.json`；整合差异另读 `limitations.json`。

先看 `parameter_mappings.json` 的论文/代码对照，再看 `consumer_cases.json` 的下游实际求解结果。所有案例是接口探针，不是新 Finding，也没有运行目标系统。

原版本保留在 `legacy-*` 文件及 [v1 包](../../paper-side-v1/nnsmith/)；`conformance.json` 未改变。新增 Pool2d 范围仅适用于该算子；正整数核大小只是必要条件，不保证整个配置有效。完整来源见 `migration.json`，历史审阅仍指 v1。
