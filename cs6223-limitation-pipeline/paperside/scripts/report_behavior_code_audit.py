"""Embed pinned code evidence and a bounded project-position review in the paper board."""
from html import escape
import json

from paperprobe.io import read_json


LABELS=dict(supported='支持',partial='部分支持',local_mismatch='局部不一致',unlocated='未定位／证据链未通过',static_undecidable='静态不可裁决')


def render_code_audit(run,archives):
    esc=lambda v:escape(str(v))
    pretty=lambda v:esc(json.dumps(v,ensure_ascii=False,indent=2))
    audit=read_json(run/'audit.json');protocol=read_json(run/'protocol.json')
    rows={b['id']:b for b in read_json(run/'behaviors.json')}
    context=read_json(run/'source-context.json')
    checks={c['id']:c for c in audit['checks']}
    def snippets(source,ids):
        parts=[]
        for sid in ids:
            s=source['snippets'][sid]
            lines='\n'.join(f'{i}  {line}' for i,line in s['lines'].items())
            parts.append(f'<details><summary>{sid} · {esc(s["function"])} · {esc(s["path"])}:{s["start"]}–{s["end"]} · '+
                         ('完整函数体' if s['complete'] else '节选')+'</summary><pre>'+esc(lines)+'</pre></details>')
        return ''.join(parts)
    def path(c,source):
        edges=[]
        for eid in c['edges']:
            e=source['edges'][eid]
            a,b=(source['snippets'][e[k]] for k in ['caller','callee'])
            edges.append(f'<li><code>{esc(a["function"])} → {esc(b["function"])}</code><br>{esc(a["path"])}:{e["line"]} · <code>{esc(e["quote"])}</code></li>')
        return '<ol>'+''.join(edges)+'</ol>' if edges else '<p>未形成通过引用校验的调用链。</p>'
    cells=[];cards=[];trace=[]
    for uid,row in rows.items():
        c=checks[uid];source=context[uid]
        gate=c.get('gate_failure')
        warning='引用待修正' if gate else '模型语义待独立核对'
        cells.append(f'<tr><td><a href="#code-{uid}">{uid}</a></td><td>{esc(row["behavior"])}</td><td>{LABELS.get(c.get("model_result"),"无完整判断")}</td><td>{LABELS[c["result"]]}</td><td>{warning}</td></tr>')
        ev=''.join(f'<blockquote><button data-page="{int(e.get("page") or e["locator"].split(".")[-1])}">论文原页</button> {esc(e["quote"])}</blockquote>' for e in row['evidence'])
        special=''
        if uid=='M02-B03':special='<p class="notice">阅读疑点：extract_sparsity 确实读取 input_tesa/output_tesa。要区分“读取属性这个子动作有支持”和“通用图传播入口未执行算法”，不能把整条都笼统算作缺失。</p>'
        if uid=='M02-B06-R02':special='<p class="notice">阅读疑点：论文伪代码返回 G，Python API 返回属性信息，返回形式不同本身不证明语义不一致。应优先核对是否产生了应有的属性更新。</p>'
        if uid=='M02-B08':special='<p class="notice">阅读疑点：直通函数本身也可能终止。缺少传播循环能支持“该入口未实现论文流程”的候选，不能直接证明论文的终止性保证被违反。</p>'
        request=read_json(run/f'{uid}.raw.request.json');response=read_json(run/f'{uid}.raw.json')
        key='code/'+uid;archives[key]=dict(request=request,response=response)
        cards.append(f'<section id="code-{uid}"><details><summary>{uid} · {LABELS[c["result"]]} · {esc(row["behavior"])}</summary>'+
            f'<p>论文前提：{esc(row["precondition"])}</p>'+ev+f'<p><b>模型原判：</b>{LABELS.get(c.get("model_result"),"未完成")}；<b>引用校验后：</b>{LABELS[c["result"]]}</p>'+
            (f'<p class="notice">引用校验：{esc(gate)}。这不等于证明源码没有实现该行为。</p>' if gate else '')+
            f'<p>{esc(c["rationale"])}</p>'+special+path(c,source)+snippets(source,c['snippets'])+
            '<details><summary>全部检索候选（含未被结论引用的源码）</summary>'+snippets(source,list(source['snippets']))+'</details>'+
            f'<p><a href="#code-call-{uid}">对应实际 prompt 与原始返回</a></p></details></section>')
        trace.append(f'<details id="code-call-{uid}"><summary>{uid}：实际 prompt、输入和返回</summary><h3>实际 system prompt</h3><pre>{esc(request["prompt"])}</pre>'+
            '<details><summary>完整 user 输入：论文、该行为、检索代码和调用边</summary><pre>'+pretty(request['data'])+'</pre></details>'+
            '<h3>模型原始返回</h3><pre>'+esc(response['choices'][0]['message']['content'])+'</pre>'+
            f'<button data-download="{key}">下载完整请求元数据和响应</button></details>')
    focus=checks['M02-B02-R01'];src=context[focus['id']]
    code_stage=f'''<section id="code-overview"><h2>新增：传播机制 → 固定版本代码对照</h2>
    <div class="stats"><div><b>14 / 206</b>本轮实跑的待审行为</div><div><b>{audit['requests']}</b>本轮代码对照 API 请求</div><div><b>{audit['counts'].get('local_mismatch',0)}</b>模型局部不一致（引用有效）</div><div><b>{audit['counts'].get('unlocated',0)}</b>引用链未通过／未定位</div></div>
    <p>直接使用传播机制的 14 条草稿，没有重抽论文、没有读取 Wanting 的 findings。固定 commit：<code>{audit['commit']}</code>。从 218 个 Python 文件建立 755 个函数和 402 条静态边的索引，1 文件语法解析失败；原生内核未纳入这个索引。</p>
    <p class="notice">这里只完成 M02；其余 19 个机制的 192 条草稿尚未做本轮代码对照。下面是模型静态判断，不是确认了 12 个 bug。多个条目落在同一实现路径，应按一组候选 finding 汇总；论文实验实际走哪条路径仍未决。</p>
    <div class="flow">14 条冻结行为 → 每条独立检索源码与调用边 → 14 次独立模型判断 → 引用与连接性检查 → 分组候选交接</div>
    <h3>先看一条：S 非空时是否继续传播？</h3><p>{esc(focus['rationale'])}</p>{path(focus,src)}{snippets(src,focus['snippets'])}
    <p>最直接的局部证据是被调用函数先收集现有属性，再令 <code>post_sparsity = pre_sparsity</code> 返回。可提出“这个入口是否跳过传播”的待验证问题；不能据此断言全仓库或所有论文实验都没有传播实现。</p>
    <h3>14 条逐项结果</h3><div style="overflow-x:auto"><table><thead><tr><th>行为 ID</th><th>论文行为</th><th>模型原判</th><th>引用校验后</th><th>审查状态</th></tr></thead><tbody>{''.join(cells)}</tbody></table></div>{''.join(cards)}
    <details><summary>本轮候选交接卡（尚未发送给团队、未执行）</summary><pre>{pretty(read_json(run/'handoff.json'))}</pre></details>
    <details><summary>固定版本、检索范围、执行协议和汇总</summary><pre>{pretty(protocol)}\n{pretty(audit)}</pre></details></section>
    <section id="code-trace"><h2>代码对照实际 prompt 与返回（14 次）</h2>{''.join(trace)}</section>'''
    position='''<section id="project-position"><h2>我们是否在正确的路上？</h2>
    <p><b>判断：继续把论文侧结果接到代码证据，同时收束前端拆解。</b>按后来确认的团队分工，这属于 Zhaopeng 的步骤 1 与 3a。你正在完成自己的模块，但当前模型输出还不是小组整体项目的完成证据。</p>
    <table><thead><tr><th>成员</th><th>按当前讨论的职责</th><th>本轮边界</th></tr></thead><tbody>
    <tr><td>Zhaopeng</td><td>论文语义、范围/前提 → 行为 → 论文到代码核验</td><td>输出带版本、原文、代码与未决项的候选交接</td></tr>
    <tr><td>Wanting</td><td>代码出发发现 limitation，并检查论文是否声明</td><td>本轮不替代她的独立发现，也没有把她的发现喂给模型</td></tr>
    <tr><td>Shanghao</td><td>测试生成、运行确认</td><td>接收候选，判断可执行入口和独立 oracle；本轮未执行</td></tr>
    <tr><td>三人</td><td>整合、评估、报告</td><td>冻结评估样本，独立核对，设计公平 baseline</td></tr></tbody></table>
    <p>本地 proposal 的 Division of Work 仍写旧安排（Shanghao 论文、Zhaopeng 仓库/测试生成、Wanting oracle/评估）；与后来的分工不一致。这里按你提供的后续分工解释，尚未修改 Overleaf。</p>
    <h3>有进展的地方</h3><p>论文阶段先独立冻结，再查固定版本代码；每个行为保留来源与调用证据。现在可以向测试负责人交接“哪个入口、什么条件、预期有什么更新、哪里仍不确定”，而不只是交一份 claim 清单。</p>
    <h3>当前不能据此声称的东西</h3><p>206 条不等于 206 个正确命题；12 条局部不一致不等于 12 个独立缺陷；SparTA 是已经看过旧路径的开发案例，不能当作盲测发现率。k=2、合并和多轮复核本身尚不能证明教授要求的研究新意。</p>
    <h3>下一动作与收束标准</h3><p>先人工核对传播这一组候选：读属性的子动作、返回接口差异、终止性保证尤其需要核对。确认后交一张 finding 卡给 Shanghao，而不是继续加长拆解清单。随后用一个实现确实支持行为的正向案例检验过度报错，再在相同资源预算下比较简单提示与当前方法的证据正确性、可交接性和成本。团队最终仍需完成测试与非纯 LLM oracle 的验证。</p>
    <p>你这一阶段的交付线：机制/行为草稿＋逐条证据对照＋合并后的候选 finding＋资源/配置/实验路径未决项。先达到这条线，再扩到其他论文。</p></section>'''
    return code_stage,position
