from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from paperprobe.io import read_json,write_json
from paperprobe.independent_discovery import load_input
from paperprobe.delivery import *
o=Path('runs/team-complete-v1/sparta');pages,images=load_input(Path(read_json(Path('runs/sparta-independent-k2-v2/protocol.json'))['baseline']))
bs=[b for p in sorted(Path('runs/sparta-k2-behaviors-v1').glob('M??-draft.json')) for b in read_json(p)['behaviors']];missing=[b for b in bs if not exact_evidence(b['evidence'],pages)]
def review():
 r=model_call(o/'interface-review.raw.json',INTERFACE_REVIEW,dict(candidate=read_json(o/'interface.json'),pages=indexed_pages(pages)),images)
 for field in ['scope','eval_points']:
  for row in r[field]:row['evidence']=span_evidence(row['evidence_spans'],pages)
 write_json(o/'interface-reviewed.json',r);print('INTERFACE_REVIEWED',len(r['scope']),len(r['eval_points']),flush=True)
def cites():
 for n in range(0,len(missing),12):
  rows=missing[n:n+12];inds=sorted({e.get('page') or int(e['locator'].split('.')[-1]) for b in rows for e in b['evidence']})
  r=model_call(o/f'citation-spans-{n//12:02d}.raw.json',SPAN_CITATION_PROMPT,dict(items=rows,pages=indexed_pages(pages,inds)),[images[p-1] for p in inds])
  for row in r['items']:row['evidence']=span_evidence(row['evidence_spans'],pages)
  write_json(o/f'citation-spans-{n//12:02d}.json',r);print('CITATION_SPANS',n,flush=True)
with ThreadPoolExecutor(max_workers=2) as p:
 a=p.submit(review);b=p.submit(cites);a.result();b.result()
