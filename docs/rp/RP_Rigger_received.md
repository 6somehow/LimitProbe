# CS6223 Project Proposal

## Evidence-Grounded Limitation and Test Scenario Generation for Systems Research

### 0. Motivating Story

Imagine the following scenario.

You are a PhD student who has just started doing systems research. One day, you read a highly appealing paper. It presents a novel system design, tells a convincing story, reports strong experimental results, and seems to open an exciting direction for follow-up research.

Even better, the authors have released the full implementation on GitHub.

You decide to build your own research on top of this work. You start extending the codebase, designing new mechanisms, and running experiments. You may even begin to imagine that this line of work could eventually become your first OSDI or SOSP paper.

Several months later, however, you discover a few lines of implementation code that reveal an important condition that was barely discussed in the paper: a hidden fallback path, a configuration-dependent behavior, a hard-coded threshold, or an assumption that significantly narrows the scope of the original claim.

The limitation was not necessarily a bug, nor did it make the original paper incorrect. But understanding it earlier could have changed how you designed your research project.

This motivates our central question:

> **Can an LLM agent use both a systems paper and its source-code repository to identify evidence-grounded limitations and translate them into concrete test scenarios?**

------

## 1. Motivation

Understanding the limitations of existing work is an important part of systems research, especially for **early-career researchers** and researchers conducting **follow-up research or secondary development** on top of existing systems.

A common research workflow is:

```text
Existing Work
    ↓
Understand Its Scope
    ↓
Identify Limitations
    ↓
Design Improvements
    ↓
New Research Project
```

However, papers necessarily simplify complex implementations in order to present a clear research story. Important details may remain primarily in the source code, such as:

- boundary conditions;
- fallback paths;
- configuration dependencies;
- hardware-specific branches;
- alternative execution paths;
- hidden implementation assumptions.

These details do not necessarily indicate errors or paper-code inconsistencies. Instead, they may reveal **where a claim should be qualified**, or suggest conditions that deserve additional testing.

Systems research is particularly suitable for this task because repositories often contain substantial behavioral information that can be inspected statically, without reproducing the entire experimental setup.

------

## 2. Task Definition

Given:

```text
Research Paper
+
Source Code Repository
```

the system generates:

```text
Candidate Limitation
+
Paper / Code Evidence
+
Concrete Test Scenario
```

For example, suppose a paper claims that a scheduler supports concurrency from 1 to 128, but the implementation contains:

```python
if concurrency < 16:
    use_fifo_scheduler()
else:
    use_new_scheduler()
```

while the paper evaluates only:

```text
16, 32, 64, 128
```

The system may produce:

```text
Limitation:
The evaluation does not characterize the scheduling-policy
transition below concurrency 16.

Test Scenario:
Evaluate concurrency = 15, 16, and 17.
```

In this project, **limitation discovery is the reasoning target**, while **test scenario generation is the software-testing output**.

------

## 3. Proposed Approach

We will first implement a minimal agentic workflow:

```text
Paper
  ↓
Claim / Evaluation Extraction
  ↓
Repository Exploration
  ↓
Relevant Code Evidence
  ↓
Limitation Generation
  ↓
Test Scenario Generation
```

The agent can use tools for:

- paper search and reading;
- repository search;
- source-file inspection;
- symbol/configuration tracing;
- evidence collection.

We will initially avoid committing to a specific architecture. Depending on early results, we may explore extensions such as:

```text
Generator + Verifier
Generator ↔ Reviewer
Reusable Skill
Iterative Refinement
```

This keeps the research methodology flexible while allowing us to focus on the most promising technical direction.

------

## 4. Evaluation

We would like to minimize manual paper reading and large-scale annotation, and instead spend most of the project effort on the agent and reasoning pipeline.

### Existing Data and Silver Supervision

We will first explore existing resources such as:

- paper-code reasoning datasets;
- scientific code discrepancy datasets;
- papers with public OpenReview comments.

These sources may not provide direct systems-paper ground truth, but they can serve as **proxy or silver datasets** for evaluating components such as:

```text
evidence retrieval
paper-code matching
limitation recognition
test generation
```

Strong frontier models may also serve as **silver annotators or upper-bound baselines**, reducing the amount of manual labeling required.

### Baselines

The primary comparison will be:

```text
Naïve LLM Prompting
        vs.
Agentic Repository Exploration
```

Depending on progress, we may additionally evaluate:

```text
Agent + Verifier
Agent + Reusable Skill
Strong Frontier Model Baseline
```

Key evaluation dimensions include:

- evidence grounding;
- limitation validity;
- specificity;
- test-scenario quality;
- unsupported or hallucinated outputs.

### Small-Scale Human Evaluation

Rather than constructing a large new gold dataset, we plan to select approximately **3–5 systems papers** for final case studies.

Each team member can manually inspect one or more papers of interest and evaluate whether generated outputs are:

1. supported by the evidence;
2. relevant to the paper's claims or scope;
3. specific and meaningful;
4. already discussed in the paper;
5. convertible into useful testing hypotheses.

Human evaluation will therefore be used mainly as a final quality check rather than the main project workload.

------

## 5. Research Questions

**RQ1 — Feasibility**

> Can an LLM agent discover evidence-grounded limitations and test scenarios from systems papers and source-code repositories?

**RQ2 — Agentic Exploration**

> Does active repository exploration improve limitation and test-scenario generation compared with naïve LLM prompting?

**RQ3 — Architecture and Reusable Knowledge**

> Can verification, reusable Skills, or structured workflows help weaker models approach a strong-model baseline?

------

## 6. Scope

This project focuses on:

> **static paper-code reasoning and implementation-grounded test generation.**

We do not aim to perform:

- full artifact reproduction;
- numerical result verification;
- general bug finding;
- exhaustive limitation discovery;
- automatic paper acceptance/rejection.

The main technical challenge is:

> **How can an LLM agent actively connect research claims with implementation evidence and turn those connections into useful limitations and concrete testing hypotheses?**

------

## 7. Expected Outcome

We expect to build:

### A Paper-Code Analysis Agent

```text
Paper + Repository
        ↓
Limitation
+
Evidence
+
Test Scenario
```

### An Empirical Comparison

We will compare naïve prompting with repository-aware agentic exploration, and potentially with verifier- or Skill-enhanced variants.

### Systems Case Studies

We will demonstrate whether the system can uncover useful boundaries, assumptions, and testing opportunities in a small set of real systems papers.

If recurring patterns emerge, such as:

```text
threshold → boundary testing
fallback → fallback-condition testing
config switch → configuration sensitivity
hardware branch → portability limitation
```

we may further summarize them into reusable **LLM Skills** as an extension.

------

## 8. Summary

Our project asks:

> **Given a systems research paper and its source-code repository, can an LLM agent use implementation evidence to identify limitations and translate them into concrete test scenarios?**

The project emphasizes:

```text
Paper Understanding
+
Repository Exploration
+
Cross-Source Evidence
        ↓
Limitation Discovery
        ↓
Test Scenario Generation
```

We aim to keep the methodology flexible, minimize manual annotation, and focus our effort on the technically interesting part: **agentic exploration and evidence-grounded reasoning across research papers and source code.**
