# 步骤 4：整合成 Finding（2026-11-11，v2）

代码侧（步骤 2 + 3b）和论文侧（Zhaopeng 的交接包）合并成 Finding，交给 Shanghao 生成测试。
四件事：**去重、分类、设 priority、求 witness_hint**。规格见 `docs/03_codeside_spec.md` §4；本页记录实际做法、结果和待团队决定的问题。

## 怎么跑

```bash
# 1. 3b 用 Zhaopeng 的 paper_side.json 重跑（会调模型；有缓存时只付变化的部分）
python scripts/run_pipeline.py --out-dir out/pipeline_ps --seed-cache out/pipeline --parallel 1 --workers 3
# 2. 步骤 4（调模型做去重判断和论文侧条件；缓存在 out/step4_cache/，全命中时约 16 秒）
python scripts/run_step4.py              # 默认 --code-dir out/pipeline_ps --out results/step4 --model x-test-2
python scripts/run_step4.py --no-llm     # 不调模型：不做跨侧合并，论文侧没有条件
python scripts/make_handoff_doc.py       # 重新生成 results/step4/HANDOFF.md
python -m codeside.cli validate results/step4/*/findings.json
```

输出（`results/step4/`）：

| 文件 | 内容 |
|---|---|
| **`limitations_for_tests.json`** | **交给 Shanghao 的单文件**：每条 Finding 一条记录，自带 Finding 全部字段 + 背后完整的 Limitation 和 3b Verification |
| **`HANDOFF.md`** | **给 Shanghao 的说明**：两侧 limitation 长什么样、数量、字段、witness 怎么读、oracle 建议、例子、全部索引（`scripts/make_handoff_doc.py` 生成） |
| `review_queue.json` | 同样的 Finding，按 priority → 审阅状态 → 类别排好，一行一条 |
| `<论文>/findings.json` | 该篇 Finding 列表（schema v0.2.0） |
| `<论文>/findings.report.json` | 计数、规则、LLM 设置和用量 |
| `<论文>/llm_records.json` | 每一对“是不是同一件事”的全部投票和理由；每条论文侧条件及代码核对结果 |
| `summary.md` | 各篇汇总表 |

代码：`codeside/integrate.py`（去重、分类、优先级），`codeside/step4_llm.py`（两类 LLM 判断），
`codeside/witness.py`（witness_hint 求解），测试 `tests/test_step4.py`。

## 1. 去重

1. **代码侧之间**（不用 LLM）：同一函数里，条件规范化后相同、effect 相同的合成一条（`not (a == b)` 和 `a != b` 视为相同）。
2. **选候选对**（规则）：
   - 论文侧 × 论文侧：属于 Zhaopeng `finding_candidates.json` 的同一组，或代码证据完全相同；
   - 代码侧 × 论文侧：代码位置有重叠。
3. **判断是不是同一件事**（LLM，`x-test-2`，temperature 0，prompt `step4-v1`）：给两条记录的条件、效果、论文引文和代码原文。
   “同一件事” = 一个测试就能覆盖的同一个代码行为；同一函数里的两个不同检查、或“大的设计差异”和其中一个具体检查，都算不同。
   每对最多问 3 次，前两次一致就停；**两票 yes 才合并**。判断为同一件事的用并查集合并。
4. 候选对里判断为“不同”的，在两边 rationale 里写 `related (candidate pair, judged different)`，方便一起看。
5. Zhaopeng 的 `effect_text` 里有 63 条是“同上……”。它指的是 conformance.json 同一条的 `local_entry.discrepancy`，
   给 LLM 和写 summary 前先展开；交接文件里保留原记录。

## 2. 分类（schema v0.2.0，7 类）

| 类别 | 来源 | 什么时候 |
|---|---|---|
| `undisclosed` | 代码侧 | 3b not_found；或找到的证据按下面规则都不算 |
| `contradicts_docs` | 代码侧 | 3b contradicted，且证据算数 |
| `stated_differently` | 代码侧 | 3b boundary_mismatch 或 weaker（写了，但边界不同或说得更弱） |
| `docs_only` | 代码侧 | 3b found，证据只在 README / 公开 docstring / 其他用户文档 |
| `paper_stated` | 代码侧 | 3b found，论文或附录里有 |
| `impl_deviates` | 论文侧 | 3a deviates |
| `not_implemented` | 论文侧 | 3a absent |

