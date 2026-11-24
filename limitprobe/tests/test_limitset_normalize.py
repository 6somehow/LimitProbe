import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/limitset'))
from normalize import normalize
from make_case_dir import build


def fixture(tmp_path):
    raw = tmp_path / 'raw'
    (raw / 'runtime').mkdir(parents=True)
    (raw / 'labels').mkdir()
    (raw / 'papers').mkdir()
    out = tmp_path / 'data'
    out.mkdir()
    ids = [f'CS6223-{i:02}' for i in range(1, 18)]
    (out / 'splits.json').write_text(json.dumps({'validation': ids[:4], 'test': ids[4:]}))
    records, labels = [], []
    for i, case_id in enumerate(ids, 1):
        contents = f'PDF for {case_id}'.encode()
        path = f'papers/{i}.pdf'
        (raw / path).write_bytes(contents)
        records.append({'case_id': case_id, 'paper': {'source_id': f'R{i}', 'title': 'ODRP' if i == 12 else f'Paper {i}', 'raw_path': path, 'download_sha256': hashlib.sha256(contents).hexdigest()}, 'repository': None})
        labels.append({'case_id': case_id, 'claim': f'secret label {i}'})
    (raw / 'runtime/inputs.ready.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in records))
    (raw / 'labels/test_labels.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in labels))
    zip_path = tmp_path / 'dataset.zip'
    zip_path.write_bytes(b'zip')
    return raw, out, zip_path, ids


def test_normalize_and_isolate(tmp_path):
    raw, out, zip_path, ids = fixture(tmp_path)
    normalize(raw, zip_path, out)
    manifest = json.loads((out / 'manifest.json').read_text())
    assert len(manifest['pdfs']) == 17
    assert manifest['files']['labels.jsonl'] == hashlib.sha256((out / 'labels.jsonl').read_bytes()).hexdigest()
    case_dir = tmp_path / 'case'
    build(ids[11], case_dir, out / 'cases.jsonl', raw)
    assert {p.name for p in case_dir.iterdir()} == {'paper.pdf', 'case.json'}
    contents = b' '.join(p.read_bytes() for p in case_dir.iterdir())
    assert b'ODRP' in contents
    assert b'OneSidedMW' not in contents and b'R03' not in contents
    assert all(other.encode() not in contents for other in ids if other != ids[11])
    assert all(f'secret label {i}'.encode() not in contents for i in range(1, 18))


def test_rejects_bad_split_and_pdf(tmp_path):
    raw, out, zip_path, ids = fixture(tmp_path)
    (out / 'splits.json').write_text(json.dumps({'validation': ids[:4], 'test': ids[4:] + ids[4:5]}))
    with pytest.raises(ValueError, match='split'):
        normalize(raw, zip_path, out)
    (out / 'splits.json').write_text(json.dumps({'validation': ids[:4], 'test': ids[4:]}))
    (raw / 'papers/1.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError, match='checksum'):
        normalize(raw, zip_path, out)


def test_unreadable_raw_and_existing_destination(tmp_path):
    raw, out, zip_path, ids = fixture(tmp_path)
    with pytest.raises(FileNotFoundError):
        normalize(tmp_path / 'missing', zip_path, out)
    normalize(raw, zip_path, out)
    with pytest.raises(FileExistsError):
        build(ids[0], out, out / 'cases.jsonl', raw)
