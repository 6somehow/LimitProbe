"""Export strict Wanting inputs and preserve claim-conformance semantics in sidecars."""
import argparse,sys,json,re,shutil,hashlib
from pathlib import Path
from paperprobe.delivery import TEAM,model_call,BIND_PROMPT,exact_evidence
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.conformance_view import three_conclusion_view
from paperprobe.semantic_audit import git

sys.path.insert(0,str(TEAM))
from schema.models import Claim,ScopeItem,EvalPoint,Binding,Limitation
from codeside.verify3b import load_paper_side
from codeside.scope_check import ScopeChecker

MODELS={'claims':Claim,'scope':ScopeItem,'eval_points':EvalPoint,'bindings':Binding}

def sparta_index(work):
 spec=read_json(Path('runs/sparta-remaining-cohort-v1/cohort.json'));rows=[]
 for name in spec['batches']:
  b=Path(name)
  for p in sorted(b.glob('M??/state.json')):
   s=read_json(p)
   if s['state']=='reviewed':rows.append(dict(mechanism=s['mechanism'],stage=str(b/s['report'])))
 rows.append(dict(mechanism='M02',stage=str(Path('runs/sparta-pi-conformance-M02-v2').resolve())))
 write_json(work/'report-index.json',sorted(rows,key=lambda x:x['mechanism']))

def source_cache(work):
 cache={};stages=read_json(work/'report-index.json')
 for entry in stages:
  stage=Path(entry['stage']);i=read_json(stage/'input.json')
  ss=[x['result'] for x in i.get('evidence_packet',[])]
  if (stage/'tools.jsonl').exists():ss += [t['result'] for t in [json.loads(x) for x in (stage/'tools.jsonl').read_text().splitlines()] if t['name']=='read_repo']
  for r in ss:
   key=(r['repo'],r['path'],r['start_line'],r['end_line']);cache[key]=r
 return list(cache.values())

def evidence(row,pages):
 ev=row['evidence']
 # Reviewed span citations are copied exact source text, not reconstituted model quotes.
 if ev and all(e.get('source')=='paper' and e.get('locator','').startswith('PDF p.') for e in ev):
  if not all(e['quote'] in pages[int(re.search(r'PDF p\.(\d+)',e['locator'])[1])-1] for e in ev):raise ValueError('Source span changed')
  return ev
 return exact_evidence(ev,pages)

