# 调用链、重复运行和盲测（2026-11-16）

对应 TODO 的 A2、A4（用 Wanting 的新调用链重跑 agent）、S5a（重复运行）、S5b（盲测）。25 次 agent 运行，合计约 73M token（含重复发送的上下文），每次约 5 到 24 分钟。原始运行在 `scratch/agent_runs/`（git 忽略），下面的表由 `scripts/experiments_table.py` 生成。

## 做法

* **新任务文本。** `task` 现在列出 `witness_hint.call_sites`：每层调用在哪一行、怎么解析的、被调函数的形参对应调用者里的哪个表达式，再加"目标里的名字用入口的输入怎么写"。agent 指令第 10 条要求从 `call_chain[0]` 进入，并用这张映射翻译 trigger 和 contrast。
* **agent 看不到已归档的结果。** 发现之前的批量里 agent 可以读 `agent_results/`（见 `BATCH_RESULTS.md` 补记三），所以这一轮沙箱隐藏了它和各结果文档。第一批 c1 运行（4 次）开始后才发现，我把它们作废了（`scratch/agent_runs/CONTAMINATED-c1-*`），隐藏之后重跑。
* **同一批 Finding 重复三次（chain-1、chain-2、chain-3）加一次盲测。** 集合：NNSmith F004、F035、F036 和 FlexPrefill F007、F008，这五条之前都有 agent 测试包，D14 或 D3 有改善空间。另外 NNSmith F001、F018、F003、F012、F034 只跑 chain-1（A2、A4）。
* **"盲测"（`--blind`），实际是半盲。** `checklimits/` 包在沙箱里换成只有编译好的 `.pyc` 的副本（`cl` 照常能跑），`CONFIDENCE_SPEC.md`、`SCORECARD.md`、`CONTRACT_TEST_REPORT.md`、`REQUESTS_TO_STEP4.md` 读不到（agent 试过读，得到空文件）。agent 仍然有任务文本、`agent/INSTRUCTIONS.md`，以及 `cl lint`、`cl run` 的输出。**但五次盲测运行都去看了编译后的模块：** 用 `strings` 看 `.pyc`（bln-f004 看了 `mutate`，blf-f007 看了 `adapter`、`confidence`、`runner`、`child`），用 `marshal` 和 `dis` 反汇编（bln-f036、blf-f008）。所以这一条件隔离的是"读源码和规则文档"，不是"知道规则"。要做干净的盲测，需要把 `lint` 和 `run` 放到沙箱外执行，agent 只拿到输出，这一步没做。
* 判定和档位都由沙箱外的 harness 重算，和以前一样。

## 结果

D14=eli 是入口检查已消除，res 是残余，ref 是被推翻，ope 是未评估；D3 同理。括号里是 token 数和用时。"earlier"是之前的归档运行（当时 agent 能读 `agent_results/`，也没有调用链信息）。

| finding | earlier | chain-1 | chain-2 | chain-3 | blind |
|---|---|---|---|---|---|
| nnsmith-F001 | - | inconclusive/invalid D14=eli D3=res (3.6M, 21min) | - | - | - |
| nnsmith-F003 | inconclusive/invalid D14=res D3=ope (2.8M, 12min) | inconclusive/invalid D14=res D3=res (3.9M, 24min) | - | - | - |
| nnsmith-F004 | yes/L1 D14=eli D3=res (3.7M, 12min) | yes/L1 D14=eli D3=res (2.1M, 9min) | yes/L1 D14=eli D3=res (0.7M, 5min) | yes/L1 D14=eli D3=res (2.5M, 5min) | yes/L1 D14=eli D3=res (2.3M, 20min) |
| nnsmith-F012 | yes/L1 D14=res D3=res (1.6M, 6min) | yes/L1 D14=eli D3=res (2.3M, 14min) | - | - | - |
| nnsmith-F018 | - | yes/L1 D14=eli D3=res (3.4M, 9min) | - | - | - |
| nnsmith-F034 | yes/L1 D14=res D3=res (2.5M, 7min) | yes/L1 D14=res D3=res (2.9M, 8min) | - | - | - |
| nnsmith-F035 | yes/L2 D14=res D3=eli (3.1M, 12min) | yes/L3 D14=eli D3=eli (3.1M, 13min) | yes/L2 D14=res D3=eli (2.9M, 13min) | yes/L3 D14=eli D3=eli (3.7M, 15min) | yes/L3 D14=eli D3=eli (2.8M, 24min) |
| nnsmith-F036 | yes/L1 D14=res D3=res (2.6M, 7min) | yes/L1 D14=res D3=res (2.9M, 7min) | yes/L1 D14=res D3=res (2.2M, 10min) | yes/L1 D14=res D3=res (1.9M, 5min) | yes/L1 D14=res D3=res (4.1M, 23min) |
| flexprefill-F007 | yes/L2 D14=res D3=eli (3.8M, 12min) | yes/L2 D14=res D3=eli (2.9M, 11min) | yes/L2 D14=res D3=eli (2.3M, 12min) | yes/L2 D14=res D3=eli (2.6M, 11min) | yes/L1 D14=res D3=ref (4.0M, 17min) |
| flexprefill-F008 | yes/L2 D14=res D3=eli (1.8M, 7min) | yes/L3 D14=eli D3=eli (2.1M, 10min) | yes/L2 D14=res D3=eli (3.7M, 19min) | yes/L2 D14=res D3=eli (4.1M, 22min) | yes/L2 D14=res D3=eli (4.3M, 23min) |



