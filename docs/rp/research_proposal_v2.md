# CS6223 Project Proposal

## 基于 LLM Agent 的 Research Software Testing

### Discovering Potential Test Scenarios from Research Papers and Source Code

## Abstract

Research software 的 source code 往往包含论文正文未充分体现的 implementation details，例如 boundary conditions、fallback paths、special-case branches 和 configuration-dependent behaviors。这些实现细节虽然不一定构成 paper–code inconsistency，也不影响 artifact 通过 Artifact Evaluation (AE)，但可能暴露论文 scope 内值得进一步测试的场景。

本项目计划构建一个 **LLM-based Research Software Testing Agent**。给定一篇 research paper 及其 source-code repository，agent 自动理解论文的 research scope 和核心机制，探索相关代码，并寻找可能导致系统行为变化的 implementation conditions。对于位于论文 scope 内、但论文未明确讨论或评估的条件，agent 将生成具体且带有 paper/code evidence 的 **candidate test scenarios**。

本项目不运行 research artifact，也不重新复现实验。我们的目标是研究：**LLM agent 是否能够利用 research code 中的实现信息，为论文自动提出有依据的额外测试场景，从而降低人工审查 research software 的成本。**

---

# 1. Problem Statement

## 1.1 Problem

Research papers 通常只能描述系统实现的一部分。实际 source code 中可能包含大量论文没有详细说明的：

* thresholds；
* conditional branches；
* fallback mechanisms；
* configuration switches；
* special-case handling。

其中一些实现条件可能改变系统行为，同时仍然处于论文所声明的适用范围内。

例如，论文声称一个 scheduler 适用于 concurrency 1–128：

```python
if concurrency < 16:
    use_fifo_scheduler()
else:
    use_new_scheduler()
```

如果论文实验主要测试 16、32、64 和 128，那么代码中的 threshold 暴露了一个自然的 testing question：

> 当 concurrency 位于 16 附近时，系统行为发生切换。15、16、17 是否应该被作为额外测试场景？

这里不存在必要的 paper–code contradiction。我们的关注点是：

> **代码是否暴露了论文没有明确讨论、但值得进一步测试的 in-scope behavior？**

因此，本项目定义的任务为：

> **In-Scope Missing Test Scenario Discovery**

给定：

```text
Research Paper + Source Code Repository
```

输出若干 **candidate test scenarios**。

一个 candidate scenario 应满足三个条件：

1. **In-Scope**：场景位于论文声明的研究范围内；
2. **Implementation-Grounded**：存在具体 source-code evidence；
3. **Not Explicitly Discussed**：论文没有明确讨论或单独评估该场景。

Agent 的目标不是判断论文是否正确，而是提出：

> **“这里可能值得增加一个 test。”**

## 1.2 Project Scope

我们假设所分析的 artifact 已经通过 AE，因此本项目不研究：

* artifact installation 或 execution；
* experiment reproduction；
* numerical result verification；
* ordinary crash/functional bug detection；
* academic fraud detection；
* author intent；
* 超出论文 scope 的 adversarial testing。

本项目仅进行 **static inspection of paper and source code**。

---

# 2. Motivation

在传统 software testing 中，test generation 通常依赖明确的 specification 或 program behavior。然而，对于 research software，重要的 specification 往往分散在两类信息中：

```text
Paper → intended scope / research claims / expected behavior

Code  → actual implementation conditions / execution alternatives
```

仅阅读论文可能无法发现实现中的 boundary 和 special cases；仅阅读代码又难以判断某个 branch 是否与论文的 research claim 相关。

因此，research software testing 存在一个特殊问题：

> **需要同时理解 natural-language research specification 和 repository-level implementation。**

人工完成这一过程需要研究者阅读大量论文和 source code，成本较高。对于希望复用某项工作的研究者、reviewer 或 artifact evaluator，这种工作通常难以规模化。

另一方面，现代 LLM 已经具备较强的 paper understanding、code understanding 和 tool-use 能力。近期 SciCoQA 表明，paper–code cross-modal reasoning 本身已经成为可以系统研究的问题；同时，其结果也显示当前模型在 omission 和 long-context paper–code reasoning 上仍存在明显困难。

这为一个 software-testing-oriented 的问题提供了机会：

