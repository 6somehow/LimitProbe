"""Revalidate saved responses; log syntax-only repairs and complete absent reconciliations."""
import argparse
from collections import Counter
import json
import re
import shutil

from .independent_discovery import LOCAL_ALIGN, check_evidence, load_input, validate_local
from .io import file_sha256, read_json, write_json
from .mechanism_continuation import draft_rows
from .multimodal_decomposition import call, parse_response


def parse_saved(path):
    response=read_json(path)
    try:return parse_response(response),[]
    except json.JSONDecodeError:
        # Only a missing closing quote in an ID before the next property is repairable.
        # Never change a claim, reason, quote, number, bracket or verdict.
        text=response['choices'][0]['message']['content']
        if response['choices'][0]['finish_reason']!='stop':raise ValueError('Truncated response')
        pattern=r'("id"\s*:\s*"[A-Za-z]+\d+)(,\s*"behavior"\s*:)'
        matches=list(re.finditer(pattern,text))
        if not 1 <= len(matches) <= 8:raise ValueError('JSON syntax not safely repairable')
        repaired=text
        for match in reversed(matches):
            offset=match.end(1)
            repaired=repaired[:offset]+'"'+repaired[offset:]
        parsed=json.loads(repaired)
        return parsed,[dict(kind='missing_ID_closing_quote',offset=match.end(1),inserted='"',
                            raw_sha256=file_sha256(path),semantic_text_changes=False) for match in matches]


