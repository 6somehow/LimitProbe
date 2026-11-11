# 环境记录（P0）

日期：2026-11-11。解释器：`<python>`（3.14.10）。不使用 venv 或 uv。

## 已安装的包（`findlimit`）

| 包 | 版本 | 原因 |
|---|---|---|
| pydantic | 2.14.3 | `models.py`（pydantic v2）；`schema.models` 也依赖它 |
| pytest | 9.2.0 | 测试 |
| coverage | 7.17.2 | P1b 的覆盖率测量（本次 tracer 不依赖它） |
| torch | 2.15.0+cpu | FlexPrefill import 和张量构造。来源 `--index-url https://download.pytorch.org/whl/cpu`。FlexPrefill 的 extra_requirements 固定为 2.4.0，3.14 没有该版本的 wheel，用 CPU 可用的最新版 |
| einops | 0.8.2 | `flex_prefill_attention.py` 第 22 行 import |
| transformers | 5.22.2 | `flex_prefill/__init__.py` 经 `modules/patch.py` 导入 `PreTrainedModel`；`flex_prefill_attention.py` 第 1782 行用 `is_flash_attn_2_available`。仓库固定 4.44.0，在 3.14 上装不了，用最新版 |
| triton | 3.9.0 | `flex_prefill_attention.py` 第 20 行 `import triton`。仓库固定 3.0.0。3.9.0 有 cp314 的 wheel，import 成功，不需要替身 |

由上述包带进来的依赖（numpy 2.5.4、huggingface-hub 2.4.0、tokenizers 0.23.3、safetensors、tqdm、pyyaml、regex、typer 等）不单独列出，完整列表用 `pip list` 取得。

未安装：`flash_attn`（需要 CUDA）。因此 `flash_attn_func = triton_flash_attention`（第 1782–1786 行）。

## U4：FlexPrefill 能否在 `findlimit` 里 import

结论：**能**。`import flex_prefill.ops.flex_prefill_attention` 成功，`GPU_NAME` 为 `None`。没有改仓库，`third_party/FlexPrefill` 的 `git status` 为空。

失败点依次是（每装一个包解决一个）：

1. `import torch`（flex_prefill_attention.py:19）：未装 → 装 torch CPU。
2. `from transformers import PreTrainedModel`（modules/patch.py:23）：导入 `flex_prefill.ops.*` 会先执行 `flex_prefill/__init__.py`，它导入 `modules.patch`。未装 → 装 transformers。
3. `import triton`（flex_prefill_attention.py:20）：未装 → 装 triton 3.9.0。

版本与仓库固定版本（torch 2.4.0、transformers 4.44.0、triton 3.0.0）不同。这是偏差，会影响 F05、F06、F03、F02（涉及 kernel 与 transformers 内部行为）；对 F07、F01 无影响，因为两个 assert 在任何 kernel 或 transformers 调用之前。

## U5：F07、F01 能否到达第 1824、1836 行

脚本：`scripts/u5_probe.py`。用 bfloat16 随机张量（种子 0），2 个头，head_dim=128，block_size=128，`gamma=0.9`，`tau=0.1`。

| 用例 | 结果 |
|---|---|
| F07 正例 `batch_size=2` | `AssertionError: only support batch size 1 for now`，位置 `flex_prefill_attention.py:1824` |
| F07 反例 `batch_size=1` | 不在 1824 抛异常；继续往下，在 triton 的 `runtime/driver.py:20` 抛 `RuntimeError: 0 active drivers`（没有 GPU） |
| F01 正例 `q_len=4096, k_len=8192` | `AssertionError`（无消息），位置 `flex_prefill_attention.py:1836` |
| F01 反例 `q_len=4096, k_len=4096` | 不在 1836 抛异常；同样在 triton `driver.py:20` 抛 `RuntimeError` |

加 `--stub-downstream`（把 `flash_attn_func`、`get_active_blocks`、`triton_block_wise_attention` 在导入后的模块对象上替换掉）后，两个反例正常返回。

需要替换的符号：**F07、F01 不需要替换任何符号**。

- `triton`：真 wheel 能 import，不需要 stub。我试过用 stub 模块替换 `triton`，`transformers` 自己会探测 triton 版本并 import 失败，所以不采用。
- `GPU_NAME`：值为 `None`。只在 `get_num_warps_stages`（由第 266、553、628、1276 行调用，都在 kernel 包装函数里）里用 `.lower()`，在两个 assert 之后。**不在路径上**。
- `flash_attn_func` / `get_active_blocks` / `triton_block_wise_attention`：在两个 assert 之后。**不在路径上**。只有"反例要正常返回"时才需要替换。

反例的处理见最终报告中"矛盾与模糊处"：反例在目标行之后因没有 GPU 而崩溃。

## 中继

出站只绑定 eth0 的源地址时连接超时（默认路由走 eth1，源地址为 eth0 的包被丢弃）。需要 `SO_BINDTODEVICE`（这台机器上不需要 root）。已在 `relay.py` 里实现，实测：只绑地址超时 10 秒，绑设备 0.04 秒连上。
