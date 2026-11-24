# 五个开发案例的静态扫描审计

审计日期：2026-10-01。使用 bundled Python、`PYTHONPATH=src`、默认 500 files / 256000 bytes 上限，只调用本项目的 AST/lexical scanner 和排序函数；没有 import 或执行目标仓库代码，没有调用模型，没有运行 CUDA/kernel。以下数量是语法条件的数量，不是可运行测试或 bugs。

## 证据和上下文池

五个仓库 HEAD 都与 catalog 固定 commit 一致；全仓库初始扫描没有截断、过大文件或解析错误。全部 6124 条条件的 quote 都在声明的源码行范围中，UTF-8 SHA256 都匹配。AST 对个别第三方字符串给出 SyntaxWarning，但未执行该源码。

| 案例 | 初始 files / conditions | 初始前 12 条的主要风险 | 冻结范围 files / conditions | 冻结范围 pool / 12 |
| --- | ---: | --- | ---: | ---: |
| MInference | 184 / 2030 | LeanK benchmark、distributed-attention 返回值兼容分支、XAttention 混入 | 6 / 51 | 8 |
| SparTA | 48 / 215 | 库组件相对集中，但 8/12 是 dict、shape、modulo 或 reduction 表达式 | 22 / 132 | 12 |
| InfiniGen | 46 / 1332 | H2O、UVM dense attention、evaluation loop、FlexGen compression 混入 | 5 / 179 | 7 |
| ALEX | 16 / 217 | 都在 core，但主要是内部 state/counter/model gate | 6 / 196 | 12 |
| FlashAttention-2 | 270 / 2330 | ft_attention、xentropy、linear、kernel-generator main gate 混入 | 16 / 172 | 12 |

冻结范围见 [discovery-scopes.json](/Users/pp/Desktop/nus/cs6223/paper-guided-testing/configs/discovery-scopes.json)。全部 include_paths 已检查存在；缩小范围后的 730 条 quote/hash 也全部通过；仍无截断或解析错误。

范围依据库组件角色与论文版本兼容性制定，没有使用 issue、known-bug/gold location、condition ID、行号过滤或生成结果。MInference 保留原论文 pattern family 的现有 sparse/streaming kernels；SparTA 保留 TeSA/specializer；InfiniGen 保留作者 controllers 与两个 ours 模型集成模块；ALEX 保留 src/core；FA2 保留 API 与通用 kernel headers，排除同目录的 offline generator。FA2 使用文件级组件清单，避免目录范围将 generator 一起包含。

这轮应称为 **在人工冻结库组件范围中的 guided candidate synthesis**。不能称为全仓库自动发现；不能将当前仓库 commit 说成原论文实验 commit。MInference 的当前 v2 kernel 含 2024–2025 integration 更新，范围只对应原论文算法 family，不覆盖后续算法或完整 offline pattern search。

## 五项实质发现

1. **共享排序没有读取论文，却存在强烈的仓库角色噪声。** `condition_priority` 只按 path/kind/literal 加分，没有读取 profile、issue 或 gold。其 `attention/kernel/cache/index` 词表仍是人工领域先验，且会优先选择同仓库中的新算法或对照实现。初始 pool 的无关条件影响所有方法，不构成 Full 独占信息泄漏；人工冻结范围及这一先验必须在方法章节披露。

2. **抽取条件不是外部参数，也不代表有执行影响。** SparTA 的 `params['BLOCK_SIZE_M_VALUE']`、`len(x.shape)`、`N % 32` 需要 config/shape 映射，不能直接赋值给表达式。ALEX 的 `num_keys_`、`bit_pos`、model slope 需要公开 API 操作序列间接触发。FA2 的 `blockIdx` 和 compile-time flags 需要 launch/configuration 映射。MInference sparse wrapper 中计算 `num_warps` 的条件存在，但对应 sparse kernel 调用中的 `num_warps` 实参被注释；观察该 predicate 不能自动宣称改变了 kernel 行为。所有案例继续保留 input binding / reachability 为 unknown，直到 adapter 或执行证据支持。

3. **条件原文不足以保证合法 boundary probes。** MInference wrapper 邻近代码要求 `Lk` 属于 `{16,32,64,128}`，因此围绕 64 的 63/65 会违反已有输入契约。FA2 API 邻近 `TORCH_CHECK` 要求 `head_size % 8 == 0`，191/193 等普通整数 ±1 也不合法。数值 equality 还可能是离散枚举 switch，例如 ALEX splitting policy，而非连续边界。应给所有方法相同的邻近 contract / function excerpts，保留出处；合法域尚未确定时继续 withheld/abstain，不能因数值在阈值两侧就判为合格测试。

4. **condition-only discovery 对主要 tensor 数据流存在盲区。** InfiniGen 核心 controller 的 `torch.where`、`topk`、`gather`、SVD 等主要机制并不依赖 literal-if。该 controller 目录只产生一个 `scaling` truthiness 条件，数值 gate 为空；冻结后 pool 主要来自 ours 模型的 eviction-policy 条件。MInference/Triton 的 vector mask、symbolic bounds，SparTA `.j2` CUDA templates，以及 FA2 `TORCH_CHECK`、static-switch/template macros 也未被完整发现。当前实验最多评估被抽取条件的候选合成质量，不能由高 provenance pass 推断算法覆盖率。

5. **类型与映射标签必须保留在模型上下文。** 审计时 `build_prompt` 的字段投影没有包含 scanner 的 `input_binding`、`value_type_source`、`numeric_format`、`parser`、`limitations`。模型因此看不到 derived expression、literal-based heuristic type 或 float32 邻居要求。建议这些信息和相同 contract excerpts 对三方法共同保留；不允许 Full 独享额外源码。源码类型仍可能未知，尤其 C++ fallback 的跨 header 字段与作用域；这些限制不能通过给候选写 `in_scope` 消失。

## Full / Direct 的公平性

审计时 `run_experiment` 先用 Full 最长 prompt 冻结截断后的 code/paper pools，再将相同的条件 ID 和 evidence 对象交给 Direct；Code-only 复用相同 code pool，但省略 paper evidence。此设计避免 Direct 因更短 instruction 额外获得上下文。共同 schema、candidate cap、禁止工具和“不声称已运行/发现 bug”的约束也一致。Full 与 Direct 的预期差别是方法指令，而不是输入材料。

人工组件范围必须三方法一致；scope manifest、排序规则、condition IDs、截断后 paper evidence IDs 和 prompt hash 应随 run 固定并保存。审计时 processed profiles 尚未生成，因此这里只核对实现逻辑与真实 code pools；正式调用前还需对实际保存的三个 prompt 的 DATA 做一次对象/ID 对比。

heuristic 分支在审计时仍直接调用 `discover_opportunities(profile, scan)`，不是冻结 model context 的实际 LLM 对比。它只适合离线 plumbing smoke test，不作为 Full/Direct 效果或成本的实验结论。机械 source checks、论文 scope、oracle correctness、运行可达性分别报告；本审计没有提供任何 bug 或 semantic-oracle 验证。
