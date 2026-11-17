# check_limits：交接说明（2026-11-17，FlexPosit 冷启动后更新）

给接手的 code agent。先读本文，再读 `CONFIDENCE_SPEC.md`（规则）、`CONTRACT_TEST_REPORT.md`（接口）、`EXPERIMENTS.md`（最近的实验）。
这个目录是 `cs6223-limitation-pipeline/checklimits/`（下称 C），仓库根是 `/home/somehow6/lesson/CS6223`，分支 `somehow6/check_limits`。

## 0. 新论文冷启动已跑通（FlexPosit，2026-11-17）

一篇没见过的论文（FlexPosit，MICRO 2026，arXiv 2609.04724，仓库 `hplp/FlexPosit` @ `e42a2191a72c`）从零跑完整条 pipeline：
`pipeline init` → `pipeline run flexposit --pdf ... --run-paper-side`（步骤 1 到 4，41 条 Finding）→ `checklimits test flexposit --provision --run-agent --workers 3`。
测试侧结果：41 条全部在 `results/report/flexposit/LIMITATIONS.md`（1:1 通过）；测了 12 条：8 个 `yes`（L1 7、L2 1），4 个 `inconclusive`/`invalid`（F001、F006、F007、F028，D2 被推翻，F028 还有 D12）；
没测 29 条：`no_code_location` 19（论文侧或无代码位置）、`outcome_unsupported` 10（效果类型 `other`）。档位仍未校准。
这是**一次**冷启动，没有人工核对 q2，不要写成准确率。

冷启动时发现并处理的问题（都不需要人工安装步骤，但要记下）：
* 依赖：需要 `pip install -e ".[llm,verify,dev]"` 和 `python -m pipeline setup-paperside`（装到 `findlimit`）。
* **SoCLaaS 直连超时：** `codeside` 读 `SOCLAAS_BASE_URL`，但论文侧（`team_paper_side.py`、`pi-mechanism-agent/run.mjs`、`run-adjudication.mjs`）原来写死了地址。已改成读 `SOCLAAS_BASE_URL`（默认值不变），超时读 `SOCLAAS_TIMEOUT`（默认 300 秒，原来 90 秒）。这是 Zhaopeng 目录里的小改动，需要告诉她。
* 跑 pipeline 的 shell 里：`SOCLAAS_BASE_URL=http://127.0.0.1:8787/v1`、`SOCLAAS_API_KEY=占位值`、`SOCLAAS_MODEL` 取自 env 文件（只取模型名）。中继加真 key，pipeline 进程见不到真 key。
* 中继对连接失败和 502/503/504 重试 2 次（`relay.py`，`UPSTREAM_RETRIES`）。之前一次上游 502 就让论文侧中止；论文侧不会续跑不完整的请求（`*.raw.request.json` 留着会报 "Prior incomplete request preserved"），续跑时只删没有结果的那一个请求文件。
* `pipeline test` 仍不透传 `--provision`，所以这次直接用 `python -m checklimits test ... --results-root <pipeline 根>/results`。
* `results/tests/flexposit/*/attempt/_pyext` 每个约 7MB（agent 的编译产物），没有提交。
* 不要用 `pkill -f "pipeline run ..."`，会杀到自己的 shell。

## 1. 项目是什么

CS6223 课程项目的测试侧（Shanghao）。对研究代码的"limitation Finding"（step 4 的输出，`results/step4/<artifact>/limitations_for_tests.json`），
由 code agent（opencode，模型 `x-test-2`，经本地中继）设计一个 CPU 上的测试，确定性 harness 重跑、审计 agent 声明的内容，
给出判定（`yes` / `no` / `inconclusive`）和置信档位（L0 到 L3，`invalid`，`n/a`）。档位由固定规则从 defeater D1 到 D14 的状态算出，
不是 LLM 打分，也不是数值分。**档位未校准**，所有报告都要这样标。

