"""Correct a demonstrated repository-identity premise; one bounded tool-enabled review."""
from pathlib import Path
import shutil,json
from paperprobe.io import read_json,write_json
from paperprobe.semantic_audit import git
from run_sparta_batch import stage_call,repair_input,now
b=Path('runs/sparta-remaining-rollout-v1').resolve();case=b/'M18';state=read_json(case/'state.json');old=b/state['report'];r=read_json(old/'report.json');i=read_json(old/'input.json')
needed={(x['repo'],x['path']) for x in r['code_evidence']};packets={}
for x in i['evidence_packet']:
 s=x['result'];p=s['path']
 if (s['repo'],p) in needed or s['repo']=='nnfusion' or any(k in p for k in ['weighted_block_cover','specialize_kernel','generate_code.py','figure17','common/utils.py']):packets[(s['repo'],p,s['start_line'],s['end_line'])]=x
repo=i['repositories']['nnfusion'];lines=git(Path(repo['repo']),'show',repo['commit']+':README.md').split('\n');start=max(1,len(lines)-39)
s=dict(repo='nnfusion',path='README.md',commit=repo['commit'],start_line=start,end_line=len(lines),lines='\n'.join(f'{n+1}: {line}' for n,line in enumerate(lines) if n+1>=start))
packets[('nnfusion','README.md',start,len(lines))]=dict(origin='Primary repository provenance: NNFusion README explicitly references Rammer',result=s)
i['evidence_packet']=list(packets.values());i['seed_read_spans']=[{k:x['result'][k] for k in ['repo','path','start_line','end_line']} for x in i['evidence_packet']]
for k in ['validation_feedback','previous_incomplete_response']:i.pop(k,None)
i.update(candidate_report=r,semantic_review=True,finalize_only=False,baseline_usage={'total_tokens':250000},revision_contract={'purpose':'The prior pending premise Rammer source is not pinned is doubtful: the supplied pinned NNFusion README explicitly cites Rammer. Investigate repository identity and actual pass registration/codegen, not just the literal project name. Reassess all pending checks with tools and supplied shared source reads.', 'do_not_force_conclusion':'Use pending only for checks genuinely not completed, with NONEMPTY actual describing inspected facts or exactly what was not inspected. No target execution. Keep all paper requirements and all 11 IDs fixed.', 'identity_limit':'A README association is evidence of lineage, not proof that this branch equals the historical Rammer runtime.'})
i['assessment_contract'].update(stage='Rammer/NNFusion identity correction and implementation review',max_requests=7,max_tools=18,max_output_tokens=10000)
out=case/'rammer-identity-review';out.mkdir();write_json(out/'input.json',i);write_json(out/'prior-state.json',state);shutil.copyfile(Path(__file__),out/'completion.snapshot.py')
write_json(out/'completion-protocol.json',dict(started_at=now(),purpose=i['revision_contract'],max_requests=7,max_tools=18,max_structural_repair_requests=1,target_execution='not_run'))
state['stages'].append(out.name);state.update(state='identity_review_running',updated_at=now());write_json(case/'state.json',state)
ok=stage_call(out,b/'runtime');final=out
if not ok:
 final=case/'rammer-identity-repair';repair_input(out,final);state['stages'].append(final.name);ok=stage_call(final,b/'runtime')
if ok:
 r=read_json(final/'report.json');state.update(report=str(final.relative_to(b)))
 state['progress']={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),'pending':sum(c[s]['review_state']=='pending' for c in r['checks']),'counts':{v:sum(c[s]['verdict']==v for c in r['checks']) for v in ['supports','deviates','absent']}} for s in ['local_entry','artifact']}
else:state['identity_followup_failure']='No accepted replacement; retain accepted source-cache-final report'
state.update(state='reviewed',updated_at=now());write_json(case/'state.json',state);print(json.dumps(state,ensure_ascii=False),flush=True)