> 不要求 agent 自动证明论文存在错误，而是让 agent 帮助研究者缩小搜索空间，自动提出 **evidence-backed testing hypotheses**。

这样的目标更加适合实际辅助工具，也符合本课程项目有限的开发和 evaluation workload。

---

# 3. Proposed Solution

我们计划实现一个轻量级 **LLM-based Research Software Testing Agent**。

整体流程如下：

```text
             Research Paper
                   │
                   ▼
          Scope / Claim Extraction
                   │
                   ▼
               LLM Agent
                   │
          Repository Navigation
                   │
                   ▼
         Relevant Code Evidence
                   │
                   ▼
      Behavior-Changing Conditions
                   │
                   ▼
        Candidate Test Scenarios
```

Agent 通过 LLM API 调用有限的工具，例如：

* search/read paper sections；
* search repository；
* read source files；
* follow relevant symbols/files；
* collect paper/code evidence。

Agent 重点寻找可能影响系统行为的 implementation cues，例如：

```text
threshold
boundary condition
fallback path
special branch
configuration switch
alternative implementation path
```

随后判断这些条件是否与论文的 scope 或主要 mechanism 有关，并生成测试建议。

### Example Output

```text
Paper Scope:
Concurrency ranges from 1 to 128.

Paper Evaluation:
16, 32, 64, 128.

Code Evidence:
scheduler.py:114
if concurrency < 16:
    use_fifo_scheduler()

Observation:
The scheduling policy changes at concurrency = 16.

Candidate Test Scenario:
Test concurrency = 15, 16, 17.

Reason:
The implementation changes behavior at a boundary
inside the stated paper scope, but the paper does not
separately discuss this transition.
```

我们不会构建复杂的 multi-agent system。项目重点是验证：

> **tool-using agentic exploration 是否能够产生具体、有 evidence 的 research software test scenarios。**

---

# 4. Preliminary Study

目前的初步分析表明该任务具有一定可行性。

首先，真实 research repositories 中经常存在论文正文没有完整展开的 implementation details，例如 fallback logic、parameter conditions 和 special-case handling。此类结构天然可以对应传统 Software Testing 中的 **Boundary Value Analysis** 和 **Condition-Based Testing**。

其次，SciCoQA 已经提供了一个现成的 paper–code dataset，包含 **635 个 paper–code discrepancies，其中 92 个来自真实案例，543 个为 synthetic cases**。这些案例同时提供 paper 与 repository context，可以减少本项目重新构建数据集和人工 annotation 的工作。

不过，SciCoQA 的原任务是：

> **Does the code faithfully match the paper?**

而我们的任务是：

> **What additional test scenarios are suggested by the implementation?**

因此，本项目计划仅将 SciCoQA 作为 **proxy benchmark / case source**，而不会改变我们的任务定义。

具体来说，可以选取其中与 implementation conditions、paper omissions 或 behavior differences 相关的案例，测试 agent 是否能够：

```text
known paper/code case
        ↓
recover relevant implementation evidence
        ↓
identify behavior-changing condition
        ↓
generate a concrete test scenario
```

这可以显著减少人工构造 benchmark 的工作量。

---

# 5. Project Timeline

| Period   | Planned Work                                                       |
| -------- | ------------------------------------------------------------------ |
| Week 1–2 | 阅读 SciCoQA 等 related work；确定 task definition 和 agent output format |
| Week 3–4 | 实现 paper parsing、repository search 和 file-reading tools            |
| Week 5–6 | 实现基本 LLM agent workflow，并完成 paper–code evidence collection         |
| Week 7–8 | 实现 test-scenario generation；加入 scope checking 和 evidence grounding |
| Week 9   | 从 SciCoQA 中筛选适合作为 proxy evaluation 的 subset                        |
| Week 10  | 运行 benchmark evaluation，并与 naïve LLM prompting baseline 比较         |
| Week 11  | 选择 3–5 篇 systems papers，整理代表性 case studies                         |
| Week 12  | 分析结果、完善 prototype、完成 report 和 presentation                         |

---

# 6. Division of Work

三名成员计划按照以下方向分工：

* **Member A — Paper Understanding & Scope Extraction**
  负责 paper parsing、research scope / claim extraction、paper evidence retrieval，以及相关 prompt 设计。

* **Member B — Agent & Repository Exploration**
  负责 LLM agent framework、repository navigation、source-code search/read tools，以及整体系统集成。

