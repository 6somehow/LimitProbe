# Prompt 模板：3b 代码 → 论文验证（问题 ①：文档里有没有写）

> 这是最初的模板。实际使用的 prompt 在 `codeside/verify3b.py`，版本号是 `PROMPT_VERSION`。

只负责判断"有没有写"。scope 和是否被评测由确定性代码判断，不交给 LLM。
建议用与生成模型**不同家族**的模型执行（避免自我偏好），并对输出做逐字 quote 校验。

## System

You check whether a limitation found in a research prototype's code is stated anywhere in its
documentation. You must quote text verbatim. If no passage states it, answer "not_found".
Do not infer that the authors "probably meant" something.

## User

```
Paper: {paper_title}
Mechanism: {mechanism}

Code limitation:
  condition (code names): {condition_expr}
  effect: {effect_text}
  location: {file}:{line}
  code snippet:
    {snippet}

Name mapping (code -> paper), from bindings:
{binding_lines}

Candidate passages (retrieved; each has an id and a source):
{passages}

Answer in JSON:
{
  "result": "found | boundary_mismatch | weaker | not_found | contradicted",
  "passage_ids": ["..."],
  "quotes": ["verbatim text copied from the passages"],
  "boundary_in_doc": "the condition as the document states it, or null",
  "rationale": "one or two sentences"
}

Definitions:
- found: a passage states this condition and effect with the same boundary.
- boundary_mismatch: a passage states the limitation but with a different boundary.
- weaker: a passage mentions it but weaker than the code (e.g. "only tested with" vs the code requiring it).
- contradicted: a passage claims the opposite (e.g. says a value is supported that the code rejects).
- not_found: none of the passages state it.
```

## 后处理（代码里做，不靠 LLM）

1. 每条 quote 必须是对应 passage 的子串，否则整条结果降级为 not_found 并记录。
2. `documented_in` 由 passage 的来源字段决定。
3. 写入 Verification(direction=code_to_paper, verifier="llm:<model>")。
