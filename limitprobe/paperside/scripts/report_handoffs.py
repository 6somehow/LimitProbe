"""Offline overview and complete per-paper handoff/audit pages, including actual model calls."""
from pathlib import Path
from html import escape as esc
import json,base64
from collections import Counter
from paperprobe.io import read_json,write_json

ROOT=Path.cwd();BASE=ROOT/'runs/team-complete-v1';OUT=ROOT/'handoffs/paper-side-v1'
CSS='''*{box-sizing:border-box}body{margin:0;background:#f8f5ed;color:#192f45;font:16px/1.65 system-ui,sans-serif}header{background:#142b44;color:#fff;padding:28px 5vw}main{max-width:1300px;margin:auto;padding:24px}nav{background:#203b57;padding:12px 5vw;position:sticky;top:0;z-index:5;display:flex;gap:18px;flex-wrap:wrap}nav a{color:white}a{color:#265b80}h1{font-size:28px}h2{margin-top:34px}.card,details{background:#fffdf7;border:1px solid #ddd8cd;border-radius:8px;padding:16px;margin:12px 0;overflow-wrap:anywhere}summary{cursor:pointer;font-weight:650}table{border-collapse:collapse;width:100%}td,th{text-align:left;vertical-align:top;border:1px solid #ded9cf;padding:12px}th{background:#e6edf2}pre{background:#edf0f3;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;max-height:650px;overflow:auto;font-size:12px}blockquote{border-left:3px solid #bea65c;background:#f2eddf;padding:12px;margin:12px 0}.notice{border-left:4px solid #ac8140;background:#f0e9d7;padding:15px}.stats{display:flex;flex-wrap:wrap;gap:25px}.stats b{display:block;font-size:30px}.muted{color:#56667a}button{padding:6px 10px;border:1px solid #a7b2c0;border-radius:4px;background:#eaf0f5;cursor:pointer}dialog{max-width:95vw;width:950px;height:94vh;border:0}dialog img{width:100%}section[id]{scroll-margin-top:140px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:750px){.cols{grid-template-columns:1fr}main{padding:14px}nav{max-height:130px;overflow:auto}td,th{padding:8px}}'''
LABEL={'supports':'支持','deviates':'不符','absent':'未实现'}
def pretty(x):return esc(json.dumps(x,ensure_ascii=False,indent=2))
def document(title,body,nav=''):
 return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+CSS+'</style><header><h1>'+esc(title)+'</h1><p>CS6223 · 论文侧语义拆解、静态源码核验与共享接口交接</p></header><nav>'+nav+'</nav><main>'+body+'</main></html>'

