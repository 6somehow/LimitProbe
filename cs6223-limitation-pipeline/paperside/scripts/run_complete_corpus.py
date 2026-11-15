"""Run frozen k=2 paper semantics, mechanism-level Pi audit and Wanting handoff for four papers."""
import argparse,base64,json,os,sys,shutil,re,traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pypdf import PdfReader
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.delivery import model_call,indexed_pages,span_evidence,exact_evidence,INTERFACE_PROMPT,INTERFACE_REVIEW,SPAN_CITATION_PROMPT,TEAM
from paperprobe.independent_discovery import DISCOVERY_PROMPTS,MERGE,SPLIT_SCOPED,LOCAL_SOURCE,LOCAL_ALIGN,validate_candidates,validate_merge,check_evidence,validate_local
from paperprobe.mechanism_continuation import draft_rows,related_pages
from paperprobe.paper_decomposition import numbered,split_group
from paperprobe.multimodal_decomposition import images_from_pdf
sys.path.insert(0,str(Path('tools/pi-mechanism-agent').resolve()));sys.path.insert(0,str(Path('scripts').resolve()))
from prepare_corpus import context,prepare
from run_conformance import prepare_review
from run_sparta_batch import stage_call,repair_input
from build_paper_handoff import build

ROOT=Path.cwd();BASE=ROOT/'runs/team-complete-v1';SOURCE=ROOT/'tools/pi-mechanism-agent'
def now():return datetime.now(timezone.utc).isoformat()
def checked(dest,prompt,data,images,validate):
    try:return validate(model_call(dest,prompt,data,images))
    except Exception as e:
        if not dest.exists():raise
        raw=read_json(dest);content=raw.get('choices',[{}])[0].get('message',{}).get('content','')
        new=dest.with_name(dest.stem+'-repair.json')
        return validate(model_call(new,prompt+'\nCorrect the explicitly reported structure/provenance errors. Return the COMPLETE required JSON; no invented missing records.',dict(original_input=data,previous_response=content,validation_error=str(e)),images,max_tokens=14000))

def prepare_paper(pid):
    work=BASE/pid;work.mkdir(parents=True,exist_ok=True)
    art=read_json(next(p for p in TEAM.glob('data/*/artifact.json') if read_json(p)['artifact_id']==pid))
    from paperprobe.semantic_audit import git
    if git(ROOT/'data/repos'/f'team-{pid}','rev-parse','HEAD').strip()!=art['commit']:raise ValueError('Pinned primary HEAD differs before API launch')
    pdf=TEAM/'third_party/papers'/f'{pid}.pdf';pin=read_json(ROOT/'workstreams/zhaopeng/team-reviewed.json')[pid]
    if file_sha256(pdf)!=pin['pdf_sha256'] or art['commit']!=pin['commit']:raise ValueError('Paper/repository pins changed')
    if (work/'paper-input.json').exists():
        p=read_json(work/'paper-input.json');pages=[x['text'] for x in p['pages']]
        images=[dict(im,data_url='data:image/jpeg;base64,'+base64.b64encode(Path(im['path']).read_bytes()).decode()) for im in p['images']]
        if any(file_sha256(Path(x['path']))!=x['sha256'] for x in images):raise ValueError('Original image hash changed')
    else:
        pages=[p.extract_text() or '' for p in PdfReader(pdf).pages];paper=work/'paper';paper.mkdir()
        images=images_from_pdf(pdf,paper);write_json(work/'paper-input.json',dict(pages=numbered(pages,range(1,len(pages)+1)),images=[{k:v for k,v in im.items() if k!='data_url'} for im in images]))
    protocol=work/'protocol.json'
    if not protocol.exists():write_json(protocol,dict(artifact=art,pdf_sha256=pin['pdf_sha256'],started_at=now(),pipeline='k2 independent discovery -> merge -> split -> independent local obligations -> reconciliation -> freeze -> Pi per mechanism -> semantic review -> typed paper interface and handoff',concurrency=2,paper_request_max_output_tokens=12000,pi_exploration_requests=7,pi_tools=24,pi_semantic_review_requests=1,structural_repairs_per_stage=1,source_repair='Actual bounded Git read for rejected unread citations, then model reassessment; no mechanical verdict edits',network_retries=0,wall_deadline_per_pi_stage_seconds=920,scope='Development rollout, not a controlled accuracy comparison with prior SparTA; all raw failures retained',target_execution='not_run'))
    return work,art,pages,images

