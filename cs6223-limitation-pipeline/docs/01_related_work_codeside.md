# 代码侧相关工作（步骤 2、3b、4）

完整调研见项目文档 `claude/related-work-survey.md`。这里只保留和代码侧直接相关的部分。
2026 年的预印本（Dude、CASCADE、SeGa 等）引用前请核对发表信息。

## 1. 仓库分析：现有工作怎么做

| 做法 | 代表工作 | 从哪开始 | 怎么探索 | 结论怎么确认 |
|---|---|---|---|---|
| 整仓库塞进 context | SciCoQA 评测 | 不选 | 不探索 | LLM |
| 通用 agent + 文件工具 | Dude、SWE-agent、Agora | LLM 自定 | grep / read 循环 | LLM（Dude 用多 agent 协商） |
| 已知单元逐个读 | WhiteFox | 优化注册表枚举 | 只读该单元源码 | 插桩确认触发 + 开/关差分 |
| 程序分析抽结构喂 LLM | SymPrompt、TELPA、KernelGPT、Ciri | AST、调用图、handler 抽取 | 抽路径条件 / 调用链；KernelGPT 迭代追问缺失定义 | 执行 / fuzzer |
| 静态分析驱动 + LLM 按需 | RepoAudit、LLMDFA、IRIS | tree-sitter 规则定位 source | 逐函数、带记忆、按需扩展 caller/callee | 验证器 / 求解器 |

要点：

