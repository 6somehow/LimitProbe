"""Create evaluation-only reference and review packets and calculate CS6223 metrics."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

from audit_evidence import spans_cover, tool_delivery, unpack
from audit_pilot import norm
from corpus_ledger import load
from pilot import dump, git, sha
from swarm_study import BACKEND, CONDITIONS, DEV, TEST, verify_inputs

PAPER_ONLY = {'11':'onesidedmw','13':'cxlfork','16':'juneberry','17':'twilight-tlite'}
DATASET = 'https://nusu-my.sharepoint.com/:w:/g/personal/shanghao_liu_u_nus_edu/IQCMYhdtAPfER5OMNVveqKorAcB0E1tiAMS4mbzOqSu5PWU'
MATCHES = {'miss':0,'partial':1,'core':2}


def import_reference(source, output):
    rows = {}
    groups = {key:'dev' for key in DEV} | {key:'test_with_source' for key in TEST} | {
        key:'test_paper_only' for key in PAPER_ONLY}
    for line in source.read_text().splitlines():
        columns = [value.strip() for value in line.strip('|').split('|')]
        if len(columns) != 4 or columns[0] not in groups:
            continue
        case, paper, mechanism, boundary = columns
        if case in rows:
            raise ValueError(f'Duplicate reference: {case}')
        rows[case] = dict(case=case,paper=paper,split=groups[case],
                          reference=mechanism,qualifications=boundary)
    if set(rows) != set(groups):
        raise ValueError('Missing case in the archived Shanghao rubric')
    if output.exists():
        raise FileExistsError(output)
    slug = DEV | TEST | PAPER_ONLY
    dump(output, dict(attribution='Shanghao, 21 November annotated reference, archived transcription',
                      dataset=DATASET,source_sha256=sha(source.read_bytes()),
                      cases=[value | {'slug':slug[key]} for key,value in sorted(rows.items())]))


def final_response(cell, summary, raw):
    if not raw.is_file() or summary.get('status') not in (None,'final_received'):
        return None
    if summary.get('returncode',0) != 0:
        return None
    request_map = cell/'request-map.json'
    ids = [row['request'] for row in load(request_map) if row['agent']=='root'] if request_map.exists() else [1]
    final = raw.read_bytes()
    for number in reversed(ids):
        provider = cell/f'response-{number:02}.json'
        if not provider.is_file():
            continue
        response = load(provider)
        choice = response['choices'][0]
        if (response.get('model')==BACKEND and choice['finish_reason']=='stop'
            and choice['message'].get('content','').encode()==final):
            return number
    return None


def source_evidence(folder, cell):
    meta = load(folder/'source.json')
    first = load(cell/'request-01.json')
    packet = (folder/'original-source-packet.txt').read_text()
    span_by_path = defaultdict(list)
    blobs = {}

    def verify(path, start, end, text):
        if path not in blobs:
            blobs[path] = git(meta['repo'],'show',f"{meta['commit']}:{path}").decode(
                'utf-8', errors='replace').splitlines()
        lines = blobs[path]
        if not 1 <= start <= end <= len(lines):
            raise ValueError(f'Outside frozen source: {path}')
        expected = '\n'.join(f'{i}: {lines[i-1]}' for i in range(start,end+1))
        if text != expected:
            raise ValueError(f'Source bytes disagree: {path}')
        span_by_path[path].append((start,end))

    if packet and any(isinstance(msg.get('content'),str) and
                      'ORIGINAL SOURCE EXCERPTS BEGIN\n'+packet+'\nORIGINAL SOURCE EXCERPTS END' in msg['content']
                      for msg in first['messages'] if msg.get('role')=='user'):
        for match in re.finditer(r'^FILE ([^\n]+) \| original lines 1–(\d+)\n(.*?)(?=\n\nFILE |\Z)',
                                 packet,flags=re.M|re.S):
            verify(match[1],1,int(match[2]),match[3])
    if (cell/'tools.json').exists():
        delivered = tool_delivery(cell)
        for record in load(cell/'tools.json'):
            if record['name'] != 'read_repo' or record['result'] not in delivered.get(record['agent'],set()):
                continue
            chunk = json.loads(record['result'])
            if chunk['commit'] != meta['commit']:
                raise ValueError('Tool read commit mismatch')
            verify(chunk['path'],chunk['start'],chunk['end'],chunk['text'])
    return span_by_path


def gap_trace(cell, records, final_request):
    events = [json.loads(line) for line in (cell/'event.jsonl').read_text().splitlines()]
    discoveries = [e for e in events if e['kind']=='gap_discovery_frozen']
    routes = [e for e in events if e['kind']=='gap_route_selected']
    checks = [e for e in events if e['kind']=='gap_verification_received']
    if len(routes)>1 or len(checks)>1 or len({e['agent'] for e in discoveries})!=len(discoveries):
        raise ValueError('Unexpected phase repetitions')
    if routes and any(events.index(event)>events.index(routes[0]) for event in discoveries):
        raise ValueError('Discovery completed after routing')
    compacted = [e for e in events if e['kind']=='native_gap_compaction']
    result = {
        'native_compaction':[
            {'agent':e['agent'],'trigger':e.get('trigger','manual'),'estimated_before':e['before'],
             'estimated_after':e['estimated_after']}
            for e in compacted
        ],
        'native_compaction_skipped':sum(e['kind']=='native_gap_compaction_skipped' for e in events),
        'independent_discoveries':len(discoveries),
        'procedures_discovered':sum(len(e.get('procedures',[])) for e in discoveries),
        'valid_candidate_lists':sum(e['parsed'] for e in discoveries),
        'candidates_before_routing':sum(len(e['candidates']) for e in discoveries),
        'cross_check_requested':bool(routes and routes[0]['recipient']),
        'cross_check_completed':bool(checks),
        'cross_check_in_final_request':False,
        'final_records_linked_to_checked_candidate':0,
    }
    if checks:
        checked = checks[0]
        candidate = checked['assignment']['candidate']['id']
        author = candidate.rpartition('#')[0]
        if not routes or routes[0]['recipient']!=checked['agent'] or checked['agent']==author:
            raise ValueError('Verification provenance mismatch')
        if not any(e['agent']==author and any(row.get('id')==candidate for row in e['candidates'] + e.get('procedures',[]))
                   for e in discoveries):
            raise ValueError('Cross-check candidate was not produced during independent discovery')
        messages = load(cell/f'request-{final_request:02}.json')['messages']
        result['cross_check_in_final_request'] = any(
            m.get('role')=='user' and isinstance(m.get('content'),str)
            and 'PHASE: final synthesis' in m['content'] and json.dumps(
                checked['answer'], ensure_ascii=False)[1:-1] in m['content']
            for m in messages
        )
        result['final_records_linked_to_checked_candidate'] = sum(
            isinstance(record.get('origin_ids'),list) and candidate in record['origin_ids']
            for record in records
        )
    return result


def packet(root, split, output, reference):
    output.mkdir(parents=True,exist_ok=True)
    refs = {row['slug']:row for row in load(reference)['cases']}
    protocol = load(root/'protocol.json')
    statuses = []
    for case,paper in protocol['split'][split].items():
        folder = root/paper
        pages = {p['page']:norm(p['text']) for p in load(folder/'paper.json')}
        for condition in CONDITIONS:
            cell = folder/condition
            summary = cell/'summary.json'
            status = dict(case=case,paper=paper,condition=condition,state='pending')
            statuses.append(status)
            if not summary.is_file():
                continue
            report = load(summary)
            raw = cell/'final.txt'
            status.update(state='failed',requests=report['requests'],
                          tokens=report.get('actual_returned_total_tokens',report.get('usage',{}).get('total_tokens')))
            final_request = final_response(cell, report, raw)
            if final_request is None:
                continue
            try:
                answer,_ = unpack(raw.read_text())
                groups = [answer[key] for key in ('candidates','known_boundaries')]
                if answer['paper_id'] != paper or answer['target_execution'] != 'not_run':
                    continue
                if not all(isinstance(group,list) and len(group)<=4 for group in groups):
                    continue
                records = [record for group in groups for record in group]
                ids = [record['id'] for record in records]
                if any(not isinstance(ident,str) or not ident for ident in ids) or len(ids)!=len(set(ids)):
                    continue
            except (ValueError,TypeError,KeyError):
                continue
            spans = source_evidence(folder,cell)
            audit = {}
            for record in records:
                citations = record.get('paper_evidence',[])
                source = record.get('code_evidence',[])
                citations = citations if isinstance(citations,list) else [None]
                source = source if isinstance(source,list) else [None]
                audit[record['id']] = {
                    'paper_found':[isinstance(cite,dict) and type(cite.get('page')) is int
                                   and isinstance(cite.get('quote'),str) and bool(norm(cite['quote']))
                                   and norm(cite['quote']) in pages.get(cite['page'],'') for cite in citations],
                    'source_delivered':[isinstance(ref,dict) and isinstance(ref.get('path'),str)
                                        and spans_cover(spans[ref['path']],ref.get('start'),ref.get('end'))
                                        for ref in source],
                }
            digest = sha(raw.read_bytes())
            ident = sha(f'{root.name}:{paper}:{condition}:{digest}'.encode())[:14]
            status.update(state='complete',report_id=ident,final_sha256=digest,final_request=final_request)
            if condition == 'evidence_gap_swarm':
                status['coordination'] = gap_trace(cell, records, final_request)
            cleaned = [{k:v for k,v in record.items() if k not in ('origin_ids','disposition')} for record in records]
            dump(output/f'{ident}.json',{'report_id':ident,'final_sha256':digest,'reference':refs[paper],
                                         'records':cleaned,'mechanical_evidence':audit,
                                         'review_fields':{'match':'miss|partial|core','record_id':'one final ID or null',
                                                          'reason':'why the single record matches or misses',
                                                          'test_ready_ids':'list of IDs with an actionable controlled comparison and oracle',
                                                          'supported_ids':'list of IDs whose evidence supports the scoped claim, as a hypothesis if applicable'}})
    dump(output/'mapping.json', {'run':str(root),'split':split,'cells':statuses})
    return statuses


def summarize(review_dir, grades_dir):
    results = load(review_dir/'mapping.json')
    outcomes = {}
    for cell in results['cells']:
        if cell['state'] != 'complete':
            continue
        ident = cell['report_id']
        path = grades_dir/f'{ident}.json'
        if not path.exists():
            continue
        g = load(path)
        row = load(review_dir/f'{ident}.json')
        ids = {r['id'] for r in row['records']}
        if (g.get('final_sha256') != cell['final_sha256'] or g.get('match') not in MATCHES or not g.get('reason')
            or (g.get('match')!='miss' and g.get('record_id') not in ids)
            or not set(g.get('test_ready_ids',[])) <= ids or not set(g.get('supported_ids',[])) <= ids):
            raise ValueError(f'Grade does not match the frozen report: {path}')
        outcomes[ident] = (g,row)

    metrics = {}
    for condition in CONDITIONS:
        cells = [c for c in results['cells'] if c['condition']==condition]
        scored = [outcomes[c['report_id']] for c in cells if c.get('report_id') in outcomes]
        core = sum(g['match']=='core' for g,_ in scored)
        partial = sum(g['match']=='partial' for g,_ in scored)
        rows = [r for _,row in scored for r in row['mechanical_evidence'].values()]
        paper = [v for record in rows for v in record['paper_found']]
        code = [v for record in rows for v in record['source_delivered']]
        metrics[condition] = {
            'planned':len(cells),'pending':sum(c['state']=='pending' for c in cells),
            'failed':sum(c['state']=='failed' for c in cells),'complete':sum(c['state']=='complete' for c in cells),
            'graded':len(scored),'core':core,'partial':partial,'miss':len(scored)-core-partial,
            'paper_citations_on_page':[sum(paper),len(paper)],'source_spans_delivered':[sum(code),len(code)],
            'test_ready_records':[sum(len(g['test_ready_ids']) for g,_ in scored if 'test_ready_ids' in g),
                                  sum(len(r['records']) for g,r in scored if 'test_ready_ids' in g)],
            'evidence_supported_records':[sum(len(g['supported_ids']) for g,_ in scored if 'supported_ids' in g),
                                          sum(len(r['records']) for g,r in scored if 'supported_ids' in g)],
            'papers_with_test_ready_record':sum(bool(g.get('test_ready_ids')) for g,_ in scored),
            'requests':sum(c.get('requests',0) for c in cells),
            'known_total_tokens':sum(c.get('tokens') or 0 for c in cells),
        }
    paired = {}
    scored_by = {(c['case'],c['condition']):MATCHES[outcomes[c['report_id']][0]['match']]
                 for c in results['cells'] if c.get('report_id') in outcomes}
    for mode in CONDITIONS[:-1]:
        rows = [(case,scored_by[case,mode],scored_by[case,CONDITIONS[-1]])
                for case in sorted({c['case'] for c in results['cells']})
                if (case,mode) in scored_by and (case,CONDITIONS[-1]) in scored_by]
        paired[mode] = {'n':len(rows),'D_wins':sum(b>a for _,a,b in rows),
                        'ties':sum(a==b for _,a,b in rows),'D_losses':sum(b<a for _,a,b in rows),'rows':rows}
    return {'split':results['split'],'conditions':metrics,'D_paired_against':paired}


def select_dev_method(review_dir, grades_dir):
    metrics = summarize(review_dir, grades_dir)
    mapping = load(review_dir/'mapping.json')
    if mapping['split'] != 'dev':
        raise ValueError('Method selection uses Dev only')
    scores = {}
    for row in mapping['cells']:
        if 'report_id' in row and (grades_dir/f"{row['report_id']}.json").is_file():
            grade = load(grades_dir/f"{row['report_id']}.json")
            scores[(row['case'],row['condition'])] = MATCHES[grade['match']]
    paired = {}
    for method in CONDITIONS[2:]:
        paired[method] = {}
        for baseline in CONDITIONS[:2]:
            rows = [(case,scores[case,method],scores[case,baseline]) for case in DEV
                    if (case,method) in scores and (case,baseline) in scores]
            paired[method][baseline] = dict(
                n=len(rows), wins=sum(m>b for _,m,b in rows),
                ties=sum(m==b for _,m,b in rows), losses=sum(m<b for _,m,b in rows),
                core_delta=sum((m==2)-(b==2) for _,m,b in rows),
            )
    eligible = [method for method, comparisons in paired.items()
                if all(p['n']==len(DEV) and p['core_delta']>=0 and p['wins']>p['losses']
                       for p in comparisons.values())]
    def order(method):
        row = metrics['conditions'][method]
        return (-row['core'], -row['partial'], row['known_total_tokens'],
                CONDITIONS.index(method))
    return {'selected':min(eligible,key=order) if eligible else None,
            'paired_vs_baselines':paired,
            'rule':'Four scored Dev pairs against each baseline; no fewer core matches and more wins than losses against each. Tie-break by core, partial, then known tokens.',
            'selection_population':'dev'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action',required=True)
    refs = commands.add_parser('reference')
    refs.add_argument('source',type=Path)
    refs.add_argument('output',type=Path)
    packets = commands.add_parser('packet')
    packets.add_argument('root',type=Path)
    packets.add_argument('output',type=Path)
    packets.add_argument('reference',type=Path)
    packets.add_argument('--split',choices=('dev','test'),required=True)
    score = commands.add_parser('summarize')
    score.add_argument('review_dir',type=Path)
    score.add_argument('grades_dir',type=Path)
    score.add_argument('output',type=Path)
    seal = commands.add_parser('release-test')
    seal.add_argument('root',type=Path)
    seal.add_argument('review_dir',type=Path)
    seal.add_argument('grades_dir',type=Path)
    args = parser.parse_args()
    if args.action == 'reference':
        import_reference(args.source,args.output)
    elif args.action == 'packet':
        packet(args.root.resolve(),args.split,args.output,args.reference)
    elif args.action == 'summarize':
        dump(args.output,summarize(args.review_dir,args.grades_dir))
    else:
        root = args.root.resolve()
        verify_inputs(root)
        mapping = load(args.review_dir/'mapping.json')
        if mapping['split']!='dev' or Path(mapping['run'])!=root:
            raise ValueError('Dev reviews must refer to the same frozen protocol')
        metrics = summarize(args.review_dir,args.grades_dir)
        for condition,value in metrics['conditions'].items():
            if value['planned']!=len(DEV) or value['pending'] or value['graded']!=value['complete']:
                raise ValueError(f'Dev review incomplete: {condition}')
        if any(c['complete']==0 for c in metrics['conditions'].values()):
            raise ValueError('Each condition needs a usable Dev run before Test')
        selection = select_dev_method(args.review_dir,args.grades_dir)
        if not selection['selected']:
            raise ValueError('Neither C nor D exceeds both Dev baselines under the prespecified rule')
        dump(root/'test-release.json',dict(input_index_sha256=sha((root/'input-index.json').read_bytes()),
                                          reviewed_dev=metrics, selection=selection))
