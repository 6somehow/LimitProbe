"""Sync data/limitset2/HUMAN_REVIEW.md (human-reviewed text) into labels.jsonl. Scorer-side only; generators never read either file."""
import json, re, sys
from pathlib import Path
root = Path('data/limitset2')
sheet = (root / 'HUMAN_REVIEW.md').read_text(encoding='utf-8')
labels = [json.loads(l) for l in (root / 'labels.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
by_id = {l['label_id']: l for l in labels}
def items(text):
    parts = re.split(r'(?<=[.!?\)])\s*;\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]
done, decisions = 0, {}
for block in re.split(r'\n(?=## LS2-)', sheet):
    m = re.match(r'## (LS2-\d\d-L\d)\b', block)
    if not m or m.group(1) not in by_id:
        continue
    lab = by_id[m.group(1)]
    lines = [x for x in block.split('\n')]
    head = next((x for x in lines if x.startswith('**') and x.rstrip().endswith('**')), None)
    if head:
        lab['headline'] = head.strip().strip('*').strip()
    body = [x for x in lines[1:] if x.strip() and not x.startswith('**') and not x.startswith('- ')]
    if body:
        lab['claim'] = body[0].strip()
    def field(name):
        for x in lines:
            if x.startswith(f'- {name}:'):
                return x.split(':', 1)[1].strip()
    if field('Critical link'): lab['critical_link'] = field('Critical link')
    if field('Conditions'): lab['necessary_conditions'] = items(field('Conditions'))
    if field('Defeaters'): lab['defeaters'] = items(field('Defeaters'))
    if field('Locations'): lab['source_locations'] = [field('Locations')]
    review = field('Review') or ''
    decisions[lab['label_id']] = 'keep' if '[x] keep' in review else 'edit' if '[x] edit' in review else 'drop' if '[x] drop' in review else 'unmarked'
    lab['review_status'] = 'human_reviewed'
    lab['labeler'] = 'claude-opus-5-5 draft, human-reviewed and edited by the dataset owner (decision: %s)' % decisions[lab['label_id']]
    done += 1
(root / 'labels.jsonl').write_text(''.join(json.dumps(l, ensure_ascii=False) + '\n' for l in labels), encoding='utf-8')
print('synced', done, 'of', len(labels), dict(__import__('collections').Counter(decisions.values())))
