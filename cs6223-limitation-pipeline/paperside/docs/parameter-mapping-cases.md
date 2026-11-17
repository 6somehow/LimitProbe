# 两个完整案例：论文参数怎样交给下游

这轮没有重新调用模型找参数。它使用既有论文分析，增加**经过原文与固定源码核对的映射样例**，用于检查最新 main（基线 `9fce6e0`）的接口。旧五篇判断没有改写；目标系统没有运行。

## 输入输出先看这一张表

| 环节 | 输入 | 输出 |
|---|---|---|
| 本次适配 | v1 交接包、固定 PDF、固定 commit 仓库、已审阅映射规格 | v2 的 `paper_side.json`，仍是 claims / scope / eval_points / bindings 四数组 |
| 追溯映射 | 某个 binding ID | `parameter_mappings.json`：原文、单位、代码类型、所属函数、声明与后续使用 |
| 消费者联调 | 明确写出的探针条件与有限输入域 | `consumer_cases.json`：实际 scope/witness 返回、是否通过、已知失败原因 |

**探针条件不是从目标代码抽出的新 limitation。** 为检查接口而设置的有限输入集合，也不是论文支持范围或真实调用链。整数性与函数所属上下文目前放在旁表，因为团队四数组接口没有相应专门字段；下游不能忽略它们直接执行 witness。

## FlexPrefill：τ → tau

完整文件：[交接目录](../handoffs/paper-side-v2/flexprefill/)。仓库版本：`a24b27bf117fd6ad4ba34b0db82c598e7786fd59`。

### 1. 作者在论文中说了什么

PDF p.6, text lines 4-5

```text
Input: Q, K, V ∈ RS×dh , τ ∈ [0, 1],
γ∈ (0, 1)
```

### 2. 对应哪段实际源码

`flex_prefill/ops/flex_prefill_attention.py:1796–1796` · `flex_prefill_attention`

```python
    tau: float = 0,
```

`flex_prefill/ops/flex_prefill_attention.py:1727–1727` · `get_active_blocks`

```python
    block_sparse_mask = kl_div < tau
```

`flex_prefill/ops/flex_prefill_attention.py:1856–1866` · `flex_prefill_attention`

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

**映射含义：** Sparse-pattern decision threshold; same scalar passed from the public attention entry to get_active_blocks.

**适用边界：** flex_prefill_attention and its get_active_blocks call; not a proof that the code and paper use an identical divergence formula

### 3. 实际输出给 Wanting 的记录

以下是四数组接口中的两条完整记录；其他原有记录仍保留在完整文件中。

```json
{
  "scope": {
    "schema_version": "0.2.0",
    "scope_id": "flexprefill-scope-001",
    "artifact_id": "flexprefill",
    "param": "sparse_pattern_threshold_tau",
    "kind": "interval",
    "lower": 0.0,
    "upper": 1.0,
    "values": null,
    "unit": null,
    "explicit": true,
    "evidence": [
      {
        "quote": "Input: Q, K, V ∈ RS×dh , τ ∈ [0, 1],\nγ∈ (0, 1)",
        "source": "paper",
        "locator": "PDF p.6, text lines 4-5"
      },
      {
        "quote": "4. Adaptive Decision: We compareDJS to a predefined thresholdτ. IfDJS <τ , the block-\nwise attention estimation adequately approximates the true distribution. Consequently, we\ncalculate ¯a for all queries, enabling query-aware sparse index selection. Otherwise, the",
        "source": "paper",
        "locator": "PDF p.4, text lines 83-85"
      }
    ]
  },
  "binding": {
    "schema_version": "0.2.0",
    "binding_id": "flexprefill-binding-001",
    "artifact_id": "flexprefill",
    "paper_term": "sparse_pattern_threshold_tau",
    "kind": "parameter",
    "code_symbol": "tau",
    "location": {
      "file": "flex_prefill/ops/flex_prefill_attention.py",
      "line_start": 1796,
      "line_end": 1796,
      "function": "flex_prefill_attention",
      "snippet": "    tau: float = 0,"
    },
    "certain": true,
    "rationale": "Static source-assisted mapping; scope-qualified, not human gold. Sparse-pattern decision threshold; same scalar passed from the public attention entry to get_active_blocks. flex_prefill_attention and its get_active_blocks call; not a proof that the code and paper use an identical divergence formula"
  }
}
```

