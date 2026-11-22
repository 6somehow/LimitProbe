"""Exercise routing and independent sessions through the actual Pi SDK without network."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pilot
from swarm_evaluation import final_response, gap_trace, select_dev_method, source_evidence, summarize
from swarm_study import BACKEND, CONDITIONS, DEV, StudyCell, freeze_study, run
from targeted_review import MODES, TargetedCell, audit_receipt, frozen_draft, prepare as prepare_review


class GapProtocol(unittest.TestCase):
    def test_targeted_review_preserves_exact_draft_and_memo_in_both_arms(self):
        async def exercise(root):
            class Fake(TargetedCell):
                def http(self, wire, number):
                    paper = dict(paper_id='nnsmith',target_execution='not_run',candidates=[],known_boundaries=[])
                    content = '\n'.join(m['content'] for m in wire['messages']
                                        if m['role']=='user' and isinstance(m['content'],str))
                    last_phase = content.rpartition('PHASE: ')[2]
                    if last_phase.startswith('frozen draft final synthesis'):
                        answer = paper | {'review_disposition':'narrowed'}
                    elif last_phase.startswith('frozen draft evidence check'):
                        answer = dict(verdict='fixture memo')
                    else:
                        answer = paper | {'review_target':dict(anchor='Fixture paper page 4',
                                                               question='Which function consumes this output?')}
                    response = dict(model=BACKEND,choices=[dict(finish_reason='stop',
                                    message=dict(role='assistant',content=json.dumps(answer)))])
                    pilot.dump(self.out/f'request-{number:02}.json',wire)
                    pilot.dump(self.out/f'response-{number:02}.json',response)
                    return response

            sem = asyncio.Semaphore(2)
            with patch.object(pilot,'secret_env',return_value={'SOCLAAS_API_KEY':'fixture'}):
                lead = Fake(root,'nnsmith','frozen_draft',sem)
                await lead.run()
                draft = frozen_draft(lead.out)
                self.assertIsNotNone(draft)
                for mode, reviewer in zip(MODES,('root','root.1')):
                    stage = Fake(root,'nnsmith',mode,sem,draft)
                    await stage.run()
                    receipt = audit_receipt(stage.out,draft)
                    self.assertEqual(receipt['reviewer'],reviewer)
                    self.assertEqual(receipt['state'],'complete')
                    self.assertEqual(receipt['draft_sha256'],draft[1])
                    self.assertEqual(receipt['requests'],2)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)/'review'
            inputs = Path(os.environ.get('CS6223_STUDY_INPUTS',pilot.MODULE/'runs'))
            source = os.environ.get('CS6223_SWARM_SOURCE')
            prepare_review(root,inputs,Path(source) if source else None)
            asyncio.run(exercise(root))

    def test_standalone_agent_has_final_writer_role(self):
        async def execute(root):
            class Fake(StudyCell):
                def http(self,payload,number):
                    user = '\n'.join(m['content'] for m in payload['messages']
                                     if m['role']=='user' and isinstance(m['content'],str))
                    if 'write the final report' not in user or 'short evidence report for the parent' in user:
                        raise AssertionError('Standalone agent received worker prompt')
                    body = dict(paper_id='nnsmith',candidates=[],known_boundaries=[],target_execution='not_run')
                    return {'model':BACKEND,'choices':[{'finish_reason':'stop',
                        'message':{'role':'assistant','content':json.dumps(body)}}], 'usage':{'total_tokens':3}}
            with patch.object(pilot,'secret_env',return_value={'SOCLAAS_API_KEY':'fixture'}):
                outcome = await Fake(root,'nnsmith','single_agent',asyncio.Semaphore(1)).run()
            self.assertEqual(outcome['returncode'],0,outcome)
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)/'study'
            inputs = Path(os.environ.get('CS6223_STUDY_INPUTS',pilot.MODULE/'runs'))
            source = os.environ.get('CS6223_SWARM_SOURCE')
            freeze_study(root,inputs,Path(source) if source else None)
            asyncio.run(execute(root))

    def test_summary_budget_does_not_change_task_budget(self):
        cell = StudyCell.__new__(StudyCell)
        cell.protocol = {'compaction':{'summaryMaxTokens':12288}}
        task = {'messages':[{'role':'user','content':'ordinary task'}],
                'max_tokens':32768,'reasoning_effort':'max'}
        summary = task | {'messages':[{'role':'user','content':'CS6223_PI_AUTO_SUMMARY:8192'}, {'role':'user','content':'run budget note'}]}
        with patch('direct.StreamingCell.http',return_value={'model':BACKEND}) as transport:
            cell.http(task,1)
            cell.http(summary,2)
        self.assertEqual(transport.call_args_list[0].args[0]['max_tokens'],32768)
        self.assertEqual(transport.call_args_list[0].args[0]['reasoning_effort'],'max')
        self.assertEqual(transport.call_args_list[1].args[0]['max_tokens'],8192)

    def test_cross_worker_evidence_is_consumed_by_final(self):
        async def smoke(root):
            class FakeCell(StudyCell):
                def cfg(self):
                    config = super().cfg()
                    config['compaction'] = config['compaction'] | {'keepRecentTokens':8}
                    return config

                def http(self, payload, request_number):
                    content = '\n'.join(message['content'] for message in payload['messages']
                                        if message['role']=='user' and isinstance(message['content'],str))
                    candidates = [{'rule':'a rule', 'trigger':'a trigger', 'mitigation':'unknown',
                                   'consequence':'a consequence','evidence':'needs an original check',
                                   'lens':'coverage','invariant':'same control','case_b':'fixture case B'}]
                    summary_only = any(isinstance(m.get('content'),str) and m['content'].startswith('CS6223_PI_AUTO_SUMMARY:') for m in payload['messages'])
                    if summary_only:
                        response = {'summary':'fixture native Pi summary'}
                    elif 'PHASE: final synthesis' in content:
                        self.assert_final(content)
                        response = {'paper_id':'nnsmith','candidates':[{'id':'H1','origin_id':'root.1#1'}], 'known_boundaries':[],
                                    'target_execution':'not_run'}
                    elif 'PHASE: cross-worker verification' in content:
                        response = {'check':'fixture verification receipt'}
                    elif 'PHASE: route an evidence gap' in content:
                        response = {'candidate_id':'root.1#1','link':'mitigation',
                                    'question':'What covers this trigger?'}
                    else:
                        if 'root.1#1' in content or 'fixture verification receipt' in content:
                            raise AssertionError('Independent discovery received other phase output')
                        response = candidates + [{'unexpected_rule_field':'candidate the parser must reject'}]
                    message = dict(role='assistant',content=json.dumps(response))
                    who = self.wire_ids[request_number-1]['agent']
                    if (who=='root.2' and 'PHASE: independent discovery' in content
                        and 'PHASE: cross-worker verification' not in content and not summary_only
                        and not any(m['role']=='tool' for m in payload['messages'])
                        and 'fixture native Pi summary' not in content):
                        message = dict(role='assistant',content='',tool_calls=[{
                            'id':'fixture_read','type':'function','function':{
                                'name':'read_repo','arguments':json.dumps({'path':'README.md','start':1,'end':17})}}])
                    pilot.dump(self.out/f'request-{request_number:02}.json',payload)
                    result = dict(model=BACKEND,choices=[dict(message=message,finish_reason='tool_calls' if 'tool_calls' in message else 'stop')],
                                  usage=dict(prompt_tokens=105000 if 'tool_calls' in message else 18000,
                                             completion_tokens=1))
                    pilot.dump(self.out/f'response-{request_number:02}.json',result)
                    return result

                @staticmethod
                def assert_final(content):
                    if 'fixture verification receipt' not in content:
                        raise AssertionError('Final missed cross-worker evidence')

            with patch.object(pilot, 'secret_env', return_value={'SOCLAAS_API_KEY':'fixture'}):
                cell = FakeCell(root,'nnsmith','evidence_gap_swarm',asyncio.Semaphore(2))
                outcome = await cell.run()
            self.assertEqual(outcome['returncode'],0,outcome)
            events = [json.loads(line) for line in (cell.out/'event.jsonl').read_text().splitlines()]
            kinds = [item['kind'] for item in events]
            self.assertEqual(kinds.count('gap_discovery_frozen'),2)
            compacts = [e for e in events if e['kind']=='native_gap_compaction']
            self.assertEqual([e['trigger'] for e in compacts],['threshold'],[e for e in events if 'compaction' in e['kind']])
            compact, = compacts
            later = [e for e in events[events.index(compact)+1:]
                     if e['kind']=='model_requested' and e['agent']==compact['agent']]
            self.assertTrue(later)
            self.assertTrue(any(isinstance(m.get('content'),str) and 'fixture native Pi summary' in m['content']
                                for m in later[0]['messages']))
            self.assertLess(max(i for i,k in enumerate(kinds) if k=='gap_discovery_frozen'),
                            kinds.index('gap_route_selected'))
            receipt, = [item for item in events if item['kind']=='gap_verification_received']
            self.assertEqual(receipt['agent'],'root.2')
            self.assertEqual(receipt['assignment']['candidate']['id'],'root.1#1')
            self.assertEqual(receipt['assignment']['candidate']['invariant'],'same control')
            final = cell.out/'final.txt'
            request = final_response(cell.out,outcome,final)
            trace = gap_trace(cell.out,json.loads(final.read_text())['candidates'],request)
            self.assertTrue(trace['cross_check_in_final_request'])
            self.assertEqual(trace['final_records_linked_to_checked_candidate'],1)
            for worker in trace['candidate_handoff_by_worker']:
                self.assertEqual(worker['raw_candidate_count'],2)
                self.assertEqual(worker['frozen_candidate_count'],1)
                self.assertEqual(worker['delivered_candidate_count'],1)
                self.assertEqual(worker['final_candidates_linked'],int(worker['worker']=='root.1'))
            spans = source_evidence(root/'nnsmith',cell.out)
            self.assertTrue(spans['README.md'])
            with self.assertRaisesRegex(ValueError,'Test release'):
                await run(root,'test')

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'study'
            inputs = Path(os.environ.get('CS6223_STUDY_INPUTS',pilot.MODULE/'runs'))
            source = os.environ.get('CS6223_SWARM_SOURCE')
            freeze_study(root,inputs,Path(source) if source else None,os.environ.get('CS6223_STUDY_POLICY','original'))
            asyncio.run(smoke(root))


class Scoring(unittest.TestCase):
    def test_targeted_comparison_keeps_draft_separate_from_self_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grades = root/'grades'
            grades.mkdir()
            conditions = ('frozen_draft',*MODES)
            cells = []
            for i, (condition, match) in enumerate(zip(conditions,('miss','partial','core'))):
                ident = f'report-{i}'
                cells.append(dict(case='01',condition=condition,state='complete',report_id=ident,final_sha256=ident))
                pilot.dump(root/f'{ident}.json',dict(records=[{'id':'H1'}],mechanical_evidence={}))
                pilot.dump(grades/f'{ident}.json',dict(final_sha256=ident,match=match,
                                                       record_id='H1',reason='fixture grade'))
            pilot.dump(root/'mapping.json',dict(split='dev',cells=cells,targeted_review_conditions=conditions))
            result = summarize(root,grades)['delegated_paired_against']
            self.assertEqual(result['frozen_draft']['rows'],[('01',0,2)])
            self.assertEqual(result['self_review']['rows'],[('01',1,2)])
            with self.assertRaises(ValueError):
                select_dev_method(root,grades)

    def test_summary_after_final_does_not_replace_final_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            answer = root/'final.txt'
            answer.write_text('final report')
            pilot.dump(root/'request-map.json',[{'request':1,'agent':'root'},
                                                {'request':2,'agent':'root'}])
            for number,text in enumerate(('final report','compaction summary'),1):
                pilot.dump(root/f'response-{number:02}.json',{'model':BACKEND,
                    'choices':[{'finish_reason':'stop','message':{'content':text}}]})
            self.assertEqual(final_response(root,{'requests':2,'returncode':0},answer),1)

    def test_failed_reports_are_not_false_diagnoses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grades = root/'grades'
            grades.mkdir()
            a,b,c,d = CONDITIONS
            pilot.dump(root/'mapping.json',{'split':'dev','cells':[
                dict(case='01',condition=a,state='complete',report_id='a',final_sha256='A'),
                dict(case='01',condition=b,state='failed'),
                dict(case='01',condition=c,state='pending'),
                dict(case='01',condition=d,state='complete',report_id='d',final_sha256='D'),
            ]})
            for ident,digest,match in [('a','A','partial'),('d','D','core')]:
                pilot.dump(root/f'{ident}.json',dict(records=[{'id':'H1'}],mechanical_evidence={
                    'H1':{'paper_found':[True,False],'source_delivered':[True]}}))
                pilot.dump(grades/f'{ident}.json',dict(final_sha256=digest,match=match,record_id='H1',
                    reason='fixture',test_ready_ids=['H1'],supported_ids=['H1']))
            result = summarize(root,grades)
            self.assertEqual(result['conditions'][b]['failed'],1)
            self.assertEqual(result['conditions'][b]['miss'],0)
            self.assertEqual(result['D_paired_against'][b]['n'],0)
            self.assertEqual(result['D_paired_against'][a]['D_wins'],1)
            self.assertEqual(result['conditions'][d]['paper_citations_on_page'],[1,2])


    def test_either_swarm_can_win_on_complete_dev_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grades = root/'grades'
            grades.mkdir()
            summaries = []
            picks = dict(zip(CONDITIONS, ('partial','partial','core','miss')))
            for case in DEV:
                for mode, match in picks.items():
                    ident = f'{case}-{mode}'
                    summaries.append(dict(case=case,condition=mode,state='complete',
                                          report_id=ident,final_sha256=ident))
                    pilot.dump(root/f'{ident}.json',{'records':[{'id':'H1'}],'mechanical_evidence':{}})
                    pilot.dump(grades/f'{ident}.json',dict(final_sha256=ident,match=match,
                                                         record_id='H1',reason='fixture'))
            mapping = root/'mapping.json'
            pilot.dump(mapping,{'split':'dev','cells':summaries})
            self.assertEqual(select_dev_method(root,grades)['selected'],'plain_swarm')
            pilot.dump(mapping,{'split':'dev','cells':summaries[4:]})
            self.assertIsNone(select_dev_method(root,grades)['selected'])


if __name__ == '__main__':
    unittest.main()
