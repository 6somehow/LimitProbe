"""One separately budgeted Pi follow-up for unresolved implementation-path checks."""
import argparse,json,os,shutil
from pathlib import Path
from paperprobe.io import read_json,write_json,file_sha256
from run_sparta_batch import stage_call,repair_input,now

def complete(batch,mid):
    if not os.environ.get('SOCLAAS_API_KEY'):raise ValueError('Authorized API environment required')
    case=batch/mid;state=read_json(case/'state.json')
    original_status=state['state']
    if original_status not in ['reviewed','failed']:raise ValueError('Expected a finished prior attempt')
    if original_status=='reviewed':
        prior=batch/state['report'];report=read_json(prior/'report.json')
    else:
        candidates=[case/name for name in reversed(state['stages']) if (case/name/'conformance-report.raw.json').exists()]
        if not candidates:raise ValueError('No parseable prior report for bounded recovery')
        prior=candidates[0];report=read_json(prior/'conformance-report.raw.json')
    todo=[c for c in report['checks'] if any(c[s]['review_state']=='pending' for s in ['artifact','local_entry'])]
    if not todo and original_status!='failed':raise ValueError('No pending checks')
    out=case/'path-completion'
    if out.exists():raise ValueError('Follow-up cannot overwrite an attempt')
    inp=read_json(prior/'input.json')
    for key in ['validation_feedback','previous_incomplete_response']:inp.pop(key,None)
    inp.update(candidate_report=report,finalize_only=False,semantic_review=True,baseline_usage={'total_tokens':140000},
       revision_contract={'purpose':'Complete pending implementation-path checks by actual source inspection; recheck all affected judgments; preserve original paper requirements.',
        'pending_ids':[c['id'] for c in todo],'no_forced_verdict':'Leave unassessed runtime/theorem guarantees pending; do not convert uncertainty to absence.',
        'original_report':str(prior),'prior_validation_error':read_json(prior/'summary.json').get('validation_error'),'budget_note':'Separately budgeted source-path follow-up after the initial rollout, not a hidden retry.'})
    inp['assessment_contract'].update(stage='pending implementation-path completion',max_requests=5,max_tools=12,soft_token_target=140000)
    out.mkdir();write_json(out/'input.json',inp);write_json(out/'prior-state.json',state)
    shutil.copyfile(Path(__file__),out/'completion.snapshot.py')
    write_json(out/'completion-protocol.json',dict(started_at=now(),prior_report=str(prior),pending_ids=[c['id'] for c in todo],max_requests=5,max_tools=12,max_structural_repair_requests=1,target_execution='not_run',preparer_sha256=file_sha256(Path(__file__))))
    state.update(state='path_completion_running',updated_at=now());state['stages'].append('path-completion');write_json(case/'state.json',state)
    ok=stage_call(out,batch/'runtime');final=out
    if not ok:
        final=case/'path-completion-repair';repair_input(out,final);state['stages'].append(final.name);write_json(case/'state.json',state)
        ok=stage_call(final,batch/'runtime')
    if not ok:
        # Preserve accepted prior report as current; the new failure is retained separately.
        state.update(state=original_status,updated_at=now(),completion_failure='Bounded follow-up did not produce an accepted replacement')
    else:
        r=read_json(final/'report.json');state.update(state='reviewed',report=str(final.relative_to(batch)),updated_at=now())
        state['progress']={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),
          'pending':sum(c[s]['review_state']=='pending' for c in r['checks']),
          'counts':{v:sum(c[s]['verdict']==v for c in r['checks']) for v in ['supports','deviates','absent']}} for s in ['local_entry','artifact']}
    write_json(case/'state.json',state);print(mid,json.dumps(state.get('progress',state),ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--mechanism',required=True);a=p.parse_args();complete(a.batch.resolve(),a.mechanism)
