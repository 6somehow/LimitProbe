"""Rebuild the study inputs from original public PDFs and exact author Git blobs."""
import argparse
from pathlib import Path
import subprocess

from corpus_ledger import load
from pilot import HERE, dump, sha
from swarm_study import DEV, TEST

PAPER_ONLY = ('onesidedmw','cxlfork','juneberry','twilight-tlite')


def prepare(output, resume=False):
    import pymupdf
    from pypdf import PdfReader

    assets = load(HERE/'study-corpus.json')
    output.mkdir(parents=True,exist_ok=resume)
    for branch, ids in (
        ('method-boundary-fixed-draft-v2-teams', [*DEV.values(), *PAPER_ONLY]),
        ('method-boundary-fixed-draft-v2-grounded', list(TEST.values())),
    ):
        root = output/branch
        frozen = []
        for paper in ids:
            folder = root/paper
            folder.mkdir(parents=True,exist_ok=resume)
            meta = assets[paper]
            pdf = folder/'original.pdf'
            if not pdf.exists():
                temporary = pdf.with_suffix('.download')
                subprocess.run(['curl','--fail','--location','--silent','--show-error',
                                '--max-time','120','--retry','2','--output',str(temporary),
                                meta['pdf_url']],check=True,timeout=380)
                if sha(temporary.read_bytes())!=meta['pdf_sha256']:
                    raise ValueError(f'Publisher PDF hash differs for {paper}')
                temporary.replace(pdf)
            if sha(pdf.read_bytes())!=meta['pdf_sha256']:
                raise ValueError(f'Publisher PDF hash differs for {paper}')
            images = folder/'images'
            images.mkdir(exist_ok=resume)
            pages = []
            with pymupdf.open(pdf) as document:
                for i,page in enumerate(PdfReader(pdf).pages,1):
                    text = page.extract_text() or ''
                    pages.append(dict(page=i,text=text,numbered='\n'.join(
                        f'{line}: {content}' for line,content in enumerate(text.splitlines(),1))))
                    document[i-1].get_pixmap(matrix=pymupdf.Matrix(0.9,0.9)).save(images/f'{i}.png')
            dump(folder/'paper.json',pages)
            commit = meta.get('commit')
            repo = None
            if commit:
                repo = folder/'repo.git'
                if not repo.exists():
                    subprocess.run(['git','init','--bare','-q',str(repo)],check=True,timeout=30)
                git = ['git','-C',str(repo)]
                if subprocess.run([*git,'cat-file','-e',f'{commit}^{{commit}}'],timeout=30,
                                  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
                    subprocess.run([*git,'fetch','--depth=1','--no-tags',meta['repo_url'],commit],check=True,timeout=250)
                sections = []
                for ref in meta['literature_study_source_spans']:
                    path,end = ref['path'],ref['end']
                    source = subprocess.check_output([*git,'show',f'{commit}:{path}'],timeout=25)
                    lines = source.decode('utf-8').splitlines()[:end]
                    if len(lines)!=end:
                        raise ValueError(f'Truncated original source: {paper}/{path}')
                    sections.append(f'FILE {path} | original lines 1–{end}\n'+'\n'.join(
                        f'{n}: {line}' for n,line in enumerate(lines,1)))
                packet = '\n\n'.join(sections)
                if sha(packet.encode())!=meta['literature_study_source_packet_sha256']:
                    raise ValueError(f'Rebuilt source packet hash differs for {paper}')
                (folder/'original-source-packet.txt').write_text(packet)
                frozen.append(folder/'original-source-packet.txt')
            dump(folder/'source.json',{'paper_id':paper,'pdf_sha256':meta['pdf_sha256'],
                                      'repo':str(repo) if repo else None,'commit':commit})
            frozen.extend([folder/'paper.json',folder/'source.json',*sorted(images.glob('*.png'))])
        dump(root/'input-index.json',{str(f.relative_to(root)):sha(f.read_bytes()) for f in frozen})


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    prepare(args.output.resolve(),args.resume)
