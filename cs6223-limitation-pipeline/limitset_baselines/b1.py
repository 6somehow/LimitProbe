"""One-shot paper (and optionally pinned source) baseline."""
import json
import subprocess
import time
import urllib.request
from pathlib import Path

from limitset_baselines.common import write_json
from pipeline.limitset import ROOT

CHAR_BUDGET = 400_000


def pinned_code(case, paper, env):
    if case['case_id'] != 'CS6223-03':
        return '', 'not applicable'
    repo = ROOT / 'third_party/InfiniGen'
    commit = case['repository']['commit']
    listing = subprocess.run(['git', '-C', str(repo), 'ls-tree', '-rl', '--full-tree', commit],
                             env=env, check=True, capture_output=True, text=True).stdout
    entries = []
    for line in listing.splitlines():
        meta, name = line.split('\t', 1)
        mode, kind, oid, size = meta.split()
        if kind == 'blob':
            entries.append((name, oid, int(size)))
    if sum(size for _, _, size in entries) + len(paper) > CHAR_BUDGET:
        return '', 'omitted: repository exceeds character budget'
    chunks = []
    for name, oid, _ in entries:
        blob = subprocess.run(['git', '-C', str(repo), 'cat-file', 'blob', oid], env=env,
                              check=True, capture_output=True).stdout
        try:
            chunks.append(f'\n--- {name} ---\n' + blob.decode('utf-8'))
        except UnicodeDecodeError:
            continue
    code = ''.join(chunks)
    if len(paper) + len(code) > CHAR_BUDGET:
        return '', 'omitted: repository exceeds character budget'
    return code, 'included'


def request(payload):
    req = urllib.request.Request('http://127.0.0.1:8787/v1/chat/completions',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json',
        'Authorization': 'Bearer relay'})
    with urllib.request.urlopen(req, timeout=600) as response:
        return json.load(response)


def run_case(case, input_dir, out_dir, env, repeat):
    import fitz
    started = time.monotonic()
    with fitz.open(input_dir / 'paper.pdf') as pdf:
        paper = '\n'.join(page.get_text() for page in pdf)
    code, code_status = pinned_code(case, paper, env)
    prompt = ('Find the limitations of this method. Return only a JSON object with a findings array. '
              'Each finding must have claim, category_code, mechanism, conditions, evidence, and caveats. '
              'category_code is applicability_limitation, mechanism_origin_unclear, method_shortcoming, or unclassified. '
              'conditions and caveats are arrays of strings; evidence is an array of objects with source_id, location, '
              'and optional support_description.\n\nPaper:\n' + paper)
    if code:
        prompt += '\n\nPinned repository:\n' + code
    payload = {'model': env.get('PIPELINE_MODEL', 'x-test-2'), 'temperature': 0,
               'messages': [{'role': 'user', 'content': prompt}]}
    if env.get('LIMITSET_GEN_OMIT_SAMPLING'):  # e.g. Claude Sonnet 5.5 rejects `temperature`
        payload.pop('temperature')
        payload['max_tokens'] = 16000  # the Anthropic API requires max_tokens
    write_json(out_dir / 'request.json', payload)
    write_json(out_dir / 'input_info.json', {'code': code_status, 'paper_characters': len(paper), 'character_budget': CHAR_BUDGET})
    write_json(out_dir / 'cost.json', {'calls': 1, 'prompt_tokens': None,
               'completion_tokens': None, 'wall_seconds': time.monotonic() - started})
    response = request(payload)
    write_json(out_dir / 'response.json', response)
    usage = response.get('usage') or {}
    cost = {'calls': 1, 'prompt_tokens': usage.get('prompt_tokens'),
            'completion_tokens': usage.get('completion_tokens'), 'wall_seconds': time.monotonic() - started}
    write_json(out_dir / 'cost.json', cost)
    parsed = json.loads(response['choices'][0]['message']['content'])
    if not isinstance(parsed, dict) or not isinstance(parsed.get('findings'), list):
        raise ValueError('response must be an object with a findings array')
    findings = []
    for finding in parsed['findings']:
        if not isinstance(finding, dict):
            raise ValueError('finding must be an object')
        finding = dict(finding)
        finding.setdefault('category_code', 'unclassified')
        finding.setdefault('mechanism', '')
        finding.setdefault('conditions', [])
        finding.setdefault('evidence', [])
        finding.setdefault('caveats', [])
        findings.append(finding)
    return {'findings': findings, 'cost': cost}
