# Pilot：FlexPrefill

- 论文：FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference，ICLR 2025 Oral（[arXiv 2502.20766](https://arxiv.org/abs/2502.20766)）
- 仓库：[bytedance/FlexPrefill](https://github.com/bytedance/FlexPrefill) @ `a24b27bf117fd6ad4ba34b0db82c598e7786fd59`
- 入口：`flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention`（第 1791 行）

## 为什么选它

- 官方仓库，论文与代码同一作者；核心逻辑集中在一个文件，入口清晰。
- 同时含有几乎所有信号类型：assert、配置依赖的 fallback 边界、模块级缓存、环境分支、硬编码常数。
- 决策逻辑在 Python 层，Triton kernel 可以 mock，Shanghao 能在 CPU 上确认大部分区域。
- 和 Shanghao 的方向（稀疏 attention）一致，方便领域把关。

## 论文侧要点（临时 stub，见 `data/pilot_flexprefill/paper_side_stub.json`，由 Zhaopeng 替换）

- 机制：query-aware / vertical-slash 逐 head 选择（τ 判定），按累计注意力阈值 γ 选块。
- 评测配置：block_size = 128；每个 head 至少 1024 tokens；τ = 0.1；γ = 0.9 / 0.95；单张 A100 80GB；RULER 4k–128k；四个模型（Llama-3.1-8B、GLM-4-9B、Yi-9B-200K、Qwen2-7B），head_dim 均为 128。
- 论文**没有提到**：batch size、dtype、短序列走 dense、decode、多轮 / KV cache 复用 / chunked prefill、GQA 处理细节。没有单独的 Limitations 一节。
- README 写了："only supports inference with a batch size of 1 and has only been tested with bfloat16 precision"；vLLM 示例里设置了 `enable_chunked_prefill=False`，但没有解释原因。

## Gold 区域表（`gold_regions.json`，人工标注，16 条）

| ID | 条件 | 结局 | 位置 |
|---|---|---|---|
| R01 | batch_size != 1 | reject | 1824 |
| R02 | q_len == 1（decode） | fallback（dense，设计如此） | 1825 |
| R03 | q_len != k_len（在已有 KV cache 上 prefill） | reject | 1836 |
| R04 | head_dim ∉ {16,32,64,128} | reject | 1837 |
| R05 | block_size ∉ {16,32,64,128} | reject | 1838 |
| R06 | q_len ≤ max(2·block_size, ⌈min_budget/block_size⌉·block_size) | fallback（dense） | 1842 |
| R07 | 其余 | mechanism | 1856 |
| R08 | dtype ≠ bfloat16（稀疏路径） | reject | 1218 |
| R09 | head_dim ≤ 128 且 block_size ∉ {32,64,128} | reject（与 R05 矛盾） | 1222 |
| R10 | num_q_heads % num_kv_heads ≠ 0 | reject | 1258 |
| R11 | triton 主版本 < 3 | env_dependent | 1267 |
| R12 | block_size ≠ 128（`// 128` 硬编码） | suspicious | 1708 |
| R13 | 模块级 causal_mask 缓存跨调用复用 | state_dependent | 1694 |
| R14 | JS 散度 < τ | mechanism_variant | 1727 |
| R15 | GPU 不是 H100 / A100 / 4090 | env_dependent | 86 |
| R16 | 未安装 flash_attn | env_dependent | 1784 |

R06 的边界依赖配置：论文配置（128, 1024）下 q_len ≤ 1024；README 示例（min_budget=512）下 ≤ 512；默认（None）下 ≤ 256。

## 初步 finding（`draft_findings.json`，草稿，待团队评审和执行确认）

| ID | 类别 | 内容 | 优先级 | 置信度 |
|---|---|---|---|---|
| F01 | undocumented | 在已有 KV cache 上 prefill（多轮、prefix 复用、chunked prefill）被 assert 拒绝 | 1 | mechanical |
| F02 | undocumented | 块预算按硬编码 128 换算；block_size 为 32/64 时 γ 覆盖可能不成立 | 1 | llm_assisted（候选） |
| F03 | undocumented | 模块级 causal_mask 缓存可能在跨设备或换 block_size 时出错 | 1 | llm_assisted（候选） |
| F04 | undocumented | head_dim 不在 {16,32,64,128} 的模型被拒绝 | 2 | mechanical |
| F05 | documented_elsewhere | 稀疏路径要求 bf16，README 只说"测过" | 2 | mechanical |
| F06 | undocumented（out of scope） | block_size=16 通过入口检查和 docstring，却在 kernel 中失败 | 3 | mechanical |
| F07 | documented_elsewhere | batch size 必须为 1（仅 README） | 3 | mechanical |

被过滤的：decode 走 dense（论文只讲 prefill）、短序列走 dense（边界低于评测的 4K，且与"至少 1024 tokens"一致）、GQA 不整除、triton 版本、flash_attn 可选。

**F02、F03 是人工读代码发现的候选，必须由 Shanghao 执行确认后才能计入结果。**

## 抽取器 v0 在 pilot 上的结果

```
gold regions: 16   predicted: 30
recall: 16/16 = 1.00
unmatched predictions: 10
  6 条：decode kernel 的 assert（prefill 前缀下不可达）      -> 需要路径可行性剪枝
  2 条：triton_bnhd_pool 的 assert（已被入口 assert 覆盖）    -> 需要冗余判断
  2 条：block_idx 的 isinstance / len 断言（内部不变量）       -> 需要内部不变量过滤
```

**注意：v0 的规则是对着这个 pilot 写的，recall 1.00 不代表泛化能力。** 第二个 artifact 才是真正的检验（TASKS.md M3）。

## CPU 执行时要提醒 Shanghao 的点

- `GPU_NAME` 在没有 CUDA 时是 None，`get_num_warps_stages` 里的 `.lower()` 会报错，需要 mock。
- 模块导入时就 `import triton`，CPU 环境需要安装 triton 或 stub 掉。
- 未安装 flash_attn 时，dense fallback 会改走 `triton_flash_attention`，它同样要求 bf16 和指定的 head_dim。
