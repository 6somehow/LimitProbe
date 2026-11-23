"""Single DeepSeek session with the same read-only evidence as the team framework."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil
import runpy
import time
import urllib.request

from pilot import Cell, HERE, JOINT_PROMPTS, TOOLS, dump, sha, validate_answer


def prepare(root, reference, paper, stream=False):
    protocol = json.loads((reference / 'protocol.json').read_text())
    assert protocol['reasoning_effort'] == 'max'
    ref_index = json.loads((reference / 'input-index.json').read_text())
    inputs = [name for name in ref_index if name.startswith(f'{paper}/')]
    assert len(inputs) > 2
    root.mkdir(parents=True)
    for name in inputs:
        source = reference / name
        assert sha(source.read_bytes()) == ref_index[name], name
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    evidence_meta = json.loads((root / paper / 'source.json').read_text())
    paper_only = evidence_meta['repo'] is None
    system = (HERE / 'prompts/system.txt').read_text()
    old, replacement = JOINT_PROMPTS['system.txt'][0]
    assert system.count(old) == 1
    system = system.replace(old, replacement)
    system = system.replace('Deliver at most three candidates;', 'Deliver at most six candidates;')
    system += (
        '\nSeparately report up to eight author-disclosed method boundaries or weaker experimental results '
        'in known_boundaries. Each contains title, mechanism, conditions, paper_evidence (page and quote), '
        'and what_is_not_established. These do not count against the six additional candidates.\n'
    )
    task = (HERE / 'prompts/task.txt').read_text()
    old, replacement = JOINT_PROMPTS['task.txt'][0]
    assert task.count(old) == 1
    task = task.replace(old, replacement)
    if paper_only:
        start = system.index(JOINT_PROMPTS['system.txt'][0][1])
        end = system.index('\n\n', start)
        system = system[:start] + (
            'Only the original paper is supplied. Use its methods, evaluation and limitations sections to '
            'test plausible diagnoses. Consider competing explanations and observed experimental conditions.'
        ) + system[end:]
        system = system.replace(
            'Tools search only the supplied original paper and author repository at the fixed commit.',
            'The only evidence tool reads original paper pages. Leave code_evidence empty and identify any claim that would require source code.')
        task = (
            'Analyze the supplied original paper for scientifically consequential limitations of its method. '
            'Use the original paper evidence to support or reject your hypotheses. Return the requested JSON.\n'
        )
    (root / 'system.txt').write_text(system)
    (root / 'task.txt').write_text(task)
    protocol.update(
        version='method-boundary-direct/1', papers=[paper], conditions=['direct_deepseek'],
        paper_only_workers=False, turns={'direct_deepseek': 16}, coordination='single raw API session',
        revision_reason='Meeting baseline: same model, original inputs, evidence tools, candidate allowance and shared resource caps',
        comparison='Compare the complete team workflow to a direct single session. No Swarm SDK, delegation, procedure map mandate or synthesis-review mandate.',
        evidence_mode='paper_only' if paper_only else 'paper_and_source',
    )
    if stream:
        protocol['transport'] = 'sse'
    dump(root / 'protocol.json', protocol)
    shutil.copy2(Path(__file__), root / 'direct.snapshot.py')
    shutil.copy2(HERE / 'pilot.py', root / 'pilot.snapshot.py')
    dump(root / 'input-index.json', {str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()})


def collect_stream(raw_lines):
    """Reconstruct a chat-completion message while retaining the original SSE separately."""
    message = {'role': 'assistant', 'content': ''}
    calls = {}
    model = finish = usage = None
    for raw in raw_lines:
        if not raw.startswith(b'data:'):
            continue
        data = raw[5:].strip()
        if data == b'[DONE]':
            break
        chunk = json.loads(data)
        if chunk.get('error'):
            raise ValueError(f"Provider stream error: {chunk['error']}")
        model = chunk.get('model') or model
        if chunk.get('usage'):
            usage = chunk['usage']
        if not chunk.get('choices'):
            continue
        choice, = chunk['choices']
        finish = choice.get('finish_reason') or finish
        delta = choice.get('delta') or {}
        for field in ('content', 'reasoning', 'reasoning_content', 'reasoning_details'):
            value = delta.get(field)
            if isinstance(value, str):
                message[field] = message.get(field, '') + value
            elif isinstance(value, list):
                message.setdefault(field, []).extend(value)
        for part in delta.get('tool_calls') or []:
            call = calls.setdefault(part['index'], {'type': 'function', 'function': {'name': '', 'arguments': ''}})
            if part.get('id'):
                call['id'] = part['id']
            for field, value in (part.get('function') or {}).items():
                call['function'][field] += value
    if not model or not finish:
        raise ValueError('Incomplete provider stream')
    if calls:
        message['tool_calls'] = [calls[i] for i in sorted(calls)]
    return {'model': model, 'usage': usage or {}, 'choices': [{'message': message, 'finish_reason': finish}]}


class StreamingCell(Cell):
    def http(self, payload, n):
        wire = payload | {'stream': True, 'stream_options': {'include_usage': True}}
        dump(self.out / f'request-{n:02d}.json', wire)
        request = urllib.request.Request(
            self.base + '/chat/completions', data=json.dumps(wire).encode(),
            headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json',
                     'Accept': 'text/event-stream'},
        )
        start = time.time()
        capture = self.out / f'response-{n:02d}.sse'
        with urllib.request.urlopen(request, timeout=self.protocol['per_request_timeout_seconds']) as response, capture.open('wb') as log:
            for line in response:
                log.write(line)
                log.flush()
                if time.time() > self.started + self.protocol['per_cell_wall_seconds']:
                    raise TimeoutError('Cell wall time expired while reading stream')
        body = collect_stream(capture.read_bytes().splitlines())
        dump(self.out / f'response-{n:02d}.json', body)
        self.log('usage.jsonl', dict(request=n, elapsed_seconds=time.time()-start, model=body['model'], usage=body['usage']))
        return body


def prepare_timeout_recovery(root, previous, force_close=False, stream=False, after_length=False):
    old_index = json.loads((previous / 'input-index.json').read_text())
    assert all(sha((previous / rel).read_bytes()) == digest for rel,digest in old_index.items())
    protocol = json.loads((previous / 'protocol.json').read_text())
    paper, = protocol['papers']
    source = previous / paper / 'direct_deepseek'
    summary = json.loads((source / 'summary.json').read_text())
    recoverable = (summary['finish_reason'] == 'length' if after_length else
                   any('timed out' in err.lower() or ((force_close or stream) and '502' in err)
                       for err in summary['errors']))
    complete = summary['final_sha256'] and (not after_length or summary['validation']['json_parsed'])
    if complete or not recoverable:
        raise ValueError('Recovery requires an archived failure without a usable final answer')
    if force_close and not summary.get('recovery'):
        raise ValueError('Forced close is reserved for a continuation that also failed')
    count = summary['requests']
    assert 0 < count < protocol['max_http_requests_per_cell']
    last_request = source / f'request-{count:02}.json'
    last_response = source / f'response-{count:02}.json'
    assert last_request.is_file() and last_response.is_file() == after_length
    messages = json.loads(last_request.read_text())['messages']
    assert messages[-1]['role']=='user' and messages[-1]['content'].startswith('Shared run budget observation:')
    root.mkdir(parents=True)
    for rel in old_index:
        if rel in ('direct.snapshot.py','protocol.json','recovery.json') or rel.startswith('checkpoint/'):
            continue
        target = root / rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(previous / rel, target)
    checkpoint = root / 'checkpoint'
    checkpoint.mkdir()
    stored = [*source.glob('request-[0-9][0-9].json'), *source.glob('response-[0-9][0-9].json')]
    stored.extend(source.glob('response-[0-9][0-9].sse'))
    stored.extend(source/name for name in ('reads.json','tools.json','summary.json','request-map.json'))
    for path in stored:
        shutil.copy2(path,checkpoint / path.name)
    dump(root / 'recovery.json',dict(parent=str(previous),requests_before_recovery=count,
         tokens_before_recovery=summary['actual_returned_total_tokens'],
         unknown_usage_requests=[i for i in range(1,count+1) if not (source/f'response-{i:02}.json').exists()],
         force_close=force_close or after_length, after_length=after_length))
    protocol['per_request_timeout_seconds'] = max(protocol['per_request_timeout_seconds'], 450)
    if stream:
        protocol['transport'] = 'sse'
    protocol['recovery_note'] = (
        'Ask for a concise final report after an output-length stop without a usable report.'
        if after_length else
        'One forced closing reply after a prior transport recovery also failed. Uses only archived evidence.'
        if force_close else
        'Resume the last incomplete raw API conversation. Original timeout and known use count toward the same caps.'
    )
    dump(root / 'protocol.json', protocol)
    shutil.copy2(Path(__file__),root/'direct.snapshot.py')
    dump(root/'input-index.json',{str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()})


async def run(root):
    tombstone = root / 'superseded.json'
    if tombstone.exists():
        replacement = json.loads(tombstone.read_text())['replacement']
        print(f'Skipping superseded prepared run; replacement: {replacement}', flush=True)
        return
    for name, expected in json.loads((root / 'input-index.json').read_text()).items():
        assert sha((root / name).read_bytes()) == expected, name
    protocol = json.loads((root / 'protocol.json').read_text())
    assert protocol['conditions'] == ['direct_deepseek']
    paper, = protocol['papers']
    archive = root / paper / 'direct_deepseek'
    if (archive / 'summary.json').is_file():
        print(f'Using archived terminal condition: {paper}/direct_deepseek', flush=True)
        return
    if archive.exists():
        raise RuntimeError(f'Condition has an existing nonterminal archive; inspect its live runner: {archive}')
    frozen_runner = root / 'direct.snapshot.py'
    if frozen_runner.read_bytes() != Path(__file__).read_bytes():
        # Queued comparisons retain their original input and runner protocol.
        await runpy.run_path(str(frozen_runner))['run'](root)
        return
    cell_type = StreamingCell if protocol.get('transport') == 'sse' else Cell
    cell = cell_type(root, paper, 'direct_deepseek', asyncio.Semaphore(1))
    cell.evidence.requires_freeze = False
    paper_text = '\n\n'.join(f'PHYSICAL PDF PAGE {p["page"]}\n{p["numbered"]}' for p in cell.evidence.pages)
    commit = cell.evidence.meta['commit']
    source_context = f'Pinned repository commit: {commit}' if commit else 'Evidence scope: published paper only'
    messages = [
        dict(role='system', content=(root / 'system.txt').read_text()),
        dict(role='user', content=(root / 'task.txt').read_text() +
             f'\nPaper ID: {paper}\n{source_context}' +
             f'\n\nORIGINAL PAPER BEGIN\n{paper_text}\nORIGINAL PAPER END'),
    ]
    tools = [dict(type='function', function=t | {'description': t['description'].replace(' after freezing hypotheses', '')})
             for t in TOOLS if t['name'] != 'freeze_hypotheses' and (commit or t['name'] == 'read_paper')]
    registered = {t['function']['name'] for t in tools}
    recovery_path = root / 'recovery.json'
    recovery = json.loads(recovery_path.read_text()) if recovery_path.is_file() else None
    if recovery:
        checkpoint = root/'checkpoint'
        cell.requests = recovery['requests_before_recovery']
        cell.tokens = recovery['tokens_before_recovery']
        cell.wire_ids = json.loads((checkpoint/'request-map.json').read_text())
        cell.evidence.reads = json.loads((checkpoint/'reads.json').read_text())
        cell.evidence.tools = json.loads((checkpoint/'tools.json').read_text())
        for f in [*checkpoint.glob('request-[0-9][0-9].json'),*checkpoint.glob('response-[0-9][0-9].json'),
                  *checkpoint.glob('response-[0-9][0-9].sse')]:
            shutil.copy2(f,cell.out/f.name)
        wire = json.loads((checkpoint/f'request-{cell.requests:02}.json').read_text())
        messages = wire['messages'][:-1]
        assert wire['tools'] == tools
        if recovery.get('after_length'):
            previous = json.loads((checkpoint / f'response-{cell.requests:02}.json').read_text())
            prior_reply = previous['choices'][0]['message']
            if prior_reply.get('content'):
                messages.append(dict(role='assistant', content=prior_reply['content']))
            messages.append(dict(role='user', content=(
                'The previous reply exhausted its output limit. Return a concise final JSON report now. '
                'Use the original evidence already supplied, and retain only hypotheses you can substantiate.'
            )))
    final = None
    finish = None
    errors = []
    try:
        for turn in range(cell.requests + 1, protocol['max_http_requests_per_cell'] + 1):
            force_close=bool(recovery and recovery.get('force_close'))
            reply = await cell.dispatch('model', dict(agent='root', turn=turn, messages=messages, tools=tools,
                                                      force_close=force_close))
            answer = reply['assistant_message']
            finish = reply['usage']['finish_reason']['original']
            calls = answer.get('tool_calls', [])
            if finish != 'tool_calls' or not calls:
                final = answer['content']
                (cell.out / 'final.txt').write_text(final)
                break
            if force_close:
                raise ValueError('Provider returned tool calls in forced closure')
            messages.append(answer)
            images = []
            for call in calls:
                function = call['function']
                name = function['name']
                result = await cell.dispatch('tool', dict(agent='root', name=name, args=json.loads(function['arguments']))) if name in registered else 'Tool refused: unavailable'
                if isinstance(result, dict):
                    blocks = result['content']
                    result = '\n'.join(b['text'] for b in blocks if b['type'] == 'text')
                    for b in blocks:
                        if b['type'] == 'image':
                            images.append(dict(type='image_url', image_url={'url': f'data:{b["mimeType"]};base64,{b["data"]}'}))
                messages.append(dict(role='tool', tool_call_id=call['id'], content=result))
            if images:
                messages.append(dict(role='user', content=[dict(type='text', text='Original page image evidence for the preceding tool results.'), *images]))
    except Exception as exc:
        errors.append(str(exc).replace(cell.key, '[REDACTED]'))
    finally:
        validation = validate_answer(final or '', cell.evidence)
        for name, data in [('reads', cell.evidence.reads), ('tools', cell.evidence.tools), ('request-map', cell.wire_ids), ('validation', validation)]:
            dump(cell.out / f'{name}.json', data)
        summary = dict(paper=paper, condition='direct_deepseek', requests=cell.requests, finish_reason=finish,
                       actual_returned_total_tokens=cell.tokens, agents=1, errors=errors, validation=validation,
                       target_execution='not_run', final_sha256=sha(final.encode()) if final else None,
                       recovery=recovery)
        dump(cell.out / 'summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--prepare-from', type=Path)
    source.add_argument('--recover-timeout-from', type=Path)
    source.add_argument('--recover-length-from', type=Path)
    parser.add_argument('--paper', default='nnsmith')
    parser.add_argument('--close-after-error',action='store_true')
    parser.add_argument('--stream', action='store_true')
    args = parser.parse_args()
    if args.prepare_from:
        prepare(args.root.resolve(), args.prepare_from.resolve(), args.paper, stream=args.stream)
    elif args.recover_timeout_from:
        prepare_timeout_recovery(args.root.resolve(), args.recover_timeout_from.resolve(),
                                 args.close_after_error, stream=args.stream)
    elif args.recover_length_from:
        prepare_timeout_recovery(args.root.resolve(), args.recover_length_from.resolve(),
                                 stream=args.stream, after_length=True)
    else:
        asyncio.run(run(args.root.resolve()))
