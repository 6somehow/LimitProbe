import test from 'node:test';
import assert from 'node:assert/strict';
import {validateReport} from './validation.mjs';
const inputs=[{id:'M02-B01'}], reads=[{path:'a.py',start_line:5,end_line:20}];
const evidence=[{path:'a.py',start_line:6,end_line:12}];
const fixture=()=>({checks:[{id:'M02-B01',result:'partial',evidence}],paths:[],finding_clusters:[]});
test('accepts complete IDs and actually read ranges',()=>assert.equal(validateReport(fixture(),inputs,reads).checks.length,1));
test('rejects missing and duplicate IDs',()=>{
  const r=fixture();r.checks=[];assert.throws(()=>validateReport(r,inputs,reads),/behavior IDs/);
  r.checks=[...fixture().checks,...fixture().checks];assert.throws(()=>validateReport(r,inputs,reads),/behavior IDs/);
});
test('rejects citations seen only by search, including path and finding maps',()=>{
  for(const group of ['checks','paths','finding_clusters']){
    const r=fixture();r[group].push({id:'M02-B01',result:'partial',evidence:[{path:'unread.py',start_line:1,end_line:2}]});
    if(group==='checks')r.checks.shift();
    assert.throws(()=>validateReport(r,inputs,reads),/Unread citation/);
  }
});
test('rejects reversed or out-of-range lines and unknown labels',()=>{
  const r=fixture();r.checks[0].evidence=[{path:'a.py',start_line:18,end_line:25}];
  assert.throws(()=>validateReport(r,inputs,reads),/Unread citation/);
  r.checks[0].result='proved_bug';assert.throws(()=>validateReport(r,inputs,reads),/Invalid result/);
});
