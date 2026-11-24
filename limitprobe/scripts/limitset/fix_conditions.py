"""Coerce finding['conditions'] to a list of strings in a predictions.jsonl (older mechanism-mode runs wrote a string)."""
import json, sys
src, dst = sys.argv[1:3]
n = 0
with open(src, encoding='utf-8') as f, open(dst, 'w', encoding='utf-8') as g:
    for line in f:
        if not line.strip():
            continue
        r = json.loads(line)
        for x in r.get('findings', []):
            c = x.get('conditions')
            if not isinstance(c, list):
                x['conditions'] = [str(c)] if c else []
                n += 1
        g.write(json.dumps(r, ensure_ascii=False) + '\n')
print('fixed', n, 'findings')
