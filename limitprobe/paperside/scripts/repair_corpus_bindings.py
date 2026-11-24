"""One binding-schema repair then cache-only export; preserve original proposals."""
import argparse
from pathlib import Path
import run_complete_corpus as runner
import build_paper_handoff as builder
from paperprobe.io import read_json,write_json


def main(pid):
    work=runner.BASE/pid;dest=work/'bindings-structure-repair-v1.raw.json'
    req=read_json(work/'bindings.raw.request.json');raw=read_json(work/'bindings.raw.json')
    write_json(work/'bindings-structure-repair-v1.protocol.json',dict(started_at=runner.now(),cause='Original binding proposal omitted required line_end, causing old builder KeyError',model_requests_max=1,scope='Binding schema only; no code verdict changes, no new source tools',original_request='bindings.raw.request.json',original_response='bindings.raw.json',repair_response=dest.name,target_execution='not_run'))
    result=runner.model_call(dest,req['prompt']+'\nSTRUCTURAL CORRECTION: Return COMPLETE JSON with bindings and open_questions. Every binding must have paper_term,kind,code_symbol,repo,path,line_start,line_end,certain,rationale. line_start and line_end must be integers, 1 <= line_start <= line_end, within the actual supplied source packet. Do not invent a missing endpoint or scalar correspondence. Reassess the previous proposals against actual supplied source. Put unverifiable proposals in open_questions; the complete original response remains preserved. Code conformance verdicts are outside scope.',dict(original_input=req['data'],previous_response=raw['choices'][0]['message']['content'],validation_error="Binding omitted line_end; old builder requires every location field"),max_tokens=12000)
    required={'paper_term','kind','code_symbol','repo','path','line_start','line_end','certain','rationale'}
    for b in result['bindings']:
        if not required.issubset(b):raise ValueError('Binding structural recovery missing required fields')
        if not isinstance(b['line_start'],int) or not isinstance(b['line_end'],int) or not 1<=b['line_start']<=b['line_end']:raise ValueError('Invalid repaired binding location')
        if b['kind'] not in ['parameter','config_key','mechanism_entry']:raise ValueError('Invalid binding kind')
    write_json(work/'bindings-structure-repair-v1.json',result)
    original=runner.model_call
    def cached(path,prompt,data,images=(),max_tokens=12000):
        path=Path(path)
        if path==work/'bindings.raw.json':return result
        if not path.exists():raise ValueError('Cache-only export refuses new request: '+str(path))
        return original(path,prompt,data,images,max_tokens=max_tokens)
    runner.model_call=cached;builder.model_call=cached
    runner.run(pid)
    print('BINDING_STRUCTURE_REPAIR_EXPORTED',pid,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--paper',required=True);a=p.parse_args();main(a.paper)