**“算不算写了”只有一条规则**：用户会读到的地方才算——论文（含附录）、README、其他用户文档、公开函数的 docstring。
代码注释（包括 TODO/FIXME）、`_` 开头函数的 docstring、只写了版本号的句子都不算。不再有开关。

合并后的 Finding 有多个代码侧类别时，取最能说明“用户不知道”的那个（contradicts_docs > undisclosed > stated_differently > …），
论文侧的类别写在 rationale 的 `paper side also reports` 里。

## 3. 设 priority（后果 × 能不能触发）

| priority | 条件 |
|---|---|
| 3（直接） | scope 为 out_of_scope；witness 判为走不到（infeasible）；审阅为 wrong |
| 1 | 类别是 undisclosed / contradicts_docs，后果严重（reject / accuracy / state），且 witness 能触发 |
| 2 | 上面那种但后果中等（path_change / resource / performance）或能不能触发未知；或类别是 stated_differently / impl_deviates |
| 3 | 其余（docs_only、paper_stated、not_implemented、后果为 other 的） |

- “能触发”= witness 状态为 solved / solved_contrast_outside_scope / trigger_only / always。
- `--strict-scope`：scope 未知的不能进 1（四篇论文侧目前几乎没有参数映射，默认不开）。
- 合并的 Finding 取各成员类别里最高的 priority。
- **审阅状态** `review`：`worth_testing` / `real_but_minor` / `wrong` / `unreviewed`，先用盲审标签填
  （`results/review/blind_review_labels.json`，Claude 子代理盲审，**不是人工**，`review_note` 里写明）。只有代码侧有标签。

## 4. 求 witness_hint（格式 `witness-v2`）

目标：给出边界两侧各一个点。`trigger` 走限制分支，`contrast` 是离它最近、但不走限制分支的点。
两点都满足路径前缀；被 Binding 映射到论文 scope 的名字，两点都在 scope 内；scope 没约束的名字优先取论文 EvalPoint 的值。

```json
{
 "format": "witness-v2",
 "kind": "input_value",              // 或 event_sequence（effect=state：要先通过前几次调用把状态弄成 trigger）
 "status": "solved",
 "condition": "q_len != k_len",
 "path_prefix": [],
 "dropped_prefix": [],               // 翻译不了、没参与求解的前缀
 "aliases": {"q_len": "q.shape[1]", "k_len": "k.shape[1]"},     // v2 新增
 "trigger":  {"q_len": 1, "k_len": 2, "q.shape[1]": 1, "k.shape[1]": 2},
 "contrast": {"q_len": 2, "k_len": 2, "q.shape[1]": 2, "k.shape[1]": 2},
 "atoms": {"q_len": {"kind": "local", "sort": "int"}, "q.shape[1]": {"kind": "derived", "sort": "int"}},
 "from_paper": {"tau": "scope sparse_pattern_threshold_tau: [0.0, 1.0]"},
 "eval_preference": {"tau": 0.1, "block_size": 128},
 "location": "flex_prefill/ops/vertical_slash_attention.py:265",
 "function": "flex_prefill/ops/vertical_slash_attention.py::..."
}
```

**v2 相对 v1 的变化**

1. **别名**：从检查所在函数里找“只赋值一次、在检查之前”的局部变量（`q_len = q.shape[1]`、`b, n, h, d = q.shape`），
   加等式 `q_len == q.shape[1]`。这样两个名字取同一个值，测试按 `q.shape[1]` 造张量就行。
   - 路径前缀会混入调用链上各层函数的条件（调用者的 `q` 和被调用者的 `q` 不是同一个张量），别名只在单层时用：
     检查就在入口函数里，或没有路径前缀。否则别名只列在 `aliases_not_applied` 里供参考，不参与求解。
   - 如果加了别名反而无解，就去掉别名重解，记在 `aliases_dropped`。
