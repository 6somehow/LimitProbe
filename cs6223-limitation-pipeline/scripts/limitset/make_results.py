"""Build the results tables of docs/13_limitset_results.md from score.json dirs and run dirs (one judge for all arms)."""
import json, math, sys
from pathlib import Path

def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)

def fmt(k, n):
    if not n:
        return 'n/a'
    lo, hi = wilson(k, n)
    return f'{k}/{n} [{lo:.2f}, {hi:.2f}]'

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def preds(path):
    return [json.loads(l) for l in Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]

def row(name, score_dir, pred_file, run_dir=None, multi=True):
    s = Path(score_dir) / 'score.json'
    if not s.exists():
        return f'| {name} | (score pending) | | | | | | |'
    d = load(s)
    labels = [l for c in d['cases'] for l in (c.get('labels') or [c])]  # one entry per label (limitset2 has 2 per case)
    scored = [c for c in labels if c.get('found') is not None]
    hit = [c for c in scored if c['found']]
    papers = {}
    for c in scored:
        papers.setdefault(c['case_id'], False)
        papers[c['case_id']] = papers[c['case_id']] or bool(c['found'])
    ph = sum(papers.values())
    cond = sum(1 for c in scored if c['fields'].get('conditions'))
    defe = sum(1 for c in scored if c['fields'].get('defeaters'))
    recs = preds(pred_file)
    ok = [r for r in recs if not r.get('insufficient_evidence_reason')]
    nf = [len(r['findings']) for r in ok]
    ver = [f for r in ok for f in r['findings'] if 'quote_verified' in f]
    vrate = f"{sum(1 for f in ver if f['quote_verified'])}/{len(ver)}" if ver else 'n/a (not checked)'
    failed = len(recs) - len(ok)
    cost = 'n/a'
    if run_dir:
        dirs = [Path(x) for x in (run_dir if isinstance(run_dir, list) else [run_dir])]
        rd = dirs[0]
        cj = rd / 'cost.jsonl'
        if cj.exists():
            rows = [json.loads(l) for l in cj.read_text().splitlines() if l.strip()]
            pt = sum(r.get('prompt_tokens') or 0 for r in rows); ct = sum(r.get('completion_tokens') or 0 for r in rows)
            cost = f"{len(rows)} calls, {pt//1000}k+{ct//1000}k tok, {sum(r.get('wall_seconds') or 0 for r in rows)/max(1,len(rows)):.0f}s/case"
        else:
            ev = [load(p) for d_ in dirs for p in sorted(d_.glob('runs/*/r*/mechanism_evidence.json'))
                  if not (d_ == dirs[0] and len(dirs) > 1 and p.parts[-3] in ('LS2-05', 'LS2-09', 'LS2-11'))]  # failed first attempts are replaced by the retries
            if ev:
                calls = sum(1 + e.get('chunk_count', 0) for e in ev)
                secs = sum((e.get('inventory_seconds') or 0) + (e.get('chunks_seconds') or 0) for e in ev) / len(ev)
                cost = f'{calls} calls, tokens n/a, {secs:.0f}s/case'
    return (f"| {name} | {fmt(len(hit), len(scored))} | {fmt(ph, len(papers))} | "
            f"{(sum(nf)/len(nf)):.1f} ({failed} failed) | {vrate} | {cond}/{len(scored)} / {defe}/{len(scored)} | {cost} |")

def validation_row(name, score_dir):
    d = load(Path(score_dir) / 'score.json')
    cs = [c for c in d['cases'] if c['split'] == 'validation']
    scored = [c for c in cs if c.get('found') is not None]
    hit = [c['case_id'] for c in scored if c['found']]
    reps = [r['found'] for c in scored for r in c['repeats'] if r.get('found') is not None]
    return f"| {name} | {fmt(len(hit), len(scored))} {hit} | {sum(reps)}/{len(reps)} |"

if __name__ == '__main__':
    out = []
    out.append('### limitset2 (11 papers, 22 human-reviewed labels, judge gpt-6.1-terra, 1 repeat)\n')
    out.append('| System | Labels hit [Wilson 95%] | Papers with >=1 hit | Findings/paper | Verified-quote rate | Labels with conditions / defeaters covered | Cost |')
    out.append('|---|---|---|---|---|---|---|')
    L2 = [('B1 (x-test-2)', 'out/limitset2/g_b1', 'out/limitset2/b1/predictions.jsonl', 'out/limitset2/b1'),
          ('B1 x2 (x-test-2, two runs merged)', 'out/limitset2/g_b1x2', 'out/limitset2/b1x2.jsonl', None),
          ('v3c (x-test-2)', 'out/limitset2/g_a1c', 'out/limitset2/a1c_full.jsonl', ['out/limitset2/a1c', 'out/limitset2/a1c_retry2_LS2-05', 'out/limitset2/a1c_retry2_LS2-09', 'out/limitset2/a1c_retry2_LS2-11']),
          ('v3c + B1 (x-test-2)', 'out/limitset2/g_union', 'out/limitset2/union.jsonl', None),
          ('B1 (Claude Sonnet 5.5)', 'out/limitset2/g_b1_sonnet', 'out/limitset2/b1_sonnet/predictions.jsonl', 'out/limitset2/b1_sonnet'),
          ('v3c (Claude Sonnet 5.5)', 'out/limitset2/g_a1c_sonnet', 'out/limitset2/a1c_sonnet/predictions.jsonl', 'out/limitset2/a1c_sonnet'),
          ('v3c + B1 (Claude Sonnet 5.5)', 'out/limitset2/g_union_sonnet', 'out/limitset2/union_sonnet.jsonl', None)]
    for name, sd, pf, rd in L2:
        if Path(pf).exists():
            out.append(row(name, sd, pf, rd))
        else:
            out.append(f'| {name} | (not run / not finished) | | | | | |')
    out.append('\n### Validation (4 development cases CS6223-01..04, judge gpt-6.1-terra, 2 repeats where run)\n')
    out.append('| System | Cases found [Wilson 95%] and which | Repeats found |')
    out.append('|---|---|---|')
    for name, sd in [('Pipeline v1 (paper-only + enrichment)', 'out/limitset/g_val4'), ('Pipeline + swarm', 'out/limitset/g_valsw'),
                     ('Mechanism v1', 'out/limitset/g_val_mech'), ('B1', 'out/limitset_baselines/g_b1_val'), ('B2 (opencode)', 'out/limitset_baselines/g_b2_val')]:
        out.append(validation_row(name, sd) if (Path(sd) / 'score.json').exists() else f'| {name} | (score pending) | |')
    Path(sys.argv[1]).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('\n'.join(out))
