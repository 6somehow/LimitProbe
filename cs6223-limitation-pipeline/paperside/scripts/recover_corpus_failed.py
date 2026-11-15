"""One bounded recovery per failed mechanism; retain all original attempts."""
import argparse, json, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path('scripts').resolve()))
from run_complete_corpus import BASE, now, supplement_unread
from paperprobe.io import read_json, write_json
from paperprobe.semantic_audit import git
from run_sparta_batch import stage_call
from run_conformance import prepare_review


def augment(stage):
    i=read_json(stage/'input.json')
    report=i.get('candidate_report',{})
    reads=[];total=0
    for e in report.get('code_evidence',[]):
        alias,path,lo,hi=e['repo'],e['path'],int(e['start_line']),int(e['end_line'])
        spans=[s for s in i['seed_read_spans'] if s['repo']==alias and s['path']==path]
        if any(int(s['start_line'])<=lo and int(s['end_line'])>=hi for s in spans):continue
        if hi-lo+1>720 or total+hi-lo+1>3000:raise ValueError('Recovery source read bound exceeded; preserve failed case')
        repo=i['repositories'][alias];lines=git(Path(repo['repo']),'show',repo['commit']+':'+path).split('\n')
        if lo<1 or hi>len(lines):raise ValueError('Candidate citation outside actual Git source')
        for start in range(lo,hi+1,180):
            end=min(hi,start+179)
            r=dict(repo=alias,path=path,commit=repo['commit'],start_line=start,end_line=end,
                   lines='\n'.join(f'{n}: {lines[n-1]}' for n in range(start,end+1)))
            i['evidence_packet'].append(dict(origin='actual bounded Git source read for failed candidate; model must reassess',result=r))
            i['seed_read_spans'].append({k:r[k] for k in ['repo','path','start_line','end_line']});reads.append(r)
        total+=hi-lo+1
    i['validation_feedback']+=' Every completed scope item MUST contain a NONEMPTY equivalence string explaining why source matches or differs; never leave it blank. Every pending item has null verdict and precise actual/pending_reason. Reassess candidate against actual supplied source, do not mechanically change verdicts. Do not invent new citation spans beyond the actual reads.'
    write_json(stage/'recovery-all-reads.json',reads);write_json(stage/'input.json',i)


def recover(folder):
    old=read_json(folder/'state.json')
    if old['state']!='failed':return
    root=folder/'bounded-recovery-v1'
    if root.exists():print('RECOVERY_ALREADY_ATTEMPTED',folder,flush=True);return
    root.mkdir();write_json(root/'original-state.json',old)
    work=folder.parent.parent;stages=list(old['stages'])
    def state(s,**kw):write_json(folder/'state.json',dict(mechanism=folder.name,state=s,stages=stages,updated_at=now(),recovery='bounded-recovery-v1',**kw))
    try:
        src=folder/stages[-1];draft=root/'completion';supplement_unread(src,draft);augment(draft)
        stages.append(str(draft.relative_to(folder)));state('bounded_recovery_running')
        if not stage_call(draft,work/'runtime'):raise ValueError('Single bounded recovery completion rejected')
        review=root/'review';prepare_review(draft,review);stages.append(str(review.relative_to(folder)));state('bounded_recovery_review_running')
        if not stage_call(review,work/'runtime'):
            repair=root/'review-repair';supplement_unread(review,repair);augment(repair)
            stages.append(str(repair.relative_to(folder)));state('bounded_recovery_review_repair_running')
            if not stage_call(repair,work/'runtime'):raise ValueError('Recovery semantic review and one repair rejected')
            review=repair
        r=read_json(review/'report.json');state('reviewed',report=str(review.relative_to(work/'code')),progress={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),'pending':sum(c[s]['review_state']=='pending' for c in r['checks'])} for s in ['local_entry','artifact']})
        print('RECOVERED',work.name,folder.name,flush=True)
    except Exception as e:state('failed',reason=str(e));print('RECOVERY_FAILED',folder,str(e),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--paper',required=True);a=p.parse_args()
    work=BASE/a.paper
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(recover,sorted((work/'code').glob('M??'))))
