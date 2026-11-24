"""Run the four paper-only Test cases under the reviewed study protocol."""
import argparse
import asyncio
import fcntl
from pathlib import Path
import shutil

from corpus_ledger import load
from pilot import dump, sha
from swarm_evaluation import PAPER_ONLY
from swarm_study import CONDITIONS, StudyCell, run_once_cell, verify_inputs


class PaperCell(StudyCell):
    def cfg(self):
        config = super().cfg()
        config['tools'] = [tool for tool in config['tools'] if tool['name']=='read_paper']
        if 'gapReview' in config:
            config['gapReview'].update(
                routes=(config['gapReview']['routes'][0],
                        'Follow the selection and stopping rules described in the paper back to the objective.'),
                verification=config['gapReview']['verification'].replace('paper and code tools','paper tools'),
            )
        return config


def prepare(parent, original, output):
    verify_inputs(parent)
    release = parent/'test-release.json'
    if not release.is_file() or load(release).get('input_index_sha256') != sha((parent/'input-index.json').read_bytes()):
        raise ValueError('Paper-only Test requires a reviewed and sealed Dev protocol')
    protocol = load(parent/'protocol.json')
    output.mkdir(parents=True,exist_ok=False)
    for name in load(parent/'input-index.json'):
        if len(Path(name).parts)!=1 and not name.startswith(('runtime/','prompts-joint/')):
            continue
        if name == 'protocol.json':
            continue
        dst = output/name
        dst.parent.mkdir(exist_ok=True)
        shutil.copyfile(parent/name,dst)
    source_index = load(original/'input-index.json')
    for paper in PAPER_ONLY.values():
        for name, expected in source_index.items():
            if not name.startswith((f'{paper}/paper.json',f'{paper}/source.json',f'{paper}/images/')):
                continue
            blob = (original/name).read_bytes()
            if sha(blob)!=expected:
                raise ValueError(f'Frozen paper changed: {name}')
            path = output/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(blob)
        if load(output/paper/'source.json').get('repo'):
            raise ValueError(f'{paper} has an implementation input')
        (output/paper/'original-source-packet.txt').write_text('')
    system = output/'prompts-joint/system.txt'
    with system.open('a') as f:
        f.write('\nOnly the paper is supplied. Leave code_evidence empty and qualify all implementation assumptions.\n')
    protocol.update(split={'test':PAPER_ONLY},stratum='paper_only',parent_run=str(parent),
                    parent_release_sha256=sha(release.read_bytes()))
    dump(output/'protocol.json',protocol)
    shutil.copyfile(Path(__file__),output/Path(__file__).name)
    dump(output/'input-index.json',{str(p.relative_to(output)):sha(p.read_bytes())
                                     for p in output.rglob('*') if p.is_file()})


async def run(root):
    verify_inputs(root)
    protocol = load(root/'protocol.json')
    if protocol['stratum']!='paper_only':
        raise ValueError('Expected paper-only Test archive')
    if (root/Path(__file__).name).read_bytes()!=Path(__file__).read_bytes():
        raise ValueError('Paper-only runner changed since preparation')
    release = Path(protocol['parent_run'])/'test-release.json'
    if sha(release.read_bytes())!=protocol['parent_release_sha256']:
        raise ValueError('Reviewed Dev release changed')
    sem = asyncio.Semaphore(protocol['global_model_concurrency'])
    for paper in protocol['split']['test'].values():
        for condition in CONDITIONS:
            folder = root/paper/condition
            if (folder/'summary.json').is_file():
                continue
            if folder.exists():
                raise ValueError(f'Existing nonterminal archive: {folder}')
            if condition=='api_once':
                await run_once_cell(root,paper,folder)
            else:
                await PaperCell(root,paper,condition,sem).run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('root',type=Path)
    parser.add_argument('--study',type=Path)
    parser.add_argument('--original',type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action=='prepare':
        prepare(args.study.resolve(),args.original.resolve(),root)
    else:
        with (root/'.runner.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            asyncio.run(run(root))
