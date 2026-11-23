# Freeze record (2026-11-23 18:49 +08)
Code frozen at the commit that contains this file (parent: 77139aee05a3691bcf50d474c812ff1bfe1df299). Test split (13 cases: CS6223-05..17) is run ONCE per system below, 2 repeats, no tuning after this point.
Systems (all declared before any test run; none selected on test results):
- P-v2: our pipeline paper-only lane, mechanism pass + enrichment (prompt paper-only-v2, enrich-v1), `python -m pipeline limitset run --split test --repeats 2`
- P-swarm: our pipeline with PaperTest Swarm generator (s7), `--generator swarm`
- B1: one-request baseline; B2: opencode headless baseline (`python -m pipeline limitset baseline --method b1|b2`)
Model alias x-test-2 (backend user-confirmed: DeepSeek V4.1 flash 1017). Judge: scorer_limitset, judge-v2-batched, temperature 0, timeout 420 s.
Validation results used for development (tuning allowed there only): out/limitset/{val3,val4,valsw}, out/limitset_baselines/{b1_val,b2_val}; validation coverage so far 0/4 (P-v2), B1 1/4, B2 1/4 (CS6223-04); P-swarm pending.
Fallback rule: if a system does not finish all 26 runs by 19:25 it is reported as partial (completed cases only), not extended.
