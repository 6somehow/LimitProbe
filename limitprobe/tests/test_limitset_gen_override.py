import json

from pipeline import limitset as L
from pipeline import limitset_baselines as B


def _tiny_world(tmp_path, monkeypatch):
    """A one-case dataset in a temporary tree, so the test needs neither the real dataset nor a git checkout."""
    root = tmp_path / 'root'
    (root / 'data/limitset').mkdir(parents=True)
    (root / 'data/limitset/cases.jsonl').write_text(json.dumps({'case_id': 'a', 'pdf_sha256': 'x', 'pdf_path': 'p.pdf', 'title': 't'}) + '\n')
    (root / 'data/limitset/splits.json').write_text(json.dumps({'validation': ['a']}))
    raw = tmp_path / 'raw'
    (raw / 'schemas').mkdir(parents=True)
    (raw / 'schemas/prediction.schema.json').write_text('{}')
    monkeypatch.setattr(L, 'ROOT', root)
    from pathlib import Path

    def fake_run(cmd, *a, **k):  # stands in for git (the revision) and for make_case_dir.py (the isolated input)
        if any('make_case_dir.py' in str(x) for x in cmd):
            inp = Path(cmd[cmd.index('--out') + 1])
            inp.mkdir(parents=True)
            (inp / 'paper.pdf').write_bytes(b'%PDF-')
            (inp / 'case.json').write_text('{}')
        return type('Result', (), {'stdout': 'sha'})()
    monkeypatch.setattr(L.subprocess, 'run', fake_run)
    return raw


def test_generator_override_is_recorded_in_manifests(tmp_path, monkeypatch):
    monkeypatch.setenv('LIMITSET_GEN_MODEL', 'claude-sonnet-5-5')
    monkeypatch.setenv('LIMITSET_GEN_RELAY_PORT', '8788')
    raw = _tiny_world(tmp_path, monkeypatch)
    out = tmp_path / 'run'
    L.main(['run', '--split', 'validation', '--repeats', '1', '--raw', str(raw), '--out', str(out), '--dry-run'])
    manifest = json.loads((out / 'run_manifest.json').read_text())
    assert manifest['model_id'] == 'claude-sonnet-5-5' and manifest['gen_relay_port'] == 8788
    src = open(B.__file__).read()
    # the baseline driver reads the same overrides and records them in its manifest identity
    assert "LIMITSET_GEN_MODEL" in src and "LIMITSET_GEN_RELAY_PORT" in src and "'gen_relay_port': gen_port" in src


def test_default_keeps_x_test_2(tmp_path, monkeypatch):
    monkeypatch.delenv('LIMITSET_GEN_MODEL', raising=False)
    monkeypatch.delenv('LIMITSET_GEN_RELAY_PORT', raising=False)
    monkeypatch.delenv('PIPELINE_MODEL', raising=False)
    raw = _tiny_world(tmp_path, monkeypatch)
    out = tmp_path / 'run'
    L.main(['run', '--split', 'validation', '--repeats', '1', '--raw', str(raw), '--out', str(out), '--dry-run'])
    manifest = json.loads((out / 'run_manifest.json').read_text())
    assert manifest['model_id'] == 'x-test-2' and manifest['gen_relay_port'] is None
