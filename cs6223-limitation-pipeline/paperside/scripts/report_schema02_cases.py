"""Render two complete review cases from the delivered JSON, without APIs."""
import json
from pathlib import Path
from paperprobe.io import read_json

ROOT = Path(__file__).resolve().parents[1]


def block(value, language='json'):
    return f'```{language}\n' + (json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str) else value) + '\n```\n'


def main():
    text = '''# 两个完整案例：论文参数怎样交给下游

这轮没有重新调用模型找参数。它使用既有论文分析，增加**经过原文与固定源码核对的映射样例**，用于检查最新 main（基线 `9fce6e0`）的接口。旧五篇判断没有改写；目标系统没有运行。

## 输入输出先看这一张表

| 环节 | 输入 | 输出 |
|---|---|---|
| 本次适配 | v1 交接包、固定 PDF、固定 commit 仓库、已审阅映射规格 | v2 的 `paper_side.json`，仍是 claims / scope / eval_points / bindings 四数组 |
| 追溯映射 | 某个 binding ID | `parameter_mappings.json`：原文、单位、代码类型、所属函数、声明与后续使用 |
| 消费者联调 | 明确写出的探针条件与有限输入域 | `consumer_cases.json`：实际 scope/witness 返回、是否通过、已知失败原因 |

**探针条件不是从目标代码抽出的新 limitation。** 为检查接口而设置的有限输入集合，也不是论文支持范围或真实调用链。整数性与函数所属上下文目前放在旁表，因为团队四数组接口没有相应专门字段；下游不能忽略它们直接执行 witness。

'''
    for aid, title, binding in [('flexprefill', 'FlexPrefill：τ → tau', 'flexprefill-binding-001'),
                                ('nnsmith', 'NNSmith：Pool2d 的 kw → kernel_w_size', 'nnsmith-parameter-pool2d-width')]:
        folder = ROOT/'handoffs/paper-side-v2'/aid
        data = read_json(folder/'paper_side.json')
        mapping = next(m for m in read_json(folder/'parameter_mappings.json')['mappings'] if m['binding_id'] == binding)
        b = next(b for b in data['bindings'] if b['binding_id'] == binding)
        scope = next(s for s in data['scope'] if s['param'] == b['paper_term'])
        text += f'## {title}\n\n'
        text += f'完整文件：[交接目录](../handoffs/paper-side-v2/{aid}/)。仓库版本：`{mapping["commit"]}`。\n\n'
        text += '### 1. 作者在论文中说了什么\n\n'
        for evidence in mapping['paper_evidence']:
            text += evidence['locator'] + '\n\n' + block(evidence['quote'], 'text') + '\n'
        text += '### 2. 对应哪段实际源码\n\n'
        for location in [mapping['declaration']] + mapping['code_steps']:
            text += f'`{location["file"]}:{location["line_start"]}–{location["line_end"]}` · `{location["function"]}`\n\n'
            text += block(location['snippet'], 'python') + '\n'
        text += '**映射含义：** ' + mapping['role'] + '\n\n'
        text += '**适用边界：** ' + mapping['scope_qualifier'] + '\n\n'
        text += '### 3. 实际输出给 Wanting 的记录\n\n'
        text += '以下是四数组接口中的两条完整记录；其他原有记录仍保留在完整文件中。\n\n'
        text += block(dict(scope=scope, binding=b)) + '\n'
        text += '### 4. 下游实际返回了什么\n\n'
        cases = [c for c in read_json(folder/'consumer_cases.json')['cases'] if c['binding_id'] == binding]
        text += '| 探针条件 | 附加测试输入域 | scope | witness 状态 | trigger / contrast | 验收 |\n|---|---|---|---|---|---|\n'
        for c in cases:
            w = c['witness']; pair = f'{w.get("trigger", "—")} / {w.get("contrast", "—")}'
            text += f'| `{c["input"]["expr"]}` | `{c["input"]["path_prefix"]}` | {c["scope_result"]["scope_status"]} | {w["status"]} | {pair} | '+('通过' if c['passed'] else '**已知失败，未计通过**')+' |\n'
        text += '\n'
        for c in cases:
            if not c['passed']:
                text += '**需要交给下游修正的问题：** ' + c['known_upstream_failure'] + '\n\n'
        if aid == 'nnsmith':
            text += '这里 `kw > 0` 可以写成下界 1，是因为它是整数。正向探针的 `{0,1,2,3}` 只约束本次接口测试；零仍由论文下界排除。没有这一额外整数域时，原始求解器返回 1.999，对真实构造参数无效。`kh → kernel_h_size` 的第二条映射也已交付。\n\n'
        else:
            text += '映射 tau 不等于证明全部阈值公式实现正确。γ 的开区间仍保持原处理，未通过伪造闭区间强行激活；本次不新增 gamma 求解器约束。\n\n'
    text += '''## 现在可以交什么，还不能声称什么

两包的 schema、来源、真实参数映射与消费者读取已验证；8 个消费者探针中 6 个通过，2 个保留为明确失败。回归测试通过不意味着这两个失败案例也通过。

未决的是下游 witness 的十进制等值编码和整数类型保留，不是要重做论文机制分析。本分支未修改 `codeside/` 或共享 schema。映射已进入共享 Binding；旁表同时记录了主接口表达不了的类型与函数上下文，便于三人确认后续契约。

验证命令（从 paperside 运行）：

```bash
python scripts/validate_delivery.py --root handoffs/paper-side-v2
# 严格消费者验收：当前预期退出码4，明确表示两个已知问题仍未通过。
python scripts/validate_delivery.py --root handoffs/paper-side-v2 --strict-consumer
python -m unittest discover -s tests -v
```
'''
    out = ROOT/'docs/parameter-mapping-cases.md'
    out.write_text(text)
    print(out)


if __name__ == '__main__':
    main()
