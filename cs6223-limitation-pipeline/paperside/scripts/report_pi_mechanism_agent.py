"""Render actual Pi mechanism investigation without hiding rejected attempts."""
from html import escape
import json
from pathlib import Path
from paperprobe.io import read_json
from report_behavior_code_audit import LABELS


def render_pi(run, baseline, archives):
    esc=lambda x:escape(str(x))
    pretty=lambda x:esc(json.dumps(x,ensure_ascii=False,indent=2))
    jl=lambda p:[json.loads(s) for s in p.read_text().splitlines() if s] if p.exists() else []
    protocol=read_json(run/'protocol.json');summary=read_json(run/'summary.json')
    review=read_json(run/'review-notes.json') if (run/'review-notes.json').exists() else {}
    report=read_json(run/'report.json') if (run/'report.json').exists() else {}
    user=read_json(run/'initial-user-input.json');system=read_json(run/'system-prompt.json')
    tools=jl(run/'tools.jsonl');messages=jl(run/'messages.jsonl')
    base=read_json(baseline/'audit.json');old={x['id']:x for x in base['checks']}
    checks={x['id']:x for x in report.get('checks',[])}
    requests=[dict(file=p.name,payload=read_json(p)) for p in sorted(run.glob('request-*.json'))]
    archives['pi-mechanism']=dict(protocol=protocol,summary=summary,system=system,user=user,
                                 requests=requests,messages=messages,tools=tools,report=report,review=review)
    def cite(e):return f"{esc(e['path'])}:{e['start_line']}–{e['end_line']}"
    rows=''
    for b in user['behaviors']:
        c=checks.get(b['id'],{});prior=old[b['id']]['result']
        rows+=f'''<tr><td>{esc(b['id'])}</td><td>{esc(b['behavior'])}</td>
        <td>{LABELS[prior]}</td><td>{LABELS.get(c.get('result'),'无有效结论')}</td><td>{esc(c.get('rationale',''))}<br>
        {'<br>'.join(cite(e) for e in c.get('evidence',[]))}</td></tr>'''
    trail=''.join(f'''<details id="pi-tool-{i}"><summary>工具 {i} · {esc(t['name'])} · {esc(json.dumps(t['args'],ensure_ascii=False))}</summary>
        <pre>{pretty(t['result'])}</pre></details>''' for i,t in enumerate(tools,1))
    paths=''.join(f'''<article class="card"><h3>{esc(p['name'])}</h3><p>{esc(p['role'])} · {esc(p['connection'])}</p>
        <p>{'<br>'.join(cite(e) for e in p['evidence'])}</p></article>''' for p in report.get('paths',[]))
    failed=run.parent/'sparta-pi-mechanism-M02-v1';failure=''
    if failed!=run and (failed/'summary.json').exists():
        fs=read_json(failed/'summary.json')
        archives['pi-rejected-v1']=dict(summary=fs,protocol=read_json(failed/'protocol.json'),
            tools=jl(failed/'tools.jsonl'),response=(failed/'final-response.txt').read_text())
        failure=f'''<details><summary>首轮失败也保留：{fs['requests']} 次请求，{fs['total_tokens']:,} tokens</summary>
        <p>目录清单和搜索结果过长，模型未读取函数体就到预算收尾，引用了只在搜索中出现的行。该结果被引用校验拒收，不能记为成功核验。
        第二轮仅调整工具输出为短目录与跨目录搜索摘要，并提醒尽早读函数体；未提供上一轮源码结论。</p><pre>{pretty(fs)}</pre>
        <button data-download="pi-rejected-v1">下载失败记录</button></details>'''
    calls=''.join(f'<details><summary>{esc(r["file"])} · 实际 HTTP 请求体（图片只保留哈希）</summary><pre>{pretty(r["payload"])}</pre></details>' for r in requests)
    review_html='<p>'+esc(review.get('key_observation',''))+'</p>'+''.join('<p><b>'+esc(x['item'])+'：</b>'+esc(x['issue'])+'</p>' for x in review.get('flags',[]))
    code='\n\n'.join('# '+p.name+'\n'+p.read_text() for p in [run/'runner.snapshot.mjs',Path('tools/pi-mechanism-agent/prepare.py'),Path('tools/pi-mechanism-agent/validation.mjs')])
    return f'''<section id="pi-overview"><h2>新路线：Pi 以整个机制为单位自主查代码</h2>
    <p>论文阶段保持冻结：20 项合并机制 → 行为拆解与机制内复核 → 共 206 条草稿。这里仅处理 M02 传播机制的 14 条行为。
    <b>探索单位是机制；行为用于最后逐项对账。</b> Pi 是工具循环框架，推理仍由 SoCLaaS 模型完成。</p>
    <div class="stats"><div><b>{summary['requests']}</b>Pi 模型请求</div><div><b>{summary['tool_calls']}</b>自主工具调用</div>
    <div><b>{summary['total_tokens']:,}</b>本轮 tokens</div><div><b>{len(checks)}/14</b>通过结构与引用检查</div></div>
    <div style="overflow:auto"><svg viewBox="0 0 960 310" role="img" aria-label="论文到 Pi 代码探索的实际流程" style="width:100%;min-width:600px;background:#f0ece2;border-radius:12px">
    <defs><marker id="pi-arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#60778e"/></marker></defs>
    <g fill="none" stroke="#60778e" stroke-width="2" marker-end="url(#pi-arr)"><path d="M220 80H290"/><path d="M480 80H550"/><path d="M740 80H795"/><path d="M385 112V175"/><path d="M550 208H480V112"/></g>
    <g font-family="sans-serif" text-anchor="middle" fill="#19324a">
    <a href="#pi-prompts"><rect x="20" y="40" width="200" height="80" rx="10" fill="#f4e8ad"/><text x="120" y="70">冻结论文输入</text><text x="120" y="98" font-size="13">M02 + 原页 p.5 + 14 条行为</text></a>
    <a href="#pi-trace"><rect x="290" y="40" width="190" height="80" rx="10" fill="#d6e8f6"/><text x="385" y="70">一个 Pi 会话</text><text x="385" y="98" font-size="13">自主决定下一步查哪里</text></a>
    <a href="#pi-paths"><rect x="550" y="40" width="190" height="80" rx="10" fill="#dfd7ef"/><text x="645" y="70">机制实现路径图</text><text x="645" y="98" font-size="13">入口 / 独立规则 / 实验依赖</text></a>
    <a href="#pi-checks"><rect x="795" y="40" width="145" height="80" rx="10" fill="#dbe9d6"/><text x="867" y="70">14 条逐项对账</text><text x="867" y="98" font-size="13">证据 / 范围 / 未决项</text></a>
    <rect x="240" y="175" width="310" height="80" rx="10" fill="#e1e8ed"/><text x="395" y="205">只读工具：本轮 18 次调用</text><text x="395" y="232" font-size="13">目录 · 搜索 · 读 Git blob · 符号 · 原页</text>
    <text x="755" y="218" font-size="14">最终引用须来自实际读取的行</text><text x="755" y="246" font-size="14">候选判断仍待人工确认；不跑目标</text>
    </g></svg></div>
    <p>框架 {esc(protocol['framework'])} {esc(protocol['version'])}；SoCLaaS 请求路由 {esc(protocol['requested_model'])}；
    commit <code>{esc(protocol['commit'])}</code>。模型可查完整论文与该 commit 的所有受限文本文件。
    未提供预选代码片段、Wanting 结论或旧版核验结果。只读 Git blob，目标系统未运行。</p>
    <p class="notice">这是已知开发案例上的方法试跑，非盲测。两轮模型与工具策略不同，旧基线主要检索 Python，本轮可搜索更多文件，不能据此声称 Pi 更准确。
    “通过检查”仅表示 ID 完整且引用位于实际读取范围，语义判断仍待人工复核。tokens 是服务返回的累计量，不代表收费金额。</p>
    {failure}<details><summary>协议、实际预算与状态</summary><pre>{pretty(dict(protocol=protocol,summary=summary))}</pre></details>
    <p><a href="#pi-paths">实现路径</a> · <a href="#pi-checks">逐项对比</a> · <a href="#pi-trace">实际工具轨迹</a> · <a href="#pi-prompts">完整 prompts 与返回</a></p></section>
    <section id="pi-paths"><h2>Pi 找到的机制实现路径</h2><article class="notice"><h3>先看人工阅读提示：模型措辞仍需收紧</h3>{review_html}<p>以下保留模型原始输出；这些静态阅读提示并非独立人工标注或最终裁决。</p></article><p>{esc(report.get('mechanism_summary','本轮未形成可接受报告。'))}</p>{paths}
    <details open><summary>候选归组与反证</summary><pre>{pretty(report.get('finding_clusters',[]))}</pre></details>
    <details><summary>检索边界与未决问题</summary><pre>{pretty({k:report.get(k,[]) for k in ['search_limits','open_questions']})}</pre></details></section>
    <section id="pi-checks"><h2>同一组 14 条行为：旧基线与 Pi 原始判断</h2><p>这张表比较输出，不是人工标准答案。旧版“未定位”可能由引用检查失败造成；旧版语义疑点见原代码对照区。</p>
    <div style="overflow-x:auto"><table><thead><tr><th>ID</th><th>论文行为</th><th>旧版最终状态</th><th>Pi 模型判断</th><th>解释与源码证据</th></tr></thead><tbody>{rows}</tbody></table></div></section>
    <section id="pi-trace"><h2>实际探索：工具调用顺序及完整结果</h2><p>以下是工具真实返回；搜索结果仅用于导航，最终引用需来自 read_repo 的实际行范围。图像数据省略，哈希保留。</p>{trail}</section>
    <section id="pi-prompts"><h2>完整 prompt、模型返回与可复跑代码</h2>
    <details><summary>实际 System prompt</summary><pre>{pretty(system)}</pre></details>
    <details><summary>初始输入：机制、14 条行为与相关原文</summary><pre>{pretty(user)}</pre><button data-page="5">查看实际附带的论文原页 p.5</button></details>
    {calls}<details><summary>各轮实际完整消息（含助手与工具返回）</summary><pre>{pretty(messages)}</pre></details>
    <details><summary>最终原始返回</summary><pre>{esc((run/'final-response.txt').read_text())}</pre></details>
    <details><summary>完整执行代码</summary><pre>{esc(code)}</pre></details>
    <button data-download="pi-mechanism">下载本轮全部请求与轨迹</button></section>'''
