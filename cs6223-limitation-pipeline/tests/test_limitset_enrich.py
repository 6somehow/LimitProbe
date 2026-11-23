import json

import pytest

from pipeline import limitset as runner
from pipeline.limitset_enrich import FakeLLM, enrich


def finding():
    return {'claim': 'A claim', 'category_code': 'unclassified', 'mechanism': 'A claim',
            'conditions': ['old'], 'evidence': [{'support_description': 'Exact quote', 'location': 'p. 1'}],
            'caveats': ['private metadata']}


def test_enrichment_cache_and_input_boundary(tmp_path):
    llm = FakeLLM(json.dumps({'category_code': 'method_shortcoming', 'mechanism': 'The quote shows why.', 'conditions': ['large inputs']}))
    original = finding()
    result, error = enrich(original, tmp_path, llm, 'model')
    assert error is None
    assert result['category_code'] == 'method_shortcoming'
    assert result['evidence'] == original['evidence']
    prompt = llm.calls[0]
    assert 'A claim' in prompt and 'Exact quote' in prompt
    assert 'private metadata' not in prompt and 'p. 1' not in prompt
    assert enrich(original, tmp_path, llm, 'model') == (result, None)
    assert len(llm.calls) == 1
    enrich(original, tmp_path, llm, 'other-model')
    assert len(llm.calls) == 2


@pytest.mark.parametrize('response', [ValueError('offline'), 'not json', '{}',
    '{"category_code":"invalid","mechanism":"x","conditions":[]}',
    '{"category_code":"unclassified","mechanism":"x","conditions":[1]}'])
def test_fallback_on_errors(tmp_path, response):
    original = finding()
    result, error = enrich(original, tmp_path, FakeLLM(response), 'model')
    assert result == original and error
    assert not list(tmp_path.iterdir())


def test_worker_records_error_without_failing(tmp_path, monkeypatch):
    out = tmp_path / 'out'
    case = {'case_id': 'a', 'pdf_path': 'paper.pdf', 'title': 'title'}
    def prepare(cmd, **kwargs):
        assert kwargs['env'] == {'PATH': '/bin'}
        inp = __import__('pathlib').Path(cmd[cmd.index('--out') + 1])
        inp.mkdir(parents=True)
        (inp / 'paper.pdf').write_text('pdf')
        (inp / 'case.json').write_text('{}')
    def generate(cmd, **kwargs):
        tdir = out / 'runs/a/r1/results/tests/a'
        (tdir / 'f').mkdir(parents=True)
        (tdir / 'index.json').write_text('{"findings": [{"finding_id": "f"}]}')
        (tdir / 'f/report.json').write_text('{"finding": {"summary": "claim"}}')
    monkeypatch.setattr(runner.subprocess, 'run', prepare)
    monkeypatch.setattr(runner, 'run_generator', generate)
    result = runner.worker(case, 1, out, tmp_path, 10, {'PATH': '/bin'}, {}, enrich_llm=FakeLLM('bad'), model='m')
    assert result['findings'][0]['category_code'] == 'unclassified'
    errors = json.loads((out / 'runs/a/r1/enrichment.json').read_text())['errors']
    assert errors[0]['finding_index'] == 0 and errors[0]['enrich_error']


def test_concurrent_enrich_one_call_per_key_and_equals_serial(tmp_path):
    import json, threading, time
    from concurrent.futures import ThreadPoolExecutor
    from pipeline.limitset_enrich import enrich
    resp = json.dumps({'category_code': 'method_shortcoming', 'mechanism': 'because', 'conditions': ['when x']})
    calls, lock = [], threading.Lock()
    def llm(prompt):
        with lock:
            calls.append(prompt)
        time.sleep(0.05)
        return resp
    findings = [{'claim': f'c{i % 3}', 'evidence': [{'support_description': 'q'}]} for i in range(9)]
    with ThreadPoolExecutor(max_workers=9) as pool:
        par = list(pool.map(lambda f: enrich(f, tmp_path / 'cp', llm, 'm'), findings))
    assert len(calls) == 3
    ser = [enrich(f, tmp_path / 'cs', lambda p: resp, 'm') for f in findings]
    assert par == ser and all(e is None for _, e in par)
