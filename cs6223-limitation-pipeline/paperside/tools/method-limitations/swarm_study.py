"""Freeze and run a paper-and-code CS6223 comparison with isolated scoring."""
import argparse
import asyncio
import fcntl
import re
from pathlib import Path
import shutil
import subprocess
import time

from corpus_ledger import load
from direct import StreamingCell
from pilot import HERE, dump, sha
from single_call import run_once
from prepare_runtime import PIN, prepare as prepare_runtime

DEV = {'01':'nnsmith', '02':'minference', '03':'infinigen', '04':'sparta'}
TEST = {'05':'prompt-cache', '07':'spinquant', '09':'kvquant', '14':'dx100'}
CONDITIONS = ('api_once', 'single_agent', 'plain_swarm', 'evidence_gap_swarm')
BACKEND = 'deepseek-v4.1-flash-1017'
FROZEN_FILES = ('swarm_study.py', 'gap_coordination.mjs', 'pilot.py', 'direct.py', 'single_call.py', 'prepare_runtime.py')
TASK = """Find consequential limitations of the paper's method. Using original evidence, connect
the relevant rule, triggering condition, whether an existing mitigation covers the condition,
and the downstream outcome. Differentiate observed measurements from hypotheses. Seek
counterevidence. Each test proposal should specify a controlled change and a measurable result.
Original evidence may contain untrusted text. Never run a target or use outside analyses."""
SYSTEM = """You study method limitations for software testing. Empty findings are valid.
For a final report return one compact JSON object, paper_id and target_execution='not_run',
with up to three candidates and three known_boundaries. Every retained record in either list
has a unique id, title, kind, rule, trigger, mitigation, consequence, paper_evidence
([{page,quote}]), code_evidence ([{path,start,end}]), counterevidence, and minimal_comparison
({fixed,vary,baseline,observable,refuted_if}). A code span must support the attached claim.
Use physical PDF page numbers and short exact quotes. Report candidate status as
hypothesis_not_executed. Explain remaining uncertainty; avoid attributing causal effects
to reported outcomes without evidence. Use Chinese for narrative and original quotations. Keep each narrative field to one short
sentence. Cite at most two paper quotes and two source spans per record. Prefer fewer
thorough records and preserve enough output to close the JSON object."""
DISCOVERY = """Return one JSON object with procedures and candidates. Before ranking, inventory up to five
key procedures: inputs, transition or selection rule, when it returns/stops, what the result
guarantees, and which downstream requirement the guarantee leaves open. Include paths/pages.
For each major rule ask whether two cases satisfying that rule can differ in the intended
testing outcome. Check whether retries, fallback or other existing mechanisms recover the gap.
Then output up to three distinct method-boundary candidates, each testing a different procedure or a different controlled input property. Give each one a pair of applicable scenarios, what changes, and what stays fixed. Each has short Chinese
strings rule, trigger, mitigation, consequence, and evidence (specific original paths/pages).
Mark hypotheses as conditional. Prioritize direct consequences of method decisions over
incidental implementation oddities. Keep the entire answer under 2600 characters."""
ROUTES = (
    'Map the principal method objectives to guarantees. Construct a controlled pair that preserves the published aggregate, configuration, or resource allowance while changing an independent property of input structure or representation. Trace the effect through the algorithm and existing safeguards.',
    'Trace acceptance, stopping, allocation and shared-state decisions into their callers. For a selected result, compare two inputs that both satisfy the acceptance rule but differ in what downstream work they exercise. For shared choices, compare components with compatible versus conflicting requirements. Prefer precise source-backed method questions.',
)
ROUTING = """Select at most one high-value unresolved link where additional source evidence
could materially change the diagnosis. Prefer an unresolved link between a central method rule and its downstream objective over an incidental defect. Output only {candidate_id,link,question}. You may choose a procedure ID when an independently
listed procedure has a material gap omitted from the candidate list. Use one exact ID, link
in rule|trigger|mitigation|consequence, and one
specific evidence question. If none is warranted return {}. Do not score or guess answers."""
VERIFY = """Independently answer the assigned question with original paper and code tools.
If the input is a procedure, derive what it establishes, whether operating outside that guarantee
can alter a test outcome, and what existing behavior could refute the concern.
Return a concise result with candidate ID, evidence and conclusion (supports, narrows,
refutes, or remains open). Explicitly note alternatives and any interpretation that remains untested."""
FINAL = """Produce the final JSON report. Trace adopted candidates via origin_ids, and record
brief disposition decisions for routed items. Use independent candidates and the verification
result as leads. Retain distinct evidence-backed diagnoses across different procedures when available; a checked candidate does not automatically displace a distinct one. Keep the rule, trigger, mitigation and downstream outcome together in one record. An unanswered link must remain conditional."""


