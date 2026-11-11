"""Prepare any frozen SparTA mechanism with neutral repository orientation, not verdicts."""
import re
from pathlib import Path
from copy import deepcopy
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.semantic_audit import git

EXTRA={
 'nnfusion':('data/repos/sparta-nnfusion-artifact','be0c5ca8cc372c5571a87e17f12dcb94a9d2b690','https://github.com/zheng-ningxin/nnfusion.git','hubert_antares'),
 'tvm':('data/repos/sparta-tvm-artifact','2eca7030aaceaad969eb6326cf5d107ba6e6f29b','https://github.com/linbinskn/tvm.git','cuda_old')}

def repository_manifest(repo,commit):
    files=[]
    if git(repo,'rev-parse','HEAD').strip()!=commit:raise ValueError('Pinned repository HEAD differs')
    for raw in git(repo,'ls-tree','-r','--long','-z',commit).split('\0'):
        if not raw:continue
        info,p=raw.split('\t',1);mode,kind,sha,size=info.split()
        files.append(dict(path=p,mode=mode,kind=kind,sha=sha,size=int(size) if size!='-' else None))
    return dict(repo=str(repo.resolve()),commit=commit,files=files,definitions={},edges=[],
                index={'skipped':[],'note':'No Python AST index for this dependency; use exact source search/read including C++/CUDA.'})

def build_context():
    previous=read_json(Path('runs/sparta-pi-conformance-M02-v2/input.json'))
    context={k:deepcopy(previous[k]) for k in ['repo','commit','pages','images','repositories','dependency_provenance']}
    for alias,(folder,commit,url,branch) in EXTRA.items():
        context['repositories'][alias]=repository_manifest(Path(folder),commit)
    context['dependency_provenance']['additional_build_dependencies']={alias:dict(url=url,branch=branch,commit=commit,declaration='primary:image/Dockerfile') for alias,(_,commit,url,branch) in EXTRA.items()}
    context['dependency_provenance']['historical_limit']='The build recipe tracks branches, not exact 2022 commits. This is the pinned present snapshot; historical runtime equivalence is unknown.'
    return context

def behavior_pages(mechanism,behaviors):
    pages=set(mechanism['pages'])
    for b in behaviors:
        for e in b.get('evidence',[]):
            if isinstance(e.get('page'),int):pages.add(e['page'])
            else:
                m=re.search(r'(?:p\.|page)\s*(\d+)',e.get('locator',''),re.I)
                if m:pages.add(int(m.group(1)))
    return sorted(p for p in pages if 1<=p<=21)

def prepare(output,mechanism_id,context=None):
    if output.exists():raise ValueError('Fresh mechanism output required')
    context=context or build_context()
    inventory=Path('runs/sparta-independent-k2-v2/merged-mechanisms.json')
    draft=Path('runs/sparta-k2-behaviors-v1')/(mechanism_id+'-draft.json')
    mechanism=next(deepcopy(m) for m in read_json(inventory)['mechanisms'] if m['id']==mechanism_id)
    behaviors=read_json(draft)['behaviors'];mechanism['pages']=behavior_pages(mechanism,behaviors)
    inp={**context,'mechanism':mechanism,'behaviors':behaviors,'assessment':'claim_conformance'}
    packets=[];spans=[]
    # Common neutral architecture/build orientation, identical for all mechanisms.
    # No M02 result or Wanting-side findings and no ranked claim-to-code snippets.
    for path in ['README.md','image/Dockerfile','sparta/core/sparta.py']:
        r=context['repositories']['primary'];text=git(Path(r['repo']),'show',r['commit']+':'+path)
        lines=text.split('\n');end=min(len(lines),100)
        span=dict(repo='primary',path=path,start_line=1,end_line=end)
        spans.append(span);packets.append(dict(origin='common repository/build orientation (not mechanism-specific findings)',result=dict(**span,commit=r['commit'],lines='\n'.join(f'{i+1}: {line}' for i,line in enumerate(lines[:end])))))
    inp.update(evidence_packet=packets,seed_read_spans=spans,
       source_navigation=[dict(repo='primary',roots=['sparta/','script/','image/'],note='Find this mechanism-specific library and experiment entries yourself; other mechanism entries are not automatically applicable.')],
       provenance=dict(merged_sha256=file_sha256(inventory),draft_sha256=file_sha256(draft)),
       baseline_usage={'total_tokens':170000},
       assessment_contract=dict(unit=f'whole {mechanism_id} mechanism; frozen per-behavior accounting',
          labels=['supports','deviates','absent'],review_states=['completed','pending'],
          previous_verdicts_supplied=False,preselected_mechanism_evidence=False,
          context_note='Common README/build/core orientation only; autonomous source exploration per mechanism. Do not default to the M02 propagation entry.',
          max_requests=7,max_tools=24,max_output_tokens=min(12500,max(6500,350*len(behaviors)+2500)),
          soft_token_target=170000,target_execution='not_run'))
    output.mkdir(parents=True);write_json(output/'input.json',inp)
    return inp