def supplement_unread(stage,out):
    repair_input(stage,out);i=read_json(out/'input.json');err=i.get('validation_feedback','')
    m=re.search(r'Unread citation ([^:]+):(.+):(\d+)-(\d+)',err)
    if m:
        alias,p,lo,hi=m[1],m[2],int(m[3]),int(m[4]);repo=i['repositories'].get(alias)
        if repo:
            from paperprobe.semantic_audit import git
            content=git(Path(repo['repo']),'show',repo['commit']+':'+p).split('\n');end=min(hi,len(content),lo+179)
            if lo<=end:
                r=dict(repo=alias,path=p,commit=repo['commit'],start_line=lo,end_line=end,lines='\n'.join(f'{n+1}: {line}' for n,line in enumerate(content) if lo<=n+1<=end))
                i['evidence_packet'].append(dict(origin='actual source read after rejected unread citation; not a supplied verdict',result=r));i['seed_read_spans'].append({k:r[k] for k in ['repo','path','start_line','end_line']});write_json(out/'recovery-read.json',r)
                i['validation_feedback']+=f'; Actual additional source {alias}:{p}:{lo}-{end} supplied. Never cite beyond its actual end.'
    i['validation_feedback']+=' Every pending item needs a NONEMPTY actual field stating inspected facts or the precise uninspected path. Every completed scope item MUST contain a NONEMPTY equivalence string explaining source matching or differences; empty equivalence is allowed only for pending work. Return every original behavior ID; unfinished work is null verdict, not absent.'
    i['assessment_contract']['max_output_tokens']=max(12000,i['assessment_contract']['max_output_tokens']);write_json(out/'input.json',i)

def audit_one(work,art,ctx,m):
    folder=work/'code'/m['id'];state_path=folder/'state.json'
    if state_path.exists():
        old=read_json(state_path)
        if old['state']=='reviewed':return dict(mechanism=m['id'],stage=str(work/'code'/old['report']))
        if old['state'] not in ['failed']:raise ValueError('Prior unfinished stage preserved; inspect job identity before resuming')
        return None
    folder.mkdir(parents=True);stages=[]
    def state(s,**kw):write_json(state_path,dict(mechanism=m['id'],state=s,stages=stages,updated_at=now(),**kw))
    try:
        draft=folder/'draft';prepare(draft,m['id'],art,work/'inventory',work/'behaviors',ctx);stages.append('draft');state('draft_running')
        ok=stage_call(draft,work/'runtime')
        if not ok:
            rep=folder/'draft-repair';supplement_unread(draft,rep);stages.append(rep.name);state('draft_repair_running');ok=stage_call(rep,work/'runtime');draft=rep
        if not ok:state('failed',reason='Draft rejected; all actual attempts preserved');return None
        review=folder/'review';prepare_review(draft,review);stages.append('review');state('review_running');ok=stage_call(review,work/'runtime')
        if not ok:
            rep=folder/'review-repair';supplement_unread(review,rep);stages.append(rep.name);state('review_repair_running');ok=stage_call(rep,work/'runtime');review=rep
        if not ok:state('failed',reason='Review rejected; all actual attempts preserved');return None
        r=read_json(review/'report.json');state('reviewed',report=str(review.relative_to(work/'code')),progress={s:{'completed':sum(c[s]['review_state']=='completed' for c in r['checks']),'pending':sum(c[s]['review_state']=='pending' for c in r['checks'])} for s in ['local_entry','artifact']})
        print('PI_DONE',art['artifact_id'],m['id'],len(r['checks']),flush=True);return dict(mechanism=m['id'],stage=str(review))
    except Exception as e:state('failed',reason=str(e));print('PI_FAILED',art['artifact_id'],m['id'],str(e),flush=True);return None

