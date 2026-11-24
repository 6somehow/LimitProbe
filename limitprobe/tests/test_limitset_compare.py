import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/limitset/compare.py'


def test_comparison_cli(tmp_path):
    score = tmp_path / 'score'
    pred = tmp_path / 'pred'
    score.mkdir()
    pred.mkdir()
    rows = [
        {'case_id': 'a', 'split': 'test', 'category': 'applicability_limitation', 'found': True, 'fields': {'mechanism': True}, 'judge_unavailable': False, 'repeats': [{'found': True}, {'found': False}]},
        {'case_id': 'b', 'split': 'test', 'category': 'method_shortcoming', 'found': True, 'fields': {}, 'judge_unavailable': True, 'repeats': [{'found': None, 'judge_unavailable': True}]},
        {'case_id': 'c', 'split': 'validation', 'category': 'method_shortcoming', 'found': False, 'fields': {}, 'judge_unavailable': False, 'repeats': []},
    ]
    (score / 'score.json').write_text(json.dumps({'cases': rows}))
    (pred / 'predictions.jsonl').write_text('\n'.join(json.dumps(x) for x in [
        {'case_id': 'a', 'findings': [{'evidence': [{'level': 'L1'}], 'process_confidence': {'confidence_band': 'high'}}, {}]},
        {'case_id': 'a', 'findings': []}, {'case_id': 'c', 'findings': [{}]},
    ]))
    (pred / 'cost.jsonl').write_text(json.dumps({'case_id': 'a', 'calls': 2, 'prompt_tokens': 10, 'completion_tokens': 4, 'wall_seconds': 8}) + '\n')
    output, data = tmp_path / 'out.md', tmp_path / 'out.json'
    subprocess.run([sys.executable, str(SCRIPT), '--system', f'pipeline={score}:{pred}', '--system', f'baseline={score}', '--split', 'test', '--out', str(output), '--json', str(data)], check=True, env=dict(os.environ))
    report = json.loads(data.read_text())
    system = report['systems'][0]
    assert system['overall']['covered'] == system['overall']['total'] == 1
    assert system['overall']['judge_unavailable'] == ['b']
    assert system['overall']['wilson_95'] is not None
    assert system['categories']['method_shortcoming']['total'] == 0
    assert system['cases']['a']['mean_findings'] == 1
    assert system['cases']['a']['stability']['fraction'] == 0.5
    assert system['evidence_tier_available'] and system['confidence_band_available']
    assert system['cost']['wall_seconds_per_case'] == 4
    assert report['systems'][1]['cost']['calls'] is None
    text = output.read_text()
    assert 'uncalibrated' in text and 'n is tiny' in text and 'mechanism' in text
    assert '1: b' in text and 'tie' in text