2. **论文侧也有条件**：LLM 读论文侧记录和引用的代码，写出“这个差异在什么输入下出现”的 Python 条件，或回答
   `always`（每次调用都会出现，如公式不同、功能缺失）/ `not_input`（取决于硬件、构建等）。
   **用代码核对**：条件里的每个名字都必须出现在引用的代码行里，否则拒收（`rejected`）。通过的交给同一个求解器，
   记录 `condition_source`。

`atoms` 说明每个名字是什么、测试要怎么造它：

| kind | 例子 | 含义 |
|---|---|---|
| input | `head_dim` | 普通名字，直接给值 |
| local | `q_len`（有别名时） | 局部变量，值由 `aliases` 里的表达式决定 |
| derived | `q.shape[1]`、`len(x)`、`self.layer_id` | 由输入算出来的值，测试要构造出这个值 |
| predicate | `is_flash_attn_2_available()`、`x is None` | 真假值，测试要安排（mock 或选输入） |
| category | `q.dtype`（和 `torch.bfloat16` 比较） | 字符串或枚举；`{"not_in": [...]}` 表示“列出的值以外的任意一个” |

| status | 含义 |
|---|---|
| solved | 两点都有 |
| solved_contrast_outside_scope | contrast 只能取在论文 scope 外 |
| trigger_only | 条件在路径上恒成立，没有 contrast |
| always | 论文侧：每次走到引用代码都会出现，任何到达那里的输入都是 witness |
| infeasible | 条件和路径前缀矛盾，从入口走不到（priority 降为 3） |
| untranslatable | 条件不是可翻译的 Python 表达式 |
| unknown | 求解超时 |
| no_condition | 论文侧：LLM 没给出可用条件（not_input 或核对不通过），只有代码位置和文字 |

`closest: false` 表示用的是退路求解（含非线性项），两点有效，但不保证最近。

## 结果（五篇）

| 论文 | Limitation（代码+论文） | Finding | 两侧合并 | undisclosed | contradicts | stated_diff | docs_only | paper_stated | impl_deviates | not_impl | p1/p2/p3 | witness 可用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FlexPrefill | 46+21 | 65 | 0 | 34 | 0 | 6 | 6 | 0 | 9 | 10 | 16/22/27 | 57/65 |
| InfiniGen | 20+12 | 31 | 0 | 19 | 0 | 1 | 0 | 0 | 9 | 2 | 8/18/5 | 30/31 |
| MInference | 50+32 | 73 | 0 | 50 | 0 | 0 | 0 | 0 | 15 | 8 | 19/37/17 | 70/73 |
| NNSmith | 36+6 | 38 | 2 | 32 | 1 | 1 | 0 | 1 | 3 | 0 | 8/22/8 | 38/38 |
| SparTA | 3+103 | 82 | 1 | 2 | 0 | 0 | 1 | 0 | 47 | 32 | 0/49/33 | 77/82 |
| **合计** | 155+174 | **289** | 3 | | | | | | | | 51/148/90 | 272/289 |

- **去重**：329 条 limitation → 289 条 Finding。代码侧机械合并这次没有命中（155 条在步骤 2 的 dedup 里已去过重）；
  LLM 判了 553 对候选，合并主要发生在论文侧之间（174 → 135 条纯论文侧 Finding，SparTA 103 → 79）。两侧真正合成一条的只有 3 个
  （NNSmith 零梯度检查、搜索时间预算；SparTA 单一 block size）。其余候选对判为“相关但不同”，在 rationale 里互相链接。
- **witness**：可用 272/289（solved 176、always 89、trigger_only 7）；infeasible 8、no_condition 9。
  别名在 19 条上参与求解，52 条因跨层只列出不用。论文侧 135 条条件里被代码核对拒收 7 条。条件通过核对只说明名字对得上，语义不一定对（例子见 `results/step4/HANDOFF.md`）。
- **priority**：p1 51 条，其中盲审 worth_testing 6、real_but_minor 11、未审 34。**审阅状态仍要人看**：盲审只覆盖了
  一部分代码侧条目，而且不是人工。
- LLM 用量（含一次因“同上”展开的重跑）：约 1080 次调用，约 170 万输入 token、6 万输出 token；缓存全命中时重跑 16 秒。

