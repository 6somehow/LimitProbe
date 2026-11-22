"""Audit frozen inputs, actual budgets, tool restrictions and observed delegation."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import unicodedata


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def norm(s):
    # Auxiliary layout match only: preserve the original quotation in every record.
    s=re.sub(r'(?<=\w)[-\u00ad]\s*\n\s*(?=\w)','',unicodedata.normalize('NFKC',s))
    return ''.join(s.split()).casefold()

def audit(root, selected_paper=None):
    protocol=load(root/'protocol.json');frozen=load(root/'input-index.json')
    assert all(sha(root/p)==h for p,h in frozen.items()),'Frozen input changed'
    papers=protocol['papers']
    if selected_paper is not None:
        assert selected_paper in papers, selected_paper
        papers=[selected_paper]
    summaries=[]
    for aid in papers:
        pages=load(root/aid/'paper.json')
        for condition in protocol['conditions']:
            folder=root/aid/condition;summary=load(folder/'summary.json');cfg=load(folder/'config.json')
            requests=sorted(folder.glob('request-[0-9][0-9].json'));responses=sorted(folder.glob('response-[0-9][0-9].json'))
            assert len(requests)==summary['requests']<=16
            request_map=load(folder/'request-map.json');wire_by_n={int(p.stem.split('-')[-1]):load(p) for p in requests}
            maps={r['request']:r for r in request_map};thinking_replays=0
            for req in requests:
                wire=load(req)
                assert wire['model']=='x-test-2'
                assert wire['max_tokens']==protocol['max_output_tokens']
                system=wire['messages'][0]
                assert system['role']=='system' and system['content'].startswith(cfg['systemPrompt'])
                assert system['content'][len(cfg['systemPrompt']):].strip()==f"<cwd>\n{cfg['cwd']}\n</cwd>", 'Unexpected personal/system context'
                if protocol.get('thinking'):
                    assert wire['thinking']==protocol['thinking'] and wire['reasoning_effort']==protocol['reasoning_effort']
                n=int(req.stem.split('-')[-1])
                if cfg.get('paperOnlyWorkers') and maps[n]['agent']!='root':
                    assert not ({t['function']['name'] for t in wire.get('tools',[])} & {'list_repo','search_repo','read_repo'})
            for response in responses:
                n=int(response.stem.split('-')[-1]);message=load(response)['choices'][0]['message']
                reasoning={k:v for k,v in message.items() if k in ['reasoning','reasoning_content','reasoning_details'] and v}
                later=[i for i in wire_by_n if i>n and maps[i]['agent']==maps[n]['agent']]
                if reasoning and later and message.get('tool_calls'):
                    next_wire=wire_by_n[min(later)]
                    ids={c['id'] for c in message['tool_calls']}
                    match=[m for m in next_wire['messages'] if m['role']=='assistant' and {c['id'] for c in m.get('tool_calls',[])}==ids]
                    assert len(match)==1 and all(match[0].get(k)==v for k,v in reasoning.items()),'Provider reasoning lost or changed'
                    thinking_replays+=1
            events=[json.loads(x) for x in (folder/'event.jsonl').read_text().splitlines()]
            agents=[e for e in events if e.get('kind')=='agent_started']
            spawns=[e for e in events if e.get('kind')=='child_spawned']
            assert all(not s['fork_messages'] for s in spawns),'Independent worker unexpectedly inherited parent'
            tools=load(folder/'tools.json')
            assert all(t['name'] in ['read_paper','freeze_hypotheses','list_repo','search_repo','read_repo'] for t in tools)
            repo_tools={'list_repo','search_repo','read_repo'}
            if condition=='paper_only_swarm':
                assert all(t['name']=='read_paper' for t in tools)
                assert all({t['function']['name'] for t in q.get('tools',[])} <= {'read_paper','spawn'}
                           for q in wire_by_n.values())
            if condition=='joint_swarm_goal':
                for agent in {row['agent'] for row in maps.values()}:
                    first=min(n for n,row in maps.items() if row['agent']==agent)
                    visible={t['function']['name'] for t in wire_by_n[first].get('tools',[])}
                    assert repo_tools <= visible and 'freeze_hypotheses' not in visible
                assert not any(t['name']=='freeze_hypotheses' for t in tools)
            if cfg.get('paperOnlyWorkers'):
                source_calls=[t for t in tools if t['name'] in repo_tools]
                assert all(t['agent']=='root' for t in source_calls)
                if source_calls:
                    assert any(t['agent']=='root' and t['name']=='freeze_hypotheses' for t in tools)
                    # Tool completion order is concurrent. The host gate is set before
                    # the checkpoint is returned, so a source call can share its batch.
                    root_calls=[]
                    for response in responses:
                        n=int(response.stem.split('-')[-1])
                        if maps[n]['agent']=='root':
                            names={t['function']['name'] for t in load(response)['choices'][0]['message'].get('tool_calls',[])}
                            root_calls.append(names)
                    freeze_turn=next(i for i,names in enumerate(root_calls) if 'freeze_hypotheses' in names)
                    refused_path=folder/'tool-errors.jsonl'
                    refused=[json.loads(row) for row in refused_path.read_text().splitlines()] if refused_path.exists() else []
                    earlier_attempts=sum(len(names & repo_tools) for names in root_calls[:freeze_turn])
                    assert earlier_attempts<=sum(t['agent']=='root' and t['error']=='Freeze paper-first hypotheses before repository access' for t in refused)
            token_sum=sum(load(p).get('usage',{}).get('total_tokens',0) for p in responses)
            assert token_sum==summary['actual_returned_total_tokens']
            candidate_audit=[]
            final_path=folder/'final.txt'
            final_wire_verified=False
            if final_path.exists():
                root_responses=[p for p in responses if maps[int(p.stem.split('-')[-1])]['agent']=='root']
                if not root_responses:
                    raise ValueError(f'Missing raw response for final report: {folder}')
                last_root_message=load(root_responses[-1])['choices'][0]['message']['content']
                final_bytes=final_path.read_bytes()
                if final_bytes != last_root_message.encode() or final_bytes != load(folder/'result.json')['answer'].encode():
                    raise ValueError(f'Final report differs from the API response: {folder}')
                final_wire_verified=True
                original=final_bytes.decode().strip()
                try:
                    result=json.loads(original.removeprefix('```json').removesuffix('```'))
                    records=[(h['id'],h) for h in result['candidates']]+[(f'K{i}',h) for i,h in enumerate(result.get('known_boundaries',[]),1)]
                    for ident,h in records:
                        quotes=[]
                        for e in h.get('paper_evidence',[]):
                            matches=[p['page'] for p in pages if e['quote'] and norm(e['quote']) in norm(p['text'])]
                            quotes.append(dict(reported_page=e['page'],normalized_exact_pages=matches,quote=e['quote'],semantic_review='still_required'))
                        candidate_audit.append(dict(id=ident,title=h['title'],quotes=quotes))
                except Exception:pass
            out=dict(paper=aid,condition=condition,requests=len(requests),response_count=len(responses),actual_returned_tokens=token_sum,
                     returned_models=sorted({load(p).get('model','unknown') for p in responses}),
                     reasoning_tokens=sum((load(p).get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens',0) or 0 for p in responses),
                     verified_reasoning_replays=thinking_replays,
                     final_sha256=sha(final_path) if final_wire_verified else None,final_wire_verified=final_wire_verified,
                     actual_agents=len(agents),actual_spawns=len(spawns),collaboration_adopted=bool(spawns),
                     terminal_finish_reasons=[dict(agent=e['agent'],finish_reason=e.get('finish_reason')) for e in events if e.get('kind')=='agent_finished'],
                     image_reads=sum(t['name']=='read_paper' for t in tools),source_reads=sum(t['name']=='read_repo' for t in tools),
                     task_tools_allowlisted=True,independent_workers=all(not s['fork_messages'] for s in spawns),
                     target_execution='not_run',candidate_quote_audit=candidate_audit,run_errors=summary['errors'])
            summaries.append(out)
    result=dict(frozen_inputs_match=True,reference_inputs='Not supplied; only generic prompts, original paper and pinned author blobs reachable',
                important_limit='This audit checks recorded inputs and tool boundaries, not model pretraining or independent semantic correctness',cells=summaries)
    suffix=f'-{selected_paper}' if selected_paper is not None else ''
    (root/f'audit{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    # Freeze every original final before any reference comparison or semantic review.
    (root/f'final-index{suffix}.json').write_text(json.dumps({f"{c['paper']}/{c['condition']}/final.txt":c['final_sha256'] for c in summaries if c['final_sha256']},indent=2)+'\n')
    print(json.dumps([{k:c[k] for k in ['paper','condition','requests','actual_agents','actual_spawns','image_reads','source_reads']} for c in summaries],ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--paper');args=p.parse_args();audit(args.root,args.paper)
