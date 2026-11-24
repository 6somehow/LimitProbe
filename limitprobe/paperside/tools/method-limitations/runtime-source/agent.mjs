/** Full Coding Agent SDK boundary: sessions, model descriptor and transcript conversion. */
import {pathToFileURL} from 'node:url';
import {dirname,resolve,join} from 'node:path';
import {readFile,mkdir} from 'node:fs/promises';
let getCurrentTools,getCurrentSystemPrompt;
export async function loadPi(entryPath){
const entry=resolve(entryPath), base=dirname(entry);
const pkg=JSON.parse(await readFile(resolve(base,'../package.json'),'utf8'));
if(pkg.name!=='@earendil-works/pi-coding-agent'||pkg.version!=='1.5.0')throw Error('Pinned SDK required');
const sdk=await import(pathToFileURL(entry));
const ai=await import(pathToFileURL(resolve(base,'../../pi-ai/dist/index.js')));
({getCurrentTools,getCurrentSystemPrompt}=ai);
return {...sdk,...ai,packageName:pkg.name,packageVersion:pkg.version};
}
function text(content){if(typeof content==='string')return content;if(!Array.isArray(content)||content.some(x=>x.type!=='text'))throw Error('Text-only task protocol');return content.map(x=>x.text).join('');}
const reasoningFields=['reasoning','reasoning_content','reasoning_details'];
function originalReasoning(message){
 const value={};for(const key of reasoningFields)if(Object.hasOwn(message,key))value[key]=message[key];
 for(const [key,item] of Object.entries(value))if(item!==null&&(key==='reasoning_details'?(!Array.isArray(item)||item.some(x=>!x||typeof x!=='object'||Array.isArray(x))):typeof item!=='string'))throw Error('Invalid original provider reasoning');
 return value;
}
export function hostContext(context){
 const messages=[{role:'system',content:getCurrentSystemPrompt(context.messages)}];
 for(const m of context.messages){
  if(m.role==='system')continue;
  if(m.role==='user')messages.push({role:'user',content:text(m.content)});
  else if(m.role==='toolResult')messages.push({role:'tool',tool_call_id:m.toolCallId,content:text(m.content)});
  else if(m.role==='assistant'){
   if(m.content.some(x=>!['text','toolCall','thinking'].includes(x.type)))throw Error('Unsupported image block');
   const thinking=m.content.filter(x=>x.type==='thinking');let reasoning={};
   if(thinking.length){
    if(thinking.length!==1)throw Error('Unexpected provider reasoning blocks');
    const envelope=JSON.parse(thinking[0].thinkingSignature);
    if(Object.keys(envelope).length!==1||!envelope.pi_swarm_provider_reasoning_v1)throw Error('Unbound provider reasoning');
    reasoning=originalReasoning(envelope.pi_swarm_provider_reasoning_v1);
    if(JSON.stringify(reasoning)!==JSON.stringify(envelope.pi_swarm_provider_reasoning_v1)||thinking[0].thinking!==(reasoning.reasoning??reasoning.reasoning_content??''))throw Error('Changed provider reasoning');
   }
   messages.push({role:'assistant',content:m.content.filter(x=>x.type==='text').map(x=>x.text).join(''),tool_calls:m.content.filter(x=>x.type==='toolCall').map(c=>({id:c.id,type:'function',function:{name:c.name,arguments:JSON.stringify(c.arguments)}})),...reasoning});
  }else throw Error('Unsupported provider message role: '+m.role);
 }
 return {messages,tools:getCurrentTools(context.messages).map(t=>({type:'function',function:{name:t.name,description:t.description,parameters:t.parameters}}))};
}
export function response(reply,model){const m=reply.assistant_message,u=reply.usage,content=[];
 const finish=u?.finish_reason;
 if(!finish||!['stop','length'].includes(finish.type))throw Error('Explicit original finish reason required');
 const reasoning=originalReasoning(m);
 if(Object.keys(reasoning).length)content.push({type:'thinking',thinking:reasoning.reasoning??reasoning.reasoning_content??'',thinkingSignature:JSON.stringify({pi_swarm_provider_reasoning_v1:reasoning})});
 if(m.content)content.push({type:'text',text:m.content});
 for(const c of m.tool_calls??[])content.push({type:'toolCall',id:c.id,name:c.function.name,arguments:typeof c.function.arguments==='string'?JSON.parse(c.function.arguments):c.function.arguments});
 return {role:'assistant',api:model.api,provider:model.provider,model:model.id,content,timestamp:Date.now(),stopReason:finish.type==='length'?'length':content.some(x=>x.type==='toolCall')?'toolUse':'stop',usage:{input:u.prompt_tokens,output:u.completion_tokens,cacheRead:u.cached_tokens??null,cacheWrite:null,totalTokens:u.prompt_tokens==null||u.completion_tokens==null?null:u.prompt_tokens+u.completion_tokens,cost:{input:null,output:null,cacheRead:null,cacheWrite:null,total:null}}};
}

export async function createPiSession({cfg,pi,modelRuntime,model,inherited,customTools}){
 const {createAgentSession,createExtensionRuntime,SessionManager,SettingsManager}=pi;
 const manager=SessionManager.inMemory(cfg.cwd);for(const m of inherited)manager.appendMessage(m);
 const resourceLoader={getExtensions:()=>({extensions:[],errors:[],runtime:createExtensionRuntime()}),getSkills:()=>({skills:[],diagnostics:[]}),getPrompts:()=>({prompts:[],diagnostics:[]}),getThemes:()=>({themes:[],diagnostics:[]}),getAgentsFiles:()=>({agentsFiles:[]}),getSystemPrompt:()=>cfg.systemPrompt,getSystemPromptSource:()=>undefined,getAppendSystemPrompt:()=>[],getAppendSystemPromptSources:()=>[],extendResources(){},async reload(){}};
 return await createAgentSession({cwd:cfg.cwd,agentDir:cfg.agentDir,modelRuntime,model,thinkingLevel:'off',resourceLoader,sessionManager:manager,settingsManager:SettingsManager.inMemory({compaction:{enabled:false},retry:{enabled:false}}),tools:customTools.map(t=>t.name),customTools});
}
