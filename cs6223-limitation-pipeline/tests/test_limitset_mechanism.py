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
    result = limitset.worker({'case_id': 'a', 'pdf_path': 'p', 'title': 't'}, 1, tmp_path / 'out', tmp_path, 10, {'PATH': '/bin'}, {}, enrich_llm=llm, generator='mechanism')
    assert result['findings'][0]['mechanism'] == 'why'
    assert result['findings'][0]['conditions'] == ['when']
    evidence = json.loads((tmp_path / 'out/runs/a/r1/mechanism_evidence.json').read_text())
    assert evidence['candidates'][0]['consequence'] == 'cost'
