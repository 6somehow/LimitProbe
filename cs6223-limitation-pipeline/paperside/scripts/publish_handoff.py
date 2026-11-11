"""Copy an explicitly selected lightweight handoff; never publish raw runs or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

FILES = {
    'artifact.json', 'paper_side.json', 'paper_side.pre-final.json', 'conformance.json',
    'limitations.json', 'finding_candidates.json', 'scope_interpretations.json',
    'pending_records.json', 'inactive_bindings.json', 'binding_provenance.json',
    'repositories.json', 'source_reads.json', 'code_evidence_registry.json',
    'manifest.json', 'validation.json', 'review-adjustments.json', 'review-notes.json',
    'corpus-acceptance.json', 'README.md', 'RUN_WITH_WANTING.md',
    'consumer_schema.snapshot.py', 'frozen-behaviors.json', 'mechanisms.json',
    'reported_observations.json', 'review-checks.json', 'archive-acceptance.json',
    'transport-uncertainty.json',
}
REQUIRED = {'artifact.json', 'paper_side.json', 'conformance.json', 'validation.json',
            'manifest.json', 'pending_records.json', 'source_reads.json', 'code_evidence_registry.json'}
SECRET = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16})\b|https?://[^\s/@:]+:[^\s/@]+@')


def publish(source, destination):
    source, destination = Path(source).resolve(), Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination already exists; select a new reviewed output directory')
    missing = REQUIRED - {p.name for p in source.iterdir() if p.is_file()}
    if missing:
        raise ValueError(f'Missing source handoff files: {sorted(missing)}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.handoff-publish-', dir=destination.parent) as temporary:
        staging = Path(temporary) / 'package'
        staging.mkdir()
        for name in sorted(FILES | {'original-bundle-index.json', 'bundle-index.json'}):
            path = source / name
            if not path.exists():
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(f'Not a regular source file: {name}')
            payload = path.read_bytes()
            literal_secret = re.search(rb'''(?i)["']?(?:api[_-]?key|password|secret|authorization)["']?\s*[:=]\s*["'][A-Za-z0-9_ /.-]{24,}["']''', payload)
            if len(payload) > 5_000_000 or b'\x00' in payload or SECRET.search(payload) or literal_secret:
                raise ValueError(f'Oversized, binary or credential-like content: {name}')
            if path.suffix == '.json':
                json.loads(payload)
            # Preserve the full bundle index separately; it includes deliberately omitted files.
            output = 'original-bundle-index.json' if name in {'bundle-index.json', 'original-bundle-index.json'} else name
            if (staging / output).exists():
                continue
            (staging / output).write_bytes(payload)
        included = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(staging.iterdir())}
        record = {
            'artifact_id': json.loads((staging / 'artifact.json').read_text())['artifact_id'],
            'format': 'lightweight handoff; source evidence checks are not semantic ground truth',
            'omitted': ['evidence/ (PDF, images, original API calls)', 'HTML dashboards', 'ZIP archives',
                        'raw runs and API logs', 'target repositories', 'node_modules', 'credentials'],
            'note': 'Original bundle index describes the full local archive, not files required in this checkout. '
                    'Historical absolute paths are provenance, not portable live links. Raw source/PDF verification needs external pinned inputs.',
            'original_bundle_index_available': (staging / 'original-bundle-index.json').exists(),
            'included': included,
        }
        (staging / 'source-distribution.json').write_text(json.dumps(record, indent=2) + '\n')
        staging.rename(destination)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    record = publish(args.source, args.destination)
    print(f"Published {record['artifact_id']}: {len(record['included'])} lightweight files; no raw evidence copied")