def run(pid):
    work,art,pages,images=prepare_paper(pid);status=work/'state.json'
    def state(s,**kw):write_json(status,dict(paper=pid,state=s,time=now(),**kw));print('PAPER',pid,s,flush=True)
    inventory=work/'inventory';inventory.mkdir(exist_ok=True)
    state('independent_discovery')
    def discover(n):
        data=dict(pages=numbered(pages,range(1,len(pages)+1)))
        rows=checked(inventory/f'discovery-{n}.raw.json',DISCOVERY_PROMPTS[n-1],data,images,lambda r:validate_candidates(r,'A' if n==1 else 'B',pages))
        write_json(inventory/f'discovery-{n}.json',dict(mechanisms=rows));return rows
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(discover,1);b=pool.submit(discover,2);a,b=a.result(),b.result()
    state('merge')
    merged=checked(inventory/'merge.raw.json',MERGE,dict(inventories=[dict(mechanisms=a),dict(mechanisms=b)],pages=numbered(pages,range(1,len(pages)+1))),images,lambda r:validate_merge(r,a+b,pages))
    write_json(inventory/'merged-mechanisms.json',merged);mechanisms=merged['mechanisms'];scope=[{k:m.get(k) for k in ['id','name','description','boundary','parent_name']} for m in mechanisms]
    frozen_hash=file_sha256(inventory/'merged-mechanisms.json')
    cont=work/'behaviors';cont.mkdir(exist_ok=True);groups={};state('split_behaviors',mechanisms=len(mechanisms))
    def split(batch):
        indices=sorted({p for m in batch for p in m['pages']}|{e['page'] for m in batch for e in m['evidence']})
        raw=checked(cont/f'split-{batch[0]["id"]}.raw.json',SPLIT_SCOPED,dict(mechanisms=batch,scope_catalog=scope,pages=numbered(pages,indices)),[images[p-1] for p in indices],lambda r:{m['id']:split_group(r,m,pages,verify_evidence=False) for m in batch})
        for mid,g in raw.items():write_json(cont/f'{mid}-initial.json',g)
        return raw
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(split,[mechanisms[i:i+3] for i in range(0,len(mechanisms),3)]):groups.update(result)
    state('mechanism_local_review',initial_behaviors=sum(len(g['behaviors']) for g in groups.values()))
    def local(m):
        mid=m['id'];g=groups[mid];inds=related_pages(m,g);imgs=[images[p-1] for p in inds]
        data=dict(mechanism=m,parent_child_boundaries=[x for x in mechanisms if x['name']==m.get('parent_name') or x.get('parent_name')==m['name']],scope_catalog=scope,pages=numbered(pages,inds))
        def val(raw):
            ids=[x['id'] for x in raw['obligations']]
            if len(ids)!=len(set(ids)):raise ValueError('Duplicate obligation IDs')
            for ob in raw['obligations']:check_evidence(ob['evidence'],pages,inds)
            return raw
        source=checked(cont/f'{mid}-obligations.raw.json',LOCAL_SOURCE,data,imgs,val)
        aligned=checked(cont/f'{mid}-reconcile.raw.json',LOCAL_ALIGN,dict(data,obligations=source['obligations'],behaviors=g['behaviors'],rejected_candidates=g['rejected'],context_gaps=source.get('context_gaps',[])),imgs,lambda r:validate_local(r,source['obligations'],g['behaviors'],pages,inds))
        write_json(cont/f'{mid}-local-review.json',aligned);draft=draft_rows(mid,g['behaviors'],aligned);write_json(cont/f'{mid}-draft.json',draft);print('FROZEN',pid,mid,len(draft['behaviors']),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(local,mechanisms))
    assert file_sha256(inventory/'merged-mechanisms.json')==frozen_hash
    state('pi_code_audit',mechanisms=len(mechanisms))
    runtime=work/'runtime';runtime.mkdir(exist_ok=True)
    for p in SOURCE.iterdir():
        if p.suffix in ['.py','.mjs'] and not p.name.endswith('.test.mjs'):
            dest=runtime/p.name
            if not dest.exists():shutil.copyfile(p,dest)
    if not (runtime/'node_modules').exists():(runtime/'node_modules').symlink_to(SOURCE/'node_modules',target_is_directory=True)
    (work/'code').mkdir(exist_ok=True);ctx=context(art,read_json(work/'paper-input.json'),ROOT/'data/repos'/f'team-{pid}');write_json(work/'repository-context.json',ctx)
    with ThreadPoolExecutor(max_workers=2) as pool:reports=list(pool.map(lambda m:audit_one(work,art,ctx,m),mechanisms))
    reports=[r for r in reports if r];write_json(work/'report-index.json',reports)
    state('paper_interface',accepted_mechanisms=len(reports),expected_mechanisms=len(mechanisms))
    interface=model_call(work/'interface.raw.json',INTERFACE_PROMPT,dict(pages=numbered(pages,range(1,len(pages)+1))),images)
    revised=checked(work/'interface-review.raw.json',INTERFACE_REVIEW,dict(candidate=interface,pages=indexed_pages(pages)),images,lambda r:validate_interface(r,pages))
    write_json(work/'interface-reviewed.json',revised)
    rows=[b for p in cont.glob('M??-draft.json') for b in read_json(p)['behaviors']];missing=[b for b in rows if not exact_evidence(b['evidence'],pages)]
    def cite(n):
        batch=missing[n:n+12];inds=sorted({e.get('page') or int(e['locator'].split('.')[-1]) for b in batch for e in b['evidence']})
        def val(r):
            if {x['id'] for x in r['items']}!={b['id'] for b in batch}:raise ValueError('Citation ID coverage')
            for x in r['items']:x['evidence']=span_evidence(x['evidence_spans'],pages)
            return r
        r=checked(work/f'citation-spans-{n//12:02d}.raw.json',SPAN_CITATION_PROMPT,dict(items=batch,pages=indexed_pages(pages,inds)),[images[p-1] for p in inds],val);write_json(work/f'citation-spans-{n//12:02d}.json',r)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(cite,range(0,len(missing),12)))
    state('handoff_export')
    proof=build(pid,work,inventory,cont,ROOT/'handoffs/paper-side-v1'/pid)
    state('finished_with_pending_checks' if proof['pending_artifact'] or len(reports)<len(mechanisms) else 'finished',validation=proof,mechanisms=len(mechanisms),accepted_mechanisms=len(reports))

def validate_interface(r,pages):
    for field in ['scope','eval_points']:
        for row in r[field]:row['evidence']=span_evidence(row['evidence_spans'],pages)
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--papers',nargs='+',default=['flexprefill','minference','infinigen','nnsmith']);a=p.parse_args();BASE.mkdir(parents=True,exist_ok=True)
    states={}
    for pid in a.papers:
        try:run(pid);states[pid]=read_json(BASE/pid/'state.json')['state']
        except Exception as e:
            states[pid]='failed';write_json(BASE/pid/'failure.json',dict(error=str(e),traceback=traceback.format_exc(),time=now()));print('PAPER_FAILED',pid,str(e),flush=True)
        write_json(BASE/'corpus-status.json',states)
