import sys, time, torch
sys.path.insert(0, '<project-root>/checklimits/scratch/agent_runs/e2e-f022-e16018/workspace/attempt')
import dev_proto
q_len = 3501; hd = 4
torch.manual_seed(0)
q = torch.randn(1, 1, q_len, hd); k = torch.randn(1, 1, q_len, hd)
t = time.time(); sc = dev_proto.scores(q, k); print('time', round(time.time() - t, 2))
for n, (v, e) in sc.items():
    print(n, float(v))
