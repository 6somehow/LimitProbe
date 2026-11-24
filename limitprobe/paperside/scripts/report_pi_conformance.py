"""Render actual paper-to-code claim conformance, preserving implementation history."""
from html import escape
import json
from pathlib import Path
from paperprobe.io import read_json
from paperprobe.conformance_view import three_conclusion_view

LABELS={'supports':'代码支持论文声明','deviates':'代码实现与论文不符','absent':'论文声明未实现'}
KINDS={'mechanism_step':'机制步骤','semantic_effect':'语义效果','guarantee':'数学／运行保证'}
EFFECTS={'supported':'该功能效果有证据支持','refuted':'模型提出功能效果反证，需核对','not_established':'尚未证明功能效果失败或等价','not_applicable':'本项未评价功能效果'}


def render_conformance(root, run, archives):
    esc=lambda v:escape(str(v))
    pretty=lambda v:esc(json.dumps(v,ensure_ascii=False,indent=2))
    jl=lambda p:[json.loads(s) for s in p.read_text().splitlines() if s] if p.exists() else []
    original_report=read_json(run/'report.json');report=three_conclusion_view(original_report);source=read_json(run/'input.json');summary=read_json(run/'summary.json')
    tools=jl(run/'tools.jsonl');messages=jl(run/'messages.jsonl');protocol=read_json(run/'protocol.json')
    user=read_json(run/'initial-user-input.json');system=read_json(run/'system-prompt.json')
    review=read_json(run/'acceptance-review.json') if (run/'acceptance-review.json').exists() else {'status':'pending'}
    evidence={e['id']:e for e in report['code_evidence']}
    source_reads=[p['result'] for p in source['evidence_packet']]+[t['result'] for t in tools if t['name']=='read_repo']
    archive=dict(protocol=protocol,summary=summary,system=system,input=user,report=report,raw_model_report=original_report,review=review,
                 tools=tools,messages=messages,requests=[dict(file=p.name,body=read_json(p)) for p in sorted(run.glob('request-*.json'))])
    archives['pi-claim-conformance']=archive
    pending_rows=[c for c in report['checks'] if any(c[s]['review_state']=='pending' for s in ['local_entry','artifact'])]
    completed_count=sum(all(c[s]['review_state']=='completed' for s in ['local_entry','artifact']) for c in report['checks'])
    stages=[dict(run=str(run),summary=summary)]
    draft_path=Path(source['first_pass_run']) if source.get('first_pass_run') else None
    draft_block=''
    if draft_path and draft_path.exists():
        draft=dict(protocol=read_json(draft_path/'protocol.json'),summary=read_json(draft_path/'summary.json'),
            structural_recheck=read_json(draft_path/'structural-recheck.json') if (draft_path/'structural-recheck.json').exists() else None,
            system=read_json(draft_path/'system-prompt.json'),input=read_json(draft_path/'initial-user-input.json'),
            report=read_json(draft_path/'report.json'),raw=(draft_path/'final-response.txt').read_text(),
            tools=jl(draft_path/'tools.jsonl'),messages=jl(draft_path/'messages.jsonl'),
            requests=[dict(file=p.name,body=read_json(p)) for p in sorted(draft_path.glob('request-*.json'))])
        archives['pi-claim-conformance-draft']=draft
        stages.insert(0,dict(run=str(draft_path),summary=draft['summary'],structural_recheck=draft['structural_recheck']))
        before={c['id']:c for c in three_conclusion_view(draft['report'])['checks']}
        changes=[dict(id=c['id'],scope=scope,before=before[c['id']][scope]['verdict'],after=c[scope]['verdict']) for c in report['checks'] for scope in ['local_entry','artifact'] if c[scope]['verdict']!=before[c['id']][scope]['verdict']]
        draft_block=f'<details><summary>第一遍原始判定 → 模型一致性复核：实际改判</summary><pre>{pretty(changes)}</pre><pre>{pretty(draft["structural_recheck"])}</pre><button data-download="pi-claim-conformance-draft">下载第一遍全部实际记录</button></details>'
    archive['stages']=stages
    requests=sum(len(list(Path(x['run']).glob('request-*.json'))) for x in stages)
    tool_calls=sum(x['summary']['tool_calls'] for x in stages)
    tokens=sum(x['summary']['total_tokens'] for x in stages)
    def excerpts(refs):
        result=[]
        for uid in refs:
            e=evidence[uid];lines={}
            for r in source_reads:
                if r.get('repo')==e['repo'] and r.get('path')==e['path']:
                    for n,line in enumerate(r['lines'].splitlines(),r['start_line']):lines[n]=line
            text='\n'.join(lines.get(n,'[未读取]') for n in range(e['start_line'],e['end_line']+1))
            result.append(f'<details><summary>{esc(uid)} · {esc(e["repo"])} · {esc(e["path"])}:{e["start_line"]}–{e["end_line"]}</summary><pre>{esc(text)}</pre></details>')
        return ''.join(result)
    def verdict(v):
        if v['review_state']=='pending':
            return '<b>核验任务未完成</b><p>'+esc(v['pending_reason'])+'</p><p>下一步：'+esc(v.get('workflow_next_step','继续补查，再形成正式结论。'))+'</p>'
        discrepancy=f'<p><b>具体不符／缺失：</b>{esc(v["discrepancy"])}</p>' if v['discrepancy'] else ''
        return f"""<strong>{LABELS[v['verdict']]}</strong><p><b>代码事实：</b>{esc(v['actual'])}</p>{discrepancy}
        <p><b>等价实现核对：</b>{esc(v['equivalence'])}</p><small>{EFFECTS[v['effect_status']]}</small>{excerpts(v['refs'])}"""
    rows=''.join(f'''<tr id="conformance-{c['id']}"><td><b>{esc(c['id'])}</b> · {KINDS[c['claim_type']]}<p><b>论文要求：</b>{esc(c['requirement'])}</p>
        <blockquote><button data-page="{c['paper']['page']}">原页 p.{c['paper']['page']}</button> {esc(c['paper']['quote'])}</blockquote></td>
        <td>{verdict(c['local_entry'])}</td><td>{verdict(c['artifact'])}</td></tr>''' for c in report['checks'] if any(c[s]['review_state']=='completed' for s in ['local_entry','artifact']))
    pending_html=''.join('<article class="card"><b>'+esc(c['id'])+'</b> · '+esc(c['requirement'])+'<p>任务状态：核验未完成；没有正式判定。</p>'+''.join(verdict(c[s]) for s in ['artifact'] if c[s]['review_state']=='pending')+'</article>' for c in pending_rows) or '<p>当前没有待完成核验任务。</p>'
    categories=''
    for label,title in LABELS.items():
        ids=[c['id'] for c in report['checks'] if c['artifact']['verdict']==label]
        categories+=f'<p><b>{title}（{len(ids)}）</b>：'+('、'.join(f'<a href="#conformance-{uid}">{uid}</a>' for uid in ids) or '无')+'</p>'
    candidates=[]
    for i,f in enumerate(report['findings'],1):
        candidates.append(f'''<article class="card"><h3>候选 {i}：{esc(f['title'])}</h3><p>范围：{esc(f['scope'])} · {'、'.join(f['behavior_ids'])}</p>
        <p><b>判断边界：</b>{esc(f['boundary'])}</p><p><b>效果边界：</b>{esc(f['unverified_effect'])}</p>{excerpts(f['refs'])}</article>''')
    checks={c['id']:c for c in report['checks']}
    focus=checks['M02-B06-R01'];v=focus['artifact']
    trace=''.join(f'<details><summary>工具 {i} · {esc(t["name"])} · {esc(json.dumps(t["args"],ensure_ascii=False))}</summary><pre>{pretty(t["result"])}</pre></details>' for i,t in enumerate(tools,1))
    code='\n\n'.join('# '+p.name+'\n'+p.read_text() for p in [run/'runner.snapshot.mjs',run/'conformance.snapshot.mjs',run/'prepare.snapshot.py']+([run/'workflow.snapshot.py'] if (run/'workflow.snapshot.py').exists() else []))
    return f'''<section id="conformance-overview"><h2>最新：论文声明与代码是否一致</h2>
    <p>本轮主分类为<b>支持声明／实现不符／声明未实现</b>。“实现多少”不再作为最终类别。
    每条先明确论文要求，再对齐实际入口、比较语义、检查替代实现；主仓库入口与包含依赖的实验路径分别给判定。</p>
    <div class="stats"><div><b>{requests}</b>两阶段实际模型请求</div><div><b>{tool_calls}</b>本轮新增工具调用</div><div><b>{tokens:,}</b>两阶段已返回 tokens</div><div><b>{completed_count}/14</b>已完成判定的声明</div></div>
    <div class="flow">冻结机制＋原文原页＋已核实源码 → Pi 自主补查 → 明确论文要求及声明类型 → 比较代码行为与等价实现 → 一致性判定 → 归组质疑候选</div>
    <p>同一份 M02 机制和 14 条论文行为，复用此前已读取并逐行校验 Git blob 的源码；没有向本轮模型提供旧分类、旧结论或预设质疑条目。
    流程自动执行“机制探索与初判 → 一次模型语义一致性复核”。复核会读取本轮初判，检查遗漏条件与跨条目矛盾；不读取旧版实现分类。机械检查只验证结构、来源范围及字段一致性，语义比较由 Pi 内的模型完成。本轮为开发案例，不是独立准确率评估。</p>
    <h3>包含依赖后的正式结论（仅三类）</h3>{categories}<p>核验进度：14 项中，{completed_count} 项已形成判定，{len(pending_rows)} 项任务待完成；待办不计入三类结论。</p>
    <article class="notice"><h3>先看“反复传播直到不再更新”</h3>
    <p><b>论文要求：</b>{esc(focus['requirement'])}</p><p><b>声明类型：</b>{KINDS[focus['claim_type']]}</p>{verdict(v)}
    <p>机制／调度步骤与论文不一致，可以作为静态质疑；这与证明输出错误或无法达到不动点是两件分别需要证据的事。</p></article>
    <p>“声明未实现”限于列出的 commit、入口与配置，不代表全世界或全仓库都不存在相关函数；未完成的核验保留为任务状态，完成后再进入三类结论。目标系统未运行。</p>
    {draft_block}<details><summary>三结论视图的状态迁移说明（未新增模型调用）</summary><pre>{pretty(report["status_migration"])}</pre></details><details><summary>本轮历史复核与验收记录</summary><pre>{pretty(review)}</pre></details>
    <p><a href="#conformance-pending">查看待完成核验任务</a> · <a href="#conformance-table">逐条论文→代码判定</a> · <a href="#conformance-findings">质疑候选</a> · <a href="#conformance-trace">实际 prompts 与返回</a></p></section>
    <section id="conformance-table"><h2>已完成判定：原文要求、代码事实和具体差异</h2>
    <details><summary>对齐范围与固定版本</summary><pre>{pretty(dict(scope=report['scope_definition'],repositories=protocol['repositories']))}</pre></details>
    <div style="overflow:auto"><table style="min-width:1050px"><thead><tr><th style="width:26%">论文声明与原文</th><th style="width:37%">本地入口</th><th style="width:37%">artifact 依赖路径</th></tr></thead><tbody>{rows}</tbody></table></div></section>
    <section id="conformance-pending"><h2>核验进度：待完成的任务</h2><p>这里记录工作状态，不是第四类结论，也不作为质疑候选。</p>{pending_html}</section><section id="conformance-findings"><h2>实现不符／声明未实现：按共享原因归组</h2>{''.join(candidates)}
    <details><summary>检索与结论边界</summary><pre>{pretty(report['limits'])}</pre></details></section>
    <section id="conformance-trace"><h2>当前三结论规则与历史实际调用</h2><details><summary>当前 Pi 输出规则与校验器（新版，尚未重新调用模型）</summary><pre>{esc((root/"tools/pi-mechanism-agent/conformance.mjs").read_text())}</pre></details><p>以下调用发生在分类规则调整之前，原始记录不改写。已完成的 13 条判定保留；B08 转为待完成任务，没有补造新判定。</p>
    <details><summary>实际 System prompt：声明一致性判定</summary><pre>{pretty(system)}</pre></details>
    <details><summary>实际输入：机制、14 条声明、原文与验证过的源码包</summary><pre>{pretty(user)}</pre><button data-page="5">查看实际附带的原始论文页</button></details>
    {trace}<details><summary>全部实际 HTTP 请求与模型消息</summary><pre>{pretty(dict(requests=archive['requests'],messages=messages))}</pre></details>
    <details><summary>原始模型返回（历史格式原样保留；当前规则只有三类结论）</summary><pre>{esc((run/'final-response.txt').read_text())}</pre></details>
    <details><summary>完整执行代码、prompt 与校验器</summary><pre>{esc(code)}</pre></details>
    <button data-download="pi-claim-conformance">下载本轮全部实际记录</button></section>'''
