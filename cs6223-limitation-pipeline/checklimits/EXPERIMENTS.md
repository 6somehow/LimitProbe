# 调用链、重复运行和盲测（2026-11-16 到 17）

对应 TODO 的 A2、A4（用 Wanting 的新调用链重跑 agent）、S5a（重复运行）、S5b（盲测）。30 次 agent 运行（第一轮 25 次，11-17 补了 5 次干净盲测），合计约 88M token（含重复发送的上下文），每次约 5 到 24 分钟。原始运行在 `scratch/agent_runs/`（git 忽略），表由 `scripts/experiments_table.py` 生成。**表里的判定和档位是用 11-17 的 harness 对每个测试包重新审计的结果**（`reaudit`），不是 agent 当时拿到的，原因见"D14 的漏洞"。

## 做法

* **新任务文本。** `task` 列出 `witness_hint.call_sites`：每层调用在哪一行、怎么解析的、被调函数的形参对应调用者里的哪个表达式，再加"目标里的名字用入口的输入怎么写"。agent 指令第 10 条要求从 `call_chain[0]` 进入，并用这张映射翻译 trigger 和 contrast。
* **agent 看不到已归档的结果。** 之前的批量里 agent 可以读 `agent_results/`（`BATCH_RESULTS.md` 补记三），这一轮沙箱隐藏了它和各结果文档。第一批 c1 运行（4 次）开始后才发现，已作废（`scratch/agent_runs/CONTAMINATED-c1-*`），隐藏之后重跑。
* **同一批 Finding 重复三次（chain-1、chain-2、chain-3）。** 集合：NNSmith F004、F035、F036 和 FlexPrefill F007、F008，之前都有 agent 测试包。另外 NNSmith F001、F018、F003、F012、F034 只跑 chain-1。
* **两种盲测。**
  * **半盲（half-blind，11-16）：** `checklimits/` 换成只有 `.pyc` 的副本，规则文档读不到。五次运行都用 `strings`、`marshal`、`dis` 去读了字节码，所以它隔离的是源码和文档，不是规则本身。
  * **干净盲测（clean-blind，11-17）：** 沙箱里完全没有 harness（包目录是空 tmpfs，规则文档读不到）。`cl` 是一个只有标准库的客户端，通过 Unix socket 把 `task`、`init`、`lint`、`run` 交给沙箱外的服务执行，只把输出还给 agent（`agent_service.py`）。服务只接受这四个命令和指令里用到的参数，路径必须在运行目录里；`run` 会执行 agent 的 driver，所以服务在同一个 bwrap 沙箱里运行它（同样的隐藏路径、只读文件系统），harness 源码对那个进程可见，agent 通过 shell 读不到。如果 driver 去打印 harness 源码就破坏了盲测，agent 不被假定去攻击沙箱。五次运行里 agent 都试着去 `ls`、`sed` harness 目录和规则文档，拿到的是空目录和空文件，然后照任务文本和 `lint`、`run` 的输出继续。
* 判定和档位由沙箱外的 harness 重算，和以前一样。

## D14 的漏洞（11-17 发现并修了）

原来的 D14 只看"哪个函数最先开始执行"。干净盲测里 NNSmith F036 的 agent 先调一次官方入口 `random_model_gen`（这次调用到不了目标），再自己构造 `GuidedGen` 去跑目标，driver 注释和 `entry_reason` 里都老实写了。harness 给的是 D14 eliminated。这是 harness 的错：入口被调用了，目标并没有经过它。

现在 D14 还要求**目标行执行时 `call_chain[0]` 仍在运行**（追踪器记录调用栈，`fidelity.entry_on_stack`）。入口先开始、目标却在入口之外执行时，D14 是 residual（写了原因）或 refuted（没写）。有测试，去掉修复后测试失败。对所有测试包重新审计的结果：

| 测试包 | 之前 | 现在 |
|---|---|---|
| NNSmith F035 chain-1、半盲 | L3 | L2 |
| FlexPrefill F008 chain-1 | L3 | L2 |
| NNSmith F036 干净盲测 | D14 eliminated | D14 residual（档位仍 L1） |

