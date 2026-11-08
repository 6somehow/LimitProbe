# Prompt 模板：动态分发解析（步骤 2 中 LLM 负责的部分）

用途：静态调用解析追不到的调用（配置字符串选函数、字典分发、`getattr`、monkey patch）。
LLM 只**提出**候选调用边；每条边必须指向仓库里真实存在的函数定义（由代码校验），
否则丢弃。校验通过的边加入抽取器的调用图，provenance 记为 llm。

## User

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
