"""Offline acceptance of a full local handoff against original paper/source/ZIP."""
import argparse
from collections import Counter
from pathlib import Path
import json
import re
import subprocess
import zipfile

from pypdf import PdfReader
from paperprobe.delivery import TEAM
from paperprobe.io import read_json, file_sha256, write_json


def validate(folder):
    artifact = read_json(folder / 'artifact.json')
    aid = artifact['artifact_id']
    manifest = read_json(folder / 'manifest.json')
    work = Path(manifest['work'])
    pages = [p.extract_text() or '' for p in PdfReader(folder / 'evidence/paper.pdf').pages]
    recorded = read_json(work / 'paper-input.json')
    assert pages == [p['text'] for p in recorded['pages']], 'Changed paper text'
    assert file_sha256(folder / 'evidence/paper.pdf') == file_sha256(TEAM / 'third_party/papers' / f'{aid}.pdf')
    data = read_json(folder / 'paper_side.json')
    quotes = 0
    observations = read_json(folder / 'reported_observations.json') if (folder / 'reported_observations.json').exists() else []
    paper_rows = data['claims'] + data['scope'] + data['eval_points'] + [r for g in observations for r in g['records']]
    for row in paper_rows:
        assert row['evidence'], 'Missing active paper evidence'
        for e in row['evidence']:
            match = re.search(r'PDF p\.(\d+)', e['locator'])
            assert match and e['quote'] and e['quote'] in pages[int(match[1]) - 1], f'Changed quote {e["locator"]}'
            quotes += 1
    pending = read_json(folder / 'pending_records.json')
    frozen = [b for p in sorted((work / 'behaviors').glob('M??-draft.json')) for b in read_json(p)['behaviors']]
    expected = {b['id'] for b in frozen}
    rows = read_json(folder / 'conformance.json')
    assert len(expected) == len(frozen) == len(rows)
    assert {r['id'] for r in rows} == expected, 'Frozen behavior coverage drift'
    claims = {c['claim_id'] for c in data['claims']}
    unresolved = {p['row']['id'] for p in pending if p.get('field') == 'claims'}
    registry = {r['evidence_id']: r for r in read_json(folder / 'code_evidence_registry.json')}
    assert len(registry) == len(read_json(folder / 'code_evidence_registry.json'))
    for row in rows:
        if row['claim_id']:
            assert row['claim_id'] in claims
        else:
            assert row['id'] in unresolved, 'Missing unresolved claim record'
        for scope in ['local_entry', 'artifact']:
            state = row[scope]
            assert state['review_state'] in ['completed', 'pending']
            assert state['verdict'] in ['supports', 'deviates', 'absent'] if state['review_state'] == 'completed' else state['verdict'] is None
            assert all(ref in registry for ref in row['evidence_registry_ids'][scope])
    repositories = read_json(folder / 'repositories.json')
    cache, source_lines = {}, {}
    sources = read_json(folder / 'source_reads.json')
    for source in sources:
        repo = repositories[source['repo']]
        assert source.get('commit', repo['commit']) == repo['commit']
        key = (source['repo'], source['path'])
        if key not in cache:
            cache[key] = subprocess.check_output(['git', '-C', repo['local_repo'], 'show', f'{repo["commit"]}:{source["path"]}'], text=True).split('\n')
        lo, hi = source['start_line'], source['end_line']
        exact = '\n'.join(f'{n}: {cache[key][n-1]}' for n in range(lo, hi + 1))
        assert source['lines'] == exact, f'Changed source {key}'
        source_lines.setdefault(key, set()).update(range(lo, hi + 1))
    for ref in registry.values():
        assert ref['commit'] == repositories[ref['repo']]['commit']
        assert set(range(ref['start_line'], ref['end_line'] + 1)) <= source_lines.get((ref['repo'], ref['path']), set()), 'Unarchived cited source'
    index = read_json(folder / 'bundle-index.json')['files']
    actual = {str(p.relative_to(folder)): file_sha256(p) for p in folder.rglob('*') if p.is_file() and p.name != 'bundle-index.json'}
    assert index == actual, 'Stale full archive index'
    archive = folder.parent / f'{aid}-handoff.zip'
    with zipfile.ZipFile(archive) as z:
        allfiles = {f'{aid}/{str(p.relative_to(folder))}': p for p in folder.rglob('*') if p.is_file()}
        assert set(z.namelist()) == set(allfiles), 'ZIP file inventory drift'
        for name, original in allfiles.items():
            assert z.read(name) == original.read_bytes(), f'ZIP differs: {name}'
    counts = Counter(r['artifact']['verdict'] for r in rows if r['artifact']['review_state'] == 'completed')
    result = dict(artifact_id=aid, result='passed', mechanisms=len(manifest['report_index']), behaviors=len(rows),
                  completed=sum(counts.values()), pending=sum(r['artifact']['review_state'] == 'pending' for r in rows),
                  verdicts=dict(counts), paper_quote_records_checked=quotes, pinned_source_records_checked=len(sources),
                  registry_records_checked=len(registry), full_archive_files=len(index) + 1, zip_sha256=file_sha256(archive),
                  interface_counts={k: len(v) for k, v in data.items()}, observations=sum(len(g['records']) for g in observations),
                  target_execution='not_run', model_api_calls=0, semantic_ground_truth='not_human_adjudicated',
                  meaning='Paper bytes, frozen IDs, source pins/read spans, claim links and full ZIP integrity; not semantic correctness or runtime validation')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', nargs='+', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    write_json(args.out, dict(results=[validate(p) for p in args.folders]))
