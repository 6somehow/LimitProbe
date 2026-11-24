"""Continue an immutable merged inventory; never discover or merge mechanisms again."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import time
from pathlib import Path

from .independent_discovery import (LOCAL_ALIGN, LOCAL_SOURCE, SPLIT_SCOPED,
                                    check_evidence, load_input, validate_local)
from .io import file_sha256, read_json, write_json
from .multimodal_decomposition import call, parse_response
from .paper_decomposition import numbered, split_group


def related_pages(mechanism, group):
    return sorted(set(mechanism['pages']) | {q['page'] for q in mechanism['evidence']} |
                  {int(q.get('page') or q['locator'].split('.')[-1])
                   for b in group['behaviors'] for q in b['evidence']})


def draft_rows(mechanism, originals, review):
    """Apply only structurally checked suggestions to a distinct pending draft."""
    decisions = {r['id']: r for r in review['behavior_reviews']}
    rows, changes = [], []
    for original in originals:
        decision = decisions[original['id']]
        replacements = decision['replacements']
        if replacements and not {'duplicate', 'scope_drift'} & set(decision['issues']):
            ids = []
            for i, replacement in enumerate(replacements, 1):
                uid = f'{original["id"]}-R{i:02d}'
                ids.append(uid)
                rows.append(dict(replacement, id=uid, origin_id=original['id'],
                                 mechanism_id=mechanism, semantic_review='pending'))
            changes.append(dict(origin_id=original['id'], issues=decision['issues'],
                                replacement_ids=ids, reason=decision['reason']))
        else:
            rows.append(dict(original, mechanism_id=mechanism, semantic_review='pending',
                             review_issues=decision['issues']))
    held = {f['addition_index'] for f in review.get('consistency_flags', []) if 'addition_index' in f}
    absorbed = set(review.get('absorbed_addition_indices', []))
    for i, addition in enumerate(review['additions'], 1):
        if i in held or i in absorbed:
            continue
        rows.append(dict(addition, id=f'{mechanism}-A{i:02d}', mechanism_id=mechanism,
                         origin='local_source_addition', semantic_review='pending'))
    return dict(behaviors=rows, changes=changes,
                held_additions=[dict(row, addition_index=i) for i,row in enumerate(review['additions'],1) if i in held],
                absorbed_additions=[dict(row, addition_index=i) for i,row in enumerate(review['additions'],1) if i in absorbed],
                publication_status='draft', semantic_review='pending')


def run(inventory, output, model='x-test-2'):
    if output.exists():
        raise ValueError('Use a fresh continuation directory; API attempts cannot be overwritten')
    inventory = inventory.resolve()
    source = inventory / 'merged-mechanisms.json'
    source_hash = file_sha256(source)
    previous = read_json(inventory / 'protocol.json')
    baseline = Path(previous['baseline'])
    pages, images = load_input(baseline)
    mechanisms = read_json(source)['mechanisms']
    if len({m['id'] for m in mechanisms}) != len(mechanisms):
        raise ValueError('Duplicate mechanism ID')
    output.mkdir(parents=True)
    implementation = output / 'implementation'
    implementation.mkdir()
    for name in ['mechanism_continuation.py', 'independent_discovery.py',
                 'paper_decomposition.py', 'semantic_audit.py', 'multimodal_decomposition.py']:
        shutil.copyfile(Path(__file__).parent / name, implementation / name)
    shutil.copyfile(source, output / 'merged-mechanisms.json')
    protocol = dict(inventory=str(inventory), merged_sha256=source_hash, requested_model=model,
                    pdf_sha256=previous['pdf_sha256'], input_modality='text_and_original_page_images',
                    mechanism_count=len(mechanisms), discovery_requests=0, merge_requests=0,
                    request_budget=(len(mechanisms)+2)//3+2*len(mechanisms), concurrency=2,
                    max_output_tokens_per_request=6500, retries=0, socket_timeout_seconds=90,
                    launch_deadline_seconds=3600, priority_mechanism='M02',
                    independent_human_review='pending', target_execution='not_run',
                    citation_policy='model_primary_mechanical_diagnostic',
                    acceptance='All mechanisms and original behavior/obligation IDs accounted for; unresolved and failures retained; edits remain model drafts',
                    code_hashes={p.name:file_sha256(p) for p in implementation.iterdir()})
    write_json(output / 'protocol.json', protocol)
    scope = [{k:m.get(k) for k in ('id','name','description','boundary','parent_name')} for m in mechanisms]
    deadline = time.monotonic() + 3600
    def invoke(prompt, data, indices, name):
        if time.monotonic() > deadline:
            raise ValueError('Run launch deadline reached')
        return call(model, prompt, data, [images[i-1] for i in indices], output / f'{name}.raw.json')
    groups, failures = {}, []
    def split(batch):
        indices = sorted({p for m in batch for p in m['pages']} |
                         {q['page'] for m in batch for q in m['evidence']})
        name = f'split-{batch[0]["id"]}'
        raw, meta = invoke(SPLIT_SCOPED, dict(mechanisms=batch, scope_catalog=scope,
                          pages=numbered(pages, indices)), indices, name)
        result = {m['id']:split_group(raw, m, pages, verify_evidence=False) for m in batch}
        write_json(output / f'{name}.json', dict(groups=result, model=meta))
        print('split', ','.join(result), sum(len(g['behaviors']) for g in result.values()), flush=True)
        return result
    def review(m):
        mid = m['id']
        indices = related_pages(m, groups[mid])
        neighbors = [r for r in mechanisms if r['name'] == m.get('parent_name') or r.get('parent_name') == m['name']]
        context = dict(mechanism=m, parent_child_boundaries=neighbors, scope_catalog=scope,
                       pages=numbered(pages, indices))
        raw, source_meta = invoke(LOCAL_SOURCE, context, indices, f'{mid}-obligations')
        obligations = raw['obligations']
        ids = [o['id'] for o in obligations]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate local obligation IDs')
        for obligation in obligations:
            check_evidence(obligation['evidence'], pages, indices)
        write_json(output / f'{mid}-obligations.json', dict(raw, model=source_meta))
        group = groups[mid]
        payload = dict(context, obligations=obligations, behaviors=group['behaviors'],
                       rejected_candidates=group['rejected'], context_gaps=raw.get('context_gaps', []))
        aligned, align_meta = invoke(LOCAL_ALIGN, payload, indices, f'{mid}-reconcile')
        result = validate_local(aligned, obligations, group['behaviors'], pages, indices)
        result.update(context_gaps=raw.get('context_gaps', []), models=[source_meta,align_meta])
        write_json(output / f'{mid}-local-review.json', result)
        draft = draft_rows(mid, group['behaviors'], result)
        write_json(output / f'{mid}-draft.json', draft)
        print('review', mid, len(obligations), 'obligations', len(result['additions']),
              'additions', len(draft['changes']), 'revisions', flush=True)
        return result
    def failure(stage, ids, exc):
        item = dict(stage=stage, ids=ids, reason=str(exc), status='unresolved')
        failures.append(item)
        write_json(output / 'failures.json', failures)
        print('unresolved', stage, ids, str(exc), flush=True)
    batches = [mechanisms[i:i+3] for i in range(0,len(mechanisms),3)]
    # Complete propagation first, then continue all remaining mechanisms.
    try:
        groups.update(split(batches[0]))
    except (ValueError, KeyError, TypeError) as exc:
        failure('split', [m['id'] for m in batches[0]], exc)
    priority = next((m for m in mechanisms if m['id'] == 'M02'), None)
    reviewed = {}
    if priority and priority['id'] in groups:
        try:
            reviewed[priority['id']] = review(priority)
        except (ValueError, KeyError, TypeError) as exc:
            failure('review', [priority['id']], exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(split,b): b for b in batches[1:]}
        for job in as_completed(jobs):
            try: groups.update(job.result())
            except (ValueError, KeyError, TypeError) as exc:
                failure('split', [m['id'] for m in jobs[job]], exc)
    write_json(output / 'behaviors.json', dict(groups=groups, semantic_review='pending'))
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(review,m): m for m in mechanisms if m['id'] in groups and m != priority}
        for job in as_completed(jobs):
            try: reviewed[jobs[job]['id']] = job.result()
            except (ValueError, KeyError, TypeError) as exc:
                failure('review', [jobs[job]['id']], exc)
    assert file_sha256(source) == source_hash, 'Frozen mechanism inventory changed during continuation'
    usage = Counter()
    for path in output.glob('*.raw.json'):
        for key,value in read_json(path).get('usage',{}).items():
            if isinstance(value,int):usage[key]+=value
    summary = dict(mechanism_count=len(mechanisms), split_mechanisms=len(groups),
                   reviewed_mechanisms=len(reviewed), original_behaviors=sum(len(g['behaviors']) for g in groups.values()),
                   additions=sum(len(r['additions']) for r in reviewed.values()),
                   compound_originals=sum('compound' in b['issues'] for r in reviewed.values() for b in r['behavior_reviews']),
                   proposed_revisions=sum(bool(b['replacements']) for r in reviewed.values() for b in r['behavior_reviews']),
                   missing_review_ids=[m['id'] for m in mechanisms if m['id'] not in reviewed],
                   failures=failures, usage=dict(usage), requests=len(list(output.glob('*.raw.request.json'))),
                   discovery_requests=0, merge_requests=0, semantic_acceptance='pending', publication_status='draft')
    write_json(output / 'summary.json', summary)
    write_json(output / 'status.json', dict(execution='complete' if not failures else 'complete_with_unresolved',
               semantic_acceptance='pending'))
    print(summary, flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model',default='x-test-2')
    args=parser.parse_args()
    run(args.inventory,args.output,args.model)
