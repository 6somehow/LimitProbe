import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/limitset/reproduce_tables.py'


def run_tables(bundle, output):
    return subprocess.run([sys.executable, str(SCRIPT), '--root', str(bundle), '--out', str(output)],
                          env={'PATH': os.defpath}, text=True, capture_output=True, check=True).stdout


def test_synthetic_bundle(tmp_path):
    system = tmp_path / 'bundle/limitset2/b1'
    system.mkdir(parents=True)
    (system / 'score.json').write_text(json.dumps({'cases': [{'case_id': 'X', 'labels': [
        {'case_id': 'X', 'found': True, 'fields': {'conditions': True, 'defeaters': False}},
        {'case_id': 'X', 'found': False, 'fields': {'conditions': False, 'defeaters': True}}]}]}))
    (system / 'predictions.jsonl').write_text(json.dumps({'findings': [{'quote_verified': True}]}) + '\n')
    output = tmp_path / 'tables.md'
    text = run_tables(tmp_path / 'bundle', output)
    assert text == output.read_text()
    assert '| B1 (x-test-2) | 1/2 ' in text
    assert '| 1/1 ' in text
    assert '| 1/2 / 1/2 |' in text


def test_real_bundle_scores(tmp_path):
    bundle = ROOT / 'results/limitset_final'
    scores = list(bundle.glob('limitset2/*/score.json'))
    assert len(scores) == 7
    text = run_tables(bundle, tmp_path / 'tables.md')
    names = {'b1': 'B1 (x-test-2)', 'b1x2': 'B1 x2 (x-test-2, two runs merged)',
             'v3c_xtest2': 'v3c (x-test-2)', 'union_xtest2': 'v3c + B1 (x-test-2)',
             'b1_sonnet': 'B1 (Claude Sonnet 5.5)', 'v3c_sonnet': 'v3c (Claude Sonnet 5.5)',
             'union_sonnet': 'v3c + B1 (Claude Sonnet 5.5)'}
    for score in scores:
        data = json.loads(score.read_text())
        labels = [label for case in data['cases'] for label in (case.get('labels') or [case])]
        scored = [label for label in labels if label.get('found') is not None]
        line = next(line for line in text.splitlines() if line.startswith(f'| {names[score.parent.name]} |'))
        assert f"| {sum(bool(label['found']) for label in scored)}/{len(scored)} " in line
    for score in (bundle / 'validation').glob('*/score.json'):
        data = json.loads(score.read_text())
        cases = [c for c in data['cases'] if c['split'] == 'validation' and c.get('found') is not None]
        repeats = [r['found'] for c in cases for r in c['repeats'] if r.get('found') is not None]
        assert f"{sum(repeats)}/{len(repeats)}" in text
