import {CONFORMANCE_SYSTEM,CONFORMANCE_REVIEW_SYSTEM,VERDICTS,validateConformance} from './conformance.mjs';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {Type} from 'typebox';
import {JUDGMENT_SYSTEM,validateJudgment,COMPACT_SYSTEM,expandCompactReport,EQUIVALENCE_REVIEW_SYSTEM} from './judgment.mjs';
import {createAgentSession, createExtensionRuntime, ModelRuntime, SessionManager, SettingsManager} from '@earendil-works/pi-coding-agent';

let SYSTEM = JUDGMENT_SYSTEM;

const runDir=path.resolve(process.argv[2]||'');
if(!process.argv[2])throw new Error('Pass prepared run directory');
const input=JSON.parse(fs.readFileSync(path.join(runDir,'input.json'),'utf8'));
if(fs.existsSync(path.join(runDir,'protocol.json')))throw new Error('Existing Pi attempt cannot be overwritten');
if(input.compact_finalization)SYSTEM=COMPACT_SYSTEM;
if(input.review_behavior_ids)SYSTEM=EQUIVALENCE_REVIEW_SYSTEM;
const conformance=input.assessment==='claim_conformance';
if(conformance)SYSTEM=input.semantic_review?CONFORMANCE_REVIEW_SYSTEM:CONFORMANCE_SYSTEM;
if(input.validation_feedback)SYSTEM+='\nSTRUCTURAL COMPLETION: correct the supplied validation_feedback, using actual source packets. Emit a complete schema-valid JSON; do not invent evidence or alter judgments merely to satisfy a label count. Keep fields concise (ideally <30 Chinese characters). No tools.';
const outputTokens=conformance?(input.assessment_contract?.max_output_tokens||7500):input.compact_finalization?6000:10000;
if(!process.env.SOCLAAS_API_KEY)throw new Error('SOCLAAS_API_KEY required');
const write=(name,value)=>fs.writeFileSync(path.join(runDir,name),JSON.stringify(value,null,2));
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
const redacted=value=>{
  if(typeof value==='string' && value.startsWith('data:image/'))return {image_data_omitted:true,sha256:hash(value)};
  if(value?.type==='image' && typeof value.data==='string')return {...value,data:{omitted:true,sha256:hash(value.data)}};
  if(Array.isArray(value))return value.map(redacted);
  if(value && typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,redacted(v)]));
  return value;
};
let requestCount=0,toolCount=0,totalTokens=0,closing=false;
const started=Date.now(),MAX_REQUESTS=input.finalize_only?1:(input.assessment_contract?.max_requests||(input.evidence_packet?4:12)),MAX_TOOLS=input.assessment_contract?.max_tools||(input.evidence_packet?12:45),TOKEN_TARGET=input.baseline_usage.total_tokens;
const protocol={framework:'@earendil-works/pi-coding-agent',version:'1.5.2',
  mechanism:input.mechanism.id,commit:input.commit,provenance:input.provenance,requested_model:'x-test-2',
  max_requests:MAX_REQUESTS,max_tool_calls:MAX_TOOLS,token_target:TOKEN_TARGET,
  token_limit_note:'Observed usage target; reserve final turn based on prior usage. In-flight input may overshoot; actual usage reported.',
  max_output_tokens:outputTokens,wall_deadline_seconds:900,network_retries:0,
  baseline:'runs/sparta-k2-code-M02-v1',comparison:'Targeted development follow-up with revised verdict contract and added dependency; not a controlled accuracy comparison.',
  previous_findings_supplied:!!input.candidate_report,preselected_snippets_supplied:!!input.evidence_packet,revision_contract:input.revision_contract,scope_contract:conformance?'Paper claim conformance, not implementation completeness':'Local generic entry versus artifact configured dependency; explicit verdicts',assessment_contract:input.assessment_contract,dependency_provenance:input.dependency_provenance,repositories:Object.fromEntries(Object.entries(input.repositories).map(([id,r])=>[id,{commit:r.commit}])),target_execution:'not_run',independent_human_review:'pending'};
