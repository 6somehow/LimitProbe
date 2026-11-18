import sys, time, torch
sys.path.insert(0, '/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/checklimits/scratch/agent_runs/e2e-f022-e16018/workspace/attempt')
import dev_proto
from dev_build import build

for a, bq in [(0.0, 0.0), (10.0, 1.5), (1.0, 0.2), (0.5, 0.1), (0.2, 0.05)]:
    for n in (0, 1):
        q, k = build(n, a=a, bias_q=bq, m2=20.0)
        sc = dev_proto.scores(q, k)
        vals = {name: float(v) for name, (v, e) in sc.items()}
        print('a', a, 'bq', bq, 'n', n, 'stream', round(vals['stream'], 6),
              'v30', round(vals['v30'], 6), 'v100', round(vals['v100'], 6),
              'v500', round(vals['v500'], 6), 'v3500', round(vals['v3500'], 6),
              'block', round(vals['block'], 6))
