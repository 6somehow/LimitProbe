import json
from pathlib import Path
import subprocess

import pytest
from pipeline import limitset as L


def test_blindness_rejects_forbidden_paths(tmp_path):
    for name in L.FORBIDDEN:
        with pytest.raises(AssertionError):
            L.safe_path(tmp_path / name / 'secret')


def test_mapping_paper_and_code():
    paper = L.mapping({'finding': {'summary': 'claim'}, 'analysis': {'reasoning': 'limitation', 'tier_note': 'reading'}, 'evidence': {'paper': [{'locator': 'p. 2', 'quote': 'text'}]}})
    assert paper['claim'] == 'limitation'
    assert paper['evidence'][0]['source_id'] == 'paper'
    code = L.mapping({'summary': 'code claim', 'limitations': [{'condition_text': 'x', 'code_evidence': [{'file': 'a.py', 'line_start': 3}]}]})
    assert code['conditions'] == ['x']
    assert code['evidence'][0]['location'] == 'a.py:3'


def test_resume_and_failure_isolation(tmp_path, monkeypatch):
    schema = {'type': 'object', 'required': ['case_id', 'findings']}
    out = tmp_path / 'out'
    run = out / 'runs/CS6223-01/r1'
    run.mkdir(parents=True)
    saved = {'case_id': 'CS6223-01', 'repeat': 1, 'findings': []}
    (run / 'prediction.json').write_text(json.dumps(saved))
    assert L.worker({'case_id': 'CS6223-01'}, 1, out, tmp_path, 10, {}, schema) == saved
    def fail(*args, **kwargs):
        assert kwargs['env'] == {'PATH': '/bin'}
        raise subprocess.CalledProcessError(1, args[0])
    monkeypatch.setattr(L.subprocess, 'run', fail)
    case = {'case_id': 'CS6223-02', 'pdf_path': 'paper.pdf'}
    failed = L.worker(case, 1, out, tmp_path, 10, {'PATH': '/bin'}, schema)
    assert failed['status'] == 'failed'
    assert (out / 'runs/CS6223-02/r1/failure.json').is_file()
