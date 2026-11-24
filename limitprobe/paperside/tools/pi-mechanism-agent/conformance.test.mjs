import test from 'node:test';
import assert from 'node:assert/strict';
import {validateConformance,checkCitations} from './conformance.mjs';
const behaviors=[{id:'B1'}],pages=[{page:5}],reads=[{repo:'nni',path:'a.py',start_line:10,end_line:30}];
const scope=()=>({review_state:'completed',verdict:'deviates',actual:'one forward and backward pass',discrepancy:'paper requires change-driven repetition',equivalence:'equivalent fixed point has not been proved',effect_status:'not_established',pending_reason:'',refs:['E1']});
const fixture=()=>({code_evidence:[{id:'E1',repo:'nni',path:'a.py',start_line:12,end_line:20}],checks:[{id:'B1',claim_type:'mechanism_step',requirement:'repeat until no update',paper:{page:5,quote:'The propagation repeats until no TeSA requires further update.'},local_entry:scope(),artifact:scope()}],findings:[{title:'scheduling difference',scope:'artifact',behavior_ids:['B1'],refs:['E1'],boundary:'only the pinned entry',unverified_effect:'no wrong output demonstrated'}]});
const validate=r=>validateConformance(r,behaviors,reads,pages);
test('accepts procedural deviation without falsely requiring an observed wrong output',()=>validate(fixture()));
test('rejects old implementation-completeness labels',()=>{
 const r=fixture();r.checks[0].artifact.verdict='partially_implemented';assert.throws(()=>validate(r),/three conclusions/);
});
test('negative verdict must identify a discrepancy, not hide uncertainty',()=>{
 let r=fixture();r.checks[0].artifact.discrepancy='';assert.throws(()=>validate(r),/definite discrepancy/);
 r=fixture();r.checks[0].artifact.pending_reason='unknown dependency';assert.throws(()=>validate(r),/definite discrepancy/);
});
test('uncertain row cannot be counted as a finding',()=>{
 const r=fixture();Object.assign(r.checks[0].artifact,{review_state:'pending',verdict:null,pending_reason:'theorem not assessed',discrepancy:''});
 assert.throws(()=>validate(r),/non-negative/);r.findings=[];validate(r);
});
test('support cannot contain an admitted discrepancy',()=>{
 const r=fixture();r.checks[0].artifact.verdict='supports';assert.throws(()=>validate(r),/Support contradicts/);
});
test('rejects fabricated IDs, paper pages and unknown source references',()=>{
 let r=fixture();r.checks[0].id='invented';assert.throws(()=>validate(r),/ID coverage/);
 r=fixture();r.checks[0].paper.page=100;assert.throws(()=>validate(r),/paper evidence/);
 r=fixture();r.checks[0].artifact.refs=['E99'];assert.throws(()=>validate(r),/Unknown evidence/);
});
test('citations retain repository identity and cannot bridge unread gaps',()=>{
 assert.throws(()=>checkCitations([{repo:'primary',path:'a.py',start_line:12,end_line:14}],reads),/Unread citation/);
 assert.throws(()=>checkCitations([{repo:'nni',path:'a.py',start_line:20,end_line:35}],reads),/Unread citation/);
});
test('unassessed theorem may have no equivalence analysis, with an explicit barrier',()=>{
 const r=fixture();r.findings=[];
 r.checks[0].claim_type='guarantee';
 for(const scope of ['local_entry','artifact'])Object.assign(r.checks[0][scope],{review_state:'pending',verdict:null,equivalence:'',discrepancy:'',pending_reason:'the mathematical guarantee is not verified',effect_status:'not_established'});
 validate(r);
});

test('pending is not a fourth conclusion and cannot be given a verdict',()=>{
 const r=fixture();r.findings=[];Object.assign(r.checks[0].artifact,{review_state:'pending',verdict:'absent',pending_reason:'not checked'});
 assert.throws(()=>validate(r),/Pending review cannot have a verdict/);
});
test('legacy insufficient is rejected as a completed conclusion',()=>{
 const r=fixture();r.checks[0].artifact.verdict='insufficient';assert.throws(()=>validate(r),/three conclusions/);
});

test('native dependency aliases can be decisive only with their actual read ranges',()=>{
 const r=fixture();r.code_evidence[0]={id:'E1',repo:'nnfusion',path:'src/pass.cpp',start_line:12,end_line:20};
 assert.throws(()=>validateConformance(r,behaviors,reads,pages),/Unread citation/);
 validateConformance(r,behaviors,[{repo:'nnfusion',path:'src/pass.cpp',start_line:10,end_line:30}],pages);
});