**所以第一版这份文档里"调用链让 F035 和 F008 升到 L3"的结论是错的**，是 D14 漏洞造成的。同时修了另一处（裸 `raise` 的 D2，`CONFIDENCE_SPEC.md` §18.2），NNSmith F001 从 `invalid` 变成 `yes`/L1。

## 结果

D14=eli 是入口检查已消除，res 残余，ref 被推翻；D3 同理。括号里是 token 数和用时。"earlier"是之前的归档运行（当时 agent 能读 `agent_results/`，也没有调用链信息）。

| finding | earlier | chain-1 | chain-2 | chain-3 | half-blind | clean-blind |
|---|---|---|---|---|---|---|
| nnsmith-F001 | - | yes/L1 D14=eli D3=res (3.6M, 21min) | - | - | - | - |
| nnsmith-F003 | inconclusive/invalid D14=res D3=res (2.8M, 12min) | inconclusive/invalid D14=res D3=res (3.9M, 24min) | - | - | - | - |
| nnsmith-F004 | yes/L1 D14=eli D3=res (3.7M, 12min) | yes/L1 D14=eli D3=res (2.1M, 9min) | yes/L1 D14=eli D3=res (0.7M, 5min) | yes/L1 D14=eli D3=res (2.5M, 5min) | yes/L1 D14=eli D3=res (2.3M, 20min) | yes/L1 D14=eli D3=res (1.3M, 9min) |
| nnsmith-F012 | yes/L1 D14=res D3=res (1.6M, 6min) | yes/L1 D14=eli D3=res (2.3M, 14min) | - | - | - | - |
| nnsmith-F018 | - | yes/L1 D14=eli D3=res (3.4M, 9min) | - | - | - | - |
| nnsmith-F034 | yes/L1 D14=res D3=res (2.5M, 7min) | yes/L1 D14=res D3=res (2.9M, 8min) | - | - | - | - |
| nnsmith-F035 | yes/L2 D14=res D3=eli (3.1M, 12min) | yes/L2 D14=res D3=eli (3.1M, 13min) | yes/L2 D14=res D3=eli (2.9M, 13min) | yes/L3 D14=eli D3=eli (3.7M, 15min) | yes/L2 D14=res D3=eli (2.8M, 24min) | yes/L2 D14=res D3=eli (4.7M, 22min) |
| nnsmith-F036 | yes/L1 D14=res D3=res (2.6M, 7min) | yes/L1 D14=res D3=res (2.9M, 7min) | yes/L1 D14=res D3=res (2.2M, 10min) | yes/L1 D14=res D3=res (1.9M, 5min) | yes/L1 D14=res D3=res (4.1M, 23min) | yes/L1 D14=res D3=res (4.0M, 14min) |
| flexprefill-F007 | yes/L2 D14=res D3=eli (3.8M, 12min) | yes/L2 D14=res D3=eli (2.9M, 11min) | yes/L2 D14=res D3=eli (2.3M, 12min) | yes/L2 D14=res D3=eli (2.6M, 11min) | yes/L1 D14=res D3=ref (4.0M, 17min) | yes/L2 D14=res D3=eli (1.8M, 12min) |
| flexprefill-F008 | yes/L2 D14=res D3=eli (1.8M, 7min) | yes/L2 D14=res D3=eli (2.1M, 10min) | yes/L2 D14=res D3=eli (3.7M, 19min) | yes/L2 D14=res D3=eli (4.1M, 22min) | yes/L2 D14=res D3=eli (4.3M, 23min) | yes/L2 D14=res D3=eli (2.7M, 28min) |

| condition | runs with a package | D14 eliminated | level L1 | L2 | L3 | invalid/n/a |
|---|---|---|---|---|---|---|
| earlier | 8 | 1 | 4 | 3 | 0 | 1 |
| chain-1 | 10 | 4 | 6 | 3 | 0 | 1 |
| chain-2 | 5 | 1 | 2 | 3 | 0 | 0 |
| chain-3 | 5 | 2 | 2 | 2 | 1 | 0 |
| half-blind | 5 | 1 | 3 | 2 | 0 | 0 |
| clean-blind | 5 | 1 | 2 | 3 | 0 | 0 |

## 读法

