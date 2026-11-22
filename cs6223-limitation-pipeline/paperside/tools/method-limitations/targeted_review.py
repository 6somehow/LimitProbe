"""Run a Dev-only paired Pi experiment from one frozen, evidence-grounded draft."""
import argparse
import asyncio
import fcntl
import json
from pathlib import Path

from audit_evidence import unpack
from corpus_ledger import load
from pilot import HERE, dump, sha
from swarm_evaluation import final_response
from swarm_study import DEV, StudyCell, freeze_study, verify_inputs


DRAFT = """Build the initial report before any review. Follow principal method decisions from
input through selection, stopping or transformation, to what consumes the result. Inspect
implementation bodies and their callers, and compare what the rule guarantees with what
the paper measures. Before choosing findings, consider two admissible cases that differ in
one property while the relevant budget or configuration is fixed. Look for evidence that
the method or an existing mitigation treats them differently. Keep reasoning conditional
where appropriate. Return the required report and one additional top-level object,
review_target: {anchor, question}. The anchor identifies one actual method rule with a
specific paper or Git source reference, even if there is no retained limitation yet.
Ask one answerable question about a missing link between that rule and a consumer,
mitigation or measured outcome. The question must not assume that a limitation exists."""

REVIEW = """Answer only the frozen draft's review_target question, using the original
paper and Git tools. Open the cited anchor and trace the immediate producer or consumer.
Check whether existing recovery or compensation covers the same condition. If the assumed
path is wrong, say so and cite the actual route. Return a compact memo with verdict,
what was read (physical page or exact Git path and lines), what that evidence establishes,
and the strongest remaining alternative. The draft is an unverified lead. Do not search
for unrelated new candidates. Preserve distinctions between measured and hypothetical effects."""

FINAL = """Write the required JSON report with the draft and the evidence check.
Only adopt a change that follows from the original evidence. Follow the checked link through
to the actual downstream use, and keep any unresolved effect conditional. Retain independent
well-supported draft findings. Prefer an exact chain and its controlled comparison to extra
candidates. Reopen the source if the memo attribution is unclear. Set review_disposition to
adopted, narrowed, refuted, or unresolved, and include one sentence in review_reason."""

MODES = ('self_review', 'delegated_review')
PHASES = ('frozen_draft', *MODES)
PROMPTS = {'draft':DRAFT, 'review':REVIEW, 'final':FINAL}
METHOD_PROMPTS = {
    'draft': """You are the lead investigator. Start from the method's main claimed outcome and
one actual paper evaluation or deployment path. Read the method, the evaluated configuration,
and at least one relevant algorithm, figure or table. Trace the path from the outer entry to
the rule that selects, transforms or stops, then to the first downstream use. Establish
which admissible inputs reach that path and what the rule guarantees there.

Before selecting candidates, contrast two cases within that same path and scope. Hold the
resource allowance and relevant configuration fixed. Vary one property that the method
does not preserve, measure or distinguish. Identify the first operation where the cases
diverge, what an existing safeguard can recover, and the measured or testable effect on
the paper's outcome. Examine an ordinary successful run before exploring error paths.
An implementation mismatch or an untested setting may be worth recording as a boundary.
It takes a separate causal argument to show that the method itself has a limitation.

Return the required report and one top-level review_target object with anchor and question.
The anchor must give a paper or Git reference and identify the relevant ordinary path.
The question must locate one unresolved link that would change the strongest candidate
about the paper's main outcome. Ask which behavior occurs, under which condition, and
what would count against the diagnosis. Only route a failure or fallback branch if you
can show that the paper's evaluated path reaches it under the specified conditions.
If you do not have a defensible candidate, audit the guarantee of the most important rule.""",
    'review': """You are the evidence investigator. Treat the frozen draft as a hypothesis.
Answer the assigned review_target question with original paper and Git evidence. First
verify whether the anchor is on the normal evaluated call path and whether the proposed
contrast stays within the paper's scope. Read the decision and the first consumer. Trace
both cases under the same budget and configuration. Check existing recovery, approximation
or an alternative explanation before judging the downstream effect. If the assigned branch
is off-path, say so and check the corresponding normal path of the same mechanism.

Return a compact memo with anchor, applicability, first_divergence, mitigation, consequence,
verdict, evidence and falsifier. Each item of evidence gives an original page or Git path
and line range and the fact it establishes. Distinguish an observed effect from a prediction
that needs a test. A verdict can support, narrow, refute or leave the proposed link open.
Concentrate on this link and its consumer. Leave unknown facts explicit and avoid adding
unrelated candidates.""",
    'final': """You are responsible for the final diagnosis. Use the frozen draft and the evidence
memo as leads. Rank candidates by how directly the method rule affects the paper's claimed
outcome through the verified execution path. For each retained method limitation, join
the rule, both admissible cases, the first divergence, the mitigation and the downstream
effect in one record. State what stays fixed, provide a measurable comparison, and name
the result that would refute the diagnosis. Cite only evidence that supports the stated
link. If a consequence has not been measured, state it as a conditional hypothesis.

Put artifact-only differences, off-path fallbacks and evaluation scope gaps in
known_boundaries unless the main-path causal link is established. Preserve a separate
well-supported method candidate from the draft if it addresses another mechanism.
Set review_disposition to adopted, narrowed, refuted or unresolved, and explain exactly
which link the memo changed in review_reason. Return the required report JSON."""
}
POLICIES = {'original':PROMPTS, 'method-path':METHOD_PROMPTS}