### 4. 下游实际返回了什么

| 探针条件 | 附加测试输入域 | scope | witness 状态 | trigger / contrast | 验收 |
|---|---|---|---|---|---|
| `tau > 0.1` | `[]` | in_scope | solved | {'tau': 0.101} / {'tau': 0.1} | 通过 |
| `tau == 2` | `[]` | out_of_scope | infeasible | — / — | 通过 |
| `tau == 0.1` | `[]` | in_scope | infeasible | — / — | **已知失败，未计通过** |

**需要交给下游修正的问题：** Main witness encodes Fraction(float), so decimal equality can conflict with its 1/1000 integer grid. ScopeChecker accepts 0.1; do not classify the parameter mapping as absent.

映射 tau 不等于证明全部阈值公式实现正确。γ 的开区间仍保持原处理，未通过伪造闭区间强行激活；本次不新增 gamma 求解器约束。

## NNSmith：Pool2d 的 kw → kernel_w_size

完整文件：[交接目录](../handoffs/paper-side-v2/nnsmith/)。仓库版本：`a8307f2b8043eb64b413a9b68ba2e6a2646cae8a`。

### 1. 作者在论文中说了什么

PDF p.4, text lines 8-14

```text
def __init__ ( self , kh , kw , stride , pad ) :
self . kh , self . kw = kh , kw ...
def requires ( self , inputs : List [ AbsTensor ]) :
ih , iw = inputs [0]. shape [ -2:]
return [ self . kw > 0 , self . kh > 0 ,
self . stride > 0 , self . pad >= 0 ,
self . kw <= 2 * self . pad + iw , ...]
```

PDF p.4, text lines 58-66

```text
While our implementation includes specifications for common
operators (detailed in §4), we designed NNSmith so that it is easy
for users to write specification for additional operators. NNSmith
specifications are written using symbolic integers and abstract
tensors. An abstract tensor is specified by its data type, rank and
shape. In our implementation we specify an abstrat tensor’s data
type and rank using concrete values, and use symbolic integers to
specify its shape. As we will see later in §3.2,NNSmith uses an SMT
solver to assign concrete integers to each symbolic integer during
```

PDF p.4, text lines 79-83

```text
Constraints. The operator’s requires function (Line 10) returns
constraints that its inputs and attributes must satisfy as a list of
logical predicates. For example, among other constraints, thePool2d
operator requires that the kernel size should be greater than 0
(Line 12).
```

### 2. 对应哪段实际源码

`nnsmith/abstract/op.py:839–839` · `Pool2d.__init__`

```python
        kernel_w_size: Union[int, z3.ExprRef],
```

`nnsmith/abstract/op.py:845–845` · `Pool2d.__init__`

```python
        self.kernel_w_size = kernel_w_size
```

`nnsmith/abstract/op.py:889–889` · `Pool2d.requires`

```python
        cons.append(nnsmith_ge(self.kernel_w_size, 1))
```

**映射含义：** Pool2d kernel width; paper kw is stored as self.kernel_w_size; requires() emits its positivity constraint.

**适用边界：** Pool2d operator specification only; includes MaxPool2d/AvgPool2d inheritance, not a universal graph input bound. Positivity is necessary, not sufficient; shape/stride/padding constraints still apply.

### 3. 实际输出给 Wanting 的记录

以下是四数组接口中的两条完整记录；其他原有记录仍保留在完整文件中。

