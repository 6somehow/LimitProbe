"""One inspected transport recovery, globally bounded to one paper/two sessions."""
import argparse, threading, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from recover_corpus_failed import augment
from run_complete_corpus import BASE, now, supplement_unread
from run_sparta_batch import stage_call,read_tools
from run_conformance import prepare_review
from paperprobe.io import read_json,write_json

STOP=threading.Event()
TRANSPORT=('ETIMEDOUT','ENOTFOUND','EPIPE','Timeout','timed out','Connection error','connection failed')


def transport_error(stage):
    p=stage/'summary.json'
    if not p.exists():return ''
    e=read_json(p).get('error','')
    return e if any(x in e for x in TRANSPORT) else ''


def recover(folder):
    if STOP.is_set():return
    old=read_json(folder/'state.json')
    if old['state']!='failed':return
    src=folder/old['stages'][-1]
    if not transport_error(src):print('NOT_TRANSPORT',folder,flush=True);return
    root=folder/'transport-recovery-v1'
    if root.exists():print('TRANSPORT_ALREADY_ATTEMPTED',folder,flush=True);return
    root.mkdir();write_json(root/'original-state.json',old)
    work=folder.parent.parent;stages=list(old['stages'])
    def state(s,**kw):write_json(folder/'state.json',dict(mechanism=folder.name,state=s,stages=stages,updated_at=now(),recovery='transport-recovery-v1',**kw))
    def call(stage):
        stages.append(str(stage.relative_to(folder)));state('transport_recovery_running')
        ok=stage_call(stage,work/'runtime')
        if not ok and transport_error(stage):STOP.set();raise ValueError('Transport failed again; circuit breaker prevents new queued mechanism calls')
        return ok
    try:
        # A zero-tool failed draft never inspected implementation. Restart its
        # full source exploration once; otherwise retain actual prior reads.
        inspected=any(t['name']=='read_repo' for t in read_tools(folder/'draft'))
        accepted_draft=next((s for s in [folder/'draft',folder/'draft-repair'] if (s/'report.json').exists()),None)
        if not inspected and accepted_draft is None:
            draft=root/'draft';draft.mkdir();i=read_json(folder/'draft/input.json')
            i['assessment_contract']['transport_recovery']='One restart after DNS/stream failure; original request consumption unknown'
            write_json(draft/'input.json',i)
        else:
            draft=root/'completion';supplement_unread(src,draft);augment(draft)
        ok=call(draft)
        if not ok:
            repair=root/'completion-repair';supplement_unread(draft,repair);augment(repair)
            if not call(repair):raise ValueError('Transport restart report structurally rejected after one repair')
            draft=repair
        # A replacement of the interrupted semantic review already uses the
        # semantic review prompt and candidate, so it is the final review.
        if read_json(draft/'input.json').get('semantic_review'):
            review=draft
        else:
            review=root/'review';prepare_review(draft,review)
            if not call(review):
                repair=root/'review-repair';supplement_unread(review,repair);augment(repair)
                if not call(repair):raise ValueError('Transport restart semantic review rejected after one repair')
                review=repair
        r=read_json(review/'report.json');state('reviewed',report=str(review.relative_to(work/'code')),progress={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),'pending':sum(c[s]['review_state']=='pending' for c in r['checks'])} for s in ['local_entry','artifact']})
        print('TRANSPORT_RECOVERED',work.name,folder.name,flush=True)
    except Exception as e:state('failed',reason=str(e));print('TRANSPORT_RECOVERY_FAILED',folder,str(e),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--paper',required=True);p.add_argument('--workers',type=int,choices=[1,2],default=2);a=p.parse_args()
    work=BASE/a.paper
    write_json(work/'transport-recovery-protocol.json',dict(started_at=now(),global_api_sessions=a.workers,paper_slots=1,workers=a.workers,attempts_per_failed_mechanism=1,transport_retry_after_recovery=0,circuit_breaker='Stop new queued calls on first new transport failure; in-flight completion preserved',zero_tool_failed_drafts='One fresh full exploration, max7 requests/24 tools, then semantic review',prior_actual_source_reads='One completion from actual source packets then semantic review',structural_repairs_per_stage=1,failed_request_usage='unknown',target_execution='not_run'))
    with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(recover,sorted((work/'code').glob('M??'))))
    print('TRANSPORT_PASS_FINISHED','circuit_breaker' if STOP.is_set() else 'completed',flush=True)
