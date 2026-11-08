# 项目总览（2026-11-01 定稿版）

## 一句话

给定一篇系统研究论文和它的代码仓库，论文侧和代码侧各自找出 limitation，再互相验证；
整合后得到"已确认 / 边界不一致 / 仅论文提及 / 代码有但论文未说明"四类 finding，
最后为每条 finding 生成测试，并在 CPU + mock、simulator 或 GPU 上执行确认。

核心发现是 **代码里存在、论文没有说明、又落在论文声明范围内** 的 limitation。

## 三个层次（proposal Table 1）

| 层次 | 例子 | 发现来源 |
|---|---|---|
| L1 评测中可见 | SparTA：低稀疏度、非结构化稀疏下效果差 | 论文 evaluation |
| L2 论文与代码之间 | 阈值、fallback、配置限制、assert | 论文 + 代码交叉（主要由代码侧产出） |
| L3 隐含假设 | InfiniGen：公式按 MHA 推导，GQA 不直接适用 | 论文假设 × 架构变体清单 |

## 流程与分工

| 步骤 | 内容 | 输出（schema 记录） | 负责人 |
|---|---|---|---|
| 1 | 论文侧找 limitation：claim、scope、评测点、自述 limitation、L1、L3 | Claim, ScopeItem, EvalPoint, Binding, Limitation(origin=paper) | Zhaopeng |
| 2 | 代码侧找 limitation：区域表；拒绝、fallback、阈值、配置限制 | Region, Limitation(origin=code) | **Wanting** |
| 3a | 论文 → 代码验证：论文 limitation 在代码里有无对应、边界是否一致 | Verification(paper_to_code) | Zhaopeng |
| 3b | 代码 → 论文验证：代码 limitation 论文 / README 有无提到、是否在 scope 内 | Verification(code_to_paper) | **Wanting** |
| 4 | 整合：去重，归为四类，输出 finding 清单 | Finding | **Wanting** |
| 5 | 测试生成：witness + oracle | TestCase | Shanghao |
| 6 | 执行确认：CPU + mock / simulator / GPU | TestCase.result | Shanghao |
| 7 | 评估 | 指标 | 三人共同 |

另外：Zhaopeng 负责 agent 编排、LLM baseline、去掉论文的消融；**Wanting 负责共享 schema**。

## Wanting 的边界

- **输入**：论文侧的 Claim / ScopeItem / EvalPoint / Binding（来自 Zhaopeng），代码仓库，论文全文和 README。
- **输出**：Region、Limitation(origin=code)、Verification(code_to_paper)、Finding（带 witness_hint，交给 Shanghao）。
- **评估**：区域表准确率（gold 对照 + 与 Shanghao 一起做动态 trace 对照）、分类准确率。

## 开发数据集

SparTA、MInference、InfiniGen（proposal 的三篇）和 NNSmith，详见 `docs/05_dataset.md`。FlexPrefill 是示范 pilot。

## 原则

1. LLM 只负责"理解和定位"（读论文、补动态分发、语义匹配），"判定"尽量由确定性分析或执行给出。
2. 每条记录都带 provenance（ast / llm / manual）和可核对的证据（verbatim quote、file:line）。
3. 方法以静态为主，执行只用于确认。
