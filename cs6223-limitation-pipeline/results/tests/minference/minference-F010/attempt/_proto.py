import os, sys, types, importlib.util, importlib.machinery, torch
sys.path.insert(0,'/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/checklimits')
from checklimits.fakes import RecordingModule, Recorder, RecordingCallable
rec=Recorder()
import importlib.machinery as _im
for _n in ['flash_attn','pycuda','pycuda.autoprimaryctx','pycuda.compiler']:
    pass
for n in ["pycuda","pycuda.autoprimaryctx","pycuda.compiler","flash_attn"]:
    sys.modules[n]=RecordingModule(n,rec,"return_first_arg")
    sys.modules[n].__spec__=_im.ModuleSpec(n,loader=None,is_package=True); sys.modules[n].__spec__.submodule_search_locations=[]
_orig_arange=torch.arange
def cpu_arange(*a,**k):
    if k.get('device') in ('cuda','cuda:0'):
        k['device']='cpu'
    return _orig_arange(*a,**k)
torch.arange=RecordingCallable("torch.arange",rec,cpu_arange)
repo='/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/MInference'
root=os.path.join(repo,'minference')
def _pkg(name,path):
    m=types.ModuleType(name); m.__path__=[path]; m.__package__=name
    sp=importlib.machinery.ModuleSpec(name,loader=None,is_package=True); sp.submodule_search_locations=[path]
    m.__spec__=sp; sys.modules[name]=m; return m
_pkg('minference',root); _pkg('minference.modules',os.path.join(root,'modules')); _pkg('minference.ops',os.path.join(root,'ops'))
def _load(name,path):
    sp=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m
bs=_load('minference.ops.block_sparse_flash_attention',os.path.join(root,'ops','block_sparse_flash_attention.py'))
ps=types.ModuleType('minference.ops.pit_sparse_flash_attention_v2')
ps.vertical_slash_sparse_attention=lambda *a,**k: None
ps.__spec__=importlib.machinery.ModuleSpec(ps.__name__,loader=None); sys.modules[ps.__name__]=ps
mf=_load('minference.modules.minference_forward',os.path.join(root,'modules','minference_forward.py'))
print("loaded, entry?",hasattr(mf,'gather_last_q_vertical_slash_topk_v4'))
class C:
    def to_dict(self): return {}
class S:
    config=C(); best_pattern={0:("block_sparse",100,100,1)}
def mk(Lq,Lk,Lv):
    q=torch.randn(1,1,2,Lq); k=torch.randn(1,1,2,Lk); v=torch.randn(1,1,2,Lv)
    return q,k,v
entry=mf.gather_last_q_vertical_slash_topk_v4
for Lv in (1,2,3):
    try:
        out=entry(S(),*mk(2,2,Lv),0)
        print("Lv",Lv,"returned",type(out))
    except Exception as e:
        import traceback; tb=traceback.extract_tb(e.__traceback__)
        print("Lv",Lv,"EXC",type(e).__name__,"at",tb[-1].filename.split('/')[-1],tb[-1].lineno,"::",str(e)[:60])
print("events",len(rec.events))
for e in rec.events[:12]: print(e)
