"""Run the archived s7 swarm on an isolated paper-only case."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'paperside/tools/papertest-swarm'))
from swarmlab import cell
from swarmlab.runner import DEFAULT_PROTOCOL
from swarmlab.contract import parse_finding_report
from pypdf import PdfReader


def main(case_dir, out):
    case_dir, out = Path(case_dir).resolve(), Path(out).resolve()
    forbidden = {'labels', 'reference_material', 'evaluator_evidence', 'reference'}
    if forbidden.intersection(case_dir.parts) or forbidden.intersection(out.parts):
        raise ValueError('blindness violation')
    if {p.name for p in case_dir.iterdir()} != {'paper.pdf', 'case.json'}:
        raise ValueError('expected isolated paper.pdf and case.json')
    case = json.loads((case_dir / 'case.json').read_text())
    case_id = case['case_id']
    inputs = out / 'inputs' / case_id
    inputs.mkdir(parents=True, exist_ok=False)
    pages = [{'page': i, 'text': page.extract_text() or ''} for i, page in enumerate(PdfReader(case_dir / 'paper.pdf').pages, 1)]
    (inputs / 'paper.json').write_text(json.dumps(pages))
    (inputs / 'source.json').write_text(json.dumps({'paper_id': case_id, 'repo': None, 'commit': None}))
    cell.secret_env = lambda: {'SOCLAAS_API_KEY': 'placeholder', 'SOCLAAS_BASE_URL': 'http://127.0.0.1:8787/v1'}
    protocol = {**DEFAULT_PROTOCOL, 'two_phase': True, 'max_report_candidates': 6}
    run = cell.Cell(inputs.parent, case_id, 'gap_receipt_swarm', out / 'cell', protocol)
    result = run.run()
    if result['error'] or not result['validation']['json_parsed']:
        raise RuntimeError(f"swarm failed: {result['error'] or result['validation']}")
    report = parse_finding_report((out / 'cell/final.txt').read_text())['data']
    report['origin'] = 'swarm-s7'
    (out / 'final.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: run_swarm_case.py CASE_DIR OUT_DIR')
    main(*sys.argv[1:])
