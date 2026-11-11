"""Freeze mechanism/paper inputs and unranked pinned source metadata for Pi tools."""
import argparse
from pathlib import Path

from paperprobe.io import file_sha256, read_json, write_json
from paperprobe.semantic_audit import git, index


def prepare(output):
    if output.exists():raise ValueError('Use a fresh Pi run directory')
    inventory=Path('runs/sparta-independent-k2-v2')
    continuation=Path('runs/sparta-k2-behaviors-v1')
    repo=Path('data/repos/team-sparta').resolve()
    commit=read_json(Path('runs/team-final-20261108/sparta/manifest.json'))['commit']
    if git(repo,'rev-parse','HEAD').strip()!=commit:raise ValueError('Repository commit differs')
    mechanism=next(m for m in read_json(inventory/'merged-mechanisms.json')['mechanisms'] if m['id']=='M02')
    request=read_json(inventory/'discovery-1.raw.request.json')
    files=[]
    for raw in git(repo,'ls-tree','-r','--long','-z',commit).split('\0'):
        if not raw:continue
        info,path=raw.split('\t',1);mode,kind,sha,size=info.split()
        files.append(dict(path=path,mode=mode,kind=kind,sha=sha,size=int(size) if size!='-' else None))
    defs,edges,stats=index(repo,commit)
    definitions={k:{field:d[field] for field in ['path','name','start','end']} for k,d in defs.items()}
    baseline=read_json(Path('runs/sparta-k2-code-M02-v1/audit.json'))
    output.mkdir(parents=True)
    write_json(output/'input.json',dict(repo=str(repo),commit=commit,mechanism=mechanism,
        behaviors=read_json(continuation/'M02-draft.json')['behaviors'],
        pages=request['data']['pages'],images=request['image_pages'],
        files=files,definitions=definitions,edges=edges,index=stats,
        baseline_usage=baseline['usage'],
        provenance=dict(merged_sha256=file_sha256(inventory/'merged-mechanisms.json'),
                        draft_sha256=file_sha256(continuation/'M02-draft.json'))))
    print('Prepared M02 with 14 behaviors, full paper access and unranked pinned source index; no prior findings.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
