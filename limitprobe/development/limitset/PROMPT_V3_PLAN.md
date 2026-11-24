PROMPT v3 PLAN (user decision 2026-11-23 ~19:45): design the generator prompt from the patterns of ALL 17 labels. Goals: 1) finish fast, 2) test arms in parallel. Supersedes the validation-only rule for prompt design.

0. HONESTY (mandatory, write in docs/13): from v3 on there is NO held-out data. Every v3 number is in-sample ("dataset-informed prompt, all 17 labels studied"). Keep v1 test results as the only clean held-out numbers. The prompt must stay GENERIC: no paper names, no case-specific terms (GQA, RoPE, sparsity, KV, CXL, ...), no label sentences. Add a leakage test: no 5-gram of any label text (labels_en + zh) appears in the prompt.

1. WHAT THE 17 LABELS HAVE IN COMMON (from headline + mechanism_insight)
All are second-order: paper fact + a general systems/ML premise -> a conditional consequence the paper did not state. Headline form "A does not imply/guarantee B" or "A conflicts with B". 7 recurring lenses:
L1 Proxy != target property: the method optimizes/measures X, but the benefit depends on Y (ratio vs structure, position vs sensitivity, access difficulty vs reorderability, model size vs net benefit, operation share vs critical path, interface size vs obligations). [04,09,14,16,17,15]
L2 Objective / stopping-rule mismatch: the search or training objective (stop at first valid; imitate a teacher; self-generated feedback) differs from the real goal; diversity on one axis hides concentration on another. [01,08,10]
L3 Granularity / unit mismatch between two mechanisms: method unit vs system/ecosystem unit (per-head vs shared group, protection unit vs scheduling unit, replica unit vs request unit, engineering boundary vs semantic dependency). [03,11,13,05]
L4 Unnecessary binding / coupling: two things bound together that need not be (state compression and update direction; cheap shared transform and search space; low-frequency logic placed on the high-frequency path). [06,07,12]
L5 Origin of the exploited structure: where does the regularity the method relies on come from (architecture, encoding, deployment condition), and which common change would move it? [02,09]
L6 Cost moved, not removed / net-benefit threshold: the cost shifts in time, place or to co-tenants; benefit needs a threshold (interval, hit rate, prediction usefulness). [16,17,12,13]
L7 Regime change over scale or time: what works early becomes the bottleneck later (as the model improves, as data/objects grow, as tenants share). [08,10,15]
Category hint: applicability = holds only when an environment/workload/ecosystem condition holds (L1,L3,L6); mechanism_origin_unclear = the cause of the exploited pattern is not established (L5); method_shortcoming = the method's own objective/design limits it (L2,L4,L7). Disclosure: many are "mechanism reported, consequence inferred"; 4 are explicit author boundaries restated with the mechanism; include both, label which.

2. GENERATOR PROMPT v3 (English, paper-only lane + InfiniGen with code)
Step 1 Mechanism inventory: list 8-15 core mechanisms/design decisions with verbatim quote anchors; for each: what it optimizes, its unit/granularity, what it assumes about workload/model/hardware, which regularity it exploits, where cost goes.
Step 2 Lens sweep: for EVERY mechanism, apply L1-L7 (one short question per lens); keep pairs where a general premise gives a non-obvious, conditional consequence. Also convert every "paper observes X but does not explain" into a causal hypothesis (why, when worse, what refutes it).
Step 3 Write candidates (25-30 per paper) in the label structure: headline ("A does not imply B" style), paper_fact (quote), premise (general knowledge, no quote needed), inference, optional toy_example (marked as not a measurement), consequence (conditional), critical_link (the one link that must hold), necessary_conditions[], defeaters[], do_not_infer[], disclosure (reported / mechanism_reported_consequence_inferred / inferred), category_code, lens.
Step 4 Self-filter + rank: move first-order items (evaluation scope, few models, missing error bars, "only prefill") to kind=evaluation_critique (kept, reported separately). Rank by non-obviousness x causal clarity x conditionality; dedupe by mechanism; keep top 20 in the main list.
Keep: quote verification, prediction schema (conditions as list), English output.

3. PARALLEL ARMS (run at the same time, 1 repeat each for screening, all 17 cases, one relay, concurrency tuned under the 429 limit; Codex for code, one package per arm)
A0 mechanism v1 (existing, rescore only)
A1 v3 prompt (Steps 1-4)
A2 v3 without Step 4 filter (breadth, ~30 items)
A3 union: A1 + swarm lane + B1 findings, dedupe by mechanism (cheap: no new generation)
Score all arms with the English judge (judge-v3-en) as soon as each finishes (pipeline: an arm's scorer starts when its run ends; wait_done.sh per arm). Pick the best arm by per-case hits (tie: field coverage, then fewer items). Then 1 more repeat of the best arm only for stability. Report: per-arm hits /17 with Wilson CI, per category, per case wins vs B1/B2/swarm, items per case, cost.

4. TIMING: start now; arms in parallel; target first numbers in ~40 min. If the 429 limit stalls, cut A2 first. Report to the user (short Chinese) when the arm table is ready.