* **Member C — Evaluation & Test Scenario Generation**
  负责 scenario generation、SciCoQA subset preparation、baseline、evaluation 和 case-study 分析。

三名成员共同参与 system design、debugging、result interpretation、report writing 和 final presentation。

---

# 7. Expected Outcome

项目预期产生以下三个结果。

### 7.1 一个可运行的 LLM Testing Agent

输入：

```text
paper + repository
```

输出：

```text
candidate test scenario
+ paper evidence
+ code evidence
+ explanation
```

### 7.2 一个轻量级 empirical evaluation

我们计划采用两种 evaluation。

**Proxy Benchmark Evaluation**

使用 SciCoQA 中适合的 subset，测试 agent 能否定位已有 paper–code cases 中的重要 implementation evidence，并进一步生成 test scenario。

同时设置一个简单 baseline：

```text
Paper + Code
     ↓
Single LLM Prompt
     ↓
Suggested Tests
```

与 agentic approach 比较：

```text
Paper
  +
iterative repository exploration
  +
evidence collection
  +
scope reasoning
     ↓
Suggested Tests
```

主要关注 agentic exploration 是否提高：

* evidence grounding；
* specificity；
* relevant implementation discovery。

**Case Studies**

选择约 **3–5 篇 systems papers**，展示大约 **8–15 个代表性 candidate test scenarios**。

Case study 不追求完整 recall，而主要检查：

1. 是否有明确的 code evidence；
2. 是否属于 paper scope；
3. 是否形成具体的 testing question。

为了减少 human labor，我们不会构建新的大规模人工标注 benchmark，只进行少量人工 spot-check。

### 7.3 Success Criteria

项目成功不要求证明 agent 能够发现所有 missing tests。

我们希望能够证明：

> **Compared with naïve prompting, an LLM agent can more reliably use concrete implementation evidence to generate specific and potentially useful test scenarios for research software.**

---

# 8. Related Work

### SciCoQA

SciCoQA 是与本项目最接近的工作。它研究 scientific paper 和 corresponding code 之间的 semantic discrepancy，并建立了包含 635 个 discrepancy 的 benchmark。该工作发现，即使当前较强的 LLM，在真实 paper–code discrepancy 上仍存在显著困难，尤其是在 paper omission 和 long-context reasoning 情况下。

SciCoQA 的核心目标是 **paper–code alignment verification**。

本项目不要求 paper 和 code 存在 inconsistency，而是利用 implementation detail 进一步生成 **candidate test scenarios**。因此二者解决的问题不同，但 SciCoQA 可以为我们的 evaluation 提供已有 paper/code cases。

### PaperBench

PaperBench 研究 AI agents 是否能够根据 research paper 从头复现研究工作。其任务包括理解论文、实现系统以及运行 experiments，并为 20 篇 ICML 论文构造了细粒度 evaluation rubrics。

与 PaperBench 不同，本项目不执行实验，也不尝试 replication。我们只对已有 repository 进行 static exploration，并生成额外的 testing hypotheses。

### Repository-Level LLM Agents

近期工作表明，repository-level code understanding 仍然是 LLM agent 的重要挑战。RepoReasoner 等研究发现，即使提供较好的上下文，模型在跨文件 reasoning 和 call-chain understanding 上仍存在明显限制。

因此，本项目采用 tool-based repository exploration，而不是一次性将整个 repository 放入 context。我们的目标不是解决通用 repository reasoning，而是将其应用于一个明确的软件测试任务：

> **从 research implementation 中发现 paper scope 内值得进一步测试的行为边界。**

---

# 9. Summary

本项目研究一个范围明确的 research software testing 问题：

> **Given a research paper and its source-code repository, can an LLM agent discover implementation-grounded, in-scope test scenarios that are not explicitly discussed or evaluated in the paper?**

我们的最终产品是一个轻量级 **LLM Research Software Testing Agent**。

项目不执行 artifact、不重新复现实验、不判断论文 correctness，也不构建新的大规模 benchmark。

通过：

```text
LLM Agent
+ repository exploration
+ paper scope reasoning
+ implementation evidence
+ test scenario generation
```

我们希望探索一种低人工成本的方法，使 research code 不仅作为 reproducibility artifact，也能够成为自动生成 additional test cases 的信息来源。

