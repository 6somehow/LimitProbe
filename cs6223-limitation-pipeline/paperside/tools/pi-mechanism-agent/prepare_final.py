"""Freeze compact final adjudication input from the same investigation's actual reads."""
import argparse
from pathlib import Path
from paperprobe.io import read_json,write_json
from prepare_revision import prepare


def finalize(output):
    base=Path('runs')
    prepare(base/'sparta-pi-judgment-M02-v3',
            [base/'sparta-pi-judgment-M02-v1',base/'sparta-pi-judgment-M02-v2'],output,True)
    inp=read_json(output/'input.json');inp.pop('candidate_report',None);inp['compact_finalization']=True
    inp['revision_contract']['why']='Compact final adjudication from actual source reads, no prior candidate conclusions. Previous streaming finalization timed out, full partial response preserved; semantic classifications must be reassessed from source.'
    write_json(output/'input.json',inp)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);finalize(p.parse_args().output)
