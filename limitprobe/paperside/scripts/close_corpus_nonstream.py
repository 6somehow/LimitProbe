"""One transport intervention per failed mechanism: Pi evidence, non-stream semantic completion."""
from pathlib import Path
import os,json,base64,subprocess,shutil,sys
from urllib.request import Request,urlopen
from datetime import datetime,timezone
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.multimodal_decomposition import make_content,parse_response
BASE=Path('runs/team-complete-v1/minference').resolve();RUNTIME=BASE/'runtime'
def now():return datetime.now(timezone.utc).isoformat()
system=subprocess.check_output(['node','--input-type=module','-e',"import {CONFORMANCE_REVIEW_SYSTEM} from './conformance.mjs';process.stdout.write(CONFORMANCE_REVIEW_SYSTEM)"],cwd=RUNTIME,text=True)
for mid in ['M05','M09']:
 case=BASE/'code'/mid;state=read_json(case/'state.json');out=case/'nonstream-final-v1'
 if out.exists():raise ValueError('One new request only; prior attempt cannot be overwritten')
 if state['state']=='reviewed':continue
 stages=sorted([p for p in case.rglob('input.json') if 'agent-config' not in str(p)],key=lambda p:p.stat().st_mtime)
 prior=stages[-1].parent;i=read_json(prior/'input.json');sources={};candidate=None;partial=''
 for p in stages:
  inp=read_json(p)
  rs=[x['result'] for x in inp.get('evidence_packet',[])]
  tf=p.parent/'tools.jsonl'
  if tf.exists():rs += [t['result'] for t in [json.loads(l) for l in tf.read_text().splitlines()] if t['name']=='read_repo']
  for r in rs:sources[(r['repo'],r['path'],r['start_line'],r['end_line'])]=r
  if (p.parent/'report.json').exists():candidate=read_json(p.parent/'report.json')
  if (p.parent/'final-response.txt').exists():partial=(p.parent/'final-response.txt').read_text()
 i['evidence_packet']=[dict(origin='Actual retained Pi reads before non-stream transport intervention',result=r) for r in sources.values()];i['seed_read_spans']=[{k:r[k] for k in ['repo','path','start_line','end_line']} for r in sources.values()]
 i.update(candidate_report=candidate,semantic_review=True,finalize_only=True)
 for k in ['validation_feedback','previous_incomplete_response']:i.pop(k,None)
 out.mkdir();write_json(out/'input.json',i);write_json(out/'prior-state.json',state);shutil.copyfile(__file__,out/'completion.snapshot.py')
 protocol=dict(framework='Pi-source-evidence semantic review, explicit Python non-stream transport fallback',started_at=now(),max_requests=1,timeout_seconds=240,max_output_tokens=12000,new_tools=0,target_execution='not_run',question='Can a bounded non-stream completion avoid previously observed stream interruptions? Not an accuracy comparison.',source='Original Pi exploration and frozen paper behaviors; no mechanical verdict edits',prior_stage=str(prior))
 write_json(out/'protocol.json',protocol);write_json(out/'system-prompt.json',dict(prompt=system))
 data=dict(mechanism=i['mechanism'],behaviors=i['behaviors'],paper_pages=[p for p in i['pages'] if p['page'] in i['mechanism']['pages']],repositories={k:{'commit':r['commit']} for k,r in i['repositories'].items()},source_evidence=i['evidence_packet'],candidate_report=candidate,prior_partial_response=partial,
  task='Return complete revised conformance JSON for all frozen IDs using only these verified sources. Every completed actual/equivalence field must be nonempty. If a property remains unassessed use pending/null with a precise reason and nonempty actual describing inspected facts. No tools, no target run. No accepted draft may exist; rebuild from the supplied evidence rather than inventing a candidate.')
 imgs=[]
 for im in i['images']:
  if im['page'] not in i['mechanism']['pages']:continue
  b=Path(im['path']).read_bytes()
  if file_sha256(Path(im['path']))!=im['sha256']:raise ValueError('Image changed')
  imgs.append(dict(im,data_url='data:image/jpeg;base64,'+base64.b64encode(b).decode()))
 payload=dict(model='x-test-2',temperature=0,reasoning_effort='none',stream=False,max_tokens=12000,messages=[dict(role='system',content=system),dict(role='user',content=make_content(data,imgs))])
 write_json(out/'initial-user-input.json',data);write_json(out/'final.raw.request.json',dict(prompt=system,data=data,settings={k:v for k,v in payload.items() if k!='messages'},image_pages=[{k:v for k,v in im.items() if k!='data_url'} for im in imgs]))
 write_json(out/'read-spans.json',i['seed_read_spans']);state['stages'].append(out.name);state.update(state='nonstream_semantic_review_running',updated_at=now());write_json(case/'state.json',state)
 try:
  req=Request('https://soclaas-api.comp.nus.edu.sg/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+os.environ['SOCLAAS_API_KEY'],'Content-Type':'application/json'})
  with urlopen(req,timeout=240) as response:raw=json.load(response)
  write_json(out/'final.raw.json',raw);r=parse_response(raw);write_json(out/'conformance-report.raw.json',r);(out/'final-response.txt').write_text(raw['choices'][0]['message']['content'])
  validator="import fs from 'node:fs';import {validateConformance} from './conformance.mjs';const p=process.argv[1],j=n=>JSON.parse(fs.readFileSync(p+'/'+n));validateConformance(j('conformance-report.raw.json'),j('input.json').behaviors,j('read-spans.json'),j('input.json').pages);"
  subprocess.run(['node','--input-type=module','-e',validator,str(out)],cwd=RUNTIME,check=True,capture_output=True,text=True)
  write_json(out/'report.json',dict(r,semantic_review='pending independent review',target_execution='not_run'))
  state.update(state='reviewed',report=str(out.relative_to(BASE/'code')),updated_at=now(),progress={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),'pending':sum(c[s]['review_state']=='pending' for c in r['checks'])} for s in ['local_entry','artifact']})
  write_json(out/'summary.json',dict(requests=1,tool_calls=0,total_tokens=raw.get('usage',{}).get('total_tokens',0),usage_included_in_raw_response=True,report_complete=True,target_execution='not_run'))
 except Exception as e:
  write_json(out/'summary.json',dict(requests=1,tool_calls=0,error=str(e)[:1200],report_complete=False,failed_request_usage='unknown if provider did not return usage',remote_terminal_state='unknown',target_execution='not_run'));state.update(state='failed',nonstream_failure=str(e)[:1200],updated_at=now())
 write_json(case/'state.json',state);print(mid,state['state'],flush=True)
entries=[]
for p in sorted((BASE/'code').glob('M??/state.json')):
 s=read_json(p)
 if s['state']=='reviewed':entries.append(dict(mechanism=s['mechanism'],stage=str(BASE/'code'/s['report'])))
write_json(BASE/'report-index.json',entries)
