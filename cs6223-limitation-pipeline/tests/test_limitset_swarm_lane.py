import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pymupdf
import pytest

from pipeline import limitset


def test_adapter_uses_paper_only_and_local_relay(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'scripts/limitset/run_swarm_case.py'
    spec = importlib.util.spec_from_file_location('swarm_adapter', path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    inp = tmp_path / 'input'
    inp.mkdir()
    (inp / 'case.json').write_text(json.dumps({'case_id': 'toy'}))
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Evidence')
        pdf.save(inp / 'paper.pdf')

    class FakeCell:
        def __init__(self, inputs, paper, condition, out, protocol):
            assert json.loads((inputs / paper / 'source.json').read_text())['repo'] is None
            assert condition == 'gap_receipt_swarm' and protocol['two_phase']
            assert adapter.cell.secret_env()['SOCLAAS_BASE_URL'] == 'http://127.0.0.1:8787/v1'
            self.out = out
            out.mkdir(parents=True)

        def run(self):
            (self.out / 'final.txt').write_text('{"candidates": []}')
            return {'error': None, 'validation': {'json_parsed': True}}

    monkeypatch.setattr(adapter.cell, 'Cell', FakeCell)
    adapter.main(inp, tmp_path / 'out')
    assert json.loads((tmp_path / 'out/final.json').read_text())['origin'] == 'swarm-s7'
    (inp / 'extra').touch()
    with pytest.raises(ValueError, match='isolated'):
        adapter.main(inp, tmp_path / 'other')


def test_blindness_rejects_reference(tmp_path):
    with pytest.raises(AssertionError, match='blindness'):
        limitset.safe_path(tmp_path / 'reference' / 'data')
