import sys, torch
sys.path.insert(0, '<project-root>/checklimits/scratch/agent_runs/e2e-f022-e16018/workspace/attempt')
import dev_proto
from dev_build import build

q, k = build(801)
sc = dev_proto.scores(q, k)
for name in ('stream', 'v3500'):
    v, e = sc[name]
    print(name, float(v), 'est row2500 key2500', float(e[0, 0, 2500, 2500]),
          'row2600 key2500', float(e[0, 0, 2600, 2500]),
          'row3000 key2500', float(e[0, 0, 3000, 2500]),
          'row3437 slice sum', float(e[0, 0, 3437, 2500:].sum()))
# recompute vertical sums for last64 and find smallest keys
q_len = q.shape[2]; head_dim = q.shape[-1]
import math
attention_mask = dev_proto.make_mask(q_len).to(q.dtype)
last_q = 64
qk_idxs = [ii + q_len for ii in list(range(-last_q, 0, 1))]
qk = torch.matmul(q[:, :, qk_idxs, :], k.transpose(2, 3)) / math.sqrt(head_dim) + attention_mask[:, :, qk_idxs]
qk = torch.nn.functional.softmax(qk, dim=-1, dtype=torch.float32)
vertical = qk.sum(-2, keepdim=True)
print('vertical key2500', float(vertical[0, 0, 0, 2500]), 'key2496', float(vertical[0, 0, 0, 2496]),
      'key3472', float(vertical[0, 0, 0, 3472]), 'key500', float(vertical[0, 0, 0, 500]))
# rank smallest ignoring 0..29 (set inf like code)
v2 = vertical.clone(); v2[..., :30] = torch.inf
print('smallest keys', torch.topk(-v2, 5, -1).indices[0, 0, 0].tolist())