MECHANISM_ROUTES = (
    """Start from the two mechanisms critical to the claimed benefit. For each, map what the
mechanism preserves or measures, and what it discards or takes as invariant. Independently
vary the structure, distribution, or representation of an input at the same admissibility and
resource budget. Determine the first step where otherwise comparable cases diverge.
Prefer a failure of the implemented method idea over an absent optional feature.""",
    """Start from the two algorithm decisions that most directly control results. Audit a
return, a fixed-size selection, or a shared state decision in its source call path where
applicable. For each rule construct two hypothetical valid cases under the same configuration
and resource budget and trace what the caller would process. For deployment assumptions,
check what changes across valid configurations and whether project code or evidence covers it.
Treat an unresolved implementation discrepancy as a separate diagnosis.""",
)
MECHANISM_DISCOVERY = """Return a compact JSON object {procedures, candidates}. Identify precise
selection/acceptance/representation rules. For each procedure record rule, stop, guarantee,
open, and provenance. Before emitting a candidate, propose two comparable cases, with fields
case_a, case_b, fixed, study_metric. If you cannot justify the claimed difference, mark it
conditional and identify a possible refutation. Explain what an existing mitigation does on
both cases. Output up to four diverse method hypotheses for the central algorithm. All candidates
must have rule, trigger, mitigation, consequence. Use paper_evidence and code_evidence for
actual references. Do not use a missing test or unsupported configuration by itself to infer
a diagnosis. Keep the report under 4300 characters."""
MECHANISM_ROUTING = """Compare the independent procedure maps and candidate pairs. Prioritize a
method assumption on the direct path from an algorithm rule to the paper objective. Ask for
one specific adjudication of which of two controlled cases would behave differently and why.
A frozen procedure can be chosen even if its implication was missed by both workers.
Return only {candidate_id, link, question}, choosing a supplied ID and link from
rule|trigger|mitigation|consequence. Return {} when a check cannot change the answer."""
MECHANISM_FINAL = """Finalize one valid JSON report. Prioritize testable causal limitations on the
method's principal result. For each retained hypothesis integrate the rule, paired cases,
applicable trigger, actual mitigation, downstream consequence, and refutation in one record.
Do not convert missing implementation or weak evidence into a general method limitation.
Preserve a separately evidenced unreviewed item if it addresses a distinct mechanism.
Keep exact original evidence and origin_ids. Use up to three candidates and three boundaries.
"""


