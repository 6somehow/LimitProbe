import json

from pipeline import limitset as L
from pipeline import limitset_baselines as B


def test_generator_override_is_recorded_in_manifests(tmp_path, monkeypatch):
    monkeypatch.setenv('LIMITSET_GEN_MODEL', 'claude-sonnet-5-5')
    monkeypatch.setenv('LIMITSET_GEN_RELAY_PORT', '8788')
    out = tmp_path / 'run'
    L.main(['run', '--split', 'validation', '--repeats', '1', '--out', str(out), '--dry-run'])
    manifest = json.loads((out / 'run_manifest.json').read_text())
    assert manifest['model_id'] == 'claude-sonnet-5-5' and manifest['gen_relay_port'] == 8788
    src = open(B.__file__).read()
    # the baseline driver reads the same overrides and records them in its manifest identity
    assert "LIMITSET_GEN_MODEL" in src and "LIMITSET_GEN_RELAY_PORT" in src and "'gen_relay_port': gen_port" in src


def test_default_keeps_x_test_2(tmp_path, monkeypatch):
    monkeypatch.delenv('LIMITSET_GEN_MODEL', raising=False)
    monkeypatch.delenv('LIMITSET_GEN_RELAY_PORT', raising=False)
    monkeypatch.delenv('PIPELINE_MODEL', raising=False)
    out = tmp_path / 'run'
    L.main(['run', '--split', 'validation', '--repeats', '1', '--out', str(out), '--dry-run'])
    manifest = json.loads((out / 'run_manifest.json').read_text())
    assert manifest['model_id'] == 'x-test-2' and manifest['gen_relay_port'] is None
