"""Offline handoff integrity/consumer checks; never semantic ground truth or target execution."""
import argparse
from pathlib import Path
import re
import sys
from paperprobe.delivery import TEAM
from paperprobe.io import read_json, file_sha256
sys.path.insert(0, str(TEAM))
from schema.models import Claim, ScopeItem, EvalPoint, Binding, Limitation
from codeside.verify3b import load_paper_side
from codeside.scope_check import ScopeChecker
from finalize_handoff import numeric_scope


def unique(rows, key):
    ids = [r[key] for r in rows]
    assert all(isinstance(value, str) and value for value in ids), f'Empty {key}'
    assert len(ids) == len(set(ids)), f'Duplicate {key}'
    return set(ids)


def validate(folder, paper_pages=None):
    folder = Path(folder)
    distribution = read_json(folder / 'source-distribution.json')
    assert {'artifact.json', 'paper_side.json', 'conformance.json', 'validation.json', 'manifest.json', 'pending_records.json', 'source_reads.json', 'code_evidence_registry.json'} <= set(distribution['included']), 'Unhashed required snapshot file'
    for relative, expected in distribution['included'].items():
        path = folder / relative
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        assert path.resolve().is_relative_to(folder.resolve()), 'Snapshot path escapes package'
        assert not path.is_symlink() and path.is_file(), f'Missing snapshot file: {relative}'
        assert file_sha256(path) == expected, f'Changed snapshot file: {relative}'
    artifact = read_json(folder / 'artifact.json')['artifact_id']
    data = read_json(folder / 'paper_side.json')
    proof = read_json(folder / 'validation.json')
    assert file_sha256(TEAM / 'schema/models.py') == proof['shared_schema_sha256'], 'Shared consumer schema changed'
    assert {k: len(v) for k, v in data.items()} == proof['counts']
    claims = set()
    for field, model, key in [('claims', Claim, 'claim_id'), ('scope', ScopeItem, 'scope_id'),
                              ('eval_points', EvalPoint, 'eval_id'), ('bindings', Binding, 'binding_id')]:
        ids = unique(data[field], key)
        if field == 'claims':
            claims = ids
        for row in data[field]:
            model.model_validate(row)
            assert row['artifact_id'] == artifact
            for evidence in row.get('evidence', []):
                assert evidence['quote'].strip() and evidence['locator'].strip(), 'Empty source evidence'
                if paper_pages is not None and evidence['source'] == 'paper':
                    page = re.search(r'(?:PDF\s+)?p\.(\d+)', evidence['locator'])
                    assert page and evidence['quote'] in paper_pages[int(page[1])], 'Paper quote absent from numbered source page'
    observations_path = folder / 'reported_observations.json'
    observations = read_json(observations_path) if observations_path.exists() else []
    observation_records = [row for group in observations for row in group['records']]
    assert len(observations) == proof.get('reported_observation_groups', 0)
    assert len(observation_records) == proof.get('reported_observation_records', 0)
    observation_ids = unique(observation_records, 'eval_id')
    assert not observation_ids.intersection(r['eval_id'] for r in data['eval_points']), 'Observation leaked into active eval points'
    if observations_path.exists():
        assert 'reported_observations.json' in distribution['included'], 'Unhashed observations'
    for row in observation_records:
        EvalPoint.model_validate(row)
        assert row['artifact_id'] == artifact and row['evidence'], 'Observation lacks paper evidence'
        for evidence in row['evidence']:
            assert evidence['quote'].strip() and evidence['locator'].strip()
            if paper_pages is not None and evidence['source'] == 'paper':
                page = re.search(r'(?:PDF\s+)?p\.(\d+)', evidence['locator'])
                assert page and evidence['quote'] in paper_pages[int(page[1])], 'Observation quote absent from source page'
    limitations = read_json(folder / 'limitations.json')
    unique(limitations, 'limitation_id')
    for row in limitations:
        Limitation.model_validate(row)
        assert row['artifact_id'] == artifact
    rows = read_json(folder / 'conformance.json')
    behavior_ids = unique(rows, 'id')
    assert len(rows) == proof['conformance_rows'], 'Missing conformance behavior'
    manifest = read_json(folder / 'manifest.json')
    assert manifest['artifact']['artifact_id'] == artifact
    assert {r['mechanism_id'] for r in rows} == unique(manifest['report_index'], 'mechanism'), 'Missing mechanism'
    pending = read_json(folder / 'pending_records.json')
    assert len(pending) == proof['pending_paper_records']
    for field, key in [('claims', 'pending_claim_records'), ('eval_points', 'held_evaluation_records'), ('scope', 'held_scope_records')]:
        assert sum(r.get('field') == field for r in pending) == proof.get(key, 0)
    frozen = folder / 'frozen-behaviors.json'
    mechanisms = folder / 'mechanisms.json'
    assert frozen.exists() == mechanisms.exists(), 'Incomplete frozen behavior/mechanism snapshot'
    if frozen.exists():
        assert {'frozen-behaviors.json', 'mechanisms.json'} <= set(distribution['included'])
        assert unique(read_json(frozen)['behaviors'], 'id') == behavior_ids, 'Frozen behavior IDs differ from conformance'
        assert unique(read_json(mechanisms)['mechanisms'], 'id') == {r['mechanism_id'] for r in rows}, 'Frozen mechanism IDs differ'
    held_claims = {r['row'].get('id', r['row'].get('claim_id', '').removeprefix(artifact + ':'))
                   for r in pending if r.get('field') == 'claims'}
    registry = read_json(folder / 'code_evidence_registry.json')
    registry_ids = unique(registry, 'evidence_id')
    source = read_json(folder / 'source_reads.json')
    repositories = read_json(folder / 'repositories.json')
    assert repositories['primary']['commit'] == read_json(folder / 'artifact.json')['commit']
    spans = {}
    for packet in source:
        key = (packet['repo'], packet['path'], packet['commit'])
        assert packet['repo'] in repositories and packet['commit'] == repositories[packet['repo']]['commit']
        numbered = packet['lines'].split('\n')
        assert len(numbered) == packet['end_line'] - packet['start_line'] + 1
        for number, text in enumerate(numbered, packet['start_line']):
            assert text.startswith(f'{number}: '), 'Malformed numbered source excerpt'
            token = (*key, number)
            assert token not in spans or spans[token] == text, 'Conflicting source excerpts'
            spans[token] = text
    for evidence in registry:
        assert evidence['evidence_id'] == f"{evidence['mechanism_id']}:{evidence['id']}"
        assert 1 <= evidence['start_line'] <= evidence['end_line']
        for line in range(evidence['start_line'], evidence['end_line'] + 1):
            assert (evidence['repo'], evidence['path'], evidence['commit'], line) in spans, 'Registry cites an unread source line'
    linked = []
    for row in rows:
        assert row['artifact_id'] == artifact and row['paper']['quote'].strip()
        assert row['id'].startswith(row['mechanism_id'] + '-'), 'Behavior/mechanism mismatch'
        claim = row.get('claim_id')
        if claim is None:
            assert row['id'] in held_claims, 'Behavior has neither claim nor pending paper record'
        else:
            assert claim == f"{artifact}:{row['id']}" and claim in claims, 'Missing claim reference'
            linked.append(claim)
        for scope in ['local_entry', 'artifact']:
            result = row[scope]
            assert result['review_state'] in {'completed', 'pending'}, 'Unsupported review state'
            if result['review_state'] == 'pending':
                assert result['verdict'] is None, 'Pending verdict must be null'
            else:
                assert result['verdict'] in {'supports', 'deviates', 'absent'}, 'Unsupported verdict'
                assert result['actual'].strip() and result['equivalence'].strip(), 'Completed result lacks explanation'
            expected_refs = [f"{row['mechanism_id']}:{ref}" for ref in result['refs']]
            assert row['evidence_registry_ids'][scope] == expected_refs, 'Changed evidence reference IDs'
            assert set(expected_refs) <= registry_ids, 'Missing evidence reference'
    assert set(linked) == claims and len(linked) == len(claims), 'Missing behavior for active claim'
    assert held_claims <= behavior_ids, 'Pending claim has no behavior'
    expected_limitations = {f"{artifact}-gap-{row['id']}" for row in rows
                            if row['artifact']['review_state'] == 'completed'
                            and row['artifact']['verdict'] in {'deviates', 'absent'}
                            and row.get('claim_id') in claims}
    assert {row['limitation_id'] for row in limitations} == expected_limitations, 'Limitations differ from completed paper-backed negative behaviors'
    assert all(row['paper_evidence'] for row in limitations), 'Limitation lacks paper evidence'

    for state in ['completed', 'pending']:
        assert sum(r['artifact']['review_state'] == state for r in rows) == proof[f'{state}_artifact']
    solver = [b for b in data['bindings'] if b['kind'] != 'mechanism_entry']
    assert len(solver) == proof['active_solver_bindings']
    assert len(data['bindings']) - len(solver) == proof['navigation_bindings']
    scopes = {s['param']: s for s in data['scope']}
    for binding in solver:
        assert binding['certain'] and binding['paper_term'] in scopes
        assert numeric_scope(scopes[binding['paper_term']]), 'Nonexplicit/nonnumeric scalar domain'
        assert re.fullmatch(r'[A-Za-z_]\w*', binding['code_symbol']), 'Unsupported scalar symbol'
    if artifact == 'flexprefill':
        assert len(solver) == 1 and solver[0]['code_symbol'] == 'tau', 'Flex tau regression'
    ss, es, bs = load_paper_side(str(folder / 'paper_side.json'))
    checker = ScopeChecker(ss, es, bs)
    existing = TEAM / 'results/pipeline' / artifact / 'limitations.json'
    expected = {row['limitation_id']: row for row in proof['wanting_existing_conditions']}
    if existing.exists():
        for raw in read_json(existing):
            result = checker.check(Limitation.model_validate(raw).condition)
            recorded = expected[raw['limitation_id']]
            assert result.scope_status == recorded['scope_status'] and result.evaluated_in_paper == recorded['evaluated_in_paper']
    print(f"Offline integrity/consumer checks passed ({artifact}): {len(rows)} behaviors; "
          f"{proof['completed_artifact']} completed / {proof['pending_artifact']} pending; {len(solver)} scalar bindings. "
          f"Frozen behavior IDs: {'checked' if frozen.exists() else 'not independently supplied; manifest/claim IDs checked'}; "
          f"Paper original text: {'checked against supplied pages' if paper_pages is not None else 'not supplied'}; "
          "code checks use included numbered excerpts, not independent Git blobs; semantic truth pending.")
    return {'artifact_id': artifact, 'behaviors': len(rows), 'scalar_bindings': len(solver)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', nargs='?', type=Path)
    parser.add_argument('--root', type=Path, default=Path('handoffs/paper-side-v1'))
    parser.add_argument('--paper-input', type=Path, help='Optional original numbered paper-input.json, for a single folder')
    args = parser.parse_args()
    assert not args.paper_input or args.folder, '--paper-input requires one folder'
    pages = None
    if args.paper_input:
        pages = {p['page']: p['text'] for p in read_json(args.paper_input)['pages']}
    selected = [args.folder] if args.folder else sorted(p.parent for p in args.root.glob('*/paper_side.json'))
    assert selected, 'No published handoffs found'
    for folder in selected:
        validate(folder, pages)
