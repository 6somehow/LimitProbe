"""Copy the specified results from a main checkout, without inputs or logs.

Run: conda run -n findlimit python scripts/limitset/bundle_results.py
The source can be overridden with --source and the destination with --root.
Every file is checked before any destination file is written.
"""
import argparse
import re
from pathlib import Path

import os
SOURCE = Path(os.environ.get('LIMITSET_OUT_ROOT') or Path(__file__).resolve().parents[2])  # directory that holds out/ with the raw run outputs
SYSTEMS = [
 ('limitset2','b1','limitset2/b1/predictions.jsonl','limitset2/g_b1','limitset2/b1'),
 ('limitset2','b1x2','limitset2/b1x2.jsonl','limitset2/g_b1x2',None),
 ('limitset2','v3c_xtest2','limitset2/a1c_full.jsonl','limitset2/g_a1c','limitset2/a1c'),
 ('limitset2','union_xtest2','limitset2/union.jsonl','limitset2/g_union',None),
 ('limitset2','b1_sonnet','limitset2/b1_sonnet/predictions.jsonl','limitset2/g_b1_sonnet','limitset2/b1_sonnet'),
 ('limitset2','v3c_sonnet','limitset2/a1c_sonnet/predictions.jsonl','limitset2/g_a1c_sonnet','limitset2/a1c_sonnet'),
 ('limitset2','union_sonnet','limitset2/union_sonnet.jsonl','limitset2/g_union_sonnet',None),
 ('validation','val4','limitset/val4/predictions.jsonl','limitset/g_val4','limitset/val4'),
 ('validation','valsw','limitset/valsw/predictions.jsonl','limitset/g_valsw','limitset/valsw'),
 ('validation','val_mech','limitset/val_mech/predictions_fixed.jsonl','limitset/g_val_mech','limitset/val_mech'),
 ('validation','b1_val','limitset_baselines/b1_val/predictions.jsonl','limitset_baselines/g_b1_val','limitset_baselines/b1_val'),
 ('validation','b2_val','limitset_baselines/b2_val/predictions.jsonl','limitset_baselines/g_b2_val','limitset_baselines/b2_val'),
]
SECRET_PATTERNS = tuple(re.compile(p) for p in (
    rb'sk-[A-Za-z0-9_-]{20,}', rb'Bearer [A-Za-z0-9._-]{20,}',
    rb'''api[_-]?key["' :=]+[A-Za-z0-9_-]{16,}''', rb'SOCLAAS_API_KEY='))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--root', type=Path, default=Path('results/limitset_final'))
    args = parser.parse_args()
    out = args.source / 'out'
    files = []
    for dataset, name, prediction, score, run in SYSTEMS:
        target = args.root / dataset / name
        if not (out / score / 'score.json').exists() and name == 'union_xtest2':
            print('Skipped union_xtest2: score missing')
            continue
        files.extend([(out / prediction, target / 'predictions.jsonl'), (out / score / 'score.json', target / 'score.json')])
        if run:
            for filename in ('run_manifest.json', 'cost.jsonl'):
                p = out / run / filename
                if p.exists(): files.append((p, target / filename))
            runs = [out / run]
            if name == 'v3c_xtest2':
                runs += [out / ('limitset2/a1c_retry2_' + case) for case in ('LS2-05','LS2-09','LS2-11')]
            # Later retry evidence replaces original evidence for that case.
            evidence = {}
            for rd in runs:
                for p in sorted(rd.glob('runs/*/r*/mechanism_evidence.json')):
                    evidence[p.parts[-3]] = p
            for case, p in sorted(evidence.items()):
                files.append((p, target / 'cases' / case / p.name))
            if name == 'v3c_xtest2':
                for rd in runs:
                    for p in sorted(rd.glob('runs/*/r*/evaluation_critiques.json')):
                        files.append((p, target / 'cases' / p.parts[-3] / ('evaluation_critiques_' + rd.name + '.json')))
        if name in ('b1x2','union_xtest2','union_sonnet'):
            p = out / prediction
            for suffix in ('.origins.json', '.summary.json'):
                extra = p.with_suffix(suffix)
                if extra.exists(): files.append((extra, target / extra.name))
    for name in ('labels_en.jsonl','labels_en.manifest.json'):
        files.append((args.source / 'data/limitset' / name, Path('data/limitset') / name))
    contents = []
    for src, dst in files:
        data = src.read_bytes()
        if src.suffix.lower() == '.pdf' or b'%PDF-' in data:
            raise ValueError(f'PDF content in {src}; no files copied')
        for line_number, line in enumerate(data.splitlines(), 1):
            for pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    prefix = match.group()[:4].decode('ascii', errors='replace')
                    raise ValueError(f'Forbidden content in {src}:{line_number} ({prefix}); no files copied')
        contents.append((dst, data))
    for dst, data in contents:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
    print(f'Copied {len(contents)} files')

if __name__ == '__main__': main()
