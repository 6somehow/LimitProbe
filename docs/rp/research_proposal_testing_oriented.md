# CS6223 Project Proposal

## 基于 LLM Agent 的 Research Software Testing

### Evidence-Grounded Test Generation from Research Papers and Source Code

## Abstract

Systems research 的 source code 往往包含论文正文未充分体现的 implementation details，例如 boundary conditions、fallback paths、special-case branches 和 configuration-dependent behaviors。这些实现细节即使不构成 paper–code inconsistency，也可能暴露论文 scope 内值得进一步测试的行为。

本项目计划构建一个 **LLM-based Research Software Testing Agent**。给定 research paper 及其 source-code repository，agent 自动理解论文的 research scope 和核心机制，探索相关代码，识别可能导致系统行为变化的 implementation conditions，并生成针对这些条件的 **candidate tests**。

与仅依赖 LLM 判断不同，我们进一步关注 **test oracle problem**。Agent 将尽可能为生成的测试构造可验证的 oracle，例如基于 boundary/branch behavior、runtime instrumentation、differential behavior、metamorphic relation 或 deterministic gate rules。LLM 主要负责 semantic reasoning，而测试结果尽可能由程序行为本身验证。

我们的目标是探索：

> **Can an LLM agent transform implementation details in research software into concrete, evidence-grounded tests with partially automated test oracles?**

---

# 1. Problem Statement

## 1.1 Problem

Research papers 通常只能描述实际系统实现的一部分。Source code 中可能存在：

* thresholds；
* conditional branches；
* fallback mechanisms；
* configuration switches；
* state transitions；
* special-case handling。

这些实现条件可能改变系统行为，但未必被论文的 evaluation 单独覆盖。

例如论文声称：

> The proposed scheduler supports concurrency from 1 to 128.

实现中存在：

```python
if concurrency < 16:
    use_fifo_scheduler()
else:
    use_new_scheduler()
```

这并不一定说明论文或实现存在错误，但从 software testing 的角度，它暴露出了一个明显的 behavioral boundary：

```text
15 → FIFO
16 → New Scheduler
17 → New Scheduler
```

因此自然产生一个测试：

> Test concurrency = 15, 16, 17.

进一步的问题是：

> **测试之后，如何判断结果是否值得关注？**

如果完全让同一个 LLM 同时生成 test 并判断 test 是否通过，那么结果容易依赖模型自身判断，缺少可靠的 test oracle。

因此，本项目研究的完整任务为：

> **给定 research paper 和 source code，自动发现论文 scope 内值得测试的 implementation behavior，生成 concrete tests，并尽可能构造不完全依赖 LLM judgment 的 test oracle。**

---

## 1.2 Project Scope

为了保证方法具有一定 generality，我们不将技术限定在 scheduler、database 或某一类 systems paper。

我们关注满足以下条件的 **systems research artifacts**：

1. source code available；
2. 论文定义了明确的 system behavior、scope 或 evaluation setting；
3. implementation 中存在可观察的 input、configuration、state 或 control-flow variation。

在该范围内，具体系统可以是：

* operating systems；
* distributed systems；
* databases；
* networking systems；
* storage systems；
* ML systems。

不同系统中的具体参数可能不同，但底层 testing pattern 是通用的，例如：

```text
Boundary
Branch
Configuration
State Transition
Fallback
Alternative Execution Path
```

因此，我们希望 generalize 的并不是某个具体 test case，而是一组 **implementation-driven testing skills**。

---

# 2. Motivation

传统 software testing 通常从 specification 或 program structure 出发生成测试。

Research software 存在一个特殊情况：

```text
Paper
  ↓
Research scope
Expected behavior
Claimed mechanism

Code
  ↓
Actual branches
Boundaries
Fallbacks
Configurations
```

Paper 提供 semantic specification，而 code 提供 implementation-level testing opportunities。

