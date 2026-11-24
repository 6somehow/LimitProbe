#!/usr/bin/env python3
"""Convert the prepared limitset into input metadata and separate labels."""
import argparse
import hashlib
import json
import platform
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def safe_pdf(raw, relative):
    path = (raw / relative).resolve()
    if not path.is_relative_to(raw.resolve()) or path.suffix.lower() != '.pdf':
        raise ValueError('invalid PDF path: ' + relative)
    return path


def normalize(raw, zip_path, out):
    records = read_jsonl(raw / 'runtime/inputs.ready.jsonl')
    ids = [f'CS6223-{i:02d}' for i in range(1, 18)]
    split = json.loads((out / 'splits.json').read_text(encoding='utf-8'))
    if split['validation'] != ids[:4] or sorted(split['validation'] + split['test']) != ids:
        raise ValueError('invalid frozen split')
    if sorted(r['case_id'] for r in records) != ids:
        raise ValueError('input case IDs must cover all 17 cases exactly once')
    cases, pdfs = [], {}
    for record in records:
        paper = record['paper']
        path = safe_pdf(raw, paper['raw_path'])
        sha = digest(path)
        if sha != paper['download_sha256']:
            raise ValueError('PDF checksum mismatch: ' + record['case_id'])
        repo = record['repository']
        if repo and (record['case_id'] != 'CS6223-03' or not repo['commit'].startswith('3754f52d')):
            raise ValueError('unexpected repository pin')
        cases.append({'case_id': record['case_id'], 'paper_id': paper['source_id'],
                      'title': paper['title'], 'mode': 'with-code' if repo else 'paper-only',
                      'repository': {'repo_url': repo['repo_url'], 'commit': repo['commit']} if repo else None,
                      'pdf_path': paper['raw_path'], 'pdf_sha256': sha})
        pdfs[paper['raw_path']] = sha
    labels_path = raw / 'labels/test_labels.jsonl'
    labels = read_jsonl(labels_path)
    if sorted(r['case_id'] for r in labels) != ids:
        raise ValueError('label case IDs must cover all 17 cases exactly once')
    zip_sha = digest(zip_path)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'cases.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in cases), encoding='utf-8')
    (out / 'labels.jsonl').write_bytes(labels_path.read_bytes())
    manifest = {'files': {name: digest(out / name) for name in ('cases.jsonl', 'labels.jsonl', 'splits.json')},
                'pdfs': pdfs, 'zip_sha256': zip_sha, 'tool_versions': {'python': platform.python_version(), 'normalize': '1'}}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    normalize(args.raw, args.zip, args.out)


if __name__ == '__main__':
    main()
