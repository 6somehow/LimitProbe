# 论文候选采集与10→5选择

采集日期：2026-10-01，Asia/Shanghai。已下载10篇公开完整PDF，浅克隆5个作者/机构官方代码仓库，并固定论文SHA256及代码commit。本说明是开发资料与机制选择记录，不是final paper，也不是bug发现结果。

机器可读入口：[papers.json](../data/catalog/papers.json)。每条记录保留正式题目、venue、年份、primary来源、PDF版本说明、是否选入、选择原因、相对路径、SHA256、repo commit及采集状态。PDF页数包含publisher封面和附录；引用页码必须以本地实际PDF为准。

## 10篇候选

| ID | 论文/官方元数据 | Venue / 年份 | PDF页数 | 本轮状态 | 本地论文 |
|---|---|---|---:|---|---|
| `minference` | [MInference 1.0: Accelerating Pre-filling for Long-Context LLMs via Dynamic Sparse Attention](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5dfbe6f5671e82c76841ba687a8a9ecb-Abstract-Conference.html) | NeurIPS 2024 / 2024 | 35 | 选入 | [minference.pdf](../data/papers/minference/paper.pdf) |
| `sparta` | [SparTA: Deep-Learning Model Sparsity via Tensor-with-Sparsity-Attribute](https://www.usenix.org/conference/osdi22/presentation/zheng-ningxin) | OSDI 2022 / 2022 | 21 | 选入 | [sparta.pdf](../data/papers/sparta/paper.pdf) |
| `infinigen` | [InfiniGen: Efficient Generative Inference of Large Language Models with Dynamic KV Cache Management](https://www.usenix.org/conference/osdi24/presentation/lee) | OSDI 2024 / 2024 | 19 | 选入 | [infinigen.pdf](../data/papers/infinigen/paper.pdf) |
| `alex` | [ALEX: An Updatable Adaptive Learned Index](https://www.microsoft.com/en-us/research/publication/alex-an-updatable-adaptive-learned-index/) | SIGMOD 2020 / 2020 | 21 | 选入 | [alex.pdf](../data/papers/alex/paper.pdf) |
| `flashattention2` | [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://proceedings.iclr.cc/paper_files/paper/2024/hash/98ed250b203d1ac6b24bbcf263e3d4a7-Abstract-Conference.html) | ICLR 2024 / 2024 | 14 | 选入 | [flashattention2.pdf](../data/papers/flashattention2/paper.pdf) |
| `hnswlib` | [Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs](https://arxiv.org/abs/1603.09320v4) | IEEE TPAMI (official repository citation year 2018) / 2018 | 13 | 备选 | [hnswlib.pdf](../data/papers/hnswlib/paper.pdf) |
| `flexgen` | [FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU](https://proceedings.mlr.press/v202/sheng23a.html) | ICML 2023 / 2023 | 23 | 备选 | [flexgen.pdf](../data/papers/flexgen/paper.pdf) |
| `streamingllm` | [Efficient Streaming Language Models with Attention Sinks](https://proceedings.iclr.cc/paper_files/paper/2024/hash/5e5fd18f863cbe6d8ae392a93fd271c9-Abstract-Conference.html) | ICLR 2024 / 2024 | 21 | 备选 | [streamingllm.pdf](../data/papers/streamingllm/paper.pdf) |
| `snapkv` | [SnapKV: LLM Knows What You are Looking for Before Generation](https://proceedings.neurips.cc/paper_files/paper/2024/hash/28ab418242603e0f7323e54185d19bde-Abstract-Conference.html) | NeurIPS 2024 / 2024 | 24 | 备选 | [snapkv.pdf](../data/papers/snapkv/paper.pdf) |
| `quest` | [QUEST: Query-Aware Sparsity for Efficient Long-Context LLM Inference](https://proceedings.mlr.press/v235/tang24l.html) | ICML 2024 / 2024 | 11 | 备选 | [quest.pdf](../data/papers/quest/paper.pdf) |

HNSW年份2018采用作者官方[hnswlib引用](https://github.com/nmslib/hnswlib)口径；下载的是[arXiv v4](https://arxiv.org/abs/1603.09320v4)，其首稿2016、v4修订2018。它不是2024新论文。FlashAttention-2和StreamingLLM的会议年份是2024，公开预印本首发2023。此次候选选择针对清晰paper–code机制和现有proposal，未声称来自最近半年或代表所有研究软件。

## 为什么选这5篇

1. **MInference、SparTA、InfiniGen**保留原proposal的三个案例，使原先的paper–code分析能转为可执行系统任务；不把proposal里探索性limitation当既成bug。
2. **ALEX**提供CPU可运行的C++索引目标，可测试插入、查找与删除的序列，便于首个真实闭环。官方实现限定单线程数值key；正确性比较须对齐map/multimap契约。
3. **FlashAttention-2**补充exact attention方法，便于建立数值reference，区分MInference等近似算法的整体模型效果与kernel计算正确性。固定2.x代码，避免使用FA3/4来解释FA2论文。

其余5篇暂不clone。HNSWlib和ALEX在CPU索引位置上重叠；FlexGen的offloading和InfiniGen重叠且完整模型实验较重；StreamingLLM、SnapKV、Quest的KV/attention任务与已选目标重叠。它们保留作替代候选，未按已知bug或issue命中难易选择。SnapKV官方[代码说明](https://github.com/FasterDecoding/SnapKV)还声明测试于transformers 4.37.0且依赖flash-attn 2.4.0，不能默认兼容现在的模型库。

这5篇现阶段的“选入”含义是进入论文处理、代码索引、机制提取和静态规格生成；本采集任务没有安装目标依赖、执行CUDA kernel、加载模型或复现论文性能。目标runner的实际可执行结果须单独报告。

## 选入机制与源码入口

以下是阅读本地论文和冻结源码得到的**候选对齐入口**。系统应继续验证符号、调用路径、前置条件及语义关系，不能仅凭同名词汇宣布对齐成功。

| ID | 论文证据位置（一基PDF页） | 当前源码入口 | 初始测试机会与判定限制 |
|---|---|---|---|
| `minference` | pp.4–6：A-shape、Vertical-Slash、Block-Sparse；p.5 Algorithms 2/3，last-query与block approximation | `minference/modules/minference_forward.py`；`minference/ops/block_sparse_flash_attention.py` | 可检查last-query、top-k clamp、64 block和padding的约束，最终kernel以同一显式sparse mask的reference判断；不能要求近似attention等于full dense。 |
| `sparta` | pp.5–6：Algorithm 1/2 TeSA propagation；Table 2 attribute algebra；§3.3 code generation | `sparta/tesa/tesa_base.py`；`sparta/tesa/block_compressed.py`的`BCSFunctionContext`；`sparta/testing/mask.py` | 当前snapshot可定位block属性、mask和BCS转换；可检查shape、支持block集合、dtype和masked round-trip。不认定论文完整propagation pass已在当前官方repo中；相关对齐应保留unknown或missing。 |
| `infinigen` | p.8 Eq.2：共同orthogonal transform保持QKᵀ；p.9 Eq.3与partial-weight/cache selection | `speedup/infinigen/infinigen/skewing_controller.py`；`partial_weight_generation_controller.py`；`kv_selection_controller.py` | 可检查per-head reshape、partial ratio取整及selection bounds；小张量可验证orthogonal invariance。GQA映射或采样精度是独立待检问题，维度不兼容不能未经支持范围检查即报bug。 |
| `alex` | pp.5–6 §4.3：density默认0.6/0.8、扩张/分裂；§4.4删除/收缩 | `src/core/alex_nodes.h`的`kMinDensity_`/`kMaxDensity_`、`resize`；`src/core/alex.h` | 生成合法整数key操作序列，跨过真实容量/density触发；与匹配重复key和删除语义的reference比较。触发split是reachability，状态/返回值违反才可能是语义问题。 |
| `flashattention2` | p.5 Algorithm 1与causal masking；p.7 block sizes/work partitioning | `flash_attn/flash_attn_interface.py`的`_get_block_size_n`、`flash_attn_func`；`csrc/flash_attn/` | 从等长Q/K、dropout=0和支持dtype开始，检查head dimension、block边界与causal mask；数值容差预先固定。不同Q/K长度的API mask对齐来自所选代码版本，不直接作为原论文等长公式的主张。 |

SparTA和InfiniGen的USENIX PDF各有一页封面，因此其“PDF page”与正文印刷页码不同；例如SparTA PDF p.5的正文印刷页为216，InfiniGen PDF p.8为161。ALEX下载的是扩展report；不要把其页码套用到ACM会议版。

## 版本固定与变化风险

| ID | 固定commit | Commit时间（源码原时区） | 选择ref |
|---|---|---|---|
| `minference` | `29ef1974fcb5a1440ccf92d7d7996900230fddcf` | 2026-09-10T21:46:22+08:00 | 作者官方默认branch的冻结快照 |
| `sparta` | `183513c5b721fa8b970e19fd95887bad9a16c1fe` | 2023-01-30T15:47:05+08:00 | 作者官方默认branch的冻结快照 |
| `infinigen` | `3754f52d131c30ab7a310e3c4cf356e8e3326ac3` | 2024-07-09T23:18:17-07:00 | 作者官方默认branch的冻结快照 |
| `alex` | `4370da6aa8b509fdc9b0d2c49faa0624b0078589` | 2024-03-12T10:51:30-04:00 | 作者官方默认branch的冻结快照 |
| `flashattention2` | `87a1277653fc55cd615f5341255e00c69d5c00a1` | 2024-02-21T15:58:23-08:00 | v2.5.5 |

- **MInference**当前官方仓库还收纳后续KV compression、多模态、其他sparse attention等方法。只有与2024 MInference 1.0论文有双向证据的子模块才可归入该论文任务；后续模块标为版本扩展或unknown。
- **SparTA**官方独立repo处于继续开发状态。原OSDI artifact还曾通过[microsoft/nni的sparta_artifact分支](https://github.com/microsoft/nni/tree/sparta_artifact/sparta)发布；本轮只clone独立SparTA仓库。缺失原propagation符号应如实保存，不自动补造成作者实现。
- **InfiniGen**使用作者[snu-comparch/InfiniGen](https://github.com/snu-comparch/InfiniGen)，不是MachineLearningSystem镜像fork。当前repo同时有accuracy和speedup实现；task需记录选用路径，不能混合两个入口的前置条件。
- **ALEX**下载微软Publication页面所指向的作者[arXiv v2](https://arxiv.org/abs/1905.08898v2)扩展报告。最初微软官网PDF直链返回HTTP 403，已在catalog的`acquisition_history`保存；未替换论文身份。官方默认branch不是论文提交时的已证明commit。
- **FlashAttention-2**使用tag `v2.5.5`，commit与tag指向已核验。它是2.x开发版本而非已证明的paper experiment commit；新增API行为需标代码来源。

固定commit与文件hash提供可重放版本，不证明paper与代码完全一致。后续不得静默pull更新；需要更新时创建新任务版本并重新记录paper/code对应关系。当前shallow checkout不包含完整history，也不含递归初始化的submodules；完整构建若需要它们，应另外固定依赖版本。

## 开发集与评估解释

本轮选入的5个仓库已经由开发者和agent阅读，用于实现与调试，属于**development/pilot corpus**。它们不是held-out测试集，不能把同一repository的多个函数、多个输入、同源mutants当作独立泛化样本。约5个系统和10篇候选也不证明跨领域通用性；其中4个是ML系统。

如果之后评估泛化，应按repository family保留独立未参与开发的目标，记录首次访问时间，隔离issue说明、人工错误标签和known witness。当前采集没有查询issue页面或bug标签；官方README及源码仅用于来源、支持范围和机制定位。人工review、依赖失败和无法对齐的候选应保留计数，避免只报告成功样例。

## 采集与复验

采集脚本：[acquire_papers.py](../scripts/acquire_papers.py)。使用已装`pypdf`的项目Python执行：

```bash
python scripts/acquire_papers.py
python scripts/acquire_papers.py --verify-only
```

首次采集从catalog下载公开PDF并浅克隆selected repo；之后使用已记录SHA256和commit复验。缺少checkout时按固定commit重建，已存在checkout有变化时报告错误，不重置本地修改。`--verify-only`不写catalog、不更新branch、不下载缺失文件。

本轮验证结果：10/10 PDF均具有`%PDF-`头、可解析全部page objects并统计非零页数；10篇标题页视觉核对无错配；5/5 repo均为shallow、HEAD等于catalog commit、工作树干净；10条`acquisition_status`均为`complete`。9个PDF首轮直接成功；ALEX按公开作者源fallback后成功，无未解决下载或clone失败。论文与代码约束阅读不等于目标程序执行验证。
