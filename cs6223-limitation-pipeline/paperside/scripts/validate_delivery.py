"""Validate the published lightweight handoff offline, without APIs or target execution."""
import argparse
from pathlib import Path
import sys
from paperprobe.delivery import TEAM
from paperprobe.io import read_json, file_sha256
sys.path.insert(0, str(TEAM))
from schema.models import Claim, ScopeItem, EvalPoint, Binding, Limitation
from codeside.verify3b import load_paper_side
from codeside.scope_check import ScopeChecker


def validate(folder):
    data = read_json(folder / 'paper_side.json')
    for field, model in [('claims', Claim), ('scope', ScopeItem), ('eval_points', EvalPoint), ('bindings', Binding)]:
        for row in data[field]:
            model.model_validate(row)
    for row in read_json(folder / 'limitations.json'):
        Limitation.model_validate(row)
    proof = read_json(folder / 'validation.json')
    assert file_sha256(TEAM / 'schema/models.py') == proof['shared_schema_sha256'], 'Shared consumer schema changed'
    assert {k: len(v) for k, v in data.items()} == proof['counts']
    rows = read_json(folder / 'conformance.json')
    assert len(rows) == proof['conformance_rows']
    for state in ['completed', 'pending']:
        assert sum(r['artifact']['review_state'] == state for r in rows) == proof[f'{state}_artifact']
    assert all(r['artifact']['verdict'] is None for r in rows if r['artifact']['review_state'] == 'pending')
    pending = read_json(folder / 'pending_records.json')
    assert len(pending) == proof['pending_paper_records']
    assert sum(r.get('field') == 'claims' for r in pending) == proof['pending_claim_records']
    assert sum(r.get('field') == 'eval_points' for r in pending) == proof['held_evaluation_records']
    solver = [b for b in data['bindings'] if b['kind'] != 'mechanism_entry']
    assert len(solver) == proof['active_solver_bindings'] == 0
    ss, es, bs = load_paper_side(str(folder / 'paper_side.json'))
    checker = ScopeChecker(ss, es, bs)
    existing = TEAM / 'results/pipeline' / 'sparta' / 'limitations.json'
    for raw in read_json(existing):
        result = checker.check(Limitation.model_validate(raw).condition)
        assert result.scope_status == 'unknown' and result.evaluated_in_paper is None
    distribution = read_json(folder / 'source-distribution.json')
    for relative, expected in distribution['included'].items():
        assert file_sha256(folder / relative) == expected, f'Changed snapshot file: {relative}'
    print(f"Offline validation passed: {len(rows)} behaviors; {proof['completed_artifact']} completed / {proof['pending_artifact']} pending; {len(solver)} solver bindings; target execution and API calls: 0")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', nargs='?', type=Path, default=Path('handoffs/paper-side-v1/sparta'))
    validate(parser.parse_args().folder)
