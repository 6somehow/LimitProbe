"""Reconcile model citations against the archived evidence and pinned originals."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from audit_pilot import norm, sha


def unpack(raw, quote_to_escape=None, syntax_edits=()):
    try:
        return json.loads(raw), 'bare_json'
    except ValueError:
        fenced = re.fullmatch(r'\s*([^\x60]*?)\x60\x60\x60(?:json)?\s*(\{.*\})\s*\x60\x60\x60\s*', raw, re.S)
        if fenced:
            return json.loads(fenced.group(2)), 'json_fence_with_preamble' if fenced.group(1).strip() else 'json_fence'
        if quote_to_escape:
            literal = '"' + quote_to_escape + '"'
            if raw.count(literal) != 1:
                raise ValueError('The recorded quote repair must match exactly one raw literal')
            escaped = json.dumps(literal, ensure_ascii=False)[1:-1]
            return json.loads(raw.replace(literal, escaped, 1)), 'recorded_quote_escape'
        if syntax_edits:
            normalized = raw
            for edit in sorted(syntax_edits, key=lambda item: item['offset'], reverse=True):
                pos, old, new = (edit[key] for key in ('offset', 'old', 'new'))
                if old != ']' or new not in {'', '}'} or normalized[pos:pos+1] != old:
                    raise ValueError('The recorded bracket repair does not match the raw report')
                normalized = normalized[:pos] + new + normalized[pos+1:]
            return json.loads(normalized), 'recorded_bracket_repair'
        raise


def load(path):
    return json.loads(path.read_text())


def tool_delivery(cell):
    mapping = {row['request']:row['agent'] for row in load(cell/'request-map.json')}
    delivered = {}
    for p in cell.glob('request-[0-9][0-9].json'):
        number = int(p.stem.split('-')[-1])
        agent = mapping[number]
        # A transport failure cannot attest that the recipient processed the tool result.
        if not (cell/f'response-{number:02}.json').is_file():
            continue
        contents = delivered.setdefault(agent,set())
        for message in load(p)['messages']:
            if message['role']=='tool' and isinstance(message.get('content'),str):
                contents.add(message['content'])
    return delivered


def spans_cover(spans, start, end):
    if not isinstance(start,int) or not isinstance(end,int) or not 1<=start<=end:
        return False
    remaining=start
    for lo,hi in sorted(spans):
        if lo <= remaining <= hi:
            remaining = hi+1
    return remaining>end


def review_cell(cell, quote_to_escape=None, syntax_edits=()):
    meta = load(cell.parent / 'source.json')
    pages = load(cell.parent / 'paper.json')
    summary = load(cell / 'summary.json')
    trace = load(cell / 'tools.json')
    delivered = tool_delivery(cell)
    reads = {}
    received = {}
    blobs = {}
    for record in trace:
        if record['name'] != 'read_repo':
            continue
        chunk = json.loads(record['result'])
        path = chunk['path']
        assert meta['repo'] and chunk['commit'] == meta['commit']
        if path not in blobs:
            blobs[path] = subprocess.check_output(
                ['git','-C',meta['repo'],'show',meta['commit']+':'+path], timeout=25,
            ).decode('utf-8', errors='replace').splitlines()
        start, end = chunk['start'], chunk['end']
        expected = '\n'.join(f'{i}: {blobs[path][i - 1]}' for i in range(start, end + 1))
        assert chunk['text'] == expected, (path, start, end)
        reads.setdefault(path, []).append((start,end))
        if record['result'] in delivered.get(record['agent'],set()):
            received.setdefault(path,[]).append((start,end))
    final = cell / 'final.txt'
    result = dict(paper=meta['paper_id'], condition=cell.name, source_commit=meta['commit'],
                  verified_source_reads=sum(map(len, reads.values())),
                  delivered_source_reads=sum(map(len,received.values())), run_errors=summary['errors'],
                  final_sha256=sha(final) if final.is_file() else None)
    if not final.is_file():
        return result | {'status': 'no_final'}
    try:
        answer, presentation = unpack(final.read_text(), quote_to_escape, syntax_edits)
        assert isinstance(answer, dict) and isinstance(answer['candidates'], list)
    except (ValueError, KeyError, AssertionError) as exc:
        return result | {'status': 'invalid_final', 'detail': str(exc)}
    result['presentation'] = presentation
    result['validation'] = summary['validation']
    records = [(r.get('id',f'H{i}'),r) for i,r in enumerate(answer['candidates'],1)]
    records += [(f'K{i}',r) for i,r in enumerate(answer.get('known_boundaries',[]),1)]
    evidence = []
    for ident, record in records:
        quotes = []
        for original in record.get('paper_evidence', []):
            quote = norm(original.get('quote') or '')
            matched = [p['page'] for p in pages if quote and quote in norm(p['text'])]
            quotes.append(dict(reported_page=original.get('page'), layout_normalized_pdf_pages=matched))
        code = []
        for ref in record.get('code_evidence', []):
            path, start, end = (ref.get(key) for key in ('path','start','end'))
            code.append(ref | {
                'covered_by_verified_reads':spans_cover(reads.get(path,[]),start,end),
                'covered_by_delivered_reads':spans_cover(received.get(path,[]),start,end),
            })
        evidence.append(dict(id=ident,title=record.get('title'),paper_quotes=quotes,source_references=code))
    return result | dict(status='evidence_checked', candidate_evidence=evidence,
                         semantic_match='review_separately')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cells', type=Path, nargs='+')
    parser.add_argument('--output', type=Path)
    args=parser.parse_args()
    result=[review_cell(cell) for cell in args.cells]
    rendered=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered,end='')