只阅读论文，很难知道哪些输入会触发不同 execution paths；只阅读代码，又难以判断某个 branch 是否与论文的 research claim 有关。

因此，本项目的核心机会是：

> **让 LLM 负责连接 paper-level semantics 与 code-level testing structure，再让传统 testing mechanisms 提供更可靠的 verification。**

这也避免把整个任务变成：

```text
LLM reads paper
→ LLM guesses issue
→ LLM says whether its guess is correct
```

相反，我们希望形成：

```text
LLM reasoning
      ↓
Concrete Test
      ↓
Program Evidence / Testing Oracle
```

---

# 3. Proposed Solution

我们计划实现一个轻量级 **Research Software Testing Agent**。

整体流程为：

```text
              Research Paper
                    │
                    ▼
           Scope / Claim Extraction
                    │
                    ▼
                 Agent
                    │
          Repository Exploration
                    │
                    ▼
        Suspicious / Interesting Code
                    │
                    ▼
          Testing Skill Selection
                    │
                    ▼
             Test Generation
                    │
                    ▼
         Oracle / Hook Generation
                    │
                    ▼
       Evidence-Grounded Test Report
```

## 3.1 Implementation-Driven Test Generation

Agent 首先寻找可能导致 behavior transition 的代码结构，例如：

```text
threshold
branch
fallback
configuration
state transition
alternative implementation
```

然后选择相应的 testing strategy。

例如对于：

```python
if queue_size < 32:
    local_path()
else:
    distributed_path()
```

Agent 可以应用 **Boundary Value Analysis**：

```text
queue_size = 31
queue_size = 32
queue_size = 33
```

对于：

```python
if cache_enabled:
    cached_path()
else:
    normal_path()
```

可以生成 **configuration differential test**：

```text
cache_enabled = true
vs.
cache_enabled = false
```

因此，不同 systems artifact 可以共享相同的 testing skills，而无需为每种系统单独设计规则。

---

## 3.2 Testing Skill Library

为了提高 generality，我们计划定义少量通用 testing skills，例如：

### Boundary Testing

针对：

```text
x < T
x >= T
```

生成：

```text
T-1, T, T+1
```

### Branch / Path Testing

针对与论文核心 mechanism 有关但 evaluation 中没有明显覆盖的 branch，生成能够触发不同 execution path 的输入或配置。

### Configuration Differential Testing

对关键 configuration 进行 controlled variation：

```text
Config A
vs.
Config B
```

比较其 observable behavior。

### Metamorphic Testing

当不存在明确 expected output 时，可以利用关系型 oracle。

例如输入规模增加时，某些 system behavior 应满足论文声明的 monotonicity 或 invariant，而不是要求我们预先知道正确的绝对输出。

这些 testing skills 可以由 agent 根据 paper semantics 和 code structure 自动选择。

---

# 4. Test Oracle

Test oracle 是本项目的重要研究问题。

我们不会完全依赖 LLM 判断测试是否“通过”。

对于一个生成的 test，我们计划使用多层 oracle。

## 4.1 Deterministic Gate Rules

首先使用能够程序化验证的规则过滤结果，例如：

```text
Is the tested value inside the paper scope?

Does the input actually cross the identified code boundary?

Does the configuration activate a different branch?

Is the relevant code evidence identifiable?
```

这些判断可以通过 parsed paper evidence、AST/code structure 或 runtime trace 完成，而不需要 LLM subjective judgment。

---

## 4.2 Runtime Instrumentation

对于 agent 认为值得进一步检查的 suspicious code block，可以自动生成轻量级 instrumentation 或 hook。

例如：

```python
if queue_size < 32:
    local_path()
else:
    distributed_path()
```

Agent 可以建议或生成 instrumentation：

```python
log("selected_path", current_path)
```

然后检查：

```text
input = 31 → local_path
input = 32 → distributed_path
```

这里 oracle 不是 LLM 的判断，而是实际 runtime execution evidence。

