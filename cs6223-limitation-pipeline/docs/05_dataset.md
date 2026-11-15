# 开发数据集：四篇论文

开发和调试使用 proposal 里的三篇论文，加上 NNSmith。FlexPrefill 保留为已完成的示范 pilot（`data/pilot_flexprefill/`），
不计入数据集。各 artifact 的元数据在 `data/<id>/artifact.json`，用 `scripts/fetch_dataset.sh` 按固定 commit 克隆。

| ID | 论文 | 会议 | 固定版本 | 领域 | proposal 中的层次 | 执行环境 |
|---|---|---|---|---|---|---|
| sparta | [SparTA](https://www.usenix.org/conference/osdi22/presentation/zheng-ningxin) | OSDI 2022 | 分支 `sparta_artifact` @ 1f61a36（2022-04-30） | 稀疏编译 | L1 评测可见 | 需 GPU；CPU 上只能 mock |
| minference | [MInference 1.0](https://arxiv.org/abs/2407.02490) | NeurIPS 2024 | tag `v0.1.4` @ 427b1dd（2024-07-05） | 稀疏 attention | L2 论文–代码差距 | CPU + mock；索引转换依赖 CUDA 扩展 |
| infinigen | [InfiniGen](https://www.usenix.org/conference/osdi24/presentation/lee) | OSDI 2024 | 3754f52（2024-07-09） | KV cache | L3 隐含假设（MHA vs GQA） | CPU（形状、显存类）+ mock |
| nnsmith | [NNSmith](https://arxiv.org/abs/2207.13066) | ASPLOS 2023 | tag `v0.0.1` @ a8307f2（2022-09-25） | DL 编译器 fuzzing | — | **全 CPU** |

### 为什么这样固定版本

paper–code 对齐要用**论文发表时的代码**，否则会把"论文之后才加的功能或修复"当成差异：

- SparTA 的 main 分支已经演进，OSDI'22 的 artifact 在 `sparta_artifact` 分支；
- MInference 的 HEAD（2026）里加了很多其他方法，`v0.1.4` 是 arXiv 论文（2024-07）之后的第一个 release；
- NNSmith 的 `v0.0.1` 最接近 ASPLOS artifact（[Zenodo 7222132](https://zenodo.org/records/7222132)，2022-10）。

### 关于 NNSmith 这一篇

分享的对话链接无法读取正文，只能从标题（"分析NNsmith搜索缺陷"）判断是 NNSmith。
如果对话里有具体结论（比如发现的搜索缺陷），请整理进 `data/nnsmith/notes.md`，它们可以直接作为 gold 候选。

## 抽取器 v0 在四篇上的首次运行（规则未针对它们调整）

```bash
python -m codeside.cli extract --repo third_party/<repo> --entry "<entry>" --artifact <id> \
  --out out/<id>.json [--package-root <dir> ...]
```

| 入口 | 区域数 | 结局分布 |
|---|---|---|
| sparta `propagate_sparsity` | 1 | mechanism 1 |
| minference `gather_last_q_vertical_slash_topk_v4` | 9 | reject 6、fallback 2、mechanism 1 |
| minference `minference_forward.forward` | 4 | reject 1、state 1、env 1、mechanism 1 |
| infinigen `TorchDevice.mha` | 1 | mechanism 1 |
| infinigen `TorchDevice.mha_gen` | 5 | reject 4、mechanism 1 |
| nnsmith `PracticalHybridSearch.search_one` | 1 | mechanism 1 |
| nnsmith `random_model_gen` | 1 | mechanism 1 |

还没有 gold，所以这里只看覆盖情况，不算 recall。

## 首次运行暴露的问题（需要人工确认的观察 + 抽取器缺口）

**值得跟进的观察（候选，未核实）：**

- **SparTA**：`sparta/propagation/propagate.py::propagate_sparsity` 在 artifact 分支里是桩函数（注释 `# mocked`，直接返回输入的稀疏度）；`talgebra.py` 里只有 matmul 的传播规则。论文的核心机制之一是稀疏度传播。需要确认 artifact 是否通过别的路径（如 `script/` 下的预计算结果）复现论文结果——这是 3a（论文 → 代码）的典型候选，交给 Zhaopeng。
- **NNSmith**：`search_one` 只在模型"可微"时用梯度搜索（`GradSearch`），否则退回随机采样（`SamplingSearch`）；可微性要求所有输入都是浮点类型。代码里有 FIXME："Estimate gradient (e.g., proxy gradient) for non-differentiable inputs"。论文强调梯度引导的搜索，非可微情况是否有说明需要 3b 核对。
- **MInference**：`q_len == 1` 走 dense（decode）；配置项 `dense` / `dilated1` / `dilated2` / `streaming` 会绕过 vertical-slash；Triton kernel 要求 head_dim ∈ {16, 32, 64, 128}；`search_pattern` 有模块级缓存 `SEARCH_MASK`。
- **InfiniGen**：`mha` 中 skew 只在 `warmup` 时执行，partial weight 只在非 warmup 且设置了比例时启用；`mha_gen` 有 4 个 assert。

**抽取器缺口（已加入 TASKS.md M2）：**

1. **不早返回的模式切换没有被识别**：InfiniGen 的 `if warmup: skew(...)` 这类分支改变了执行的机制，但没有 return，v0 不产出区域。
2. **双分支分发**：NNSmith 的 `if self.differentiable: return GradSearch.search_one(...) else: return SamplingSearch.search_one(...)`，以及 MInference 的 `dilated` / `streaming`，都是"切换到另一种实现"，但被调函数名不在 fallback 提示词表里，v0 不报。建议 schema 增加一种 outcome（例如 `alternative`）。
3. **`ClassName.method(self, ...)` 形式的调用**没有解析。
4. **条件依赖 `__init__` 里设置的属性**（如 `self.differentiable`）：需要分析构造函数，把属性的来源条件带进来。
5. **继承**：子类没有重写的方法要到父类里找。

## 开发集与泛化的说明

四篇都用于开发调试，所以在它们上面得到的数字都是**开发集上的数字**，不能直接当作泛化结论。
建议在 M3 之前约定：最后再挑 1–2 篇没见过的 artifact 作为 held-out，只跑一次、不调规则，用来报告泛化结果。
