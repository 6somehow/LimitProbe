import os, sys, types, torch

REPO = '<project-root>/third_party/MInference'
sys.path.insert(0, REPO)

for name in ['flash_attn', 'pycuda', 'pycuda.autoprimaryctx', 'pycuda.compiler', 'minference.cuda']:
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
sys.modules['flash_attn'].flash_attn_varlen_func = lambda *a, **k: None
sys.modules['flash_attn'].flash_attn_func = lambda *a, **k: None
sys.modules['pycuda.compiler'].SourceModule = lambda *a, **k: None
sys.modules['minference.cuda'].convert_vertical_slash_indexes = lambda *a, **k: None

_orig = torch.arange


def cpu_arange(*a, **k):
    d = k.get('device')
    if d is not None and str(d).startswith('cuda'):
        k['device'] = 'cpu'
    return _orig(*a, **k)


torch.arange = cpu_arange

import transformers.modeling_flash_attention_utils as _mfa

_mfa.flash_attn_supports_top_left_mask = lambda: None

pkg = types.ModuleType('minference')
pkg.__path__ = [os.path.join(REPO, 'minference')]
pkg.__package__ = 'minference'
sys.modules['minference'] = pkg
import minference.modules.minference_forward as m

print('imported', m.gather_last_q_vertical_slash_topk_v4)


class C:
    def __init__(self, vs):
        self.vs = vs

    def to_dict(self):
        return {'vs_only': self.vs}


class S:
    def __init__(self, vs, ty='block_sparse'):
        self.config = C(vs)
        self.best_pattern = {0: (ty, 1000, 6096, 1)}


for qlen in [8, 128]:
    for vs in [True, False]:
        s = S(vs)
        torch.manual_seed(0)
        q = torch.randn(1, 1, qlen, 8)
        k = torch.randn(1, 1, qlen, 8)
        v = torch.randn(1, 1, qlen, 8)
        try:
            r = m.gather_last_q_vertical_slash_topk_v4(s, q, k, v, 0)
            print('qlen', qlen, 'vs', vs, '->', type(r), r)
        except Exception as e:
            import traceback
            print('qlen', qlen, 'vs', vs, 'EXC', type(e).__name__, e)
            traceback.print_exc()
