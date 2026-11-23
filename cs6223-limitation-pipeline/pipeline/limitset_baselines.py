"""Plan isolated limitset baseline runs.

Execution is deliberately unavailable until the swarmlab input adapter is implemented.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from pipeline.limitset import ROOT, RAW, read, safe_path


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m pipeline limitset baseline')
    parser.add_argument('--method', required=True, choices=['b1', 'b2'])
    parser.add_argument('--split', required=True, choices=['validation', 'test'])
    parser.add_argument('--case')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--out', type=Path, default=ROOT / 'out/limitset_baselines')
    parser.add_argument('--raw', type=Path, default=RAW)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if min(args.repeats, args.workers) < 1:
        parser.error('repeats and workers must be positive')
    ids = read(ROOT / 'data/limitset/splits.json')[args.split]
    if args.case and args.case not in ids:
        parser.error('case is not in the selected split')
    selected = [case for case in ids if not args.case or args.case == case]
    raw, out = safe_path(args.raw).resolve(), safe_path(args.out).resolve()
    if not args.dry_run:
        parser.error('baseline execution is not implemented')
    env = dict(os.environ)
    for case in selected:
        for repeat in range(1, args.repeats + 1):
            run = out / 'runs' / case / f'r{repeat}'
            inp = run / 'input'
            if not inp.exists():
                run.mkdir(parents=True, exist_ok=True)
                subprocess.run([sys.executable, str(ROOT / 'scripts/limitset/make_case_dir.py'), case,
                                '--out', str(inp), '--raw', str(raw)], check=True, env=env)
            if {p.name for p in inp.iterdir()} != {'paper.pdf', 'case.json'}:
                raise ValueError('unexpected files in isolated case input')
            print(f'{args.method} {case} r{repeat}: {inp}')
