"""Offline checks for one-shot baseline and execution isolation."""
import json
import os
from pathlib import Path
import subprocess

import fitz
import pytest

from limitset_baselines import b1
from pipeline import limitset_baselines as baseline


class FakeLLM:
    def __init__(self, content):
        self.content, self.calls = content, []

    def __call__(self, payload):
        self.calls.append(payload)
        return {'choices': [{'message': {'content': self.content}}],
                'usage': {'prompt_tokens': 7, 'completion_tokens': 3}}


def pdf_at(path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), 'A complete paper.')
    doc.save(path)
    doc.close()


def test_one_request_and_strict_parsing(tmp_path, monkeypatch):
    pdf_at(tmp_path / 'paper.pdf')
    fake = FakeLLM('{"findings":[{"claim":"limited"}]}')
    monkeypatch.setattr(b1, 'request', fake)
    result = b1.run_case({'case_id': 'CS6223-01'}, tmp_path, tmp_path, {}, 1)
    assert len(fake.calls) == 1
    assert fake.calls[0]['temperature'] == 0
    assert 'A complete paper.' in fake.calls[0]['messages'][0]['content']
    assert result['findings'][0]['category_code'] == 'unclassified'
    assert result['cost']['prompt_tokens'] == 7
    monkeypatch.setattr(b1, 'request', FakeLLM('not json'))
    with pytest.raises(json.JSONDecodeError):
        b1.run_case({'case_id': 'CS6223-01'}, tmp_path, tmp_path, {}, 1)
    assert json.loads((tmp_path / 'cost.json').read_text())['calls'] == 1


def test_rejects_case_outside_split():
    with pytest.raises(SystemExit):
        baseline.main(['--method', 'b2', '--split', 'validation', '--case', 'CS6223-12', '--dry-run'])


def test_missing_b2_is_clear(tmp_path, capsys, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'limitset_baselines.b2', None)  # simulate an uninstalled B2
    with pytest.raises(SystemExit):
        baseline.main(['--method', 'b2', '--split', 'validation', '--out', str(tmp_path)])
    assert 'b2 baseline is not installed' in capsys.readouterr().err


def test_worker_records_failure_and_cost(tmp_path, monkeypatch):
    case = {'case_id': 'CS6223-01', 'pdf_path': 'paper.pdf'}
    raw = tmp_path / 'raw'
    raw.mkdir()
    out = tmp_path / 'out'
    def fake_run(cmd, **kwargs):
        assert kwargs['env'] == {'PATH': os.environ['PATH']}
        inp = Path(cmd[cmd.index('--out') + 1])
        inp.mkdir()
        (inp / 'paper.pdf').touch()
        (inp / 'case.json').write_text('{}')
    def fake_generator(cmd, **kwargs):
        assert kwargs['env'] == {'PATH': os.environ['PATH']}
        run = Path(cmd[-2])
        (run / 'cost.json').write_text(json.dumps({'calls': 1, 'prompt_tokens': None, 'completion_tokens': None, 'wall_seconds': 1}))
        raise subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(baseline.subprocess, 'run', fake_run)
    monkeypatch.setattr(baseline, 'run_generator', fake_generator)
    record, cost, cached = baseline.worker((case, 1), 'b1', out, raw, 5, {'PATH': os.environ['PATH']}, {})
    assert record['status'] == 'failed' and cost['calls'] == 1 and not cached
    assert (out / 'runs/CS6223-01/r1/failure.json').exists()
