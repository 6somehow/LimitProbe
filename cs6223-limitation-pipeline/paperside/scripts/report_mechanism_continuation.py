"""Render real continuation records into the existing standalone k=2 HTML."""
from collections import Counter
from html import escape
import json

from paperprobe.io import read_json
from paperprobe.multimodal_decomposition import parse_response


def render_continuation(run, inventory, archives):
    def esc(x):return escape(str(x))
    def pretty(x):return esc(json.dumps(x,ensure_ascii=False,indent=2))
    def ev(rows):
        result=[]
        for r in rows:
            page=r.get('page')
            if page is None:
                page=int(r['locator'].split('.')[-1])
            result.append(f'<blockquote><button data-page="{page}">PDF p.{page}</button> {esc(r["quote"])}</blockquote>')
        return ''.join(result)
    labels=dict(compound='复合动作',unsupported_inference='无依据推断',missing_precondition='缺少前提',
                insufficient_evidence='引文不足',duplicate='可能重复',scope_drift='机制归属疑问',
                covered='已覆盖',partial='部分覆盖',missing='未覆盖',uncertain='待确认')
    summary=read_json(run/'summary.json') if (run/'summary.json').exists() else dict(execution='running')
    groups=read_json(run/'behaviors.json')['groups'] if (run/'behaviors.json').exists() else {}
    if not groups:
        for path in run.glob('split-M*.json'):groups.update(read_json(path)['groups'])
    mechanisms=read_json(inventory/'merged-mechanisms.json')['mechanisms']
    reviewed={m['id']:read_json(run/f'{m["id"]}-local-review.json') for m in mechanisms if (run/f'{m["id"]}-local-review.json').exists()}
    counters=[]
    for key,label in [('reviewed_mechanisms','完成复核的机制'),('original_behaviors','初次拆解行为'),
                      ('additions','模型补充建议'),('split_compounds','写入草稿的复合项拆分'),
                      ('draft_behaviors','待审草稿行为'),('requests','本轮实际请求')]:
        counters.append(f'<div><b>{summary.get(key,"运行中")}</b>{label}</div>')
    metrics='<div class="stats">'+''.join(counters)+'</div>'

    def behavior(row):
        return f'<p><b>{esc(row.get("id","候选"))}</b> {esc(row["behavior"])}</p><p class="muted">前提：{esc(row["precondition"])}；依据：{esc(row["basis"])}</p>'+ev(row['evidence'])

    def detail(mid, guided=False):
        group=groups.get(mid,dict(behaviors=[],rejected=[],open_questions=[]))
        rev=reviewed.get(mid)
        if not rev:return '<p>本机制复核尚未完成；见失败/未决记录。</p>'
        source_path=run/f'{mid}-context-obligations.json'
        source=read_json(source_path if source_path.exists() else run/f'{mid}-obligations.json')
        decisions={r['id']:r for r in rev['behavior_reviews']}
        rows=[]
        for original in group['behaviors']:
            r=decisions[original['id']]
            issue='、'.join(labels[i] for i in r['issues']) or '模型未标记问题'
            replacement=''.join('<div class="decision">'+behavior(dict(v,id=f'{original["id"]}-R{i:02d}'))+'</div>' for i,v in enumerate(r['replacements'],1))
            if replacement and {'duplicate','scope_drift'} & set(r['issues']):
                replacement='<p class="notice">该替换有归属／重复疑问，保留建议，尚未写入草稿。</p>'+replacement
            rows.append('<article class="card">'+behavior(original)+f'<p><b>复核：{issue}</b> · {esc(r["reason"])}</p>'+replacement+'</article>')
        ledger={o['id']:o for o in source['obligations']}
        obligations=[]
        for c in rev['obligation_checks']:
            o=ledger[c['id']]
            obligations.append(f'<article class="card"><span class="tag">{esc(o["id"])} · {labels[c["status"]]}</span>'+
                               behavior(dict(o,id=o['id']))+f'<p>对应行为：{esc(", ".join(c["behavior_ids"]) or "无")}</p><p>{esc(c["reason"])}</p></article>')
        additions=[]
        for i,a in enumerate(rev['additions'],1):
            reasons=[c['reason'] for c in rev['obligation_checks'] if c['id'] in a['obligation_ids']]
            held=any(f.get('addition_index')==i for f in rev.get('consistency_flags',[]))
            absorbed=i in rev.get('absorbed_addition_indices',[])
            additions.append('<article class="card">'+behavior(dict(a,id=f'{mid}-A{i:02d}'))+
                             ('<p class="notice">该建议与“已覆盖”判定存在内部冲突，保留展示，暂不并入草稿。</p>' if held else '')+
                             ('<p class="notice">该补充已由上方替换条目完整表达，保留来源，不再重复加入草稿。</p>' if absorbed else '')+
                             f'<p>补充来源：{esc(", ".join(a["obligation_ids"]))}</p><p>{esc("；".join(reasons))}</p></article>')
        explanation=''
        if guided:
            explanation='''<div class="panel" id="count-scope"><h3>103 条与 8 条分别在数什么？</h3>
            <table><thead><tr><th>统计范围</th><th>初次拆解</th><th>复核后待审草稿</th></tr></thead><tbody>
            <tr><td>全部 20 个机制</td><td>103 条</td><td>206 条</td></tr>
            <tr><td>其中：传播机制 M02</td><td>8 条</td><td>14 条</td></tr>
            <tr><td>其余 19 个机制</td><td>95 条</td><td>192 条</td></tr></tbody></table>
            <p>这次带你看的是总清单中的 M02 子集。独立读原文另外列出的 15 项 O，是用于核对的步骤清单；它们会对应已有行为、提出拆分或补充，不会直接全部追加。</p></div>
            <div class="panel"><h3>先看我们实际做的四步</h3>
            <p><b>① 拆行为：</b>把冻结的传播机制和相关原页交给模型，得到下方初次行为列表。它与 M01/M03 同批请求，返回原文在“实际调用”中完整保留。</p>
            <p><b>② 独立读原文：</b>另一请求只看机制、边界、原页，不看刚才的行为，重新列出步骤。目的在于让遗漏仍有机会被发现。</p>
            <p><b>③ 双向对账：</b>将两份清单和原页一起交给模型。对原文步骤判断覆盖情况，对已有行为检查复合动作、前提和证据，并输出替换与补充建议。</p>
            <p><b>④ 生成明确拆分：</b>本次对账标出了 4 个复合项，却省略了替换数组，因此又做了一次专门的编辑请求。下方替换来自该请求，原始对账仍完整保留；模型同时判断哪些补充已被替换覆盖，以免重复添加。</p>
            <p>下方是本次真实结果，不预设一定会补到某一步。模型建议仍需要你核对论文；原条目不覆盖，修改另存为 draft。</p></div>'''
            if rev.get('edit_patch'):
                brief=[]
                for edit in rev['edit_patch']['edits']:
                    brief.append(f'<li><b>{esc(edit["id"])}</b> → {len(edit["replacements"])} 条：{esc(edit["reason"])}</li>')
                explanation+='<div class="panel"><h3>这次实际拆了哪 4 项</h3><ul>'+''.join(brief)+'</ul></div>'
                explanation+='''<div class="panel"><h3>先把这笔账算清楚</h3>
                <p>初次 8 条 → 4 个复合项各拆成 2 条（净增 4）→ 再独立新增 2 条 → 最后 14 条待审草稿。
                “查找邻居”虽然也出现在补充建议里，已经由 B05 的替换表达，因此没有重复加入。</p>
                <p>两条独立新增分别是：传播可双向进行；PropOneNode 的传播行为随算子和属性类型而变化。它们偏向能力与分发规则，阅读时还要核对与 M05/M07 的归属边界。</p>
                <p class="notice">仍值得你检查：B05 的第二条替换把“排除 N”作为入队节点的筛选条件写在同一句里。
                如果下一阶段按源码调用操作逐项核验，Remove(N) 和 Insert(...) 仍可进一步拆开。本次结果是模型建议，尚不能宣称每条都已经达到最终粒度。</p></div>'''
            mapping=[]
            counts=Counter(c['status'] for c in rev['obligation_checks'])
            stage_specs=[
                ('split-M01','① 初次拆行为','输入 M01/M02/M03 及第 4、5、9 页的文字和原图。整个批次返回 16 条，其中 M02 是 8 条。',
                 dict(groups=[g for g in parse_response(read_json(run/'split-M01.raw.json'))['groups'] if g['id']=='M02'])),
                ('M02-obligations','② 独立读原文','只看 M02、机制边界与第 5 页，不看上述 8 条行为。返回 15 项 O；原始 JSON 两处 ID 漏引号，派生解析仅补引号，原文与判断未改。',source['obligations']),
                ('M02-reconcile','③ 双向对账',f'同时看 8 条 B、15 项 O 与第 5 页。返回 {counts["covered"]} 项已覆盖、{counts["partial"]} 项部分覆盖、{counts["missing"]} 项未覆盖；标记 4 个复合项并提出 3 条补充，但未给出替换数组。',
                 parse_response(read_json(run/'M02-reconcile.raw.json'))),
                ('M02-explicit-edits','④ 明确生成替换','只处理那 4 个复合项及 3 条补充。返回 8 条替换，并将第 1 条补充标为已由替换覆盖。',rev.get('edit_patch',{})),
            ]
            for name,title,note,returned in stage_specs:
                req=read_json(run/f'{name}.raw.request.json')
                mapping.append(f'<article class="card"><h3>{title}</h3><p>{esc(note)}</p><p><a href="#call-{name}">查看完整实际请求和原始响应</a></p>'+
                    '<details><summary>这一步实际发送的完整 system prompt</summary><pre>'+esc(req['prompt'])+'</pre></details>'+
                    '<details><summary>这一步实际返回的传播机制内容</summary><pre>'+pretty(returned)+'</pre></details></article>')
            explanation+='<div id="propagation-call-map"><h3>流程节点 → 实际 prompt → 实际返回</h3>'+''.join(mapping)+\
                '<article class="card"><h3>⑤ 程序生成草稿：没有再调用模型</h3><p>保留 B01/B03/B04/B08 四条；用 8 条 R 替换四个复合 B；补入 A02/A03 两条。A01 被替换吸收，所以编号有跳号。</p><p><b>8 − 4 + 8 + (3 − 1) = 14。</b> M 是机制，B 是初次行为，O 是独立原文核对项，R 是替换，A 是补充。14 条仍是待审草稿。</p></article></div>'
        return explanation+f'<h3>初次行为 → 每条复核 → 建议替换（{len(group["behaviors"])} 条原始行为）</h3>'+''.join(rows)+\
            f'<h3>独立原文步骤及对账（{len(ledger)} 项）</h3><details><summary>展开逐项 covered / partial / missing / uncertain</summary>'+''.join(obligations)+'</details>'+\
            f'<h3>本机制补充建议（{len(additions)} 条）</h3>'+(''.join(additions) or '<p>模型本轮未提出额外补充。</p>')+\
            '<details><summary>未决项、初次拆解拒收项和原始复核 JSON</summary><pre>'+pretty(dict(context_gaps=rev.get('context_gaps',[]),open_questions=rev.get('open_questions',[]),
             source_out_of_scope=source.get('out_of_scope',[]),split_rejected=group.get('rejected',[]),
             split_open_questions=group.get('open_questions',[]),review=rev))+'</pre></details>'

    table=[]
    all_details=[]
    for m in mechanisms:
        mid=m['id'];r=reviewed.get(mid);g=groups.get(mid,{})
        compound=sum('compound' in b['issues'] for b in r['behavior_reviews']) if r else '—'
        adds=len(r['additions']) if r else '—'
        counts=Counter(c['status'] for c in r['obligation_checks']) if r else {}
        table.append(f'<tr><td><a href="#continuation-{mid}">{mid} {esc(m["name"])}</a></td><td>{len(g.get("behaviors",[]))}</td><td>{compound}</td><td>{adds}</td><td>{esc(dict(counts))}</td></tr>')
        if mid!='M02':
            all_details.append(f'<section id="continuation-{mid}"><details><summary>{mid} {esc(m["name"])}</summary>'+detail(mid)+'</details></section>')
    trace=[]
    for req_path in sorted(run.glob('*.raw.request.json')):
        name=req_path.name.removesuffix('.raw.request.json')
        req=read_json(req_path)
        response_path=run/f'{name}.raw.json'
        response=read_json(response_path) if response_path.exists() else dict(status='No response saved')
        key='continuation/'+name
        archives[key]=dict(request=req,response=response)
        try:parsed=parse_response(response)
        except (ValueError,KeyError,TypeError):parsed=response
        trace.append(f'<details id="call-{name}"><summary>{esc(name)}：真实 prompt、输入、返回</summary>'+
                     f'<p>图片物理页：{esc([im["page"] for im in req["image_pages"]])}；实际模型：{esc(response.get("model","未完成"))}</p>'+
                     '<h3>实际 system prompt</h3><pre>'+esc(req['prompt'])+'</pre>'+
                     '<details><summary>完整 user 文本输入</summary><pre>'+pretty(req['data'])+'</pre></details>'+
                     '<h3>实际模型返回</h3><pre>'+pretty(parsed)+'</pre>'+
                     f'<button data-download="{key}">下载完整请求元数据与原始响应</button></details>')
    guided=detail('M02',True)
    flow=f'''<section id="pipeline-flow"><h2>实际流程图</h2><p>发现与合并是上一轮已完成的输入，本轮没有重跑。两份行为清单到对账时才汇合；“独立步骤”请求看不到初次行为。本轮基础流程 47 次调用，另有 4 次一致性重核、2 次缺页上下文修正和 1 次明确拆分请求；全部留档。</p>
    <div style="overflow-x:auto"><svg class="flow-wide" viewBox="0 0 1050 490" role="img" aria-label="冻结机制分别产生初次行为和独立原文步骤，两者汇合进行机制内对账，形成待审草稿" style="min-width:780px;width:100%;background:#f0ece2;border-radius:8px">
    <defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8" fill="#536c83"/></marker></defs>
    <g fill="none" stroke="#536c83" stroke-width="2" marker-end="url(#arrow)"><path d="M175 175H265V108H340"/><path d="M175 175H265V260H340"/><path d="M580 108H660V175H715"/><path d="M580 260H660V175H715"/><path d="M835 223V335"/></g>
    <a href="#merged"><rect x="20" y="120" width="155" height="110" rx="10" fill="#dce2e8"/><text x="97" y="153" text-anchor="middle" fill="#18334f" font-size="18">冻结机制 20 项</text><text x="97" y="182" text-anchor="middle" fill="#18334f" font-size="14">沿用 k=2 合并结果</text><text x="97" y="207" text-anchor="middle" fill="#18334f" font-size="14">0 次重新发现 / 合并</text></a>
    <a href="#continuation-trace"><rect x="340" y="55" width="240" height="105" rx="10" fill="#dbe8f5"/><text x="460" y="90" text-anchor="middle" fill="#18334f" font-size="18">批量拆行为 · 7 次调用</text><text x="460" y="119" text-anchor="middle" fill="#18334f" font-size="14">初次行为 {summary.get('original_behaviors','?')} 条</text><text x="460" y="143" text-anchor="middle" fill="#18334f" font-size="14">保留原文、前提、明确/推断</text></a>
    <a href="#call-M02-obligations"><rect x="340" y="205" width="240" height="110" rx="10" fill="#e7dff1"/><text x="460" y="239" text-anchor="middle" fill="#18334f" font-size="18">独立原文步骤 · 20 次调用</text><text x="460" y="268" text-anchor="middle" fill="#18334f" font-size="14">仅看机制相关原页与边界</text><text x="460" y="294" text-anchor="middle" fill="#18334f" font-size="14">不看初次行为清单</text></a>
    <a href="#call-M02-reconcile"><rect x="715" y="120" width="240" height="105" rx="10" fill="#dceadf"/><text x="835" y="155" text-anchor="middle" fill="#18334f" font-size="18">机制内对账 · 20 次调用</text><text x="835" y="183" text-anchor="middle" fill="#18334f" font-size="14">步骤是否遗漏？行为是否复合？</text><text x="835" y="207" text-anchor="middle" fill="#18334f" font-size="14">同时检查前提、证据与归属</text></a>
    <a href="#continuation-all"><rect x="620" y="335" width="400" height="103" rx="10" fill="#142f4b"/><text x="820" y="369" text-anchor="middle" fill="white" font-size="18">待审草稿：{summary.get('draft_behaviors','?')} 条行为</text><text x="820" y="399" text-anchor="middle" fill="white" font-size="14">补充建议 {summary.get('additions','?')}；实际建议拆复合项 {summary.get('split_compounds','?')}</text><text x="820" y="423" text-anchor="middle" fill="white" font-size="14">原始记录不覆盖 · 内部冲突暂缓并入</text></a>
    <text x="22" y="385" fill="#536c83" font-size="15">文字 + 原页图像贯穿模型调用</text><text x="22" y="414" fill="#536c83" font-size="15">机械检查辅助定位；不替代语义判断</text><text x="22" y="465" fill="#536c83" font-size="14">点击流程节点可跳到真实记录；尚未进行目标源码核验、目标执行或独立人工确认。</text></svg>
    <svg class="flow-mobile" viewBox="0 0 420 720" role="img" aria-label="移动端流程图：冻结机制，分别拆行为和独立读原文，汇合对账，修改为待审草稿" style="width:100%;background:#f0ece2;border-radius:8px">
    <defs><marker id="arrow-mobile" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8" fill="#536c83"/></marker></defs>
    <g fill="none" stroke="#536c83" stroke-width="2" marker-end="url(#arrow-mobile)"><path d="M210 105V138H105V170"/><path d="M210 105V138H315V170"/><path d="M105 285V320H210V350"/><path d="M315 285V320H210V350"/><path d="M210 440V480"/><path d="M210 550V590"/></g>
    <a href="#merged"><rect x="65" y="20" width="290" height="85" rx="9" fill="#dce2e8"/><text x="210" y="55" text-anchor="middle" fill="#18334f" font-size="19">冻结的 20 项机制</text><text x="210" y="83" text-anchor="middle" fill="#18334f" font-size="14">沿用上一轮结果 · 本轮不重找</text></a>
    <a href="#call-split-M01"><rect x="15" y="170" width="180" height="115" rx="9" fill="#dbe8f5"/><text x="105" y="200" text-anchor="middle" fill="#18334f" font-size="17">初次拆行为</text><text x="105" y="228" text-anchor="middle" fill="#18334f" font-size="15">7 次调用 → 103 条</text><text x="105" y="257" text-anchor="middle" fill="#18334f" font-size="13">保留前提与原文</text></a>
    <a href="#call-M02-obligations"><rect x="225" y="170" width="180" height="115" rx="9" fill="#e7dff1"/><text x="315" y="200" text-anchor="middle" fill="#18334f" font-size="17">独立读原文步骤</text><text x="315" y="228" text-anchor="middle" fill="#18334f" font-size="15">每机制 1 次，共 20 次</text><text x="315" y="257" text-anchor="middle" fill="#18334f" font-size="13">不看左侧的行为清单</text></a>
    <a href="#call-M02-reconcile"><rect x="65" y="350" width="290" height="90" rx="9" fill="#dceadf"/><text x="210" y="383" text-anchor="middle" fill="#18334f" font-size="19">机制内双向对账 · 20 次</text><text x="210" y="414" text-anchor="middle" fill="#18334f" font-size="14">步骤漏了吗？已有条目复合吗？</text></a>
    <a href="#continuation-trace"><rect x="35" y="480" width="350" height="70" rx="9" fill="#f1e2c4"/><text x="210" y="508" text-anchor="middle" fill="#18334f" font-size="16">本次额外局部修订 · 7 次</text><text x="210" y="534" text-anchor="middle" fill="#18334f" font-size="13">一致性重核 4 + 补相关页 2 + 明确拆分 1</text></a>
    <a href="#continuation-all"><rect x="35" y="590" width="350" height="95" rx="9" fill="#142f4b"/><text x="210" y="624" text-anchor="middle" fill="white" font-size="19">206 条待审草稿</text><text x="210" y="652" text-anchor="middle" fill="white" font-size="14">25 个复合项拆分 · 75 条新增并入</text><text x="210" y="675" text-anchor="middle" fill="white" font-size="12">原始记录保留；疑问项暂缓；待人工确认</text></a></svg></div></section>'''
    case=f'''<section id="continuation-overview"><h2>机制内复核：本轮真实结果</h2>{metrics}
    <p class="notice">直接复用原来的 20 项合并机制，未重新发现、未重新合并；本轮只做论文侧行为拆解与复核，未查目标源码、未运行目标系统。所有替换和补充为模型建议，独立人工确认仍待完成。</p>
    <p>77 条补充建议中，1 条与“已覆盖”判定冲突而暂缓，1 条已由传播机制的替换覆盖；75 条写入待审草稿。另有 1 项替换因机制归属／重复疑问暂缓。格式修复只补 ID 引号、补回省略的空数组，原始返回保留。</p>
    <p><a href="#continuation-M02">先看传播机制</a> · <a href="#continuation-all">全部机制</a> · <a href="#continuation-trace">本轮完整实际调用</a></p>
    <details><summary>执行协议、统计和失败/未决记录</summary><pre>{pretty(read_json(run/'protocol.json'))}\n{pretty(summary)}</pre></details></section>
    <section id="continuation-M02"><h2>带你走一遍：M02 稀疏属性传播</h2>
    <p><button data-page="5">打开 PDF p.5：算法 1</button> · <a href="#call-split-M01">初次拆解调用</a> · <a href="#call-M02-obligations">独立步骤调用</a> · <a href="#call-M02-reconcile">对账调用</a> · <a href="#call-M02-explicit-edits">明确拆分调用</a></p>{guided}</section>
    {flow}<section id="continuation-all"><h2>全部机制：补了什么，拆了什么</h2><div style="overflow-x:auto"><table><thead><tr><th>机制</th><th>原始行为</th><th>复合项标记</th><th>补充建议</th><th>原文步骤对账</th></tr></thead><tbody>{''.join(table)}</tbody></table></div>{''.join(all_details)}</section>
    <section id="continuation-trace"><h2>本轮实际 prompt 与返回（{len(trace)} 个请求记录）</h2>{''.join(trace)}</section>'''
    return case,summary
