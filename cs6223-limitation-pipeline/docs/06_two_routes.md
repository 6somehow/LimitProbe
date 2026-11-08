# 步骤 2 的两条技术路线与对比协议

步骤 2（代码侧找 limitation）同时实现两条路线，最后在同一套 gold 上对比。

| 路线 | 做法 | 代码 | 状态 |
|---|---|---|---|
| **A 静态分析（不用 LLM）** | Python `ast` 读代码，按规则抽取条件和结局 | `codeside/extractor.py` | v0 可用，M2a 改进 |
| **B 静态 + LLM（2026-11-05 改为此定义）** | A 产出候选，LLM 只负责找 A 找不到的：补调用边、补漏报；**不删除 A 的任何结果**；LLM 的每个结论都由代码校验 | `codeside/hybrid_extractor.py` | 已在 pilot 和四篇上运行 |
| B-agent：自由探索 | A 的结果全部保留；LLM 用只读工具（列目录、grep、读文件）自己探索整个 repo，上报的结果由代码校验 | `codeside/agent_extractor.py` | 已在 pilot 和四篇上各跑 3 次（`agent-v2`） |
| B-sweep：分块通读 + 复核 | A 的结果全部保留；代码按 import 关系选文件（入口文件、它 import 的两层、import 它的一层），切块后每块问一次 LLM；结果由代码校验，再经相关性复核只保留“论文机制的限制” | `codeside/sweep_extractor.py`、`codeside/relevance_filter.py` | 已在 pilot 和四篇上各跑 3 次（`sweep-v2` + `relevance-v1`） |
| 对照组：纯 LLM | 把入口及可达函数的源码（带 `file:line`）一次交给 LLM | `codeside/llm_extractor.py` | 只作对照，不是候选方案 |

## 路线 B 的设计

```
路线 A 候选 ─> 1. 补调用边 ─> 重跑 A ─> 2. 补漏报 ─> 区域表
```

| 阶段 | LLM 做什么 | 代码如何校验 | 依据 |
|---|---|---|---|
| 1. 补调用边（最多 2 轮） | 为 A 解析不了的调用（`Class.method(self)`、继承、`obj.method()`）选择目标 | 候选由代码从仓库定义里列出，只能从中选；外部库调用不发给 LLM | SEA（静态候选 + LLM 筛选）；Python 调用图研究显示 LLM 不宜单独产出边 |
| 2. 补漏报（逐函数） | 找 A 的规则漏掉的行为切换 | 代码引用须在该行，条件须能解析且名字都在函数里；同一行已有区域视为重复 | RepoAudit（逐函数 + 校验器） |

失败处理：解析失败或 API 出错重试 3 次，仍失败就保留 A 的结果并记入 `failed_calls`，不会当作空结果。

已知局限：A 的多报（如不可达路径）会原样保留，由 M2a 的确定性规则处理。`alternative` 结局还没进 schema，切换实现暂时标为 mechanism_variant。

Prompt 版本：`hybrid-v1` 在 pilot 上跑过一次，补漏报噪声较多；`hybrid-v2` 收紧了补漏报的范围（排除性能调参、默认值、兼容分支等），这次修改看过 pilot 结果，所以 pilot 数字不算未调参结果。`hybrid-v3` 去掉了让 LLM 删除 A 结果的步骤（v2 在开发集上误删过一条真实限制，且删除无法由代码验证），补漏报的 prompt 与 v2 相同；当前结果都来自 v3。

## B 的三种做法对比（2026-11-06）

新增结果由 Claude subagent 对照源码盲审（不告诉它来源），分三类：有用 / 真的但没用 / 错的。
单个审稿人、样本小，比例只能看大致趋势。

| 做法 | 每篇每次新增 | 3 次一致性（Jaccard） | 每次 token | 盲审：有用 | 错的 |
|---|---|---|---|---|---|
| 路线 B（hybrid-v3） | 0–40 | — | 约 2 万/入口 | 4/48（8%） | 4 |
| B-agent（agent-v2） | 0–39 | 0.07–0.33 | 35–84 万 | 21/54（39%） | 11 |
| B-sweep 未复核（sweep-v2） | 1–130 | 0.64–0.82 | 11–18 万 | 4/49（8%） | 4 |
| B-sweep + 复核 | 1–38 | 0.55–0.76 | 再加约 10 万 | **10/46（22%）**，新样本 | 2 |
| B-agent + 复核 | 0–29 | 0.11–0.33 | 再加约 3 万 | 第一轮样本上 20/36（56%） | — |