### 和 pilot 草稿 F01–F07 对照（草稿未评审，只作参考；草稿已迁到新类别名）

| 草稿 | 草稿类别 / 优先级 | 生成结果 | 一致？ |
|---|---|---|---|
| F01 `q_len != k_len` | undisclosed / 1 | F013 undisclosed / 1 | 一致 |
| F02 硬编码 `// 128` | undisclosed / 1 | F050 undisclosed / 3 | 类别一致；effect 抽成 other，所以 3。论文侧 M08-B05/B06 也指这一行，但 LLM 判为“更大范围的阈值语义差异”，未合并，只链接 |
| F03 模块级 causal_mask 缓存 | undisclosed / 1 | 无 | 步骤 2 没抽出（状态类） |
| F04 head_dim 不支持 | undisclosed / 2 | F014 undisclosed / 1 | 类别一致；reject + 能触发 = 1 |
| F05 只支持 bf16 | docs_only / 2 | F022 stated_differently / 2 | 3b 判 weaker（文档说得比代码弱） |
| F06 block_size 16 | undisclosed / 3 | F054 docs_only / 3 | 3b 找到公开 docstring “only support 16, 32, 64 and 128” |
| F07 batch size > 1 | docs_only / 3 | F052 docs_only / 3 | 一致 |

类别 4/6 一致，优先级 4/6 一致。

## 对 Shanghao 10 条的处理

| # | 问题 | 状态 |
|---|---|---|
| 1 | 步骤 4 没实现 | 已实现：去重、分类、priority、witness 四步，单文件 `limitations_for_tests.json` |
| 2 | witness_hint 没格式、没求解器 | `witness-v2` + z3；别名、论文侧条件已补；格式等 Shanghao 确认 |
| 3 | M1 没开、schema v0.2.0、F01–F07 没评审 | schema v0.2.0 草稿已做（7 类 + review 字段），待开会确认 |
| 4 | 候选没人工筛 | `review` 字段先用盲审填，人工筛仍要做 |
| 5 | “没写”不等于值得测 | priority 改为“后果 × 能触发”；`review_queue.json` 按 priority → 审阅状态排 |
| 6 | “算不算写了”没定 | 统一规则：只算用户会读到的地方（见上），待团队确认 |
| 7 | 四篇区域 gold 没标 | 要人工，未做 |
| 8 | 路线 A 没降噪 | 未做（M2a）；infeasible 的已自动降为 3 |
| 9 | 入口函数没确认 | 要团队确认，未做 |
| 10 | 被测仓库和 PDF 不在 git | 见下 |

### 环境（第 10 条）

```bash
cd cs6223-limitation-pipeline
scripts/fetch_dataset.sh   # 按 data/*/artifact.json 克隆五个仓库到固定 commit（third_party/）
scripts/fetch_papers.sh    # 下载五篇 PDF（arXiv 固定版本 / USENIX），打印 sha256 前 16 位
```

已核对：五个仓库本地 HEAD 和 `data/*/artifact.json` 的 commit 一致；Zhaopeng 交接包里 `artifact.json` 的 commit 也一致。
本机 PDF 的 sha256 前 16 位：flexprefill `d2240298d13ad238`、infinigen `638e3f536447ce7f`、minference `b061e544a499c1e1`、
nnsmith `0e297c1b5859fcd7`、sparta `dee06b8df674fcc7`。

## 待团队决定

1. schema v0.2.0：7 类、`review` / `review_note` 字段（`docs/02_schema.md`）。
2. witness_hint 格式 `witness-v2` 是否可用（Shanghao）。
3. “算不算写了”的统一规则。
4. priority 规则；scope 未知时能不能进 1（现在默认能）。
5. 去重的 LLM 判断标准：“大的设计差异”和“其中一个具体检查”算不算同一件事（现在算不同，只链接）。
6. 论文侧需要补参数映射（Binding kind=parameter），否则 scope 和 witness 的论文约束在四篇上都是空的。
7. 原 M1 的其他问题（TestCase 是否加环境字段、是否加 `alternative` 结局）。
