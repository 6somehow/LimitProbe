# test / report 接口契约（版本 `checklimits-test-report/1`，2026-11-15）

对应 `docs/E2E_PLAN_P0_2026-11-15.md` 的 P0-4。生产方：Shanghao。接收方：Wanting（`pipeline` 的 test 阶段）、全组（报告）。

## 1. 调用

在 `cs6223-limitation-pipeline/checklimits/` 目录下执行（从仓库根目录执行 `python -m checklimits` 会因目录同名而失败，pipeline 调用时用 `cwd=` 指定）：

```bash
python -m checklimits envcheck <artifact>                 # 环境预检，写 ENV.json
python -m checklimits test     <artifact> [选项]          # 选取、测试、写 report.json 和 LIMITATIONS.md
python -m checklimits report   <artifact> [--results-root] # 只用已有 report.json 重新生成 LIMITATIONS.md
```

`test` 的选项：

| 选项 | 含义 |
|---|---|
| `--results-root DIR` | 输出根目录，默认 `checklimits/results/e2e`。pipeline 接线时传 `<pipeline 根>/results` |
| `--attempts-root DIR`（可重复） | 查找已有测试包（attempt）的目录。默认：`agent_results/` 和 `<results-root>/tests/<artifact>/` |
| `--run-agent` | 对"能判断但没有测试包"的 Finding 运行 code agent（需要中继和 SoCLaaS 凭据，每条约 5 到 15 分钟）。不加则这些 Finding 记为 `not_run(not_attempted)` |
| `--only ID`（可重复） | 只测指定 Finding；报告仍包含全部 Finding，其余的沿用已有记录（见 §5） |
| `--workers N` | 并行度，默认 3 |
| `--fast` | 少做重复和变异（只用于冒烟，档位会变低） |
| `--strict` | 有任何 `env_unavailable` / `agent_failed` / `harness_error` 时退出码为 4 |
| `--skip-envcheck` | 不做环境预检 |
| `--provision` | 环境预检不通过、但仓库已检出时，先建 `scratch/venv_<artifact>`（`provision`：按仓库钉的版本装 torch CPU 版和依赖，不跑仓库自己的测试），再检查一次。过程写进 `ENV.json` 的 `provisioned`。pipeline 的 `test` 命令还没有透传这个选项 |

输入：`results/step4/<artifact>/limitations_for_tests.json`（schema 0.2.0）和 `data/*/artifact.json`（`artifact_id` 匹配的那个）。

## 2. 输出布局

`<results-root>` 下：

```
tests/<artifact>/ENV.json                    环境预检结果
tests/<artifact>/index.json                  汇总：输入条数、记录条数、各状态计数、1:1 检查结果
tests/<artifact>/<finding_id>/report.json    每条 Finding 一份，本文 §3
tests/<artifact>/<finding_id>/execution_report.json   仅 status=tested：harness 的完整报告（models.ExecutionReport）
tests/<artifact>/<finding_id>/testcase.json  仅 status=tested：codeside 的 TestCase 记录（`codeside.cli validate` 可校验）
tests/<artifact>/<finding_id>/attempt/       仅 status=tested：被审计的测试包副本，可重放
report/<artifact>/LIMITATIONS.md             汇总报告
```

`<finding_id>` 是 step 4 的完整 id，例如 `nnsmith-F004`。

## 3. `report.json`（每条 Finding 一份，不论是否测了）

```json
{
  "schema_version": "checklimits-test-report/1",
  "finding_id": "nnsmith-F004",
  "artifact_id": "nnsmith",
  "status": "tested",
  "not_run": null,
  "verdict": "yes",
  "level": "L1",
  "calibrated": false,
  "confidence_label": "uncalibrated",
  "level_note": "...",
  "verdict_reason": "...",
  "observed": {"positive": "AssertionError at ...", "negative": "no exception at ..."},
  "defeaters": {"D1": "eliminated", "D3": "residual", "...": "..."},
  "open_doubts": [{"id": "D3", "name": "...", "status": "residual", "evidence": "..."}],
  "next_steps": ["..."],
  "finding": {"category": "...", "step4_level": "L2", "effect_type": "path_change", "priority": 1,
              "summary": "...", "review": "worth_testing", "review_note": "...", "scope_status": "unknown",
              "witness_status": "solved", "location": "nnsmith/graph_gen.py:260", "function": "...",
              "condition": "..."},
  "evidence": {"paper": [{"quote": "...", "source": "paper", "locator": "..."}],
               "code": [{"file": "...", "line_start": 260, "function": "...", "snippet": "..."}]},
  "files": {"execution_report": "execution_report.json", "testcase": "testcase.json", "attempt": "attempt"},
  "provenance": {"findings_file": "results/step4/nnsmith/limitations_for_tests.json", "findings_sha256": "...",
                 "source": "reaudit", "attempt_origin": "agent_results/batch_nnsmith/F004-n1-f004",
                 "n_attempts_found": 1, "profile": "default-v1", "generated_at": "2026-11-15T17:00:00+08:00"}
}
```

