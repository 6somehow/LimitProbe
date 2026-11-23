#!/usr/bin/env python3
"""Build data/limitset2 (held-out set v2) from papers in RAW and draft labels.

RAW (outside git): <limitset2-raw>/{papers/<id>/paper.pdf,paper.txt, draft_labels/<id>.json}
Writes: data/limitset2/{cases.jsonl, labels.jsonl, splits.json, manifest.json, REVIEW.md}
Labels are scorer-only; generators must never read them.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = Path('<limitset2-raw>')
CATS = {'applicability_limitation', 'mechanism_origin_unclear', 'method_shortcoming'}
DISC = {'explicit_boundary_reported', 'mechanism_reported_consequence_inferred', 'mixed_reported_and_inferred', 'inferred'}
REQ = ['case_id', 'paper_id', 'category_code', 'headline', 'claim', 'reasoning_chain', 'mechanism_insight',
       'critical_link', 'necessary_conditions', 'defeaters', 'caveats', 'do_not_infer', 'source_locations',
       'verbatim_quotes', 'disclosure_assessment', 'claim_nature', 'labeler']

# id, title, venue, paper URL, code URL (None = no public code)
PAPERS = [
    ('flexprefill', 'FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference', 'ICLR 2025', 'https://arxiv.org/abs/2502.20766', 'https://github.com/bytedance/FlexPrefill'),
    ('flexposit', 'FlexPosit: Tunable Fractional Precision for LLM Inference Accelerators', 'MICRO 2026', 'project copy (third_party/papers/flexposit.pdf)', 'see data/flexposit/artifact.json'),
    ('qoserve', 'QoServe: Breaking the Silos of LLM Inference Serving', 'ASPLOS 2026', 'project copy (third_party/papers/qoserve.pdf)', 'see data/qoserve/artifact.json'),
    ('tessera', 'Tessera (OSDI 2026)', 'OSDI 2026', 'project copy (docs/osdi26-hu-weifang.pdf)', None),
    ('distserve', 'DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving', 'OSDI 2024', 'https://arxiv.org/abs/2401.09670', 'https://github.com/LLMServe/DistServe'),
    ('sarathi', 'Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve', 'OSDI 2024', 'https://arxiv.org/abs/2403.02310', 'https://github.com/microsoft/sarathi-serve'),
    ('streamingllm', 'Efficient Streaming Language Models with Attention Sinks', 'ICLR 2024', 'https://arxiv.org/abs/2309.17453', 'https://github.com/mit-han-lab/streaming-llm'),
    ('h2o', 'H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models', 'NeurIPS 2023', 'https://arxiv.org/abs/2306.14048', 'https://github.com/FMInference/H2O'),
    ('quest', 'Quest: Query-Aware Sparsity for Efficient Long-Context LLM Inference', 'ICML 2024', 'https://arxiv.org/abs/2406.10774', 'https://github.com/mit-han-lab/Quest'),
    ('awq', 'AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration', 'MLSys 2024', 'https://arxiv.org/abs/2306.00978', 'https://github.com/mit-han-lab/llm-awq'),
    ('vattention', 'vAttention: Dynamic Memory Management for Serving LLMs without PagedAttention', 'ASPLOS 2025', 'https://arxiv.org/abs/2405.04437', 'https://github.com/microsoft/vattention'),
]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def check_label(lab, text):
    errs = [f'missing {k}' for k in REQ if k not in lab]
    if lab.get('category_code') not in CATS:
        errs.append('bad category_code')
    if lab.get('disclosure_assessment') not in DISC:
        errs.append('bad disclosure_assessment')
    t = norm(text)
    for q in lab.get('verbatim_quotes') or []:
        if norm(q) not in t:
            errs.append(f'quote not in paper.txt: {q[:60]}')
    if not lab.get('verbatim_quotes'):
        errs.append('no verbatim_quotes')
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', type=Path, default=RAW)
    ap.add_argument('--out', type=Path, default=ROOT / 'data/limitset2')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    cases, labels, problems = [], [], []
    for i, (pid, title, venue, url, code) in enumerate(PAPERS, 1):
        pdf = a.raw / 'papers' / pid / 'paper.pdf'
        cid = f'LS2-{i:02d}'
        cases.append({'case_id': cid, 'paper_id': pid, 'title': title, 'venue': venue, 'mode': 'paper-only',
                      'repository': None, 'code_url': code, 'paper_url': url,
                      'pdf_path': f'papers/{pid}/paper.pdf', 'pdf_sha256': sha(pdf)})
        draft = a.raw / 'draft_labels' / f'{pid}.json'
        if not draft.is_file():
            problems.append(f'{cid} {pid}: no draft labels')
            continue
        text = (a.raw / 'papers' / pid / 'paper.txt').read_text(encoding='utf-8', errors='replace')
        for j, lab in enumerate(json.loads(draft.read_text(encoding='utf-8')), 1):
            errs = check_label(lab, text)
            problems += [f'{cid}-{j} {pid}: {e}' for e in errs]
            labels.append({'schema_version': 'cs6223.limitset2.v1', **lab, 'case_id': cid, 'label_id': f'{cid}-L{j}',
                           'review_status': 'draft_unreviewed', 'runtime_test': {'status': 'not_run', 'verdict': None, 'confidence_level': None}})
    w = lambda name, rows: (a.out / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    w('cases.jsonl', cases)
    w('labels.jsonl', labels)
    (a.out / 'splits.json').write_text(json.dumps({
        'frozen': '2026-11-23',
        'rule': 'Held-out set v2. All cases are test. Built after prompt v3 was designed; prompt designers and generators must not read labels.jsonl. Labels are model drafts (claude-opus-5-5) until human review.',
        'test': [c['case_id'] for c in cases]}, indent=2) + '\n', encoding='utf-8')
    (a.out / 'manifest.json').write_text(json.dumps({
        'raw_root': str(a.raw), 'files': {n: sha(a.out / n) for n in ('cases.jsonl', 'labels.jsonl', 'splits.json')},
        'pdfs': {c['pdf_path']: c['pdf_sha256'] for c in cases}, 'problems': problems}, indent=2) + '\n', encoding='utf-8')
    lines = ['# limitset2 label review sheet', '', 'Status: model drafts (claude-opus-5-5), NOT human-reviewed. Mark each label: keep / edit / drop.', '']
    for lab in labels:
        lines += [f"## {lab['label_id']} ({lab['paper_id']}) - {lab['category_code']} - {lab['disclosure_assessment']}",
                  f"**{lab['headline']}**", '', lab['claim'], '', f"- Critical link: {lab['critical_link']}",
                  f"- Conditions: {'; '.join(lab['necessary_conditions'])}", f"- Defeaters: {'; '.join(lab['defeaters'])}",
                  f"- Locations: {'; '.join(lab['source_locations'])}", '- Review: [ ] keep  [ ] edit  [ ] drop', '']
    (a.out / 'REVIEW.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'cases {len(cases)} labels {len(labels)} problems {len(problems)}')
    for p in problems:
        print(' ', p)


if __name__ == '__main__':
    main()
