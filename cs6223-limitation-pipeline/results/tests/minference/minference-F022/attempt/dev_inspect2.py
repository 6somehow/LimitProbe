import sys, torch, math
sys.path.insert(0, '<project-root>/checklimits/scratch/agent_runs/e2e-f022-e16018/workspace/attempt')
import dev_proto
from dev_build import build

n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
q, k = build(n, a=0.0, bias_q=0.0, m2=20.0)
sc = dev_proto.scores(q, k)
q_len = q.shape[2]; head_dim = q.shape[-1]
attention_mask = dev_proto.make_mask(q_len).to(q.dtype)
aw = torch.matmul(q, k.transpose(2, 3)) / math.sqrt(head_dim) + attention_mask
aw = torch.nn.functional.softmax(aw, dim=-1, dtype=torch.float32).to(q.dtype)
print('raw slice sums rows 2800,3000,3300,3400,3437,3460,3500',
      [round(float(aw[0, 0, i, 2500:].sum()), 4) for i in (2800, 3000, 3300, 3400, 3437, 3460, 3500)])
for name in ('stream', 'v30', 'v3500'):
    v, e = sc[name]
    print(name, 'score', round(float(v), 4),
          'est r3000 k2500', float(e[0, 0, 3000, 2500]),
          'est r3000 k2496', float(e[0, 0, 3000, 2496]),
          'est r3000 slice', float(e[0, 0, 3000, 2500:].sum()))
last_q = 64
qk_idxs = [ii + q_len for ii in list(range(-last_q, 0, 1))]
qk = torch.matmul(q[:, :, qk_idxs, :], k.transpose(2, 3)) / math.sqrt(head_dim) + attention_mask[:, :, qk_idxs]
qk = torch.nn.functional.softmax(qk, dim=-1, dtype=torch.float32)
vertical = qk.sum(-2, keepdim=True)
v2 = vertical.clone(); v2[..., :30] = torch.inf
print('vertical k2500', float(vertical[0, 0, 0, 2500]), 'k2496', float(vertical[0, 0, 0, 2496]),
      'k2592', float(vertical[0, 0, 0, 2592]))
print('smallest keys', torch.topk(-v2, 5, -1).indices[0, 0, 0].tolist())
for name in ('stream', 'v30', 'v3500'):
    v, e = sc[name]
    r = (aw * e)[0, 0, :, 2500:].sum(-1)
    nz = [(i, round(float(r[i]), 3)) for i in range(2500, q_len) if float(r[i]) > 0.01]
    print(name, 'nrows', len(nz), 'sumr', round(float(r.sum()),4), 'meansum', round(float(r.mean()),6), 'first', nz[:4], 'last', nz[-4:])