| 字段 | 规则 |
|---|---|
| `status` | `tested`：harness 对这条 Finding 跑出了完整报告（`verdict` 仍可能是 `inconclusive`）。`not_run`：没有运行，`not_run` 字段必填 |
| `not_run` | `{"code": ..., "reason": "..."}`，`code` 取值见 §4。`status=tested` 时为 `null` |
| `verdict` | `yes` / `no` / `inconclusive`；`not_run` 时为 `null` |
| `level` | `L0` / `L1` / `L2` / `L3` / `invalid` / `n/a`；`not_run` 时为 `null` |
| `calibrated` | 现在恒为 `false`，`confidence_label` 恒为 `"uncalibrated"`。档位表示"哪些已知的出错理由被测量并排除了"，**不是**经验准确率 |
| `defeaters` | `eliminated` / `residual` / `open` / `refuted`，定义见 `CONFIDENCE_SPEC.md` |
| `open_doubts` | 所有不是 `eliminated` 的 defeater 及其证据，报告里的"未消除的疑点" |
| `evidence` | 取自 step 4 的原始数据，没有改写 |

`analysis`（可选，2026-11-18）：`not_run` 记录可带分析块，字段 `kind="analysis_only"`、`tier`（A0/A1/A2）、`assessment`、`reasoning`、`static`、`probes`、`would_confirm`、`calibrated=false`。它不是测试，`status` 仍是 `not_run`，`verdict`/`level` 仍是 `null`。见 `CONFIDENCE_SPEC.md` §22。

兼容规则：只增加可选字段，不改名、不删字段、不改枚举含义；改了就升 `checklimits-test-report/2`。

## 4. `not_run.code` 取值

| code | 含义 | 谁能解除 |
|---|---|---|
| `no_code_location` | Finding 没有代码位置（纯论文侧，或 Limitation 没有 code_evidence） | Zhaopeng（Z3 给出可测性提示和代码位置） |
| `outcome_unsupported` | 效果类型或目标语句 harness 无法判断（例如 `reject` 标在不能抛异常的语句上；`fallback` 标在赋值上；效果是 `suspicious`） | Wanting（W2 标签约定） |
| `witness_unusable` | step 4 的 witness 没有可用的 trigger（状态 `trigger_only`、`unsat`、`unknown`） | Wanting（W1、W3） |
| `env_unavailable` | 仓库没有检出，或该 artifact 的解释器、依赖不可用 | Shanghao（S3）或人工装环境。**环境失败不是 Finding 失败** |
| `input_unreadable` | Finding 或其位置读不出来（文件不存在、行号越界、JSON 缺字段） | 上游数据 |
| `not_attempted` | harness 能判断，但没有测试包，也没有开 `--run-agent` | 运行 `--run-agent` |
| `agent_failed` | 开了 `--run-agent`，agent 没有产出可审计的测试包（预算耗尽、崩溃） | 重跑 |
| `harness_error` | 重新审计已有测试包时 harness 抛了异常 | Shanghao（bug） |

## 5. 不丢条目（1:1）

* `index.json` 的 `n_input` 是 step 4 文件里的 Finding 数，`n_records` 是 `report.json` 数，`LIMITATIONS.md` 里每个 Finding 出现一次作为表格行、一次作为小节。三者必须相等且 id 集合一致，`one_to_one` 为 `true`。
* 不一致时 `test` 退出码为 3，并在 `index.json` 的 `problems` 里列出差异。
* `--only` 只限制这次运行谁去测；其余 Finding 的记录从 `<results-root>/tests/<artifact>/` 里已有的 `report.json` 沿用，没有就按 §4 记为 `not_run`。

## 6. 退出码

| 码 | 含义 |
|---|---|
| 0 | 报告完整（1:1 通过）。有 `not_run` 不影响 |
| 2 | 输入错误：artifact 未登记、findings 文件不存在或不是 schema 0.2.0 |
| 3 | 1:1 检查失败，或写出的文件无法再读回 |
| 4 | 仅 `--strict`：报告完整，但有环境、agent 或 harness 方面的 `not_run` |
| 1 | 其他未处理异常 |

`envcheck` 的退出码：0 为 `ok`，4 为 `not_ok`，2 为输入错误。

stdout 最后输出一个 JSON 对象（`artifact`、`n_input`、`counts`、`one_to_one`、`report`、`exit_code`），pipeline 可以直接解析。

## 7. 环境预检 `ENV.json`

```json
{"artifact_id": "nnsmith", "status": "ok", "reasons": [],
 "repo": {"path": "third_party/nnsmith", "exists": true, "head": "a8307f2...", "expected": "a8307f2...", "matches": true, "clean": true},
 "python": {"path": "scratch/venv_nnsmith/bin/python", "exists": true, "version": "3.11.9"},
 "imports": [{"module": "nnsmith.graph_gen", "ok": true, "error": null}],
 "execution_env": ["cpu"]}
```

`status` 为 `ok` 或 `not_ok`。`not_ok` 时，所有能判断的 Finding 记为 `not_run(env_unavailable)`，`reason` 引用 ENV.json 里的原因。预检只检查和记录，不安装任何东西。

## 8. 不在今天范围内

* `python -m pipeline test <id>` 的接线（W6）在 `pipeline/run.py`，属于 Wanting。接线只需要在 `cwd=checklimits/` 下调用 `python -m checklimits test <id> --results-root ../results`，并按 §6 解释退出码。
* 档位校准（C1）。
