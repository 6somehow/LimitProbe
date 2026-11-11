# CS6223 limitation pipeline

给定一篇系统研究论文和对应代码仓库，从论文、代码两个方向识别限制与实现差异，整合成 finding，再交给测试侧生成测试并执行确认。

## 分工与阅读入口

| 部分 | 负责人 | 输入与交付 | 说明 |
|---|---|---|---|
| 论文侧：步骤 1、3a | Zhaopeng | 论文机制与行为、适用范围和实验配置 → 固定版本源码证据与静态差异候选 | [论文侧说明](paperside/README.md) · [SparTA 交接包](paperside/handoffs/paper-side-v1/sparta/) |
| 代码侧：步骤 2、3b | Wanting | 代码限制 → 论文/README/注释是否声明、是否在论文范围内 | [代码侧进度与结果](docs/08_progress_step2_3b.md) · [结果快照](results/) |
| 整合：步骤 4 | Wanting | 两侧证据去重、对齐，形成 finding | [共享方法与接口](docs/03_codeside_spec.md) |
| 测试与执行：步骤 5–6 | Shanghao | finding → witness、oracle 与执行结果 | [项目总览与分工](docs/00_project_overview.md) |

论文侧问：**论文承诺的行为，在指定源码路径中是否兑现？** 代码侧问：**代码中的限制，论文或其他文档是否说明？** 两侧可能指向同一处实现，整合时需要去重；行为条数和限制候选数不能直接比较。

## 论文侧：Zhaopeng

### 方法

```text
论文全文：文字 + 原始页面图像
  → 两次独立发现机制（按章节 / 按系统流程）
  → 合并、去重，保留父子机制并冻结清单
  → 按机制拆行为
  → 独立列出相关原页的步骤，与初次行为对账、拆分或补充
  → 冻结行为；此后才引入代码
  → 每个机制一个 Pi 会话，自主搜索、读源码和查静态调用关系
  → 模型语义复核 + 程序检查 ID、引用范围和结果结构
  → 三类判断、归组候选与共享接口交接
```

代码调查以**机制**为单位，判断以**行为声明**为单位。模型为每个机制分别选择主仓库入口和对应 artifact 路径，记录适用配置、仓库及 commit。工具只读固定 Git 源码，不执行目标系统。模型使用 SoCLaaS `x-test-2` 路由，工具会话使用 Pi SDK。

完成核验的声明只有三类：

| 判断 | 含义 |
|---|---|
| `supports` | 所检查路径支持论文声明及其条件，允许语义等价实现 |
| `deviates` | 有相关实现，但具体步骤、条件、更新或返回行为与声明不符 |
| `absent` | 所检查路径没有实现声明的核心行为 |

未完成核验的条目保留 `review_state=pending, verdict=null`，不计入三类结果或质疑候选。局部路径的缺失不能扩大成整个系统都未实现，静态差异也不等于已确认运行错误。

例如 SparTA 描述用一种或多种块大小覆盖非剪枝元素；主仓库的多块分解路径中存在桩函数和异常分支。交付会保留论文原文、该路径及源码行号，让整合和测试侧继续核对触发条件与影响。

### 已入库结果与交接

当前入库的是 **SparTA**：20 项机制、206 条冻结行为；199 条形成静态判断（支持 96 / 不符 55 / 未实现 48），7 条仍待核验。父子机制存在重叠，这些数字不是独立缺陷数。其余四篇的运行与验收正在本地并行进行，完成后再更新仓库结果。

[SparTA 交接包](paperside/handoffs/paper-side-v1/sparta/)包含：

- [`paper_side.json`](paperside/handoffs/paper-side-v1/sparta/paper_side.json)：Wanting `--paper-side` 的原生输入，204 条 claim、26 条 scope、29 个评估配置、26 条入口导航映射。
- [`conformance.json`](paperside/handoffs/paper-side-v1/sparta/conformance.json)：完整 206 条行为的两种作用域、判断与源码引用；[`finding_candidates.json`](paperside/handoffs/paper-side-v1/sparta/finding_candidates.json)保留原模型归组。
- [`validation.json`](paperside/handoffs/paper-side-v1/sparta/validation.json)与[接入命令](paperside/handoffs/paper-side-v1/sparta/RUN_WITH_WANTING.md)：已通过实际消费者加载和范围检查器的接口检查。

26 条映射都是导航映射，**当前没有可交给数值求解器的标量参数映射**；Wanting 的三个 SparTA 条件仍为 `unknown`。不确定映射和未闭合记录单独保留，不通过宽松约束制造 `in_scope`。三类声明判断留在独立文件中，不机械改成共享 `Verification` 的五类标签。

安装、离线检查、模型复跑及完整文件表统一见 [paperside/README.md](paperside/README.md)。本模块未运行目标系统，模型语义和候选影响仍待团队复核。

## 代码侧快速开始：Wanting

```bash
pip install -e ".[dev]"
scripts/fetch_dataset.sh   # 四篇 + pilot
python -m pytest -q
python -m codeside.cli extract --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --out out/flexprefill_regions.json
python -m codeside.cli evaluate --pred out/flexprefill_regions.json \
  --gold data/pilot_flexprefill/gold_regions.json
```

- [步骤 2 + 3b 进度和结果](docs/08_progress_step2_3b.md)
- [代码侧任务清单](TASKS.md) · [开发上下文](CLAUDE.md)
- [开发数据集](docs/05_dataset.md)：SparTA、MInference、InfiniGen、NNSmith；FlexPrefill 为示范 pilot。
