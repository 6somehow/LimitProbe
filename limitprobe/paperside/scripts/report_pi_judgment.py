"""Display explicit, scoped implementation verdicts and actual Pi evidence."""
import json
from html import escape
from pathlib import Path
from paperprobe.io import read_json

LABELS={'implemented':'有：已实现','partially_implemented':'部分有：仍缺具体步骤','not_implemented':'没有：该路径未实现','not_assessable':'理论性质／本轮不可裁决'}


def render_judgment(run, archives):
    esc=lambda v:escape(str(v))
    pretty=lambda v:esc(json.dumps(v,ensure_ascii=False,indent=2))
    readjl=lambda p:[json.loads(s) for s in p.read_text().splitlines() if s] if p.exists() else []
    report=read_json(run/'report.json');summary=read_json(run/'summary.json');protocol=read_json(run/'protocol.json')
    source=read_json(run/'input.json');user=read_json(run/'initial-user-input.json');system=read_json(run/'system-prompt.json')
    tools=readjl(run/'tools.jsonl');messages=readjl(run/'messages.jsonl')
    review=read_json(run/'acceptance-review.json') if (run/'acceptance-review.json').exists() else {'accepted':False,'reason':'pending'}
    archive=dict(protocol=protocol,summary=summary,system=system,input=user,report=report,review=review,
                 tools=tools,messages=messages,requests=[dict(file=p.name,body=read_json(p)) for p in sorted(run.glob('request-*.json'))])
    archives['pi-explicit-judgment']=archive
    behaviors={b['id']:b for b in source['behaviors']}
    source_reads=[t['result'] for t in tools if t['name']=='read_repo']+[p['result'] for p in source.get('evidence_packet',[])]
    stages=[]
    for p in sorted(run.parent.glob('sparta-pi-judgment-M02-v*/summary.json')):
        stages.append(dict(run=p.parent.name,summary=read_json(p),review=read_json(p.parent/'acceptance-review.json') if (p.parent/'acceptance-review.json').exists() else {}))
    archive['stages']=stages
    history_links=[]
    for stage in stages:
        folder=run.parent/stage['run'];key='judgment-history/'+stage['run']
        archives[key]=dict(summary=stage['summary'],review=stage['review'],
            protocol=read_json(folder/'protocol.json'),system=read_json(folder/'system-prompt.json'),
            input=read_json(folder/'initial-user-input.json'),raw=(folder/'final-response.txt').read_text(),
            tools=readjl(folder/'tools.jsonl'),requests=[dict(file=p.name,body=read_json(p)) for p in sorted(folder.glob('request-*.json'))])
        history_links.append(f'<p>{esc(stage["run"])} <button data-download="{key}">下载该阶段全部实际请求、原始返回与轨迹</button></p>')
    cumulative_tokens=sum(x['summary']['total_tokens'] for x in stages)
    cumulative_requests=sum(len(list((run.parent/x['run']).glob('request-*.json'))) for x in stages)
    cumulative_tools=sum(x['summary']['tool_calls'] for x in stages)
    def cite(e):
        return f"{esc(e['repo'])} · {esc(e['path'])}:{e['start_line']}–{e['end_line']}"
    def excerpts(evidence):
        snippets=[]
        for e in evidence:
            lines={}
            for r in source_reads:
                if r.get('repo')!=e['repo'] or r.get('path')!=e['path']:continue
                for i,line in enumerate(r['lines'].splitlines(),r['start_line']):lines[i]=line
            text='\n'.join(lines.get(i,'[未读取]') for i in range(e['start_line'],e['end_line']+1))
            snippets.append(f'<details><summary>{cite(e)}</summary><pre>{esc(text)}</pre></details>')
        return ''.join(snippets)
    def scope(v):
        return f'''<b>{LABELS[v['verdict']]}</b><p>{esc(v['rationale'])}</p>
        <p><b>代码里有：</b>{esc('；'.join(v['implemented_parts']) or '未确认对应实现')}</p>
        <p><b>代码里缺：</b>{esc('；'.join(v['missing_parts']) or '本判定未提出缺失项')}</p>
        <small>范围：{esc(v['entry_scope'])}</small><p>反证／替代实现：{esc(v['counterevidence'])}</p>{excerpts(v['evidence'])}'''
    rows=''.join(f'''<tr id="judgment-{c['id']}"><td><b>{esc(c['id'])}</b><p>{esc(behaviors[c['id']]['behavior'])}</p></td>
        <td>{scope(c['local_entry'])}</td><td>{scope(c['artifact'])}</td></tr>''' for c in report['checks'])
    categories=''
    for verdict,label in LABELS.items():
        ids=[c['id'] for c in report['checks'] if c['artifact']['verdict']==verdict]
        categories+=f'<p><b>{label}（{len(ids)}）</b>：'+('、'.join(f'<a href="#judgment-{i}">{i}</a>' for i in ids) or '无')+'</p>'
    failure=''
    first=run.parent/'sparta-pi-judgment-M02-v1'
    if first!=run and (first/'acceptance-review.json').exists():
        earlier=dict(summary=read_json(first/'summary.json'),review=read_json(first/'acceptance-review.json'),raw=(first/'final-response.txt').read_text(),tools=readjl(first/'tools.jsonl'))
        archives['pi-explicit-rejected']=earlier
        failure=f'''<details><summary>明确标签首轮被拒收：{earlier['summary']['requests']} 请求，{earlier['summary']['total_tokens']:,} tokens</summary>
        <p>模型尚未打开 NNI 函数体就报告依赖没有实现。结构与行范围校验通过，并不能保证推断正确；源码／轨迹复核拒收了这份结论。
        随后增加依赖已读门槛，给下一轮提供由 AST 生成的实际调用方法定义导航，没有提供预设语义结论。</p>
        <pre>{pretty(earlier['review'])}</pre><button data-download="pi-explicit-rejected">下载被拒收记录</button></details>'''
    trajectory=''.join(f'<details><summary>工具 {i} · {esc(t["name"])} · {esc(json.dumps(t["args"],ensure_ascii=False))}</summary><pre>{pretty(t["result"])}</pre></details>' for i,t in enumerate(tools,1))
    code='\n\n'.join('# '+p.name+'\n'+p.read_text() for p in [run/'runner.snapshot.mjs',run/'judgment.snapshot.mjs',run/'prepare.snapshot.py']+[run/name for name in ['revision-preparation.py','final-preparation.py'] if (run/name).exists()])
    return f'''<section id="judgment-overview"><h2>最新：明确判定代码里有什么、缺什么</h2>
    <p><b>先检查完整调用路径，再给判定。</b> 不再把“没搜到名字”作为未实现，也不把本地 mock 扩展成整个 artifact 缺失。
    本地入口与实验依赖分别给结论；论文行为仍为同一组冻结的 14 条，本轮未运行目标系统。</p>
    <div class="stats"><div><b>{cumulative_requests}</b>本阶段累计实际请求</div><div><b>{cumulative_tools}</b>累计工具调用</div><div><b>{cumulative_tokens:,}</b>已返回 tokens（含失败；超时用量未知）</div><div><b>14 × 2</b>行为 × 判定范围</div></div>
    <div class="flow">机制＋原页＋冻结行为 → Pi 沿脚本导入查依赖 → 读实际入口及委托函数 → 分别判定本地／artifact → 列出已实现动作、缺失动作、源码与反证</div>
    <p class="notice">更正上一轮说明：README 指向 microsoft/nni 的 sparta_artifact 分支，与当前 primary commit 相同。
    Dockerfile 安装的是 zheng-ningxin/nni 的 artifact 分支，本轮固定到 <code>{esc(source['repositories']['nni']['commit'])}</code>。
    原 Dockerfile 没有固定提交，本次查的是现存分支快照，不能断言它等于 2022 年实验使用的版本。</p>
    <h3>包含依赖后，经模型复核的分类</h3>{categories}
    <details open><summary>验收复核与剩余边界</summary><pre>{pretty(review)}</pre></details>
    <p>本表由 v6 的 14 行完整输出，加上 v7 对其中 5 条 artifact 行的实际模型复核组成；合并程序只应用模型返回，不自行改判定。五条分别为读取属性、节点更新、返回结果、剪枝合并和双向传播。输入复用前面真实的源码读取结果。中间失败、修订和一次流式超时均保留；超时没有返回用量，因此累计 tokens 只是已知量，不是完整消耗。</p><p>所有判定均适用于报告列出的入口／配置。明确缺少某行为属于静态质疑候选，不自动等于实际 bug；理论保证不能因“缺少循环”直接判成违反。</p>
    {failure}<details><summary>所有阶段的成本与接纳状态（不隐藏失败）</summary><pre>{pretty(stages)}</pre>{''.join(history_links)}</details><p><a href="#judgment-table">逐条有／缺与源码</a> · <a href="#judgment-trace">实际 prompt 与自主探索</a> · <a href="#pi-overview">保留上一轮报告</a></p></section>
    <section id="judgment-table"><h2>14 条行为的明确判断：本地入口 vs artifact 路径</h2>
    <p>{esc(report['mechanism_summary'])}</p><details><summary>本轮对齐的调用路径与判定范围</summary><pre>{pretty(dict(scope=report['scope_definition'],paths=report['paths']))}</pre></details>
    <div style="overflow:auto"><table style="min-width:1050px"><thead><tr><th style="width:22%">论文行为</th><th style="width:39%">本地 SpartaModel 入口</th><th style="width:39%">包含 NNI 的 artifact 路径</th></tr></thead><tbody>{rows}</tbody></table></div>
    <details><summary>按共享原因归组的质疑候选</summary><pre>{pretty(report['finding_clusters'])}</pre></details>
    <details><summary>检索边界与未决问题</summary><pre>{pretty({k:report[k] for k in ['search_limits','open_questions']})}</pre></details></section>
    <section id="judgment-trace"><h2>实际 prompt、原始返回、调用轨迹与完整实现</h2>
    <details><summary>完整 System prompt：实现判断合同</summary><pre>{pretty(system)}</pre></details>
    <details><summary>实际用户输入与自动生成的代码导航</summary><pre>{pretty(user)}</pre><button data-page="5">查看附带原页 p.5</button></details>
    {trajectory}<details><summary>最终模型实际看到的完整源码包（复用此前真实读取结果）</summary><pre>{pretty(source.get('evidence_packet',[]))}</pre></details><details><summary>全部实际请求体与模型消息</summary><pre>{pretty(dict(requests=archive['requests'],messages=messages))}</pre></details>
    <details><summary>原始最终返回</summary><pre>{esc((run/'final-response.txt').read_text())}</pre></details>
    <details><summary>完整执行代码</summary><pre>{esc(code)}</pre></details><button data-download="pi-explicit-judgment">下载完整实跑档案</button></section>'''
