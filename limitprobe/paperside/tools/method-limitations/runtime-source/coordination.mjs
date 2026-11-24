/** Read-only views and direct-neighbour messaging, independent of task and model. */
const copy=value=>JSON.parse(JSON.stringify(value));

export function neighbour(agents,from,to){
 const sender=agents.get(from),target=agents.get(to);
 if(!sender||!target||!(sender.parent===to||target.parent===from))throw Error('Recipient must be your direct parent or child');
 return target;
}

export function readSession(agents,from,{agent,cursor=0,count,tail}){
 const target=neighbour(agents,from,agent);
 if(tail!==undefined){if(!Number.isInteger(tail)||tail<1||cursor!==0||count!==undefined)throw Error('Tail requires a positive count without cursor/count');cursor=Math.max(0,(target.transcript??[]).length-tail);}
 if(!Number.isInteger(cursor)||cursor<0||(count!==undefined&&(!Number.isInteger(count)||count<1)))throw Error('Explicit nonnegative cursor and positive count required');
 const messages=copy(target.transcript??[]);
 if(cursor>messages.length)throw Error('Cursor exceeds current session length');
 const end=count===undefined?messages.length:Math.min(messages.length,cursor+count);
 return {agent,status:target.status,task:target.task,
  view:'complete Pi-visible input plus observed output/tool completions; provider raw reasoning stays in original trace',
  cursor,total:messages.length,next_cursor:end<messages.length?end:null,messages:messages.slice(cursor,end)};
}

export function resourceView(agents,deadlineEpoch,now,taskState){
 return {observed_epoch:now,overall_cut_remaining_s:Math.max(0,deadlineEpoch-now),
  agents:[...agents.values()].map(a=>({agent:a.id,parent:a.parent,status:a.status,
   model_request_started_epoch:a.modelStarted??null})),task_state:taskState};
}
