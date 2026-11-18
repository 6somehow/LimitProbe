"""Migrate reviewed handoffs, checking parameter mappings from pinned paper and Git.

This is an offline reviewed-fixture adapter, not an automatic mapping discovery run.
No target imports, model calls or target execution.
"""
import argparse
import ast
from dataclasses import asdict
from pathlib import Path
import shutil
import subprocess
import tempfile

from pypdf import PdfReader
from paperprobe.delivery import TEAM, span_evidence
from paperprobe.io import read_json, write_json, file_sha256
import sys
sys.path.insert(0, str(TEAM))
from schema.models import SCHEMA_VERSION, Artifact, Binding, Claim, ScopeItem, EvalPoint, Limitation, Condition
from codeside.verify3b import load_paper_side
from codeside.scope_check import ScopeChecker
from codeside.witness import solve
from publish_handoff import FILES
from validate_delivery import validate

ROOT = Path(__file__).resolve().parents[1]


def functions(source):
    result = {}
    def visit(body, prefix=''):
        for node in body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + node.name
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[name] = node
                visit(node.body, name + '.')
    visit(ast.parse(source).body)
    return result


def checked_mapping(spec, source, pages, commit):
    defs = functions(source)
    fn = defs[spec['function']]
    arg = next(a for a in fn.args.args + fn.args.kwonlyargs if a.arg == spec['parameter'])
    annotation = ast.unparse(arg.annotation) if arg.annotation else ''
    assert ('int' if spec['type'] == 'integer' else 'float') in annotation, 'Parameter type not evidenced'
    lines = source.split('\n')
    packets = []
    def snippet(lo, hi):
        assert 1 <= lo <= hi <= len(lines)
        packet = dict(repo='primary', path=spec['path'], commit=commit, start_line=lo, end_line=hi,
                      lines='\n'.join(f'{i}: {lines[i-1]}' for i in range(lo, hi + 1)))
        packets.append(packet)
        return dict(file=spec['path'], function=spec['function'], line_start=lo, line_end=hi,
                    snippet='\n'.join(lines[lo-1:hi]))
    declaration = snippet(arg.lineno, arg.end_lineno)
    reads = []
    for check in spec['source_checks']:
        expected = ast.dump(ast.parse(check['expression']).body[0], include_attributes=False)
        matches = [n for n in ast.walk(defs[check['function']]) if isinstance(n, ast.stmt)
                   and ast.dump(n, include_attributes=False) == expected]
        assert len(matches) == 1, f'Expected source step changed: {check["function"]}'
        node = matches[0]
        reads.append(dict(function=check['function'], **{k: v for k, v in snippet(node.lineno, node.end_lineno).items() if k != 'function'}))
    evidence = span_evidence(spec['paper_spans'], pages)
    mapping = dict(binding_id=spec['binding_id'], paper_term=spec['paper_term'], code_parameter=spec['parameter'],
                   code_type=spec['type'], unit=spec['unit'], owner=spec['function'], repo='primary', commit=commit,
                   role=spec['role'], scope_qualifier=spec['scope_qualifier'], paper_evidence=evidence,
                   declaration=declaration, code_steps=reads, status='source_checked_by_agent_not_human_gold',
                   integer_domain_note='Integer positivity becomes >=1. Shared scope solver uses reals; fixtures pin integer values. Full discrete-domain inference is not claimed.' if spec['type'] == 'integer' else None)
    return mapping, packets


def typed_witness_valid(witness, name, code_type):
    if code_type != 'integer':
        return True
    values = [witness[point][name] for point in ['trigger', 'contrast'] if name in witness.get(point, {})]
    return all(isinstance(value, (int, float)) and not isinstance(value, bool) and float(value).is_integer() for value in values)


def refresh_distribution(folder, source, generated):
    record = dict(artifact_id=read_json(folder/'artifact.json')['artifact_id'], format='schema 0.2.0 reviewed lightweight handoff',
                  source_handoff=str(source), omitted=['Original PDF, target repository, raw API calls, ZIP and HTML dashboards'],
                  release_generated_files=generated,
                  note='v1 files are historical evidence. Migration changes schema metadata and explicitly reviewed scope/bindings only; no conformance verdicts or claim statements rewritten.',
                  included={p.name: file_sha256(p) for p in sorted(folder.iterdir()) if p.is_file() and p.name != 'source-distribution.json'})
    write_json(folder/'source-distribution.json', record)


