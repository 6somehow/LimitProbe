/** Thin process/RPC entry. No benchmark policy or model transport here. */
import {createInterface} from 'node:readline';
import {loadPi} from './agent.mjs';
import {runSwarm} from './swarm.mjs';
const lines=createInterface({input:process.stdin});let serial=0;const pending=new Map(),eventPromises=[];
let deliverTaskUpdate;
lines.on('line',line=>{try{
 const r=JSON.parse(line);
 if(r.notification==='task_update'){
  if(!deliverTaskUpdate||Object.keys(r).sort().join(',')!=='notification,value'||!r.value||typeof r.value!=='object'||Array.isArray(r.value))throw Error('Unexpected task update');
  deliverTaskUpdate(r.value);return;
 }
 const p=pending.get(r.id);if(!p)throw Error('Unknown RPC id');pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));
}catch(e){process.stderr.write(String(e));process.exit(1);}});
lines.on('close',()=>{for(const p of pending.values())p.reject(Error('Host disconnected'));});
function rpc(op,data={}){const id=++serial;return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});process.stdout.write(JSON.stringify({id,op,data})+'\n');});}

try{
 const pi=await loadPi(process.argv[2]);
 const cfg=await rpc('init',{SDK:pi.packageName,version:pi.packageVersion});
 const result=await runSwarm(cfg,rpc,pi,handler=>{deliverTaskUpdate=handler;});await rpc('done',result);
 lines.close();process.stdin.destroy();
}catch(e){try{await rpc('failed',{error:String(e)});}catch{}process.stderr.write(String(e)+'\n');process.exitCode=1;lines.close();process.stdin.destroy();}
