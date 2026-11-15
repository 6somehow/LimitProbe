"""Run Pi exploration + bounded model semantic review using claim-conformance verdicts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from paperprobe.io import read_json,write_json
from prepare_conformance import prepare
from prepare_mechanism import prepare as prepare_mechanism


def prepare_review(draft, review):
    if review.exists():raise ValueError('Review output must be fresh')
    inp=read_json(draft/'input.json')
    if inp.get('assessment')!='claim_conformance':raise ValueError('Review requires a fresh conformance draft, not implementation labels')
    if not (draft/'report.json').exists():raise ValueError('Draft did not pass structural checks; preserve failure and stop')
    inp['candidate_report']=read_json(draft/'report.json')
    allowed={'supports','deviates','absent'}
    if any(not (c.get(scope,{}).get('review_state')=='completed' and c[scope].get('verdict') in allowed or c.get(scope,{}).get('review_state')=='pending' and c[scope].get('verdict') is None) for c in inp['candidate_report']['checks'] for scope in ['local_entry','artifact']):raise ValueError('Old or unknown verdicts cannot be relabeled by this workflow')
    for line in (draft/'tools.jsonl').read_text().splitlines() if (draft/'tools.jsonl').exists() else []:
        t=json.loads(line)
        if t['name']!='read_repo':continue
        r=t['result'];inp['evidence_packet'].append(dict(origin='draft Pi read_repo',result=r))
        inp['seed_read_spans'].append({k:r[k] for k in ['repo','path','start_line','end_line']})
    inp.update(semantic_review=True,finalize_only=True,first_pass_run=str(draft.resolve()),baseline_usage={'total_tokens':90000})
    inp['assessment_contract'].update(stage='semantic consistency review',max_requests=1,
        previous_verdicts_supplied='Only first draft of THIS conformance assessment; not old implementation labels')
    review.mkdir(parents=True);write_json(review/'input.json',inp)


def run(output,mechanism='M02'):
    if not os.environ.get('SOCLAAS_API_KEY'):raise ValueError('Set SOCLAAS_API_KEY in the authorized environment')
    if output.exists():raise ValueError('Use a fresh workflow directory')
    output.mkdir(parents=True)
    draft=output/'draft';review=output/'review'
    write_json(output/'workflow.json',dict(stages=[str(draft),str(review)],max_requests=5,max_tools=12,
        soft_token_targets=dict(draft=110000,review=70000),retries=0,target_execution='not_run',
        semantics='Model proposes new claim-conformance verdicts; model reviews all qualifiers and cross-row consistency; code validates structure and provenance only.'))
    if mechanism=='M02':prepare(draft)
    else:prepare_mechanism(draft,mechanism)
    runner=Path(__file__).with_name('run-adjudication.mjs')
    subprocess.run(['node',str(runner),str(draft)],check=True,timeout=920)
    prepare_review(draft,review)
    subprocess.run(['node',str(runner),str(review)],check=True,timeout=920)
    final=read_json(review/'report.json')
    progress={scope:{'completed':sum(c[scope]['review_state']=='completed' for c in final['checks']),
                     'pending':sum(c[scope]['review_state']=='pending' for c in final['checks'])}
              for scope in ['local_entry','artifact']}
    write_json(output/'result.json',dict(report=str((review/'report.json').resolve()),
        status='has_pending_checks' if any(v['pending'] for v in progress.values()) else 'ready_for_human_semantic_review',
        progress=progress,target_execution='not_run'))
    print('Pi conformance report saved:',review/'report.json',progress)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mechanism',default='M02');a=p.parse_args();run(a.output,a.mechanism)
