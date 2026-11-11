/** Check actual completed corpus evidence; this is provenance, never semantic ground truth. */
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {execFileSync} from 'node:child_process';import {pathToFileURL} from 'node:url';
const base=path.resolve(process.argv[2]||'runs/team-complete-v1'),papers=process.argv.slice(3).length?process.argv.slice(3):['flexprefill','minference','infinigen','nnsmith'];
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),walk=p=>fs.existsSync(p)?fs.readdirSync(p,{withFileTypes:true}).flatMap(e=>e.isDirectory()&&e.name!=='node_modules'?walk(path.join(p,e.name)):e.isFile()?[path.join(p,e.name)]:[]):[];
const results=[],cache=new Map();
for(const pid of papers){
 const work=path.join(base,pid),inventory=read(path.join(work,'inventory/merged-mechanisms.json')).mechanisms,entries=read(path.join(work,'report-index.json'));
 assert.equal(entries.length,inventory.length,`${pid}: all mechanism reports required`);assert.equal(new Set(entries.map(x=>x.mechanism)).size,entries.length);
 const {validateConformance}=await import(pathToFileURL(path.join(work,'runtime/conformance.mjs')));let behaviors=0,completed=0,pending=0,sourceReads=0;const counts={supports:0,deviates:0,absent:0};
 for(const entry of entries){
  const run=entry.stage,i=read(path.join(run,'input.json')),r=read(path.join(run,'report.json')),frozen=read(path.join(work,'behaviors',entry.mechanism+'-draft.json')).behaviors;
  assert.deepEqual(i.behaviors,frozen,'Paper behavior drift');validateConformance(r,frozen,read(path.join(run,'read-spans.json')),i.pages);behaviors+=frozen.length;
  for(const c of r.checks){if(c.artifact.review_state==='pending')pending++;else{completed++;counts[c.artifact.verdict]++;}}
 }
 for(const name of walk(path.join(work,'code')).filter(p=>path.basename(p)==='input.json')){
  const i=read(name),t=path.join(path.dirname(name),'tools.jsonl');const tools=fs.existsSync(t)?fs.readFileSync(t,'utf8').trim().split('\n').filter(Boolean).map(x=>JSON.parse(x)):[];
  const sources=[...i.evidence_packet.map(x=>x.result),...tools.filter(t=>t.name==='read_repo'&&t.result?.lines).map(t=>t.result)];
  for(const source of sources){
   const repo=i.repositories[source.repo];assert(repo,'Source alias');if(source.commit)assert.equal(source.commit,repo.commit);
   const key=`${repo.repo}:${repo.commit}:${source.path}`;if(!cache.has(key))cache.set(key,execFileSync('git',['-C',repo.repo,'show',`${repo.commit}:${source.path}`],{encoding:'utf8',maxBuffer:4000000}).split('\n'));
   const expected=cache.get(key).slice(source.start_line-1,source.end_line).map((s,n)=>`${source.start_line+n}: ${s}`).join('\n');assert.equal(source.lines,expected,`Changed source ${key}`);sourceReads++;
  }
 }
 let requests=0,tokens=0,toolCalls=0;const failures=[];
 for(const name of walk(work).filter(p=>p.endsWith('.json'))){
  const n=path.basename(name);if(n.endsWith('.request.json')||/^request-\d+\.json$/.test(n))requests++;
  if(n.includes('snapshot')||n==='input.json')continue;
  let x;try{x=read(name);}catch{continue;}
  if(Array.isArray(x.choices)&&x.usage)tokens+=x.usage.total_tokens||0;
  if(n==='summary.json'&&fs.existsSync(path.join(path.dirname(name),'system-prompt.json'))){if(!x.usage_included_in_raw_response)tokens+=x.total_tokens||0;toolCalls+=x.tool_calls||0;if(x.error||x.validation_error)failures.push({stage:path.relative(work,path.dirname(name)),error:x.error||x.validation_error});}
 }
 const result={paper:pid,mechanisms:inventory.length,behaviors,completed,pending,counts,verified_source_records:sourceReads,requests,returned_tokens:tokens,tool_calls:toolCalls,rejected_stages:failures,target_execution:'not_run',semantic_truth:'pending independent review'};results.push(result);console.log(JSON.stringify(result));
}
fs.writeFileSync(path.join(base,'corpus-acceptance.json'),JSON.stringify({checks:'frozen IDs; exact source contents/commits; read citation ranges; three conclusions and separate lifecycle; actual logged usage',results},null,2));
