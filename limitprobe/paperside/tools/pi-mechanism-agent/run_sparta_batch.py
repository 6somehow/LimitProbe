"""Bounded rollout of the 19 remaining frozen SparTA mechanisms using real Pi sessions."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from copy import deepcopy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from paperprobe.io import read_json,write_json,file_sha256
from prepare_mechanism import build_context,prepare
from run_conformance import prepare_review

LOCK=threading.Lock()

def now():return datetime.now(timezone.utc).isoformat()

def read_tools(stage):
    return [json.loads(s) for s in (stage/'tools.jsonl').read_text().splitlines()] if (stage/'tools.jsonl').exists() else []

def repair_input(source,destination):
    i=read_json(source/'input.json')
    for t in read_tools(source):
        if t['name']=='read_repo':
            r=t['result'];i['evidence_packet'].append(dict(origin='actual read before structural repair',result=r))
            i['seed_read_spans'].append({k:r[k] for k in ['repo','path','start_line','end_line']})
    summary=read_json(source/'summary.json') if (source/'summary.json').exists() else {}
    i.update(finalize_only=True,previous_incomplete_response=(source/'final-response.txt').read_text() if (source/'final-response.txt').exists() else '',
             validation_feedback=summary.get('validation_error',summary.get('error','No complete report produced')))
    if (source/'conformance-report.raw.json').exists():i['candidate_report']=read_json(source/'conformance-report.raw.json')
    i['assessment_contract'].update(stage='bounded structural completion',max_requests=1)
    i['baseline_usage']={'total_tokens':90000}
    destination.mkdir();write_json(destination/'input.json',i)


def stage_call(stage,runtime):
    with (stage/'process.log').open('w') as log:
        try:result=subprocess.run(['node',str(runtime/'run-adjudication.mjs'),str(stage)],stdout=log,stderr=subprocess.STDOUT,timeout=920)
        except subprocess.TimeoutExpired:
            write_json(stage/'process-failure.json',dict(error='local deadline reached; server consumption unknown',time=now()));return False
    return result.returncode==0 and (stage/'report.json').exists()


def run_case(batch,mid,context):
    folder=batch/mid;folder.mkdir();stages=[]
    def save(state,**kw):
        with LOCK:write_json(folder/'state.json',dict(mechanism=mid,state=state,stages=stages,updated_at=now(),**kw))
    save('preparing')
    draft=folder/'draft';prepare(draft,mid,context);stages.append('draft');save('draft_running')
    ok=stage_call(draft,batch/'runtime')
    if not ok:
        repaired=folder/'draft-repair';repair_input(draft,repaired);stages.append('draft-repair');save('draft_repair_running')
        ok=stage_call(repaired,batch/'runtime');draft=repaired
    if not ok:save('failed',reason='No structurally accepted first-stage report');return mid,'failed'
    review=folder/'review';prepare_review(draft,review)
    # Keep actual variable-size report allowance and pin this new semantic contract.
    i=read_json(review/'input.json');i['assessment_contract']['stage']='whole-mechanism semantic consistency review';write_json(review/'input.json',i)
    stages.append('review');save('review_running')
    ok=stage_call(review,batch/'runtime')
    if not ok:
        repaired=folder/'review-repair';repair_input(review,repaired);stages.append('review-repair');save('review_repair_running')
        ok=stage_call(repaired,batch/'runtime');review=repaired
    if not ok:save('failed',reason='No structurally accepted semantic review');return mid,'failed'
    report=read_json(review/'report.json')
    progress={s:{'completed':sum(c[s]['review_state']=='completed' for c in report['checks']),
                 'pending':sum(c[s]['review_state']=='pending' for c in report['checks']),
                 'counts':{v:sum(c[s]['verdict']==v for c in report['checks']) for v in ['supports','deviates','absent']}}
              for s in ['local_entry','artifact']}
    save('reviewed',report=str(review.relative_to(batch)),progress=progress,
         semantic_ground_truth='pending independent human review',target_execution='not_run')
    return mid,'reviewed'


def launch(batch,ids,workers):
    if not os.environ.get('SOCLAAS_API_KEY'):raise ValueError('Authorized API environment required')
    if batch.exists():raise ValueError('Fresh batch directory required')
    batch.mkdir(parents=True);runtime=batch/'runtime';runtime.mkdir()
    src=Path(__file__).parent.resolve()
    for name in ['run-adjudication.mjs','conformance.mjs','judgment.mjs','prepare_judgment.py','prepare_conformance.py','prepare_mechanism.py','run_conformance.py','run_sparta_batch.py']:
        shutil.copyfile(src/name,runtime/name)
    (runtime/'node_modules').symlink_to(src/'node_modules',target_is_directory=True)
    context=build_context();write_json(batch/'repository-context.json',context)
    inventory=read_json(Path('runs/sparta-independent-k2-v2/merged-mechanisms.json'))['mechanisms']
    selected=[m['id'] for m in inventory if m['id'] in ids]
    protocol=dict(started_at=now(),mechanisms=selected,reused_M02='runs/sparta-pi-conformance-M02-v2',workers=workers,
       mechanism_unit='one Pi exploration session per frozen mechanism; per-claim accounting; one model semantic review',
       code_scope='primary library/entry and mechanism-aligned artifact scripts, native kernels and declared dependencies; not M02 defaults',
       verdicts=['supports','deviates','absent'],pending='workflow state with null verdict, excluded from conclusions',
       max_nominal_requests_per_mechanism=8,max_repair_requests_per_mechanism=2,max_new_tools_per_mechanism=24,
       soft_token_target_per_mechanism=dict(draft=170000,review=90000,repair_reserve=180000),
       retries=0,repair_policy='at most one new completion request per failed stage; preserve original outputs; no mechanical verdict edits',
       target_execution='not_run',comparison='development rollout, not controlled accuracy or novelty evidence',
       runtime_sha256={p.name:file_sha256(p) for p in runtime.iterdir() if p.is_file()},
       repositories={k:{'commit':v['commit'],'repo':v['repo']} for k,v in context['repositories'].items()})
    write_json(batch/'protocol.json',protocol)
    print('BATCH',str(batch),'mechanisms',selected,'workers',workers,flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(run_case,batch,mid,context):mid for mid in selected}
        for future in as_completed(futures):
            mid=futures[future]
            try:_,status=future.result()
            except Exception as e:
                write_json(batch/mid/'state.json',dict(mechanism=mid,state='failed',error=str(e),updated_at=now()));status='failed'
            print('CASE',mid,status,now(),flush=True)
    write_json(batch/'completed.json',dict(finished_at=now(),states={mid:read_json(batch/mid/'state.json')['state'] for mid in selected}))
    print('BATCH_FINISHED',now(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mechanisms',nargs='*');p.add_argument('--workers',type=int,default=2)
    a=p.parse_args();all_ids=[f'M{i:02d}' for i in range(1,21) if i!=2]
    launch(a.output.resolve(),a.mechanisms or all_ids,min(max(a.workers,1),2))
