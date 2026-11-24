"""Bounded corpus runner with immediate stop on transport failure."""
import argparse,traceback,threading,re
from pathlib import Path
import run_complete_corpus as runner
import build_paper_handoff as builder
from paperprobe.io import read_json,write_json
from recover_corpus_transport import transport_error,TRANSPORT


class TransportStop(BaseException):pass


def main(pid,workers=1,run_name='serial'):
    work=runner.BASE/pid;work.mkdir(parents=True,exist_ok=True)
    if not re.fullmatch(r'[a-z0-9-]+',run_name):raise ValueError('Invalid run identity')
    protocol=work/(run_name+'-protocol.json')
    if protocol.exists():raise ValueError('Serial run already started; inspect before any separately named resume')
    write_json(protocol,dict(started_at=runner.now(),global_api_sessions=workers,paper_slots=1,workers=workers,k2_discovery='Two independent prompts with isolated inputs; execution sequential only when workers=1',transport_retries=0,circuit_breaker='First transport failure aborts paper and cancels unstarted futures; in-flight work preserved; no automatic retry',target_execution='not_run'))
    pool=runner.ThreadPoolExecutor
    class SerialPool(pool):
        def __init__(self,*args,**kwargs):super().__init__(max_workers=workers)
    runner.ThreadPoolExecutor=SerialPool
    stopped=threading.Event()
    original_call=runner.model_call
    def call(*args,**kwargs):
        if stopped.is_set():raise TransportStop('Prior transport failure; no new API request')
        try:return original_call(*args,**kwargs)
        except Exception as e:
            if any(t in str(e) for t in TRANSPORT):
                stopped.set();raise TransportStop(str(e)) from e
            raise
    runner.model_call=call;builder.model_call=call
    original_stage=runner.stage_call
    def stage(stage,runtime):
        if stopped.is_set():
            state=stage.parent/'state.json'
            if state.exists():
                r=read_json(state);r.update(state='failed',reason='Not started: prior transport circuit breaker',updated_at=runner.now());write_json(state,r)
            raise TransportStop('Prior transport failure; no new stage API request')
        ok=original_stage(stage,runtime)
        err=transport_error(stage)
        if not ok and err:
            stopped.set()
            state=stage.parent/'state.json'
            if state.exists():
                r=read_json(state);r.update(state='failed',reason='Serial circuit breaker: '+err,updated_at=runner.now());write_json(state,r)
            raise TransportStop(err)
        return ok
    runner.stage_call=stage
    try:
        runner.run(pid)
        write_json(work/(run_name+'-complete.json'),dict(finished_at=runner.now(),state=read_json(work/'state.json')['state']))
    except BaseException as e:
        old=read_json(work/'state.json') if (work/'state.json').exists() else None
        failed='blocked_transport' if isinstance(e,TransportStop) else 'failed'
        record=dict(paper=pid,state=failed,error=str(e),traceback=traceback.format_exc(),time=runner.now(),previous_state=old,remote_consumption='unknown' if isinstance(e,TransportStop) else None)
        write_json(work/(run_name+'-failure.json'),record);write_json(work/'state.json',record)
        print('SERIAL_STOP',pid,failed,str(e),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--paper',required=True);p.add_argument('--workers',type=int,choices=[1,2],default=1);p.add_argument('--run-name',default='serial');a=p.parse_args();main(a.paper,a.workers,a.run_name)
