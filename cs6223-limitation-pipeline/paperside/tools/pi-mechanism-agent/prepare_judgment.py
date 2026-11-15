"""Prepare a bounded two-repository implementation assessment; never execute target."""
import argparse
import ast
from pathlib import Path
from paperprobe.io import read_json,write_json
from paperprobe.semantic_audit import git


def prepare(output):
    if output.exists():raise ValueError('Fresh output required')
    original=read_json(Path('runs/sparta-pi-mechanism-M02-v2/input.json'))
    dep=Path('data/repos/sparta-nni-artifact').resolve()
    commit=git(dep,'rev-parse','HEAD').strip()
    assert commit=='8c656fb380c577a984a6b4430b9d53fe91c8bd6e'
    files=[]
    for raw in git(dep,'ls-tree','-r','--long','-z',commit).split('\0'):
        if not raw:continue
        info,p=raw.split('\t',1);mode,kind,sha,size=info.split()
        files.append(dict(path=p,mode=mode,kind=kind,sha=sha,size=int(size) if size!='-' else None))
    original['repositories']={
      'primary':{k:original[k] for k in ['repo','commit','files','definitions','edges','index']},
      'nni':dict(repo=str(dep),commit=commit,files=files,definitions={},edges=[],index=dict(skipped=[],note='Python call index not built for dependency; search and read source.'))}
    original['dependency_provenance']=dict(
      readme_branch='https://github.com/microsoft/nni.git refs/heads/sparta_artifact',
      readme_branch_resolved_commit=original['commit'],
      installed_dependency='https://github.com/zheng-ningxin/nni.git refs/heads/artifact',
      installed_dependency_commit=commit,
      declaration=dict(repo='primary',path='image/Dockerfile',note='Read this configuration to verify dependency mapping.'),
      resolution_note='Current branch head pinned for this static assessment; 2022 Docker build did not pin a commit. Historical runtime version is unknown.')
    navigation=[]
    for f in files:
        if not f['path'].endswith('.py') or f['kind']!='blob' or f['size']>300000:continue
        source=git(dep,'show',commit+':'+f['path'])
        if 'def propagate_mask(' not in source:continue
        tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='propagate_mask':
                navigation.append(dict(repo='nni',path=f['path'],symbol=node.name,start_line=node.lineno,end_line=node.end_lineno,origin='AST definition lookup of actual method called by experiment scripts; no semantic verdict'))
    original['source_navigation']=navigation
    original['baseline_usage']={'total_tokens':120000}
    output.mkdir(parents=True);write_json(output/'input.json',original)
    print('Prepared 14 frozen behaviors and 2 pinned repositories; no prior semantic verdicts supplied.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