最终目标（`docs/E2E_PLAN_P0_2026-11-15.md`）：给一篇没见过的论文和它的仓库，一条命令序列产出 `LIMITATIONS.md`。
三人分工：Wanting（代码侧、step 4、`pipeline/`），Zhaopeng（论文侧），Shanghao（本目录：测试执行和报告）。

## 2. 用户的规则（必须遵守）

* 回复用中文，简短平实。提交信息用英文。
* Python 环境只用 conda 的 `findlimit`：`/home/somehow6/miniconda3/envs/findlimit/bin/python`（3.14）。不要新建别的环境。例外：`C/scratch/` 下的 pip venv（被测代码的环境，临时，可删）。
* 只改 `C/` 下的文件。不碰 `codeside/`、`schema/`、`paperside/`、根目录 `pyproject.toml`、`slides/`、`docs/`、`pipeline/`（那些是别人的）。不改 `third_party/`。
* **密钥：** 绝不打印或提交 `/home/somehow6/LLM_API_KEY/` 下任何内容。SoCLaaS 只通过 `set -a; . soclaas.env; set +a` 加载给中继；OpenAI 的 key 文件（路径 `LLM_API_KEY/openai_ys/openai_swl_12_28.txt`，只读它的路径，不读内容到输出）只由 `labels llm` 在内存里使用。直连 SoCLaaS 会超时，出站要绑 eth0（中继已处理）；api.openai.com 直连可用。
* 小提交，`git add` 用具体路径（不要 `git add -A` 顶层），不 force push，不改历史。推送已被批准；**每次推送前**扫描待推送提交里是否有真实密钥（两把：SoCLaaS 和 OpenAI），做法见 §8。
* 删文件、sudo、系统网络改动、范围之外的事：先问。
* `scratch/`、`runs/` 被 git 忽略。`locks/toy/` 也忽略。

## 3. 代码和文档地图（C 下）

| 路径 | 内容 |
|---|---|
| `checklimits/` | Python 包。`harness.py` 编排，`runner.py`/`child.py`/`tracer.py` 执行和追踪，`confidence.py` 规则，`audit.py`/`fidelity.py`/`mutate.py`/`bva.py` 检查，`adapter.py` 读 step 4 |
| `checklimits/e2e.py`, `testreport.py` | `test`/`report`/`envcheck`：每条 Finding 一份 `report.json`，汇总 `LIMITATIONS.md`，1:1 检查，退出码 |
| `checklimits/agent_*.py` | agent 层：`agent_cli`（task/init/lint）、`agent_loop`（bwrap 沙箱 + 修复回环）、`agent_batch`（选取、批量、reaudit）、`agent_service`（干净盲测的服务） |
| `checklimits/provision.py` | `provision`：建 `scratch/venv_<名字>`，按仓库钉的版本装依赖，跑仓库自己的测试，写 `PREFLIGHT.md` |
| `checklimits/labels.py`, `llm_label.py` | 人工标注表、一致性、LLM 第一遍标注 |
| `checklimits/bench.py` | 故障注入基准（82 个 case） |
| `agent/INSTRUCTIONS.md`, `agent/cl`, `agent/cl_client.py` | agent 的技能文档和 `cl` 包装 |
| `tests/` | 300 个测试，约 90 秒 |
| `results/e2e/` | 五个 artifact 的报告样例（`tests/<a>/<finding>/report.json`，`report/<a>/LIMITATIONS.md`） |
| `results/bench/` | 基准结果 |
| `labels/` | 20 条标注表，基线 `sheet_shanghao.csv`，`llm/` 是 LLM 第一遍，`context/` 是每条的 driver 全文 |
| `agent_results/` | 早期 agent 测试包的归档（agent 在沙箱里读不到） |
| `PLAN.md` §11 | 决策日志（第 1 到 14 条） |

文档：`CONFIDENCE_SPEC.md`（§1 到 §20，规则和每次修订）、`EXPERIMENTS.md`、`BATCH_RESULTS.md`、`NNSMITH_RESULTS.md`、`AGENT_RESULTS.md`、
`S4B_OTHER_EFFECTS.md`、`PREFLIGHT_FLEXPOSIT.md`、`REQUESTS_TO_STEP4.md`（给 Wanting 的请求，**第 6 节还没转给她**）、`CONTRACT_TEST_REPORT.md`。

