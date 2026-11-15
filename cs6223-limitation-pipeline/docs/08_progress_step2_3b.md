# 代码侧进度：步骤 2 + 步骤 3b（截至 2026-11-08）

负责人：Wanting。这份文档用简单的话说明做了什么、怎么跑、结果是什么、还差什么。
细节见 `06_two_routes.md`（步骤 2）、`06_3b_eval.md`（3b 的评测）、`07_pipeline_b_3b.md`（端到端运行）。

## 一句话

输入一篇论文的 PDF 和代码仓库，输出“代码里有、但论文没写”的限制候选清单。
步骤 2 在代码里找限制，3b 拿这些限制去论文和文档里查有没有写。两步已经串起来，五篇论文都跑完了。

## 流程：从输入到输出

```
论文 PDF + 代码仓库
   │
   ▼  步骤 2：在代码里找限制
   │   路线 A：规则扫代码（assert / raise / if 分支）
   │   路线 B：LLM 补漏（分块通读 + 自由探索），复核后合并、去重；A 的结果一条不删
   │   → out/pipeline/<论文>/limitations.json
   ▼  步骤 3b：每条限制回答 3 个问题
   │   1. 文档写了吗？  检索论文/README/注释 → LLM 判断 → 原文引用必须逐字查得到 → 问 3 次取多数
   │   2. 在论文范围内吗？  z3 对比论文声明的适用范围
   │   3. 论文测过吗？  z3 对比论文的评测配置
   ▼
   3b.json（结论，交给步骤 4）、3b.detail.json（引用、每轮投票、是否要人工复核）
   candidates.json（五篇汇总）
```

3b 的判断结果有五种：没写（not_found）、写了（found）、写得更弱（weaker）、边界对不上（boundary_mismatch）、写的相反（contradicted）。

## 怎么跑

```bash
uv venv && uv pip install -e ".[dev,llm,verify]"
scripts/fetch_dataset.sh && scripts/fetch_papers.sh       # 代码仓库和论文 PDF 放到 third_party/（不进 git）
echo 'SOCLAAS_API_KEY=...' > .env; echo 'SOCLAAS_BASE_URL=...' >> .env   # 不进 git
python -m pytest -q                                       # 111 个测试
python scripts/run_pipeline.py --model x-test-2 --repeats 3 --parallel 1 --workers 3
python scripts/summarize_pipeline.py
```

模型：`x-test-2`（实际是 deepseek-v4.1-flash-1017），temperature 0。并发不要开太高，否则会被限流。

## 做了什么

| 部分 | 内容 | 代码 |
|---|---|---|
| 步骤 2 路线 A | 静态分析，不用 LLM | `codeside/extractor.py` |
| 步骤 2 路线 B | 分块通读 + 自由探索 + 相关性复核 + 去重 | `sweep_extractor.py`、`agent_extractor.py`、`relevance_filter.py`、`dedup.py` |
| 3b 文档索引 | PDF 切段、README/注释切段、BM25 检索、引用逐字校验 | `codeside/doc_index.py` |
| 3b 范围判断 | 用 z3 判断在不在范围内、测没测过；翻译不了就给 unknown | `codeside/scope_check.py` |
| 3b 主体 | 4 种查找方式（检索 / 全文 / 逐段扫 / 检索+反方复查），默认用最后一种 | `codeside/verify3b.py` |
| 端到端 | 步骤 2 → 3b，五篇一起跑 | `scripts/run_pipeline.py`、`scripts/summarize_pipeline.py` |
| 测试 | 单元测试 + 答案已知的测试集 | `tests/`、`scripts/eval_3b.py` |

### 3b 的“答案已知的测试”

真实论文写没写，没有标准答案，所以自己出了三类题（`tests/fixtures/eval_3b_cases.json`）：

| 题型 | 正确答案 | 默认方法成绩 |
|---|---|---|
| 在论文副本里植入的 27 句限制 | 找到 | 25/27 |
| 8 条用词相似、但论文没写的陷阱 | 没写 | 误报 0/8 |
| 7 条其他论文里真实写过的限制 | 找到 | 7/7 |

题是自己出的，比真实情况简单，成绩偏乐观。“我们没有评测过 X”这种委婉说法容易漏。

## 结果（`results/`）

五篇共 155 条限制：

| 论文 | 来源 | 限制数 | 都没写 | 写在某处 | 需人工复核 |
|---|---|---|---|---|---|
| FlexPrefill | A | 29 | 22 | 7 | 2 |
| FlexPrefill | B | 17 | 11 | 6 | 1 |
| InfiniGen | A | 4 | 4 | 0 | 0 |
| InfiniGen | B | 16 | 15 | 1 | 0 |
| MInference | A | 11 | 11 | 0 | 0 |
| MInference | B | 39 | 39 | 0 | 2 |
| NNSmith | B | 36 | 30 | 6 | 2 |
| SparTA | B | 3 | 2 | 1 | 0 |

合计：没写 134、写了 12、写得更弱 5、边界对不上 3、写的相反 1。

主要发现：
1. **论文很少说明代码里的限制。** FlexPrefill 草稿的 13 条，论文一条都没写（3 轮一致）；其中 3 条写在 README 或注释里。
2. **最强的候选有 24 条**：盲审标为“有用”、3b 判为“没写”。
3. **候选 F02 的依据有误**：stub 写 `block_size` 只有 128，但论文附录 F.2 也测了 64，所以它在论文范围内。64 和 128 效果接近，危害可能不大，要实际跑测试确认。

## 还没完成 / 要一起定的

1. **“没写”不等于“值得报”。** 判为没写的里面有 35 条“真的但没用”、12 条“错的”。3b 只回答写没写。
2. **范围判断缺数据。** 只有 FlexPrefill 有临时的论文侧 stub，其余四篇 scope 都是 unknown，要等论文侧（Zhaopeng）的数据。
3. **README/注释的判断不够稳定**，多轮不一致的标了 `needs_review`。
4. **判断规则待定**：FIXME 注释算不算“写了”？只写版本号、没说后果，算不算写了？（建议都算“没写”）
5. **盲审标签**只覆盖一部分条目，每条只有一个审稿人。

## 下一步

- 人工看那 24 条，挑最强的几条交给测试侧（Shanghao）写测试。
- 拿到论文侧数据后重跑 3b，补上范围判断。
- 三人定上面第 4 条的规则。