def build(pid,work,inventory,behaviors,output):
 output.mkdir(parents=True,exist_ok=True)
 art=read_json(next(p for p in TEAM.glob('data/*/artifact.json') if read_json(p)['artifact_id']==pid))
 paper=read_json(work/'paper-input.json');pages=[x['text'] for x in paper['pages']]
 interface=read_json(work/'interface-reviewed.json');source=source_cache(work);pending=[]
 active={k:[] for k in MODELS}
 for field in ['scope','eval_points']:
  model=MODELS[field]
  for n,row in enumerate(interface[field],1):
   ev=evidence(row,pages)
   if not ev:pending.append(dict(field=field,row=row,reason='No exact source evidence'));continue
   body={k:v for k,v in row.items() if k in model.model_fields and k not in ['scope_id','eval_id','artifact_id','schema_version','evidence']}
   item={('scope_id' if field=='scope' else 'eval_id'):f'{pid}-{field}-{n:03d}','artifact_id':pid,**body,'evidence':ev}
   active[field].append(model.model_validate(item).model_dump(mode='json'))
 repairs={r['id']:r for p in work.glob('citation-spans-??.json') for r in read_json(p)['items']}
 bs=[b for p in sorted(behaviors.glob('M??-draft.json')) for b in read_json(p)['behaviors']]
 reports={row['mechanism']:three_conclusion_view(read_json(Path(row['stage'])/'report.json')) for row in read_json(work/'report-index.json')}
 checks={c['id']:c for r in reports.values() for c in r['checks']}
 claimlinks={}
 for b in bs:
  ev=exact_evidence(b['evidence'],pages);repair=repairs.get(b['id'])
  if not ev and repair and repair['status']=='supported':ev=evidence(repair,pages)
  if not ev:pending.append(dict(field='claims',row=b,reason='Citation/whole-statement support unresolved',repair=repair));continue
  claim=dict(claim_id=f'{pid}:{b["id"]}',artifact_id=pid,mechanism=b.get('mechanism_id',b['id'].split('-')[0]),statement=b['behavior'],kind='guarantee' if checks.get(b['id'],{}).get('claim_type')=='guarantee' else 'capability',evidence=ev)
  active['claims'].append(Claim.model_validate(claim).model_dump(mode='json'));claimlinks[b['id']]=claim['claim_id']
 # Parameter binding proposals see only paper scopes and verbatim code reads, never Wanting findings.
 primary=[r for r in source if r['repo']=='primary']
 dedup={}
 for r in primary:
  key=r['path'];lo,hi=r['start_line'],r['end_line']
  existing=dedup.setdefault(key,{})
  for n,line in enumerate(r['lines'].splitlines(),lo):existing[n]=line
 packets=[]
 for path,lines in dedup.items():
  runs=[]
  for n in sorted(lines):
   if not runs or n!=runs[-1][-1]+1 or len(runs[-1])>=120:runs.append([])
   runs[-1].append(n)
  for ids in runs:packets.append(dict(repo='primary',path=path,start_line=min(ids),end_line=max(ids),lines='\n'.join(lines[n] for n in ids)))
 # All cited source is retained in the package; binding prompt input is bounded deterministically.
 packets=packets[:40]
 proposal_path=work/'bindings.raw.json'
 raw=model_call(proposal_path,BIND_PROMPT,dict(scope=active['scope'],mechanisms=read_json(inventory/'merged-mechanisms.json')['mechanisms'],source_reads=packets))
 inactive=[];scopes={x['param']:x for x in active['scope']}
 for n,b in enumerate(raw['bindings'],1):
  reason=None
  if b.get('repo')!='primary':reason='Dependency binding cannot be represented as primary by shared v0.1 schema'
  read=any(p['path']==b['path'] and p['start_line']<=b['line_start']<=b['line_end']<=p['end_line'] for p in packets)
  if not read:reason='Binding cites source outside supplied packet'
  if b['kind']!='mechanism_entry':
   s=scopes.get(b['paper_term'])
   if not b.get('certain') or not s or s['kind']=='free_text':reason='Uncertain or nonnumeric/nonliteral scope mapping is inactive for solver'
   if not re.fullmatch(r'[A-Za-z_]\w*',b['code_symbol']):reason='ScopeChecker supports simple scalar code names only'
  if reason:inactive.append(dict(proposal=b,reason=reason));continue
  item=dict(binding_id=f'{pid}-binding-{n:03d}',artifact_id=pid,paper_term=b['paper_term'],kind=b['kind'],code_symbol=b['code_symbol'],certain=b['certain'],location=dict(file=b['path'],line_start=b['line_start'],line_end=b['line_end']),rationale='LLM-assisted static mapping, independent review pending. '+b['rationale'])
  active['bindings'].append(Binding.model_validate(item).model_dump(mode='json'))
 write_json(output/'scope_interpretations.json',interface)
 write_json(output/'paper_side.json',active);write_json(output/'pending_records.json',pending);write_json(output/'inactive_bindings.json',inactive)
 # Preserve both scopes and the original three conclusions; no enum renaming into Verification.
 conformance=[];findings=[];registry=[];limitations=[]
 for mid,r in reports.items():
  evmap={e['id']:e for e in r['code_evidence']}
  stage=Path(next(x['stage'] for x in read_json(work/'report-index.json') if x['mechanism']==mid));repo_meta=read_json(stage/'input.json')['repositories']
  for e in r['code_evidence']:registry.append(dict(e,evidence_id=f'{mid}:{e["id"]}',mechanism_id=mid,commit=repo_meta[e['repo']]['commit']))
  for c in r['checks']:
   row=dict(c,artifact_id=pid,claim_id=claimlinks.get(c['id']),mechanism_id=mid,scope_definition=r['scope_definition'],evidence_registry_ids={s:[f'{mid}:{uid}' for uid in c[s]['refs']] for s in ['local_entry','artifact']})
   conformance.append(row);v=c['artifact']
   if v['review_state']!='completed' or v['verdict']=='supports':continue
   locs=[dict(file=evmap[uid]['path'],line_start=evmap[uid]['start_line'],line_end=evmap[uid]['end_line']) for uid in v['refs'] if evmap[uid]['repo']=='primary']
   original=next(b for b in bs if b['id']==c['id'])
   lim=dict(limitation_id=f'{pid}-gap-{c["id"]}',artifact_id=pid,origin='paper',level='L2',condition_text=f'Pinned inspected artifact path: {r["scope_definition"]["artifact"]}. Paper precondition: {original.get("precondition","")}',effect_type='other',effect_text=v['discrepancy'],paper_evidence=next((cl['evidence'] for cl in active['claims'] if cl['claim_id']==row['claim_id']),[]),code_evidence=locs,provenance='llm',notes=f'Static discrepancy hypothesis, not a confirmed runtime effect. Original verdict={v["verdict"]}; behavior={c["id"]}; external repo refs stay in code_evidence_registry.json. Equivalence: {v["equivalence"]}; effect_status={v["effect_status"]}')
   if lim['paper_evidence']:limitations.append(Limitation.model_validate(lim).model_dump(mode='json'))
  for f in r['findings']:findings.append(dict(f,artifact_id=pid,mechanism_id=mid,claim_ids=[claimlinks.get(x) for x in f['behavior_ids']],evidence_registry_ids=[f'{mid}:{x}' for x in f['refs']]))
 write_json(output/'conformance.json',conformance);write_json(output/'finding_candidates.json',findings);write_json(output/'limitations.json',limitations);write_json(output/'code_evidence_registry.json',registry)
 write_json(output/'artifact.json',art);write_json(output/'source_reads.json',source)
 # Actual consumer functions and actual Wanting conditions, no LLM or target execution.
 ss,es,bds=load_paper_side(str(output/'paper_side.json'));checker=ScopeChecker(ss,es,bds)
 limpath=TEAM/'results/pipeline'/pid/'limitations.json';integration=[]
 if limpath.exists():
  for rawlim in read_json(limpath):
   lim=Limitation.model_validate(rawlim);sc=checker.check(lim.condition)
   integration.append(dict(limitation_id=lim.limitation_id,scope_status=sc.scope_status,evaluated_in_paper=sc.evaluated_in_paper,reason=sc.reason))
 proof=dict(consumer='actual codeside.verify3b.load_paper_side + ScopeChecker; no API and no target execution',shared_schema_sha256=file_sha256(TEAM/'schema/models.py'),counts={k:len(v) for k,v in active.items()},conformance_rows=len(conformance),completed_artifact=sum(c['artifact']['review_state']=='completed' for c in conformance),pending_artifact=sum(c['artifact']['review_state']=='pending' for c in conformance),pending_paper_records=len(pending),inactive_bindings=len(inactive),wanting_existing_conditions=integration,target_execution='not_run',semantic_ground_truth='pending independent review')
 write_json(output/'validation.json',proof)
 write_json(output/'manifest.json',dict(artifact=art,work=str(work.resolve()),report_index=read_json(work/'report-index.json'),input_hashes=dict(inventory=file_sha256(inventory/'merged-mechanisms.json'),paper_input=file_sha256(work/'paper-input.json')),schema='0.1.0 unchanged; three-conclusion conformance is a separate sidecar, not an overloaded Verification enum',target_execution='not_run'))
 shutil.copyfile(TEAM/'schema/models.py',output/'consumer_schema.snapshot.py')
 (output/'README.md').write_text(f'''# {pid} 论文侧交接包\n\n`paper_side.json` 是 Wanting `codeside.verify3b --paper-side` 的原生输入，四个数组保持共享 schema v0.1.0。`validation.json` 已调用实际消费者的加载函数和范围检查器。\n\n`conformance.json` 保留全部 {len(conformance)} 条行为、两条作用域及原始三结论；未完成项 verdict=null，不是第四类结论。`finding_candidates.json` 按原模型原因归组，父子机制可能重叠，不能直接当作独立 bug 数。`limitations.json` 是附原文的静态差异候选，未赋予已确认运行效果。共享 Verification 的五类语义与正向 claim 判定不同，因此没有机械改标签；整合时通过 claim_id/behavior_id 读取 conformance。\n\n`source_reads.json` 保留实际代码片段；registry 的 repo 别名必须与原始报告的固定 commit 配合。共享 CodeLocation 不支持多仓库，故依赖库引用留在 registry，不伪装成主仓库路径。\n\n`pending_records.json` 留存引用或语义未闭合的论文条目；`inactive_bindings.json` 中的映射不传给求解器。经验设置不变成支持范围；free_text 不强制数值化；集合/张量/len 条件无法表达时 unknown 是明确的接口限制，不是模型发现缺陷。\n\n本模块没有运行目标；团队独立复核和下游测试仍待进行。复跑需 `x-test-2` 授权环境，所有实际 prompts/返回保存在 manifest 指向的 work 目录。\n''')
 print('HANDOFF',pid,json.dumps(proof,ensure_ascii=False),flush=True)
 return proof

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--paper',required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--behaviors',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.paper=='sparta':sparta_index(a.work)
 build(a.paper,a.work,a.inventory,a.behaviors,a.output)
