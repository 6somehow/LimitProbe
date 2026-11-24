import test from 'node:test';
import assert from 'node:assert/strict';
import {validateJudgment} from './judgment.mjs';
const behaviors=[{id:'B1'}];
const reads=[{repo:'primary',path:'a.py',start_line:1,end_line:10},{repo:'nni',path:'a.py',start_line:40,end_line:60}];
const positive=()=>({verdict:'implemented',implemented_parts:['reads attributes'],missing_parts:[],rationale:'body performs read',entry_scope:'function f',counterevidence:'none',evidence:[{repo:'primary',path:'a.py',start_line:2,end_line:4}]});
const fixture=()=>({checks:[{id:'B1',local_entry:positive(),artifact:positive()}],paths:[],finding_clusters:[]});
test('accepts explicit scoped evidence',()=>assert.equal(validateJudgment(fixture(),behaviors,reads).checks.length,1));
test('rejects vague labels and negatives with no explicit missing action',()=>{
 let r=fixture();r.checks[0].artifact.verdict='unlocated';assert.throws(()=>validateJudgment(r,behaviors,reads),/explicit verdict/);
 r=fixture();r.checks[0].artifact.verdict='not_implemented';assert.throws(()=>validateJudgment(r,behaviors,reads),/missing action/);
});
test('does not confuse identical paths in different repositories',()=>{
 const r=fixture();r.checks[0].artifact.evidence[0].repo='nni';assert.throws(()=>validateJudgment(r,behaviors,reads),/Unread citation/);
});
test('rejects unsupported decisive claim and contradictory present/missing fields',()=>{
 let r=fixture();r.checks[0].artifact.evidence=[];assert.throws(()=>validateJudgment(r,behaviors,reads),/read code evidence/);
 r=fixture();r.checks[0].artifact.missing_parts=['no loop'];assert.throws(()=>validateJudgment(r,behaviors,reads),/contradicts/);
});
test('permits explicit static barrier, and checks ID coverage',()=>{
 const r=fixture();r.checks[0].artifact={...positive(),verdict:'not_assessable',evidence:[],implemented_parts:[],rationale:'mathematical termination argument cannot be decided by present static method'};
 validateJudgment(r,behaviors,reads);r.checks.push(r.checks[0]);assert.throws(()=>validateJudgment(r,behaviors,reads),/ID coverage/);
});
test('artifact-wide decisive output requires reading dependency',()=>{
 assert.throws(()=>validateJudgment(fixture(),behaviors,reads.filter(r=>r.repo==='primary')),/dependency source bodies/);
});
test('allows adjacent actual reads, rejects unobserved gaps',()=>{
 const r=fixture();r.checks[0].artifact.evidence=[{repo:'nni',path:'a.py',start_line:45,end_line:65}];
 validateJudgment(r,behaviors,[...reads,{repo:'nni',path:'a.py',start_line:61,end_line:70}]);
 assert.throws(()=>validateJudgment(r,behaviors,[...reads,{repo:'nni',path:'a.py',start_line:62,end_line:70}]),/Unread citation/);
});
test('compact transport expands only references; never invents citation ranges',async()=>{
 const {expandCompactReport}=await import('./judgment.mjs');
 const v={verdict:'implemented',have:'read',lack:'',why:'body',counter:'none',refs:['E1']};
 const raw={mechanism_summary:'x',scope_definition:{local_entry:'f',artifact:'g'},code_evidence:[{id:'E1',repo:'primary',path:'a.py',start_line:2,end_line:4}],checks:[{id:'B1',local_entry:v,artifact:v}],findings:[],search_limits:[],open_questions:[]};
 validateJudgment(expandCompactReport(raw),behaviors,reads);
 raw.checks[0].artifact={...v,refs:['invented']};assert.throws(()=>expandCompactReport(raw),/Unknown evidence ID/);
});
