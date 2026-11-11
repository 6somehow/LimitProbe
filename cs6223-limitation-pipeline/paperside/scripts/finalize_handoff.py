"""Finalize a portable delivery without changing any model conformance verdict."""
import argparse,json,re,sys,shutil,zipfile
from pathlib import Path
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.delivery import TEAM
sys.path.insert(0,str(TEAM))
from schema.models import Claim,ScopeItem,EvalPoint,Binding,Limitation
from codeside.verify3b import load_paper_side
from codeside.scope_check import ScopeChecker

def numeric_scope(s):
 return (s.get('explicit') is True) and ((s['kind']=='interval' and (s.get('lower') is not None or s.get('upper') is not None)) or (s['kind']=='set' and bool(s.get('values')) and all(type(v) in [int,float] for v in s['values'])))

def finish(folder):
 manifest=read_json(folder/'manifest.json');data=read_json(folder/'paper_side.json')
 adjustments=read_json(folder/'review-adjustments.json') if (folder/'review-adjustments.json').exists() else {}
 pending=read_json(folder/'pending_records.json')
 for action in adjustments.get('scope_replacements',[]):
  old=next((r for r in data['scope'] if r['scope_id']==action['original_id']),None)
  if old is not None and action.get('hold_original') and not any(r.get('review_action_id')==action['original_id'] for r in pending):
   pending.append(dict(field='scope',row=old,review_action_id=action['original_id'],reason=action['reason']))
  ids={r['scope_id'] for r in action['records']}|{action['original_id']}
  data['scope']=[r for r in data['scope'] if r['scope_id'] not in ids]+action['records']
 for action in adjustments.get('evaluation_replacements',[]):
  old=next((r for r in data['eval_points'] if r['eval_id']==action['original_id']),None)
  if old is not None and action.get('hold_original') and not any(r.get('review_action_id')==action['original_id'] for r in pending):
   pending.append(dict(field='eval_points',row=old,review_action_id=action['original_id'],reason=action['reason']))
  ids={r['eval_id'] for r in action['records']}|{action['original_id']}
  data['eval_points']=[r for r in data['eval_points'] if r['eval_id'] not in ids]+action['records']
 write_json(folder/'pending_records.json',pending)
 scopes={s['param']:s for s in data['scope']};inactive=read_json(folder/'inactive_bindings.json')
 draft=folder/'paper_side.pre-final.json'
 if not draft.exists():write_json(draft,data)
 data['bindings']=[b for b in data['bindings'] if b['kind']!='mechanism_entry']
 selected=[]
 for b in data['bindings']:
  if b['certain'] and b['paper_term'] in scopes and numeric_scope(scopes[b['paper_term']]) and re.fullmatch(r'[A-Za-z_]\w*',b['code_symbol']):selected.append(b)
  else:inactive.append(dict(proposal=b,reason='Actual ScopeChecker ignores nonnumeric/free-text domains; do not activate an unconstrained or uncertain binding'))
 navigation=[];repositories={};source_proof=[]
 for item in manifest['report_index']:
  mid=item['mechanism'];stage=Path(item['stage']);i=read_json(stage/'input.json');r=read_json(stage/'report.json');scope=r['scope_definition']['local_entry'];repo=i['repositories']['primary']
  for alias,rr in i['repositories'].items():
   prev=repositories.get(alias)
   if prev and prev['commit']!=rr['commit']:raise ValueError('Mixed repository pins in delivery')
   repositories[alias]=dict(commit=rr['commit'],local_repo=rr['repo'])
  defs=[d for d in repo.get('definitions',{}).values() if d['path'] in scope and (d['name'] in scope or d['name'].split('.')[-1] in scope)]
  defs=sorted(defs,key=lambda d:scope.find(d['name']) if d['name'] in scope else scope.find(d['name'].split('.')[-1]))[:2]
  for n,d in enumerate(defs,1):
   term=i['mechanism']['name'];b=Binding.model_validate(dict(binding_id=f'{manifest["artifact"]["artifact_id"]}-{mid}-entry-{n}',artifact_id=manifest['artifact']['artifact_id'],paper_term=term,kind='mechanism_entry',code_symbol=f'{d["path"]}::{d["name"]}',location=dict(file=d['path'],line_start=d['start'],line_end=d['end']),certain=False,rationale='Navigation selected by the mechanism Pi report local_entry; definition mechanically indexed at the pinned commit. This does not assert implementation support or a runtime call trace.')).model_dump(mode='json')
   navigation.append(b);source_proof.append(dict(binding_id=b['binding_id'],report=str(stage/'report.json'),scope_definition=scope,commit=repo['commit']))
 data['bindings']=selected+navigation
 for k,model in [('claims',Claim),('scope',ScopeItem),('eval_points',EvalPoint),('bindings',Binding)]:
  for x in data[k]:model.model_validate(x)
 for x in read_json(folder/'limitations.json'):Limitation.model_validate(x)
 write_json(folder/'paper_side.json',data);write_json(folder/'inactive_bindings.json',inactive);write_json(folder/'binding_provenance.json',source_proof);write_json(folder/'repositories.json',repositories)
 ss,es,bs=load_paper_side(str(folder/'paper_side.json'));checker=ScopeChecker(ss,es,bs)
 aid=manifest['artifact']['artifact_id'];probe=[]
 for row in read_json(TEAM/'results/pipeline'/aid/'limitations.json'):
  lim=Limitation.model_validate(row);v=checker.check(lim.condition);probe.append(dict(limitation_id=lim.limitation_id,scope_status=v.scope_status,evaluated_in_paper=v.evaluated_in_paper,reason=v.reason))
 validation=read_json(folder/'validation.json');validation.update(pending_paper_records=len(pending),pending_claim_records=sum(r.get('field')=='claims' for r in pending),held_evaluation_records=sum(r.get('field')=='eval_points' for r in pending),held_scope_records=sum(r.get('field')=='scope' for r in pending),counts={k:len(v) for k,v in data.items()},active_solver_bindings=len(selected),navigation_bindings=len(navigation),inactive_bindings=len(inactive),wanting_existing_conditions=probe,solver_guard='Only author-explicit numeric literal sets/bounded intervals and certain scalar bindings activated. Evaluation-only sets cannot exclude other inputs; actual consumer otherwise treats free_text as unconstrained.')
 write_json(folder/'validation.json',validation)
 evidence=folder/'evidence';evidence.mkdir(exist_ok=True);pdf=TEAM/'third_party/papers'/f'{aid}.pdf';shutil.copyfile(pdf,evidence/'paper.pdf')
 work=Path(manifest['work']);calls=evidence/'interface-calls';calls.mkdir(exist_ok=True)
 for p in work.glob('*.json'):
  if 'raw' in p.name or 'citation' in p.name:shutil.copyfile(p,calls/p.name)
 if aid=='sparta':shutil.copyfile(Path('sparta-independent-k2.html'),evidence/'full-audit.html')
 (folder/'RUN_WITH_WANTING.md').write_text(f'''# 直接接入 Wanting\n\n此目录的 paper_side.json 原样传给 codeside.verify3b 的 --paper-side。不要把它替换成完整 conformance.json；后者是保留三类判断的扩展证据。\n\n```bash\n# 在 Wanting 仓库内，使用已装 pydantic / z3 / 文档检索依赖的 Python\npython -m codeside.verify3b \\\n  --limitations results/pipeline/{aid}/limitations.json \\\n  --artifact data/{'pilot_flexprefill' if aid=='flexprefill' else aid}/artifact.json \\\n  --pdf /绝对路径/交接包/{aid}/evidence/paper.pdf \\\n  --repo /固定到artifact.json中commit的仓库路径 \\\n  --paper-side /绝对路径/交接包/{aid}/paper_side.json \\\n  --model x-test-2 --repeats 3 --workers 3 \\\n  --out /新的结果目录/{aid}-3b.json\n```\n\n这条命令会调用模型。当前 validation.json 的集成检查只加载实际消费者并运行其范围检查器，不冒充已经重新运行全文档核查。源码、图表和已完成语义核验均不构成已确认运行缺陷。\n\n原始证据：evidence/paper.pdf、scope_interpretations.json、source_reads.json、code_evidence_registry.json；每条依赖引用有独立 repo/commit，不能当作主仓库路径。原始论文页与 prompt 的引用路径见 manifest 和实际调用记录。\n''')
 write_json(folder/'bundle-index.json',dict(artifact_id=aid,files={str(p.relative_to(folder)):file_sha256(p) for p in folder.rglob('*') if p.is_file() and p.name!='bundle-index.json'}))
 archive=folder.parent/(aid+'-handoff.zip')
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in folder.rglob('*'):
   if p.is_file():z.write(p,str(Path(aid)/p.relative_to(folder)))
 print('DELIVERY_FINAL',aid,validation['counts'],'solver',len(selected),'navigation',len(navigation),'zip',archive.stat().st_size,flush=True)
 return validation

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args();finish(a.folder)
