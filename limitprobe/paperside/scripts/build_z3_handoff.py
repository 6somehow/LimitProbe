"""Source-checked Z3 plans and truthful test-side contract fixtures for two papers.

Reviewed templates enrich existing frozen conformance records. This does not
automatically discover new findings, change old verdicts, or execute target code.
"""
import argparse
import ast
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

from paperprobe.delivery import TEAM, span_evidence
from paperprobe.io import read_json, write_json, file_sha256
sys.path.insert(0,str(TEAM))
from schema.models import Artifact, Finding, Limitation, Region
from adapt_schema02 import functions

ROOT=Path(__file__).resolve().parents[1]


def prefix_reference(values, gamma, strict=False):
    """Independent rational arithmetic, NOT an execution of score_cover_topk."""
    total=Fraction(0)
    for n,value in enumerate(sorted(values,reverse=True),1):
        total+=value
        reached=total>gamma if strict else total>=gamma
        if reached:
            return n
    return len(values)+1


class Sources:
    def __init__(self,repo,commit):
        self.repo,self.commit,self.cache,self.reads=repo,commit,{},[]
        assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==commit
    def code(self,path):
        if path not in self.cache:
            self.cache[path]=subprocess.check_output(['git','-C',str(self.repo),'show',f'{self.commit}:{path}'],text=True)
        return self.cache[path]
    def location(self,path,fn,statement=None):
        source=self.code(path);node=functions(source)[fn]
        if statement:
            expected=ast.dump(ast.parse(statement).body[0],include_attributes=False)
            matches=[n for n in ast.walk(node) if isinstance(n,ast.stmt) and ast.dump(n,include_attributes=False)==expected]
            assert len(matches)==1,(path,fn,statement)
            node=matches[0]
        lines=source.split('\n');lo,hi=node.lineno,node.end_lineno
        snippet='\n'.join(lines[lo-1:hi])
        self.reads.append(dict(repo='primary',commit=self.commit,path=path,start_line=lo,end_line=hi,
                               lines='\n'.join(f'{i}: {lines[i-1]}' for i in range(lo,hi+1))))
        return dict(file=path,line_start=lo,line_end=hi,function=f'{path}::{fn}',snippet=snippet)
    def edge(self,path,caller,callee,target_name,first_arg=None):
        source=self.code(path);fn=functions(source)[caller]
        nodes=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and ast.unparse(n.func)==target_name]
        if first_arg:
            nodes=[n for n in nodes if n.args and ast.unparse(n.args[0])==first_arg]
        assert len(nodes)==1,(caller,target_name)
        node=nodes[0];lines=source.split('\n');lo,hi=node.lineno,node.end_lineno
        self.reads.append(dict(repo='primary',commit=self.commit,path=path,start_line=lo,end_line=hi,
                               lines='\n'.join(f'{i}: {lines[i-1]}' for i in range(lo,hi+1))))
        return dict(caller=f'{path}::{caller}',callee=callee,file=path,line_start=lo,line_end=hi,
                    call='\n'.join(lines[lo-1:hi]),positional_arguments=[ast.unparse(a) for a in node.args],
                    keyword_arguments={k.arg:ast.unparse(k.value) for k in node.keywords},
                    provenance='AST call found at the pinned commit; not a runtime trace')


