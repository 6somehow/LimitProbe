"""Blind, isolated opencode baseline for one limitset case."""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path('<project-root>')
DEFAULT_OPENCODE = MAIN / 'checklimits/scratch/opencode/node_modules/opencode-linux-x64/bin/opencode'
HOME_TEMPLATE = MAIN / 'checklimits/scratch/oc_home_template'
PROMPT = ('Find the limitations of this method. Write your findings to findings.md. '
          'Return a JSON list of findings with claim, category_code, mechanism, conditions, '
          'and evidence quotes (source_id, location, support_description).')
CATEGORIES = {'applicability_limitation', 'mechanism_origin_unclear', 'method_shortcoming', 'unclassified'}
FORBIDDEN = {'labels', 'reference_material', 'evaluator_evidence'}


def _parse(text):
    failures = []
    raw = text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)```', raw, re.S | re.I)
    if match:
        raw = match.group(1).strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = data.get('findings')
        if not isinstance(data, list):
            raise ValueError('expected a list')
    except (ValueError, TypeError):
        data = [{'claim': m.group(1).strip()} for line in text.splitlines()
                if (m := re.match(r'^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)', line))]
        if not data:
            return [], ['Could not parse JSON or bullet/numbered findings']
        failures.append('JSON parsing failed; extracted bullet/numbered findings')
    findings = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get('claim'), str) or not item['claim'].strip():
            failures.append('Skipped finding without a string claim')
            continue
        category = item.get('category_code')
        if category not in CATEGORIES:
            if category:
                failures.append('Unrecognized category_code: ' + str(category))
            category = 'unclassified'
        def strings(value):
            return [x for x in value if isinstance(x, str)] if isinstance(value, list) else []
        evidence = []
        for ev in item.get('evidence', []) if isinstance(item.get('evidence'), list) else []:
            if isinstance(ev, dict) and isinstance(ev.get('source_id'), str) and isinstance(ev.get('location'), str):
                evidence.append({k: ev[k] for k in ('source_id', 'location', 'support_description') if isinstance(ev.get(k), str)})
            else:
                failures.append('Skipped evidence without source_id and location')
        finding = {'claim': item['claim'], 'category_code': category,
                   'mechanism': item.get('mechanism') if isinstance(item.get('mechanism'), str) else '',
                   'conditions': strings(item.get('conditions')), 'evidence': evidence,
                   'caveats': strings(item.get('caveats'))}
        for key in ('disclosure_status', 'runtime_verdict'):
            if key in item and ((key == 'disclosure_status' and item[key] in ('reported_in_paper', 'inferred', 'uncertain')) or
                                (key == 'runtime_verdict' and (item[key] is None or isinstance(item[key], str)))):
                finding[key] = item[key]
        findings.append(finding)
    return findings, failures


def run_case(case, input_dir, out_dir, env, repeat):
    case_id = case if isinstance(case, str) else case['case_id']
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = out / 'workspace'
    work.mkdir()  # Refuse reuse: every run must start empty.
    source = Path(input_dir).resolve()
    copied = []
    for p in source.rglob('*'):
        rel = p.relative_to(source)
        if FORBIDDEN.intersection(rel.parts) or p.is_symlink() or not p.is_file() or p.suffix.lower() not in ('.pdf', '.txt'):
            continue
        dest = work / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        copied.append(str(rel))
    if not any(x.lower().endswith('.pdf') for x in copied):
        raise ValueError('isolated input must contain a PDF')
    if not any(x.lower().endswith('.txt') for x in copied):
        import fitz  # the driver supplies only paper.pdf: extract its text for the agent's read tools
        pdf = next(work / x for x in copied if x.lower().endswith('.pdf'))
        with fitz.open(pdf) as doc:
            (work / 'paper.txt').write_text('\n'.join(page.get_text() for page in doc), encoding='utf-8')
    home = out / 'home'
    if HOME_TEMPLATE.is_dir():
        shutil.copytree(HOME_TEMPLATE, home, symlinks=False)
    else:
        home.mkdir()
    config = {'model': 'relay/x-test-2', 'small_model': 'relay/x-test-2', 'autoupdate': False,
              'share': 'disabled', 'snapshot': False,
              'provider': {'relay': {'npm': '@ai-sdk/openai-compatible', 'name': 'checklimits relay',
                  'options': {'baseURL': 'http://127.0.0.1:8787/v1', 'apiKey': 'placeholder-not-a-secret'},
                  'models': {'x-test-2': {'name': 'x-test-2', 'tool_call': True, 'reasoning': True,
                                          'limit': {'context': 128000, 'output': 16000}}}}},
              'permission': {'edit': {'*': 'deny', 'findings.md': 'allow', '*/findings.md': 'allow'},
                             'bash': 'deny', 'webfetch': 'deny', 'websearch': 'deny',
                             'external_directory': 'deny', 'doom_loop': 'deny'}}
    config_path = out / 'opencode.json'
    config_path.write_text(json.dumps(config, indent=2))
    executable = Path(env.get('LIMITSET_OPENCODE', str(DEFAULT_OPENCODE))).resolve()
    child_env = {'PATH': '/usr/bin:/bin:/usr/local/bin', 'HOME': str(home), 'LANG': 'C.UTF-8', 'TERM': 'dumb',
                 'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_DATA_HOME': str(home / '.local/share'),
                 'XDG_CACHE_HOME': str(home / '.cache'), 'XDG_STATE_HOME': str(home / '.local/state'),
                 'OPENCODE_CONFIG': str(config_path), 'OPENCODE_DISABLE_AUTOUPDATE': '1',
                 'OPENCODE_DISABLE_MODELS_FETCH': '1', 'OPENCODE_DISABLE_LSP_DOWNLOAD': '1',
                 'OPENCODE_DISABLE_CLAUDE_CODE': '1', 'OPENCODE_DISABLE_EXTERNAL_SKILLS': '1',
                 'npm_config_offline': 'true'}
    # A minimal filesystem, rather than a read-only host mount, prevents access to other cases.
    cmd = ['bwrap', '--die-with-parent', '--unshare-pid', '--new-session', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp']
    for path in ('/usr', '/bin', '/lib', '/lib64', '/etc/ssl', '/etc/resolv.conf'):
        if Path(path).exists():
            cmd += ['--ro-bind', path, path]
    cmd += ['--ro-bind', str(executable), str(executable), '--bind', str(home), str(home),
            '--ro-bind', str(config_path), str(config_path), '--bind', str(work), str(work), '--chdir', str(work),
            str(executable), 'run', '--format', 'json', '--model', 'relay/x-test-2', '--dir', str(work), PROMPT]
    started = time.monotonic()
    proc = subprocess.Popen(cmd, env=child_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=float(env.get('LIMITSET_OPENCODE_TIMEOUT', '1800')))
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    wall = time.monotonic() - started
    (out / 'events.jsonl').write_text(stdout)
    (out / 'stderr.txt').write_text(stderr)
    final = ''
    turns = calls = prompt_tokens = completion_tokens = 0
    token_seen = False
    backend = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        part = event.get('part') or {}
        if event.get('type') == 'text':
            final = part.get('text', final)
        elif event.get('type') == 'step_finish':
            turns += 1
            tokens = part.get('tokens') or {}
            if 'input' in tokens or 'output' in tokens:
                token_seen = True
                prompt_tokens += tokens.get('input') or 0
                completion_tokens += tokens.get('output') or 0
        elif event.get('type') == 'tool_use' and (part.get('state') or {}).get('status') in ('completed', 'error'):
            calls += 1
        backend = event.get('modelID') or part.get('modelID') or backend
    findings_file = work / 'findings.md'
    findings, failures = _parse(findings_file.read_text() if findings_file.is_file() else final)
    if proc.returncode or timed_out:
        failures.append('opencode timed out' if timed_out else f'opencode exited {proc.returncode}')
    version = env.get('LIMITSET_OPENCODE_VERSION', '1.19.5' if executable == DEFAULT_OPENCODE else 'unknown')
    result = {'findings': findings, 'cost': {'calls': turns, 'prompt_tokens': prompt_tokens if token_seen else None,
              'completion_tokens': completion_tokens if token_seen else None, 'wall_seconds': wall, 'turns': turns,
              'tool_version': version, 'model_id': backend, 'prompt': PROMPT},
              'parse_failures': failures, 'tool_calls': calls, 'exit_code': proc.returncode,
              'input_note': 'paper only; pinned InfiniGen unavailable or not verified' if case_id == 'CS6223-03' else 'paper only',
              'repeat': repeat}
    (out / 'b2_result.json').write_text(json.dumps(result, indent=2))
    return result