**1. 调用链有帮助，但没有想象的大。**
* D14 eliminated：之前的 8 个测试包里 1 个，chain-1 的 10 个里 4 个（F001、F004、F012、F018），chain-2 是 1 个，chain-3 是 2 个。F012 和 F018 的 D14 是调用链带来的（F012 之前是 residual，F018 之前没有测试包）；F004 一直是 eliminated（调用链只有两层）。
* **38 个测试包里只有 1 个 L3**（NNSmith F035 的 chain-3，目标确实在入口里执行）。L3 对这批 Finding 不是常态，一次运行的 L3 不能当结论。

**2. 重复运行：判定稳定，档位基本稳定。** 五条 Finding 各三次，判定 15 次全是 `yes`；档位三次相同的有 4 条，只有 F035 是 L2、L2、L3。样本很小，一个模型。

**3. 盲测：干净盲测的结果和白盒相同。** 五次干净盲测全是 `yes`，档位 L1、L2、L1、L2、L2（F004、F035、F036、F007、F008），**和白盒 chain-1 的五个档位逐条一样**；D14 eliminated 也都只有 F004 一条。半盲测里 FlexPrefill F007 低一级（D3 被推翻，agent 写的 oracle 没被变异体检验到）。成本：干净盲测平均 2.9M token、17 分钟、64 个工具调用，白盒是 2.7M、11 分钟、54 个。**在这五条 Finding 上没有看到"知道规则才能拿到某个档位"的证据**：agent 靠任务文本和 `lint`、`run` 的反馈就达到了同样的档位。n=5，一个模型，不能外推。

**4. agent 读源码发现的两个调用链问题，step 4 的静态分析给不出（已写进 `REQUESTS_TO_STEP4.md` 第 6 节）。**
* NNSmith F034、F036 的调用链最后一步是 `override`，目标在 `GuidedGen.post_process`。`GuidedGen` 在整个仓库只有定义，没有实例化，官方入口构造的是 `PureSymbolGen`。所以目标从官方入口走不到，D14 保持 residual。
* FlexPrefill F007：目标守卫检查传入列表的长度，而官方入口里这些列表的长度由构造过程决定，守卫从入口不可能为假。step 4 记为 `solved`。F007 的 L2 应读作"直接调内部函数可复现"。

**5. 裸 `raise` 的缺口已修。** `raise` 只在守卫成立时执行，对照点到不了目标行，原来 D2 求不到值，测试 `invalid`。现在在 `raise` 外层 `if` 的头上求条件。NNSmith F001、FlexPrefill F019 变成 `yes`/L1。NNSmith F003 仍是 `invalid`：它的 `raise e` 在 `except` 里，而且 D6 被推翻。

## 限制

* 同一个模型（x-test-2），五条 Finding 三次重复，十条 Finding 一次。没有真值，没有显著性检验。
* "earlier"和 chain-1 之间有三个变量同时变了：任务文本有了调用链，`agent_results/` 被隐藏，agent 指令加了一段。chain-1 到 chain-3 是同一个条件。
* 重复运行是同一批次内顺序启动，没有随机化顺序。
* 干净盲测里 agent 仍然有指令文件（要求做什么、有哪些检查名字），只是没有规则和源码；`lint` 和 `run` 的反馈会泄露一部分规则（"next_steps"写明哪个 defeater 没消除、怎么消除）。这是有意保留的：它是 agent 的正常工作界面。
* **D5 对机器负载敏感。** NNSmith 的 `random_model_gen` 用 `max_gen_millisec` 做时间限制，三个重新审计并行时，F035 chain-3 的一个邻点探测在目标判定前超时，D5 变成 open，档位从 L3 掉到 L1。单独重跑两次都是 L3，上面的表用单独重跑的结果。这是安全方向的误差（只会降档），但说明审计结果和并行度有关。
* D14 现在更严，但"入口在运行"仍不等于"这条路径是产品里真实会走的路径"：参数是 agent 选的，调用链是静态分析的，两者都可能有错。

## 结果写进了报告

重新审计后的测试包已写进 `results/e2e/`：FlexPrefill 29 条已测（29 个 `yes`：L3 6、L2 7、L1 16），NNSmith 22 条已测（21 个 `yes`：L2 1、L1 20；1 个 `invalid`）。取 chain-1 而不是最好的一次，避免挑选：规则是"当前流程的第一次运行"。