def detail(pid,folder):
 data=read_json(folder/'paper_side.json');v=read_json(folder/'validation.json');manifest=read_json(folder/'manifest.json');work=Path(manifest['work']);rows=read_json(folder/'conformance.json');registry={e['evidence_id']:e for e in read_json(folder/'code_evidence_registry.json')};sources=read_json(folder/'source_reads.json');claims={x['claim_id']:x for x in data['claims']}
 def snippet(uid):
  e=registry[uid];lines={}
  for s in sources:
   if s['repo']==e['repo'] and s['path']==e['path']:lines.update({s['start_line']+n:l for n,l in enumerate(s['lines'].splitlines())})
  text='\n'.join(lines.get(n,'[未留档]') for n in range(e['start_line'],e['end_line']+1))
  if '[未留档]' in text:raise ValueError('Missing cited source in delivery')
  return f'<details><summary>{esc(e["repo"])} · {esc(e["path"])}:{e["start_line"]}–{e["end_line"]} · {e["commit"][:10]}</summary><pre>{esc(text)}</pre></details>'
 counts=Counter(c['artifact']['verdict'] for c in rows if c['artifact']['review_state']=='completed');body=f'<section><h2>交接与核验概况</h2><div class="stats"><div><b>{len(rows)}</b>冻结行为</div><div><b>{v["completed_artifact"]}</b>已给出 artifact 判断</div><div><b>{v["pending_artifact"]}</b>核验待办</div></div><p>本轮模型判断：支持 {counts["supports"]}／不符 {counts["deviates"]}／未实现 {counts["absent"]}。没有运行目标，不作为已确认 bug 数。</p><p><a href="paper_side.json">Wanting 原生输入</a> · <a href="validation.json">实际消费者检查</a> · <a href="../{pid}-handoff.zip">交接 ZIP</a> · <a href="RUN_WITH_WANTING.md">接入命令</a> · <a href="evidence/paper.pdf">原论文 PDF</a></p><p class="notice">导航映射不等于标量参数映射。仅有明确数值域且语义可靠的标量映射才传给求解器。其他映射留在 inactive_bindings.json。三结论保留于 conformance.json，没有机械重命名成共享 Verification 的五类。</p><details><summary>接口与检查完整结果</summary><pre>'+pretty(v)+'</pre></details></section>'
 body+='<section id="interface"><h2>共享接口：claim／scope／eval_points／binding</h2>'+''.join(f'<details><summary>{k} · {len(values)} 条</summary><pre>{pretty(values)}</pre></details>' for k,values in data.items())+'<details><summary>待完善的论文条目与不启用的映射</summary><pre>'+pretty(dict(pending=read_json(folder/'pending_records.json'),inactive=read_json(folder/'inactive_bindings.json')))+'</pre></details></section>'
 for mid in sorted({c['mechanism_id'] for c in rows}):
  group=[c for c in rows if c['mechanism_id']==mid];scope=group[0]['scope_definition'];items=[]
  for c in group:
   ev=claims.get(c['claim_id'],{}).get('evidence',[])
   paper=''.join(f'<blockquote>{esc(e["locator"])}<br>{esc(e["quote"])}</blockquote>' for e in ev) or '<p>此声明引用尚待完善；保留原始核验记录。</p>'
   parts=[]
   for s in ['local_entry','artifact']:
    x=c[s];text=(LABEL[x['verdict']] if x['review_state']=='completed' else '核验待办，无判定')
    parts.append(f'<div class="card"><b>{s} · {text}</b><p>{esc(x["actual"])}</p><p>{esc(x["discrepancy"] or x["pending_reason"])}</p><p>等价性：{esc(x["equivalence"])}</p><small>效果状态：{esc(x["effect_status"])}</small>'+''.join(snippet(uid) for uid in c['evidence_registry_ids'][s])+'</div>')
   items.append(f'<article><h3>{esc(c["id"])} · {esc(c["requirement"])}</h3>{paper}<div class="cols">'+''.join(parts)+'</div></article>')
  body+=f'<details id="{mid}"><summary>{mid} · {len(group)} 条行为的原文、源码与判断</summary><pre>{pretty(scope)}</pre>'+''.join(items)+'</details>'
 archives={}
 for p in sorted(work.rglob('*.request.json')):
  response=p.with_name(p.name.replace('.request.json','.json'));archives[str(p.relative_to(work))]=dict(request=read_json(p),response=read_json(response) if response.exists() else {'state':'no completed response retained'})
 for stage in sorted((work/'code').glob('M??/*')) if (work/'code').exists() else []:
  if not (stage/'protocol.json').exists():continue
  archives[str(stage.relative_to(work))]=dict(protocol=read_json(stage/'protocol.json'),summary=read_json(stage/'summary.json') if (stage/'summary.json').exists() else {},system=read_json(stage/'system-prompt.json'),input=read_json(stage/'initial-user-input.json'),requests=[read_json(p) for p in sorted(stage.glob('request-*.json'))],raw=(stage/'final-response.txt').read_text() if (stage/'final-response.txt').exists() else '',tools=[json.loads(x) for x in (stage/'tools.jsonl').read_text().splitlines()] if (stage/'tools.jsonl').exists() else [])
 body+='<section id="actual"><h2>本轮实际 prompts、请求与返回</h2><p>原始调用完整留存；图像字节用页码和哈希引用，原始 PDF 在包内。模型失败和被拒收的阶段同样保留。</p>'+''.join(f'<details data-archive="{esc(k)}"><summary>{esc(k)}</summary><pre></pre></details>' for k in archives)+'</section>'
 if pid=='sparta':body+='<p><a href="evidence/full-audit.html">SparTA 原完整看板：两次发现、拆解及全部 Pi 历史调用</a></p>'
 payload=json.dumps(archives,ensure_ascii=False).replace('<','\\u003c')
 body+='<script type="application/json" id="archives">'+payload+'</script><script>const archives=JSON.parse(document.querySelector("#archives").textContent);document.addEventListener("toggle",e=>{const d=e.target;if(d.open&&d.dataset.archive&&!d.dataset.loaded){d.querySelector("pre").textContent=JSON.stringify(archives[d.dataset.archive],null,2);d.dataset.loaded="1"}},true)</script>'
 (folder/'audit.html').write_text(document(pid+' · 论文侧交接与完整证据',body,'<a href="../../../paper-side-handoff.html">五篇总览</a><a href="#interface">共享接口</a><a href="#actual">实际调用</a>'))