def freeze_runtime(output, swarm_source=None):
    if swarm_source:
        prepare_runtime(swarm_source,output,PIN)
    else:
        shutil.copytree(HERE/'vendor-pi-swarm', output)
    shutil.copyfile(HERE/'gap_coordination.mjs', output/'gap_coordination.mjs')
    agent_path = output/'agent.mjs'
    agent = agent_path.read_text()
    default = 'compaction:{enabled:false}'
    if agent.count(default) != 1:
        raise ValueError('Pinned Pi settings hook changed')
    agent_path.write_text(agent.replace(default, 'compaction:cfg.compaction??{enabled:false}'))
    path = output/'swarm.mjs'
    code = path.read_text()
    hooks = {
        'export async function runSwarm(': "import {gapWorkflow} from './gap_coordination.mjs';\nexport async function runSwarm(",
        ' async function runAgent(id,parent,depth,task,inherited=[]){':
            ' const gap=cfg.gapReview?gapWorkflow(cfg.gapReview,emit):null; let summaryRequests=0;\n async function runAgent(id,parent,depth,task,inherited=[]){',
        "session.subscribe(e=>{eventPromises.push(rpc('sdk_event',{agent:id,event:e,observed_epoch:Date.now()/1000}));});":
            '''session.subscribe(e=>{
    if(e.type==='compaction_start')a.compacting=true;
    if(e.type==='compaction_end'){
     a.compacting=false;
     if(e.result)void emit('native_gap_compaction',{agent:id,trigger:e.reason,before:e.result.tokensBefore,estimated_after:e.result.estimatedTokensAfter});
     else void emit('native_gap_compaction_skipped',{agent:id,trigger:e.reason,error:e.errorMessage});
    }
    eventPromises.push(rpc('sdk_event',{agent:id,event:e,observed_epoch:Date.now()/1000}));
   });''',
        'session.agent.streamFunction=async(_,context)=>{':
            'session.agent.streamFunction=async(_,context,options)=>{',
        "if(a.turnLimit!==undefined&&a.turn>=a.turnLimit)throw Error('Agent turn limit exceeded without final');":
            "if(!a.compacting&&a.turnLimit!==undefined&&a.turn>=a.turnLimit)throw Error('Agent turn limit exceeded without final');",
        'const request=hostContext(context),turn=a.turn++;': '''const request=hostContext(context),turn=a.compacting?a.turn:a.turn++;
     if(a.compacting){
      if(summaryRequests>=(cfg.compaction?.maxSummaryRequests??0))throw Error('Native summary request safety budget reached');
      summaryRequests++;
      request.tools=[];
      const cap=Number.isSafeInteger(options?.maxTokens)&&options.maxTokens>0?options.maxTokens:cfg.compaction.summaryMaxTokens;
      request.messages.push({role:'user',content:'CS6223_PI_AUTO_SUMMARY:'+cap});
     }''',
    }
    gap_block = '''     if(gap){
      const completeGap=async text=>{
       await session.prompt(text);
       if(session.agent.state.errorMessage||aborting)throw Error(session.agent.state.errorMessage??'Job cancelled');
       const last=session.messages.at(-1);
       if(last?.role!=='assistant'||last.stopReason!=='stop')throw Error('Nonterminal gap phase');
       const answer=last.content.filter(c=>c.type==='text').map(c=>c.text).join('');
       if(!answer.trim())throw Error('Empty gap phase');
       return answer;
      };
      const resumeGap=(text,turns)=>{
       a.turnLimit=a.turn+turns;
       session.setActiveToolsByName(turns===1?[]:customTools.map(t=>t.name));
       return completeGap(text);
      };
      const answer=await gap({id,task:cfg.task,complete:completeGap,resumePhase:resumeGap,
       startWorker:child=>runAgent(child,id,depth+1,cfg.task)});
      a.status='completed';a.finishReason='stop';
      await emit('agent_finished',{agent:id,parent,answer,finish_reason:'stop',model_replies:a.turn});
      return answer;
     }
'''
    boundary = '     if(review?.fixedDraft){' if '     if(review?.fixedDraft){' in code else '     while(true){'
    hooks[boundary] = gap_block + boundary
    for before, after in hooks.items():
        if code.count(before) != 1:
            raise ValueError('Pinned Pi runtime hook changed: '+before)
        code = code.replace(before, after, 1)
    path.write_text(code)