def flex_plan(source,pages):
    path='flex_prefill/ops/flex_prefill_attention.py'
    target=source.location(path,'score_cover_topk','topk = torch.sum(cumsum_x <= score, dim=-1) + 1')
    ret=source.location(path,'score_cover_topk','return topk')
    fn=source.location(path,'score_cover_topk')
    budget=source.location(path,'get_active_blocks','num_vertical_blocks = score_cover_topk(vertical, gamma) // 128 + 1')
    edges=[source.edge(path,'flex_prefill_attention',f'{path}::get_active_blocks','get_active_blocks'),
           source.edge(path,'get_active_blocks',f'{path}::score_cover_topk','score_cover_topk','vertical')]
    edges[0]['formal_parameter_map']=dict(q='q',k='k',v='v',block_size='block_size',gamma='gamma',tau='tau',
                                        min_budget='ceil(min_budget / block_size)',max_budget='ceil(max_budget / block_size)')
    edges[1]['formal_parameter_map']=dict(x='vertical',score='gamma')
    values=[Fraction(1,512)]*512
    gamma=Fraction(127,512);contrast=Fraction(255,1024)
    arithmetic=dict(method='Independent exact-rational reference/counterfactual calculation; target NOT executed',
                    trigger=dict(gamma=float(gamma),ge_prefix=prefix_reference(values,gamma),strict_prefix=prefix_reference(values,gamma,True)),
                    contrast=dict(gamma=float(contrast),ge_prefix=prefix_reference(values,contrast),strict_prefix=prefix_reference(values,contrast,True)))
    assert arithmetic['trigger']['ge_prefix']==127 and arithmetic['trigger']['strict_prefix']==128
    assert arithmetic['contrast']['ge_prefix']==arithmetic['contrast']['strict_prefix']==128
    lines=pages[5].splitlines()
    lo=next(i for i,line in enumerate(lines,1) if '# Sort vertical and slash attention scores' in line)
    hi=next(i for i,line in enumerate(lines,1) if i>=lo and line.strip().startswith('Ks') and 'min' in line)
    exact_paper=span_evidence([dict(page=6,start_line=lo,end_line=hi)],pages)
    return dict(behavior='M08-B05',target=target,related_locations=[ret,fn,budget],call_chain=edges,
                condition_text='At score_cover_topk, a sorted cumulative probability equals gamma exactly.',
                machine_condition='torch.any(torch.cumsum(torch.sort(x, dim=-1, descending=True).values, dim=-1) == score)',
                trigger=dict(frame='score_cover_topk',arguments=dict(x=dict(shape=[1,1,512],dtype='float32',fill_fraction='1/512'),score_fraction='127/512')),
                contrast=dict(frame='score_cover_topk',arguments=dict(x=dict(shape=[1,1,512],dtype='float32',fill_fraction='1/512'),score_fraction='255/1024')),
                arithmetic=arithmetic,test_family='numerical differential / boundary O3; not exception or branch',
                proposed_oracle=dict(observe='Returned prefix count, not merely whether the helper was reached',
                                     reference='min k with cumulative >= gamma, if Algorithm 3 equation is accepted as normative',
                                     pass_for_candidate='Trigger differs from paper reference; off-equality control agrees',
                                     cannot_establish='No claim about final attention error, latency, selected block set or whole-model correctness'),
                path_conditions=['Public flex_prefill_attention needs batch_size=1, matching q/k lengths and valid head_dim/block_size.',
                                 'q_len must exceed the dense-short-sequence fallback bound.',
                                 'min/max budget clamps and the tau-selected head pattern can mask a helper difference.'],
                blockers=['The paper caption says exceeds gamma while its equation says >= gamma; resolve which is normative before a bug verdict.',
                          'Paper av and code token-score/block-score representations must be aligned; local prefix arithmetic alone is insufficient.',
                          'Helper tensor recipe is concrete; construction of q/k producing it through the public causal attention entry is NOT solved.',
                          'CPU testing may require dependencies/import substitutions. Disclose any extraction/mock and retain D14/fidelity doubts.'],
                current_extraction_paper_evidence=exact_paper,
                plan_state='local_plan_only_requires_custom_oracle_and_semantic_review')


