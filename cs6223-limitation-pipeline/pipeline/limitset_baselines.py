"""Run blind limitset baselines in isolated, resumable case processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from pipeline.limitset import (ROOT, RAW, RAW2, dataset_cases, dataset_schema, RunnerRelay, failure_record, now, read,
                               run_generator, safe_path, validate)
from limitset_baselines.common import write_json


def execute(method, case, inp, run, env, repeat):
    module = importlib.import_module('limitset_baselines.' + method)
    result = module.run_case(case, inp, run, env, repeat)
    write_json(run / 'result.json', result)


def worker(job, method, out, raw, timeout, env, schema, cases_path=None):
    case, repeat = job
    run = out / 'runs' / case['case_id'] / f'r{repeat}'
    done = run / 'prediction.json'
    if done.is_file() and (run / 'cost.json').is_file():
        record, cost = read(done), read(run / 'cost.json')
        validate(record, schema)
        return record, cost, True
    run.mkdir(parents=True, exist_ok=True)
    inp = run / 'input'
    started = time.monotonic()
    try:
        if inp.exists():
            shutil.rmtree(inp)
        pdf = safe_path(raw / case['pdf_path']).resolve()
        if not pdf.is_relative_to(raw):
            raise ValueError('PDF outside raw root')
        subprocess.run([sys.executable, str(ROOT / 'scripts/limitset/make_case_dir.py'), case['case_id'],
                        '--out', str(inp), '--raw', str(raw), '--cases', str(cases_path or ROOT / 'data/limitset/cases.jsonl')], check=True, env=env,
                       timeout=timeout, capture_output=True)
        if {p.name for p in inp.iterdir()} != {'paper.pdf', 'case.json'}:
            raise ValueError('unexpected files in isolated case input')
        (run / 'result.json').unlink(missing_ok=True)
        (run / 'cost.json').unlink(missing_ok=True)
        cmd = [sys.executable, '-m', 'pipeline.limitset_baselines', '_case', method,
               str(inp), str(run), str(repeat)]
        with (run / 'generator.log').open('w') as log:
            run_generator(cmd, env=env, timeout=timeout, log=log)
        result = read(run / 'result.json')
        record = {'case_id': case['case_id'], 'repeat': repeat, 'findings': result['findings']}
        validate(record, schema)
        cost = result['cost']
        write_json(run / 'cost.json', cost)
        write_json(done, record)
        (run / 'failure.json').unlink(missing_ok=True)
        return record, cost, False
    except Exception as exc:
        record = failure_record(case, repeat, out, f'{type(exc).__name__}: {exc}; see generator.log')
        cost = read(run / 'cost.json') if (run / 'cost.json').exists() else {
            'calls': 0, 'prompt_tokens': None, 'completion_tokens': None,
            'wall_seconds': time.monotonic() - started}
        return record, cost, False


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m pipeline limitset baseline')
    parser.add_argument('--dataset', choices=['limitset', 'limitset2'], default='limitset')
    parser.add_argument('--method', required=True, choices=['b1', 'b2'])
    parser.add_argument('--split', required=True, choices=['validation', 'test'])
    parser.add_argument('--case')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--timeout', type=int, default=3600)
    parser.add_argument('--out', type=Path, default=ROOT / 'out/limitset_baselines')
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if min(args.repeats, args.workers, args.timeout) < 1:
        parser.error('repeats, workers and timeout must be positive')
    cases_path, cases, ids = dataset_cases(args.dataset, args.split)
    if args.case and args.case not in ids:
        parser.error('case is not in the selected split')
    selected = [c for c in cases if c['case_id'] in ids and (not args.case or args.case == c['case_id'])]
    raw, out = safe_path(args.raw or (RAW2 if args.dataset == 'limitset2' else RAW)).resolve(), safe_path(args.out).resolve()
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(ROOT), env.get('PYTHONPATH')]))
    jobs = [(c, n) for c in selected for n in range(1, args.repeats + 1)]
    if args.dry_run:
        for c, n in jobs:
            inp = out / 'runs' / c['case_id'] / f'r{n}' / 'input'
            if inp.exists():
                shutil.rmtree(inp)
            inp.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, str(ROOT / 'scripts/limitset/make_case_dir.py'), c['case_id'],
                            '--out', str(inp), '--raw', str(raw), '--cases', str(cases_path or ROOT / 'data/limitset/cases.jsonl')], check=True, env=env)
            if {p.name for p in inp.iterdir()} != {'paper.pdf', 'case.json'}:
                raise ValueError('unexpected files in isolated case input')
            print(f"{args.method} {c['case_id']} r{n}: {inp}")
        return
    try:
        importlib.import_module('limitset_baselines.' + args.method)
    except ModuleNotFoundError as exc:
        if exc.name == 'limitset_baselines.' + args.method:
            parser.error(f'{args.method} baseline is not installed')
        raise
    schema = dataset_schema(args.dataset, raw)
    out.mkdir(parents=True, exist_ok=True)
    sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env, capture_output=True, text=True, check=True).stdout.strip()
    gen_model = os.environ.get('LIMITSET_GEN_MODEL') or env.get('PIPELINE_MODEL', 'x-test-2')  # generator-only override
    gen_port = int(os.environ.get('LIMITSET_GEN_RELAY_PORT') or 0) or None
    if gen_model != env.get('PIPELINE_MODEL', 'x-test-2'):
        env['PIPELINE_MODEL'] = gen_model
    identity = {'method': args.method, 'model_id': gen_model, 'gen_relay_port': gen_port,
                'git_sha': sha, 'dataset': args.dataset, 'temperature': 0, 'split': args.split}
    manifest_path = out / 'run_manifest.json'
    if manifest_path.exists():
        previous = read(manifest_path)
        if any(previous.get(k) != v for k, v in identity.items()):
            parser.error('output manifest does not match this run; use a fresh output directory')
    manifest = {**identity, 'repeats': args.repeats, 'started_at': now(),
                'pdf_hashes': {c['case_id']: c['pdf_sha256'] for c in selected}}
    write_json(manifest_path, manifest)
    cached = all((out / 'runs' / c['case_id'] / f'r{n}' / 'prediction.json').is_file() and
                 (out / 'runs' / c['case_id'] / f'r{n}' / 'cost.json').is_file() for c, n in jobs)
    try:
        if cached:
            rows = [worker(job, args.method, out, raw, args.timeout, env, schema, cases_path) for job in jobs]
        else:
            from pipeline import e2e, run as pipeline_run
            relay_env = dict(os.environ)
            with RunnerRelay(e2e, pipeline_run, relay_env, out):
                env['SOCLAAS_API_KEY'] = 'relay'
                env['SOCLAAS_BASE_URL'] = f'http://127.0.0.1:{gen_port}/v1' if gen_port else e2e.RELAY_URL
                with ThreadPoolExecutor(max_workers=args.workers) as pool:
                    rows = list(pool.map(lambda job: worker(job, args.method, out, raw, args.timeout, env, schema, cases_path), jobs))
    except Exception as exc:
        rows = []
        for c, n in jobs:
            run = out / 'runs' / c['case_id'] / f'r{n}'
            if (run / 'prediction.json').is_file() and (run / 'cost.json').is_file():
                rows.append((read(run / 'prediction.json'), read(run / 'cost.json'), True))
            else:
                rows.append((failure_record(c, n, out, f'Relay startup failed: {type(exc).__name__}: {exc}'),
                             {'calls': 0, 'prompt_tokens': None, 'completion_tokens': None, 'wall_seconds': 0}, False))
    costs = [{'case_id': r['case_id'], 'repeat': r['repeat'], **cost} for r, cost, _ in rows]
    (out / 'predictions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r, _, _ in rows))
    (out / 'cost.jsonl').write_text(''.join(json.dumps(c) + '\n' for c in costs))
    manifest['costs'] = costs
    manifest['counts'] = {'ok': sum(not skip and r.get('status') != 'failed' for r, _, skip in rows),
                          'failed': sum(r.get('status') == 'failed' for r, _, _ in rows),
                          'skipped': sum(skip for _, _, skip in rows)}
    manifest['finished_at'] = now()
    write_json(manifest_path, manifest)


if __name__ == '__main__':
    if sys.argv[1:2] == ['_case']:
        _, _, method, inp, run, repeat = sys.argv
        execute(method, read(Path(inp) / 'case.json'), Path(inp), Path(run), dict(os.environ), int(repeat))
    else:
        main()