def freeze_study(output, previous_runs, swarm_source=None, policy="original"):
    output.mkdir(parents=True, exist_ok=False)
    dev = previous_runs/'method-boundary-fixed-draft-v2-teams'
    test = previous_runs/'method-boundary-fixed-draft-v2-grounded'
    for source, papers in [(dev, DEV), (test, TEST)]:
        index = load(source/'input-index.json')
        for case, paper in papers.items():
            folder = output/paper
            folder.mkdir()
            for relative, expected in index.items():
                path = Path(relative)
                if (path.parts[0] != paper or path.parts[1] not in
                    ('paper.json','images','source.json','original-source-packet.txt')):
                    continue
                blob = (source/path).read_bytes()
                if sha(blob) != expected:
                    raise ValueError(f'Original input changed: {path}')
                (output/path).parent.mkdir(exist_ok=True)
                (output/path).write_bytes(blob)
            for filename in ('paper.json','source.json','original-source-packet.txt'):
                if not (folder/filename).is_file():
                    raise ValueError(f'Missing original input for {paper}: {filename}')
    freeze_runtime(output/'runtime',swarm_source)
    for name in FROZEN_FILES:
        shutil.copyfile(HERE/name, output/name)
    common = output/'prompts-joint'
    common.mkdir()
    for name, content in {'system':SYSTEM, 'task':TASK, 'lead':'Use available tools to analyze the task and write the final report.',
                          'worker':'Produce a short evidence report for the parent. Do not write the final report.'}.items():
        (common/f'{name}.txt').write_text(content)
    dump(output/'protocol.json', {
        'version':'cs6223-evidence-gap/7' if policy=='mechanism' else 'cs6223-evidence-gap/6',
        'discovery_policy':policy, 'split':{'dev':DEV, 'test':TEST}, 'conditions':CONDITIONS,
        'reasoning_effort':'max', 'thinking':{'type':'enabled'}, 'model_alias':'x-test-2', 'expected_backend':BACKEND,
        'max_http_requests_per_cell':10, 'max_output_tokens':32768,
        'max_actual_returned_tokens_per_cell':750000, 'closing_reserve_tokens':0,
        'max_report_candidates':3, 'global_model_concurrency':4,
        'per_request_timeout_seconds':360, 'per_cell_wall_seconds':1600,
        'staged_review':{'discovery_per_worker':2,'routing':1,'cross_check':2,'final':1},
        'compaction':{'enabled':True,'reserveTokens':40960,'keepRecentTokens':8000,
                      'maxSummaryRequests':2,'summaryMaxTokens':12288},
        'target_execution':'not_run', 'reference_allowed_in_generation':False,
        'test_exposure':'Known historical pilot papers, held out from tuning of this protocol version.',
    })
    dump(output/'input-index.json', {str(path.relative_to(output)):sha(path.read_bytes())
                                     for path in sorted(output.rglob('*')) if path.is_file()})


def verify_inputs(root):
    index = load(root/'input-index.json')
    for name, digest in index.items():
        if sha((root/name).read_bytes()) != digest:
            raise ValueError(f'Frozen input changed: {name}')
    for name in FROZEN_FILES:
        if sha((HERE/name).read_bytes()) != index[name]:
            raise ValueError(f'Current runner differs from frozen runner: {name}')


def task_with_originals(root, paper):
    folder = root/paper
    meta = load(folder/'source.json')
    text = '\n\n'.join(f"PHYSICAL PDF PAGE {page['page']}\n{page['numbered']}" for page in load(folder/'paper.json'))
    source = (folder/'original-source-packet.txt').read_text()
    task = (root/'prompts-joint/task.txt').read_text()
    return (f"{task}\nPaper ID: {paper}\nPinned repository commit: {meta['commit']}"
            f'\n\nORIGINAL PAPER BEGIN\n{text}\nORIGINAL PAPER END'
            f'\n\nORIGINAL SOURCE EXCERPTS BEGIN\n{source}\nORIGINAL SOURCE EXCERPTS END')


