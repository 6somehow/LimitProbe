"""Validate Z3 evidence/contract records; never execute target code."""
import argparse
import ast
from pathlib import Path
import re
import subprocess
import sys

from paperprobe.io import read_json, file_sha256
from paperprobe.delivery import TEAM
sys.path.insert(0,str(TEAM))
from schema.models import Artifact, Finding, Limitation, Region

ROOT=Path(__file__).resolve().parents[1]


def validate(folder,repo=None,pdf=None):
    artifact=Artifact.model_validate(read_json(folder/'artifact.json'))
    aid=artifact.artifact_id
    source=ROOT/'handoffs/paper-side-v2'/aid
    proof=read_json(folder/'provenance.json')
    assert file_sha256(source/'conformance.json')==proof['conformance_sha256']
    original=read_json(source/'conformance.json')
    expected={r['id'] for r in original if r['artifact']['review_state']=='completed' and r['artifact']['verdict']!='supports'}
    hints=read_json(folder/'testability_hints.json')['hints']
    assert {h['behavior'] for h in hints}==expected and len(hints)==len(expected), 'Missing or duplicate Z3 triage'
    assert all(h['target_execution']=='not_run' for h in hints)
    expanded=[h for h in hints if h.get('finding_id')]
    assert len(expanded)==proof['expanded_cases']==1
    data=read_json(folder/'limitations_for_tests.json')
    assert data['schema_version']=='0.2.0' and len(data['findings'])==1
    ids=[]
    for raw in data['findings']:
        record={k:v for k,v in raw.items() if k not in ['limitations','verifications']}
        finding=Finding.model_validate(record);ids.append(finding.finding_id)
        assert finding.category=='impl_deviates' and finding.effect_type=='other'
        assert finding.witness_hint['status']=='unknown' and finding.witness_hint['trigger'] is None
        for l in raw['limitations']:
            lim=Limitation.model_validate(l)
            assert lim.origin=='paper' and lim.code_evidence and lim.paper_evidence, 'Do not forge code origin or omit source'
    packets=read_json(folder/'source_reads.json')
    lines={}
    for p in packets:
        assert p['commit']==artifact.commit
        for i,line in enumerate(p['lines'].split('\n'),p['start_line']):
            assert line.startswith(f'{i}: ')
            value=line.split(': ',1)[1];key=(p['path'],i)
            assert key not in lines or lines[key]==value
            lines[key]=value
        if repo:
            blob=subprocess.check_output(['git','-C',str(repo),'show',f'{artifact.commit}:{p["path"]}'],text=True).split('\n')
            assert p['lines']=='\n'.join(f'{i}: {blob[i-1]}' for i in range(p['start_line'],p['end_line']+1)), 'Source drift'
    for hint in expanded:
        Region.model_validate(hint['proposed_region'])
        ast.parse(hint['machine_condition'],mode='eval')
        assert hint['effect_type']=='other' and hint['blockers']
        for loc in [hint['target']]+hint['related_locations']:
            assert loc['snippet']=='\n'.join(lines[(loc['file'],i)] for i in range(loc['line_start'],loc['line_end']+1))
        for edge in hint['call_chain']:
            assert edge['call']=='\n'.join(lines[(edge['file'],i)] for i in range(edge['line_start'],edge['line_end']+1))
            assert edge['formal_parameter_map']
        if pdf:
            from pypdf import PdfReader
            assert file_sha256(pdf)==proof['pdf_sha256']
            pages=[p.extract_text() or '' for p in PdfReader(pdf).pages]
            assert all(e['quote'] in pages[int(re.search(r'p\.(\d+)',e['locator'])[1])-1] for e in hint['paper_evidence'])
    check=read_json(folder/'consumer_contract_check.json')
    assert check['n_input']==check['n_records']==len(ids) and check['one_to_one']
    assert check['target_execution']=='not_run' and check['model_api_calls']==0
    for result in check['checks']:
        assert result['native_schema_loaded'] and result['paper_locations_supplied']>0
        assert result['native_region_count']==0 and result['native_classifier']['code']=='no_code_location'
        assert result['proposed_region_supported'] is False
    for fid in ids:
        result=read_json(folder/'contract_output/tests'/aid/fid/'report.json')
        assert result['finding_id']==fid and result['schema_version']=='checklimits-test-report/1'
        assert result['status']=='not_run' and result['verdict'] is None and result['level'] is None
        assert result['not_run']['reason'] and result['confidence_label']=='uncalibrated' and result['calibrated'] is False
    index=folder/'package-index.json'
    if index.exists():
        assert read_json(index)['files']=={str(p.relative_to(folder)):file_sha256(p) for p in folder.rglob('*') if p.is_file() and p!=index}, 'Stale Z3 archive index'
    print(f'Z3 {aid}: {len(hints)} triaged; 1 expanded; schema/evidence and truthful not_run output checked; no target execution')
    return dict(artifact=aid,triaged=len(hints),expanded=len(expanded),target_execution='not_run')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path);p.add_argument('--repo',type=Path);p.add_argument('--pdf',type=Path)
    a=p.parse_args();validate(a.folder,a.repo,a.pdf)
