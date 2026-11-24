# Z3：两篇论文怎样交给 Shanghao 测试

**当前交付是有源码依据的测试计划与可读取的契约样例，不是已经运行的测试。** FlexPrefill 21 条、NNSmith 6 条原有负项均已逐条留档；其中各展开一个案例，其他项仍有语义或输入构造待办。原三类判定未改写，模型 API 和目标执行均为零。

## 先对齐真实契约

2026-11-16 直接读取 Teams 附件：

- [CONTRACT_TEST_REPORT.md](https://nusu-my.sharepoint.com/:t:/g/personal/shanghao_liu_u_nus_edu/IQAmkKzVXHhvSbK2ezUP1tviAf6yW0hhSdr7v-Kqfa9LWS4)：输入是0.2.0的 `limitations_for_tests.json`；每个Finding保留一份 `report.json`；未测的 verdict/level 必须是null；档位未校准。
- [REQUESTS_TO_STEP4.md](https://nusu-my.sharepoint.com/:t:/g/personal/shanghao_liu_u_nus_edu/IQCK6nmh1zVpRrzfq2kFPE6NATEWLvd6mVtgqo3H6hjRV_8)：真实调用链与逐层参数；reject只对应能抛异常的语句，path_change对应if/while本身；不能给返回值/数值差异乱贴标签。

实际消费者代码取自 Shanghao 分支 `1753dab2dda1c088f0aeb0546a5d3755f8ebf947`，各包记录源码哈希。

| 交给谁 | 文件 | 含义 |
|---|---|---|
| Wanting / Shanghao | `testability_hints.json` | 原行为ID、代码位置、调用链、触发/对照配方、oracle、阻塞与适用边界 |
| Shanghao 的现有adapter | `limitations_for_tests.json` + `artifact.json` | 两个独立的paper-origin契约fixture，ID带Z3，未覆盖真实step4输出 |
| 你们一起看 | `consumer_contract_check.json` | 消费者实际读取和分类结果 |
| 报告侧 | `contract_output/tests/.../report.json`、`contract_output/report/.../LIMITATIONS.md` | 使用实际报告库生成的未运行记录，1:1保留条目 |

## 为什么补了位置，当前仍然不执行

实测调用 `load_task_step4` 能读入两个fixture，位置也都存在。但 `region_from_limitation` 明确拒绝 `origin=paper`，所以原生Region数为0，分类器仍返回 `no_code_location`。这里不是位置丢了，是消费者尚未为论文侧位置建立Region。

即使先看旁表里的拟议Region，两条效果都需要自定义oracle，当前 `other → suspicious` 没有对应效果检查。我们保持paper来源和other标签，未伪装成code来源、reject或fallback。

## 案例一：累计分数恰好等于 γ

论文：flexprefill；原行为 `M08-B05`；原claim `flexprefill:M08-B05`。关联真实step4 Finding：`['flexprefill-F030']`。这是衍生Z3样例，不是新发现。

[完整交接目录](../handoffs/z3-v1/flexprefill/) · [全部提示](../handoffs/z3-v1/flexprefill/testability_hints.json)

### 论文要求

PDF p.6, text lines 55-61

```text
# Sort vertical and slash attention scores
Iv ← argsort(av)
Is ← argsort(as)
# Obtain the minimum computational budget
making the sum of the scores exceeds γ
Kv ← min{k : Pi∈Iv [1:k] av[i] ≥ γ}
Ks ← min{k : Pi∈Is[1:k] as[i] ≥ γ}
```

### 真实代码位置

`flex_prefill/ops/flex_prefill_attention.py:1590–1590`，所属函数 `flex_prefill/ops/flex_prefill_attention.py::score_cover_topk`。

```python
    topk = torch.sum(cumsum_x <= score, dim=-1) + 1
```

上下文 `flex_prefill/ops/flex_prefill_attention.py:1588–1591`：

```python
def score_cover_topk(x: torch.Tensor, score: float):
    cumsum_x = torch.cumsum(torch.sort(x, dim=-1, descending=True).values, dim=-1)
    topk = torch.sum(cumsum_x <= score, dim=-1) + 1
    return topk
```

### 调用链与参数怎样传过去

`flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention` → `flex_prefill/ops/flex_prefill_attention.py::get_active_blocks`

```python
    block_idx = get_active_blocks(
        q,
        k,
        v,
        block_size,
        gamma,
        math.ceil(min_budget / block_size),
        math.ceil(max_budget / block_size),
        tau,
        gqa_interleave,
    )
```

```json
{
  "q": "q",
  "k": "k",
  "v": "v",
  "block_size": "block_size",
  "gamma": "gamma",
  "tau": "tau",
  "min_budget": "ceil(min_budget / block_size)",
  "max_budget": "ceil(max_budget / block_size)"
}
```

`flex_prefill/ops/flex_prefill_attention.py::get_active_blocks` → `flex_prefill/ops/flex_prefill_attention.py::score_cover_topk`

```python
    num_vertical_blocks = score_cover_topk(vertical, gamma) // 128 + 1
```

```json
{
  "x": "vertical",
  "score": "gamma"
}
```

### 触发条件和拟议输入

At score_cover_topk, a sorted cumulative probability equals gamma exactly.

```json
{
  "trigger_recipe": {
    "frame": "score_cover_topk",
    "arguments": {
      "x": {
        "shape": [
          1,
          1,
          512
        ],
        "dtype": "float32",
        "fill_fraction": "1/512"
      },
      "score_fraction": "127/512"
    }
  },
  "control_recipe": {
    "frame": "score_cover_topk",
    "arguments": {
      "x": {
        "shape": [
          1,
          1,
          512
        ],
        "dtype": "float32",
        "fill_fraction": "1/512"
      },
      "score_fraction": "255/1024"
    }
  }
}
```

这些是helper帧的具体输入，不是假装已经构造出的Q/K。使用二进制可精确表示的分数，避免十进制误差混入。独立有理数参考计算如下；它不执行目标函数：

```json
{
  "method": "Independent exact-rational reference/counterfactual calculation; target NOT executed",
  "trigger": {
    "gamma": 0.248046875,
    "ge_prefix": 127,
    "strict_prefix": 128
  },
  "contrast": {
    "gamma": 0.2490234375,
    "ge_prefix": 128,
    "strict_prefix": 128
  }
}
```

### 怎么判，什么不能判

```json
{
  "observe": "Returned prefix count, not merely whether the helper was reached",
  "reference": "min k with cumulative >= gamma, if Algorithm 3 equation is accepted as normative",
  "pass_for_candidate": "Trigger differs from paper reference; off-equality control agrees",
  "cannot_establish": "No claim about final attention error, latency, selected block set or whole-model correctness"
}
```

尚未解决的边界：

- The paper caption says exceeds gamma while its equation says >= gamma; resolve which is normative before a bug verdict.
- Paper av and code token-score/block-score representations must be aligned; local prefix arithmetic alone is insufficient.
- Helper tensor recipe is concrete; construction of q/k producing it through the public causal attention entry is NOT solved.
- CPU testing may require dependencies/import substitutions. Disclose any extraction/mock and retain D14/fidelity doubts.

### 实际给 Shanghao 的输入

下列完整外层结构能被他的loader读取。`witness.status=unknown` 是因为没有经过正式入口求解/执行确认；局部配方另存旁表，不谎报solved。

```json
{
  "schema_version": "0.2.0",
  "witness_format": "witness-v2",
  "note": "Z3 PAPER-ORIGIN CONTRACT FIXTURE, not regenerated production step4 output. Cross-reference source_step4_finding_ids in sidecar. No target execution.",
  "findings": [
    {
      "schema_version": "0.2.0",
      "finding_id": "flexprefill-Z3-M08-B05",
      "artifact_id": "flexprefill",
      "category": "impl_deviates",
      "level": "L2",
      "limitation_ids": [
        "flexprefill-gap-M08-B05"
      ],
      "verification_ids": [],
      "scope_status": "unknown",
      "evaluated_in_paper": null,
      "effect_type": "other",
      "summary": "K_v=min{k: 前 k 个 a_v 累计≥γ}",
      "witness_hint": {
        "format": "witness-v2",
        "kind": "input_value",
        "status": "unknown",
        "trigger": null,
        "contrast": null,
        "note": "Local recipe in testability_hints.json; not a solver-certified public-entry witness",
        "effect_location": {
          "file": "flex_prefill/ops/flex_prefill_attention.py",
          "line_start": 1590,
          "line_end": 1590,
          "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
          "snippet": "    topk = torch.sum(cumsum_x <= score, dim=-1) + 1"
        },
        "location": "flex_prefill/ops/flex_prefill_attention.py:1590",
        "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
        "z3_hint_file": "testability_hints.json",
        "z3_case_id": "flexprefill-Z3-M08-B05"
      },
      "confidence": "llm_assisted",
      "priority": 2,
      "rationale": "Reviewed Z3 contract fixture derived from an existing frozen behavior; not a production step4 run.",
      "review": "unreviewed",
      "review_note": "Agent source-assisted review only; see blockers before accepting the static discrepancy.",
      "limitations": [
        {
          "schema_version": "0.2.0",
          "limitation_id": "flexprefill-gap-M08-B05",
          "artifact_id": "flexprefill",
          "origin": "paper",
          "level": "L2",
          "condition_text": "At score_cover_topk, a sorted cumulative probability equals gamma exactly.",
          "condition": null,
          "effect_type": "other",
          "effect_text": "同上：>γ 而非 ≥γ，且 //128+1 与预算截断改变前缀长度",
          "paper_evidence": [
            {
              "quote": "# Sort vertical and slash attention scores\nIv ← argsort(av)\nIs ← argsort(as)\n# Obtain the minimum computational budget\nmaking the sum of the scores exceeds γ\nKv ← min{k : Pi∈Iv [1:k] av[i] ≥ γ}\nKs ← min{k : Pi∈Is[1:k] as[i] ≥ γ}",
              "source": "paper",
              "locator": "PDF p.6, text lines 55-61"
            }
          ],
          "code_evidence": [
            {
              "file": "flex_prefill/ops/flex_prefill_attention.py",
              "line_start": 1590,
              "line_end": 1590,
              "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
              "snippet": "    topk = torch.sum(cumsum_x <= score, dim=-1) + 1"
            },
            {
              "file": "flex_prefill/ops/flex_prefill_attention.py",
              "line_start": 1591,
              "line_end": 1591,
              "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
              "snippet": "    return topk"
            },
            {
              "file": "flex_prefill/ops/flex_prefill_attention.py",
              "line_start": 1588,
              "line_end": 1591,
              "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
              "snippet": "def score_cover_topk(x: torch.Tensor, score: float):\n    cumsum_x = torch.cumsum(torch.sort(x, dim=-1, descending=True).values, dim=-1)\n    topk = torch.sum(cumsum_x <= score, dim=-1) + 1\n    return topk"
            }
          ],
          "region_ids": [],
          "provenance": "llm",
          "notes": "Static discrepancy hypothesis, not a confirmed runtime effect. Original verdict=deviates; behavior=M08-B05; external repo refs stay in code_evidence_registry.json. Equivalence: 未证明对最终 S 的覆盖质量无影响; effect_status=not_established Z3 reviewed locations and plans; not target-executed."
        }
      ],
      "verifications": []
    }
  ]
}
```

### 消费者实际输出

调用实际分类器和 `not_run_record`，未调用test/envcheck/run_agent。这里没有生成置信分数，测试verdict和level为null。原Finding的L2是研究分类，不是测试置信档位。

```json
{
  "schema_version": "checklimits-test-report/1",
  "finding_id": "flexprefill-Z3-M08-B05",
  "artifact_id": "flexprefill",
  "status": "not_run",
  "not_run": {
    "code": "no_code_location",
    "reason": "no code location (paper-side finding or no code evidence); Source locations exist, but adapter.region_from_limitation refuses origin=paper. This proposed effect also needs a custom oracle: outcome 'suspicious' has no effect check yet"
  },
  "verdict": null,
  "level": null,
  "calibrated": false,
  "confidence_label": "uncalibrated",
  "level_note": "",
  "verdict_reason": "",
  "observed": {},
  "defeaters": {},
  "open_doubts": [],
  "next_steps": [],
  "finding": {
    "category": "impl_deviates",
    "step4_level": "L2",
    "effect_type": "other",
    "priority": 2,
    "summary": "K_v=min{k: 前 k 个 a_v 累计≥γ}",
    "review": "unreviewed",
    "review_note": "Agent source-assisted review only; see blockers before accepting the static discrepancy.",
    "scope_status": "unknown",
    "witness_status": "unknown",
    "location": "flex_prefill/ops/flex_prefill_attention.py:1590",
    "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
    "condition": null
  },
  "evidence": {
    "paper": [
      {
        "quote": "# Sort vertical and slash attention scores Iv ← argsort(av) Is ← argsort(as) # Obtain the minimum computational budget making the sum of the scores exceeds γ Kv ← min{k : Pi∈Iv [1:k] av[i] ≥ γ} Ks ← min{k : Pi∈Is[1:k] as[i] ≥ γ}",
        "source": "paper",
        "locator": "PDF p.6, text lines 55-61"
      }
    ],
    "code": [
      {
        "file": "flex_prefill/ops/flex_prefill_attention.py",
        "line_start": 1590,
        "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
        "snippet": "topk = torch.sum(cumsum_x <= score, dim=-1) + 1"
      },
      {
        "file": "flex_prefill/ops/flex_prefill_attention.py",
        "line_start": 1591,
        "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
        "snippet": "return topk"
      },
      {
        "file": "flex_prefill/ops/flex_prefill_attention.py",
        "line_start": 1588,
        "function": "flex_prefill/ops/flex_prefill_attention.py::score_cover_topk",
        "snippet": "def score_cover_topk(x: torch.Tensor, score: float): cumsum_x = torch.cumsum(torch.sort(x, dim=-1, descending=True).values, dim=-1) topk = torch.sum(cumsum_x <= score, dim=-1) + 1 return topk"
      }
    ]
  },
  "files": {},
  "provenance": {
    "source": "offline Z3 contract probe; target execution not_run",
    "findings_sha256": "0e2250ef46d48cf72d83575fb18de9874442d3d86a45d894cdeaf540019361c1"
  }
}
```

## 案例二：预算耗尽后返回 None，而非论文的失败异常

论文：nnsmith；原行为 `M08-B10`；原claim `nnsmith:M08-B10`。关联真实step4 Finding：`['nnsmith-F024']`。这是衍生Z3样例，不是新发现。

[完整交接目录](../handoffs/z3-v1/nnsmith/) · [全部提示](../handoffs/z3-v1/nnsmith/testability_hints.json)

### 论文要求

PDF p.7

```text
raise failed to find viable⟨𝑋,𝑊⟩
```

PDF p.7, text lines 43-53

```text
Search process. The overall input search algorithm (Algorithm 3)
proceeds as follows: Given a model𝑀 and time budget𝑇 , we first
randomly initialize inputs and weights⟨𝑋,𝑊⟩ (Line 2) used by the
first iteration of the search algorithm (Line 3). In each iteration, we
find the first operator (in topological order, Line 4) that produces
an FP exceptional value (Line 7). We use its loss function as an
optimization objective (Line 8) to tune ⟨𝑋,𝑊⟩. If the gradient is
neither zero nor a FP exceptional values then we move on to the
next iteration (Line 14), otherwise we restart the search with a
different initial value (Line 11 and 13). The algorithm throws an
exception (Line 16) if it does not terminate within the time budget.
```

### 真实代码位置

`nnsmith/materialize/torch/symbolnet.py:293–293`，所属函数 `nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen`。

```python
        return sat_inputs
```

上下文 `nnsmith/materialize/torch/symbolnet.py:289–290`：

```python
        if sat_inputs is None:
            TORCH_LOG.debug("[grad] no valid range found!!!")
```

### 调用链与参数怎样传过去

`nnsmith/materialize/torch/input_gen.py::PracticalHybridSearch.search_one` → `nnsmith/materialize/torch/input_gen.py::GradSearch.search_one`

```python
            return GradSearch.search_one(self, start_inp, timeout_ms)
```

```json
{
  "self": "self",
  "start_inp": "start_inp",
  "timeout_ms": "timeout_ms"
}
```

前提：`self.differentiable is true`。

`nnsmith/materialize/torch/input_gen.py::GradSearch.search_one` → `nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen`

```python
        return self.net.grad_input_gen(
            init_tensors=start_inp, use_cuda=self.use_cuda, max_time=timeout_s
        )
```

```json
{
  "init_tensors": "start_inp",
  "use_cuda": "self.use_cuda",
  "max_time": "timeout_ms/1000 when not None"
}
```

### 触发条件和拟议输入

After entry/setup succeeds, the grad_input_gen time budget expires while sat_inputs remains None.

```json
{
  "trigger_recipe": {
    "frame": "PracticalHybridSearch.search_one",
    "arguments": {
      "start_inp": {
        "x": {
          "shape": [
            1
          ],
          "dtype": "float32",
          "values": [
            1.0
          ]
        }
      },
      "timeout_ms": 0
    },
    "model_recipe": "A minimal differentiable SymbolNet (e.g. ReLU(x)), CPU; constructor/schedule to be materialized by test agent",
    "prerequisites": [
      "self.differentiable=True",
      "CPU use_cuda=False",
      "Model/optimizer setup must succeed"
    ]
  },
  "control_recipe": {
    "frame": "PracticalHybridSearch.search_one",
    "arguments": {
      "start_inp": {
        "x": {
          "shape": [
            1
          ],
          "dtype": "float32",
          "values": [
            1.0
          ]
        }
      },
      "timeout_ms": 1000
    },
    "expected_behavior": "Valid input may be returned within budget; collect actual runtime evidence, not guaranteed by this recipe"
  }
}
```

`timeout_ms=0` 从search_one进入，除以1000后是 `max_time=0`。初始化成功后while不进入，sat_inputs仍为None，走到return。不能改用外层 `search(max_time_ms=0)`，因为那样外层就跳过循环，根本到不了目标。模型构造和正向对照仍需要Shanghao实际实现、运行确认。

### 怎么判，什么不能判

```json
{
  "observe": "Whether failure is raised, the return value, and target-return reachability",
  "reference": "Paper explicitly throws failure on budget exhaustion; pinned code returns sat_inputs (None if no success)",
  "pass_for_candidate": "Zero-budget search reaches return None without the paper failure exception; a successful control is returned normally",
  "cannot_establish": "Do not classify an unrelated setup exception as the claimed failure. None may be a deliberate equivalent failure protocol; review caller policy."
}
```

尚未解决的边界：

- Current harness reject cannot establish an absent exception at a return statement; do not mislabel this as reject.
- CPU model/optimizer fixture has not been built or executed.
- The experiment caller supplies return_list=True to search(), but this pinned inherited signature has no such keyword or **kwargs. Static binding mismatch blocks that experiment route; no runtime TypeError was observed here.

实验路径另有静态阻塞：

```json
{
  "call": "    n_try, sat_inputs = searcher.search(\n        max_time_ms=gen_time * 0.02 * 1000, max_sample=2, return_list=True\n    )",
  "unsupported_keywords": [
    "return_list"
  ],
  "analysis": "Static keyword/signature check only; not executed"
}
```

### 实际给 Shanghao 的输入

下列完整外层结构能被他的loader读取。`witness.status=unknown` 是因为没有经过正式入口求解/执行确认；局部配方另存旁表，不谎报solved。

```json
{
  "schema_version": "0.2.0",
  "witness_format": "witness-v2",
  "note": "Z3 PAPER-ORIGIN CONTRACT FIXTURE, not regenerated production step4 output. Cross-reference source_step4_finding_ids in sidecar. No target execution.",
  "findings": [
    {
      "schema_version": "0.2.0",
      "finding_id": "nnsmith-Z3-M08-B10",
      "artifact_id": "nnsmith",
      "category": "impl_deviates",
      "level": "L2",
      "limitation_ids": [
        "nnsmith-gap-M08-B10"
      ],
      "verification_ids": [],
      "scope_status": "unknown",
      "evaluated_in_paper": null,
      "effect_type": "other",
      "summary": "预算耗尽则抛出失败异常",
      "witness_hint": {
        "format": "witness-v2",
        "kind": "input_value",
        "status": "unknown",
        "trigger": null,
        "contrast": null,
        "note": "Local recipe in testability_hints.json; not a solver-certified public-entry witness",
        "effect_location": {
          "file": "nnsmith/materialize/torch/symbolnet.py",
          "line_start": 293,
          "line_end": 293,
          "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
          "snippet": "        return sat_inputs"
        },
        "location": "nnsmith/materialize/torch/symbolnet.py:293",
        "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
        "z3_hint_file": "testability_hints.json",
        "z3_case_id": "nnsmith-Z3-M08-B10"
      },
      "confidence": "llm_assisted",
      "priority": 2,
      "rationale": "Reviewed Z3 contract fixture derived from an existing frozen behavior; not a production step4 run.",
      "review": "unreviewed",
      "review_note": "Agent source-assisted review only; see blockers before accepting the static discrepancy.",
      "limitations": [
        {
          "schema_version": "0.2.0",
          "limitation_id": "nnsmith-gap-M08-B10",
          "artifact_id": "nnsmith",
          "origin": "paper",
          "level": "L2",
          "condition_text": "After entry/setup succeeds, the grad_input_gen time budget expires while sat_inputs remains None.",
          "condition": null,
          "effect_type": "other",
          "effect_text": "失败未以异常表达，改为随机输入回退",
          "paper_evidence": [
            {
              "quote": "raise failed to find viable⟨𝑋,𝑊⟩",
              "source": "paper",
              "locator": "PDF p.7"
            },
            {
              "quote": "Search process. The overall input search algorithm (Algorithm 3)\nproceeds as follows: Given a model𝑀 and time budget𝑇 , we first\nrandomly initialize inputs and weights⟨𝑋,𝑊⟩ (Line 2) used by the\nfirst iteration of the search algorithm (Line 3). In each iteration, we\nfind the first operator (in topological order, Line 4) that produces\nan FP exceptional value (Line 7). We use its loss function as an\noptimization objective (Line 8) to tune ⟨𝑋,𝑊⟩. If the gradient is\nneither zero nor a FP exceptional values then we move on to the\nnext iteration (Line 14), otherwise we restart the search with a\ndifferent initial value (Line 11 and 13). The algorithm throws an\nexception (Line 16) if it does not terminate within the time budget.",
              "source": "paper",
              "locator": "PDF p.7, text lines 43-53"
            }
          ],
          "code_evidence": [
            {
              "file": "nnsmith/materialize/torch/symbolnet.py",
              "line_start": 293,
              "line_end": 293,
              "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
              "snippet": "        return sat_inputs"
            },
            {
              "file": "nnsmith/materialize/torch/symbolnet.py",
              "line_start": 289,
              "line_end": 290,
              "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
              "snippet": "        if sat_inputs is None:\n            TORCH_LOG.debug(\"[grad] no valid range found!!!\")"
            },
            {
              "file": "nnsmith/materialize/torch/symbolnet.py",
              "line_start": 253,
              "line_end": 253,
              "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
              "snippet": "        sat_inputs = None"
            }
          ],
          "region_ids": [],
          "provenance": "llm",
          "notes": "Static discrepancy hypothesis, not a confirmed runtime effect. Original verdict=deviates; behavior=M08-B10; external repo refs stay in code_evidence_registry.json. Equivalence: 回退随机输入改变失败语义; effect_status=not_established Z3 reviewed locations and plans; not target-executed."
        }
      ],
      "verifications": []
    }
  ]
}
```

### 消费者实际输出

调用实际分类器和 `not_run_record`，未调用test/envcheck/run_agent。这里没有生成置信分数，测试verdict和level为null。原Finding的L2是研究分类，不是测试置信档位。

```json
{
  "schema_version": "checklimits-test-report/1",
  "finding_id": "nnsmith-Z3-M08-B10",
  "artifact_id": "nnsmith",
  "status": "not_run",
  "not_run": {
    "code": "no_code_location",
    "reason": "no code location (paper-side finding or no code evidence); Source locations exist, but adapter.region_from_limitation refuses origin=paper. This proposed effect also needs a custom oracle: outcome 'suspicious' has no effect check yet"
  },
  "verdict": null,
  "level": null,
  "calibrated": false,
  "confidence_label": "uncalibrated",
  "level_note": "",
  "verdict_reason": "",
  "observed": {},
  "defeaters": {},
  "open_doubts": [],
  "next_steps": [],
  "finding": {
    "category": "impl_deviates",
    "step4_level": "L2",
    "effect_type": "other",
    "priority": 2,
    "summary": "预算耗尽则抛出失败异常",
    "review": "unreviewed",
    "review_note": "Agent source-assisted review only; see blockers before accepting the static discrepancy.",
    "scope_status": "unknown",
    "witness_status": "unknown",
    "location": "nnsmith/materialize/torch/symbolnet.py:293",
    "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
    "condition": null
  },
  "evidence": {
    "paper": [
      {
        "quote": "raise failed to find viable⟨𝑋,𝑊⟩",
        "source": "paper",
        "locator": "PDF p.7"
      },
      {
        "quote": "Search process. The overall input search algorithm (Algorithm 3) proceeds as follows: Given a model𝑀 and time budget𝑇 , we first randomly initialize inputs and weights⟨𝑋,𝑊⟩ (Line 2) used by the first iteration of the search algorithm (Line 3). In each iteration, we find the first operator (in topological order, Line 4) that produces an FP exceptional value (Line 7). We use its loss function as an optimization objective (Line 8) to tune ⟨𝑋,𝑊⟩. If the gradient is neither zero nor a FP exceptional…",
        "source": "paper",
        "locator": "PDF p.7, text lines 43-53"
      }
    ],
    "code": [
      {
        "file": "nnsmith/materialize/torch/symbolnet.py",
        "line_start": 293,
        "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
        "snippet": "return sat_inputs"
      },
      {
        "file": "nnsmith/materialize/torch/symbolnet.py",
        "line_start": 289,
        "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
        "snippet": "if sat_inputs is None: TORCH_LOG.debug(\"[grad] no valid range found!!!\")"
      },
      {
        "file": "nnsmith/materialize/torch/symbolnet.py",
        "line_start": 253,
        "function": "nnsmith/materialize/torch/symbolnet.py::SymbolNet.grad_input_gen",
        "snippet": "sat_inputs = None"
      }
    ]
  },
  "files": {},
  "provenance": {
    "source": "offline Z3 contract probe; target execution not_run",
    "findings_sha256": "d80931d38bc493748f46a685b980828482f2e41423cd7f8c4c33848db768db75"
  }
}
```

## 剩余项怎么处理

所有27条保留原行为/claim ID、原判断与源码导航。未展开的项不补造已求解输入。其中11条FlexPrefill理论/实验环境项先做语义复核：论文的KKT推导不一定需要运行时代码，报告使用A100也不等于脚本必须强制GPU型号。NNSmith的“先shuffle后不断取前半”还存在与逐轮随机减半分布等价的可能，先检查这些前提再称差异。

## 交接验收和下一步

Z3的两个主案例已补：原文、精准源码、参数转换、局部触发/对照配方、oracle与阻塞。输入/输出能按契约读取、条目1:1保留；两个样例均明确未运行。

下游S4需要允许paper-origin位置建立Region，并接入“数值前缀长度”和“失败返回协议”oracle。不能仅观察一个分支就宣称论文差异已复现，也不应为了绕过门槛把other改成reject。

离线验证（从paperside运行，不调用模型，不执行目标）：

```bash
python scripts/validate_z3_handoff.py handoffs/z3-v1/flexprefill
python scripts/validate_z3_handoff.py handoffs/z3-v1/nnsmith
```

重做实际消费者读取时，运行 `scripts/probe_z3_consumer.py --help`，提供固定版本consumer checkout及目标仓库路径。只读取/分类/渲染报告，不运行test或环境预检。
