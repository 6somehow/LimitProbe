#!/usr/bin/env python3
"""Build a single-case input directory without reading reference labels."""
import argparse
import json
import shutil
from pathlib import Path
from normalize import digest, read_jsonl, safe_pdf

ROOT = Path(__file__).resolve().parents[2]
import os
DEFAULT_RAW = Path(os.environ.get('LIMITSET_RAW') or ROOT.parent / 'CS6223_Limitation_Testset')  # dataset root, outside git


def build(case_id, out, cases_path, raw):
    matches = [c for c in read_jsonl(cases_path) if c['case_id'] == case_id]
    if len(matches) != 1:
        raise ValueError('case ID not found or duplicated')
    case = matches[0].copy()
    pdf = safe_pdf(raw, case['pdf_path'])
    if digest(pdf) != case['pdf_sha256']:
        raise ValueError('PDF checksum mismatch')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(pdf, out / 'paper.pdf')
    case['pdf_path'] = 'paper.pdf'
    (out / 'case.json').write_text(json.dumps(case, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('case_id')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--raw', type=Path, default=DEFAULT_RAW)
    p.add_argument('--cases', type=Path, default=ROOT / 'data/limitset/cases.jsonl')
    a = p.parse_args()
    build(a.case_id, a.out, a.cases, a.raw)


if __name__ == '__main__':
    main()