def prepare(root, previous_runs, swarm_source=None, policy='original'):
    freeze_study(root, previous_runs, swarm_source)
    protocol = load(root/'protocol.json')
    prompts = POLICIES[policy]
    protocol.update(version='cs6223-targeted-review/1', prompt_policy=policy,
                    split={'dev':DEV}, conditions=list(PHASES),
                    max_http_requests_per_cell=7, max_actual_returned_tokens_per_cell=460000,
                    global_model_concurrency=4, per_cell_wall_seconds=1350,
                    staged_review={'draft':4,'review':3,'final':2},
                    prompt_sha256={name:sha(prompt.encode()) for name,prompt in prompts.items()},
                    runner_sha256=sha(Path(__file__).read_bytes()))
    for name, prompt in prompts.items():
        (root/'prompts-joint'/f'targeted-{name}.txt').write_bytes(prompt.encode())
    dump(root/'protocol.json',protocol)
    index = load(root/'input-index.json')
    for name, digest in protocol['prompt_sha256'].items():
        index[f'prompts-joint/targeted-{name}.txt'] = digest
    index['protocol.json'] = sha((root/'protocol.json').read_bytes())
    dump(root/'input-index.json',index)


def frozen_draft(folder):
    raw = folder/'final.txt'
    summary = load(folder/'summary.json')
    if final_response(folder,summary,raw) is None:
        return None
    try:
        report, _ = unpack(raw.read_text())
    except (TypeError, ValueError):
        return None
    if not isinstance(report,dict):
        return None
    target = report.get('review_target')
    if (report.get('paper_id') != summary['paper'] or report.get('target_execution') != 'not_run'
        or not isinstance(target,dict)
        or any(not isinstance(target.get(key),str) or not 8 <= len(target[key].strip()) <= 900
               for key in ('anchor','question'))):
        return None
    return report, sha(raw.read_bytes())


class TargetedCell(StudyCell):
    def __init__(self, root, paper, phase, sem, draft=None):
        super().__init__(root,paper,phase,sem)
        self.draft = draft

    def cfg(self):
        config = super().cfg()
        turns = self.protocol['staged_review']
        prompts = {name:(self.root/'prompts-joint'/f'targeted-{name}.txt').read_text()
                   for name in self.protocol['prompt_sha256']}
        config['leadPrompt'] = config['workerPrompt'] = 'Use the original evidence and complete the requested phase.'
        if self.draft is None:
            config['task'] += '\n\nPHASE: shared lead draft\n' + prompts['draft']
            config['limits']['maxTurns'] = turns['draft']
            return config
        report, digest = self.draft
        delegated = self.condition=='delegated_review'
        config['limits'].update(maxActive=2 if delegated else 1, maxTotal=2 if delegated else 1,
                                maxTurns=turns['review'])
        config['gapReview'] = dict(mode='delegate' if delegated else 'self', draft=report, draftSha256=digest,
                                   verification=prompts['review'], final=prompts['final'], verificationTurns=turns['review'],
                                   finalTurns=turns['final'])
        return config


