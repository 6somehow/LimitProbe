"""Bounded paper-first method investigation using the real AgentSwarm-Serve Pi runtime.

No shell/file tools are exposed to agents. Only original PDFs and pinned Git blobs
are reachable. The host does not import or execute target code. Reference cases
are kept outside the model-visible inputs and are never used as online rewards.
"""
import argparse
import asyncio
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import time
import urllib.request
from prepare_runtime import prepare as prepare_runtime

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
ASSETS = Path(os.environ.get('CS6223_METHOD_ASSETS', '/Users/pp/Desktop/nus/cs6223/paper-guided-testing')).expanduser()


def sha(b): return hashlib.sha256(b).hexdigest()
def dump(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')
def git(repo, *args): return subprocess.check_output(['git','-C',str(repo),*args], timeout=25)

def secret_env():
    values = {}
    path = Path.home()/'.config/soclaas/soclaas.env'
    for row in path.read_text().splitlines() if path.is_file() else ():
        k, sep, v = row.removeprefix('export ').partition('=')
        if sep: values[k.strip()] = v.strip().strip('\"\'')
    for name in ('SOCLAAS_API_KEY','SOCLAAS_BASE_URL'):
        if os.environ.get(name):
            values[name] = os.environ[name]
    if not values.get('SOCLAAS_API_KEY'):
        raise ValueError('Set SOCLAAS_API_KEY or configure ~/.config/soclaas/soclaas.env')
    return values


JOINT_PROMPTS = {
    'system.txt': [('Propose hypotheses independently of source implementation details. Before any repository tools can be used, call freeze_hypotheses with your paper-grounded draft. This freezes your initial hypotheses; it is not a correctness check or reward. Subsequently use source tools', 'Paper and repository tools are available from the start. Use paper and source evidence in whatever order best serves the investigation; no hypothesis checkpoint is required. Use source tools'),
                   ('All delegated workers are paper-only in this condition; only the root can inspect repository evidence, after freezing its paper-first hypotheses.', 'The root and delegated workers can inspect both original paper and repository evidence from their first turn.')],
    'task.txt': [('freeze paper-first hypotheses, seek counterevidence in code,', 'seek counterevidence in the paper and source,')],
    'lead.txt': [('independent reconstruction of the paper', 'independent investigation of the paper and repository, including the paper'),
                 ('freeze your paper-first draft before source inspection, and use original source evidence to test your interpretation', 'use the paper and source together to test your interpretation')],
    'worker.txt': [('Freeze your own paper-grounded hypotheses before code inspection.', 'Paper and repository tools are available from the start.')],
}


def load_source_manifest(path):
    source_path = path.absolute()
    entries = json.loads(source_path.read_text())
    if not isinstance(entries, dict):
        raise ValueError('Source manifest must map paper IDs to entries')
    for entry in entries.values():
        for field in ('pdf','repo'):
            if entry.get(field):
                asset = Path(entry[field]).expanduser()
                entry[field] = str(Path(os.path.normpath(source_path.parent / asset)).resolve())
    return entries


def prepare(root, profile='procedure_max', papers=None, sources=None):
    if sources is not None and (not papers or any(a not in sources for a in papers)):
        raise ValueError('Provide a source manifest entry for every selected paper')
    paper_only=profile=='paper_only_synthesis_max'
    synthesis=profile=='paired_synthesis_max' or paper_only
    if paper_only and not (papers and sources and all(a in sources and sources[a].get('repo') is None for a in papers)):
        raise ValueError('Paper-only runs require an explicit PDF manifest with no repository for each paper')
    paired=profile=='paired_max' or synthesis
    if paired: profile='procedure_max'
    from pypdf import PdfReader
    import fitz
    assert not root.exists(), 'Use a new run; never overwrite evidence'
    root.mkdir(parents=True)
    shutil.copytree(HERE/'prompts', root/'prompts')
    if profile in ['structured_swarm','procedure_audit','procedure_thinking','procedure_max']:
        p=root/'prompts/system.txt'
        s=p.read_text()
        s+='''\nSCIENTIFIC WORKFLOW: Before selecting candidates, reconstruct the chain from the final user-facing objective through each internal criterion, decision/stopping rule, and reported evaluation metric. For each link distinguish logical sufficiency, necessity, and empirical correlation; retain author-provided mitigations. Seek an explicit mechanism, not a generic absence of proof.\nMaintain a separate inventory of author-disclosed method boundaries and weaker/negative experimental results. Do not discard them merely because they are already known, and do not confuse them with new discoveries. Traverse all evaluation subsections and figure captions; inspect original page images where needed.\nAdd top-level known_boundaries (at most 8 records) to your final JSON. Each record contains title, mechanism, conditions, paper_evidence [{page,quote}], and what_is_not_established. These do not compete with the at-most-three additional candidates. The original candidate schema and falsification requirements remain unchanged.\n'''
        p.write_text(s)
        (root/'prompts/lead.txt').write_text('''Begin with spawn to obtain an independent reconstruction of the paper's claims and evaluation evidence, including weaker results and disclosed boundaries. You choose the precise assignment. You may use a second worker for a complementary mechanism analysis or adversarial review; choose the timing and scope yourself. Workers receive the original paper independently, not your session. Meanwhile or afterwards reconstruct the objective-to-internal-criterion chain, challenge assumptions, freeze your paper-first draft before source inspection, and use original source evidence to test your interpretation. Integrate original reports critically. If delegated evidence is incomplete, say so. You have at most {turns} model replies and {n} direct workers. Deliver separate known_boundaries and new candidates; no new candidate is required.\n''')
        if profile in ['procedure_audit','procedure_thinking','procedure_max']:
            with p.open('a') as f:
                f.write('''\nPROCEDURE AUDIT: Enumerate every author-proposed algorithm or decision procedure before ranking hypotheses. For each, record inputs, mutable state, chosen objective or decision criterion, transition/update rule, termination/acceptance condition, returned artifact, and the downstream research objective. Ask what the output logically establishes and which relevant properties remain unconstrained. Examine selection, discarded alternatives, iteration and repeated invocations as well as one successful run. Check whether randomness, restarts, feedback or other mitigations close a proposed gap. Do not assume an unconstrained property is automatically a flaw: give a concrete causal consequence and a controlled way to test it. Preserve conditional testing opportunities even when they are not contradictions of an explicit universal claim.\nAdd procedure_map with these records to final JSON. Retain up to six candidates rather than three; do not invent candidates to fill a quota. No keyword, case-specific example or reference limitation is supplied. All delegated workers are paper-only in this condition; only the root can inspect repository evidence, after freezing its paper-first hypotheses. Keep every narrative field within 90 Chinese characters and each original quotation within 40 words; avoid repeating the full paper or the same rationale.\n''')
    prepare_runtime(None,root/'runtime')
    shutil.copy2(Path(__file__), root/'pilot.snapshot.py')
    for aid in dict.fromkeys(papers or ['sparta','nnsmith']):
        folder=root/aid;folder.mkdir();(folder/'images').mkdir()
        if sources and aid in sources:
            artifact=sources[aid]
            pdf=Path(artifact['pdf'])
            repo=Path(artifact['repo']) if artifact.get('repo') else None
        else:
            pdf=ASSETS/'handoffs/paper-side-v1'/aid/'evidence/paper.pdf'
            artifact=json.loads((MODULE/'handoffs/paper-side-v1'/aid/'artifact.json').read_text())
            repo=ASSETS/'data/repos'/('team-'+aid)
        commit=artifact.get('commit')
        if repo is not None:
            if not isinstance(commit,str) or not re.fullmatch(r'[0-9a-f]{40}',commit):
                raise ValueError(f'{aid}: use a full fixed Git commit')
            git(repo,'cat-file','-e',commit+'^{commit}')
        elif commit is not None or not paper_only:
            raise ValueError(f'{aid}: missing author repository outside the paper-only profile')
        digest=sha(pdf.read_bytes())
        if artifact.get('pdf_sha256') and artifact['pdf_sha256']!=digest:
            raise ValueError(f'{aid}: original PDF hash does not match manifest')
        original=PdfReader(pdf);doc=fitz.open(pdf)
        pages=[]
        for i,page in enumerate(original.pages,1):
            text=page.extract_text() or ''
            lines=text.splitlines()
            pages.append(dict(page=i,text=text,numbered='\n'.join(f'{n}: {s}' for n,s in enumerate(lines,1))))
            doc[i-1].get_pixmap(matrix=fitz.Matrix(0.9,0.9)).save(folder/'images'/f'{i}.png')
        dump(folder/'paper.json',pages)
        dump(folder/'source.json',dict(paper_id=aid,pdf_sha256=digest,repo=str(repo) if repo is not None else None,commit=commit,
                                      allowed_inputs='original paper pages and original tracked repository only' if repo else 'original paper pages only',
                                      **{key:artifact[key] for key in ('pdf_url','repo_url','source_role') if key in artifact}))
    protocol=dict(version='method-boundary-pilot/2',date='2026-11-20',source_main='a0cc31a3e05eca9b68121bf6962b35a1c46403c7',
       model_alias='x-test-2',model_identity='Existing SoCLaaS DeepSeek route; concrete backend revision not independently attested',
       conditions=['single_goal','swarm_goal'],papers=['sparta','nnsmith'],max_http_requests_per_cell=16,
       max_output_tokens=7000,max_actual_returned_tokens_per_cell=600000,closing_reserve_tokens=150000,
       revision_reason='v1 exhausted budget before final or truncated final JSON; no candidate content used to revise prompts',
       token_cap_note='Admission stops after observed usage reaches cap; at most two admitted concurrent replies can overshoot. HTTP request count is hard.',
       global_model_concurrency=2,per_request_timeout_seconds=150,per_cell_wall_seconds=900,
       tree=dict(max_active=3,max_children=2,max_depth=1,worker_context='independent',joined=True),
       turns=dict(single_goal=16,swarm_goal=dict(root=6,worker=5)),temperature=0,
       retries=0,prior_outputs_supplied=False,reference_document_supplied=False,reference_rewards=False,
       target_execution='not_run',design_status='Development pilot designed after seeing reference cases, not a held-out evaluation',
       primary_question='Can goal-driven paper-first investigation propose defensible method-level boundary hypotheses without reference answers?',
       acceptance=['original prompts/responses and tool evidence retained','reference answers excluded from model inputs/tools',
                   'source claims point to actual read spans','counterevidence and falsification specified',
                   'method candidates distinct from implementation defects','negative results and truncated outputs retained'],
       interpretation='One sample per condition/paper. No accuracy, significance, recall, new-bug or swarm superiority claim.')
    if profile in ['structured_swarm','procedure_audit','procedure_thinking','procedure_max']:
        protocol.update(version='method-boundary-pilot/3',conditions=['swarm_goal'],
                        revision_reason='Adaptive development after v2: no delegation adopted, disclosed boundaries competed with new candidates, and local-code exploration dominated. Generic workflow changes only; no target-specific limitation supplied.',
                        coordination='Initial independent delegation required; assignment, optional second worker and investigation remain model decisions',
                        comparison='Different workflow and coordination prompts from v2; not an isolated swarm ablation')
        if profile in ['procedure_audit','procedure_thinking','procedure_max']:
            protocol.update(version='method-boundary-pilot/4',papers=['nnsmith'],paper_only_workers=True,max_report_candidates=6,
                            revision_reason='NNSmith reference was absent from all v2/v3 intermediate and final candidates. Audit every procedure generically before candidate ranking; prohibit worker code access. No reference answers or match feedback supplied to model.',
                            comparison='Adaptive NNSmith-only development retry, not a held-out comparison or evidence of generality')
            if profile in ['procedure_thinking','procedure_max']:
                protocol.update(version='method-boundary-pilot/5',thinking={'type':'enabled'},reasoning_effort='high',max_output_tokens=16000,
                                temperature=None,revision_reason='Enable native DeepSeek thinking after synthetic two-call transport preflight; preserve all returned reasoning fields. Scientific prompts are byte-identical to v4b.',
                                comparison='Adaptive thinking-enabled retry; combined thinking/output budget differs from v4b, not an isolated controlled ablation')
                if profile=='procedure_max':
                    protocol.update(version='method-boundary-pilot/6',reasoning_effort='max',max_output_tokens=32768,
                                    per_request_timeout_seconds=300,per_cell_wall_seconds=1200,
                                    revision_reason='User explicitly requested reasoning_effort=max; abort high condition and start a fresh run without reusing its hypotheses or reports.')
    if paired:
        joint=root/'prompts-joint'
        shutil.copytree(root/'prompts',joint)
        for name,replacements in JOINT_PROMPTS.items():
            target=joint/name
            content=target.read_text()
            for old,new in replacements:
                assert content.count(old)==1, (name,old)
                content=content.replace(old,new)
            target.write_text(content)
        protocol.update(version='method-boundary-pilot/7',papers=['nnsmith','sparta'],
                        conditions=['swarm_goal','joint_swarm_goal'],
                        comparison='Same Pi-swarm, model, research objective, evidence and limits. Change only source availability and instructions required by each workflow.',
                        revision_reason='Compare paper-first workflow with joint paper and source access from the first turn.',
                        primary_question='Which workflow recovers the frozen method-level reference cases?')
    if synthesis:
        for directory in ['prompts','prompts-joint']:
            lead=root/directory/'lead.txt'
            lead.write_text(lead.read_text().rstrip()+'\n\n'+(root/'prompts/candidate-synthesis.txt').read_text())
        protocol.update(version='method-boundary-pilot/8',papers=['nnsmith'],
                        comparison='Repeat both NNSmith workflows from v7. Only the root final candidate synthesis instructions change.',
                        revision_reason='Test whether explicit review of procedure-map rows improves final candidate synthesis.',
                        prior_outputs_supplied=False,reference_document_supplied=False)
    if paper_only:
        protocol.update(version='method-boundary-paper-only/1',conditions=['paper_only_swarm'],
                        evidence_mode='paper_only',paper_only_workers=True,
                        comparison='Separate feasibility stratum for papers without a verified author implementation.',
                        revision_reason='Inputs have published paper evidence and no confirmed author repository.')
        system=(joint/'system.txt').read_text()
        start=system.index(JOINT_PROMPTS['system.txt'][0][1])
        stop=system.index('\n\n',start)
        system=system[:start]+(
            'Only original paper evidence is available. Use the methods, evaluation and limitations sections to look for support and counterevidence. '
            'Consider alternative explanations, mitigations and the measured experimental conditions. Qualify hypotheses that require implementation evidence.'
        )+system[stop:]
        system=system.replace(JOINT_PROMPTS['system.txt'][1][1],
                              'The root and delegated workers can read original paper evidence from their first turn.')
        system=system.replace('Tools search only the supplied original paper and author repository at the fixed commit.',
                              'The only evidence tool reads original pages. Leave code_evidence empty and attribute implementation questions to an evidence gap.')
        (root/'prompts/system.txt').write_text(system)
        (root/'prompts/task.txt').write_text(
            'Analyze the supplied original paper for scientifically consequential limitations of its method. Use its procedures, assumptions and evaluations to substantiate or refute hypotheses. Separate implementation claims that would require source code. Return the requested JSON.\n')
        (root/'prompts/lead.txt').write_text(
            'Begin with spawn to obtain an independent analysis of the methods and experimental evidence. Assign complementary readings and integrate them critically. You have {turns} model replies and at most {n} workers.\n\n'+
            (root/'prompts/candidate-synthesis.txt').read_text())
        (root/'prompts/worker.txt').write_text(
            'Analyze the original paper within {turns} replies. Support your diagnosis with precise paper evidence, consider counterevidence and flag unsupported implementation claims.\n')
    if papers:
        protocol['papers']=list(dict.fromkeys(papers))
    dump(root/'protocol.json',protocol)
    fingerprints={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
    dump(root/'input-index.json',fingerprints)
    print('Prepared',root)


class Evidence:
    def __init__(self, folder, out):
        self.meta=json.loads((folder/'source.json').read_text()); self.pages=json.loads((folder/'paper.json').read_text())
        self.folder,self.out=folder,out; self.frozen=set();self.reads=[];self.tools=[];self.cache={};self.paper_only_workers=False;self.requires_freeze=True;self.max_report_candidates=3
        rows=git(self.meta['repo'],'ls-tree','-r','--long',self.meta['commit']).decode().splitlines() if self.meta['repo'] else []
        self.paths={}
        for row in rows:
            info,name=row.split('\t',1); mode,kind,obj,size=info.split()
            if kind=='blob' and size.isdigit() and int(size)<=500000:self.paths[name]=dict(mode=mode,size=int(size),sha=obj)
    def blob(self,path):
        # Exact tracked paths only: no worktree, parent paths, symlink resolution, or Git history.
        if path not in self.paths or self.paths[path]['mode']=='120000':raise ValueError('Not an allowed original tracked blob')
        if path not in self.cache:
            self.cache[path]=git(self.meta['repo'],'show',self.meta['commit']+':'+path).decode('utf-8',errors='replace')
        if '\x00' in self.cache[path]:raise ValueError('Binary source not readable')
        return self.cache[path]
    def call(self,agent,name,args):
        record=dict(agent=agent,name=name,args=args)
        if name=='read_paper':
            n=args['page'];page=self.pages[n-1]
            if type(n)!=int or n<1 or page['page']!=n:raise ValueError('Invalid physical page')
            image=(self.folder/'images'/f'{n}.png').read_bytes()
            result={'content':[{'type':'text','text':json.dumps(page,ensure_ascii=False)},
                              {'type':'image','data':base64.b64encode(image).decode(),'mimeType':'image/png'}]}
            record['image_sha256']=sha(image)
        elif not self.meta['repo']:
            raise ValueError('Only original PDF access is available for this paper')
        elif name=='freeze_hypotheses':
            if agent in self.frozen:raise ValueError('Initial paper hypotheses already frozen')
            if not isinstance(args.get('hypotheses'),list):raise ValueError('Hypotheses list required; empty allowed')
            self.frozen.add(agent);dump(self.out/('paper-first-'+agent+'.json'),args)
            result='Original paper-first draft frozen. Now inspect source to challenge it. This is not acceptance or a reward.'
        else:
            if self.paper_only_workers and agent!='root':raise ValueError('This worker has paper-only capabilities')
            if self.requires_freeze and agent not in self.frozen:raise ValueError('Freeze paper-first hypotheses before repository access')
            if name=='list_repo':
                prefix=args.get('prefix',''); paths=[p for p in self.paths if p.startswith(prefix)]
                result=json.dumps(dict(paths=paths[:100],total=len(paths)),ensure_ascii=False)
            elif name=='search_repo':
                q=args['query'];scope=args.get('prefix','')
                if not 2<=len(q)<=160:raise ValueError('Bounded literal query required')
                if scope.startswith(('/',':')) or '..' in PurePosixPath(scope).parts:raise ValueError('Invalid search scope')
                command=['git','-C',self.meta['repo'],'grep','-n','-I','-i','-F','-e',q,self.meta['commit'],'--']
                if scope:command.append(scope)
                found=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25)
                if found.returncode not in [0,1]:raise ValueError('Original Git search failed')
                hits=[];total=0
                for row in found.stdout.decode('utf-8',errors='replace').splitlines():
                    p,n,line=row.removeprefix(self.meta['commit']+':').split(':',2)
                    if p not in self.paths:continue
                    total+=1
                    if len(hits)<32:hits.append(dict(path=p,line=int(n),text=line[:300]))
                result=json.dumps(dict(hits=hits,total=total,note='Pointers only; read full source before asserting behavior'),ensure_ascii=False)
            elif name=='read_repo':
                p=args['path'];start=args.get('start',1);end=args.get('end',start+99)
                if type(start)!=int or type(end)!=int or not 1<=start<=end<=start+159:raise ValueError('Read at most 160 lines')
                lines=self.blob(p).splitlines();end=min(end,len(lines))
                if start>end:raise ValueError('Invalid source range')
                self.reads.append(dict(agent=agent,path=p,start=start,end=end))
                result=json.dumps(dict(path=p,commit=self.meta['commit'],start=start,end=end,
                                       text='\n'.join(f'{i}: {lines[i-1]}' for i in range(start,end+1))),ensure_ascii=False)
            else:raise ValueError('Tool not allowed')
        record['result']=compact(result);self.tools.append(record)
        return result


def compact(value):
    if isinstance(value,list):return [compact(v) for v in value]
    if isinstance(value,dict):
        if value.get('type')=='image' and 'data' in value:return {k:v for k,v in value.items() if k!='data'}|{'data_sha256':sha(base64.b64decode(value['data']))}
        if value.get('type')=='image_url':return {'type':'image_url','image_sha256':sha(value['image_url']['url'].encode())}
        return {k:compact(v) for k,v in value.items()}
    return value


def tool_schema(name,description,properties,required):
    return dict(name=name,description=description,parameters=dict(type='object',properties=properties,required=required,additionalProperties=False))

TOOLS=[
 tool_schema('read_paper','Read an original physical PDF page, as text plus its original image.',{'page':{'type':'integer','minimum':1}},['page']),
 tool_schema('freeze_hypotheses','Freeze your paper-first hypotheses before source inspection. Empty list is valid. Not an acceptance check.',{'hypotheses':{'type':'array','items':{'type':'object','properties':{'title':{'type':'string'},'argument':{'type':'string'},'pages':{'type':'array','items':{'type':'integer'}}},'required':['title','argument','pages'],'additionalProperties':False}}},['hypotheses']),
 tool_schema('list_repo','List original tracked repository paths after freezing hypotheses.',{'prefix':{'type':'string'}},[]),
 tool_schema('search_repo','Search literal text in original fixed-commit repository after freezing hypotheses.',{'query':{'type':'string'},'prefix':{'type':'string'}},['query']),
 tool_schema('read_repo','Read at most 160 original Git-blob lines after freezing hypotheses. No execution.',{'path':{'type':'string'},'start':{'type':'integer','minimum':1},'end':{'type':'integer','minimum':1}},['path'])]


class Cell:
    def __init__(self,root,aid,condition,semaphore):
        self.root,self.aid,self.condition,self.semaphore=root,aid,condition,semaphore
        self.protocol=json.loads((root/'protocol.json').read_text())
        self.folder=root/aid;self.out=self.folder/condition
        assert not self.out.exists(),'Never overwrite a run'
        self.out.mkdir();self.evidence=Evidence(self.folder,self.out)
        self.joint=condition=='joint_swarm_goal'
        self.evidence.requires_freeze=not self.joint
        self.evidence.paper_only_workers=not self.joint and self.protocol.get('paper_only_workers',False)
        self.evidence.max_report_candidates=self.protocol.get('max_report_candidates',3)
        self.started=time.time();self.requests=0;self.tokens=0;self.errors=[];self.wire_ids=[]
        self.write_lock=asyncio.Lock();self.tasks=set();self.result=None
        self.env=secret_env();self.key=self.env['SOCLAAS_API_KEY']
        self.base=self.env.get('SOCLAAS_BASE_URL','https://soclaas-api.comp.nus.edu.sg/v1').rstrip('/')
    def log(self,name,value):
        with (self.out/name).open('a') as f:f.write(json.dumps(compact(value),ensure_ascii=False)+'\n')
    def cfg(self):
        p=lambda name:(self.root/('prompts-joint' if self.joint else 'prompts')/name).read_text()
        full='\n\n'.join('PHYSICAL PDF PAGE '+str(x['page'])+'\n'+x['numbered'] for x in self.evidence.pages)
        swarm=self.condition in ['swarm_goal','joint_swarm_goal','paper_only_swarm']
        tools=TOOLS
        if self.joint:
            tools=[t|{'description':t['description'].replace(' after freezing hypotheses','')}
                   for t in TOOLS if t['name']!='freeze_hypotheses']
        if self.condition=='paper_only_swarm':
            tools=[t for t in TOOLS if t['name']=='read_paper']
        commit=self.evidence.meta['commit']
        source_context='Pinned repository commit: '+commit if commit else 'Evidence scope: published paper only'
        return dict(cwd=str(self.out),agentDir=str(self.out/'agent-config'),endpoint='http://unused-host-transport.invalid',
            modelId='x-test-2',modelName='SoCLaaS existing DeepSeek route',contextLimit=131072,maxOutputTokens=self.protocol['max_output_tokens'],
            systemPrompt=p('system.txt'),task=p('task.txt')+'\nPaper ID: '+self.aid+'\n'+source_context+'\n\nORIGINAL PAPER BEGIN\n'+full+'\nORIGINAL PAPER END',
            tools=tools,paperOnlyWorkers=self.evidence.paper_only_workers,leadPrompt=p('lead.txt'),workerPrompt=p('worker.txt'),
            remainingPrompt='You have {n} replies left. Continue the research goal, seek counterevidence, and reserve the final reply for the requested JSON. No discovery is a valid result.',
            lastTurnPrompt='This is your final model reply; tools are disabled. Deliver the requested JSON using only evidence actually obtained. Withdraw unsupported items and disclose gaps.',
            spawnDescription='Delegate a complementary source investigation or adversarial review of your own hypothesis. No answer key is provided.',
            spawnSchema=dict(type='object',properties={'task':{'type':'string'}},required=['task'],additionalProperties=False),
            limits=dict(maxActive=3 if swarm else 1,maxDepth=1 if swarm else 0,maxTotal=3 if swarm else 1,
                        maxChildren=2 if swarm else 1,maxTurns=16 if not swarm else 6,workerContext='independent',
                        **({'turnsByRole':self.protocol['turns']['swarm_goal']} if swarm else {})),deadlineEpoch=self.started+self.protocol['per_cell_wall_seconds'])
    def http(self,payload,n):
        (self.out/f'request-{n:02d}.json').write_text(json.dumps(payload,ensure_ascii=False))
        request=urllib.request.Request(self.base+'/chat/completions',data=json.dumps(payload).encode(),
                                       headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        start=time.time()
        with urllib.request.urlopen(request,timeout=self.protocol['per_request_timeout_seconds']) as response:raw=response.read()
        (self.out/f'response-{n:02d}.json').write_bytes(raw)
        body=json.loads(raw);self.log('usage.jsonl',dict(request=n,elapsed_seconds=time.time()-start,model=body.get('model'),usage=body.get('usage')))
        return body
    async def dispatch(self,op,data):
        if op=='init':return self.cfg()
        if op in ['event','sdk_event']:
            self.log(op+'.jsonl',data);return True
        if op=='tool':
            try:return await asyncio.to_thread(self.evidence.call,data['agent'],data['name'],data['args'])
            except Exception as exc:
                error=str(exc);self.log('tool-errors.jsonl',dict(**data,error=error));return 'Tool refused: '+error
        if op=='model':
            async with self.semaphore:
                cap=self.protocol['max_actual_returned_tokens_per_cell']
                request_cap=self.protocol['max_http_requests_per_cell']
                if self.requests>=request_cap or self.tokens>=cap or time.time()>self.started+self.protocol['per_cell_wall_seconds']:raise ValueError('Shared cell budget reached')
                self.requests+=1;n=self.requests;self.wire_ids.append(dict(request=n,agent=data['agent'],turn=data['turn']))
                payload=dict(model='x-test-2',messages=list(data['messages']),max_tokens=self.protocol['max_output_tokens'],temperature=0,stream=False,reasoning_effort='none')
                if self.protocol.get('thinking'):
                    payload.pop('temperature')
                    payload['thinking']=self.protocol['thinking']
                    payload['reasoning_effort']=self.protocol['reasoning_effort']
                if data.get('tools'):payload['tools']=data['tools']
                closing=self.tokens>=cap-self.protocol.get('closing_reserve_tokens',0) or (not self.protocol.get('staged_review') and self.requests>=request_cap-2)
                note=f'Shared run budget observation: {self.requests}/{request_cap} HTTP requests admitted, {self.tokens} actual tokens observed. '
                if data.get('force_close'):
                    if payload.get('tools'):payload['tool_choice']='none'
                    note+='Transport recovery: conclude using the evidence already read. Return the requested final JSON and disclose remaining gaps.'
                elif closing:
                    if payload.get('tools'):payload['tool_choice']='none'
                    note+='Finalization reserve reached. No further task tools: now return compact final JSON from the evidence obtained, including uncertainties. If you are the parent integrating child reports, report incomplete child evidence honestly.'
                else:note+='Reserve resources for a final report; source exploration alone is not the goal. You may conclude with no defensible candidates.'
                payload['messages'].append(dict(role='user',content=note))
                body=await asyncio.to_thread(self.http,payload,n)
                if body.get('error'):raise ValueError('Provider error: '+str(body['error']))
                choice=body['choices'][0];u=body.get('usage') or {};self.tokens+=u.get('total_tokens',0)
                original=choice['message'];msg=dict(role='assistant',content=original.get('content') or '')
                if original.get('tool_calls'):msg['tool_calls']=original['tool_calls']
                for key in ['reasoning','reasoning_content','reasoning_details']:
                    if key in original:msg[key]=original[key]
                finish=choice.get('finish_reason')
                if finish not in ['stop','tool_calls','length']:raise ValueError('Unrecognized original finish reason '+str(finish))
                print(self.aid,self.condition,n,data['agent'],finish,'tokens',u.get('total_tokens'),flush=True)
                return dict(assistant_message=msg,usage=dict(prompt_tokens=u.get('prompt_tokens'),completion_tokens=u.get('completion_tokens'),cached_tokens=(u.get('prompt_tokens_details') or {}).get('cached_tokens'),finish_reason=dict(type='length' if finish=='length' else 'stop',original=finish)))
        if op=='done':self.result=data;return True
        if op=='failed':self.errors.append(data);return True
        raise ValueError('Unknown host operation '+op)
    async def answer(self,message):
        try:value=await self.dispatch(message['op'],message.get('data') or {});reply=dict(id=message['id'],ok=True,value=value)
        except Exception as exc:
            error=str(exc).replace(self.key,'[REDACTED]');self.errors.append(dict(op=message['op'],error=error));reply=dict(id=message['id'],ok=False,error=error)
        async with self.write_lock:
            try:self.proc.stdin.write((json.dumps(reply,ensure_ascii=False)+'\n').encode());await self.proc.stdin.drain()
            except (BrokenPipeError,ConnectionResetError):pass
    async def run(self):
        cfg=self.cfg();dump(self.out/'config.json',cfg)
        sdk=HERE/'node_modules/@earendil-works/pi-coding-agent/dist/index.js'
        # The reused runtime resolves its dependencies through the passed SDK path.
        stderr=(self.out/'stderr.log').open('wb')
        self.proc=await asyncio.create_subprocess_exec('node',str(self.root/'runtime/runtime.mjs'),str(sdk),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=stderr,start_new_session=True,limit=16000000)
        async def read():
            while row:=await self.proc.stdout.readline():
                m=json.loads(row);task=asyncio.create_task(self.answer(m));self.tasks.add(task);task.add_done_callback(self.tasks.discard)
            await self.proc.wait()
        try:await asyncio.wait_for(read(),timeout=self.protocol['per_cell_wall_seconds']+20)
        except (asyncio.TimeoutError,asyncio.CancelledError) as exc:
            self.errors.append(dict(error='Cell wall timeout' if isinstance(exc,asyncio.TimeoutError) else 'Cell cancelled'))
            try:os.killpg(self.proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:await asyncio.wait_for(self.proc.wait(),10)
            except asyncio.TimeoutError:os.killpg(self.proc.pid,signal.SIGKILL);await self.proc.wait()
        finally:
            if self.tasks:await asyncio.gather(*self.tasks,return_exceptions=True)
            stderr.close();dump(self.out/'reads.json',self.evidence.reads);dump(self.out/'tools.json',self.evidence.tools);dump(self.out/'request-map.json',self.wire_ids)
        if self.result:
            dump(self.out/'result.json',self.result)
            (self.out/'final.txt').write_text(self.result['answer'])
        validation=validate_answer(self.result['answer'] if self.result else '',self.evidence)
        dump(self.out/'validation.json',validation)
        summary=dict(paper=self.aid,condition=self.condition,requests=self.requests,actual_returned_total_tokens=self.tokens,
                     elapsed_seconds=time.time()-self.started,returncode=self.proc.returncode,errors=self.errors,agents=self.result.get('agents') if self.result else None,
                     target_execution='not_run',validation=validation)
        dump(self.out/'summary.json',summary);print('CELL FINISHED',json.dumps(summary,ensure_ascii=False),flush=True)
        return summary


def validate_answer(text,evidence):
    issues=[]
    try:
        clean=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip());answer=json.loads(clean)
        if answer.get('paper_id')!=evidence.meta['paper_id']:issues.append('paper id mismatch')
        if answer.get('target_execution')!='not_run':issues.append('invented execution status')
        items=answer['candidates']
        if not isinstance(items,list) or len(items)>evidence.max_report_candidates:issues.append('candidate count/schema')
        for h in items:
            if h.get('status') not in ['hypothesis_not_executed','withdrawn']:issues.append('invalid hypothesis state')
            if not h.get('paper_evidence'):issues.append(h.get('id','?')+': missing paper evidence')
            for e in h.get('paper_evidence',[]):
                page=e.get('page');quote=e.get('quote','')
                if type(page)!=int or not 1<=page<=len(evidence.pages) or not quote or quote not in evidence.pages[page-1]['text']:
                    issues.append(h.get('id','?')+': quote needs semantic/original-page review')
            for e in h.get('code_evidence',[]):
                if not any(r['path']==e.get('path') and r['start']<=e.get('start',0)<=e.get('end',0)<=r['end'] for r in evidence.reads):
                    issues.append(h.get('id','?')+': unread source span')
            c=h.get('minimal_comparison',{})
            if not all(c.get(k) for k in ['fixed','vary','baseline','observable','refuted_if']):issues.append(h.get('id','?')+': incomplete falsification plan')
        return dict(json_parsed=True,candidates=len(items),issues=issues,semantic_review='pending',mechanical_checks_do_not_prove_truth=True)
    except Exception as exc:return dict(json_parsed=False,issues=[str(exc)],semantic_review='pending')


async def run(root):
    protocol=json.loads((root/'protocol.json').read_text());assert protocol['model_alias']=='x-test-2'
    # Exact frozen inputs are checked before any paid call.
    for p,h in json.loads((root/'input-index.json').read_text()).items():assert sha((root/p).read_bytes())==h,p
    semaphore=asyncio.Semaphore(2)
    cells=[]
    # A paper pair shares concurrency but has separate sessions, source gates and evidence directories.
    for aid in protocol['papers']:
        pending=[]
        for condition in protocol['conditions']:
            archive=root/aid/condition
            if (archive/'summary.json').is_file():
                cells.append(json.loads((archive/'summary.json').read_text()))
            elif archive.exists():
                raise RuntimeError(f'Condition has an existing nonterminal archive; inspect its live runner: {archive}')
            else:
                pending.append(condition)
        cells+=await asyncio.gather(*(Cell(root,aid,c,semaphore).run() for c in pending))
    dump(root/'summary.json',dict(cells=cells,target_execution='not_run',total_requests=sum(c['requests'] for c in cells),actual_returned_total_tokens=sum(c['actual_returned_total_tokens'] for c in cells)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run']);p.add_argument('root',type=Path);p.add_argument('--profile',choices=['v2','structured_swarm','procedure_audit','procedure_thinking','procedure_max','paired_max','paired_synthesis_max','paper_only_synthesis_max'],default='procedure_max');p.add_argument('--papers', nargs='+');p.add_argument('--sources',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.root.resolve(),a.profile,a.papers,load_source_manifest(a.sources) if a.sources else None)
    else:
        root = a.root.resolve()
        with (root / '.runner.lock').open('a') as ownership:
            # Queued invocations of the same run reuse terminal archives in order.
            fcntl.flock(ownership, fcntl.LOCK_EX)
            asyncio.run(run(root))