本项目不会重新运行完整 paper experiments；runtime checking 只针对局部、低成本的 generated tests，在环境允许时执行。

---

## 4.3 Differential and Metamorphic Oracles

对于没有显式 ground truth 的 systems behavior，可以比较不同输入之间的行为。

例如：

```text
Input A
   ↓
Behavior A

Input B
   ↓
Behavior B
```

测试的重点可以不是：

> “Behavior A 的正确值应该是多少？”

而是：

> “当输入跨越 implementation boundary 时，observable behavior 是否发生了预期的 transition？”

类似地，可以利用论文中的 invariants 或 relational claims 构造 **metamorphic oracle**。

---

## 4.4 Limited LLM-as-a-Judge

某些问题仍然涉及 semantic judgment，例如：

> 某个 generated test 是否真正属于论文 scope？

对于这部分，我们可以使用预先定义的 rubric：

```text
1. Evidence exists in paper.
2. Evidence exists in code.
3. Scenario remains inside stated scope.
4. Test targets an observable behavior transition.
```

LLM 仅负责 rubric 中难以完全形式化的部分。

我们计划通过少量人工检查验证 LLM rubric judgment 与 human judgment 的一致性，而不是让 LLM 作为唯一 oracle。

因此最终结构为：

```text
Deterministic Gate
        +
Program / Runtime Evidence
        +
Differential or Metamorphic Oracle
        +
Limited Rubric-Based LLM Judgment
```

---

# 5. Preliminary Study

我们的初步观察是，systems code 中普遍存在适合这种方式处理的 implementation cues：

```text
if size < threshold
if feature_enabled
fallback()
switch(mode)
retry / timeout condition
fast path / slow path
```

这些结构与具体 research domain 无关，因此 testing technique 在原则上可以应用于不同类型的 systems research artifact。

另一方面，SciCoQA 已经提供了 paper 和 source-code pair，以及已知的 paper–code semantic cases。

虽然 SciCoQA 的任务是 paper–code discrepancy detection，而不是 test generation，但它可以作为已有 case source：

```text
Known implementation detail
          ↓
Our Agent
          ↓
Generate corresponding test
          ↓
Generate evidence / oracle
```

从而减少重新构造 dataset 和大规模人工 annotation 的成本。

---

# 6. Evaluation

Evaluation 将重点回答三个问题。

## RQ1: Generality

> Agent 的 testing skills 是否能够应用于不同类别的 systems research artifacts？

我们计划选择来自多个 systems domain 的少量 paper，而不是只选择同一种 system。

例如：

```text
Database
Distributed System
ML System
Operating/System Software
```

evaluation 数量可以有限，但 testing mechanism 应保持一致。

---

## RQ2: Test Generation Quality

> Agent 是否能够生成具体、implementation-grounded 的测试，而不是泛泛的 testing suggestion？

例如：

**Naïve LLM**

> Test different request sizes.

**Our Agent**

> Test request sizes 255 KB, 256 KB, and 257 KB because `buffer.cc` switches allocation strategy at 256 KB, which lies within the paper's stated 1 KB–1 MB scope.

主要比较：

* specificity；
* paper evidence；
* code evidence；
* concrete test input；
* targeted behavior。

---

## RQ3: Oracle Quality

> 有多少 generated tests 能够获得不完全依赖 LLM 的 oracle？

我们可以统计：

```text
Rule-verifiable
Runtime-verifiable
Differential/metamorphic
LLM-only
```

理想结果是大部分 test 至少具有一种非纯 LLM 的 verification mechanism。

这也将成为项目区别于简单 “LLM reviews research code” 的关键点。

---

# 7. Project Timeline

