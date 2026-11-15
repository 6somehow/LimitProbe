"""Resume a paper after inspected transport failure using one new request identity."""
import argparse
import threading
from pathlib import Path
import run_complete_corpus as runner
import build_paper_handoff as builder
from paperprobe.io import read_json,write_json


def main(pid,workers=2):
    work=runner.BASE/pid
    original=runner.model_call
    ledger=work/'network-recovery-v1.json'
    routes=read_json(ledger) if ledger.exists() else dict(version='network-recovery-v1',started_at=runner.now(),policy='Each preserved incomplete original request gets at most one separately named transport recovery; remote consumption of failed original unknown',routes={})
    ledger_lock=threading.Lock()
    routes['actual_workers']=workers
    pool=runner.ThreadPoolExecutor
    class BoundedPool(pool):
        def __init__(self,*args,**kwargs):super().__init__(max_workers=workers)
    runner.ThreadPoolExecutor=BoundedPool
    def resolve(dest):
        dest=Path(dest)
        if '-network-recovery-v1' not in dest.stem and not dest.exists() and dest.with_suffix('.request.json').exists():
            name=str(dest.relative_to(work));new=dest.with_name(dest.stem+'-network-recovery-v1.json')
            with ledger_lock:
                routes['routes'][name]=str(new.relative_to(work));write_json(ledger,routes)
            return new
        return dest
    def call(dest,prompt,data,images=(),max_tokens=12000):
        # model_call rejects another attempt if the recovery identity is unfinished.
        return original(resolve(dest),prompt,data,images,max_tokens=max_tokens)
    checked=runner.checked
    def checked_call(dest,prompt,data,images,validate):
        return checked(resolve(dest),prompt,data,images,validate)
    runner.checked=checked_call
    runner.model_call=call;builder.model_call=call
    try:
        runner.run(pid)
        routes['result']=read_json(work/'state.json')['state']
    except Exception as e:
        import traceback
        routes['result']='failed';write_json(work/'network-recovery-v1.failure.json',dict(error=str(e),traceback=traceback.format_exc(),time=runner.now()))
        print('NETWORK_RECOVERY_FAILED',pid,str(e),flush=True)
    routes['finished_at']=runner.now();write_json(ledger,routes)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--paper',required=True);p.add_argument('--workers',type=int,choices=[1,2],default=2);a=p.parse_args();main(a.paper,a.workers)