| condition | runs with a package | D14 eliminated | level L1 | L2 | L3 | invalid/n/a |
|---|---|---|---|---|---|---|
| earlier | 8 | 1 | 4 | 3 | 0 | 1 |
| chain-1 | 10 | 6 | 5 | 1 | 2 | 2 |
| chain-2 | 5 | 1 | 2 | 3 | 0 | 0 |
| chain-3 | 5 | 2 | 2 | 2 | 1 | 0 |
| blind | 5 | 2 | 3 | 1 | 1 | 0 |

## 读法

**1. 调用链让 D14 变得可以消除，但不稳定。**
* chain-1 的 10 次运行里 6 次 D14 为 eliminated，之前的 8 次里是 1 次。NNSmith F035（L2 到 L3）、F012、F018，FlexPrefill F008（L2 到 L3）。
* 同一批五条 Finding 重复三次：D14 eliminated 的有 3、1、2 条（chain-1、2、3）。F035 是 L3、L2、L3，F008 是 L3、L2、L2。**同样的任务，agent 有时走官方入口，有时直接调内部函数并写 `entry_reason`。** 档位的波动只有 F035 和 F008 这两条，一级之差，都来自 D14。
* 所以 L3 在这个集合上不是 agent 每次都能达到的，不能把一次运行的 L3 当作结论。

**2. 重复运行：判定稳定，档位基本稳定。** 五条 Finding 各三次，判定 15 次全是 `yes`；档位三次相同的 3 条，差一级的 2 条，没有差两级的。样本很小，只有一个模型。

**3. 半盲测：判定相同，档位差不多，但不能当作"盲测"的结论。** 五次运行全是 `yes`，档位 L1、L3、L1、L1、L2，在白盒三次的范围内，只有 FlexPrefill F007 低一级：D3（变异检查）被推翻，agent 写的 oracle 没有被变异体检验到，白盒的三次都是 L2。D14 eliminated 了 2 条，白盒是 1 到 3 条。成本更高：平均 3.5M token、21 分钟，白盒是 2.7M、11 分钟，盲测平均多 15 个工具调用（69 对 54），而每次运行有约 13 个调用在读字节码或规则文档（23、22、5、9、5 个）。因为五次都读了字节码（见上），"没有看到知道规则才能拿高档位的证据"这句话只能说成：**读源码和读字节码得到的档位相近**。要回答"不知道规则时 agent 能做到什么"，需要上面说的沙箱外执行。

**4. agent 读源码发现的两个调用链问题，step 4 的静态分析给不出（已写进 `REQUESTS_TO_STEP4.md` 第 6 节）。**
* NNSmith F034、F036 的调用链最后一步是 `override`，目标在 `GuidedGen.post_process`。agent 查到 `GuidedGen` 在整个仓库只有定义，没有实例化，官方入口构造的是 `PureSymbolGen`。所以目标从官方入口走不到，D14 保持 residual，`entry_reason` 里写了这个。
* FlexPrefill F007：目标守卫检查传入列表的长度，而官方入口里这些列表的长度由构造过程决定，守卫从入口不可能为假。step 4 记为 `solved`，因为这不是入口参数的线性约束。F007 的 L2 因此应读作"直接调内部函数可复现"。

**5. 一个 harness 缺口：目标是裸 `raise` 时测试是 `invalid`。** NNSmith F001、F003 在这一轮都是 `inconclusive/invalid`（D2 被推翻）。原因：`raise` 只有守卫成立时才会执行，对照点到不了目标行，D2（"条件在对照点为假"）在目标行上求不到值。五个 artifact 里这类共 6 条，其中 FlexPrefill F019 也是同样原因 invalid。修法是在 `raise` 外层 `if` 的头上求条件，需要改追踪器的两个后端、运行器和审计，**还没做**，也不想在实验进行中改 harness（会让几次运行的审计口径不一致）。

## 限制

* 同一个模型（x-test-2），五条 Finding 三次重复，十条 Finding 一次。没有真值，没有显著性检验。
* "earlier"和 chain-1 之间有三个变量同时变了：任务文本有了调用链，`agent_results/` 被隐藏，agent 指令加了一段。不能把 D14 的改善全部归因于调用链。chain-1 到 chain-3 之间是同一个条件，那部分可以看作纯噪声。
* 重复运行是同一批次内顺序启动，没有随机化顺序。
* 半盲测隐藏了源码和规则文档，没有隐藏字节码，agent 也仍然知道要做什么（指令文件在）。

## 结果写进了报告

chain-1 的十个测试包已经用 `checklimits test --attempts-root` 审计并写进 `results/e2e/`（FlexPrefill 29 条已测，NNSmith 22 条已测，都没有 `not_attempted`）。取 chain-1 而不是最好的一次，避免挑选：规则是"当前流程的第一次运行"。