| Period   | Planned Work                                                        |
| -------- | ------------------------------------------------------------------- |
| Week 1–2 | 确定 task definition；整理通用 testing skills 和 oracle categories          |
| Week 3–4 | 实现 paper parsing、repository search 和 agent tool interface           |
| Week 5–6 | 实现 boundary / branch / configuration test generation                |
| Week 7   | 实现 deterministic gate rules 和 evidence collection                   |
| Week 8   | 实现 instrumentation hook 与 differential/metamorphic oracle prototype |
| Week 9   | 从 SciCoQA 和公开 systems artifacts 中选择 evaluation cases                |
| Week 10  | 与 naïve LLM baseline 比较 test generation                             |
| Week 11  | 分析 generality 和 oracle coverage，整理 case studies                     |
| Week 12  | 完成系统、报告与 presentation                                               |

---

# 8. Division of Work

* **Member A — Paper Semantics & Scope Reasoning**
  Paper parsing、scope / claim extraction、paper evidence retrieval、scope gate rules。

* **Member B — Agent & Test Generation**
  Repository navigation、testing skill selection、boundary/branch/configuration test generation。

* **Member C — Oracle & Evaluation**
  Runtime hook、differential/metamorphic oracle、SciCoQA cases、baseline 和 evaluation。

三名成员共同负责 system integration、case-study analysis、report 和 presentation。

---

# 9. Expected Outcome

本项目预期实现一个能够输入：

```text
Research Paper
+
Source Repository
```

并输出：

```text
Implementation Observation
+
Concrete Test Input
+
Paper Evidence
+
Code Evidence
+
Suggested Test Oracle
```

的 LLM-based testing agent。

例如：

```text
Paper Scope:
Concurrency = 1–128.

Code Evidence:
scheduler.py switches policy at 16.

Generated Test:
concurrency = 15, 16, 17.

Runtime Hook:
record selected scheduler.

Oracle:
Verify whether execution path changes at the boundary
and whether the observed behavior is consistent with
the mechanism described in the paper.
```

项目成功的核心标准不是发现所有 possible bugs，而是验证：

> **LLM agent 是否能够把 research implementation 中隐藏的 behavior boundaries 转化为 concrete tests，并为这些测试提供尽可能独立于 LLM judgment 的 verification mechanism。**

---

# 10. Related Work

## Paper–Code Alignment

SciCoQA 研究 scientific paper 与 source code 之间的 semantic discrepancy。其核心任务是判断 implementation 是否忠实于 paper description。

本项目不要求 paper 与 code 存在 inconsistency。我们利用 implementation details 生成 additional tests，因此 research question 更接近 **implementation-aware test generation**。

SciCoQA 可以作为部分 evaluation cases 的来源，而不是本项目的任务定义。

## LLM-Based Repository Understanding

已有研究表明，LLM 可以借助 code search 和 repository navigation tools 进行 repository-level reasoning，但长距离 cross-file reasoning 仍具有挑战。

因此，本项目采用 iterative tool use，而不是将整个 repository 一次性提供给模型。

## Traditional Software Testing

本项目借鉴：

* Boundary Value Analysis；
* White-box Testing；
* Differential Testing；
* Metamorphic Testing；
* Runtime Instrumentation。

其中 LLM 的主要作用是连接：

```text
Paper-level semantic knowledge
            ↕
Code-level testing opportunities
```

而不是替代这些 testing techniques 的 oracle。

---

# 11. Summary

本项目研究：

> **Given a research paper and its implementation, can an LLM agent automatically derive concrete, in-scope tests from implementation behavior, while constructing test oracles that do not fully depend on the LLM itself?**

核心方法可以概括为：

```text
Paper Semantics
      +
White-box Code Inspection
      ↓
LLM Agent
      ↓
Testing Skill Selection
      ↓
Concrete Test Generation
      ↓
Rule / Runtime / Differential / Metamorphic Oracle
```

相比单纯使用 LLM 进行 paper–code review，本项目希望加入一个更明确的 **software testing insight**：

> **LLM discovers where to test; traditional testing mechanisms help determine what the test means.**