class StudyCell(StreamingCell):
    def __init__(self, root, paper, condition, sem):
        super().__init__(root, paper, condition, sem)
        self.joint = True
        self.evidence.requires_freeze = False

    def cfg(self):
        config = super().cfg()
        config['task'] = task_with_originals(self.root, self.aid)
        config['compaction'] = self.protocol['compaction']
        config['lastTurnPrompt'] = 'Tools are disabled on this reply. Finish the current phase in its requested format.'
        config['remainingPrompt'] = 'You have {n} replies left in this phase.'
        if self.condition == 'single_agent':
            config['limits']['maxTurns'] = 8
        elif self.condition == 'plain_swarm':
            config['leadPrompt'] += (' Delegate original-evidence work to one or two independent workers '
                                     'and incorporate the evidence into the final answer.')
            config['limits'].update(maxDepth=1,maxActive=3,maxTotal=3,maxChildren=2,maxTurns=4,
                                    turnsByRole={'root':4,'worker':2})
        elif self.condition == 'evidence_gap_swarm':
            config['limits'].update(maxDepth=0,maxActive=3,maxTotal=3,maxChildren=2,maxTurns=2)
            config['gapReview'] = dict(routes=ROUTES, discovery=DISCOVERY, routing=ROUTING,
                                       verification=VERIFY, final=FINAL, verificationTurns=2,
                                       coordinatorTask=TASK+'\nPaper ID: '+self.aid)
            if self.protocol.get('discovery_policy')=='mechanism':
                config['gapReview'].update(routes=MECHANISM_ROUTES, discovery=MECHANISM_DISCOVERY,
                                           routing=MECHANISM_ROUTING, final=MECHANISM_FINAL,
                                           candidateLimit=4)
        return config

    def http(self, payload, n):
        last = payload['messages'][-2].get('content') if len(payload['messages'])>=2 else None
        summary = re.fullmatch(r'CS6223_PI_AUTO_SUMMARY:([1-9][0-9]*)',last) if isinstance(last,str) else None
        if summary and not payload.get('tools'):
            payload['max_tokens'] = min(int(summary[1]),self.protocol['compaction']['summaryMaxTokens'])
            payload['reasoning_effort'] = 'high'
        response = super().http(payload, n)
        if response['model'] != BACKEND:
            raise ValueError('Unexpected provider model')
        return response


async def run_once_cell(root, paper, output):
    protocol = load(root/'protocol.json')
    wire = dict(model=protocol['model_alias'], reasoning_effort=protocol['reasoning_effort'],
                thinking=protocol['thinking'], max_tokens=protocol['max_output_tokens'],
                stream=True, stream_options={'include_usage':True},
                messages=[{'role':'system','content':(root/'prompts-joint/system.txt').read_text()},
                          {'role':'user','content':task_with_originals(root,paper)}])
    output.mkdir(exist_ok=False)
    dump(output/'request-01.json', wire)
    dump(output/'input.json',{'request_sha256':sha((output/'request-01.json').read_bytes()), 'request_limit':1})
    await asyncio.to_thread(run_once,output,wire)


async def run(root, split, selected=None, conditions=None):
    verify_inputs(root)
    protocol = load(root/'protocol.json')
    if split == 'test':
        seal = root/'test-release.json'
        if not seal.is_file() or load(seal).get('input_index_sha256') != sha((root/'input-index.json').read_bytes()):
            raise ValueError('Test release requires a matching frozen protocol and reviewed Dev outcomes')
    sem = asyncio.Semaphore(protocol['global_model_concurrency'])
    papers = list(selected or protocol['split'][split].values())
    if not set(papers) <= set(protocol['split'][split].values()):
        raise ValueError(f'Selection outside {split}')

    async def run_cell(paper, condition):
        folder = root/paper/condition
        if (folder/'summary.json').exists():
            return
        if folder.exists():
            raise ValueError(f'Existing nonterminal archive: {folder}')
        if condition == 'api_once':
            async with sem:
                await run_once_cell(root,paper,folder)
        else:
            await StudyCell(root,paper,condition,sem).run()

    for condition in (conditions or CONDITIONS):
        await asyncio.gather(*(run_cell(paper,condition) for paper in papers))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','run'))
    parser.add_argument('root',type=Path)
    parser.add_argument('--previous-runs',type=Path)
    parser.add_argument('--swarm-source',type=Path)
    parser.add_argument('--policy',choices=('original','mechanism'),default='original')
    parser.add_argument('--split',choices=('dev','test'),default='dev')
    parser.add_argument('--papers',nargs='+')
    parser.add_argument('--conditions',nargs='+',choices=CONDITIONS)
    args=parser.parse_args()
    root=args.root.resolve()
    if args.action=='prepare':
        freeze_study(root,args.previous_runs.resolve(),args.swarm_source,args.policy)
    else:
        with (root/'.runner.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            asyncio.run(run(root,args.split,args.papers,args.conditions))