- **SciCoQA** 的"整仓库塞进去"随长度明显变差：266 篇里 70 篇加代码超过 100K tokens，recall 随长度下降（[arXiv 2601.12910](https://arxiv.org/html/2601.12910v1)）。
- **RepoAudit**（ICML 2025）：initiator 用 tree-sitter 找 source，explorer 一次分析一个函数并存记忆，validator 检查路径条件可满足性；15 个项目上精度 78.43%（[arXiv 2501.18160](https://arxiv.org/html/2501.18160v3)）。**我们的抽取器沿用这个结构**，只是把 source 从"bug 模式"换成"论文机制入口"。
- **LLMDFA**（NeurIPS 2024）：LLM 写脚本调用解析库抽 source/sink，路径可行性交给定理证明器（[arXiv 2402.10754](https://arxiv.org/abs/2402.10754v2)）。启示：LLM 生成检查，工具执行检查。
- **SymPrompt**：用 AST 收集每条返回路径上的分支条件；人工检查只有 6/10 的测试真的走了目标路径（[arXiv 2402.00097](https://arxiv.org/html/2402.00097v2)）。启示：路径是否被触发必须由执行回答。
- **Agora**（ICML 2026）：普通 ReAct 读代码 agent 找到 0 个协议逻辑 bug，加入挖掘出的 bug 模式后找到 15 个（[arXiv 2605.29910](https://arxiv.org/pdf/2605.29910)）。启示：自由漫游不够，需要外部知识告诉它看哪里——我们用论文。
- **WhiteFox**（OOPSLA 2024）：读优化源码总结触发条件，插桩确认触发，开/关差分；101 个 bug（[arXiv 2310.15991](https://arxiv.org/html/2310.15991v3)）。能"逐个读"是因为优化可从注册表枚举，研究原型没有注册表。

## 2. 代码 → 论文核对（3b）

- **SciCoQA**：把"代码有、论文没写"叫 Paper Omission，是最难的一类，占复现报告差异的 50%；**它的定义排除了 bug、可由配置修正的超参数不一致和琐碎工程细节**——恰好是我们关注的阈值、fallback、配置限制。系统领域也不在它的覆盖范围内。
- **Dude**（arXiv 2609.03416，预印本）：code→paper 方向由 code claimer 抽取"值得注意的实现"，再由 paper verifier 回论文核对，加 anchor / relevance 过滤；SciCoQA 上 F1 86.55（GPT-5.4）。只用 grep/glob/read 静态查看，判定靠 LLM。**这是 3b 最直接的对照**：我们的区别是 (a) 核对对象是带条件的区域而不是描述，(b) 判断 scope 和是否被评测，(c) 产出 witness。
- **NeurIPS 2026 agentic code audit**（Iversen 等）：87 篇论文、609 条差异，约一半由 agent 写的可执行检查支撑（[poster](https://neurips.cc/virtual/2026/poster/157023)）。
- **CASCADE**（FSE 2026，预印本）：从函数文档列出 "if [condition] then [behavior]"，生成并运行测试，再用"按文档重新生成实现"做差分过滤；P 0.88 / R 0.21（[arXiv 2604.19400](https://arxiv.org/pdf/2604.19400)）。和我们的"条件 → 影响"结构一致，但粒度是单个函数。
- **SeGa**（ISSTA 2026，预印本）：约 30% 的报告被团队认定为有意为之（[arXiv 2604.23509](https://arxiv.org/pdf/2604.23509)）。启示：3b 和步骤 4 必须区分 bug、未声明的限制和合理的工程取舍。
- **RFC → 约束**（Liu 等）：LLM 从文本里恢复约束的 recall 只有约 17%（独立约束）和 0%（依赖约束）（[alphaXiv 2511.17977](https://www.alphaxiv.org/abs/2511.17977.md)）。启示：**阈值从代码里挖，论文只用来判断范围和意图**。

## 3. 配置与阈值

- **ctest**（OSDI 2020）：在目标配置下重跑已有测试，复用其断言；62/64 真实配置故障（[PDF](https://www.usenix.org/system/files/osdi20-sun.pdf)）。研究原型通常没有测试套件，所以我们必须自己生成 witness。
- **Ciri**：LLM 静态判断配置是否有误，跨参数依赖类错误 F1 只有约 0.3（[arXiv 2310.09690](https://arxiv.org/html/2310.09690v2)）。启示：配置依赖型区域（例如 FlexPrefill 的 `min_budget` 决定 fallback 边界）不能交给 LLM 判断。
- **DocTer**（ISSTA 2022）：从 API 文档挖约束，生成合规、违规和边界输入（[arXiv 2109.01002](https://arxiv.org/html/2109.01002v4)）。我们的 witness_hint 生成是同一思路，只是约束来自代码。

## 4. 工具选型

| 工具 | 用途 | 状态 / 备注 |
|---|---|---|
| Python `ast`（标准库） | v0 抽取器：条件、assert、调用、行号 | 零依赖；`ast.unparse` 需要 Python 3.9+ |
| LibCST | 需要保留格式或改写代码时（如做变异体） | 留给 Shanghao 的变异测试 |
| tree-sitter | 多语言（C++/CUDA 调用层） | 需要时再引入 |
| PyCG | Python 调用图 | **2023-11-26 已归档、不再维护**（[GitHub](https://github.com/vitsalis/PyCG)），不作为依赖 |
| Scalpel | Python 静态分析框架（CFG、调用图） | [GitHub](https://github.com/SMAT-Lab/Scalpel)；可作为调用解析的备选 |
| z3-solver | 区域 ∩ scope 求交、路径可行性、witness 求解 | `pip install z3-solver`；简单区间可先手写 |

## 5. 对代码侧设计的结论

1. 种子由论文给（Binding 的机制入口），探索按函数、带记忆，判定交给 AST 和求解器。
2. 3b 的判定拆成三个独立问题：文档里有没有写（检索 + LLM，quote 必须逐字可查）、在不在 scope 内（确定性）、有没有被评测（确定性）。
3. 输出必须可复核：每条 Region 带 file:line 和原始条件表达式；每条 Verification 带 verbatim quote。

## 6. 路线 B（静态 + LLM）的设计依据

| 工作 | 做法 | 用在路线 B 的哪里 |
|---|---|---|
| [IRIS](https://arxiv.org/html/2405.17238v3)（ICLR 2025） | LLM 补 CodeQL 的规格，再带路径上下文判断每条告警 | 曾用于删多报（hybrid-v2），v3 已去掉 |
| [ZeroFalse](https://arxiv.org/html/2510.02534v1)（预印本） | 把分析器告警连同流迹和上下文交给 LLM 裁决 | 曾用于删多报（hybrid-v2），v3 已去掉 |
| [LLM4PFA](https://arxiv.org/abs/2506.10322)（预印本） | LLM agent 判断路径是否可行以过滤误报 | 曾用于不可达判定（hybrid-v2），v3 已去掉 |
| [RepoAudit](https://icml.cc/virtual/2025/poster/45170)（ICML 2025） | 逐函数按需探索，校验器防幻觉 | 补漏报逐函数进行，并校验输出 |
| [SEA](https://themoonlight.io/review/semantic-enhanced-indirect-call-analysis-with-large-language-models) | 静态分析给候选目标，LLM 筛选（面向 C 的间接调用） | 补调用边只能从真实定义里选 |
| [LLM 调用图实证研究](https://arxiv.org/pdf/2410.00603) | Python 调用图上 PyCG 总体优于 LLM，LLM 只在部分情况补到边 | 不让 LLM 自由产出调用边 |
| [Datadog 的误报过滤](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives.md) | 工程实践：提高过滤力度会增加漏掉真问题的风险 | 删除有漏掉真问题的风险，v3 改为不删除 |

以上内容来自搜索结果和摘要，尚未逐篇细读全文，写报告前请核对。
