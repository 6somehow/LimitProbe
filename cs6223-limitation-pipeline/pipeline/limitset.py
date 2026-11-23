"""Run the paper-only lane on isolated limitset cases."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import time
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = Path('/home/somehow6/lesson/CS6223/CS6223_Limitation_Testset')
FORBIDDEN = {'labels', 'reference_material', 'evaluator_evidence', 'reference'}


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
    kind = a.get('kind_code')
    if kind in ('applicability_limitation', 'mechanism_origin_unclear', 'method_shortcoming'):
        claim = f.get('summary') or claim
        conditions = a.get('conditions') if isinstance(a.get('conditions'), list) else conditions
    return {'claim': str(claim), 'category_code': kind or 'unclassified', 'mechanism': str(a.get('mechanism') or ('' if kind else a.get('reasoning') or f.get('summary') or '')), 'conditions': conditions, 'evidence': evidence, 'caveats': caveats}


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


def failure_record(case, repeat, out, reason):
    run = out / 'runs' / case['case_id'] / f'r{repeat}'
    run.mkdir(parents=True, exist_ok=True)
    failure = {'case_id': case['case_id'], 'repeat': repeat, 'findings': [],
               'insufficient_evidence_reason': reason, 'status': 'failed'}
    (run / 'failure.json').write_text(json.dumps(failure, indent=2) + '\n')
    return failure


def _as_list(value):
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)] if value else []


def run_generator(cmd, *, env, timeout, log):
    proc = subprocess.Popen(cmd, env=env, cwd=ROOT, start_new_session=True,
                            stdout=log, stderr=subprocess.STDOUT)
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        raise
    if code:
        raise subprocess.CalledProcessError(code, cmd)


def worker(case, repeat, out, raw, timeout, env, schema, swarm_template=None, enrich_llm=None, model=None, generator="paper-only", mechanism_version="paper-only-mech-v2", examples_path=None):
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
        if generator == 'swarm':
            swarm_out = run / 'swarm'
            if swarm_out.exists():
                shutil.rmtree(swarm_out)
            cmd = [sys.executable, str(ROOT / 'scripts/limitset/run_swarm_case.py'), str(case_dir), str(swarm_out)]
            with (run / 'generator.log').open('w') as log:
                run_generator(cmd, env=env, timeout=timeout, log=log)
            from paperside_bridge.swarm_to_paper_side import convert
            handoff, limitations = convert(case['case_id'], swarm_out / 'final.json', case_dir / 'paper.pdf')
            findings = []
            for lim in limitations:
                candidate = lim.swarm_provenance['candidate']
                findings.append({'claim': candidate.get('claim') or candidate.get('rule') or lim.effect_text,
                                 'category_code': lim.swarm_category or 'unclassified', 'mechanism': candidate.get('causal_argument') or '',
                                 'conditions': [lim.condition_text] if lim.condition_text != 'Unspecified' else [],
                                 'evidence': [{'source_id': 'paper', 'location': e.locator, 'support_description': e.quote} for e in lim.paper_evidence],
                                 'caveats': [], 'origin': 'swarm-s7'})
            (run / 'conversion.json').write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + '\n')
            if enrich_llm is not None:
                from pipeline.limitset_enrich import enrich
                results = [enrich(f, out / 'enrich_cache', enrich_llm, model) for f in findings]
                findings = [f for f, _ in results]
                (run / 'enrichment.json').write_text(json.dumps({'errors': [{'finding_index': i, 'enrich_error': e} for i, (_, e) in enumerate(results) if e]}, indent=2) + '\n')
            record = {'case_id': case['case_id'], 'repeat': repeat, 'findings': findings, 'sources': ['swarm-s7']}
            validate(record, schema)
            done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
            (run / 'failure.json').unlink(missing_ok=True)
            return record
        if generator == 'mechanism':
            from checklimits.checklimits.paper_only import pdf_text, mechanism_candidates
            code_files = {}
            if case['case_id'] == 'CS6223-03':
                import ast
                repo = Path('/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/InfiniGen')
                artifact = read(ROOT / 'data/infinigen/artifact.json')
                for entry in artifact['entry_points']:
                    path, symbol = entry.split('::')
                    content = (repo / path).read_text(encoding='utf-8')
                    node = ast.parse(content)
                    for part in symbol.split('.'):
                        node = next(n for n in node.body if getattr(n, 'name', None) == part)
                    lines = content.splitlines(keepends=True)
                    excerpt = ''.join(lines[node.lineno - 1:node.end_lineno])[:12000]
                    code_files[path] = code_files.get(path, '') + excerpt + '\n'
            stats = {}
            candidates, critiques, dropped = mechanism_candidates(pdf_text(case_dir / 'paper.pdf'), code_files, enrich_llm, version=mechanism_version, examples_path=examples_path, stats=stats)
            findings = []
            for c in candidates:
                findings.append({'claim': str(c.get('claim') or ''), 'category_code': c['category_code'],
                                 'mechanism': str(c.get('mechanism') or ''), 'conditions': _as_list(c.get('necessary_conditions') or c.get('conditions')),
                                 'evidence': c['evidence'], 'caveats': [], 'origin': mechanism_version})
            (run / 'mechanism_evidence.json').write_text(json.dumps({'candidates': candidates, 'dropped_for_unverified_quotes': dropped, **stats}, ensure_ascii=False, indent=2) + '\n')
            (run / 'evaluation_critiques.json').write_text(json.dumps(critiques, ensure_ascii=False, indent=2) + '\n')
            record = {'case_id': case['case_id'], 'repeat': repeat, 'findings': findings, 'sources': [mechanism_version]}
            validate(record, schema)
            done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
            (run / 'failure.json').unlink(missing_ok=True)
            return record
        swarm = safe_path(Path(swarm_template.format(case=case['case_id']))).resolve() if swarm_template else None
        if swarm and not swarm.is_file():
            swarm = None
        cmd = [sys.executable, '-m', 'pipeline.limitset', '_paper', case['case_id'], str(case_dir / 'paper.pdf'), str(run), case['title']]
        if swarm:
            cmd.append(str(swarm))
        with (run / 'generator.log').open('w') as log:
            run_generator(cmd, env=env, timeout=timeout, log=log)
        tdir = run / ('results/swarm/tests' if swarm else 'results/tests') / case['case_id']
        index = read(tdir / 'index.json')
        findings = [mapping(read(tdir / item['finding_id'] / 'report.json')) for item in index['findings']]
        source = 'swarm' if swarm else 'paper-only'
        for finding in findings:
            finding['origin'] = source
        sources = [source]
        code = ROOT / 'results/step4/infinigen/limitations_for_tests.json'
        if case['case_id'] == 'CS6223-03' and code.is_file():
            findings.extend({**mapping(f), 'origin': source} for f in read(code)['findings'])
            sources.append('results/step4/infinigen')
        if enrich_llm is not None:
            from pipeline.limitset_enrich import enrich
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=int(os.environ.get('LIMITSET_ENRICH_THREADS', '8'))) as pool:
                results = list(pool.map(lambda f: enrich(f, out / 'enrich_cache', enrich_llm, model), findings))
            enriched = [r for r, _ in results]
            errors = [{'finding_index': i, 'enrich_error': e} for i, (_, e) in enumerate(results) if e]
            findings = enriched
            (run / 'enrichment.json').write_text(json.dumps({'errors': errors}, indent=2) + '\n')
        record = {'case_id': case['case_id'], 'repeat': repeat, 'findings': findings, 'sources': sources}
        validate(record, schema)
        done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        (run / 'failure.json').unlink(missing_ok=True)
        return record
    except Exception as exc:
        return failure_record(case, repeat, out, f'{type(exc).__name__}: {exc}')


class RunnerRelay:
    def __init__(self, e2e, pipeline_run, env, out):
        self.e2e, self.pipeline_run, self.env, self.out = e2e, pipeline_run, env, out
        self.proc = None

    def __enter__(self):
        if self.e2e.relay_up():
            return self
        renv = dict(os.environ)
        renv.update(SOCLAAS_API_KEY=self.env['SOCLAAS_API_KEY'], SOCLAAS_BASE_URL=self.env['SOCLAAS_BASE_URL'])
        cmd = [sys.executable, '-m', 'checklimits.relay', '--port', str(self.e2e.RELAY_PORT),
               '--log', str(self.out / 'relay.log'), '--iface', self.env.get('SOCLAAS_IFACE', 'eth0')]
        with (self.out / 'relay.stderr').open('w') as err:
            self.proc = subprocess.Popen(cmd, cwd=self.pipeline_run.CHECKLIMITS, env=renv,
                                         stdout=subprocess.DEVNULL, stderr=err)
        for _ in range(50):
            if self.e2e.relay_up():
                return self
            if self.proc.poll() is not None:
                break
            time.sleep(0.2)
        self.__exit__(None, None, None)
        raise RuntimeError('relay did not start; see relay.stderr')

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()


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
    r.add_argument('--no-enrich', action='store_true')
    r.add_argument('--generator', choices=['paper-only', 'swarm', 'mechanism'], default='paper-only')
    r.add_argument('--mechanism-version', choices=['paper-only-mech-v1', 'paper-only-mech-v2'], default='paper-only-mech-v2')
    r.add_argument('--mechanism-examples', type=Path)
    r.add_argument('--swarm-report', help='report path template containing {case}')
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
    manifest = {'git_sha': sha, 'model_id': env.get('PIPELINE_MODEL', 'x-test-2'), 'split': a.split, 'generator': a.generator, 'mechanism_version': a.mechanism_version, 'mechanism_examples': str(a.mechanism_examples) if a.mechanism_examples else None, 'repeats': a.repeats, 'started_at': now(), 'pdf_hashes': {c['case_id']: c['pdf_sha256'] for c in selected}}
    from pipeline.limitset_enrich import PROMPT_VERSION
    manifest['enrichment'] = {'enabled': not a.no_enrich, 'model_id': manifest['model_id'], 'prompt_version': PROMPT_VERSION}
    manifest_path = out / 'run_manifest.json'
    if manifest_path.is_file():
        previous = read(manifest_path)
        if previous.get('generator', 'paper-only') != a.generator or (a.generator == 'mechanism' and (previous.get('mechanism_version', 'paper-only-mech-v1') != a.mechanism_version or previous.get('mechanism_examples') != manifest['mechanism_examples'])):
            p.error('output directory belongs to a different generator')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    jobs = [(c, n) for c in selected for n in range(1, a.repeats + 1)]
    cached = {(c['case_id'], n) for c, n in jobs
              if (out / 'runs' / c['case_id'] / f'r{n}' / 'prediction.json').is_file()}
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
        records = []
        try:
            if len(cached) == len(jobs):
                records = [read(out / 'runs' / c['case_id'] / f'r{n}' / 'prediction.json') for c, n in jobs]
                for record in records:
                    validate(record, schema)
            else:
                e = pipeline_run.env()
                env.update(e)
                # Relay's standard log paths are shared; keep this runner's logs in out.
                with RunnerRelay(e2e, pipeline_run, e, out):
                    from pipeline.limitset_enrich import RelayLLM
                    llm = None if a.no_enrich and a.generator != 'mechanism' else RelayLLM(manifest['model_id'], e2e.RELAY_PORT, timeout=900 if a.generator == 'mechanism' else 60)
                    with ThreadPoolExecutor(max_workers=a.workers) as pool:
                        records = list(pool.map(lambda job: worker(*job, out, raw, a.timeout, env, schema, a.swarm_report, llm, manifest['model_id'], a.generator, a.mechanism_version, a.mechanism_examples), jobs))
        except Exception as exc:
            reason = f'Relay startup failed: {type(exc).__name__}: {exc}'
            for c, n in jobs:
                done = out / 'runs' / c['case_id'] / f'r{n}' / 'prediction.json'
                if done.is_file():
                    record = read(done)
                    validate(record, schema)
                    records.append(record)
                else:
                    records.append(failure_record(c, n, out, reason))
        (out / 'predictions.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in records))
        manifest['counts'] = {'ok': sum(x.get('status') != 'failed' and (x['case_id'], x['repeat']) not in cached for x in records),
                              'failed': sum(x.get('status') == 'failed' for x in records),
                              'skipped': sum((x['case_id'], x['repeat']) in cached and x.get('status') != 'failed' for x in records)}
    if a.dry_run:
        manifest['counts'] = {'ok': 0, 'failed': 0, 'skipped': len(jobs)}
    manifest['finished_at'] = now()
    (out / 'run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def paper_worker(args):
    from pipeline import e2e, run
    from types import SimpleNamespace
    case, pdf, output, title, *report = args
    run.ROOT = Path(output)
    e2e.paper_only_cmd(SimpleNamespace(artifact_id=case, pdf=pdf, title=title, venue=None, model=None, swarm_report=Path(report[0]) if report else None, swarm_pdf_extractor='pypdf'))


if __name__ == '__main__':
    if sys.argv[1:2] == ['_paper']:
        paper_worker(sys.argv[2:])
    else:
        main()
