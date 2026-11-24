# Prompt template: dynamic dispatch resolution (the LLM portion of step 2)

Purpose: resolve calls that static call resolution cannot follow (configuration strings selecting functions, dictionary dispatch, `getattr`, and monkey patches).
The LLM only **proposes** candidate call edges. Code checks that each edge points to a function definition that exists in the repository; otherwise it is discarded. Valid edges are added to the extractor call graph with provenance recorded as llm.

## User

```

**English translation (documentation only)**

```
Repository: {repo_url} @ {commit}
We are tracing which function actually runs for this call site:

  {file}:{line}
  {snippet}

Relevant definitions (retrieved by grep for the names involved):
{definitions}

Configuration values that reach this call site (from bindings / defaults):
{config_values}

Answer in JSON:
{
  "targets": [
    {"function": "path/to/file.py::name", "when": "condition under which this target runs"}
  ],
  "unresolved": "what is still unknown, or null"
}
Only list functions whose definitions appear above.
```
