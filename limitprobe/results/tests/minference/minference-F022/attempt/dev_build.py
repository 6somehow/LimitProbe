import sys, time, math, torch
sys.path.insert(0, '<project-root>/checklimits/scratch/agent_runs/e2e-f022-e16018/workspace/attempt')
import dev_proto

Q_LEN = 3501
HD = 4
M = 6.0
M2 = 10.0
C = 1.0
D = 1.0
A = 10.0
BIAS_KEY = 2600
BIAS_ROW = 3401
BIAS_Q = 1.5


def build(n_attend=501, start=2800, q_len=Q_LEN, hd=HD, m=M, m2=M2, c=C, d=D, a=A, bias_q=BIAS_Q):
    q = torch.zeros(1, 1, q_len, hd, dtype=torch.float32)
    k = torch.zeros(1, 1, q_len, hd, dtype=torch.float32)
    q[..., 2] = c
    k[0, 0, :32, 2] = d
    # positive group: rows [start, start+n_attend) attend key 2500
    q[0, 0, start:start + n_attend, 1] = -m
    # last 64 rows attend the +m keys near the end (for vertical sums)
    q[0, 0, q_len - 64:, 1] = m
    k[0, 0, 2500, 1] = -m2
    k[0, 0, 2496, 1] = m2          # balance block 78 mean
    # block 108: keys 3456..3487, 16 +m and 16 -m
    k[0, 0, 3456:3472, 1] = m
    k[0, 0, 3472:3488, 1] = -m
    # block 109: keys 3488..3500 (13 keys), 6 +m, 6 -m, 1 zero
    k[0, 0, 3488:3494, 1] = m
    k[0, 0, 3494:3500, 1] = -m

    # bias row attends key 2600 weakly; last 64 attend it strongly so vertical keeps it
    k[0, 0, BIAS_KEY, 3] = a
    k[0, 0, 2592, 3] = -a        # balance block 81 mean
    q[0, 0, q_len - 64:, 3] = a
    q[0, 0, BIAS_ROW, 3] = bias_q
    return q, k


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 501
    q, k = build(n)
    t = time.time()
    sc = dev_proto.scores(q, k)
    print('n', n, 'time', round(time.time() - t, 2))
    for name, (v, e) in sc.items():
        print(name, float(v))