相关性复核（`relevance-v1`）在第一轮 144 条已审结果上：有用的 26 条保留 25 条，其余 118 条删掉 79 条。
复核和审稿用的是同一套标准，这个一致性偏乐观；22% 来自没参与过评估的第 2 次运行样本，更可信。

结论：
- **分块通读覆盖最稳**，但大量结果是基线方法（StreamingLLM、vertical-slash、FlexGen top-k、dilated）、
  搬运/调度细节和同一检查在多个 kernel 里的重复。复核能去掉大半，剩下的主要是这两类。
- **自由探索精度最高**，能去 import 图到不了的地方（SparTA 的 7 条有用结果都来自它），但不稳定、贵。
- 两者结果重合少，适合合并：分块通读负责入口附近查全，自由探索负责远处。
- 所有做法的 FlexPrefill recall 都是 16/16，继承自 A，不能用来区分 B 的做法。

### 最终的 B：分块通读 + 自由探索，复核后合并去重

```
A ─┬─ sweep ─ 复核 ─┐
   └─ agent ─ 复核 ─┴─ 合并 ─ 去重（codeside/dedup.py，不用 LLM）─ A + B 新增
```

去重只作用于 B 的新增，A 一条不删：
1. **上游已检查**：函数的所有调用方（按名字建的调用图，同名定义超过 3 个就不算）都已经检查过同一条件，则删掉内层这条。
2. **同一文件同一开关**：B 新增之间条件和结局相同的，留第一处，其余位置写进 notes；和 A 的条件相同但在别的函数里（比如 HF 版和 vLLM 版），保留并注明。
条件比较前先归一化（`not (a == b)` 等于 `a != b`）。

| 论文 | 3 次新增数 | 3 次一致性 | 3 次都有 |
|---|---|---|---|
| FlexPrefill | 17、18、19 | 0.64 | 12 |
| InfiniGen | 16、12、15 | 0.57 | 9 |
| MInference | 39、38、44 | 0.50 | 23 |
| NNSmith | 36、33、38 | 0.41 | 16 |
| SparTA | 3、4、15 | 0.21 | 1 |

盲审（第 3 次合并结果中从没审过的 38 条）：**有用 12（32%）**，真的但没用 20，错 6。
没加“死代码”规则：3 条错误是 NNSmith 里从没被实例化的 `GuidedGen`，但“仓库里没人调用”不等于用户用不到（库的公开接口），自动删会误删。

结果目录：`out/routes_sweep/`（未复核）、`out/routes_filtered/`（复核后，含 sweep 和 agent）、`out/routes_merged/`（最终）。
软链接：InfiniGen 的 `flexgen/flexgen/pytorch_backend.py` 指向入口文件，scope 按真实路径去重（第一次运行的结果留在 `out/routes_sweep_v2_symlink_dup/`）。

## 为什么两条都做

- 相关工作里两种做法都有：SymPrompt、RepoAudit 一类用程序分析抽结构；SciCoQA、Dude 一类让 LLM 直接读代码。
- 哪条更好不能靠论证，只能靠实验。对比结果本身就是报告里的一张表，也直接回答"确定性抽取有没有必要"。

## 公平对比的规则

1. **同样的输入**：B 看到的代码，正好是 A 从同一个入口能走到的那些函数（`collect_context` 复用 A 的调用解析）。如果要测"LLM 自由探索"，另做一个变体 B-agent，单独列一行。
2. **同样的输出格式**：都产出 `Region` 记录，provenance 分别是 `ast` 和 `llm`。
3. **同样的校验**：函数必须在上下文里、行号必须落在该函数内、条件必须能解析成 Python 表达式、结局必须是已知类别。不合格的条目计入"被拒绝"，不直接丢掉。
4. **同样的 gold 和匹配规则**：同文件、同函数、同结局、行号误差 ≤ 2。
5. **固定并记录 LLM 设置**：模型 ID、temperature = 0、prompt 版本（`llm_extractor.py` 里的 `SYSTEM` 和 `USER_TEMPLATE`）、上下文长度。
6. **LLM 路线每个入口跑 3 次**，报告平均值和波动。

