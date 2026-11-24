"""Read Z3 fixtures with Shanghao's real consumer; never run targets or agents."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch


def probe(root, folder, repo):
    sys.path[:0] = [str(root/'checklimits'), str(root)]
    from checklimits.adapter import load_task_step4
    from checklimits.agent_batch import classify_finding
    from checklimits.runner import outcome_support
    from checklimits.testreport import not_run_record, render_markdown, check_one_to_one
    from schema.models import Region
    load = lambda p: json.loads(p.read_text())
    dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n')
    finding_file = folder/'limitations_for_tests.json'
    data = load(finding_file)
    plans = {p['finding_id']:p for p in load(folder/'testability_hints.json')['hints'] if p.get('finding_id')}
    records, results = [], []
    def forbidden(*args, **kwargs):
        raise AssertionError('Z3 contract probe must not execute targets, attempts or agents')
    # These functions would start external work if accidentally invoked.
    with patch('checklimits.agent_batch.run_agent', forbidden), patch('checklimits.harness.run_attempt', forbidden):
        for raw in data['findings']:
            task = load_task_step4(raw['finding_id'], finding_file, folder/'artifact.json')
            status = classify_finding(raw['finding_id'], str(folder), str(finding_file), str(repo), root=root)
            assert status is not None, 'Fixture unexpectedly became runnable; review before executing anything'
            plan = plans[raw['finding_id']]
            region = Region.model_validate(plan['proposed_region'])
            supported, why = outcome_support(region, repo)
            diagnosis = ('Source locations exist, but adapter.region_from_limitation refuses origin=paper. '
                         if not task.regions else 'Native Region exists; consult the actual classifier result. ')
            diagnosis += 'This proposed effect also needs a custom oracle: '+why
            record = not_run_record(raw, status[0], status[1]+'; '+diagnosis,
                                    dict(source='offline Z3 contract probe; target execution not_run',
                                         findings_sha256=hashlib.sha256(finding_file.read_bytes()).hexdigest()))
            assert record.status == 'not_run' and record.verdict is None and record.level is None
            out = folder/'contract_output/tests'/raw['artifact_id']/raw['finding_id']
            out.mkdir(parents=True, exist_ok=True)
            dump(out/'report.json',record.model_dump(mode='json')); records.append(record)
            results.append(dict(finding_id=raw['finding_id'], native_schema_loaded=True,
                                paper_locations_supplied=sum(len(l.code_evidence) for l in task.limitations),
                                native_region_count=len(task.regions), native_classifier=dict(code=status[0],reason=status[1]),
                                proposed_region_schema_valid=True, proposed_region_supported=supported,
                                proposed_region_reason=why, diagnosis=diagnosis))
    art = load(folder/'artifact.json')
    markdown = render_markdown(art,records,None,'limitations_for_tests.json',hashlib.sha256(finding_file.read_bytes()).hexdigest())
    markdown = '> Offline contract-format demonstration only. No target, agent, environment probe or tests ran.\n\n'+markdown
    problems = check_one_to_one([r['finding_id'] for r in data['findings']],records,markdown)
    assert not problems, problems
    out = folder/'contract_output/report'/art['artifact_id'];out.mkdir(parents=True,exist_ok=True)
    (out/'LIMITATIONS.md').write_text(markdown.rstrip()+'\n')
    result = dict(consumer_root=str(root), consumer_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
                  consumer_files_sha256={name:hashlib.sha256((root/'checklimits'/name).read_bytes()).hexdigest() for name in ['CONTRACT_TEST_REPORT.md','REQUESTS_TO_STEP4.md','checklimits/adapter.py','checklimits/agent_batch.py','checklimits/testreport.py']},
                  adapter_sha256=hashlib.sha256((root/'checklimits/checklimits/adapter.py').read_bytes()).hexdigest(),
                  checks=results,n_input=len(data['findings']),n_records=len(records),one_to_one=True,
                  model_api_calls=0,target_execution='not_run',environment_precheck='not_run',
                  status='contract_readable_but_not_executable_by_current_consumer')
    dump(folder/'consumer_contract_check.json',result)
    index=folder/'package-index.json'
    if index.exists():
        previous=load(index)
        previous['files']={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and p!=index}
        dump(index,previous)
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer-root',required=True,type=Path)
    parser.add_argument('--handoff',required=True,type=Path)
    parser.add_argument('--repo',required=True,type=Path)
    args=parser.parse_args();probe(args.consumer_root.resolve(),args.handoff.resolve(),args.repo.resolve())