```json
{
  "scope": {
    "schema_version": "0.2.0",
    "scope_id": "nnsmith-scope-pool2d-width",
    "artifact_id": "nnsmith",
    "param": "pool2d_kernel_width",
    "kind": "interval",
    "lower": 1.0,
    "upper": null,
    "values": null,
    "unit": "elements",
    "explicit": true,
    "evidence": [
      {
        "quote": "def __init__ ( self , kh , kw , stride , pad ) :\nself . kh , self . kw = kh , kw ...\ndef requires ( self , inputs : List [ AbsTensor ]) :\nih , iw = inputs [0]. shape [ -2:]\nreturn [ self . kw > 0 , self . kh > 0 ,\nself . stride > 0 , self . pad >= 0 ,\nself . kw <= 2 * self . pad + iw , ...]",
        "source": "paper",
        "locator": "PDF p.4, text lines 8-14"
      },
      {
        "quote": "While our implementation includes specifications for common\noperators (detailed in §4), we designed NNSmith so that it is easy\nfor users to write specification for additional operators. NNSmith\nspecifications are written using symbolic integers and abstract\ntensors. An abstract tensor is specified by its data type, rank and\nshape. In our implementation we specify an abstrat tensor’s data\ntype and rank using concrete values, and use symbolic integers to\nspecify its shape. As we will see later in §3.2,NNSmith uses an SMT\nsolver to assign concrete integers to each symbolic integer during",
        "source": "paper",
        "locator": "PDF p.4, text lines 58-66"
      },
      {
        "quote": "Constraints. The operator’s requires function (Line 10) returns\nconstraints that its inputs and attributes must satisfy as a list of\nlogical predicates. For example, among other constraints, thePool2d\noperator requires that the kernel size should be greater than 0\n(Line 12).",
        "source": "paper",
        "locator": "PDF p.4, text lines 79-83"
      }
    ]
  },
  "binding": {
    "schema_version": "0.2.0",
    "binding_id": "nnsmith-parameter-pool2d-width",
    "artifact_id": "nnsmith",
    "paper_term": "pool2d_kernel_width",
    "kind": "parameter",
    "code_symbol": "kernel_w_size",
    "location": {
      "file": "nnsmith/abstract/op.py",
      "line_start": 839,
      "line_end": 839,
      "function": "Pool2d.__init__",
      "snippet": "        kernel_w_size: Union[int, z3.ExprRef],"
    },
    "certain": true,
    "rationale": "Static source-assisted mapping; scope-qualified, not human gold. Pool2d kernel width; paper kw is stored as self.kernel_w_size; requires() emits its positivity constraint. Pool2d operator specification only; includes MaxPool2d/AvgPool2d inheritance, not a universal graph input bound. Positivity is necessary, not sufficient; shape/stride/padding constraints still apply."
  }
}
```

### 4. 下游实际返回了什么

| 探针条件 | 附加测试输入域 | scope | witness 状态 | trigger / contrast | 验收 |
|---|---|---|---|---|---|
| `kernel_w_size == 2` | `['kernel_w_size in {0, 1, 2, 3}']` | in_scope | solved | {'kernel_w_size': 2} / {'kernel_w_size': 3} | 通过 |
| `kernel_w_size == 0` | `['kernel_w_size in {0, 1, 2, 3}']` | out_of_scope | infeasible | — / — | 通过 |
| `kernel_w_size == 2` | `[]` | in_scope | solved | {'kernel_w_size': 2} / {'kernel_w_size': 1.999} | **已知失败，未计通过** |

**需要交给下游修正的问题：** Shared schema interval bounds serialize to floats. Main witness infers real for this integer parameter and returns fractional contrast (e.g.1.999). Declared code_type must be preserved; do not execute this contrast.

这里 `kw > 0` 可以写成下界 1，是因为它是整数。正向探针的 `{0,1,2,3}` 只约束本次接口测试；零仍由论文下界排除。没有这一额外整数域时，原始求解器返回 1.999，对真实构造参数无效。`kh → kernel_h_size` 的第二条映射也已交付。

## 现在可以交什么，还不能声称什么

两包的 schema、来源、真实参数映射与消费者读取已验证；8 个消费者探针中 6 个通过，2 个保留为明确失败。回归测试通过不意味着这两个失败案例也通过。

未决的是下游 witness 的十进制等值编码和整数类型保留，不是要重做论文机制分析。本分支未修改 `codeside/` 或共享 schema。映射已进入共享 Binding；旁表同时记录了主接口表达不了的类型与函数上下文，便于三人确认后续契约。

验证命令（从 paperside 运行）：

```bash
python scripts/validate_delivery.py --root handoffs/paper-side-v2
# 严格消费者验收：当前预期退出码4，明确表示两个已知问题仍未通过。
python scripts/validate_delivery.py --root handoffs/paper-side-v2 --strict-consumer
python -m unittest discover -s tests -v
```