def nn_plan(source,pages):
    path='nnsmith/materialize/torch/symbolnet.py';inp='nnsmith/materialize/torch/input_gen.py'
    target=source.location(path,'SymbolNet.grad_input_gen','return sat_inputs')
    failure_branch=source.location(path,'SymbolNet.grad_input_gen','if sat_inputs is None:\n    TORCH_LOG.debug("[grad] no valid range found!!!")')
    loop=source.location(path,'SymbolNet.grad_input_gen')
    init=source.location(path,'SymbolNet.grad_input_gen','sat_inputs = None')
    unit=source.location(inp,'GradSearch.search_one','timeout_s = None if timeout_ms is None else timeout_ms / 1000')
    edges=[source.edge(inp,'PracticalHybridSearch.search_one',f'{inp}::GradSearch.search_one','GradSearch.search_one'),
           source.edge(inp,'GradSearch.search_one',f'{path}::SymbolNet.grad_input_gen','self.net.grad_input_gen')]
    edges[0]['formal_parameter_map']=dict(self='self',start_inp='start_inp',timeout_ms='timeout_ms')
    edges[0]['path_condition']='self.differentiable is true'
    edges[1]['formal_parameter_map']=dict(init_tensors='start_inp',use_cuda='self.use_cuda',max_time='timeout_ms/1000 when not None')
    exp='experiments/nnsmith_gen_onnx.py'
    call=source.edge(exp,'nnsmith_gen_once',f'{inp}::InputSearchBase.search','searcher.search')
    search=functions(source.code(inp))['InputSearchBase.search']
    supplied=set(call['keyword_arguments']);accepted={a.arg for a in search.args.args+search.args.kwonlyargs}
    unknown=sorted(supplied-accepted)
    assert unknown==['return_list'] and search.args.kwarg is None
    declaration=source.location(inp,'InputSearchBase.search')
    return dict(behavior='M08-B10',target=target,related_locations=[failure_branch,init,loop,unit,declaration],call_chain=edges,
                condition_text='After entry/setup succeeds, the grad_input_gen time budget expires while sat_inputs remains None.',
                machine_condition='sat_inputs is None',
                trigger=dict(frame='PracticalHybridSearch.search_one',arguments=dict(start_inp={'x':dict(shape=[1],dtype='float32',values=[1.0])},timeout_ms=0),
                             model_recipe='A minimal differentiable SymbolNet (e.g. ReLU(x)), CPU; constructor/schedule to be materialized by test agent',
                             prerequisites=['self.differentiable=True','CPU use_cuda=False','Model/optimizer setup must succeed']),
                contrast=dict(frame='PracticalHybridSearch.search_one',arguments=dict(start_inp={'x':dict(shape=[1],dtype='float32',values=[1.0])},timeout_ms=1000),
                              expected_behavior='Valid input may be returned within budget; collect actual runtime evidence, not guaranteed by this recipe'),
                proposed_oracle=dict(observe='Whether failure is raised, the return value, and target-return reachability',
                                     reference='Paper explicitly throws failure on budget exhaustion; pinned code returns sat_inputs (None if no success)',
                                     pass_for_candidate='Zero-budget search reaches return None without the paper failure exception; a successful control is returned normally',
                                     cannot_establish='Do not classify an unrelated setup exception as the claimed failure. None may be a deliberate equivalent failure protocol; review caller policy.'),
                test_family='exception-policy / return-protocol O4 with custom oracle; not reject at a non-raising return',
                path_conditions=['Use the registered search_one entry for the zero-budget local test.',
                                 'InputSearchBase.search(max_time_ms=0) skips its own loop and never calls search_one; it is not an equivalent entry.',
                                 'A positive-budget expiry case is still needed before generalizing beyond the zero-budget boundary.'],
                blockers=['Current harness reject cannot establish an absent exception at a return statement; do not mislabel this as reject.',
                          'CPU model/optimizer fixture has not been built or executed.',
                          'The experiment caller supplies return_list=True to search(), but this pinned inherited signature has no such keyword or **kwargs. Static binding mismatch blocks that experiment route; no runtime TypeError was observed here.'],
                experiment_route_check=dict(call=call,search_signature=declaration,unsupported_keywords=unknown,analysis='Static keyword/signature check only; not executed'),
                additional_paper_evidence=span_evidence([dict(page=7,start_line=43,end_line=53)],pages),
                plan_state='local_plan_only_requires_custom_oracle_and_entry_validation')