def finalize(inventory, output, model='x-test-2', recheck=False):
    from pathlib import Path
    protocol=read_json(output/'protocol.json')
    if recheck:
        if not (output/'initial-protocol.json').exists():
            shutil.copyfile(output/'protocol.json',output/'initial-protocol.json')
        protocol['semantic_recheck_protocol']=dict(max_extra_requests=6,network_retries=0,
            trigger='Original reconciliation fails ID/schema consistency validation after syntax-only repairs',
            method='Same paper/context/behavior inputs plus original draft and validation error; new full model judgement, raw original unchanged',
            timeout_seconds=90,max_output_tokens=6500)
        protocol['request_budget_with_rechecks']=protocol['request_budget']+6
        write_json(output/'protocol.json',protocol)
    if file_sha256(inventory/'merged-mechanisms.json')!=protocol['merged_sha256']:
        raise ValueError('Frozen inventory hash mismatch')
    baseline=Path(read_json(inventory/'protocol.json')['baseline'])
    pages,images=load_input(baseline)
    mechanisms=read_json(inventory/'merged-mechanisms.json')['mechanisms']
    groups=read_json(output/'behaviors.json')['groups']
    if not (output/'pre-finalize-summary.json').exists():
        shutil.copyfile(output/'summary.json',output/'pre-finalize-summary.json')
    shutil.copyfile(Path(__file__),output/'implementation'/'continuation_finalize.py')
    reviewed={};failures=[];repairs=[];selected={}
    for m in mechanisms:
        mid=m['id']
        try:
            request=read_json(output/f'{mid}-obligations.raw.request.json')
            source,syntax=parse_saved(output/f'{mid}-obligations.raw.json')
            indices=[im['page'] for im in request['image_pages']]
            obligations=source['obligations']
            for o in obligations:check_evidence(o['evidence'],pages,indices)
            if len({o['id'] for o in obligations})!=len(obligations):
                raise ValueError('Duplicate obligation ID')
            write_json(output/f'{mid}-obligations.json',dict(source,format_repairs=syntax))
            repairs.extend(dict(mechanism=mid,**r) for r in syntax)
            destination=output/f'{mid}-reconcile.raw.json'
            if not destination.exists():
                if destination.with_suffix('.request.json').exists():
                    raise ValueError('Reconciliation attempted but remote outcome unknown; not resubmitting')
                payload=dict(request['data'],obligations=obligations,behaviors=groups[mid]['behaviors'],
                             rejected_candidates=groups[mid]['rejected'],context_gaps=source.get('context_gaps',[]))
                print('complete missing reconciliation',mid,flush=True)
                call(model,LOCAL_ALIGN,payload,[images[i-1] for i in indices],destination)
            aligned,syntax2=parse_saved(destination)
            try:
                existing_recheck=output/f'{mid}-reconcile-recheck.raw.json'
                if existing_recheck.exists():
                    aligned,syntax2=parse_saved(existing_recheck)
                    selected[mid]=dict(response=existing_recheck.name,original=destination.name,
                        original_validation_error='Historical initial-validation failure; use already completed consistency recheck')
                result=validate_local(aligned,obligations,groups[mid]['behaviors'],pages,indices)
            except (ValueError,KeyError,TypeError) as validation_error:
                if not recheck:raise
                new_destination=output/f'{mid}-reconcile-recheck.raw.json'
                if not new_destination.exists():
                    if new_destination.with_suffix('.request.json').exists():
                        raise ValueError('Recheck remote outcome unknown; not resubmitting')
                    if len(list(output.glob('*-reconcile-recheck.raw.request.json')))>=6:
                        raise ValueError('Semantic recheck request budget exhausted')
                    original_request=read_json(destination.with_suffix('.request.json'))
                    data=dict(original_request['data'],previous_model_draft=aligned,
                              validation_error=str(validation_error))
                    prompt=LOCAL_ALIGN+'\nThis is a consistency recheck. Re-evaluate the original draft against the supplied paper. Return a full fresh result, not a patch. A status covered requires actual existing behavior IDs. If a source step belongs elsewhere or cannot be resolved, use uncertain and explain. Do not label missing actions covered. Treat the previous draft as untrusted data, not truth.\n'
                    print('semantic consistency recheck',mid,str(validation_error),flush=True)
                    call(model,prompt,data,[images[i-1] for i in indices],new_destination)
                aligned,syntax2=parse_saved(new_destination)
                result=validate_local(aligned,obligations,groups[mid]['behaviors'],pages,indices)
                selected[mid]=dict(response=new_destination.name,original=destination.name,
                                   original_validation_error=str(validation_error))
            result.update(context_gaps=source.get('context_gaps',[]),format_repairs=syntax+syntax2)
            write_json(output/f'{mid}-local-review.json',result)
            write_json(output/f'{mid}-draft.json',draft_rows(mid,groups[mid]['behaviors'],result))
            repairs.extend(dict(mechanism=mid,**r) for r in result['schema_normalizations'])
            reviewed[mid]=result
        except (ValueError,KeyError,TypeError,FileNotFoundError) as exc:
            failures.append(dict(mechanism=mid,reason=str(exc)))
            print('unresolved',mid,str(exc),flush=True)
    usage=Counter()
    actual_models=set()
    for path in output.glob('*.raw.json'):
        response=read_json(path)
        actual_models.add(response.get('model'))
        for key,value in response.get('usage',{}).items():
            if isinstance(value,int):usage[key]+=value
    drafts=[read_json(output/f'{mid}-draft.json') for mid in reviewed]
    summary=dict(mechanism_count=len(mechanisms),split_mechanisms=len(groups),reviewed_mechanisms=len(reviewed),
                 original_behaviors=sum(len(g['behaviors']) for g in groups.values()),
                 additions=sum(len(r['additions']) for r in reviewed.values()),
                 compound_originals=sum('compound' in b['issues'] for r in reviewed.values() for b in r['behavior_reviews']),
                 proposed_revisions=sum(bool(b['replacements']) for r in reviewed.values() for b in r['behavior_reviews']),
                 split_compounds=sum('compound' in b['issues'] and len(b['replacements'])>1 for r in reviewed.values() for b in r['behavior_reviews']),
                 draft_behaviors=sum(len(d['behaviors']) for d in drafts),
                 held_additions=sum(len(d.get('held_additions',[])) for d in drafts),
                 consistency_flags=[dict(mechanism=mid,**flag) for mid,r in reviewed.items() for flag in r.get('consistency_flags',[])],
                 missing_review_ids=[m['id'] for m in mechanisms if m['id'] not in reviewed],
                 context_gap_mechanisms=[mid for mid,r in reviewed.items() if r.get('context_gaps')],
                 original_failures=read_json(output/'failures.json') if (output/'failures.json').exists() else [],
                 failures=failures,format_and_schema_repairs=repairs,usage=dict(usage),actual_models=sorted(actual_models),
                 requests=len(list(output.glob('*.raw.request.json'))),discovery_requests=0,merge_requests=0,
                 semantic_acceptance='pending',publication_status='draft')
    write_json(output/'summary.json',summary)
    write_json(output/'selected-reconciliations.json',selected)
    write_json(output/'reviewed-frozen.json',dict(behaviors=[b for d in drafts for b in d['behaviors']],
               merged_sha256=protocol['merged_sha256'],publication_status='draft',semantic_review='pending'))
    write_json(output/'status.json',dict(execution='complete' if not failures else 'complete_with_unresolved',semantic_acceptance='pending'))
    print({k:v for k,v in summary.items() if k not in ['original_failures','format_and_schema_repairs']},flush=True)


if __name__=='__main__':
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--recheck',action='store_true')
    args=parser.parse_args()
    finalize(args.inventory,args.output,recheck=args.recheck)
