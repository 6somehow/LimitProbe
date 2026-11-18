import sys, types, pathlib, importlib.util
import torch

REPO = pathlib.Path('/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/InfiniGen')
for sub in ('speedup/infinigen', 'speedup/flexgen'):
    p = str(REPO / sub)
    if p not in sys.path: sys.path.insert(0, p)

torch.manual_seed(0)

def load_target():
    path = REPO / 'speedup/flexgen/infinigen/pytorch_backend.py'
    spec = importlib.util.spec_from_file_location('_cl_target_backend', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['_cl_target_backend'] = mod
    spec.loader.exec_module(mod)
    return mod

tb = load_target()
tb.fix_recursive_import()
from flexgen.compression import CompressionConfig

torch.Tensor.is_cuda = property(lambda self: True)

dev = tb.TorchDevice('cpu')
cd = dev.compressed_device

def tt(shape_or_t):
    if isinstance(shape_or_t, torch.Tensor):
        return tb.TorchTensor.create_from_torch(shape_or_t, dev)
    return tb.TorchTensor.create_from_torch(torch.zeros(shape_or_t), dev)

def run(group_dim):
    b, tgt_s, n_head, head_dim = 1, 1, 1, 2
    h = n_head * head_dim
    P, G = 3, 2
    K = P + G - 1
    cfg = CompressionConfig(num_bits=4, group_size=2, group_dim=group_dim, symmetric=False)
    cfg_cache = CompressionConfig(num_bits=4, group_size=2, group_dim=group_dim, symmetric=False)
    class C: pass
    class T: pass
    class P_: pass
    c=C(); c.n_head=n_head; c.input_dim=h
    t=T(); t.prompt_len=P; t.gen_len=G
    po=P_(); po.gpu_batch_size=b; po.comp_cache_config=cfg_cache
    cd.init_attention_compute_workspace(c, t, po)

    inputs = tt(torch.randn(b, tgt_s, h))
    mask = tt(torch.ones(b, K + 1))
    wq = tt(torch.randn(h, h+1)); bq=tt(torch.randn(h))
    wk = tt(torch.randn(h, h+1)); bk=tt(torch.randn(h))
    wv = tt(torch.randn(h, h)); bv = tt(torch.randn(h))
    wo = tt(torch.randn(h, h)); bo = tt(torch.randn(h))
    wln = tt(torch.randn(h)); bln = tt(torch.randn(h))

    k_raw = torch.randn(K, b*n_head, head_dim, dtype=torch.float16)
    v_raw = torch.randn(K, b*n_head, head_dim, dtype=torch.float16)
    comp_k = cd.compress(k_raw, cfg_cache)
    comp_v = cd.compress(v_raw, cfg_cache)
    k_cache = tb.TorchTensor(comp_k.shape, comp_k.dtype, comp_k.data, cd)
    v_cache = tb.TorchTensor(comp_v.shape, comp_v.dtype, comp_v.data, cd)

    donate = [False]*14
    out = dev.mha_gen(inputs, mask, wq, bq, wk, bk, wv, bv,
                      wo, bo, wln, bln, n_head, k_cache, v_cache, donate,
                      1.0, True, cfg, None, None, None, 1.0, 1)
    print('group_dim', group_dim, 'returned new_k shape', out[1].shape, 'new_v', out[2].shape, 'value', out[0].shape)

run(0)
run(1)
