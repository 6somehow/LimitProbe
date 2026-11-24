"""Standalone, bilingual audit page for actual k=2 discovery and merging calls."""
import argparse
import base64
from collections import Counter
from html import escape
import json
from pathlib import Path

from paperprobe.io import read_json
from paperprobe.multimodal_decomposition import parse_response


def esc(value):
    return escape(str(value))


def dump(value):
    return esc(json.dumps(value, ensure_ascii=False, indent=2))


def report(root, run, output, continuation=None, code_audit=None, pi_agent=None, pi_judgment=None, pi_conformance=None, pi_batch=None):
    protocol = read_json(run / "protocol.json")
    previous_run = Path(protocol['reused_discoveries'][0]['path']).parent if protocol.get('reused_discoveries') else None
    discoveries = [read_json(run / f"discovery-{i}.json") for i in (1, 2)]
    merged = read_json(run / "merged-mechanisms.json")
    comparison = read_json(run / "comparison.json")
    by_id = {r["id"]: r for d in discoveries for r in d["mechanisms"]}
    comparisons = {r["id"]: r for r in comparison["comparisons"]}
    archives = {}
    pages = {}
    source_request = read_json(run / "discovery-1.raw.request.json")
    for im in source_request["image_pages"]:
        pages[str(im["page"])] = "data:image/jpeg;base64," + base64.b64encode(Path(im["path"]).read_bytes()).decode()

    def evidence(rows):
        return ''.join(f'<blockquote><button data-page="{r["page"]}">PDF p.{r["page"]}</button> {esc(r["quote"])}</blockquote>' for r in rows)

    def card(m, include_id=True):
        hints = m.get("mechanical", [])
        note = "机械字符匹配仅供定位；不决定是否有语义依据。"
        if hints:
            note += f' {sum(bool(r["exact_text_match"]) for r in hints)}/{len(hints)} 条引文可精确匹配提取文本。'
        anchor = f' id="{m["id"]}"' if include_id else ''
        return f'''<article{anchor} class="card"><span class="tag">{m['id']}</span>
        <h3>{esc(m['name'])}</h3><p>{esc(m['description'])}</p>
        <p class="muted">机制边界：{esc(m.get('boundary',''))}</p>{evidence(m['evidence'])}
        <small>{note}</small></article>'''

    arms = ''.join(f'<section><h2>{title} · {len(d["mechanisms"])} 个候选</h2>' + ''.join(card(m) for m in d['mechanisms']) + '</section>'
                   for title,d in zip(("A：按章节发现", "B：按系统流程发现"), discoveries))
    merge_cards = []
    relation_names = dict(equivalent="与旧版等价", expanded="范围或粒度有变化", new_candidate="模型认为新增", uncertain="关系待确认")
    for m in merged['mechanisms']:
        c = comparisons[m['id']]
        members = ' + '.join(f'<a href="#{i}">{i}：{esc(by_id[i]["name"])}</a>' for i in m['members'])
        merge_cards.append(f'''<section class="merged" id="{m['id']}">{card(m, False)}
          <div class="decision"><p><b>来源：</b>{members}</p><p><b>合并理由：</b>{esc(m['merge_reason'])}</p>
          <p><b>父机制：</b>{esc(m.get('parent_name') or '无 / 未声明')}</p>
          <p><b>与旧版对齐：</b>{relation_names.get(c['relationship'],c['relationship'])}；
          历史文字版 {esc(', '.join(c['historical_ids']) or '未对应')}；此前图文版 {esc(', '.join(c['vision_ids']) or '未对应')}</p>
          <p>{esc(c['reason'])}</p></div></section>''')
    prompt_sections = []
    usage = Counter()
    for name,label in [('discovery-1','① 独立发现 A'),('discovery-2','② 独立发现 B'),('merge','③ 合并'),('comparison','④ 与旧版对齐')]:
        req=read_json(run/f'{name}.raw.request.json')
        response=read_json(run/f'{name}.raw.json')
        for k,v in response.get('usage',{}).items():
            if isinstance(v,int):usage[k]+=v
        archives[name]=dict(request=req,response=response)
        prompt_sections.append(f'''<details><summary>{label}：实际 prompt、输入和原始输出</summary>
          <p>请求路由 {esc(req['model'])}；实际返回模型 {esc(response.get('model'))}；图片 {len(req['image_pages'])} 页。
          完整输入保存于下方展开项和下载包，图片按物理页顺序追加；API key 不写入记录。</p>
          <h3>System prompt（原样）</h3><pre>{esc(req['prompt'])}</pre>
          <details><summary>User 文本输入（完整 JSON）</summary><pre>{dump(req['data'])}</pre></details>
          <h3>模型实际输出（解析显示，未改写）</h3><pre>{dump(parse_response(response))}</pre>
          <details><summary>原始响应（含 usage）</summary><pre>{dump(response)}</pre></details>
          <button data-download="{name}">下载完整请求元数据与响应</button></details>''')
    baseline_sections=[]
    for name,prefix,label in [(protocol['historical'],'H','历史文字版'),(protocol['baseline'],'V','此前图文版')]:
        original=parse_response(read_json(Path(name)/'map.raw.json'))
        baseline_sections.append(f'<details><summary>{label}：{len(original["mechanisms"])} 个原始候选（不是字符规则接纳数）</summary>'+
           ''.join(f'<article id="{prefix}{i:02d}" class="card"><h3>{prefix}{i:02d} {esc(m["name"])}</h3><p>{esc(m["description"])}</p>{evidence(m["evidence"])}</article>' for i,m in enumerate(original['mechanisms'],1))+'</details>')
    exclusions=''.join(f'<p>{esc(r["id"])}：{esc(r["reason"])}</p>{evidence(r["evidence"])}' for r in merged['exclusions']) or '<p>无排除项。</p>'
    continuation_html=''
    if continuation:
        from report_mechanism_continuation import render_continuation
        continuation_html,continuation_summary=render_continuation(continuation,run,archives)
    if code_audit:
        if not continuation:raise ValueError('Code audit requires its paper continuation')
        from report_behavior_code_audit import render_code_audit
        code_html,position_html=render_code_audit(code_audit,archives)
        continuation_html=continuation_html.replace('<section id="pipeline-flow">',
            code_html+position_html+'<section id="pipeline-flow">',1)
        continuation_html=continuation_html.replace('viewBox="0 0 1050 490"','viewBox="0 0 1050 650"')
        continuation_html=continuation_html.replace('viewBox="0 0 420 720"','viewBox="0 0 420 890"')
        wide='''<path d="M820 438V500" fill="none" stroke="#536c83" stroke-width="2" marker-end="url(#arrow)"/>
        <a href="#code-overview"><rect x="620" y="500" width="400" height="105" rx="10" fill="#dce9f7"/>
        <text x="820" y="533" text-anchor="middle" fill="#18334f" font-size="18">已接入：M02 的 14 条 → 静态代码对照</text>
        <text x="820" y="563" text-anchor="middle" fill="#18334f" font-size="14">固定 commit · 检索片段 · 连接的调用边</text>
        <text x="820" y="589" text-anchor="middle" fill="#18334f" font-size="14">归组为候选 finding；运行确认交给下一阶段</text></a>'''
        mobile='''<path d="M210 685V730" fill="none" stroke="#536c83" stroke-width="2" marker-end="url(#arrow-mobile)"/>
        <a href="#code-overview"><rect x="35" y="730" width="350" height="110" rx="9" fill="#dce9f7"/>
        <text x="210" y="763" text-anchor="middle" fill="#18334f" font-size="18">已接入：M02 的 14 条 → 代码对照</text>
        <text x="210" y="791" text-anchor="middle" fill="#18334f" font-size="14">固定版本 · 源码片段 · 静态调用链</text>
        <text x="210" y="820" text-anchor="middle" fill="#18334f" font-size="13">候选交接；其余 192 条与运行验证待完成</text></a>'''
        continuation_html=continuation_html.replace('</svg>',wide+'</svg>',1)
        # The second SVG is the mobile form; use its unique final output line.
        marker='原始记录保留；疑问项暂缓；待人工确认</text></a></svg>'
        continuation_html=continuation_html.replace(marker,'原始记录保留；疑问项暂缓；待人工确认</text></a>'+mobile+'</svg>',1)
    if pi_agent:
        if not code_audit:raise ValueError('Pi comparison requires baseline code audit')
        from report_pi_mechanism_agent import render_pi
        continuation_html=render_pi(pi_agent,code_audit,archives)+continuation_html
    if pi_judgment:
        from report_pi_judgment import render_judgment
        continuation_html=render_judgment(pi_judgment,archives)+continuation_html
    batch_html=''; batch_summary=None
    if pi_batch:
        from report_sparta_batch import render_batch
        batch_html,batch_summary=render_batch(root,pi_batch,archives)
    if pi_conformance:
        from report_pi_conformance import render_conformance
        from report_current_workflow import render_current_flow
        continuation_html=render_current_flow(root,batch_summary)+batch_html+render_conformance(root,pi_conformance,archives)+continuation_html
    fonts=(root/'runs/sparta-annotated-reading/fonts.css').read_text()
    payload=json.dumps(dict(archives=archives,pages=pages),ensure_ascii=False).replace('<','\\u003c')
    prior=''
    if previous_run:
        old_merge=read_json(previous_run/'merged-mechanisms.json')
        prior='<details><summary>首版合并与本次修订：完整保留，未覆盖旧结果</summary><p>首版将连续但职责不同的算法压成同一机制。本版只收紧合并粒度规则，复用原封不动的 A/B；不是重新进行两次发现，也不是独立验证集。</p><h3>首版合并输出</h3><pre>'+dump(old_merge)+'</pre><h3>首版实际合并 prompt</h3><pre>'+esc(read_json(previous_run/'merge.raw.request.json')['prompt'])+'</pre></details>'
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>SparTA · k=2 独立机制发现</title><style>__FONTS__
    *{box-sizing:border-box}body{margin:0;background:#f8f5ed;color:#16283f;font-family:'IBM Plex Sans',sans-serif;line-height:1.65}header{background:#10253d;color:#fff;padding:32px max(5vw,20px)}header h1{margin:0;font-size:30px}header p{max-width:1000px;color:#d3deea}nav{position:sticky;top:0;z-index:2;background:#18334f;padding:10px 5vw;display:flex;gap:24px;flex-wrap:wrap}nav a{color:white}main{max-width:1320px;padding:24px;margin:auto}h2{margin-top:32px}h3{font-size:18px;margin:8px 0}.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}.card,.panel,details{background:#fffdf8;border:1px solid #deddd4;border-radius:9px;padding:18px;margin:12px 0;min-width:0;overflow-wrap:anywhere}.card p{font-family:'Lora',serif}.tag{background:#e6edf4;padding:3px 9px;border-radius:4px;font-size:13px}.muted,small{color:#596577}.merged{display:grid;grid-template-columns:1fr 1fr;gap:18px;border-bottom:1px solid #ddd;padding:15px 0;scroll-margin-top:70px}.decision{background:#f0ece2;padding:20px;border-left:3px solid #8c71b7;overflow-wrap:anywhere}.decision a{display:inline-block;margin-bottom:5px}.stats{display:flex;gap:20px;flex-wrap:wrap}.stats b{font-size:28px;display:block}blockquote{margin:12px 0;border-left:3px solid #b5a271;background:#f4f0e7;padding:10px;font-size:14px}button{border:1px solid #aeb9c8;background:#eef2f7;color:#17304d;border-radius:4px;padding:5px 9px;cursor:pointer}a{color:#285880}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;max-height:700px;overflow:auto;background:#edf1f4;padding:14px}dialog{width:min(95vw,1000px);height:94vh;border:0;padding:12px;background:#eee}dialog img{width:100%}dialog::backdrop{background:#0009}.notice{border-left:4px solid #be8c30;background:#f5ecd8;padding:15px}.flow{background:#142f4b;color:white;padding:20px;border-radius:8px}section[id],article[id]{scroll-margin-top:80px}@media(max-width:800px){.cols,.merged{grid-template-columns:1fr}main{padding:15px}header h1{font-size:24px}nav{gap:12px}}
    </style><header><h1>SparTA：两次独立发现 → 合并机制</h1><p>CS6223 · 论文侧 semantic 拆解。两轮都读同一份 21 页论文的文字和原始图片；A 按章节，B 按系统流程；互不看对方结果，不看代码。</p></header>
    <nav><a href="#overview">实跑概况</a><a href="#discoveries">两次候选</a><a href="#merged">合并与旧版对比</a><a href="#prompts">实际 prompts</a><a href="#local">后续如何复核</a></nav><main>
    <section id="overview"><h2>这次实际跑了什么</h2><div class="stats">__STATS__</div>
    <p class="notice">当前只实跑机制发现、合并与旧版对齐；行为拆解和机制内复核已接入代码，但本次未运行。模型输出与模型对齐都待核对；机制数量不代表召回率或准确率。</p>
    <p>相对旧版改变了发现轮次和阅读视角，不能把差异全部归因于 k=2。旧结果按原始候选比较，不混入此前机械引文规则的拒收影响。20 项中包括 1 个组合父机制和 1 项 artifact 复现流程，并非 20 个互不重叠的核心算法。</p>__PRIOR__
    <details><summary>本轮协议与运行边界</summary><pre>__PROTOCOL__</pre></details></section>
    <section id="discoveries"><h2>两轮互相独立的原始发现</h2><p>英文名称与描述来自模型原始返回；引文按钮打开对应原始 PDF 页面。机械匹配只作提示。</p><div class="cols">__ARMS__</div></section>
    <section id="merged"><h2>合并结果及逐项旧版对齐</h2><p>每个来源候选须有去向，支持单轮候选；保留父子机制和不同阶段。下方合并理由与旧版对齐理由均为模型草稿。</p><p>__COMPARE_SUMMARY__</p>__MERGED__
    <details><summary>排除记录</summary>__EXCLUSIONS__</details><details><summary>未决问题</summary><pre>__QUESTIONS__</pre></details>
    <details><summary>旧版未对应项</summary><pre>__UNMATCHED__</pre></details>__BASELINES__</section>
    <section id="prompts"><h2>实际调用：完整 prompt 与实际返回</h2><p>以下是已经发出的请求，不是事后编写的示例。下载包含所有文本输入、图片页序/哈希和原始响应；原页可在页面内直接查看。</p>__PROMPTS__</section>
    <section id="local"><h2>后续：机制内逐项对账（尚未实跑）</h2><div class="flow">冻结机制 → 拆行为 → 独立原文步骤清单 → 对照行为并提出修改</div>
    <ol><li><b>先读原文，暂时不看已有行为：</b>只在该机制的相关页面中列出初始化、条件、更新、分支、fallback、返回与表示不变量。每项保留前提、原文和页码。</li>
    <li><b>双向对账：</b>每个原文步骤必须标 covered / partial / missing / uncertain；每条已有行为都必须检查是否复合、缺条件、无依据、重复或偏离机制。covered 必须引用具体行为 ID。</li>
    <li><b>提出修改而非直接裁决：</b>拆分保留原行为来源；补充项也要求原子性和原文依据。重复、归属疑问不自动删除；缺页/跨机制依赖保留 context_gaps。</li>
    <li><b>保留不确定性：</b>不重新扫描全文，不声称全文穷尽，也不运行目标代码。机械验证 ID、页码和引用结构，不以字符串匹配代替语义判断。</li></ol>
    <div class="panel"><h3>用传播机制理解“逐项对账”（解释用例，尚未运行新复核）</h3>
    <p>先从算法 1 独立列出步骤，例如：初始化工作集；判断循环条件；弹出节点；判断属性是否更新；调用传播规则；发现邻居；排除当前节点并入队；返回图。</p>
    <p>再对照拆出的行为：若一条同时写“循环并弹出节点”，标为 compound 并提出拆分；若只有“查找邻居”，就不能把“排除当前节点并入队”算成已覆盖。</p>
    <p>判定依据是能否分别核验，不机械地按动词数量拆句。例如一个前提可以附着在动作上；若循环终止条件本身就是需要核验的控制行为，则应单独保留。父机制只记录调度顺序，子机制记录内部算法步骤，避免重复。</p></div>
    <details><summary>下一阶段实际将使用的两个 prompt（设计，尚未发送）</summary><pre>__LOCAL_PROMPTS__</pre></details>
    <details><summary>当前完整流程代码（含尚未运行的后续阶段）</summary><pre>__CODE__</pre></details></section>
    </main><dialog id="pageDialog"><button id="closePage">关闭原页</button><p id="pageTitle"></p><img id="pageImg" alt="原始 PDF 页面"></dialog>
    <script id="payload" type="application/json">__PAYLOAD__</script><script>const data=JSON.parse(document.querySelector('#payload').textContent),dialog=document.querySelector('#pageDialog');document.addEventListener('click',e=>{const p=e.target.dataset.page;if(p){document.querySelector('#pageTitle').textContent='PDF 物理页 '+p;document.querySelector('#pageImg').src=data.pages[p];dialog.showModal()}const name=e.target.dataset.download;if(name){const url=URL.createObjectURL(new Blob([JSON.stringify(data.archives[name],null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name+'-actual-request-response.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}});document.querySelector('#closePage').onclick=()=>dialog.close();</script></html>'''
    from paperprobe.independent_discovery import LOCAL_SOURCE, LOCAL_ALIGN
    prior_usage=Counter()
    if previous_run:
        for name in ['merge','comparison']:
            for k,v in read_json(previous_run/f'{name}.raw.json').get('usage',{}).items():
                if isinstance(v,int):prior_usage[k]+=v
    stats=''.join(f'<div><b>{n}</b>{label}</div>' for n,label in [(len(discoveries[0]['mechanisms']),'A 候选'),(len(discoveries[1]['mechanisms']),'B 候选'),(len(merged['mechanisms']),'合并机制（含父子层级）'),(6 if previous_run else 4,'累计实际 API 请求'),(usage['total_tokens']+prior_usage['total_tokens'],'累计 tokens（含图像输入）')])
    replacements=dict(FONTS=fonts, STATS=stats, PROTOCOL=dump(protocol), ARMS=arms, MERGED=''.join(merge_cards),
                      COMPARE_SUMMARY=esc(comparison['summary']), EXCLUSIONS=exclusions,
                      QUESTIONS=dump(merged['open_questions']), BASELINES=''.join(baseline_sections),
                      UNMATCHED=dump({k:comparison.get(k,[]) for k in ['historical_unmatched','vision_unmatched']}),
                      PROMPTS=''.join(prompt_sections), PRIOR=prior,
                      CODE=esc((root/'src/paperprobe/independent_discovery.py').read_text()),
                      LOCAL_PROMPTS=esc(LOCAL_SOURCE+'\n\n--- 对账 ---\n\n'+LOCAL_ALIGN), PAYLOAD=payload)
    for k,v in replacements.items():html=html.replace('__'+k+'__',v)
    if continuation:
        html=html.replace('<main>','<main>'+continuation_html,1)
        html=html.replace('<nav>','<nav><a href="#continuation-M02">传播案例</a><a href="#pipeline-flow">流程图</a><a href="#continuation-all">行为复核</a>',1)
        html=html.replace('当前只实跑机制发现、合并与旧版对齐；行为拆解和机制内复核已接入代码，但本次未运行。模型输出与模型对齐都待核对；机制数量不代表召回率或准确率。',
                          '下方保留上一轮机制发现结果与统计；本轮行为拆解与复核在页面最前面展示。两轮原始请求分别留档，模型输出仍待核对。')
        html=html.replace('后续：机制内逐项对账（尚未实跑）','机制内逐项对账：方法说明')
        html=html.replace('用传播机制理解“逐项对账”（解释用例，尚未运行新复核）','传播机制的设计示例（实际结果见页面顶部）')
        html=html.replace('下一阶段实际将使用的两个 prompt（设计，尚未发送）','复核 prompt 定义（实际已发送版本见本轮调用记录）')
        html=html.replace('当前完整流程代码（含尚未运行的后续阶段）','完整发现流程及可选后续代码')
        continuation_code='\n\n'.join('# '+name+'\n'+(root/'src/paperprobe'/name).read_text()
            for name in ['mechanism_continuation.py','continuation_finalize.py','continuation_targeted.py'])
        html=html.replace('</main>','<details><summary>本轮续跑与格式修复完整代码</summary><pre>'+esc(continuation_code)+'</pre></details></main>')
        html=html.replace('</style>','table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px;border:1px solid #d6d9dc;text-align:left;vertical-align:top}th{background:#e6edf4}.flow-mobile{display:none}@media(max-width:800px){.flow-wide{display:none}.flow-mobile{display:block}}</style>',1)
    if code_audit:
        html=html.replace('<nav>','<nav><a href="#code-overview">代码对照</a><a href="#project-position">分工与方向</a>',1)
        html=html.replace('本轮只做论文侧行为拆解与复核，未查目标源码、未运行目标系统',
                          '以上是论文阶段结果；后续源码证据见「代码对照」，目标系统仍未运行')
        html=html.replace('SparTA：两次独立发现 → 合并机制','SparTA：论文机制 → 行为 → 代码证据')
        html=html.replace('</style>','table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #ddd8ce;vertical-align:top;text-align:left}th{background:#e8edf2}nav{max-height:150px;overflow:auto}</style>',1)
        html=html.replace('<title>SparTA · k=2 独立机制发现</title>','<title>SparTA · 论文行为与代码对照</title>')
        html=html.replace('</main>','<details><summary>本轮代码对照完整实现</summary><pre>'+esc((root/'src/paperprobe/behavior_code_audit.py').read_text())+'</pre></details></main>')
    if pi_agent:
        html=html.replace('</style>','section[id]{scroll-margin-top:130px}</style>',1)
        html=html.replace('<nav>','<nav><a href="#pi-overview">Pi 机制 Agent</a><a href="#pi-trace">自主查库轨迹</a>',1)
        html=html.replace('已接入：M02 的 14 条 → 静态代码对照','旧基线：14 条 → 逐项静态代码对照')
        html=html.replace('已接入：M02 的 14 条 → 代码对照','旧基线：14 条 → 逐项代码对照')
    if pi_judgment:
        html=html.replace('<nav>','<nav><a href="#judgment-overview">最新明确判定</a>',1)
        html=html.replace('新路线：Pi 以整个机制为单位自主查代码','上一轮保留：Pi 机制探索（最新判定见顶部）')
    if pi_conformance:
        html=html.replace('<nav>','<nav><a href="#current-workflow">当前完整流程图</a><a href="#conformance-overview">最新声明一致性判定</a>',1)
        html=html.replace('href="#pipeline-flow">流程图</a>','href="#pipeline-flow">历史拆解流程</a>')
        html=html.replace('最新：明确判定代码里有什么、缺什么','历史实现清单：不作为当前最终分类')
        html=html.replace('>最新明确判定</a>','>历史实现分类</a>')
    if pi_batch:
        html=html.replace('<title>SparTA · k=2 独立机制发现</title>','<title>SparTA · 论文语义拆解与 Pi 源码核验</title>')
        html=html.replace('SparTA：两次独立发现 → 合并机制','SparTA：论文语义拆解 → Pi 源码核验')
        html=html.replace('<nav>','<nav><a href="#sparta-batch">其余 19 项机制实跑</a>',1)
        html=html.replace('>最新声明一致性判定</a>','>M02 传播案例判定</a>')
        html=html.replace('最新：论文声明与代码是否一致','保留的 M02 传播案例：论文声明与代码是否一致')
        html=html.replace('当前 Pi 输出规则与校验器（新版，尚未重新调用模型）','当前 Pi 输出规则与校验器（新增机制已实跑；M02 保留原始调用）')
    output.write_text(html)
    print(output, output.stat().st_size, 'bytes')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--continuation',type=Path)
    parser.add_argument('--code-audit',type=Path)
    parser.add_argument('--pi-agent',type=Path)
    parser.add_argument('--pi-judgment',type=Path)
    parser.add_argument('--pi-conformance',type=Path)
    parser.add_argument('--pi-batch',type=Path)
    args=parser.parse_args()
    report(Path.cwd(),args.run,args.output,args.continuation,args.code_audit,args.pi_agent,args.pi_judgment,args.pi_conformance,args.pi_batch)