## 4. 怎么跑

全部在 C 目录下（从仓库根跑 `python -m checklimits` 会因目录同名失败；测试要在 `cs6223-limitation-pipeline/` 下跑）。

```bash
PY=/home/somehow6/miniconda3/envs/findlimit/bin/python
cd cs6223-limitation-pipeline && $PY -m pytest -q checklimits/tests            # 300 passed
cd checklimits
$PY -m checklimits envcheck <artifact>                                         # 环境预检
$PY -m checklimits test <artifact> [--run-agent] [--only ID] [--provision] [--strict] [--results-root DIR] [--attempts-root DIR]
$PY -m checklimits report <artifact>
$PY -m checklimits batch --artifact nnsmith --batch-id X --only nnsmith-F004 [--blind] --workers 3   # 只跑 agent
$PY -m checklimits reaudit --root <dir of packages> --out scratch/<x>          # 不用 agent，用当前规则重新审计
$PY -m checklimits bench --out scratch/bench_x --workers 3                      # 82 个 case，约 14 分钟
$PY -m checklimits provision <名字> --repo-dir <checkout> --commit <hash> --extras dev
$PY -m checklimits labels sample|evaluate|llm|compare|context|baseline|refresh-key ...
cd .. && $PY -m pipeline test <artifact>                                       # Wanting 接的入口，等价于上面的 test
```

**agent 运行需要中继：**
```bash
cd C; rm -f runs/relay.log; (set -a; . /home/somehow6/LLM_API_KEY/SoCLaaS/soclaas.env; set +a; nohup $PY -m checklimits.relay --port 8787 --log runs/relay.log > runs/relay.stderr 2>&1 &)
# 用完按 PID 关：ps -eo pid,args | grep "[c]hecklimits.relay" | awk '{print $1}' | xargs -r kill   （不要 pkill -f，会杀到自己的 shell）
```
一次 agent 运行约 5 到 30 分钟，1 到 4M token（含重复发送的上下文）。批量用 `--workers 3`。
**不要在 agent 运行或并行重审的同时做对时间敏感的审计**（见 §7 的 D5）。

## 5. 当前结果（`results/e2e/`，规则版本见 CONFIDENCE_SPEC §18 到 §20）

| artifact | Finding | 已测 | 结果 |
|---|---|---|---|
| FlexPrefill | 65 | 29 | 29 个 `yes`：L3 6、L2 7、L1 16 |
| NNSmith | 38 | 22 | 20 个 `yes`：L2 1、L1 19；2 个 `inconclusive`/`invalid`（F003、F009） |
| SparTA、InfiniGen、MInference | 82、31、73 | 0 | 仓库没检出（全是 `env_unavailable` 或 `no_code_location`） |

没测的原因都写在 `report.json` 的 `not_run`（8 种原因码，`CONTRACT_TEST_REPORT.md` §4）。
基准（82 个 case）：假阳性 0，15 个 `yes` 全对，`no` 几乎没有（D3 没消除就不报 `no`，所以错的 `no` 为 0，对的 `no` 也只剩 1 个）。
调用链实验：38 个测试包里只有 1 个 L3；D14 eliminated 在 chain-1 的 10 个包里有 4 个。干净盲测和白盒的档位逐条一样（n=5）。

## 6. 这一阶段做了什么（按时间）

