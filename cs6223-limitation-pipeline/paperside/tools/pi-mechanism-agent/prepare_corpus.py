"""Generic pinned paper/repository preparation, independent of SparTA-specific paths."""
from pathlib import Path
from copy import deepcopy
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.semantic_audit import git,index
from prepare_mechanism import repository_manifest

def context(artifact,paper_input,repo):
    primary=repository_manifest(repo,artifact['commit'])
    defs,edges,stats=index(repo,artifact['commit'])
    primary.update(definitions={k:{field:d[field] for field in ['path','name','start','end']} for k,d in defs.items()},edges=edges,index=stats)
    return dict(repo=str(repo.resolve()),commit=artifact['commit'],repositories={'primary':primary},
      pages=paper_input['pages'],images=paper_input['images'],
      dependency_provenance={'artifact':artifact,'scope':'Only supplied pinned repositories can be read. An uninspected required external dependency is pending, not absent.','historical_limit':'Pinned source is not proof of the paper historical runtime.'})

def prepare(output,mid,artifact,inventory,continuation,ctx):
    output.mkdir(parents=True)
    mechanism=deepcopy(next(x for x in read_json(inventory/'merged-mechanisms.json')['mechanisms'] if x['id']==mid))
    behaviors=read_json(continuation/f'{mid}-draft.json')['behaviors']
    pages=set(mechanism['pages'])
    for b in behaviors:
        for e in b['evidence']:pages.add(e.get('page') or int(e['locator'].split('.')[-1]))
    mechanism['pages']=sorted(pages)
    primary=ctx['repositories']['primary'];known={f['path'] for f in primary['files']}
    orientation=[p for p in ['README.md','README.rst','pyproject.toml','setup.py'] if p in known][:2]
    orientation += list(dict.fromkeys(e.split('::')[0] for e in artifact['entry_points']))[:2]
    packets=[];spans=[]
    for p in dict.fromkeys(orientation):
        if p not in known:continue
        lines=git(Path(primary['repo']),'show',primary['commit']+':'+p).split('\n');end=min(len(lines),70)
        r=dict(repo='primary',path=p,commit=primary['commit'],start_line=1,end_line=end,lines='\n'.join(f'{n+1}: {line}' for n,line in enumerate(lines[:end])))
        packets.append(dict(origin='neutral README/build and declared entry orientation; no findings',result=r));spans.append({k:r[k] for k in ['repo','path','start_line','end_line']})
    inp={**ctx,'mechanism':mechanism,'behaviors':behaviors,'assessment':'claim_conformance','evidence_packet':packets,'seed_read_spans':spans,
      'source_navigation':[dict(repo='primary',entry_points=artifact['entry_points'],note='Entry points are navigation, not evidence that they implement every paper mechanism. Inspect mechanism-specific call paths and experiment scripts.')],
      'provenance':dict(artifact_id=artifact['artifact_id'],merged_sha256=file_sha256(inventory/'merged-mechanisms.json'),draft_sha256=file_sha256(continuation/f'{mid}-draft.json')),
      'preparation_source':str(Path(__file__).resolve()),'baseline_usage':{'total_tokens':170000},
      'assessment_contract':dict(unit=f'whole mechanism {mid}; frozen behavior accounting',labels=['supports','deviates','absent'],review_states=['completed','pending'],previous_verdicts_supplied=False,preselected_mechanism_evidence=False,max_requests=7,max_tools=24,max_output_tokens=min(12500,max(7500,350*len(behaviors)+2500)),target_execution='not_run')}
    write_json(output/'input.json',inp);return inp