write('protocol.json',protocol);fs.copyFileSync(new URL(import.meta.url),path.join(runDir,'runner.snapshot.mjs'));fs.copyFileSync(new URL('./judgment.mjs',import.meta.url),path.join(runDir,'judgment.snapshot.mjs'));fs.copyFileSync(new URL('./prepare_judgment.py',import.meta.url),path.join(runDir,'prepare.snapshot.py'));
if(conformance){fs.copyFileSync(new URL('./conformance.mjs',import.meta.url),path.join(runDir,'conformance.snapshot.mjs'));fs.copyFileSync(input.preparation_source || new URL('./prepare_conformance.py',import.meta.url),path.join(runDir,'prepare.snapshot.py'));}
const repos=input.repositories;const pick=id=>{if(!Object.hasOwn(repos,id))throw new Error('Unknown repository alias');return repos[id];};
const repoField=()=>Type.Optional(Type.Union(Object.keys(repos).map(id=>Type.Literal(id))));
const reads=[...(input.seed_read_spans||[])];
function git(args,repo='primary'){return execFileSync('git',['-C',pick(repo).repo,...args],{encoding:'utf8',timeout:25000,maxBuffer:3000000});}
const budgetCheck=()=>{if(Date.now()-started>900000)throw new Error('Wall deadline reached');if(++toolCount>MAX_TOOLS)throw new Error('Tool budget reached: return final report');};
function wrapped(name,description,parameters,execute){return {name,label:name,description,parameters,execute:async(_id,args)=>{
  budgetCheck();const sequence=toolCount;const result=await execute(args);
  fs.appendFileSync(path.join(runDir,'tools.jsonl'),JSON.stringify({sequence,name,args,result:redacted(result)})+'\n');
  console.log('tool',sequence,name,JSON.stringify(args));
  return result.content ? result : {content:[{type:'text',text:JSON.stringify(result)}],details:{}};
}};}
const customTools=[
  wrapped('list_repo','List tracked paths at the pinned commit; use offset for pagination.',Type.Object({repo:repoField(),prefix:Type.Optional(Type.String()),offset:Type.Optional(Type.Integer({minimum:0}))}),({repo='primary',prefix='',offset=0})=>{
    const names=pick(repo).files.filter(f=>f.path.startsWith(prefix)).map(f=>f.path);
    const children=[...new Set(names.map(p=>p.slice(prefix.length).replace(/^\//,'').split('/')[0]))];
    return {total:names.length,children,paths:names.slice(offset,offset+40),next_offset:offset+40<names.length?offset+40:null};}),
  wrapped('search_repo','Search literal text in tracked repository files at commit. No regex/shell. Scope is an optional directory prefix. Results sample files across top-level directories; narrow scope to inspect more.',Type.Object({repo:repoField(),query:Type.String({minLength:2,maxLength:160}),scope:Type.Optional(Type.String())}),({repo='primary',query,scope=''})=>{
    if(scope.startsWith('/')||scope.includes('..')||scope.startsWith(':'))throw new Error('Invalid repository scope');
    let text='';try{text=git(['grep','-n','-I','-i','-F','-e',query,pick(repo).commit,'--',...(scope?[scope]:[])],repo);}catch(e){if(e.status!==1)throw new Error('Git search failed or exceeded size cap');}
    const rows=text.trim().split('\n').filter(Boolean), groups=new Map();
    for(const row of rows){const short=row.replace(pick(repo).commit+':','');const p=short.split(':')[0];if(!groups.has(p))groups.set(p,[]);groups.get(p).push(short);}
    const dirs=new Map();for(const [p,hits]of groups){const top=p.split('/')[0];if(!dirs.has(top))dirs.set(top,[]);dirs.get(top).push({path:p,hit_count:hits.length,hits:hits.slice(0,2).map(s=>s.slice(0,240))});}
    const sampled=[];for(let i=0;sampled.length<18;i++){let found=false;for(const group of dirs.values()){if(group[i]&&sampled.length<18){sampled.push(group[i]);found=true;}}if(!found)break;}
    return {total_hits:rows.length,total_files:groups.size,top_level_groups:[...dirs.keys()],sampled_files:sampled,truncated:groups.size>sampled.length,note:'Search hits are pointers, not full-body evidence. Read relevant files before conclusions.'};}),
  wrapped('read_repo','Read a tracked Git blob with line numbers. Up to 180 lines; no code execution.',Type.Object({repo:repoField(),path:Type.String(),start_line:Type.Optional(Type.Integer({minimum:1})),end_line:Type.Optional(Type.Integer({minimum:1}))}),({repo='primary',path:p,start_line=1,end_line=start_line+119})=>{
    const meta=pick(repo).files.find(f=>f.path===p);if(!meta||meta.kind!=='blob'||meta.size>700000)throw new Error('Not a readable bounded tracked file');
    const text=git(['show',`${pick(repo).commit}:${p}`],repo);if(text.includes('\0'))throw new Error('Binary file');
    const lines=text.split('\n');const end=Math.min(end_line,start_line+179,lines.length);
    if(start_line>end)throw new Error('Invalid line range');reads.push({repo,path:p,start_line,end_line:end});
    return {repo,path:p,commit:pick(repo).commit,sha:meta.sha,total_lines:lines.length,start_line,end_line:end,
      lines:lines.slice(start_line-1,end).map((s,i)=>`${start_line+i}: ${s}`).join('\n')};}),
  wrapped('symbol_context','Look up Python function definitions and incoming/outgoing statically resolved calls; these are not runtime traces.',Type.Object({repo:repoField(),symbol:Type.String({minLength:2})}),({repo='primary',symbol})=>{
    const source=pick(repo);
    const matches=Object.entries(source.definitions).filter(([,d])=>d.name.toLowerCase().includes(symbol.toLowerCase())).slice(0,16);
    return {python_parse_failures:source.index.skipped,matches:matches.map(([id,d])=>({id,...d,
      incoming:source.edges.filter(e=>e.callee===id).slice(0,15).map(e=>({...e,caller_name:source.definitions[e.caller].name})),
      outgoing:source.edges.filter(e=>e.caller===id).slice(0,20).map(e=>({...e,callee_name:source.definitions[e.callee].name}))}))};}),
  wrapped('read_paper','Read one physical PDF page as text and original image; original image resolves OCR errors.',Type.Object({page:Type.Integer({minimum:1,maximum:input.pages.length})}),({page})=>{
    const im=input.images.find(im=>im.page===page);const bytes=fs.readFileSync(im.path);
    if(hash(bytes)!==im.sha256)throw new Error('Paper image hash differs');
    return {content:[{type:'text',text:JSON.stringify(input.pages.find(p=>p.page===page))},{type:'image',data:bytes.toString('base64'),mimeType:im.mime_type}],details:{page}};})
];
const configDir=path.join(runDir,'agent-config');fs.mkdirSync(configDir);
write('system-prompt.json',{prompt:SYSTEM});
fs.writeFileSync(path.join(configDir,'models.json'),JSON.stringify({providers:{soclaas:{baseUrl:'https://soclaas-api.comp.nus.edu.sg/v1',api:'openai-completions',apiKey:'$SOCLAAS_API_KEY',
 compat:{supportsStore:false,supportsDeveloperRole:false,supportsReasoningEffort:false,maxTokensField:'max_tokens',supportsStrictMode:false},
 models:[{id:'x-test-2',name:'SoCLaaS DeepSeek route',input:['text','image'],reasoning:false,contextWindow:1048576,maxTokens:outputTokens,
 samplingParams:{temperature:0,reasoning_effort:'none'},cost:{input:0,output:0,cacheRead:0,cacheWrite:0}}]}}},null,2));
const runtime=await ModelRuntime.create({modelsPath:path.join(configDir,'models.json'),authPath:path.join(configDir,'auth.json'),allowModelNetwork:false});
const model=runtime.getModel('soclaas','x-test-2');if(!model)throw new Error('Custom model not loaded');
const loader={getExtensions:()=>({extensions:[],errors:[],runtime:createExtensionRuntime()}),getSkills:()=>({skills:[],diagnostics:[]}),
 getPrompts:()=>({prompts:[],diagnostics:[]}),getThemes:()=>({themes:[],diagnostics:[]}),getAgentsFiles:()=>({agentsFiles:[]}),
 getSystemPrompt:()=>SYSTEM,getSystemPromptSource:()=>undefined,getAppendSystemPrompt:()=>[],getAppendSystemPromptSources:()=>[],extendResources:()=>{},reload:async()=>{}};
const {session}=await createAgentSession({cwd:input.repo,agentDir:configDir,modelRuntime:runtime,model,thinkingLevel:'off',resourceLoader:loader,
 tools:customTools.map(t=>t.name),customTools,settingsManager:SettingsManager.inMemory({retry:{enabled:false,maxRetries:0},compaction:{enabled:false}}),
 sessionManager:SessionManager.inMemory(input.repo)});
session.agent.onPayload=(payload)=>{
 if(++requestCount>MAX_REQUESTS||Date.now()-started>900000)throw new Error('Agent request budget reached');
 payload.temperature=0;payload.max_tokens=outputTokens;payload.reasoning_effort='none';
 if(requestCount>=MAX_REQUESTS||requestCount>=11||totalTokens>=TOKEN_TARGET-35000){closing=true;payload.tool_choice='none';payload.messages.push({role:'user',content:input.review_behavior_ids?'Budget closing: return only the requested review IDs in the system schema. No tools.':`Budget closing: return final JSON covering ALL ${input.behaviors.length} supplied behavior IDs. Keep each explanation concise. No more tools. Record unfinished checks as pending work, not invented verdicts.`});}
 write(`request-${String(requestCount).padStart(2,'0')}.json`,redacted(payload));
 console.log('request',requestCount,'prior tokens',totalTokens,closing?'finalization requested':'');return payload;
};
session.subscribe(event=>{
 if(event.type==='message_end'){
  const m=event.message;if(m.role==='assistant'&&m.stopReason==='error')error=m.errorMessage||'Provider stream failed';fs.appendFileSync(path.join(runDir,'messages.jsonl'),JSON.stringify(redacted(m))+'\n');
  if(m.role==='assistant'){totalTokens+=m.usage?.totalTokens||0;console.log('assistant',m.stopReason,'tokens',m.usage?.totalTokens||0);}
 }
 if(['tool_execution_start','tool_execution_end','agent_end','agent_settled','auto_retry_start'].includes(event.type))
  fs.appendFileSync(path.join(runDir,'events.jsonl'),JSON.stringify(redacted(event))+'\n');
});
const userInput={mechanism:input.mechanism,behaviors:input.behaviors,paper_pages:input.pages.filter(p=>input.mechanism.pages.includes(p.page)),
 repositories:Object.fromEntries(Object.entries(input.repositories).map(([id,r])=>[id,{commit:r.commit}])),source_navigation:input.source_navigation,evidence_packet:input.evidence_packet,candidate_report:input.candidate_report,review_behavior_ids:input.review_behavior_ids,revision_contract:input.revision_contract,assessment_contract:input.assessment_contract,validation_feedback:input.validation_feedback,previous_incomplete_response:input.previous_incomplete_response,finalize_only:input.finalize_only,dependency_provenance:input.dependency_provenance,task:conformance?'Judge each original paper claim anew using only supports, deviates or absent for completed checks in both scoped paths; record uncompleted work as review_state=pending and verdict=null. Interpret the paper requirement, compare actual code, and distinguish mechanism mismatch from unproved effect failure. Do not rename any old implementation labels.':'Determine actual implemented and missing semantics at the local generic entry and artifact-configured dependency paths. Read build configuration and real code. If candidate_report is present, it is an unaccepted draft to revise, not ground truth.'};
write('initial-user-input.json',userInput);
const initialImages=input.images.filter(im=>input.mechanism.pages.includes(im.page)).map(im=>{
 const bytes=fs.readFileSync(im.path);if(hash(bytes)!==im.sha256)throw new Error('Initial image changed');
 return {type:'image',mimeType:im.mime_type,data:bytes.toString('base64')};
});
const timer=setTimeout(()=>session.abort(),900000);
let error;
try{await session.prompt(JSON.stringify(userInput),{images:initialImages,expandPromptTemplates:false});}
catch(e){error=String(e.message).replaceAll(process.env.SOCLAAS_API_KEY,'[REDACTED]');}
finally{clearTimeout(timer);}
const last=session.getLastAssistantText()||'';fs.writeFileSync(path.join(runDir,'final-response.txt'),last);
write('read-spans.json',reads);
let report;let validationError;
try{
 const trimmed=last.trim().replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'');report=JSON.parse(trimmed);
 if(conformance){write('conformance-report.raw.json',report);}
 else if(input.review_behavior_ids){
   write('equivalence-review.json',report);
   const ids=report.checks.map(c=>c.id);
   if(ids.length!==input.review_behavior_ids.length||new Set(ids).size!==ids.length||ids.some(id=>!input.review_behavior_ids.includes(id)))throw new Error('Invalid equivalence review coverage');
   const reviews=new Map(report.checks.map(c=>[c.id,c]));
   report=structuredClone(input.base_report);
   for(const c of report.checks)if(reviews.has(c.id)){const {id,...v}=reviews.get(c.id);c.artifact=v;c.artifact_review_run=path.basename(runDir);}
   report.revision_applied={source:'Pi model equivalence review',ids};
 }else if(input.compact_finalization){write('compact-report.json',report);report=expandCompactReport(report);}
 if(conformance)validateConformance(report,input.behaviors,reads,input.pages);
 else validateJudgment(report,input.behaviors,reads);
 write('report.json',{...report,semantic_review:'pending',target_execution:'not_run'});
}catch(e){validationError=e.message;}
const completedChecks=Array.isArray(report?.checks)?report.checks:[];
write('summary.json',{requests:requestCount,tool_calls:toolCount,total_tokens:totalTokens,elapsed_seconds:(Date.now()-started)/1000,
 token_target:TOKEN_TARGET,report_complete:!!report&&!validationError,assessment_complete:conformance?!!report&&!validationError&&completedChecks.every(c=>['local_entry','artifact'].every(scope=>c[scope]?.review_state==='completed')):undefined,error,validation_error:validationError,
 counts:Object.fromEntries(['local_entry','artifact'].map(scope=>[scope,Object.fromEntries((conformance?VERDICTS:['implemented','partially_implemented','not_implemented','not_assessable']).map(v=>[v,completedChecks.filter(c=>c[scope]?.verdict===v).length]))])),
 progress:conformance?Object.fromEntries(['local_entry','artifact'].map(scope=>[scope,{completed:completedChecks.filter(c=>c[scope]?.review_state==='completed').length,pending:completedChecks.filter(c=>c[scope]?.review_state==='pending').length}])):undefined,
 target_execution:'not_run',semantic_review:'pending'});
session.dispose();
console.log('finished',JSON.stringify({requestCount,toolCount,totalTokens,error,validationError}));
if(error||validationError)process.exitCode=1;