1. 第二个 artifact（NNSmith）：发现并修了模块级目标、`reject` 标在不能抛异常的语句上、稳定性哈希太严三个 harness 缺陷。
2. E2E 关键路径（依据 `docs/E2E_PLAN_P0_2026-11-15.md`）：`test`/`report`/`envcheck`、契约、`not_run` 原因码、1:1 检查。Wanting 接了 `pipeline test` 和 step 4 的调用链、效果标签检查。
3. 用调用链重跑 agent（A2/A4），重复三次，半盲和干净盲测（S5）；FlexPosit 预检（B1）；82 个 case 的基准（S5c）；`other` 类效果的分析（S4b，决定不实现新 oracle）。
4. 发现沙箱当时没隐藏 `agent_results/`（早期批量里 agent 能读别的 Finding 的测试包），已隐藏并在结果文档补记。
5. 用户批准的四项改动：`no` 只在 D3 已消除时报告；裸 `raise` 目标在守卫上求 D2；LLM（gpt-6.1-sol）先标注；干净盲测（`cl` 经 Unix socket 交给沙箱外的服务）。
6. **发现并修了 D14 漏洞：** 原来只看"哪个函数最先开始"，agent 先调一次入口、再直接调目标函数也算通过。现在要求目标行执行时入口仍在运行。**撤回了"调用链让 F035、F008 升到 L3"的结论。**
7. 人工基线（用户的 `labels/sheet_shanghao.csv`）发现 NNSmith F009 的方向反了（agent 谓词与 Region 条件矛盾，harness 却给 `yes`）。已加谓词与 Region 条件的交叉检查（D2，§20），F009 现在 `invalid`。
8. 验证了 `test --run-agent` 的真实路径（NNSmith F018、F025，各一次 agent 运行，都是 `yes`/L1，报告和 testcase 通过 `codeside.cli validate`）。

## 7. 已知问题和注意

* **D5 对机器负载敏感。** NNSmith 的 `random_model_gen` 用 `max_gen_millisec` 做时间限制，并行审计时邻点探测可能超时，D5 变 `open`，档位掉级（F035 chain-3 在 3 个并行 worker 下 L3 掉到 L1，单独跑是 L3）。只会降档，不会升档。重审时用 `--workers 1` 或 2，别和 agent 运行同时做。
* **D14 的覆盖范围：** 入口在运行，不等于这条路径是产品真实会走的路径；调用链是静态分析的，有错的（NNSmith F034、F036 的 `override` 步骤指向从未被实例化的 `GuidedGen`；FlexPrefill F007 的守卫从入口不可能为假）。这些已写进 `REQUESTS_TO_STEP4.md` §6，**还没有转给 Wanting**。
* **早期批量运行（FlexPrefill 的 b1/b2，NNSmith 的 n0/n1）当时 agent 能读 `agent_results/`**（约 24 到 27 次运行提到它）。`results/e2e/` 里的测试包是后来用隐藏之后的流程重跑过的一部分，不是全部。
* `labels/` 基线的 q2（测试是否有效）基本是空的：审阅者没拿到 driver 源码，写了 `Unverified`（19/20）。`labels/context/Lxx.md` 已经补了 driver 全文，等人补 q2。q1（断言成立）已有：18 条 `yes` 里 16 条成立（Wilson 0.67 到 0.97）。LLM 与基线的 q1 一致率 17/18（唯一不同：flexprefill-F013，`q_len==1` 的前置条件）。
* 档位没有校准，基准是我们自己编的故障，n 很小。别把档位写成准确率。
* 仍然 `invalid`：NNSmith F003（`raise e` 在 `except` 里，且 D6 被推翻）。F019、F022 因 Region 条件含函数调用，谓词的 D2 只能是 residual。
* `results/tests/nnsmith/`、`results/report/nnsmith/`、`results/tests/sparta/`、`results/report/sparta/`（在 `cs6223-limitation-pipeline/results/`，不在 C 下）是我跑 `pipeline test` 写的，**未提交**，已与 `checklimits/results/e2e/` 同步。留不留由用户决定。
* 仓库根有几个用户自己的未跟踪文件（`.gitignore`、`docs/E2E_PLAN_P0_2026-11-15.md`、`shanghao_*`、`slides/`），不要动。

## 8. 提交和推送

