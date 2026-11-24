/** Tree lifecycle and same-reply fork/join; no task-specific search or scoring. */
import {join} from 'node:path';
import {mkdir} from 'node:fs/promises';
import {forkForWorker} from './fork.mjs';
import {hostContext,response,createPiSession} from './agent.mjs';
import {neighbour,readSession,resourceView} from './coordination.mjs';
export async function runSwarm(cfg,rpc,pi,subscribeTaskUpdates){
 const {ModelRuntime,createAssistantMessageEventStream}=pi;
 const agents=new Map(),backgroundJobs=new Map(),completedReports=[],eventPromises=[];let active=0,total=0,aborting=false,reservations=0;
 function emit(kind,data){const p=rpc('event',{kind,...data,observed_epoch:Date.now()/1000,observed_monotonic_ms:performance.now()});eventPromises.push(p);return p;}
 async function abortAll(){
  aborting=true;
  for(const agent of agents.values())for(const wake of agent.waiters)wake();
  await Promise.allSettled([...agents.values()].map(a=>a.session?.abort()));
 }
 const interrupt=()=>{void abortAll();};process.on('SIGTERM',interrupt);
 for(const n of ['maxActive','maxDepth',...('maxTurns' in cfg.limits?['maxTotal','maxChildren','maxTurns']:[])])if(!Number.isInteger(cfg.limits[n])||cfg.limits[n]<(n==='maxDepth'?0:1))throw Error('Explicit finite limits');
 if(cfg.turnPrompts!==undefined){
  if(typeof cfg.reportHeader!=='string'||!cfg.reportHeader.includes('{child}')||!cfg.reportHeader.includes('{finish_reason}'))throw Error('Explicit worker status header required');
  if(!cfg.turnPrompts||Object.keys(cfg.turnPrompts).sort().join(',')!=='root,worker')throw Error('Explicit root/worker turn prompts required');
  for(const role of Object.values(cfg.turnPrompts))if(!role||Object.keys(role).sort().join(',')!=='last,remaining'||Object.values(role).some(v=>typeof v!=='string'||!v))throw Error('Explicit complete role turn prompts required');
 }
 const {maxTotal=Infinity,maxChildren=Infinity,workerContext='inherit'}=cfg.limits;
 if(!['inherit','independent'].includes(workerContext))throw Error('Unknown worker context policy');
 const background=cfg.limits.spawnMode==='background';
 const waitForReport=cfg.limits.waitForReport===true;
 const progressMessages=cfg.limits.progressMessages===true;
 const taskUpdates=[];
 if(cfg.taskUpdates===true){
  if(!progressMessages||!subscribeTaskUpdates)throw Error('Task updates require root progress waiting');
  subscribeTaskUpdates(value=>{
   taskUpdates.push(value);
   for(const wake of agents.get('root')?.waiters??[])wake();
  });
 }
 const coordination=cfg.limits.coordination===true;
 if('resourceObservations' in cfg.limits&&cfg.limits.resourceObservations!==true)throw Error('Explicit resourceObservations=true required');
 const resourceObservations=coordination||cfg.limits.resourceObservations===true;
 const followups=cfg.limits.followupTasks===true;
 if(followups&&(!coordination||!background||cfg.limits.maxTurns!==undefined))throw Error('Follow-up tasks require Cut-only background coordination');
 if('teamAdaptation' in cfg.limits)throw Error('Removed teamAdaptation configuration: replay historical runs with their frozen source');
 if(coordination&&(!background||!progressMessages))throw Error('Coordination requires background messages');
 if(background&&cfg.limits.maxDepth!==1)throw Error('Background spawning requires depth one');
 const roleTurns=cfg.limits.turnsByRole;
 if(roleTurns!==undefined&&(!roleTurns||Object.keys(roleTurns).sort().join(',')!=='root,worker'||Object.values(roleTurns).some(v=>!Number.isInteger(v)||v<1||v>cfg.limits.maxTurns)))throw Error('Explicit root/worker turn budgets within global safety required');
 await mkdir(cfg.agentDir,{recursive:true});
 const modelRuntime=await ModelRuntime.create({authPath:join(cfg.agentDir,'auth.json'),modelsPath:null,allowModelNetwork:false,refreshOnCreate:false});
 modelRuntime.registerProvider('swarm-native',{api:'openai-completions',baseUrl:cfg.endpoint,apiKey:'loopback-adapter-no-auth',authHeader:false,models:[{id:cfg.modelId,name:cfg.modelName,reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:cfg.contextLimit,maxTokens:cfg.maxOutputTokens}]});
 const model=modelRuntime.getModel('swarm-native',cfg.modelId);if(!model)throw Error('Explicit host model descriptor missing');
 function track(child,pending){
  const job={result:null};backgroundJobs.set(child,job);
  const settle=result=>{job.result=result;job.report=completedReports.findLast(r=>r.child===child);const parent=agents.get(agents.get(child).parent);for(const wake of parent?.waiters??[])wake();};
  job.settled=pending.then(answer=>settle({answer}),error=>settle({error:String(error)}));
 }
 async function runAgent(id,parent,depth,task,inherited=[]){
  if(aborting)throw Error('Job cancelled');
  if(active>=cfg.limits.maxActive||total>=maxTotal)throw Error('Safety capacity exceeded');
  active++;total++;const a={id,parent,depth,task,round:0,children:0,turn:0,turnLimit:roleTurns?.[parent?'worker':'root']??cfg.limits.maxTurns,session:null,status:'starting',mailbox:[],toolReceipts:[],transcript:[],modelStarted:null,waiters:new Set()};agents.set(id,a);
  await emit('agent_started',{agent:id,parent,depth,active,total,task,turn_limit:a.turnLimit});
  const customTools=cfg.tools.map(t=>({...t,label:t.name,execute:async(callId,args)=>{
   await emit('tool_started',{agent:id,callId,name:t.name,args});
   const result=await rpc('tool',{agent:id,callId,name:t.name,args});
   if(progressMessages&&parent)a.toolReceipts.push({callId,name:t.name,args,result});
   await emit('tool_finished',{agent:id,callId,name:t.name,result});
   return {content:[{type:'text',text:result}],details:{source:'host-original-tool'}};
  }}));
  if(progressMessages&&(parent||coordination))customTools.push({
   name:'msg',label:'msg',
   description:coordination?'Send a directed message to your direct parent or child using to. Ask a question, redirect work, or share a source/candidate reference and what it supports. Delivery wakes a waiting recipient; an in-flight model call is not interrupted. Children may omit to for their parent.':'Send a useful intermediate finding to your direct parent. Include the source or candidate reference and what it supports. You can keep working after sending.',
   parameters:{type:'object',properties:{text:{type:'string'},...(coordination?{to:{type:'string'}}:{})},required:['text'],additionalProperties:false},
   execute:async(callId,{text,to})=>{
    if(typeof text!=='string'||!text.trim())throw Error('A nonempty message is required');
    const recipient=coordination?neighbour(agents,id,to??parent):agents.get(parent);
    if(aborting||recipient.status!=='running')throw Error('Recipient is no longer receiving messages');
    const mail={agent:id,recipient:recipient.id,callId,text};
    const recorded=emit('progress_message_sent',mail);
    recipient.mailbox.push(mail);
    for(const wake of recipient.waiters)wake();
    await recorded;
    return {content:[{type:'text',text:'Queued for '+recipient.id+' at its next model decision; wakes a waiting recipient.'}]};
   }
  });
  if(coordination)customTools.push({
   name:'read_session',label:'read_session',
   description:'Read the complete Pi-visible session of a direct child or parent, including completed tool results. Default returns all messages; tail selects the latest N complete messages (cannot combine with cursor/count). Optional cursor/count explicitly paginate without truncating message content. Raw provider reasoning remains in the original trace.',
   parameters:{type:'object',properties:{agent:{type:'string'},cursor:{type:'integer'},count:{type:'integer'},tail:{type:'integer'}},required:['agent'],additionalProperties:false},
   execute:async(callId,args)=>{
    const value=readSession(agents,id,args);
    await emit('session_read',{agent:id,callId,args,value});
    return {content:[{type:'text',text:JSON.stringify(value)}]};
   }
  });
  if(followups&&!parent)customTools.push({name:'followup_task',label:'followup_task',
   description:'Give an existing direct child additional work. If it is running, queue the task for its next safe decision. If it completed successfully, start another work round in the SAME session with all prior messages and original receipts retained. Does not interrupt an in-flight model call, create a new agent, reset the overall Cut, or retry a failed/cancelled child.',
   parameters:{type:'object',properties:{target:{type:'string'},message:{type:'string'}},required:['target','message'],additionalProperties:false},
   execute:async(callId,args)=>{
    const {target,message}=args,child=agents.get(target);
    if(!child||child.parent!==id)throw Error('Follow-up target must be your existing direct child');
    if(typeof message!=='string'||!message.trim())throw Error('Nonempty follow-up task required');
    if(aborting||Date.now()/1000>=cfg.deadlineEpoch)throw Error('Overall Cut reached or run cancelled');
    if(!['starting','running','completed'].includes(child.status))throw Error('Failed or cancelled child cannot be resumed');
    const mode=child.status==='completed'?'resumed':'queued';
    if(mode==='resumed'&&active+reservations>=cfg.limits.maxActive)throw Error('Active safety capacity reached; child not resumed');
    const round=child.round+(mode==='resumed'?1:0);
    if(mode==='resumed'){child.round=round;child.status='running';active++;}
    await emit('followup_requested',{agent:id,callId,args,target,mode,round});
    if(mode==='queued'){
     child.mailbox.push({agent:id,recipient:target,callId,text:message,followup:true});
     for(const wake of child.waiters)wake();
    }else{
     // Reserve synchronously before awaiting session startup; concurrent followups see running.
     track(target,child.executePrompt('Follow-up task from '+id+':\n'+message,{resumed:true,request:{agent:id,callId,text:message}}));
    }
    return {content:[{type:'text',text:JSON.stringify({target,mode,round,history:'same original session',overall_cut:'unchanged'})}]};
   }
  });
  if(progressMessages&&!parent)customTools.push({
   name:'wait_for_update',label:'wait_for_update',
   description:'Wait for any direct child to send a progress message or reach a terminal state.'+(cfg.taskUpdates===true?' An observed task update also wakes you.':'')+' Returns immediately if no children are active. Progress text arrives in your next model input.',
   parameters:{type:'object',properties:{},additionalProperties:false},
   execute:async(callId,_,signal)=>{
    const snapshot=()=>{
     const messages=[...new Set(a.mailbox.map(mail=>mail.agent))];
     const terminal=[...backgroundJobs].filter(([,job])=>job.result&&!job.statusSeen);
     return {messages,terminal,active:reservations>0||[...backgroundJobs.values()].some(job=>!job.result)};
    };
    await emit('update_wait_started',{agent:id,callId});
    await new Promise((resolve,reject)=>{
     const cleanup=()=>{a.waiters.delete(wake);signal?.removeEventListener('abort',cancel);};
     const cancel=()=>{cleanup();reject(Error('Update wait cancelled'));};
     const wake=()=>{
      if(signal?.aborted||aborting){cancel();return;}
      const {messages,terminal,active}=snapshot();
      if(messages.length||terminal.length||taskUpdates.length||!active){cleanup();resolve();}
     };
     a.waiters.add(wake);
     signal?.addEventListener('abort',cancel,{once:true});
     wake();
    });
    const {messages,terminal,active}=snapshot();
    const children=terminal.map(([child,job])=>{
     job.statusSeen=true;
     return {child,status:job.result.error?'failed':'completed',...(job.result.error?{error:job.result.error}:{})};
    });
    const update={message_from:messages,terminal:children,active_children:active};
    if(cfg.taskUpdates===true)update.task_updates=taskUpdates.splice(0);
    await emit('update_wait_returned',{agent:id,callId,update});
    return {content:[{type:'text',text:JSON.stringify(update)}]};
   }
  },{
   name:'inspect_child',label:'inspect_child',
   description:'Inspect a direct child’s assignment, status and list of completed task tool calls. Pass call_id to read one original tool receipt in full.',
   parameters:{type:'object',properties:{child:{type:'string'},call_id:{type:'string'}},required:['child'],additionalProperties:false},
   execute:async(callId,{child,call_id})=>{
    const target=agents.get(child);
    if(!target||target.parent!==id)throw Error('Unknown direct child');
    const value={child,status:target.status,task:target.task};
    if(call_id!==undefined){
     value.receipt=target.toolReceipts.find(receipt=>receipt.callId===call_id);
     if(!value.receipt)throw Error('No completed tool call with that ID');
    }else{
     value.calls=target.toolReceipts.map(({callId,name})=>({call_id:callId,name}));
    }
    await emit('child_inspected',{agent:id,callId,child,requested_call_id:call_id,value});
    return {content:[{type:'text',text:JSON.stringify(value)}]};
   }
  });
  async function deliver(child,callId,answer,report){
   const finish_reason=report?.finish_reason??agents.get(child).finishReason;
   const header=cfg.reportHeader?.replaceAll('{child}',child).replaceAll('{finish_reason}',finish_reason)??'';
   const delivery_text=(followups?'[Work round '+(report?.round??agents.get(child).round)+']\n':'')+header+answer;
   await emit('child_joined',{agent:id,child,callId,finish_reason,delivery_text,...(followups?{round:report?.round??agents.get(child).round}:{})});
   return {content:[{type:'text',text:delivery_text}],details:{child,finish_reason}};
  }
  if(background&&depth===0)customTools.push({
   name:'collect',label:'collect',
   description:waitForReport?'Get the report for a direct child returned by spawn. Set wait=true to wait for this child to complete or fail. Otherwise return immediately if pending.':'Get the completed report for a direct child returned by spawn. Returns immediately with pending if still running.',
   parameters:{type:'object',properties:{child:{type:'string'},...(waitForReport?{wait:{type:'boolean'}}:{})},required:['child'],additionalProperties:false},
   execute:async(callId,{child,wait},signal)=>{
    const job=backgroundJobs.get(child);
    if(!job)throw Error('Unknown direct child');
    if(waitForReport&&wait===true&&!job.result){
     await emit('child_wait_started',{agent:id,child,callId});
     await new Promise((resolve,reject)=>{
      const cancel=()=>reject(Error('Report wait cancelled'));
      if(signal?.aborted){cancel();return;}
      signal?.addEventListener('abort',cancel,{once:true});
      void job.settled.then(()=>{signal?.removeEventListener('abort',cancel);resolve();});
     });
    }
    if(!job.result)return {content:[{type:'text',text:'Child '+child+' is still pending.'}]};
    if(job.result.error)throw Error(job.result.error);
    job.delivered=true;if(job.report)job.report.delivered=true;
    return deliver(child,callId,job.result.answer,job.report);
   }
  });
  if(depth<cfg.limits.maxDepth)customTools.push({name:'spawn',label:'spawn',description:cfg.spawnDescription,parameters:cfg.spawnSchema,execute:async(callId,args)=>{
   if(active+reservations>=cfg.limits.maxActive||total+reservations>=maxTotal||a.children>=maxChildren){await emit('spawn_refused',{agent:id,callId,active,total});return {content:[{type:'text',text:'refused: configured agent/width capacity reached'}],details:{refused:true}};}
   const blind=args.review_docids!==undefined;
   if (cfg.blindReviewPrompt && (blind ? args.task!==undefined || !Array.isArray(args.review_docids)
     || args.review_docids.length<1 || (a.turnLimit!==undefined&&args.review_docids.length>4)
     || args.review_docids.some(id=>typeof id!=='string'||!/^\d{1,7}$/.test(id))
     : typeof args.task!=='string'||!args.task.trim())) {
    return {content:[{type:'text',text:'Provide either task or numeric review_docids.'}],details:{refused:true}};
   }
   const review=Boolean(cfg.blindReviewPrompt && blind);
   const independent=workerContext==='independent';
   let childTask=review?cfg.task+'\n\n'+cfg.blindReviewPrompt+'\nDocument IDs: '+args.review_docids.join(', '):
    independent?cfg.task+'\n\nAssigned route: '+args.task:args.task;
   let child,snapshot;reservations++;
   try{
   if(coordination&&independent&&!review){
    const context={parent_artifacts:await rpc('state',{agent:id,turn:a.turn}),note:'Current parent-visible original artifact index; further context is chosen by the parent. Read original sources/programs; references do not certify interpretations.'};
    childTask+='\n\nCurrent handoff snapshot:\n'+JSON.stringify(context);
    await emit('delegation_context',{agent:id,callId,turn:a.turn,context});
   }
   child=id+'.'+(++a.children);snapshot=review||independent?[]:forkForWorker(a.session.messages);
   await emit('child_spawned',{agent:id,child,callId,task:childTask,fork_messages:snapshot,...(review?{blind_review:true}:{})});
   }finally{reservations--;}
   const pending=runAgent(child,id,depth+1,childTask,snapshot);
   if(!background)return deliver(child,callId,await pending);
   track(child,pending);
   return {content:[{type:'text',text:'Started child '+child+'. Use collect with this ID to get its completed report.'}],details:{child}};
  }});
  if(coordination)for(const tool of customTools){
   const execute=tool.execute;
   tool.execute=async(callId,args,...rest)=>{
    const result=await execute(callId,args,...rest);
    const content=result.content.map(c=>{if(c.type!=='text')throw Error('Text session tool required');return c.text;}).join('');
    const message={role:'tool',tool_call_id:callId,content};
    a.transcript.push(message);
    await emit('session_tool_observed',{agent:id,callId,name:tool.name,args,message});
    return result;
   };
  }
  async function observeResources(){
   const taskState=await rpc('state',{agent:id,turn:a.turn});
   const snapshot=resourceView(agents,cfg.deadlineEpoch,Date.now()/1000,taskState);
   const delivery_text='Current run resources and available artifacts (observations, not instructions):\n'+JSON.stringify(snapshot);
   await emit('resource_snapshot',{agent:id,turn:a.turn,snapshot,delivery_text});
   return delivery_text;
  }
  try{
   const {session}=await createPiSession({cfg,pi,modelRuntime,model,inherited,customTools});
   a.session=session;a.status='running';session.agent.toolExecution='parallel';
   if(resourceObservations)await emit('agent_ready',{agent:id});
   if(JSON.stringify(session.getActiveToolNames().sort())!==JSON.stringify(customTools.map(t=>t.name).sort()))throw Error('Unexpected active tools');
   session.subscribe(e=>{eventPromises.push(rpc('sdk_event',{agent:id,event:e,observed_epoch:Date.now()/1000}));});
   if(a.turnLimit===1)session.setActiveToolsByName([]);
   const previous=session.agent.prepareNextTurnWithContext;
   session.agent.prepareNextTurnWithContext=async(context,signal)=>{
    const last=a.turnLimit!==undefined&&a.turn===a.turnLimit-1;
    // Reflect permanent safety exhaustion before the SDK refreshes the next model context.
    const unavailable=total+reservations>=maxTotal||a.children>=maxChildren;
    session.setActiveToolsByName(last?[]:customTools.filter(t=>t.name!=='spawn'||!unavailable).map(t=>t.name));
    let update=await previous?.(context,signal);
    if(a.mailbox.length){
     const messages=[];
     for(const mail of a.mailbox.splice(0)){
      const delivery_text=(mail.followup?'Follow-up task from ':'Progress message from ')+mail.agent+':\n'+mail.text;
      await emit(mail.followup?'followup_delivered':'progress_message_delivered',{...mail,turn:a.turn,delivery_text});
      messages.push({role:'user',content:delivery_text,timestamp:Date.now()});
     }
     update={...update,messages:[...(update?.messages??[]),...messages]};
    }
    if(depth===0&&cfg.limits.deliverCompletedReports){
     const notices=[];
     for(const report of completedReports){
      if(report.delivered)continue;
      report.delivered=true;
      const {child,finish_reason,answer,round}=report;
      const delivery_text='Completed report from '+child+(followups?' (work round '+round+', finish reason: ':' (finish reason: ')+finish_reason+'). Original report follows:\n'+answer;
      await emit('child_report_notice',{agent:id,child,finish_reason,delivery_text,...(followups?{round}:{})});
      notices.push({role:'user',content:delivery_text,timestamp:Date.now()});
     }
     if(notices.length)update={...update,messages:[...(update?.messages??[]),...notices]};
    }
    if(resourceObservations){
     const delivery_text=await observeResources();
     update={...update,messages:[...(update?.messages??[]),{role:'user',content:delivery_text,timestamp:Date.now()}]};
    }
    if(a.turnLimit===undefined||a.turn>=a.turnLimit)return update;
    const turns=cfg.turnPrompts?.[parent?'worker':'root'];
    const template=turns?(last?turns.last:turns.remaining):(last?cfg.lastTurnPrompt:cfg.remainingPrompt);
    const hint=template.replaceAll('{n}',String(a.turnLimit-a.turn));
    return {...update,messages:[...(update?.messages??[]),{role:'user',content:hint,timestamp:Date.now()}]};
   };
   session.agent.streamFunction=async(_,context)=>{
    const stream=createAssistantMessageEventStream();
    try{
     if(aborting||Date.now()/1000>=cfg.deadlineEpoch)throw Error('Condition deadline reached');
     if(a.turnLimit!==undefined&&a.turn>=a.turnLimit)throw Error('Agent turn limit exceeded without final');
     const request=hostContext(context),turn=a.turn++;
     if(resourceObservations){a.transcript=JSON.parse(JSON.stringify(request.messages));a.modelStarted=Date.now()/1000;}
     await emit('model_requested',{agent:id,parent,turn,pi_context:context,...request,...(resourceObservations?{model_started_epoch:a.modelStarted}:{})});
     const reply=await rpc('model',{agent:id,parent,turn,...request});
     if(resourceObservations){a.modelStarted=null;a.transcript.push(JSON.parse(JSON.stringify(reply.assistant_message)));}
     await emit('model_returned',{agent:id,turn,reply});
     const m=response(reply,model);stream.push({type:'done',reason:m.stopReason,message:m});
    }catch(e){const m={role:'assistant',content:[],api:model.api,provider:model.provider,model:model.id,stopReason:'error',errorMessage:String(e),timestamp:Date.now()};stream.push({type:'error',reason:'error',error:m});}
    return stream;
   };
   const rights=depth<cfg.limits.maxDepth?cfg.leadPrompt.replaceAll('{n}',String(cfg.limits.maxChildren??cfg.limits.maxActive)).replaceAll('{turns}',a.turnLimit===undefined?'':String(a.turnLimit)):cfg.workerPrompt.replaceAll('{turns}',a.turnLimit===undefined?'':String(a.turnLimit));
   const initialFinal=a.turnLimit===1?(cfg.turnPrompts?.[parent?'worker':'root']?.last??cfg.lastTurnPrompt):'';
   const initialResources=resourceObservations?'\n\n'+await observeResources():'';
   a.executePrompt=async(prompt,{resumed=false,request}={})=>{
    try{
     if(resumed){
      await emit('agent_resumed',{agent:id,parent,round:a.round,callId:request.callId,requested_by:request.agent});
      const delivery_text=prompt+'\n\n'+await observeResources();
      await emit('followup_delivered',{agent:request.agent,recipient:id,callId:request.callId,text:request.text,turn:a.turn,delivery_text});
      prompt=delivery_text;
     }
     while(true){
      await session.prompt(prompt);
      if(session.agent.state.errorMessage||aborting)throw Error(session.agent.state.errorMessage??'Job cancelled');
      const messages=session.messages,last=messages.at(-1);
      if(last?.role!=='assistant'||last.content.some(c=>c.type==='toolCall'))throw Error('No terminal assistant answer');
      const answer=last.content.filter(c=>c.type==='text').map(c=>c.text).join('');if(!answer.trim())throw Error('Empty final answer');
      a.status='completed';a.finishReason=last.stopReason;
      await emit('agent_finished',{agent:id,parent,answer,finish_reason:a.finishReason,model_replies:a.turn,turn_limit:a.turnLimit,messages,...(followups?{round:a.round}:{})});
      if(parent&&background)completedReports.push({child:id,answer,finish_reason:a.finishReason,round:a.round,delivered:false});
      // A follow-up may arrive during the final in-flight response. Preserve that final,
      // then continue queued work; never silently drop it just because the SDK stopped.
      if(followups&&parent&&a.mailbox.some(mail=>mail.followup)){
       a.status='running';a.round++;
       await emit('agent_resumed',{agent:id,parent,round:a.round,queued:true});
       const updates=a.mailbox.splice(0),parts=[];
       for(const mail of updates){
        const delivery_text=(mail.followup?'Follow-up task from ':'Progress message from ')+mail.agent+':\n'+mail.text;
        await emit(mail.followup?'followup_delivered':'progress_message_delivered',{...mail,turn:a.turn,delivery_text});parts.push(delivery_text);
       }
       prompt=parts.join('\n\n')+'\n\n'+await observeResources();continue;
      }
      return answer;
     }
    }catch(e){a.status='failed';await emit('agent_failed',{agent:id,parent,error:String(e)});throw e;}
    finally{active--;await emit('agent_released',{agent:id,active,total});}
   };
   a.promptStarted=true;
   return await a.executePrompt((parent?'Worker sub-task: ':'Task: ')+task+'\n\n'+rights+(initialFinal?'\n'+initialFinal:'')+initialResources);
  }catch(e){
   if(!a.promptStarted){a.status='failed';active--;await emit('agent_failed',{agent:id,parent,error:String(e)});await emit('agent_released',{agent:id,active,total});}
   throw e;
  }

 }

 const timer=setTimeout(()=>{void abortAll();},Math.max(1,cfg.deadlineEpoch*1000-Date.now()));
 try{
  let answer;
  try{answer=await runAgent('root',null,0,cfg.task);}
  finally{
   if(background&&active){
    aborting=true;
    await rpc('cancel_workers');
    await Promise.all([...backgroundJobs.values()].map(job=>job.settled));
   }
  }
  await Promise.all(eventPromises);
  return {answer,agents:total,active};
 }
 finally{clearTimeout(timer);process.off('SIGTERM',interrupt);if(active)await abortAll();for(const a of agents.values())a.session?.dispose();}
}
