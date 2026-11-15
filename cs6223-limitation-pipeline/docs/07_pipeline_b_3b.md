# 步骤 2（最终的 B）→ 步骤 3b：端到端运行（2026-11-06）

```bash
python scripts/run_pipeline.py --model x-test-2 --repeats 3 --parallel 1 --workers 3   # 结果在 out/pipeline/<id>/
python scripts/summarize_pipeline.py [--labels <盲审标签 JSON>]                       # 汇总 + out/pipeline/candidates.json
```

- 输入：`out/routes_merged/<id>/merged_run1.json`（A + 复核后的 sweep 和 agent，去重，见 `06_two_routes.md`）。
- `to-limitations --include-variants`：B 的 `mechanism_variant` 也导出，`effect_type` 记为 `path_change`（schema 不变；默认仍跳过）。A 自己的 `mechanism` 区域不导出。
- 3b：`consensus`，3 轮，`3b-v3`，`x-test-2`（实际 `deepseek-v4.1-flash-1017`）。只有 FlexPrefill 有论文侧 stub，其余四篇的 scope 都是 unknown。
- 并发要低（`--parallel 1 --workers 3`），否则会被限流（429）；3b 遇到调用失败会报错退出，不会当成“没写”，缓存保证重跑不重复付费。

## 修掉的问题

`scope_check.py` 遇到非布尔条件会让 z3 抛异常，整篇论文的 3b 直接失败（B 的条件写法比 A 多样，比如 `not gqa_interleave`、path_prefix 里的单个整数名字）。
现在 z3 的异常统一转成 Untranslatable → scope 为 unknown，加了回归测试。

## 结果

| 论文 | 来源 | 限制数 | 论文和文档都没写 | 写在某处 | 需人工复核 |
|---|---|---|---|---|---|
| FlexPrefill | A | 29 | 22 | 7 | 2 |
| FlexPrefill | B | 17 | 11 | 6 | 1 |
| InfiniGen | A | 4 | 4 | 0 | 0 |
| InfiniGen | B | 16 | 15 | 1 | 0 |
| MInference | A | 11 | 11 | 0 | 0 |
| MInference | B | 39 | 39 | 0 | 2 |
| NNSmith | B | 36 | 30 | 6 | 2 |
| SparTA | B | 3 | 2 | 1 | 0 |

共 155 条：not_found 134、found 12、weaker 5、boundary_mismatch 3、contradicted 1。

和盲审标签对照（B 的新增里有标签的 83 条）：有用 29 条，其中 24 条 3b 判为没写，是目前最强的候选，
列表在 `out/pipeline/candidates.json`（`label == "useful"` 且 `result == "not_found"`）。

FlexPrefill 的 scope（基于 stub）：in_scope 且没写 2 条（`kl_div < tau`、`seq_len <= min(vertical_size, slash_size) * block_size`），
scope_edge 且没写 3 条（`q_len != k_len` 两处、`q_len != 1`），其余大多 unknown。

## 注意

- **not_found 不等于 finding。** 有 35 条“真的但没用”和 12 条“错的”也被判为没写；3b 只回答“写没写”，不判断值不值得报。
- 盲审标签只覆盖部分条目，每条只有一个 Claude 审稿人。
- 四篇开发集没有论文侧数据，scope 全是 unknown，“在不在论文范围内”还没法判断。