```bash
cd /home/somehow6/lesson/CS6223
git add <具体路径>; git commit -m "<英文说明>"
(set -a; . /home/somehow6/LLM_API_KEY/SoCLaaS/soclaas.env; set +a; git log -p HEAD --not --remotes | OKF=/home/somehow6/LLM_API_KEY/openai_ys/openai_swl_12_28.txt python3 -c "
import os,sys
d=sys.stdin.buffer.read(); ks={'soclaas':os.environ['SOCLAAS_API_KEY'].encode(),'openai':open(os.environ['OKF'],'rb').read().strip()}
print({n:(k in d) for n,k in ks.items()})")      # 必须全是 False
git diff --name-only origin/somehow6/check_limits..HEAD | grep -vc "^cs6223-limitation-pipeline/checklimits/"   # 必须是 0
git push origin somehow6/check_limits
```

## 9. 下一步（按优先级）

1. ~~新论文 P = FlexPosit 的真正冷启动~~ 已完成（见 §0）。**原来的描述：**：等 Wanting 和 Zhaopeng 产出 `data/flexposit/` 和 `results/step4/flexposit/`（W4、Z4）。到手后：
   `python -m pipeline test flexposit --run-agent`。环境部分已备好：`PREFLIGHT_FLEXPOSIT.md`（pinned commit `e42a2191a72c…`，60 个仓库测试通过，无人工步骤），`test --provision` 能自动建 venv。
   注意 `pipeline test` 还没有透传 `--provision`，需要 Wanting 加（`CONTRACT_TEST_REPORT.md` 已写）。冷启动之前，"新论文端到端"只有各段分别验证过，没有整体验证过。
2. **把 `REQUESTS_TO_STEP4.md` 转给 Wanting**（尤其 §6：`override` 指向未实例化的类、列表长度类守卫求解器看不出不可行、裸 `raise` 的约定）。
3. **标注：** 补基线的 q2（用 `labels/context/`），然后 `labels evaluate`。想要更有意义的数字就扩大样本（`labels sample --n 40 --out labels40`，是一批新的抽样，不保证包含现在这 20 条；规则改了之后对旧的 key 用 `labels refresh-key`）。LLM 第一遍用 `labels llm`（见 §4，需要 `--key-file`）。
4. D5 的负载敏感：可以考虑给探测加重试，或在 `reaudit`/`test` 里默认降低并行度。
5. S4a（论文侧 Finding 按分支或异常测）依赖 Zhaopeng 的 Z3（可测性提示）；S4b 已决定不做（`S4B_OTHER_EFFECTS.md`）。
6. 已完成、不用再做：`no` 规则、裸 `raise` 的 D2、LLM 标注、干净盲测、82 个 case 基准（用最终规则重跑过，结果不变）。

## 10. 容易踩的坑

* `tests/` 里用 `from toyhelper import build`（不是 `tests.toyhelper`）。
* 测试里用 `Path("/tmp/...")` 做沙箱路径要小心：bwrap 的 `/tmp` 是 tmpfs。agent 运行目录在 `C/scratch/agent_runs/`。
* `agent_loop.HIDE_PATHS_DIRS` 决定 agent 看不到什么；`SCRATCH_KEEP_RO` 自动包含 `scratch/venv*`。新加会泄露答案的目录要加进去。
* 改 harness 规则之后：重跑 `bench`、用 `test <artifact>` 重新审计 `results/e2e/`、`labels refresh-key`，并在 `CONFIDENCE_SPEC.md` 加一节写清前后差别。不要看着基准调阈值（`no` 规则就是看了基准定的，文档里已经写明）。
* `checklimits test` 里选择测试包的规则：`--attempts-root` 给的顺序决定优先级，默认是 `<results-root>/tests/<artifact>/`（上次测过的副本）先，再 `agent_results/`；同一个根里按名字取最后一个。想让新的 agent 包生效，把它放进 `scratch/<x>/<名字>/attempt/` 并用 `--attempts-root scratch/<x>`。
* 报告里的 `generated_at` 每次不同，所以重新生成会让 `results/e2e/` 大量文件出现 diff，这是正常的。
