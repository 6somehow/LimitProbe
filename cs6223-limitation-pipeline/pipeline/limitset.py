"""Run the paper-only lane on isolated limitset cases."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = Path('<limitset-raw>')
FORBIDDEN = {'labels', 'reference_material', 'evaluator_evidence'}


def safe_path(path):
    assert not (FORBIDDEN & set(Path(path).resolve().parts)), 'blindness violation'
    return Path(path)


def read(path):
    return json.loads(safe_path(path).read_text(encoding='utf-8'))


def mapping(record):
    f = record.get('finding', record)
    a = record.get('analysis') or {}
    limitations = record.get('limitations') or []
    claim = a.get('reasoning') or f.get('summary') or ''
    conditions = [str(x.get('condition_text')) for x in limitations if x.get('condition_text')]
    if f.get('condition'):
        conditions.append(str(f['condition']))
    evidence = []
    for e in (record.get('evidence') or {}).get('paper', []):
        evidence.append({'source_id': 'paper', 'location': str(e.get('locator') or ''), 'support_description': str(e.get('quote') or '')})
    for lim in limitations:
        for e in lim.get('code_evidence', []):
            evidence.append({'source_id': 'code', 'location': str(e.get('file') or '') + ':' + str(e.get('line_start') or '')})
    caveats = [str(x) for x in (a.get('tier_note'), f.get('review_note')) if x]
    return {'claim': str(claim), 'category_code': 'unclassified', 'mechanism': str(a.get('reasoning') or f.get('summary') or ''), 'conditions': conditions, 'evidence': evidence, 'caveats': caveats}


def validate(record, schema):
    try:
        import jsonschema
    except ImportError:
        assert record['case_id'] and isinstance(record['findings'], list)
        for f in record['findings']:
            assert all(k in f for k in ('claim', 'category_code', 'mechanism', 'conditions', 'evidence', 'caveats'))
    else:
        jsonschema.validate(record, schema)


def now():
    return datetime.now(timezone.utc).isoformat()


def worker(case, repeat, out, raw, timeout, env, schema):
    run = out / 'runs' / case['case_id'] / f'r{repeat}'
    done = run / 'prediction.json'
    if done.is_file():
        record = read(done)
        validate(record, schema)
        return record
    run.mkdir(parents=True, exist_ok=True)
    case_dir = run / 'input'
    try:
        if case_dir.exists():
            shutil.rmtree(case_dir)
        pdf = safe_path(raw / case['pdf_path'])
        assert pdf.resolve().is_relative_to(raw.resolve()), 'PDF outside raw root'
        cmd = [sys.executable, str(ROOT / 'scripts/limitset/make_case_dir.py'), case['case_id'], '--out', str(case_dir), '--raw', str(raw)]
        subprocess.run(cmd, check=True, env=env, timeout=timeout, capture_output=True, text=True)
        assert {p.name for p in case_dir.iterdir()} == {'paper.pdf', 'case.json'}
        cmd = [sys.executable, '-m', 'pipeline.limitset', '_paper', case['case_id'], str(case_dir / 'paper.pdf'), str(run), case['title']]
        with (run / 'generator.log').open('w') as log:
            subprocess.run(cmd, check=True, env=env, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT)
        tdir = run / 'results/tests' / case['case_id']
        index = read(tdir / 'index.json')
        findings = [mapping(read(tdir / item['finding_id'] / 'report.json')) for item in index['findings']]
        sources = ['paper-only']
        code = ROOT / 'results/step4/infinigen/limitations_for_tests.json'
        if case['case_id'] == 'CS6223-03' and code.is_file():
            findings.extend(mapping(f) for f in read(code)['findings'])
            sources.append('results/step4/infinigen')
        record = {'case_id': case['case_id'], 'repeat': repeat, 'findings': findings, 'sources': sources}
        validate(record, schema)
        done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        return record
    except Exception as exc:
        failure = {'case_id': case['case_id'], 'repeat': repeat, 'findings': [], 'insufficient_evidence_reason': f'{type(exc).__name__}: {exc}', 'status': 'failed'}
        (run / 'failure.json').write_text(json.dumps(failure, indent=2) + '\n')
        return failure


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m pipeline limitset')
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--split', choices=['validation', 'test'], required=True)
    r.add_argument('--case')
    r.add_argument('--repeats', type=int, default=1)
    r.add_argument('--workers', type=int, default=3)
    r.add_argument('--timeout', type=int, default=3600)
    r.add_argument('--out', type=Path, default=ROOT / 'out/limitset')
    r.add_argument('--raw', type=Path, default=RAW)
    r.add_argument('--dry-run', action='store_true')
    a = p.parse_args(argv)
    if min(a.repeats, a.workers, a.timeout) < 1:
        p.error('repeats, workers and timeout must be positive')
    raw, out = safe_path(a.raw).resolve(), safe_path(a.out).resolve()
    cases = [json.loads(line) for line in (ROOT / 'data/limitset/cases.jsonl').read_text().splitlines() if line.strip()]
    ids = read(ROOT / 'data/limitset/splits.json')[a.split]
    selected = [c for c in cases if c['case_id'] in ids and (not a.case or c['case_id'] == a.case)]
    if a.case and not selected:
        p.error('case is not in the selected split')
    schema = read(raw / 'schemas/prediction.schema.json')
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(ROOT), env.get('PYTHONPATH')]))
    sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env, capture_output=True, text=True, check=True).stdout.strip()
    manifest = {'git_sha': sha, 'model_id': env.get('PIPELINE_MODEL', 'x-test-2'), 'split': a.split, 'repeats': a.repeats, 'started_at': now(), 'pdf_hashes': {c['case_id']: c['pdf_sha256'] for c in selected}}
    (out / 'run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    jobs = [(c, n) for c in selected for n in range(1, a.repeats + 1)]
    if a.dry_run:
        for c, n in jobs:
            run = out / 'runs' / c['case_id'] / f'r{n}'
            inp = run / 'input'
            safe_path(raw / c['pdf_path'])
            if not inp.exists():
                run.mkdir(parents=True, exist_ok=True)
                subprocess.run([sys.executable, str(ROOT / 'scripts/limitset/make_case_dir.py'), c['case_id'], '--out', str(inp), '--raw', str(raw)], env=env, check=True)
            assert {x.name for x in inp.iterdir()} == {'paper.pdf', 'case.json'}
            print(f"{c['case_id']} r{n}: {inp}")
    else:
        from pipeline import e2e, run as pipeline_run
        e = pipeline_run.env()
        env.update(e)
        with e2e.Relay(e):
            with ThreadPoolExecutor(max_workers=a.workers) as pool:
                records = list(pool.map(lambda job: worker(*job, out, raw, a.timeout, env, schema), jobs))
        (out / 'predictions.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in records))
    manifest['finished_at'] = now()
    (out / 'run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def paper_worker(args):
    from pipeline import e2e, run
    from types import SimpleNamespace
    case, pdf, output, title = args
    run.ROOT = Path(output)
    e2e.paper_only_cmd(SimpleNamespace(artifact_id=case, pdf=pdf, title=title, venue=None, model=None, swarm_report=None))


if __name__ == '__main__':
    if sys.argv[1:2] == ['_paper']:
        paper_worker(sys.argv[2:])
    else:
        main()
