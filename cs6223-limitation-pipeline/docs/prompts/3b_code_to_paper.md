# Prompt template: 3b code → paper verification (question ①: is it stated in the documentation?)

> This is the original template. The prompt used in practice is in `codeside/verify3b.py`; its version is `PROMPT_VERSION`.

It only determines whether the limitation is stated. Deterministic code decides scope and evaluation coverage; these are not delegated to the LLM.
Use a model from a **different family** than the generation model to avoid self-preference, and check output quotes verbatim.

## System

You check whether a limitation found in a research prototype's code is stated anywhere in its
documentation. You must quote text verbatim. If no passage states it, answer "not_found".
Do not infer that the authors "probably meant" something.

**English translation (documentation only)**

You check whether a limitation found in a research prototype's code is stated anywhere in its
documentation. You must quote text verbatim. If no passage states it, answer "not_found".
Do not infer that the authors "probably meant" something.

## User

```

**English translation (documentation only)**

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

## Postprocessing (in code, not by the LLM)

1. Each quote must be a substring of its corresponding passage; otherwise downgrade the whole result to not_found and record it.
2. Set `documented_in` from the passage source field.
3. Write Verification(direction=code_to_paper, verifier="llm:<model>").
