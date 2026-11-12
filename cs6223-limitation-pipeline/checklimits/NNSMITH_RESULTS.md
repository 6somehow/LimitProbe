# 第二个 artifact：NNSmith（2026-11-12）

目的：检验方法不是 FlexPrefill 专用。NNSmith 是深度学习编译器的模糊测试工具，纯 Python、CPU 可跑，和 FlexPrefill（GPU kernel、torch、triton）几乎没有共同之处。

**做了什么：** 克隆固定 commit `a8307f2`（tag v0.0.1），建独立 venv（`scripts/make_venv_nnsmith.sh`：torch 2.4.0+cpu、z3、onnx、hydra 等），`batch --artifact nnsmith` 对 step 4 的 38 条 Finding 做同样的选取和 agent 运行。除了适配器要从 `artifact.json` 的入口点列表里选和目标同一文件的入口外，**没有为 NNSmith 写任何特例代码**。

## 结果

| | 数量 |
|---|---|
| step 4 的 Finding | 38 |
| harness 能判断（最终规则） | 19 |
| 其中 agent 得到 `yes` | 19（18 条 L1，1 条 L2，0 条 L3） |
| 其余：无代码位置 3、效果类型是 suspicious 2、目标不是分支 7（`fallback` 标在赋值上）、`reject` 但目标不能抛异常 6、witness 只有 trigger 1 | 19 |

没有 L3。压低档位的是：

* **D3 变异 residual 17 条。** 守卫只有一两个可变异点（取反是唯一的非等价变异体）：变异体个数 1 的 11 条、2 的 2 条、3 的 4 条、6 个和 10 个各 1 条。与 FlexPrefill 的结论一致：这是这类守卫的属性，不是算子集的问题。
* **D14 入口 residual 13 条。** 同 FlexPrefill：Region 的调用链只有"入口加目标所在函数"。
* D5 residual 3 条、open 1 条；D2 residual 3 条（条件靠 agent 写的谓词，翻译是否忠实没有验证）。

## 批量暴露并修复的三个 harness 缺陷（第二个 artifact 才看得到）

**1. 模块级目标（`Region.location.function == "<module>"`，nnsmith-F011）。** AST 比较的函数表里没有 `<module>`，目标被判成"已被修改"（D11 refuted）；模块级语句的"局部变量"是模块字典，里面有 `__file__` 等绝对路径，重放在另一目录里跑，哈希不同（D9 refuted）。现在：`<module>` 指模块体里 import 时执行的语句；捕获局部变量时跳过 `__` 开头的名字，并把仓库路径替换为 `<repo>`。

**2. `reject` 标在不能抛异常的语句上（F002、F005、F007，F006、F008 同类）。** step 4 把"程序最终拒绝了"标为 `reject`，但目标是 `while not check_sat():`、`if ...: continue` 这类语句。harness 的 `reject` 规则是"目标位置抛异常"，永远不会满足，于是给出**很自信的 `no / L1`**，3 条都是。这比弃权更糟，因为方向错了。现在：`reject` 只在目标能抛异常时判断（`assert`、`raise`，或分支体里有 `raise` 的 `if` / `while`），否则返回 `not_run` 并写明原因；分支体里有 `raise` 的 `if`，异常算在整条语句的行范围内。FlexPrefill 也受益：F047（盲审标 `wrong`，用完预算没写出 driver）就是这个原因。

**3. 稳定性哈希太严（D8、D9）。** 哈希包含目标行所有局部变量的值，`init_time = time.time()` 这样的变量每次不同，一个确定的行为被判成"不稳定"。5 条被 D9 误判，3 条被 D8 误判。现在只哈希 Region 条件里出现的名字的值；其余局部变量仍保存在报告里。代价写在测试里：只改了与条件无关的局部变量的未提交改动，重放发现不了；重放检查的是"这个 finding 能复现"，不是"每个变量都相同"。

三个缺陷都有回归测试，去掉修复后测试失败。

## 重新审计

用最终规则对两个 artifact 的归档 attempt 重新跑 harness（不重新运行 agent）：

| | 判定 / 档位分布 |
|---|---|
| FlexPrefill 33 个 attempt | yes：L3 6、L2 8、L1 16；无结论 3。与 agent 运行时只有 F053 不同（L3 到 L1，算子 v2 的变异体计数）|
| NNSmith 25 个 attempt | yes：L2 1、L1 18；无结论 6（全是 `not_run`，即上面第 2 类目标）。agent 运行时的 3 个 `no / L1` 变成 `not_run` |

## 限制

* 同一个 agent、同一个模型、没有重复；白盒（agent 能读 harness 源码）。
* NNSmith 的 19 条全是 `fallback`（分支被执行）这一类效果，没有 `reject` 型的 `assert`。这个 artifact 的 Finding 大部分是配置开关和生成策略的分支，不是输入校验。
* NNSmith 的 Finding 没有人工审阅，盲审标签只覆盖一部分，和结果没有可看出的关系。
* 没有真值，档位未校准。
