"""Embed all actual remaining-mechanism Pi runs in the existing standalone paper board."""
from pathlib import Path
from html import escape
import json
from collections import Counter
from paperprobe.io import read_json
from paperprobe.conformance_view import three_conclusion_view

LABELS={'supports':'支持论文声明','deviates':'实现与论文不符','absent':'声明未实现'}

def jl(path):return [json.loads(x) for x in path.read_text().splitlines() if x] if path.exists() else []

def collect(cohort):
    spec=read_json(cohort/'cohort.json');cases={}
    for name in spec['batches']:
        batch=Path(name)
        for statefile in sorted(batch.glob('M??/state.json')):
            state=read_json(statefile);cases[state['mechanism']]=dict(state=state,folder=statefile.parent,batch=batch)
    return spec,cases

def render_batch(root,cohort,archives):
    esc=lambda v:escape(str(v))
    pretty=lambda v:esc(json.dumps(v,ensure_ascii=False,indent=2))
    spec,cases=collect(cohort)
    inventory=read_json(root/'runs/sparta-independent-k2-v2/merged-mechanisms.json')['mechanisms']
    mechanisms={m['id']:m for m in inventory}
    totals=Counter();completed=pending=reviewed=expected=requests=tool_calls=tokens=0;unknown_usage=[];rejected_stages=[]
    sections=[];overview=[];stage_links=[]
    source_commits={}
    for mid in sorted(x for x in mechanisms if x!='M02'):
        frozen=read_json(root/'runs/sparta-k2-behaviors-v1'/f'{mid}-draft.json')['behaviors'];expected+=len(frozen)
        case=cases.get(mid);name=mechanisms[mid]['name']
        if not case:
            overview.append(f'<tr><td>{mid} {esc(name)}</td><td>{len(frozen)}</td><td>未开始</td><td>—</td><td>—</td></tr>');continue
        state=case['state'];folder=case['folder'];stages=[];source_reads=[]
        # Include every stage, including failed repairs, without rewriting raw records.
        stage_order={name:n for n,name in enumerate(state.get('stages',[]))}
        for stage in sorted((p for p in folder.iterdir() if p.is_dir() and (p/'protocol.json').exists()),key=lambda p:stage_order.get(p.name,999)):
            info=dict(name=stage.name,protocol=read_json(stage/'protocol.json'),
                summary=read_json(stage/'summary.json') if (stage/'summary.json').exists() else {'state':'running'},
                system=read_json(stage/'system-prompt.json') if (stage/'system-prompt.json').exists() else {},
                input=read_json(stage/'initial-user-input.json') if (stage/'initial-user-input.json').exists() else {},
                requests=[dict(file=p.name,body=read_json(p)) for p in sorted(stage.glob('request-*.json'))],
                messages=jl(stage/'messages.jsonl'),tools=jl(stage/'tools.jsonl'),events=jl(stage/'events.jsonl'),
                raw=(stage/'final-response.txt').read_text() if (stage/'final-response.txt').exists() else '',
                read_spans=read_json(stage/'read-spans.json') if (stage/'read-spans.json').exists() else [],
                completion_protocol=read_json(stage/'completion-protocol.json') if (stage/'completion-protocol.json').exists() else None,
                completion_code=(stage/'completion.snapshot.py').read_text() if (stage/'completion.snapshot.py').exists() else None)
            inp=read_json(stage/'input.json');source_commits.update({k:v['commit'] for k,v in inp['repositories'].items()})
            source_reads += [x['result'] for x in inp.get('evidence_packet',[])]+[x['result'] for x in info['tools'] if x['name']=='read_repo' and isinstance(x.get('result'),dict) and 'lines' in x['result']]
            if info['summary'].get('error') or info['summary'].get('validation_error'):
                rejected_stages.append(dict(stage=f'{mid}/{stage.name}',error=info['summary'].get('error'),validation_error=info['summary'].get('validation_error')))
            requests+=len(info['requests']);tool_calls+=info['summary'].get('tool_calls',0);tokens+=info['summary'].get('total_tokens',0)
            if any(m.get('role')=='assistant' and m.get('stopReason')=='error' for m in info['messages']):unknown_usage.append(f'{mid}/{stage.name}')
            key=f'batch/{mid}/{stage.name}';archives[key]=info
            stages.append((stage,key,info))
        status=state['state']
        if status!='reviewed' or not state.get('report'):
            overview.append(f'<tr><td><a href="#batch-{mid}">{mid} {esc(name)}</a></td><td>{len(frozen)}</td><td>{esc(status)}</td><td>—</td><td>—</td></tr>')
            sections.append(f'<section id="batch-{mid}"><h2>{mid} · {esc(name)}</h2><p>任务状态：{esc(status)}。尚无可接纳的最终报告，不计入本轮判定。</p><pre>{pretty(state)}</pre>'+''.join(f'<button data-download="{key}">下载 {mid}/{stage.name} 实际记录</button>' for stage,key,_ in stages)+'</section>');continue
        report_path=case['batch']/state['report'];report=three_conclusion_view(read_json(report_path/'report.json'))
        reviewed+=1
        for c in report['checks']:
            v=c['artifact']
            if v['review_state']=='completed':completed+=1;totals[v['verdict']]+=1
            else:pending+=1
        count=Counter(c['artifact']['verdict'] for c in report['checks'] if c['artifact']['review_state']=='completed')
        wait=sum(c['artifact']['review_state']=='pending' for c in report['checks'])
        overview.append(f'<tr><td><a href="#batch-{mid}">{mid} {esc(name)}</a></td><td>{len(frozen)}</td><td>调查＋模型复核已运行</td><td>支持 {count["supports"]}／不符 {count["deviates"]}／未实现 {count["absent"]}</td><td>{wait} 项待办</td></tr>')
        ev={e['id']:e for e in report['code_evidence']}
        def snippets(refs):
            parts=[]
            for uid in refs:
                e=ev[uid];lines={}
                for r in source_reads:
                    if r.get('repo')==e['repo'] and r.get('path')==e['path']:
                        for n,line in enumerate(r['lines'].splitlines(),r['start_line']):
                            if n in lines and lines[n]!=line:raise ValueError('Source evidence changed across stages')
                            lines[n]=line
                excerpt='\n'.join(lines.get(n,'[源码未留档]') for n in range(e['start_line'],e['end_line']+1))
                if '[源码未留档]' in excerpt:raise ValueError('Cited source range missing from archive')
                parts.append(f'<details><summary>{esc(uid)} · {esc(e["repo"])} · {esc(e["path"])}:{e["start_line"]}–{e["end_line"]}</summary><pre>{esc(excerpt)}</pre></details>')
            return ''.join(parts)
        def scoped(v):
            if v['review_state']=='pending':return '<b>核验任务待完成</b><p>'+esc(v['pending_reason'])+'</p>'
            return f'<b>{LABELS[v["verdict"]]}</b><p><b>代码事实：</b>{esc(v["actual"])}</p>'+(
                f'<p><b>具体差异：</b>{esc(v["discrepancy"])}</p>' if v['discrepancy'] else '')+f'<p><b>等价性核对：</b>{esc(v["equivalence"])}</p><small>效果判定：{esc(v["effect_status"])}</small>'+snippets(v['refs'])
        first=next((read_json(stage/'report.json') for stage,_,_ in stages if stage.name.startswith('draft') and (stage/'report.json').exists()),None)
        changes=[]
        if first:
            old={c['id']:c for c in first['checks']}
            for c in report['checks']:
                for scope in ['local_entry','artifact']:
                    before=old[c['id']][scope];after=c[scope]
                    if (before['review_state'],before['verdict'])!=(after['review_state'],after['verdict']):
                        changes.append(dict(id=c['id'],scope=scope,before=before['verdict'],after=after['verdict'],actual=after['actual'],discrepancy=after['discrepancy'],pending_reason=after['pending_reason']))
        rows=[];todos=[]
        for c in report['checks']:
            v=c['artifact']
            paper=f'<blockquote><button data-page="{c["paper"]["page"]}">论文原页 p.{c["paper"]["page"]}</button> {esc(c["paper"]["quote"])}</blockquote>'
            if v['review_state']=='pending':todos.append(f'<article class="card"><b>{esc(c["id"])}</b><p>{esc(c["requirement"])}</p>{paper}{scoped(v)}</article>')
            if any(c[s]['review_state']=='completed' for s in ['local_entry','artifact']):
                rows.append(f'<tr id="batch-{c["id"]}"><td><b>{esc(c["id"])}</b><p>{esc(c["requirement"])}</p><small>{esc(c["claim_type"])}</small>{paper}</td><td>{scoped(c["local_entry"])}</td><td>{scoped(v)}</td></tr>')
        findings=''.join(f'<article class="card"><h3>{esc(f["title"])}</h3><p>{esc(f["scope"])} · {esc("、".join(f["behavior_ids"]))}</p><p>适用范围：{esc(f["boundary"])}</p><p>效果边界：{esc(f["unverified_effect"])}</p>{snippets(f["refs"])}</article>' for f in report['findings']) or '<p>本轮没有归组质疑候选。</p>'
        trace=[]
        for stage,key,info in stages:
            trace.append(f'<details><summary>{mid}/{stage.name}：协议、用量与校验状态</summary><pre>{pretty(dict(protocol=info["protocol"],summary=info["summary"],completion=info['completion_protocol']))}</pre></details>')
            trace.append(f'<details><summary>{mid}/{stage.name}：完整实际 System prompt</summary><pre>{pretty(info["system"])}</pre></details>')
            for field,label in [('input','实际用户输入（机制、原文和源码上下文）'),('tools','全部实际工具调用及返回'),('raw','原始最终返回'),('messages','完整模型与工具消息')]:
                trace.append(f'<details data-batch-lazy="{key}" data-batch-field="{field}"><summary>{mid}/{stage.name}：{label}</summary><pre></pre></details>')
            for n,request in enumerate(info['requests']):
                trace.append(f'<details data-batch-lazy="{key}" data-batch-field="requests" data-batch-index="{n}"><summary>{mid}/{stage.name}/{esc(request["file"])}：实际 HTTP 请求体</summary><pre></pre></details>')
            trace.append(f'<button data-download="{key}">下载 {mid}/{stage.name} 全部实际记录</button>')
        sections.append(f'''<section id="batch-{mid}"><h2>{mid} · {esc(name)}</h2><p>{esc(report['mechanism_summary'])}</p>
        <p><b>artifact 本轮模型判定：</b>支持 {count['supports']}／不符 {count['deviates']}／未实现 {count['absent']}；核验待办 {wait} 项。
        结论限于各行选定的入口、配置和 commit；模型复核不等于独立人工确认。</p>
        <div class="notice"><p><b>本地入口：</b>{esc(report['scope_definition']['local_entry'])}</p><p><b>本次 artifact 范围：</b>{esc(report['scope_definition']['artifact'])}</p><p>下方判定只适用于上述路径与固定版本；其他实验入口须另行对齐。</p></div>
        <details><summary>从首份接纳草稿到最终报告的改判（{len(changes)} 个路径判定）</summary><pre>{pretty(changes) if changes else ('本轮复核未改变主标签；完整返回仍保留在下方。' if first else '首阶段未通过接纳检查；补查后首次形成可接纳判断，原始失败记录仍保留。')}</pre></details>
        <details><summary>本机制的对齐入口与版本</summary><pre>{pretty(dict(scope=report['scope_definition'],repositories=source_commits))}</pre></details>
        <div style="overflow:auto"><table style="min-width:1050px"><thead><tr><th style="width:26%">论文要求与原文</th><th style="width:37%">本地机制入口</th><th style="width:37%">所检查的 artifact 范围</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
        <details><summary>本机制待完成核验任务（不计入结论）</summary>{''.join(todos) or '<p>无待办。</p>'}</details>
        <details><summary>按共享原因归组的质疑候选</summary>{findings}</details><details><summary>范围与未决边界</summary><pre>{pretty(report['limits'])}</pre></details>
        <details id="batch-trace-{mid}"><summary>本机制所有实际 prompts、原始返回、工具轨迹与失败记录</summary>{''.join(trace)}</details></section>''')
    summary=dict(selected_mechanisms=19,reviewed_mechanisms=reviewed,expected_behaviors=expected,completed_behaviors=completed,pending_behaviors=pending,
        counts=dict(totals),rejected_stages=rejected_stages,requests=requests,tool_calls=tool_calls,returned_tokens=tokens,unknown_usage=unknown_usage,
        failures={mid:c['state'] for mid,c in cases.items() if c['state']['state']=='failed'},target_execution='not_run')
    reused=three_conclusion_view(read_json(root/'runs/sparta-pi-conformance-M02-v2/report.json'))
    combined=totals.copy();reused_pending=0
    for c in reused['checks']:
        v=c['artifact']
        if v['review_state']=='completed':combined[v['verdict']]+=1
        else:reused_pending+=1
    summary['including_reused_M02']=dict(mechanisms=reviewed+1,expected_behaviors=206,completed_behaviors=sum(combined.values()),pending_behaviors=pending+reused_pending,counts=dict(combined))
    write_path=cohort/'summary.json';write_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    archives['sparta-batch-summary']=dict(protocol=spec,summary=summary,acceptance=read_json(cohort/'acceptance.json') if (cohort/'acceptance.json').exists() else None)
    runtime_files={}
    for batch in spec['batches']:
        runtime=Path(batch)/'runtime'
        if runtime.exists():
            runtime_files[Path(batch).name]={p.name:p.read_text() for p in runtime.iterdir() if p.is_file() and p.suffix in ['.py','.mjs']}
    runtime_files['report_and_validation']={name:(root/'scripts'/name).read_text() for name in ['report_sparta_batch.py','report_independent_discovery.py','report_current_workflow.py','validate_sparta_batch.mjs']}
    archives['sparta-batch-code']=runtime_files
    html=f'''<section id="sparta-batch"><h2>最新批量核验：SparTA 其余 19 项机制</h2>
    <p>沿用冻结机制与行为，没有重新发现机制、没有把 Wanting 的结果输入模型。每机制独立选择源码入口；本地实现与对应 artifact 路径分别判定。
    每项运行 Pi 自主查库与模型语义复核，补查和收尾请求另行留档。实际请求中的图像二进制用哈希留档，原始论文页可点开；提示文字与原始最终返回完整保留。源码均来自固定 commit，目标系统未运行。</p>
    <div class="stats"><div><b>{reviewed}/19</b>已运行调查与语义复核的机制</div><div><b>{completed}/{expected}</b>已形成判定的行为</div><div><b>{requests}</b>实际模型请求（含失败/修正）</div><div><b>{tokens:,}</b>已返回 tokens</div></div>
    <p><b>artifact 本轮模型判定：</b>支持 {totals['supports']}／不符 {totals['deviates']}／未实现 {totals['absent']}。
    核验待办 {pending} 项，不作为第四类结论。M02 复用此前结果，另见原传播案例；这里的统计仅含新增的 192 条。</p>
    <p>连同沿用的 M02：20 项机制中已判定 {sum(combined.values())}/206 条；支持 {combined['supports']}／不符 {combined['deviates']}／未实现 {combined['absent']}；核验待办 {pending+reused_pending} 条。</p>
    <p class="notice">声明数量与候选数量不是独立缺陷数；父子机制存在重叠。结构/引用校验不证明语义正确，模型结论仍待团队独立复核。
    Dockerfile 追踪分支，当前固定源码快照不等于已确认的历史实验环境。原生内核和依赖只做静态检查。</p>
    <p>新增只读工具调用 {tool_calls} 次。{'部分失败响应未返回 token 用量，已返回 tokens 是已知下界。' if unknown_usage else '用量按服务实际返回累计；不代表货币费用。'}</p>
    <p>留存 {len(rejected_stages)} 个被拒收阶段；后续接纳不会覆盖先前的失败和成本。源码留档已逐行与固定 commit 校验，语义判断仍需独立复核。</p>
    <details><summary>批量协议、失败与用量</summary><pre>{pretty(dict(protocol=spec,summary=summary))}</pre></details>
    <div style="overflow:auto"><table><thead><tr><th>机制</th><th>冻结行为数</th><th>执行状态</th><th>三类模型判定</th><th>任务进度</th></tr></thead><tbody>{''.join(overview)}</tbody></table></div>
    <p><a href="#conformance-overview">保留 M02 传播案例</a> · <a href="#current-workflow">当前流程图</a> · <button data-download="sparta-batch-summary">下载批量汇总</button> · <button data-download="sparta-batch-code">下载全部实际执行代码快照</button></p></section>
    {''.join(sections)}
    <script>document.addEventListener('toggle',function(event){{const el=event.target;if(!el.open||!el.dataset.batchLazy||el.dataset.loaded)return;const archive=data.archives;let value=archive[el.dataset.batchLazy][el.dataset.batchField];if(el.dataset.batchIndex!==undefined)value=value[Number(el.dataset.batchIndex)];el.querySelector('pre').textContent=typeof value==='string'?value:JSON.stringify(value,null,2);el.dataset.loaded='1';}},true);</script>'''
    return html,summary
