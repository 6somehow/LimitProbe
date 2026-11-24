# Code-side evidence per artifact (static, uncalibrated)

Written by `scripts/run_step4.py`; rules in `docs/11_process_confidence.md`. The code side sets no level. `ceiling` is the highest test level a Finding can reach under the test side's rules, predicted before any test.

| artifact | code-side findings | ceiling: not_testable | L1 | L2 | L3 | not_measured | decision on main / side / unknown path | decisions in entry-reachable functions | listed by the code side |
|---|---|---|---|---|---|---|---|---|---|
| flexposit | 22 | 10 | 10 | 1 | 1 | 0 | 7 / 7 / 8 | 24 in 20 functions | 6 |
| flexprefill | 46 | 17 | 14 | 4 | 11 | 0 | 10 / 24 / 12 | 70 in 18 functions | 29 |
| infinigen | 20 | 1 | 13 | 6 | 0 | 0 | 2 / 15 / 3 | 34 in 14 functions | 8 |
| minference | 50 | 13 | 26 | 1 | 10 | 0 | 16 / 21 / 10 | 64 in 32 functions | 28 |
| nnsmith | 35 | 13 | 20 | 0 | 2 | 0 | 4 / 19 / 10 | 149 in 191 functions | 17 |
| qoserve | 14 | 5 | 4 | 0 | 5 | 0 | 6 / 6 / 2 | 39 in 22 functions | 11 |
| sparta | 3 | 1 | 1 | 1 | 0 | 0 | 0 / 1 / 2 | 5 in 9 functions | 1 |

Check states over all artifacts (eliminated / residual / open / refuted):

| check | eliminated | residual | open | refuted |
|---|---|---|---|---|
| C1 location | 185 | 5 | 0 | 0 |
| C2 condition | 156 | 29 | 5 | 0 |
| C3 reachability | 98 | 20 | 72 | 0 |
| C4 feasibility | 139 | 39 | 0 | 12 |
| C5 extraction | 111 | 79 | 0 | 0 |
| C6 effect_label | 142 | 0 | 48 | 0 |
| C7 documentation | 28 | 162 | 0 | 0 |
| C8 review | 0 | 69 | 108 | 13 |