def main():
 table=[];summary={}
 for pid in ['sparta','flexprefill','minference','infinigen','nnsmith']:
  folder=OUT/pid;work=BASE/pid;state=read_json(work/'state.json') if (work/'state.json').exists() else {'state':'not_started'}
  if (folder/'validation.json').exists():
   v=read_json(folder/'validation.json');detail(pid,folder);summary[pid]=v
   table.append(f'<tr><td>{pid}</td><td>{esc(state["state"] if pid!="sparta" else "handoff_ready")}</td><td>{v["conformance_rows"]}</td><td>{v["completed_artifact"]}／{v["pending_artifact"]}</td><td>{v["counts"]["claims"]}／{v["counts"]["scope"]}／{v["counts"]["eval_points"]}／{v["counts"]["bindings"]}</td><td><a href="handoffs/paper-side-v1/{pid}/audit.html">完整证据与接口</a> · <a href="handoffs/paper-side-v1/{pid}-handoff.zip">ZIP</a></td></tr>')
  else:table.append(f'<tr><td>{pid}</td><td>{esc(state["state"])}</td><td colspan="4">尚未形成可交付包，不记为完成</td></tr>')
 body='<h2>五篇交付状态</h2><p>沿用论文侧独立拆解与机制级 Pi 核验；主仓库代码只按固定 commit 静态读取。没有运行目标。完成、待核验与失败分别记录。</p><div style="overflow:auto"><table><tr><th>论文</th><th>状态</th><th>行为数</th><th>已判定／待办</th><th>claim／scope／实验点／映射</th><th>交接</th></tr>'+''.join(table)+'</table></div><p class="notice">数量是行为与候选数，不是独立缺陷数。父子机制和论文间重复不算新的缺陷。未知范围不强制数值化，模型判断仍待团队独立审阅。</p><h2>交给 Wanting 的文件</h2><ul><li>paper_side.json：共享 schema v0.1.0，直接给 --paper-side。</li><li>scope_interpretations.json：范围条件、单位、评估域与解释。</li><li>conformance.json：完整三结论与待办，关联 claim_id，不混用五类 Verification。</li><li>limitations.json／finding_candidates.json：静态差异候选与原模型归组。</li><li>source_reads.json／code_evidence_registry.json：源码、仓库别名和固定 commit。</li><li>validation.json／RUN_WITH_WANTING.md：实际消费者检查结果与接入方法。</li></ul>'
 (ROOT/'paper-side-handoff.html').write_text(document('CS6223 · 论文侧交接总览',body,'<a href="sparta-independent-k2.html">SparTA 原看板</a>'))
 write_json(OUT/'summary.json',summary);print('HANDOFF_REPORT',len(summary),'packages')
if __name__=='__main__':main()
