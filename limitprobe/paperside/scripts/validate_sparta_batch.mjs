/** Validate preserved evidence and final accounting, not the semantic truth of LLM verdicts. */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const root=process.cwd(),cohort=path.resolve(process.argv[2]),partial=process.argv.includes('--partial');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const spec=read(path.join(cohort,'cohort.json')),seen=new Set(),results=[],cache=new Map();
for(const batch of spec.batches){
 const {validateConformance}=await import(pathToFileURL(path.join(batch,'runtime/conformance.mjs')));
 for(const mid of fs.readdirSync(batch).filter(s=>/^M\d\d$/.test(s)).sort()){
  assert(!seen.has(mid),'Duplicate mechanism across batches');
  const folder=path.join(batch,mid),state=read(path.join(folder,'state.json'));
  if(partial&&state.state!=='reviewed')continue;
  seen.add(mid);
  assert.equal(state.state,'reviewed',`${mid} must finish before acceptance`);
  const run=path.join(batch,state.report),input=read(path.join(run,'input.json')),report=read(path.join(run,'report.json'));
  const frozen=read(path.join(root,'runs/sparta-k2-behaviors-v1',`${mid}-draft.json`));
  assert.deepEqual(input.behaviors,frozen.behaviors,'Paper-side behaviors must remain frozen');
  validateConformance(report,input.behaviors,read(path.join(run,'read-spans.json')),input.pages);
  let verifiedReads=0;
  for(const stage of fs.readdirSync(folder).filter(s=>fs.existsSync(path.join(folder,s,'input.json')))){
   const stagePath=path.join(folder,stage),i=read(path.join(stagePath,'input.json'));
   const tp=path.join(stagePath,'tools.jsonl');
   const tools=fs.existsSync(tp)?fs.readFileSync(tp,'utf8').trim().split('\n').filter(Boolean).map(s=>JSON.parse(s)):[];
   const sources=[...i.evidence_packet.map(x=>x.result),...tools.filter(t=>t.name==='read_repo'&&t.result?.lines).map(t=>t.result)];
   for(const source of sources){
    const repo=i.repositories[source.repo];assert(repo,'Source alias must resolve');
    if(source.commit)assert.equal(source.commit,repo.commit,'Evidence commit mismatch');
    const key=`${repo.repo}:${repo.commit}:${source.path}`;
    if(!cache.has(key))cache.set(key,execFileSync('git',['-C',repo.repo,'show',`${repo.commit}:${source.path}`],{encoding:'utf8',maxBuffer:3000000}).split('\n'));
    const expected=cache.get(key).slice(source.start_line-1,source.end_line).map((s,n)=>`${source.start_line+n}: ${s}`).join('\n');
    assert.equal(source.lines,expected,`Source content mismatch: ${key}`);verifiedReads++;
   }
  }
  results.push({mechanism:mid,behaviors:report.checks.length,verified_source_reads:verifiedReads,artifact_pending:report.checks.filter(c=>c.artifact.review_state==='pending').length});
 }
}
if(!partial){
 assert.deepEqual([...seen].sort(),[...spec.mechanisms].sort(),'All 19 remaining mechanisms required');
 assert.equal(results.reduce((s,r)=>s+r.behaviors,0),192);
}
const output={checks:'schema, frozen behaviors, actual source content and citation coverage; not semantic ground truth',partial,mechanisms:results.length,behaviors:results.reduce((s,r)=>s+r.behaviors,0),results,target_execution:'not_run'};
fs.writeFileSync(path.join(cohort,partial?'acceptance.partial.json':'acceptance.json'),JSON.stringify(output,null,2));
console.log(JSON.stringify(output,null,2));
