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


def test_generator_timeout_kills_child(tmp_path):
    import os
    import sys
    import time
    child = tmp_path / 'child.pid'
    script = ("import os, subprocess, sys, time; "
              "p=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], env=dict(os.environ)); "
              "open(sys.argv[1], 'w').write(str(p.pid)); time.sleep(60)")
    with (tmp_path / 'log').open('w') as log:
        with pytest.raises(subprocess.TimeoutExpired):
            L.run_generator([sys.executable, '-c', script, str(child)], env=dict(os.environ), timeout=2, log=log)
    pid = int(child.read_text())
    for _ in range(100):
        stat = Path(f'/proc/{pid}/stat')
        if not stat.exists() or stat.read_text().split()[2] == 'Z':
            break
        time.sleep(0.02)
    else:
        pytest.fail('generator child survived timeout')


def test_relay_start_failure_writes_manifest(tmp_path, monkeypatch):
    from pipeline import e2e, run
    root = tmp_path / 'root'
    (root / 'data/limitset').mkdir(parents=True)
    (root / 'data/limitset/cases.jsonl').write_text(json.dumps({'case_id': 'a', 'pdf_sha256': 'x'}) + '\n')
    (root / 'data/limitset/splits.json').write_text(json.dumps({'validation': ['a']}))
    raw = tmp_path / 'raw'
    (raw / 'schemas').mkdir(parents=True)
    (raw / 'schemas/prediction.schema.json').write_text('{}')
    monkeypatch.setattr(L, 'ROOT', root)
    monkeypatch.setattr(run, 'env', lambda: {})
    monkeypatch.setattr(e2e, 'relay_up', lambda: False)
    monkeypatch.setattr(L.subprocess, 'run', lambda *a, **k: type('Result', (), {'stdout': 'sha'})())
    out = tmp_path / 'out'
    L.main(['run', '--split', 'validation', '--raw', str(raw), '--out', str(out), '--repeats', '2'])
    manifest = json.loads((out / 'run_manifest.json').read_text())
    assert manifest['finished_at'] and manifest['counts'] == {'ok': 0, 'failed': 2, 'skipped': 0}
    assert all('Relay startup failed' in json.loads(line)['insufficient_evidence_reason'] for line in (out / 'predictions.jsonl').read_text().splitlines())


def test_swarm_report_passed_to_paper_lane(tmp_path, monkeypatch):
    from pipeline import e2e
    report = tmp_path / 'report.txt'
    report.write_text('report')
    captured = []
    monkeypatch.setattr(e2e, 'paper_only_cmd', captured.append)
    L.paper_worker(['case', 'paper.pdf', str(tmp_path), 'title', str(report)])
    assert captured[0].swarm_report == report
    assert captured[0].swarm_pdf_extractor == 'pypdf'


def test_worker_uses_swarm_results_and_origin(tmp_path, monkeypatch):
    out = tmp_path / 'out'
    report = tmp_path / 'a.txt'
    report.write_text('report')
    case = {'case_id': 'a', 'pdf_path': 'paper.pdf', 'title': 'title'}
    def prepare(cmd, **kwargs):
        inp = Path(cmd[cmd.index('--out') + 1])
        inp.mkdir(parents=True)
        (inp / 'paper.pdf').write_text('pdf')
        (inp / 'case.json').write_text('{}')
    def generate(cmd, **kwargs):
        assert cmd[-1] == str(report)
        tdir = out / 'runs/a/r1/results/swarm/tests/a'
        (tdir / 'f').mkdir(parents=True)
        (tdir / 'index.json').write_text('{"findings": [{"finding_id": "f"}]}')
        (tdir / 'f/report.json').write_text('{"finding": {"summary": "claim"}}')
    monkeypatch.setattr(L.subprocess, 'run', prepare)
    monkeypatch.setattr(L, 'run_generator', generate)
    result = L.worker(case, 1, out, tmp_path, 10, {}, {}, str(tmp_path / '{case}.txt'))
    assert result['sources'] == ['swarm']
    assert result['findings'][0]['origin'] == 'swarm'
