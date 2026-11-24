import sys, torch, math
sys.path.insert(0, '<project-root>/checklimits/scratch/agent_runs/e2e-f022-e16018/workspace/attempt')
import dev_proto
from dev_build import build

q, k = build(801)
q_len = q.shape[2]; head_dim = q.shape[-1]
attention_mask = dev_proto.make_mask(q_len).to(q.dtype)
attn_weights = torch.matmul(q, k.transpose(2, 3)) / math.sqrt(head_dim) + attention_mask
attn_weights = torch.nn.functional.softmax(attn_weights, dim=-1, dtype=torch.float32).to(q.dtype)
sc = dev_proto.scores(q, k)
for name in ('stream', 'v3500'):
    v, e = sc[name]
    r = (attn_weights * e)[0, 0, :, 2500:].sum(-1)
    nz = [(i, float(r[i])) for i in range(2500, q_len) if float(r[i]) > 0.01]
    print(name, 'score', float(v), 'n_nonzero_rows', len(nz))
    print(' first', nz[:6])
    print(' last', nz[-8:])
    print(' 3300-3340', [(i, round(float(r[i]), 3)) for i in range(3298, 3305)])
    print(' 3430-3440', [(i, round(float(r[i]), 3)) for i in range(3430, 3441)])