def build(aid,repo,pdf,out):
    assert not out.exists(),'Preserve previous Z3 outputs; choose a fresh directory'
    original=ROOT/'handoffs/paper-side-v2'/aid
    art=read_json(original/'artifact.json');source=Sources(repo,art['commit'])
    from pypdf import PdfReader, __version__ as pdf_parser_version
    assert file_sha256(pdf)==read_json(ROOT/'workstreams/zhaopeng/team-reviewed.json')[aid]['pdf_sha256']
    pages=[p.extract_text() or '' for p in PdfReader(pdf).pages]
    rows=read_json(original/'conformance.json');claims={c['claim_id']:c for c in read_json(original/'paper_side.json')['claims']}
    plan=(flex_plan if aid=='flexprefill' else nn_plan)(source,pages)
    selected=next(r for r in rows if r['id']==plan['behavior'])
    limitation=next(l for l in read_json(original/'limitations.json') if l['limitation_id']==f'{aid}-gap-{plan["behavior"]}')
    native=read_json(TEAM/'results/step4'/aid/'limitations_for_tests.json')
    linked=[f['finding_id'] for f in native['findings'] if limitation['limitation_id'] in f['limitation_ids']]
    fid=f'{aid}-Z3-{plan["behavior"]}'
    # Keep the paper origin, category and original claim identity. A custom oracle is
    # not representable as reject/path_change in the current effect-only contract.
    limitation=dict(limitation,schema_version='0.2.0',code_evidence=[plan['target']]+plan['related_locations'][:2],
                    condition_text=plan['condition_text'],condition=None,effect_type='other',
                    notes=(limitation.get('notes') or '')+' Z3 reviewed locations and plans; not target-executed.')
    current_evidence=plan.pop('current_extraction_paper_evidence',claims[selected['claim_id']]['evidence'])+plan.pop('additional_paper_evidence',[])
    limitation['paper_evidence']=current_evidence
    limitation=Limitation.model_validate(limitation).model_dump(mode='json')
    finding=Finding(finding_id=fid,artifact_id=aid,category='impl_deviates',level='L2',
                    limitation_ids=[limitation['limitation_id']],scope_status='unknown',effect_type='other',
                    summary=selected['requirement'],witness_hint=dict(format='witness-v2',kind='input_value',status='unknown',
                    trigger=None,contrast=None,effect_location=plan['target'],
                    location=f'{plan["target"]["file"]}:{plan["target"]["line_start"]}',function=plan['target']['function'],
                    z3_hint_file='testability_hints.json',z3_case_id=fid,
                    note='Local recipe in testability_hints.json; not a solver-certified public-entry witness'),
                    confidence='llm_assisted',priority=2,rationale='Reviewed Z3 contract fixture derived from an existing frozen behavior; not a production step4 run.',
                    review='unreviewed',review_note='Agent source-assisted review only; see blockers before accepting the static discrepancy.').model_dump(mode='json')
    region=Region(region_id=f'Z3-{plan["behavior"]}',artifact_id=aid,entry_point=plan['call_chain'][0]['caller'],
                  condition=dict(expr=plan['machine_condition'],params=[],path_prefix=[]),outcome='suspicious',
                  location=plan['target'],call_chain=[plan['call_chain'][0]['caller']]+[e['callee'] for e in plan['call_chain']],
                  provenance='llm',notes='Proposed Region sidecar only. Not fed into the native adapter or claimed as a code-origin discovery.').model_dump(mode='json')
    plan.update(finding_id=fid,claim_id=selected['claim_id'],limitation_id=limitation['limitation_id'],
                source_step4_finding_ids=linked,original_verdict=selected['artifact']['verdict'],
                paper_evidence=current_evidence,archived_claim_evidence=claims[selected['claim_id']]['evidence'],
                proposed_region=region,effect_type='other',target_execution='not_run',model_api_calls=0)
    for e in plan['paper_evidence']:
        import re
        page=int(re.search(r'p\.(\d+)',e['locator'])[1]);assert e['quote'] in pages[page-1]
    registry={e['evidence_id']:e for e in read_json(original/'code_evidence_registry.json')}
    hints=[]
    for row in rows:
        a=row['artifact']
        if a['review_state']!='completed' or a['verdict']=='supports':continue
        hint=dict(behavior=row['id'],claim_id=row['claim_id'],original_verdict=a['verdict'],requirement=row['requirement'],
                  discrepancy=a['discrepancy'],source_navigation=[registry[r] for r in row['evidence_registry_ids']['artifact']],
                  effect_type='other',target_execution='not_run')
        if row['id']==plan['behavior']:hint.update(plan)
        elif aid=='flexprefill' and row['mechanism_id']=='M11':
            hint.update(plan_state='needs_semantic_review',trigger=None,
                        testability_note='A mathematical proof/KKT derivation is not automatically an executable promise. First justify why a runtime implementation is required; no test location is fabricated.')
        elif aid=='flexprefill' and row['id']=='M12-A05':
            hint.update(plan_state='needs_semantic_review',trigger=None,
                        testability_note='Reported A100 experiment hardware need not be enforced by a script. Obtain historical environment evidence before calling this an implementation gap.')
        elif aid=='nnsmith' and row['id']=='M05-B08-R02':
            hint.update(plan_state='needs_semantic_review',trigger=None,
                        testability_note='Initial uniform shuffle followed by nested prefix halving may be distribution-equivalent to randomly choosing half at each step. Check solver/order/timeout assumptions before treating this as a discrepancy.')
        else:
            hint.update(plan_state='needs_custom_oracle_and_path_review',trigger=None,
                        testability_note='Cited spans are navigation, not a selected effect statement. Materialize input/path and oracle before test execution; no fabricated solved witness.')
        hints.append(hint)
    out.mkdir(parents=True)
    write_json(out/'artifact.json',Artifact.model_validate(art).model_dump(mode='json'))
    write_json(out/'limitations_for_tests.json',dict(schema_version='0.2.0',witness_format='witness-v2',
               note='Z3 PAPER-ORIGIN CONTRACT FIXTURE, not regenerated production step4 output. Cross-reference source_step4_finding_ids in sidecar. No target execution.',
               findings=[dict(finding,limitations=[limitation],verifications=[])]))
    write_json(out/'testability_hints.json',dict(version='paperside-z3/1',artifact_id=aid,
               method='Reviewed source-assisted Z3 templates/triage, not a new model extraction run; original verdicts preserved',hints=hints))
    write_json(out/'source_reads.json',list({(r['path'],r['start_line'],r['end_line']):r for r in source.reads}.values()))
    write_json(out/'provenance.json',dict(schema='0.2.0',target_commit=art['commit'],pdf_sha256=file_sha256(pdf),
               conformance_sha256=file_sha256(original/'conformance.json'),source_step4_file_sha256=file_sha256(TEAM/'results/step4'/aid/'limitations_for_tests.json'),
               existing_negative_behaviors=len(hints),expanded_cases=1,pdf_parser=dict(package='pypdf',version=pdf_parser_version),
               model_api_calls=0,target_execution='not_run',
               source='Teams CONTRACT_TEST_REPORT.md and REQUESTS_TO_STEP4.md read 2026-11-16; consumer source pinned separately in probe result'))
    (out/'README.md').write_text(f'# {aid} · Z3交接\n\n先看 `testability_hints.json` 的主案例与边界，再看 `limitations_for_tests.json` 的原生契约样例。这里是论文侧fixture，不是重跑或覆盖step4结果。\n\n论文origin保持paper；effect保持other，因为返回值/数值oracle尚不受当前异常/分支检查支持。`consumer_contract_check.json`和`contract_output/`记录真实消费者读取与未运行原因；不包含测试结果或置信度评分。\n\n原有{len(hints)}条负项逐条留存triage，其中1条给出详细局部输入与源码调用链，其余未完成输入构造或语义复核时明确留待办，不伪装成已求解witness。\n')
    print(f'Z3 {aid}: {len(hints)} negative behaviors triaged; 1 source-checked expanded case; target not_run')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--paper',choices=['flexprefill','nnsmith'],required=True)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--pdf',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.paper,a.repo.resolve(),a.pdf.resolve(),a.out.resolve())