def audit_receipt(folder, draft):
    report, digest = draft
    raw = folder/'final.txt'
    summary = load(folder/'summary.json')
    number = final_response(folder,summary,raw)
    if number is None:
        return dict(state='failed',requests=summary['requests'])
    events = [json.loads(line) for line in (folder/'event.jsonl').read_text().splitlines()]
    receipts = [e for e in events if e['kind']=='frozen_draft_review_received']
    wire = load(folder/f'request-{number:02}.json')
    blocks = [m['content'].rpartition('\n\n')[2] for m in wire['messages']
              if m['role']=='user' and isinstance(m.get('content'),str)
              and 'PHASE: frozen draft final synthesis' in m['content']]
    try:
        answer, _ = unpack(raw.read_text())
    except ValueError:
        answer = None
    expected = 'root.1' if folder.name=='delegated_review' else 'root'
    if (len(receipts)!=1 or len(blocks)!=1 or receipts[0]['reviewer']!=expected
        or receipts[0]['draft_sha256']!=digest):
        raise ValueError(f'Missing or inconsistent review provenance: {folder}')
    delivered = json.loads(blocks[0])
    if (delivered['draft_sha256']!=digest or delivered['draft']!=report
        or delivered['review']!=receipts[0]['answer']):
        raise ValueError(f'Final request did not receive the exact frozen memo: {folder}')
    structurally_complete = (isinstance(answer,dict) and answer.get('paper_id')==summary['paper']
                            and answer.get('target_execution')=='not_run'
                            and all(isinstance(answer.get(k),list) for k in ('candidates','known_boundaries')))
    if not structurally_complete:
        return dict(state='invalid_report',requests=summary['requests'],final_sha256=sha(raw.read_bytes()))
    return dict(state='complete', reviewer=expected, final_request=number, draft_sha256=digest,
                final_sha256=sha(raw.read_bytes()), review_disposition=answer.get('review_disposition'),
                requests=summary['requests'], tokens=summary['actual_returned_total_tokens'])


async def run(root, draft_only=False):
    verify_inputs(root)
    protocol = load(root/'protocol.json')
    if protocol.get('runner_sha256')!=sha(Path(__file__).read_bytes()) or protocol['split']!={'dev':DEV}:
        raise ValueError('Run requires the frozen Dev-only targeted review protocol')
    sem = asyncio.Semaphore(protocol['global_model_concurrency'])

    async def cell(paper, phase, draft=None):
        folder = root/paper/phase
        if not (folder/'summary.json').exists():
            if folder.exists():
                raise ValueError(f'Existing nonterminal archive: {folder}')
            await TargetedCell(root,paper,phase,sem,draft).run()
        return folder

    async def pair(paper):
        draft = frozen_draft(await cell(paper,'frozen_draft'))
        if draft is None:
            return paper, dict(state='blocked_by_draft')
        folders = await asyncio.gather(*(cell(paper,mode,draft) for mode in MODES))
        return paper, {folder.name:audit_receipt(folder,draft) for folder in folders}

    if draft_only:
        return await asyncio.gather(*(cell(paper,'frozen_draft') for paper in DEV.values()))
    results = dict(await asyncio.gather(*(pair(paper) for paper in DEV.values())))
    dump(root/'pair-audit.json',results)
    return results


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('root',type=Path)
    parser.add_argument('--previous-runs',type=Path,default=HERE.parents[1]/'runs')
    parser.add_argument('--swarm-source',type=Path)
    parser.add_argument('--prompt-policy',choices=POLICIES,default='method-path')
    parser.add_argument('--draft-only',action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action=='prepare':
        prepare(root,args.previous_runs,args.swarm_source,args.prompt_policy)
    else:
        with (root/'.runner.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
            asyncio.run(run(root,args.draft_only))