## 对比指标

| 指标 | 含义 | 来源 |
|---|---|---|
| recall | 找到了多少条 gold 区域 | `compare` 命令 |
| extra | 多报了多少条；之后人工复核，分为"gold 漏标"和"噪声" | `compare` + 人工 |
| cond_exact | 匹配上的区域里，条件表达式与 gold 一致的比例（"边界抓得准不准"） | `compare` |
| rejected / 幻觉率 | LLM 输出中未通过校验的比例（行号不存在、条件不能解析等） | `.meta.json` |
| 稳定性 | 3 次运行匹配到的 gold 集合的重合度 | 脚本统计 |
| 成本 | token 数、耗时；A 路线几乎为零 | `.meta.json` + 计时 |
| 下游可用性 | 条件能否直接用于 3b 的 scope 求交和 witness 求解（能解析、名字能通过 Binding 映射） | 步骤 3b / 4 统计 |

结果按 artifact、按结局类型、按开发集 / held-out 分开报告。

## 命令

```bash
# 路线 A
python -m codeside.cli extract --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --out out/static.json

# 路线 B（需要 pip install -e ".[llm]"，以及 .env 里的 SOCLAAS_API_KEY、SOCLAAS_BASE_URL；--provider anthropic 改用 Anthropic）
python -m codeside.cli extract-hybrid --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/hybrid_run1.json

# B-agent：自由探索整个 repo（--entry 可重复；每次最多 60 步、80 万 token）
python -m codeside.cli extract-agent --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/agent_run1.json

# B-sweep：分块通读（--entry 可重复）；复核可接在任何 B 结果后面，A 的结果不会被删
python -m codeside.cli extract-sweep --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/sweep_run1.json
python -m codeside.cli filter --regions out/sweep_run1.json --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --model x-test-2 --out out/sweep_run1_filtered.json

# 最终的 B：合并复核后的 sweep 和 agent，并去重
python -m codeside.cli merge out/sweep_run1_filtered.json out/agent_run1_filtered.json \
  --repo third_party/FlexPrefill --out out/b_final_run1.json

# 对照组：纯 LLM
python -m codeside.cli extract-llm --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/llm_run1.json
#   同时写出 out/llm_run1.meta.json：实际模型（resolved_model）、被拒绝的条目、幻觉率、上下文大小

# 对比
python -m codeside.cli compare --gold data/pilot_flexprefill/gold_regions.json \
  --pred static=out/static.json --pred llm1=out/llm_run1.json
```

当前 pilot 上路线 A 的结果：

```
route   pred  recall  extra  cond_exact  rejected  halluc_rate
static  30    16/16   10     13/13       -         -
```

批量运行全部入口（A 一次，B 和对照组各 3 次）：`python scripts/run_routes.py --model x-test-2`；
B-agent 每篇论文 3 次：`python scripts/run_routes.py --model x-test-2 --mode agent`（结果在 `out/routes_agent/`），
B-sweep：`--mode sweep`（结果在 `out/routes_sweep/`），
汇总：`python scripts/summarize_routes.py`，一致性：`python -m codeside.cli stability <runs...>`。
更严格的匹配：`compare` / `evaluate` 加 `--tol 0 --one-to-one`。

## 注意

- **gold 的条件必须用代码里的原始名字和写法**（比如写 `math.ceil` 而不是 `ceil`），否则 cond_exact 会误判。
- **cond_exact 目前只是文本比较**（会把 `not (a == b)` 和 `a != b` 视为相同），以后可以换成 z3 判断等价。
- **路线 A 的规则是对着 FlexPrefill 写的，路线 B 的 prompt 不要对着 gold 反复调。** 否则对比就不公平。prompt 每改一版都记录下来。
