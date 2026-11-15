"""One explicit final semantic completion with verified cross-mechanism source cache."""
import json,os,re,shutil
from pathlib import Path
from paperprobe.io import read_json,write_json
from paperprobe.semantic_audit import git
from run_sparta_batch import repair_input,stage_call,now

base=Path('runs/sparta-remaining-rollout-v1').resolve()
cache={}
for batch in [Path('runs/sparta-remaining-preflight-v1'),base]:
 for stage in batch.glob('M??/*/input.json'):
  i=read_json(stage)
  sources=[x['result'] for x in i.get('evidence_packet',[])]
  tools=stage.parent/'tools.jsonl'
  if tools.exists():sources += [t['result'] for t in [json.loads(x) for x in tools.read_text().splitlines()] if t['name']=='read_repo']
  for r in sources:
   key=(r['repo'],r['path'],r['start_line'],r['end_line'])
   if key in cache and cache[key]['lines']!=r['lines']:raise ValueError('Source cache conflict')
   cache[key]=r
for mid in ['M18','M20']:
 case=base/mid;state=read_json(case/'state.json')
 if state['state']!='failed':raise ValueError('Expected the recorded rejected final report')
 previous=case/'path-completion-repair';out=case/'source-cache-final'
 repair_input(previous,out);i=read_json(out/'input.json')
 sources=list(cache.values()) if mid=='M18' else []
 if mid=='M20':
  repo=i['repositories']['primary'];p='image/Dockerfile.a100';lines=git(Path(repo['repo']),'show',repo['commit']+':'+p).split('\n')
  sources.append(dict(repo='primary',path=p,commit=repo['commit'],start_line=1,end_line=len(lines),lines='\n'.join(f'{n+1}: {line}' for n,line in enumerate(lines))))
 for r in sources:
  i['evidence_packet'].append(dict(origin='verified source read cache from this rollout; no other mechanism judgments supplied',result=r))
  i['seed_read_spans'].append({k:r[k] for k in ['repo','path','start_line','end_line']})
 i['assessment_contract'].update(stage='single final completion with source cache',max_requests=1,max_output_tokens=10000)
 i['validation_feedback']+='; Every pending row must retain nonempty actual describing the inspected evidence or the fact it remains uninspected; do not invent a result. Reassess candidate against the newly supplied verbatim source cache. Return all IDs and all fields. For M20 Dockerfile.a100 the complete file is supplied now. Pending is a work state, never an accusation.'
 write_json(out/'input.json',i);shutil.copyfile(Path(__file__),out/'completion.snapshot.py')
 write_json(out/'completion-protocol.json',dict(started_at=now(),max_requests=1,new_tools=0,source_cache_records=len(sources),purpose='Close observed schema/reference failures using actual source reads, not mechanical label edits',target_execution='not_run'))
 write_json(out/'prior-state.json',state);state['stages'].append(out.name);state.update(state='source_cache_completion_running',updated_at=now());write_json(case/'state.json',state)
 ok=stage_call(out,base/'runtime')
 if not ok:state.update(state='failed',updated_at=now(),closure_failure='Final bounded model completion rejected')
 else:
  r=read_json(out/'report.json');state.update(state='reviewed',report=str(out.relative_to(base)),updated_at=now())
  state['progress']={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),'pending':sum(c[s]['review_state']=='pending' for c in r['checks']),'counts':{v:sum(c[s]['verdict']==v for c in r['checks']) for v in ['supports','deviates','absent']}} for s in ['local_entry','artifact']}
 write_json(case/'state.json',state);print(mid,json.dumps(state,ensure_ascii=False),flush=True)
