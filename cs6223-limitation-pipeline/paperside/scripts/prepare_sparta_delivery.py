"""First deliverable: paper-only interface and exact evidence repairs for frozen SparTA claims."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
from paperprobe.io import read_json,write_json
from paperprobe.independent_discovery import load_input
from paperprobe.delivery import model_call,exact_evidence,INTERFACE_PROMPT,CITATION_PROMPT
root=Path.cwd();out=root/'runs/team-complete-v1/sparta';out.mkdir(parents=True,exist_ok=True)
old=read_json(root/'runs/sparta-independent-k2-v2/protocol.json');pages,images=load_input(Path(old['baseline']))
behaviors=[b for p in sorted((root/'runs/sparta-k2-behaviors-v1').glob('M??-draft.json')) for b in read_json(p)['behaviors']]
missing=[b for b in behaviors if not exact_evidence(b['evidence'],pages)]
write_json(out/'paper-input.json',dict(pages=[dict(page=i,text=t) for i,t in enumerate(pages,1)],images=[{k:v for k,v in x.items() if k!='data_url'} for x in images]))
def interface():
 r=model_call(out/'interface.raw.json',INTERFACE_PROMPT,dict(pages=[dict(page=i,text=t) for i,t in enumerate(pages,1)]),images)
 write_json(out/'interface.json',r);print('SPARTA_INTERFACE',len(r['scope']),len(r['eval_points']),flush=True)
def repairs():
 for n in range(0,len(missing),12):
  batch=missing[n:n+12];inds=sorted({e.get('page') or int(e['locator'].split('.')[-1]) for b in batch for e in b['evidence']})
  r=model_call(out/f'citations-{n//12:02d}.raw.json',CITATION_PROMPT,dict(items=batch,pages=[dict(page=p,text=pages[p-1]) for p in inds]),[images[p-1] for p in inds])
  write_json(out/f'citations-{n//12:02d}.json',r);print('SPARTA_CITATIONS',n,len(r['items']),flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:
 a=pool.submit(interface);b=pool.submit(repairs);a.result();b.result()
