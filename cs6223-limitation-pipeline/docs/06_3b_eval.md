# 步骤 3b：实现与评测

给定代码侧 Limitation，分别回答：文档里写了吗（LLM + 逐字校验）、在论文 scope 内吗（确定性）、论文评测过吗（确定性）。

> **以下数字都是开发数字。** 对照的草稿没有经过评审，植入测试是合成数据；泛化结论要等 held-out（TASKS M3）。

## 相关工作：没有完全相同的工作

| 工作 | 相同点 | 不同点 |
|---|---|---|
| [SciCoQA](https://arxiv.org/abs/2601.12910)（ACL 2026） | 论文–代码差异，含 Paper Omission | 整体检测差异；不判断 scope 和是否评测；最好的模型也只检出 46.7%，Paper Omission 尤其难 |
| [MPDetector](https://arxiv.org/abs/2411.11410)（ISSTA 2025） | 代码约束对文档约束；符号执行 + LLM | 对象是 API 文档，方向是文档中已写的约束 |
| [DocPrism](https://arxiv.org/abs/2511.00215) | 文档–代码不一致 | 指出 LLM 容易把文档与实现的自然差距当成不一致（消融中标记率 98%→14%），3b 的判定规则针对了这一点 |
| [ZeroFalse](https://arxiv.org/abs/2510.02534)、[LLM4PFA](https://arxiv.org/abs/2506.10322)、[IRIS](https://arxiv.org/abs/2405.17238) | 确定性分析 + LLM 复核 | 对象是漏洞告警；启发了 skeptic 复核 |
| Dude（见 `01_related_work_codeside.md`） | code→paper 方向 | 核对对象是描述，判定靠 LLM |

3b 的差异点：核对对象是**带条件的区域**；三个问题分开回答；证据必须逐字可查；不写的情况要主动验证。

## 实现

| 文件 | 作用 |
|---|---|
| `scripts/fetch_papers.sh` | 下载五篇 PDF 到 `third_party/papers/`，URL 固定版本 |
| `codeside/doc_index.py` | PDF 分节切段（处理双栏、页眉、参考文献），README / docstring / 注释建索引，BM25，逐字校验 |
| `codeside/scope_check.py` | scope 与评测覆盖，z3 求解；翻译不了就返回 `unknown` / `None`，不猜 |
| `codeside/verify3b.py` | 四种取证方法、复核、组装 Verification |
| `scripts/eval_3b.py`、`tests/fixtures/eval_3b_cases.json` | 答案已知的测试集 |
| `scripts/run_3b_dataset.sh` | 四篇开发集：路线 A → 3b |

取证方法（skill）：

| skill | 做法 |
|---|---|
| `retrieve` | BM25 + LLM 生成的论文措辞查询，判断候选段落 |
| `fullpaper` | 一条 limitation 对整篇论文 |
| `sweep` | 按章节通读，每章一次问全部 limitation |
| `consensus`（默认） | 跑以上三种，有人找到时由 skeptic 尝试反驳 |

README / docstring / 注释单独判断一层。除检索外，**定位点附近的注释和文档字符串强制进入候选**，因为作者常在限制旁边解释它，用词却和条件无关。

防止静默出错的规则：

- 非 `not_found` 的结果必须有逐字出现在所引段落中的 quote（最短 12 字符，不能有省略号），否则降级并记录。
- 存入的 quote 取自原文切片，不是模型的版本。
- 模型输出被截断、调用失败、三次都解析不出 JSON 时直接报错，绝不会变成"论文没提"。
- `temperature=0` 也不确定。多轮不一致时取多数，同时标 `needs_review`，不让多数票盖掉真实证据。

输出：`<out>.json` 是 Verification 列表；`<out>.detail.json` 还有各 skill 各轮结果、论文层和其他文档层各自的结论、校验失败记录、模型设置和用量。

```bash
scripts/fetch_papers.sh
python -m codeside.verify3b --limitations data/pilot_flexprefill/gold_code_limitations.json \
  --artifact data/pilot_flexprefill/artifact.json --pdf third_party/papers/flexprefill.pdf \
  --repo third_party/FlexPrefill --paper-side data/pilot_flexprefill/paper_side_stub.json \
  --model x-test-2 --repeats 3 --out out/3b/flexprefill.json
python scripts/eval_3b.py            # 约 5 分钟
scripts/run_3b_dataset.sh
```

论文版本：FlexPrefill arXiv v1、MInference arXiv v1（与固定的代码版本同期）、NNSmith arXiv v2、InfiniGen 和 SparTA 为 USENIX 官方版。

## 结果

模型 `x-test-2`（实际 `deepseek-v4.1-flash-1017`），`temperature=0`，prompt `3b-v3`。

### 答案已知的测试

| skill | 植入句：标签全对 | 植入句：找到 | 相似但不存在：误报 | 论文真实写过：命中 |
|---|---|---|---|---|
| retrieve | 23/27 | 25/27 | 0/8 | 7/7 |
| fullpaper | 23/27 | 24/27 | 1/8 | 7/7 |
| sweep | 22/27 | 24/27 | 1/8 | **3/7** |
| consensus | 23/27 | 25/27 | 0/8 | 7/7 |

- **四者差距多在 1–2 条，样本太小，不能说谁显著更好。** 只有 sweep 在真实正例上明显落后，不建议单独用。
- 默认用 consensus；要省 token 时 retrieve 是合理替代，这轮结果和 consensus 几乎相同。
- 错得多的是细分标签（`boundary_mismatch` 和 `contradicted` 混淆），"写没写"的判断更可靠。
- 已知盲点："我们没有评测过 X" 这种弱表述容易漏；skeptic 有误杀风险（曾以"这句像后来加的"否掉植入句）。
- 植入句写得比真实论文直白，所以这些数字**偏乐观**。

### Pilot（FlexPrefill，13 条，3 轮）

**论文层：13 条全部 `not_found`，3 轮完全一致。** 关键词独立核查也支持这一点（batch、dtype、GQA、flash_attn 等在论文中命中 0 次）。

稳定性（3 轮完全相同的条数）：retrieve、fullpaper、consensus 13/13，sweep 11/13，README / 注释层 11/13。

与**未评审草稿**对比：result 一致 8/13。scope 能判断的 4 条里一致 3 条，其余 9 条为 `unknown`。

| 条目 | 草稿 | 3b | 看法（待评审） |
|---|---|---|---|
| CL02 decode | found，无证据 | not_found | docstring 只写 "flash decoding"，未说是 dense。两种读法都说得过去；草稿没有 quote，过不了校验 |
| CL05 block_size=16 | contradicted | not_found，1/3 轮判对，`needs_review` | **3b 错了**：docstring 明写支持 16，而 kernel 拒绝 |
| CL06 短序列 | weaker，无证据 | not_found | 草稿靠"至少 1024 tokens"推断；那句是实验设置，3b 更严格 |
| CL09 triton | found（README 写 `triton==3.0.0`） | not_found | 只写版本要求，没写低版本的后果 |
| CL13 flash_attn | found（README 写 optional） | not_found | 草稿自己的理由也写着 "not the consequence" |

建议评审时明确：**依赖版本声明算不算写了这条限制？**

### 开发集

| 论文 | limitation 来源 | 结果 |
|---|---|---|
| MInference | 路线 A，11 条 | 全部 not_found |
| InfiniGen | 路线 A，4 条 | 全部 not_found |
| NNSmith | 路线 A 产出 0 条，手写 1 条（非可微退化） | 论文层 not_found，3/3 轮一致 |
| SparTA | 路线 A 产出 0 条 | 未验证 |

这里 scope 全部是 `unknown`，因为还没有论文侧数据。路线 A 的 limitation 里有不少内部断言（如 `q.dim() == 4`），论文本来就不会写，所以这些 not_found 不等于都是有价值的 finding，最后一步还要过滤。

NNSmith 这条：论文只把 Sampling 当作对比基线，没说非可微模型会退回它。代码注释里有 FIXME，模型对"这算不算写了"的判断不稳定。

## 需要团队处理的问题

1. **F02 的 scope 依据有误。** stub 的 S2 写 `block_size` 只有 128，依据是论文 "uses a block_size = 128 in all experiments"。但论文附录 F.2 比较了 64 和 128，并写道 "different block sizes can be flexibly selected according to different hardware"。用 stub 算，CL10 是 `out_of_scope`；把 S2 改成 {64, 128} 就是 `in_scope`。Zhaopeng 的步骤 1 需要覆盖这一点。**同时 Table 7 显示 64 和 128 表现接近，这可能削弱 F02 对准确率的担心**，要靠 Shanghao 的执行来确认。
2. **stub 太小，scope 大多判断不了。** batch_size、head_dim、dtype 没有 Binding，所以 9/13 是 `unknown`。这是如实结果，不是 bug，等步骤 1 的真实输出。
3. **注释算不算"已说明"**（`02_schema.md` 问题 1）。FIXME 把 NNSmith 这样的核心候选变成 `documented_elsewhere`，步骤 4 需要决定规则。
4. **决策表缺口**：3b 在论文正文 found 但论文侧没列出时，`03_codeside_spec.md` 4.2 没有对应类别。

## 未做 / 已知局限

- `Verification.result` 只有一个值。论文层和其他文档层各自的结论放在 `rationale` 和 detail 文件里；要结构化需要改 schema（M1）。
- 表格和图中的数字是提取文本，图里的文字基本不可用；scope 判断依赖论文侧的结构化数据。
- `path_prefix` 里翻译不了的条件被丢弃并记录，可能把 `out_of_scope` 判成 scope 内。
- 还没有和评审后的 gold 对比，因为 gold 还不存在（M1）。
- prompt 改过两版（原因写在 `verify3b.py`），都来自 pilot 错误。v3 没有修好 CL02，CL05 还变差了，所以没再继续调。
