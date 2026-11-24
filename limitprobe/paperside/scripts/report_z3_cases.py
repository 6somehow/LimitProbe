"""Render the two reviewed Z3 input/output cases from actual saved records."""
from pathlib import Path
import json
from paperprobe.io import read_json

ROOT=Path(__file__).resolve().parents[1]


def code(value,lang='json'):
    return f'```{lang}\n'+(json.dumps(value,ensure_ascii=False,indent=2) if not isinstance(value,str) else value)+'\n```\n\n'


def main():
    text='''# Z3：两篇论文怎样交给 Shanghao 测试

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

'''
    for aid,title in [('flexprefill','案例一：累计分数恰好等于 γ'),('nnsmith','案例二：预算耗尽后返回 None，而非论文的失败异常')]:
        folder=ROOT/'handoffs/z3-v1'/aid
        plan=next(h for h in read_json(folder/'testability_hints.json')['hints'] if h.get('finding_id'))
        native=read_json(folder/'limitations_for_tests.json')
        report=read_json(folder/'contract_output/tests'/aid/plan['finding_id']/'report.json')
        text+=f'## {title}\n\n'
        text+=f'论文：{aid}；原行为 `{plan["behavior"]}`；原claim `{plan["claim_id"]}`。关联真实step4 Finding：`{plan["source_step4_finding_ids"]}`。这是衍生Z3样例，不是新发现。\n\n'
        text+=f'[完整交接目录](../handoffs/z3-v1/{aid}/) · [全部提示](../handoffs/z3-v1/{aid}/testability_hints.json)\n\n'
        text+='### 论文要求\n\n'
        for e in plan['paper_evidence']:
            text+=e['locator']+'\n\n'+code(e['quote'],'text')
        text+='### 真实代码位置\n\n'
        loc=plan['target']
        text+=f'`{loc["file"]}:{loc["line_start"]}–{loc["line_end"]}`，所属函数 `{loc["function"]}`。\n\n'+code(loc['snippet'],'python')
        selected=plan['related_locations'][1] if aid=='flexprefill' else plan['related_locations'][0]
        text+=f'上下文 `{selected["file"]}:{selected["line_start"]}–{selected["line_end"]}`：\n\n'+code(selected['snippet'],'python')
        text+='### 调用链与参数怎样传过去\n\n'
        for e in plan['call_chain']:
            text+=f'`{e["caller"]}` → `{e["callee"]}`\n\n'
            text+=code(e['call'],'python')+code(e['formal_parameter_map'])
            if e.get('path_condition'):text+='前提：`'+e['path_condition']+'`。\n\n'
        text+='### 触发条件和拟议输入\n\n'+plan['condition_text']+'\n\n'
        text+=code(dict(trigger_recipe=plan['trigger'],control_recipe=plan['contrast']))
        if aid=='flexprefill':
            text+='这些是helper帧的具体输入，不是假装已经构造出的Q/K。使用二进制可精确表示的分数，避免十进制误差混入。独立有理数参考计算如下；它不执行目标函数：\n\n'+code(plan['arithmetic'])
        else:
            text+='`timeout_ms=0` 从search_one进入，除以1000后是 `max_time=0`。初始化成功后while不进入，sat_inputs仍为None，走到return。不能改用外层 `search(max_time_ms=0)`，因为那样外层就跳过循环，根本到不了目标。模型构造和正向对照仍需要Shanghao实际实现、运行确认。\n\n'
        text+='### 怎么判，什么不能判\n\n'+code(plan['proposed_oracle'])
        text+='尚未解决的边界：\n\n'+''.join('- '+b+'\n' for b in plan['blockers'])+'\n'
        if aid=='nnsmith':
            e=plan['experiment_route_check']
            text+='实验路径另有静态阻塞：\n\n'+code(dict(call=e['call']['call'],unsupported_keywords=e['unsupported_keywords'],analysis=e['analysis']))
        text+='### 实际给 Shanghao 的输入\n\n'
        text+='下列完整外层结构能被他的loader读取。`witness.status=unknown` 是因为没有经过正式入口求解/执行确认；局部配方另存旁表，不谎报solved。\n\n'+code(native)
        text+='### 消费者实际输出\n\n'
        text+='调用实际分类器和 `not_run_record`，未调用test/envcheck/run_agent。这里没有生成置信分数，测试verdict和level为null。原Finding的L2是研究分类，不是测试置信档位。\n\n'+code(report)
    text+='''## 剩余项怎么处理

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
'''
    out=ROOT/'docs/z3-two-paper-cases.md';out.write_text(text);print(out)


if __name__=='__main__':main()
