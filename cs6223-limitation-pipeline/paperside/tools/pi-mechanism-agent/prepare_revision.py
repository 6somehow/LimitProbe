"""Prepare a verdict revision with verbatim prior read_repo results; preserve all attempts."""
import argparse
import json
from pathlib import Path
from paperprobe.io import read_json,write_json


def prepare(source, prior, output, finalize_only=False):
    if output.exists():raise ValueError('Fresh output required')
    inp=read_json(source/'input.json');packet=[];spans=[];seen=set()
    for folder in [*prior,source]:
        for line in (folder/'tools.jsonl').read_text().splitlines():
            t=json.loads(line)
            if t['name']!='read_repo':continue
            r=t['result'];key=tuple(r[k] for k in ['repo','path','start_line','end_line'])
            if key in seen:continue
            seen.add(key);spans.append({k:r[k] for k in ['repo','path','start_line','end_line']})
            packet.append(dict(origin=folder.name,result=r))
    inp['evidence_packet']=packet;inp['seed_read_spans']=spans
    if (source/'parsed-candidate.json').exists():inp['candidate_report']=read_json(source/'parsed-candidate.json')
    inp['baseline_usage']={'total_tokens':110000}
    inp['revision_contract']={
      'why':'Finalization of the SAME source investigation. All actual source read results are supplied. No further tools needed. Return the complete final JSON now; reconcile local function body evidence, dependency implementation, unsupported fixed-point equivalence, and termination caveat. No mechanical renaming of old judgments.' if finalize_only else 'Previous draft stopped before reading local function body; implemented label contradicts missing_parts; termination requires mathematical reasoning, not proof assertions. Reassess all rows using complete actual source packet and any additional readonly tools.',
      'source_packet':'All unique actual read_repo results from preceding stages; raw responses preserved.'}
    if finalize_only:inp['finalize_only']=True
    output.mkdir(parents=True);write_json(output/'input.json',inp)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--prior',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--finalize-only',action='store_true');a=p.parse_args();prepare(a.source,a.prior,a.output,a.finalize_only)