def adapt(source, output, repo, pdf, spec_path):
    assert SCHEMA_VERSION == '0.2.0', 'Adapter reviewed only for shared schema 0.2.0'
    source, output = source.resolve(), output.absolute()
    assert not output.exists(), 'Output exists; preserve the previous reviewed handoff'
    artifact = read_json(source/'artifact.json'); aid = artifact['artifact_id']; commit = artifact['commit']
    assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == commit, 'Wrong target commit'
    pins = read_json(ROOT/'workstreams/zhaopeng/team-reviewed.json')[aid]
    assert file_sha256(pdf) == pins['pdf_sha256'], 'Wrong paper PDF'
    pages = [p.extract_text() or '' for p in PdfReader(pdf).pages]
    specifications = [s for s in read_json(spec_path)['mappings'] if s['artifact'] == aid]
    assert specifications, 'No reviewed mapping specification for this artifact'
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.schema02-') as temp:
        folder = Path(temp)/aid; folder.mkdir()
        for p in source.iterdir():
            if p.is_file() and p.name in FILES | {'original-bundle-index.json'}:
                shutil.copyfile(p, folder/p.name)
        for name in ['paper_side.json', 'validation.json', 'consumer_schema.snapshot.py']:
            shutil.copyfile(source/name, folder/('legacy-' + name))
        for name in ['archive-acceptance.json', 'corpus-acceptance.json']:
            if (folder/name).exists():
                (folder/name).rename(folder/('legacy-' + name))
        original = read_json(source/'paper_side.json')
        data = {field: [dict(r, schema_version=SCHEMA_VERSION) for r in original[field]] for field in original}
        for field, model in [('claims', Claim), ('scope', ScopeItem), ('eval_points', EvalPoint), ('bindings', Binding)]:
            data[field] = [model.model_validate(r).model_dump(mode='json') for r in data[field]]
        packets = read_json(folder/'source_reads.json'); mappings = []
        for spec in specifications:
            code = subprocess.check_output(['git', '-C', str(repo), 'show', f'{commit}:{spec["path"]}'], text=True)
            mapping, new_packets = checked_mapping(spec, code, pages, commit)
            packets.extend(new_packets); mappings.append(mapping)
            scope = next((r for r in data['scope'] if r['scope_id'] == spec['scope_id']), None)
            if scope is None:
                assert spec.get('scope'), 'New parameter needs paper-supported scope'
                scope = ScopeItem(scope_id=spec['scope_id'], artifact_id=aid, param=spec['paper_term'],
                                  unit=spec['unit'], evidence=mapping['paper_evidence'], **spec['scope']).model_dump(mode='json')
                data['scope'].append(scope)
            assert scope['param'] == spec['paper_term']
            binding = Binding(binding_id=spec['binding_id'], artifact_id=aid, paper_term=spec['paper_term'],
                              kind='parameter', code_symbol=spec['parameter'], certain=True, location=mapping['declaration'],
                              rationale=f'Static source-assisted mapping; scope-qualified, not human gold. {spec["role"]} {spec["scope_qualifier"]}').model_dump(mode='json')
            data['bindings'] = [b for b in data['bindings'] if b['binding_id'] != binding['binding_id']] + [binding]
        write_json(folder/'paper_side.json', data)
        write_json(folder/'source_reads.json', list({(p['repo'],p['path'],p['start_line'],p['end_line']):p for p in packets}.values()))
        write_json(folder/'parameter_mappings.json', dict(method='Reviewed evidence-backed fixtures, no model calls or target execution', mappings=mappings))
        write_json(folder/'limitations.json', [Limitation.model_validate(dict(r, schema_version=SCHEMA_VERSION)).model_dump(mode='json') for r in read_json(folder/'limitations.json')])
        artifact = Artifact.model_validate(dict(artifact, schema_version=SCHEMA_VERSION)).model_dump(mode='json')
        write_json(folder/'artifact.json', artifact)
        manifest = read_json(folder/'manifest.json'); manifest['artifact'] = artifact
        write_json(folder/'manifest.json', manifest)
        shutil.copyfile(TEAM/'schema/models.py', folder/'consumer_schema.snapshot.py')
        checker = ScopeChecker(*load_paper_side(str(folder/'paper_side.json')))
        checks = []
        for spec in specifications:
            for probe in spec['cases']:
                condition = Condition(expr=probe['expr'], params=[spec['parameter']], path_prefix=probe.get('path_prefix', []))
                result = checker.check(condition); witness = solve(condition, checker)
                assert result.scope_status == probe['expected_scope'], (probe, result)
                typed = typed_witness_valid(witness, spec['parameter'], spec['type'])
                passed = witness['status'] == probe['expected_witness'] and typed
                assert passed or probe.get('known_upstream_failure'), (probe, witness)
                if witness['status'] == 'solved': assert witness.get('from_paper'), 'Paper bounds absent from witness'
                checks.append(dict(binding_id=spec['binding_id'], owner=spec['function'],
                                   purpose='Consumer contract probe, not an extracted limitation or target-system test',
                                   input=condition.model_dump(mode='json'), scope_result=asdict(result), witness=witness,
                                   expected_scope=probe['expected_scope'], expected_witness=probe['expected_witness'],
                                   code_parameter=spec['parameter'], code_type=spec['type'], typed_values_valid=typed,
                                   fixture_domain_note='The finite set in path_prefix is a contract-test input domain, not an extracted code path or paper scope.' if probe.get('path_prefix') else None,
                                   passed=passed, known_upstream_failure=probe.get('known_upstream_failure') if not passed else None))
        write_json(folder/'consumer_cases.json', dict(schema_version=SCHEMA_VERSION, cases=checks, target_execution='not_run'))
        validation = read_json(source/'validation.json')
        if 'interface_review' in validation:
            validation['legacy_interface_review'] = validation.pop('interface_review')
        existing = []
        for row in read_json(TEAM/'results/pipeline'/aid/'limitations.json'):
            result = checker.check(Limitation.model_validate(row).condition)
            existing.append(dict(limitation_id=row['limitation_id'], scope_status=result.scope_status, evaluated_in_paper=result.evaluated_in_paper, reason=result.reason))
        validation.update(counts={k:len(v) for k,v in data.items()}, shared_schema_sha256=file_sha256(TEAM/'schema/models.py'),
                          active_solver_bindings=sum(b['kind'] != 'mechanism_entry' for b in data['bindings']),
                          wanting_existing_conditions=existing, shared_schema_version=SCHEMA_VERSION,
                          parameter_mapping_records=len(mappings), consumer_contract_cases=len(checks),
                          consumer_contract_passed=sum(c['passed'] for c in checks), consumer_known_failures=sum(not c['passed'] for c in checks),
                          migration_source_sha256=file_sha256(source/'paper_side.json'),
                          migration='Metadata to 0.2.0 + explicit reviewed parameter/scope additions; original conformance unchanged')
        write_json(folder/'validation.json', validation)
        write_json(folder/'migration.json', dict(consumer_commit=subprocess.check_output(['git','-C',str(TEAM),'rev-parse','HEAD'],text=True).strip(),
                   schema_version=SCHEMA_VERSION, source_handoff=str(source), source_paper_side_sha256=file_sha256(source/'paper_side.json'),
                   mapping_spec_sha256=file_sha256(spec_path), paper_sha256=file_sha256(pdf), code_commit=commit,
                   model_api_calls=0, target_execution='not_run', conformance_unchanged=file_sha256(source/'conformance.json')==file_sha256(folder/'conformance.json'),
                   note='Legacy review/archive files refer to v1, not a fresh 0.2.0 experiment. Certain mapping means checked identity, not implementation correctness.'))
        (folder/'README.md').write_text(f'# {aid} · schema 0.2.0 交接样例\n\n直接输入：`paper_side.json`；整合差异另读 `limitations.json`。\n\n先看 `parameter_mappings.json` 的论文/代码对照，再看 `consumer_cases.json` 的下游实际求解结果。所有案例是接口探针，不是新 Finding，也没有运行目标系统。\n\n原版本保留在 `legacy-*` 文件及 [v1 包](../../paper-side-v1/{aid}/)；`conformance.json` 未改变。新增 Pool2d 范围仅适用于该算子；正整数核大小只是必要条件，不保证整个配置有效。完整来源见 `migration.json`，历史审阅仍指 v1。\n')
        (folder/'RUN_WITH_WANTING.md').write_text(f'# 接入\n\n从团队根目录运行既有 verify3b/pipeline 命令，指定 `--paper-side paperside/handoffs/paper-side-v2/{aid}/paper_side.json`，整合阶段指定 `--paper-dir paperside/handoffs/paper-side-v2/{aid}`。其余 PDF、repo 与输入文件按实际环境提供。\n\n离线验证：从 paperside 运行 `python scripts/validate_delivery.py handoffs/paper-side-v2/{aid}`。原 v1 调用日志没有重新生成；真实模型调用和目标执行均为零。\n')
        refresh_distribution(folder, source, ['parameter_mappings.json','consumer_cases.json','migration.json'])
        validate(folder, {n+1:p for n,p in enumerate(pages)})
        folder.rename(output)
    print(f'ADAPTED {aid}: {len(mappings)} mappings / {len(checks)} real consumer probes; output {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--pdf', required=True, type=Path)
    parser.add_argument('--mapping-spec', type=Path, default=ROOT/'workstreams/zhaopeng/parameter-mappings-v2.json')
    args = parser.parse_args()
    adapt(args.source, args.out, args.repo, args.pdf, args.mapping_spec)
