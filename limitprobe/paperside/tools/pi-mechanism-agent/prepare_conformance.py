"""Freeze a fresh conformance assessment without supplying previous verdicts."""
import argparse
from pathlib import Path
from paperprobe.io import read_json,write_json,file_sha256
from paperprobe.semantic_audit import git


def prepare(output):
    if output.exists():raise ValueError('Fresh run directory required')
    source=Path('runs/sparta-pi-judgment-M02-v7/input.json')
    old=read_json(source)
    inp={k:old[k] for k in ['repo','commit','mechanism','behaviors','pages','images','repositories','source_navigation','dependency_provenance','provenance']}
    # Coalesce overlapping source reads without summarizing or filling unread gaps.
    observed={}
    for packet in old['evidence_packet']:
        r=packet['result'];alias=r['repo'];repo=inp['repositories'][alias]
        blob=git(Path(repo['repo']),'show',repo['commit']+':'+r['path']).split('\n')
        for line in range(r['start_line'],r['end_line']+1):
            original=f'{line}: {blob[line-1]}'
            stored=r['lines'].split('\n')[line-r['start_line']]
            if stored!=original:raise ValueError('Cached source differs from pinned blob')
            observed.setdefault((alias,r['path']),{})[line]=original
    packets=[];spans=[]
    for (alias,path),lines in sorted(observed.items()):
        ordered=sorted(lines);groups=[]
        for n in ordered:
            if not groups or n!=groups[-1][-1]+1:groups.append([n])
            else:groups[-1].append(n)
        for group in groups:
            span=dict(repo=alias,path=path,start_line=group[0],end_line=group[-1])
            spans.append(span);packets.append(dict(origin='verified prior Git reads; overlaps coalesced, no omitted-line inference',result=dict(**span,commit=inp['repositories'][alias]['commit'],lines='\n'.join(lines[n] for n in group))))
    inp.update(assessment='claim_conformance',evidence_packet=packets,seed_read_spans=spans,
        baseline_usage={'total_tokens':110000},
        assessment_contract=dict(unit='whole M02 mechanism; per-behavior conformance accounting',
          labels=['supports','deviates','absent'],review_states=['completed','pending'],previous_verdicts_supplied=False,
          source_packet_sha256=file_sha256(source),context_note='Reuse verified source reads and original paper; no old verdicts, candidate report, counts or expected negative IDs supplied.',
          max_requests=4,max_tools=12,max_output_tokens=7500,soft_token_target=110000,target_execution='not_run'))
    output.mkdir(parents=True);write_json(output/'input.json',inp)
    print(f'Prepared {len(inp["behaviors"])} frozen behaviors, {len(spans)} verified contiguous source spans; no old verdicts.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
