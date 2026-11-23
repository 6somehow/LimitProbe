import json

from checklimits.checklimits.paper_only import mechanism_candidates
from pipeline.limitset_enrich import FakeLLM


def test_mechanism_quotes_and_separate_critiques():
    paper = 'The method uses a fixed threshold for selection.'
    code = 'def select():\n    return fixed_threshold\n'
    base = {'claim': 'A limit', 'mechanism': 'Because of a fixed threshold',
            'conditions': ['Changing workloads'], 'consequence': 'Loss',
            'defeaters': ['Adaptive threshold'], 'disclosure': 'inferred',
            'quotes': [{'source': 'paper', 'quote': paper, 'locator': 'page 1'}]}
    candidates = [dict(base, category_code='method_shortcoming'),
                  dict(base, kind='missing_comparison'),
                  dict(base, category_code='method_shortcoming', quotes=[{'source': 'code', 'locator': 'a.py', 'quote': 'return fixed_threshold'}]),
                  dict(base, category_code='method_shortcoming', quotes=['invented quotation'])]
    llm = FakeLLM(json.dumps({'candidates': candidates}))
    result, critiques, dropped = mechanism_candidates(paper, {'a.py': code}, llm)
    assert len(result) == 2 and len(critiques) == 1 and dropped == 1
    assert critiques[0]['kind'] == 'evaluation_critique'
    assert result[1]['evidence'][0]['source_id'] == 'code'
    assert '15-20' in llm.calls[0] and 'design-level trade-offs' in llm.calls[0]


def test_worker_maps_candidates(tmp_path, monkeypatch):
    from pathlib import Path
    from pipeline import limitset
    from checklimits.checklimits import paper_only
    def prepare(cmd, **kwargs):
        assert kwargs['env'] == {'PATH': '/bin'}
        path = Path(cmd[cmd.index('--out') + 1])
        path.mkdir(parents=True)
        (path / 'paper.pdf').write_text('pdf')
        (path / 'case.json').write_text('{}')
    monkeypatch.setattr(limitset.subprocess, 'run', prepare)
    monkeypatch.setattr(paper_only, 'pdf_text', lambda p: 'A sufficiently long exact quotation.')
    llm = FakeLLM(json.dumps({'candidates': [{'category_code': 'method_shortcoming', 'claim': 'claim', 'mechanism': 'why', 'conditions': ['when'], 'consequence': 'cost', 'defeaters': ['none'], 'disclosure': 'inferred', 'quotes': ['A sufficiently long exact quotation.']}]}))
    result = limitset.worker({'case_id': 'a', 'pdf_path': 'p', 'title': 't'}, 1, tmp_path / 'out', tmp_path, 10, {'PATH': '/bin'}, {}, enrich_llm=llm, generator='mechanism', mechanism_version='paper-only-mech-v1')
    assert result['findings'][0]['mechanism'] == 'why'
    assert result['findings'][0]['conditions'] == ['when']
    evidence = json.loads((tmp_path / 'out/runs/a/r1/mechanism_evidence.json').read_text())
    assert evidence['candidates'][0]['consequence'] == 'cost'


def test_v2_two_steps_and_deduplication():
    from checklimits.checklimits.paper_only import MECH_V2
    paper = 'The method uses a fixed threshold for selection.'
    base = {'category_code': 'method_shortcoming', 'mechanism': 'fixed threshold',
            'necessary_conditions': ['workload shift'], 'quotes': [paper]}
    responses = iter([json.dumps({'mechanisms': [{'mechanism': 'selection'}]}),
                      json.dumps({'candidates': [base, dict(base), dict(base, kind='evaluation_critique'),
                                                dict(base, quotes=['invented quotation'])]})])
    calls = []
    def ask(prompt):
        calls.append(prompt)
        return next(responses)
    stats = {}
    result, critiques, dropped = mechanism_candidates(paper, {}, ask, version=MECH_V2, stats=stats)
    assert len(calls) == 2 and 'selection' in calls[1]
    assert len(result) == 1 and len(critiques) == 1 and dropped == 1
    assert stats['merged_candidates'] == 1


def test_v3_steps_filter_and_no_filter():
    from checklimits.checklimits.paper_only import MECH_V3
    paper = 'The method uses a fixed threshold for selection.'
    item = {'headline': 'Selection does not guarantee success', 'category_code': 'method_shortcoming',
            'paper_fact': paper, 'premise': 'Conditions change', 'inference': 'Selection may fail',
            'necessary_conditions': ['change'], 'quotes': [paper]}
    critique = dict(item, kind='evaluation_critique')
    for no_filter in (False, True):
        responses = [json.dumps({'mechanisms': [{'mechanism': 'selection'}]}),
                     json.dumps({'sweep': [{'lens': 'L1'}]}),
                     json.dumps({'candidates': [item, critique, dict(item, quotes=['invented quotation'])]})]
        if not no_filter:
            responses.append(json.dumps({'candidates': [item, dict(item, quotes=['invented quotation'])],
                                         'evaluation_critiques': [critique]}))
        calls = []
        def ask(prompt):
            calls.append(prompt)
            return responses[len(calls) - 1]
        result, critiques, dropped = mechanism_candidates(paper, {}, ask, version=MECH_V3, no_filter=no_filter)
        assert len(calls) == (3 if no_filter else 4)
        assert len(result) == len(critiques) == dropped == 1
        assert result[0]['necessary_conditions'] == ['change']
