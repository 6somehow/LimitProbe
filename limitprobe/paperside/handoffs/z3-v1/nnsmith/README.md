# nnsmith · Z3交接

先看 `testability_hints.json` 的主案例与边界，再看 `limitations_for_tests.json` 的原生契约样例。这里是论文侧fixture，不是重跑或覆盖step4结果。

论文origin保持paper；effect保持other，因为返回值/数值oracle尚不受当前异常/分支检查支持。`consumer_contract_check.json`和`contract_output/`记录真实消费者读取与未运行原因；不包含测试结果或置信度评分。

原有6条负项逐条留存triage，其中1条给出详细局部输入与源码调用链，其余未完成输入构造或语义复核时明确留待办，不伪装成已求解witness。
